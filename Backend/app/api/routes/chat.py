"""
Chat API route - Master Orchestrator Integration.

Primary conversational endpoint using the Master Orchestrator per instructionagent.md Section 4.
This endpoint provides the full Master Response Schema with all 7 agents.
"""

import logging
from fastapi import APIRouter, HTTPException
from app.schemas.request_models import ChatRequest
from app.schemas.response_models import MasterResponse
from app.agents.master_orchestrator import get_master_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
orchestrator = get_master_orchestrator()


@router.post("", response_model=MasterResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Master Orchestrator Chat Endpoint.
    
    Per instructionagent.md Section 4.3 - Master Response Schema:
    - Orchestrates all 7 agents: NER+Triage, Clinical Pathway, Hospital Discovery,
      Financial Engine, Geo-Spatial, XAI Explainer, Appointment & Paperwork
    - Returns structured response with full context for frontend rendering
    
    Args:
        request: ChatRequest with message, session_id, location, patient_profile
        
    Returns:
        MasterResponse with complete agent outputs
    """
    logger.info(f"📝 Master Orchestrator request: session={request.session_id}, message='{request.message[:50]}...'")
    
    try:
        # Process through Master Orchestrator
        result = orchestrator.process(
            session_id=request.session_id,
            user_message=request.message,
            location=request.location or "",
            patient_profile=request.patient_profile.model_dump() if request.patient_profile else {},
        )
        
        logger.info(f"✅ Master Orchestrator complete: {len(result.chat_response.message)} chars, "
                     f"triage={result.chat_response.triage_level}, "
                     f"hospitals={len(result.results_panel.hospitals.hospitals) if result.results_panel.hospitals else 0}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Master Orchestrator failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")
