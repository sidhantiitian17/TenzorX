"""
Feedback API route.

Captures "Correct this interpretation" submissions for model improvement.
Per instructionagent.md Section 6: POST /api/feedback
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status

from app.schemas.response_models import FeedbackRequest, FeedbackResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["Feedback"])

# In-memory feedback store (replace with database in production)
_feedback_store: List[Dict[str, Any]] = []


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback for interpretation correction",
    description="Captures 'Correct this interpretation' submissions. "
                "Per instructionagent.md Section 6.",
)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Submit feedback for a procedure mapping.
    
    Captures user corrections when the AI's interpretation of their query
    was incorrect. Used for model improvement.
    
    Args:
        request: FeedbackRequest with session_id, original_query, 
                 mapped_procedure, user_correction
                 
    Returns:
        FeedbackResponse with success status
        
    Per instructionagent.md Section 6:
    Request:
    {
      "session_id": "abc-123",
      "original_query": "Knee replacement near Nagpur",
      "mapped_procedure": "Total Knee Arthroplasty (TKA)",
      "user_correction": "Actually I meant partial knee replacement"
    }
    """
    try:
        logger.info(f"Feedback received from session {request.session_id}")
        logger.info(f"Original query: '{request.original_query}'")
        logger.info(f"Mapped: '{request.mapped_procedure}' → Correction: '{request.user_correction}'")
        
        # Store feedback
        feedback_entry = {
            "session_id": request.session_id,
            "original_query": request.original_query,
            "mapped_procedure": request.mapped_procedure,
            "user_correction": request.user_correction,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "received",
        }
        
        _feedback_store.append(feedback_entry)
        
        # In production: Send to feedback queue, analytics, etc.
        # Example: await send_to_feedback_queue(feedback_entry)
        
        logger.info(f"Feedback stored successfully. Total feedback: {len(_feedback_store)}")
        
        return FeedbackResponse(
            success=True,
            message="Thank you! Your feedback helps us improve. The correction has been recorded.",
        )
        
    except Exception as e:
        logger.error(f"Failed to store feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feedback: {str(e)}",
        )


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="Get feedback statistics",
    description="Returns statistics about submitted feedback (admin use).",
)
async def get_feedback_stats():
    """
    Get feedback statistics.
    
    Returns:
        Dict with total feedback count and recent corrections
    """
    try:
        total = len(_feedback_store)
        
        # Get recent corrections (last 10)
        recent = _feedback_store[-10:] if _feedback_store else []
        
        return {
            "total_feedback_received": total,
            "recent_corrections": [
                {
                    "timestamp": f["timestamp"],
                    "original": f["mapped_procedure"],
                    "correction": f["user_correction"],
                }
                for f in recent
            ],
        }
        
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback stats: {str(e)}",
        )
