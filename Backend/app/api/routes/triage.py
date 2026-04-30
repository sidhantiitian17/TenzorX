"""
Triage API router.

Provides the complete MVP /triage endpoint combining heuristic classification,
mock ICD-10 mapping, LangChain Agentic responses, and Financial Engines.
"""

from __future__ import annotations
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.models.schemas import UserQueryRequest
from app.services.classifier import (
    MANDATORY_MEDICAL_DISCLAIMER,
    SeverityClassification,
    classify_symptom_severity,
)
from app.services.ner_parser import map_symptoms_to_icd10
from app.services.langchain_agent import process_patient_query
from app.services.cost_engine import calculate_estimated_cost
from app.services.nbfc_scorer import calculate_loan_eligibility

router = APIRouter(prefix="/triage", tags=["Triage"])

class TriageResponse(BaseModel):
    """Structured response returned by the triage endpoint."""
    severity: Literal["Red", "Yellow", "Green"]
    rationale: str
    disclaimer: str = Field(..., description="Mandatory medical disclaimer")
    icd10_codes: dict[str, str]
    agent_response: str
    normalized_query: str
    cost_estimate: Optional[dict] = None
    loan_eligibility: Optional[dict] = None

def _extract_symptoms(query: str) -> list[str]:
    """Extract symptom-like phrases from a natural language query."""
    normalized = " ".join(query.lower().split())
    symptom_candidates = [
        "severe chest pain", "chest pain", "radiating arm pain",
        "shortness of breath", "difficulty breathing", "fever",
        "diabetes", "hypertension", "abdominal pain", "vomiting",
        "cough", "swelling", "infection",
    ]
    extracted = [symptom for symptom in symptom_candidates if symptom in normalized]
    return extracted or [normalized]

@router.post(
    "",
    response_model=TriageResponse,
    status_code=status.HTTP_200_OK,
    summary="Run complete triage with AI and Financials",
)
async def triage_user_query(payload: UserQueryRequest) -> TriageResponse:
    """Run the MVP triage workflow, agentic response, and financial calculations."""

    if not payload.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty.",
        )

    # --- PHASE 2 & 3: CLINICAL & AI LOGIC ---
    extracted_symptoms = _extract_symptoms(payload.query)
    severity_result: SeverityClassification = classify_symptom_severity(payload.query)
    icd10_codes = map_symptoms_to_icd10(extracted_symptoms)

    context = {
        "triage_status": severity_result.severity,
        "rationale": severity_result.rationale,
        "identified_codes": icd10_codes
    }

    agent_response = process_patient_query(
        session_id="mvp-session-1", 
        query=payload.query, 
        context=context
    )

    # --- PHASE 4: FINANCIAL ENGINES ---
    cost_estimate = None
    loan_eligibility = None

    if payload.financial_profile:
        # Mock base cost for MVP (e.g., 2,50,000 INR)
        base_cost = 250000 
        comorbidities = payload.patient_profile.known_comorbidities if payload.patient_profile else []
        
        cost_estimate = calculate_estimated_cost(base_cost, comorbidities)
        
        # Calculate loan covering 80% over 24 months
        loan_amount = cost_estimate["adjusted_cost"] * 0.8
        proposed_emi = loan_amount / 24 
        
        loan_eligibility = calculate_loan_eligibility(
            gross_monthly_income=payload.financial_profile.gross_monthly_income,
            existing_emis=payload.financial_profile.existing_emis,
            proposed_medical_emi=proposed_emi
        )

    return TriageResponse(
        severity=severity_result.severity,
        rationale=severity_result.rationale,
        disclaimer=MANDATORY_MEDICAL_DISCLAIMER,
        icd10_codes=icd10_codes,
        agent_response=agent_response,
        normalized_query=" ".join(payload.query.split()),
        cost_estimate=cost_estimate,
        loan_eligibility=loan_eligibility
    )