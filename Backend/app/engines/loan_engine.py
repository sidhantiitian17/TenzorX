"""
NBFC Loan Pre-Underwriting Engine (Gap 3 Resolver).

Computes DTI ratio and assigns risk bands for healthcare loans.
Formula: DTI = (Existing_EMIs + Proposed_Medical_EMI) / Gross_Monthly_Income × 100
"""

from typing import Dict, Any, List


# Interest rate ranges by risk band
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
    """

    LOAN_COVERAGE_RATIO = 0.80  # Loan covers 80% of total estimated cost
    TENURES_MONTHS = [12, 24, 36]

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
        """
        loan_amount = round(total_treatment_cost * self.LOAN_COVERAGE_RATIO)

        # Calculate for standard 24-month tenure at median rate
        primary_emi = self.calculate_emi(loan_amount, 24, 14.0)
        primary_dti = ((existing_emis + primary_emi) / gross_monthly_income) * 100 if gross_monthly_income > 0 else 999

        risk_band = self._classify_dti(primary_dti)
        band_data = INTEREST_RATES[risk_band]

        # Recalculate EMI options with actual band rate
        actual_rate = sum(band_data["range"]) / 2 if band_data["range"][0] > 0 else 0
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

        return {
            "loan_amount": loan_amount,
            "treatment_cost": total_treatment_cost,
            "coverage_ratio": self.LOAN_COVERAGE_RATIO,
            "gross_monthly_income": gross_monthly_income,
            "existing_emis": existing_emis,
            "primary_dti": round(primary_dti, 1),
            "risk_band": risk_band,
            "risk_flag": self._risk_flag(primary_dti),
            "underwriting_assessment": band_data["approval"],
            "interest_rate_range": band_data["range"],
            "call_to_action": self._call_to_action(risk_band),
            "emi_options": final_emi_options,
        }

    def _classify_dti(self, dti: float) -> str:
        """Classify DTI into risk band."""
        if dti < 30:
            return "low_risk"
        elif dti < 40:
            return "medium_risk"
        elif dti < 50:
            return "high_risk"
        return "critical_risk"

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
