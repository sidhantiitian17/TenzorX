"""
Loan Eligibility API route.

Provides NBFC pre-underwriting evaluation.
"""

from fastapi import APIRouter
from app.schemas.request_models import LoanRequest
from app.engines.loan_engine import LoanEngine

router = APIRouter()
loan_engine = LoanEngine()


@router.post("")
async def loan_eligibility(request: LoanRequest):
    """
    Evaluate loan eligibility for healthcare financing.
    """
    result = loan_engine.evaluate(
        total_treatment_cost=request.total_treatment_cost,
        gross_monthly_income=request.gross_monthly_income,
        existing_emis=request.existing_emis,
    )
    return result
