"""
EMI Calculator API route.

Standalone endpoint for real-time EMI calculation (called by frontend sliders).
Per instructionagent.md Section 6: POST /api/emi-calculate
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.response_models import EMIRequest, EMIResponse
from app.engines.loan_engine import LoanEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/emi-calculate", tags=["EMI Calculator"])
loan_engine = LoanEngine()


@router.post(
    "",
    response_model=EMIResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate EMI for healthcare loan",
    description="Real-time EMI recalculation for frontend sliders without going through LLM. "
                "Per instructionagent.md Section 6.",
)
async def calculate_emi(request: EMIRequest) -> EMIResponse:
    """
    Calculate EMI for a healthcare loan.
    
    Args:
        request: EMIRequest with principal, annual_rate_pct, tenure_months
        
    Returns:
        EMIResponse with monthly_emi and total_repayment
        
    Example:
        Request: {"principal": 200000, "annual_rate_pct": 12.5, "tenure_months": 24}
        Response: {"monthly_emi": 9461, "total_repayment": 227075}
    """
    try:
        logger.info(f"EMI calculation request: principal={request.principal}, rate={request.annual_rate_pct}%, tenure={request.tenure_months}mo")
        
        # Calculate EMI using loan engine
        emi = loan_engine.calculate_emi(
            principal=request.principal,
            tenure_months=request.tenure_months,
            annual_rate=request.annual_rate_pct,
        )
        
        # Calculate total repayment
        total_repayment = round(emi * request.tenure_months)
        
        logger.info(f"EMI calculated: {emi}/month, total={total_repayment}")
        
        return EMIResponse(
            monthly_emi=int(emi),
            total_repayment=total_repayment,
        )
        
    except Exception as e:
        logger.error(f"EMI calculation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"EMI calculation failed: {str(e)}",
        )


@router.get(
    "/tenure-options",
    status_code=status.HTTP_200_OK,
    summary="Get standard EMI tenure options",
    description="Returns standard tenure options (12, 24, 36 months) with current rates.",
)
async def get_tenure_options():
    """
    Get standard EMI tenure options.
    
    Returns:
        Dict with available tenures and indicative rates
    """
    return {
        "tenures": [12, 24, 36],
        "indicative_rates": {
            "low_risk": "12-13%",
            "medium_risk": "13-15%",
            "high_risk": "15-16%",
        },
        "max_loan_coverage": "80%",
        "note": "These are indicative figures. Confirm final rates with lenders.",
    }
