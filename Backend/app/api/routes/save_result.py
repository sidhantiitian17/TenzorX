"""
Save Result API route.

Saves the current result set to the session's saved_results.
Per instructionagent.md Section 6: POST /api/save-result
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status

from app.schemas.response_models import SaveResultRequest, SaveResultResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/save-result", tags=["Saved Results"])

# In-memory session store (should match session.py)
_saved_results_store: Dict[str, List[Dict[str, Any]]] = {}


def get_session_saved_results(session_id: str) -> List[Dict[str, Any]]:
    """Get saved results for a session."""
    if session_id not in _saved_results_store:
        _saved_results_store[session_id] = []
    return _saved_results_store[session_id]


@router.post(
    "",
    response_model=SaveResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save current results to session",
    description="Saves the current result set to the session's saved_results. "
                "Per instructionagent.md Section 6.",
)
async def save_result(request: SaveResultRequest) -> SaveResultResponse:
    """
    Save current results to session.
    
    Stores a snapshot of the current search results for later retrieval.
    Used for the "Saved Results" sidebar feature.
    
    Args:
        request: SaveResultRequest with session_id and result_data
        
    Returns:
        SaveResultResponse with success flag and count
        
    Per instructionagent.md Section 2.1:
    Session contains: "saved_results": list[dict]
    
    Per instructionagent.md Section 5:
    - "Saved Results" sidebar section = session["saved_results"]
    """
    try:
        logger.info(f"Saving result for session {request.session_id}")
        
        # Get existing saved results
        saved_results = get_session_saved_results(request.session_id)
        
        # Create saved result entry
        saved_entry = {
            "id": f"saved_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(saved_results)}",
            "timestamp": datetime.utcnow().isoformat(),
            **request.result_data,
        }
        
        # Add to saved results
        saved_results.append(saved_entry)
        _saved_results_store[request.session_id] = saved_results
        
        logger.info(f"Result saved. Session {request.session_id} now has {len(saved_results)} saved results")
        
        return SaveResultResponse(
            success=True,
            saved_count=len(saved_results),
        )
        
    except Exception as e:
        logger.error(f"Failed to save result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save result: {str(e)}",
        )


@router.get(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Get saved results for session",
    description="Returns all saved results for the 'Saved Results' sidebar.",
)
async def get_saved_results(session_id: str):
    """
    Get saved results for a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of saved results
        
    Per instructionagent.md Section 5:
    - "Saved Results" sidebar section = session["saved_results"]
    """
    try:
        saved_results = get_session_saved_results(session_id)
        
        return {
            "session_id": session_id,
            "saved_results": saved_results,
            "count": len(saved_results),
        }
        
    except Exception as e:
        logger.error(f"Failed to get saved results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve saved results: {str(e)}",
        )


@router.delete(
    "/{session_id}/{result_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a saved result",
    description="Removes a specific saved result from the session.",
)
async def delete_saved_result(session_id: str, result_id: str):
    """
    Delete a saved result.
    
    Args:
        session_id: Session identifier
        result_id: Saved result ID to delete
        
    Returns:
        Success message
    """
    try:
        saved_results = get_session_saved_results(session_id)
        
        original_count = len(saved_results)
        _saved_results_store[session_id] = [
            r for r in saved_results if r.get("id") != result_id
        ]
        
        deleted = len(_saved_results_store[session_id]) < original_count
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved result '{result_id}' not found",
            )
        
        return {
            "success": True,
            "message": f"Saved result {result_id} removed",
            "remaining_count": len(_saved_results_store[session_id]),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete saved result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete saved result: {str(e)}",
        )
