"""
NBFC Loan Pre-Underwriting Engine (Gap 3 Resolver).

Computes DTI ratio and assigns risk bands for healthcare loans.
Formula: DTI = (Existing_EMIs + Proposed_Medical_EMI) / Gross_Monthly_Income × 100

Now integrates with Neo4j NBFCRiskBand nodes per instructioncreate.md Section 6.
Falls back to hardcoded values if graph is unavailable.
"""

from typing import Dict, Any, List, Optional
import logging

from app.engines.neo4j_loan_client import get_loan_client

logger = logging.getLogger(__name__)


# Fallback interest rate ranges by risk band (used if Neo4j unavailable)
INTEREST_RATES = {
    "low_risk": {"range": (12.0, 13.0), "approval": "Very High"},
    "medium_risk": {"range": (13.0, 15.0), "approval": "High (Conditional)"},
    "high_risk": {"range": (15.0, 16.0), "approval": "Manual Review Required"},
    "critical_risk": {"range": (0, 0), "approval": "Unlikely — Restructure First"},
}


class LoanEngine:
    """
    Automated NBFC healthcare loan pre-underwriting engine.
    Computes DTI ratio and assigns risk bands in milliseconds.
    
    Integrates with Neo4j NBFCRiskBand nodes for dynamic risk assessment.
    """

    LOAN_COVERAGE_RATIO = 0.80  # Loan covers 80% of total estimated cost
    TENURES_MONTHS = [12, 24, 36]

    def __init__(self, use_neo4j: bool = True):
        """
        Initialize the loan engine.
        
        Args:
            use_neo4j: Whether to query NBFCRiskBand from Neo4j (default True)
        """
        self.use_neo4j = use_neo4j
        self._loan_client = None
    
    @property
    def loan_client(self):
        """Lazy initialization of Neo4j loan client."""
        if self._loan_client is None and self.use_neo4j:
            try:
                self._loan_client = get_loan_client()
            except Exception as e:
                logger.warning(f"Failed to initialize Neo4j loan client: {e}")
                self.use_neo4j = False
        return self._loan_client

    def calculate_emi(self, principal: float, tenure_months: int, annual_rate: float) -> float:
        """Standard EMI formula: P × r × (1+r)^n / ((1+r)^n - 1)"""
        if annual_rate == 0:
            return principal / tenure_months
        monthly_rate = annual_rate / (12 * 100)
        n = tenure_months
        emi = principal * monthly_rate * ((1 + monthly_rate) ** n) / (((1 + monthly_rate) ** n) - 1)
        return round(emi)

    def evaluate(
        self,
        total_treatment_cost: float,
        gross_monthly_income: float,
        existing_emis: float,
    ) -> Dict[str, Any]:
        """
        Full pre-underwriting evaluation.
        Returns risk band, EMI options, and call-to-action.
        
        Queries Neo4j NBFCRiskBand if available, otherwise uses fallback.
        """
        loan_amount = round(total_treatment_cost * self.LOAN_COVERAGE_RATIO)

        # Calculate for standard 24-month tenure at median rate
        primary_emi = self.calculate_emi(loan_amount, 24, 14.0)
        primary_dti = ((existing_emis + primary_emi) / gross_monthly_income) * 100 if gross_monthly_income > 0 else 999

        # Get risk band from Neo4j or fallback
        if self.use_neo4j and self.loan_client:
            try:
                band_data = self.loan_client.get_risk_band_by_dti(primary_dti)
                risk_band = self._neo4j_band_to_legacy(band_data["risk_flag"])
                # Use graph-derived rates
                actual_rate = (band_data["interest_rate_min"] + band_data["interest_rate_max"]) / 2
                if actual_rate < 0:
                    actual_rate = 0
                band_info = {
                    "range": (band_data["interest_rate_min"], band_data["interest_rate_max"]),
                    "approval": band_data["approval_likelihood"],
                    "from_neo4j": True
                }
            except Exception as e:
                logger.warning(f"Neo4j query failed, using fallback: {e}")
                risk_band = self._classify_dti(primary_dti)
                band_info = INTEREST_RATES[risk_band]
                actual_rate = sum(band_info["range"]) / 2 if band_info["range"][0] > 0 else 0
        else:
            risk_band = self._classify_dti(primary_dti)
            band_info = INTEREST_RATES[risk_band]
            actual_rate = sum(band_info["range"]) / 2 if band_info["range"][0] > 0 else 0
        final_emi_options = []
        for tenure in self.TENURES_MONTHS:
            if actual_rate > 0:
                emi = self.calculate_emi(loan_amount, tenure, actual_rate)
                dti_this = round(((existing_emis + emi) / gross_monthly_income) * 100, 1)
            else:
                emi = 0
                dti_this = primary_dti
            final_emi_options.append({
                "tenure_months": tenure,
                "emi": emi,
                "dti_at_this_tenure": dti_this,
            })

        # Build response with Neo4j data if available
        result = {
            "loan_amount": loan_amount,
            "treatment_cost": total_treatment_cost,
            "coverage_ratio": self.LOAN_COVERAGE_RATIO,
            "gross_monthly_income": gross_monthly_income,
            "existing_emis": existing_emis,
            "primary_dti": round(primary_dti, 1),
            "risk_band": risk_band,
            "risk_flag": self._risk_flag(primary_dti),
            "underwriting_assessment": band_info["approval"],
            "interest_rate_range": band_info["range"],
            "call_to_action": self._call_to_action(risk_band),
            "emi_options": final_emi_options,
        }
        
        # Add Neo4j-derived fields if available
        if self.use_neo4j and hasattr(self, '_last_band_data') and self._last_band_data:
            result["neo4j_band_id"] = self._last_band_data.get("band_id")
            result["neo4j_cta"] = self._last_band_data.get("cta_text")
            result["loan_coverage_pct"] = self._last_band_data.get("loan_coverage_pct")
        
        return result

    def _classify_dti(self, dti: float) -> str:
        """Classify DTI into risk band (legacy classification)."""
        if dti < 30:
            return "low_risk"
        elif dti < 40:
            return "medium_risk"
        elif dti < 50:
            return "high_risk"
        return "critical_risk"
    
    def _neo4j_band_to_legacy(self, risk_flag: str) -> str:
        """Convert Neo4j risk_flag to legacy risk_band format."""
        mapping = {
            "LOW": "low_risk",
            "MEDIUM": "medium_risk",
            "HIGH": "high_risk",
            "CRITICAL": "critical_risk"
        }
        return mapping.get(risk_flag, "medium_risk")

    def _risk_flag(self, dti: float) -> str:
        """Get visual risk flag."""
        if dti < 30:
            return "🟢 Low Risk"
        if dti < 40:
            return "🟡 Medium Risk"
        if dti < 50:
            return "🔴 High Risk"
        return "⛔ Critical Risk"

    def _call_to_action(self, risk_band: str) -> str:
        """Get call-to-action message based on risk band."""
        ctas = {
            "low_risk": "Aap eligible hain — Apply Now",
            "medium_risk": "Proceed with Standard Application",
            "high_risk": "Flag for Manual Review",
            "critical_risk": "Recommend Alternate Financing",
        }
        return ctas[risk_band]


