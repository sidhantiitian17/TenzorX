"""
NBFC-style loan pre-underwriting engine.

This module computes a debt-to-income ratio and assigns a risk band with an
interest-rate range and call-to-action for the medical financing workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


RiskBand = Literal["Low Risk", "Medium Risk", "High Risk", "Critical Risk"]


@dataclass(frozen=True, slots=True)
class LoanEligibilityResult:
    """Structured underwriting result for the NBFC financing workflow."""

    dti_ratio: float
    risk_band: RiskBand
    estimated_interest: str
    call_to_action: str


def _validate_positive_number(value: float, field_name: str) -> float:
    """Validate that a monetary input is a positive number."""

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0")
    return float(value)


def _resolve_risk_band(dti_ratio: float) -> LoanEligibilityResult:
    """Map the DTI ratio to a risk band, interest range, and CTA."""

    if dti_ratio < 30:
        return LoanEligibilityResult(
            dti_ratio=round(dti_ratio, 2),
            risk_band="Low Risk",
            estimated_interest="12%-13%",
            call_to_action="Apply Now",
        )

    if dti_ratio < 40:
        return LoanEligibilityResult(
            dti_ratio=round(dti_ratio, 2),
            risk_band="Medium Risk",
            estimated_interest="13%-15%",
            call_to_action="Standard Application",
        )

    if dti_ratio <= 50:
        return LoanEligibilityResult(
            dti_ratio=round(dti_ratio, 2),
            risk_band="High Risk",
            estimated_interest="15%-16%",
            call_to_action="Manual Review",
        )

    return LoanEligibilityResult(
        dti_ratio=round(dti_ratio, 2),
        risk_band="Critical Risk",
        estimated_interest="N/A",
        call_to_action="Alternate Financing",
    )


def calculate_dti_and_risk_band(
    gross_monthly_income: float,
    existing_emis: float,
    proposed_medical_emi: float,
) -> dict[str, Any]:
    """Calculate debt-to-income ratio and NBFC risk band.

    The calculation follows the exact formula requested:
    DTI = ((Existing_EMIs + Proposed_Medical_EMI) / Gross_Monthly_Income) * 100
    """

    income = _validate_positive_number(gross_monthly_income, "gross_monthly_income")
    existing_emi = max(0.0, float(existing_emis))
    proposed_emi = _validate_positive_number(proposed_medical_emi, "proposed_medical_emi")

    dti_ratio = ((existing_emi + proposed_emi) / income) * 100
    band = _resolve_risk_band(dti_ratio)

    return {
        "dti_ratio": band.dti_ratio,
        "risk_band": band.risk_band,
        "estimated_interest": band.estimated_interest,
        "call_to_action": band.call_to_action,
    }
