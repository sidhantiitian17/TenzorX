"""
Procedure Detection API Route

Real-time endpoint for detecting medical procedures from user queries.
Uses LLM to analyze queries and return structured clinical mapping.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.agents.procedure_detection_agent import get_procedure_detection_agent

logger = logging.getLogger(__name__)

# ============================================================================
# Router Configuration
# ============================================================================
router = APIRouter(
    prefix="/detect-procedure",
    tags=["Procedure Detection"],
    responses={
        500: {"description": "Internal server error"},
        422: {"description": "Validation error"},
    },
)


# ============================================================================
# Request/Response Models
# ============================================================================
class ProcedureDetectionRequest(BaseModel):
    """Request model for procedure detection."""
    query: str = Field(
        ...,
        description="User's health query or symptom description",
        min_length=1,
        max_length=1000,
        examples=["I have kidney stones and need treatment options"],
    )


class ConfidenceFactor(BaseModel):
    """Confidence factor for procedure detection."""
    key: str
    label: str
    score: int


class ProcedureDetectionResponse(BaseModel):
    """Response model for procedure detection."""
    success: bool = True
    data: Dict[str, Any] = Field(
        description="Detected procedure information",
        examples=[{
            "procedure": "Nephrolithiasis Treatment",
            "category": "Urology",
            "icd10_code": "N20.0",
            "icd10_label": "Calculus of kidney",
            "snomed_code": "9557008",
            "confidence": 0.85,
            "confidence_factors": [
                {"key": "explicit_mention", "label": "Explicit condition mention", "score": 95}
            ],
            "rationale": "User explicitly mentions kidney stones seeking treatment",
        }],
    )
    query: str


# ============================================================================
# API Endpoints
# ============================================================================
@router.post(
    "",
    response_model=ProcedureDetectionResponse,
    summary="Detect Medical Procedure",
    description="""
    Analyze a user's health query and detect the primary medical procedure.
    
    This endpoint uses LLM to:
    - Extract the primary procedure/condition from the query
    - Classify into medical category
    - Map to ICD-10 code
    - Map to SNOMED CT code
    - Provide confidence scoring
    
    Works with vague queries, symptoms, or layman's terms.
    """,
    response_description="Structured procedure detection with clinical codes",
    status_code=status.HTTP_200_OK,
)
async def detect_procedure(request: ProcedureDetectionRequest) -> ProcedureDetectionResponse:
    """
    Detect medical procedure from user query.
    
    Args:
        request: ProcedureDetectionRequest containing the user query
        
    Returns:
        ProcedureDetectionResponse with detected procedure and clinical codes
        
    Raises:
        HTTPException: If detection fails or query is invalid
    """
    try:
        logger.info(f"Procedure detection request: {request.query[:50]}...")
        
        # Get agent instance
        agent = get_procedure_detection_agent()
        
        # Perform detection
        result = agent.detect(request.query)
        
        # Build response
        response_data = {
            "procedure": result.procedure,
            "category": result.category,
            "icd10_code": result.icd10_code,
            "icd10_label": result.icd10_label,
            "snomed_code": result.snomed_code,
            "confidence": result.confidence,
            "confidence_factors": result.confidence_factors,
            "rationale": result.rationale,
        }
        
        logger.info(f"Detected procedure: {result.procedure} (confidence: {result.confidence})")
        
        return ProcedureDetectionResponse(
            success=True,
            data=response_data,
            query=request.query,
        )
        
    except Exception as e:
        logger.error(f"Procedure detection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Procedure detection failed: {str(e)}",
        )


@router.get(
    "/health",
    summary="Procedure Detection Health Check",
    description="Check if the procedure detection service is operational",
    response_description="Health status",
)
async def health_check() -> Dict[str, Any]:
    """Health check for procedure detection service."""
    try:
        agent = get_procedure_detection_agent()
        # Quick test detection
        test_result = agent.detect("test")
        
        return {
            "status": "healthy",
            "service": "procedure_detection",
            "agent_initialized": agent is not None,
            "test_detection_working": test_result.procedure is not None,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "procedure_detection",
            "error": str(e),
        }