# =============================================================================
# Module-level DTI Calculation (TC-21 to TC-22)
# =============================================================================


def calculate_dti_band(
    monthly_income: float,
    existing_emis: float,
    loan_amount: float,
    tenure_months: int = 24,
    annual_rate: float = 14.0,
    use_neo4j: bool = True,
) -> dict:
    """
    Calculate DTI band for loan eligibility.
    
    Args:
        monthly_income: Gross monthly income
        existing_emis: Existing monthly EMI obligations
        loan_amount: Proposed loan amount
        tenure_months: Loan tenure (default 24)
        annual_rate: Annual interest rate (default 14%)
        use_neo4j: Whether to query from Neo4j graph (default True)
        
    Returns:
        Dict with risk_band, dti, interest_rate_min, cta, etc.
    """
    # Calculate EMI using standard formula
    monthly_rate = annual_rate / (12 * 100)
    if monthly_rate == 0:
        emi = loan_amount / tenure_months
    else:
        n = tenure_months
        emi = loan_amount * monthly_rate * ((1 + monthly_rate) ** n) / (((1 + monthly_rate) ** n) - 1)
    emi = round(emi)
    
    # Calculate DTI
    total_emis = existing_emis + emi
    dti = (total_emis / monthly_income) * 100 if monthly_income > 0 else 999.0
    dti = round(dti, 1)
    
    # Query Neo4j for risk band if enabled
    if use_neo4j:
        try:
            client = get_loan_client()
            band_data = client.get_risk_band_by_dti(dti)
            return {
                "dti": dti,
                "risk_band": band_data["risk_flag"],
                "emi": emi,
                "loan_amount": loan_amount,
                "interest_rate_min": band_data["interest_rate_min"],
                "interest_rate_max": band_data["interest_rate_max"],
                "cta": band_data["cta_text"],
                "approval_likelihood": band_data["approval_likelihood"],
                "loan_coverage_pct": band_data["loan_coverage_pct"],
                "from_neo4j": True,
            }
        except Exception as e:
            logger.warning(f"Neo4j query failed in calculate_dti_band: {e}")
    
    # Fallback classification
    if dti < 30:
        risk_band = "LOW"
        rate_range = (12.0, 13.0)
        cta = "Apply Now"
    elif dti < 40:
        risk_band = "MEDIUM"
        rate_range = (13.0, 15.0)
        cta = "Standard Application"
    elif dti < 50:
        risk_band = "HIGH"
        rate_range = (15.0, 16.0)
        cta = "Manual Review"
    else:
        risk_band = "CRITICAL"
        rate_range = (0.0, 0.0)
        cta = "Recommend Alternate Financing"
    
    return {
        "dti": dti,
        "risk_band": risk_band,
        "emi": emi,
        "loan_amount": loan_amount,
        "interest_rate_min": rate_range[0],
        "interest_rate_max": rate_range[1],
        "cta": cta,
    }
