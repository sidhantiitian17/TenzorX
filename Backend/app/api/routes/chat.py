"""
Chat API route.

Primary conversational endpoint for the healthcare agent.
"""

from fastapi import APIRouter, HTTPException
from app.schemas.request_models import ChatRequest
from app.schemas.response_models import ChatResponse
from app.agents.healthcare_agent import HealthcareAgent
from app.confidence.rag_confidence import RAGConfidenceScorer

router = APIRouter()
agent = HealthcareAgent()
confidence_scorer = RAGConfidenceScorer()


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Primary conversational endpoint.
    Accepts user message + session context, returns structured AI response.
    """
    try:
        result = agent.process(
            session_id=request.session_id,
            user_message=request.message,
            location=request.location or "",
            patient_profile=request.patient_profile.model_dump() if request.patient_profile else {},
        )

        # Score RAG confidence
        confidence = confidence_scorer.score(
            user_query=request.message,
            retrieved_context=str(result.get("search_data", {}))[:1000],
            llm_response=result.get("narrative", ""),
        )
        result["confidence"] = confidence

        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
