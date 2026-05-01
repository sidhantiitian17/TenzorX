"""
Session Management API routes.

Per instructionagent.md Section 6:
- GET /api/session/{session_id} - Returns current session state
- PATCH /api/session/{session_id}/appointment - Updates appointment status
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status

from app.schemas.response_models import (
    SessionState,
    AppointmentStatusUpdate,
    AppointmentUpdateResponse,
    PatientProfile,
    UserLocation,
)
from app.agents.memory_manager import get_session_messages_as_dicts
from app.agents.appointment_agent import get_appointment_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/session", tags=["Session Management"])

# In-memory session store (replace with Redis in production)
_session_store: Dict[str, Dict[str, Any]] = {}


def get_or_create_session(session_id: str) -> Dict[str, Any]:
    """Get existing session or create new one."""
    if session_id not in _session_store:
        _session_store[session_id] = {
            "session_id": session_id,
            "user_location": None,
            "patient_profile": {
                "age": None,
                "comorbidities": [],
                "budget_inr": None,
                "insurance": False,
            },
            "conversation_history": [],
            "last_procedure": None,
            "last_results": None,
            "saved_results": [],
            "appointment_requests": [],
        }
    return _session_store[session_id]


@router.get(
    "/{session_id}",
    response_model=SessionState,
    status_code=status.HTTP_200_OK,
    summary="Get session state",
    description="Returns current session state for frontend hydration on refresh. "
                "Per instructionagent.md Section 6.",
)
async def get_session(session_id: str) -> SessionState:
    """
    Get current session state.
    
    Args:
        session_id: Session identifier
        
    Returns:
        SessionState with all session data
        
    Per instructionagent.md Section 2.1 - Session schema:
    {
        "session_id": "uuid-v4",
        "user_location": {"city": str, "state": str, "lat": float, "lng": float},
        "patient_profile": {"age": int, "comorbidities": list, "budget_inr": int, "insurance": bool},
        "conversation_history": [],
        "last_procedure": str | None,
        "last_results": dict | None,
        "saved_results": list[dict],
        "appointment_requests": list[dict]
    }
    """
    try:
        logger.info(f"Getting session state for: {session_id}")
        
        session_data = get_or_create_session(session_id)
        
        # Get conversation history from memory manager
        conversation_history = get_session_messages_as_dicts(session_id)
        
        # Get appointments from appointment agent
        appointment_agent = get_appointment_agent()
        appointments = appointment_agent.get_appointments(session_id)
        
        # Build session state
        return SessionState(
            session_id=session_id,
            user_location=session_data.get("user_location"),
            patient_profile=PatientProfile(**session_data.get("patient_profile", {})),
            conversation_history=conversation_history,
            last_procedure=session_data.get("last_procedure"),
            last_results=session_data.get("last_results"),
            saved_results=session_data.get("saved_results", []),
            appointment_requests=appointments,
        )
        
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}",
        )


@router.patch(
    "/{session_id}/appointment",
    response_model=AppointmentUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update appointment status",
    description="Updates an appointment request status (requested → confirmed → cancelled). "
                "Per instructionagent.md Section 6.",
)
async def update_appointment_status(
    session_id: str,
    update: AppointmentStatusUpdate,
) -> AppointmentUpdateResponse:
    """
    Update appointment status.
    
    Args:
        session_id: Session identifier
        update: AppointmentStatusUpdate with appointment_id and new status
        
    Returns:
        AppointmentUpdateResponse with success flag and updated appointment
        
    Per instructionagent.md Section 6:
    Request: {"appointment_id": "appt_001", "status": "confirmed"}
    """
    try:
        logger.info("Updating appointment status")
        
        appointment_agent = get_appointment_agent()
        
        # Update status
        updated_appointment = appointment_agent.update_appointment_status(
            session_id=session_id,
            appointment_id=update.appointment_id,
            status=update.status,
        )
        
        if not updated_appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment '{update.appointment_id}' not found in session '{session_id}'",
            )
        
        logger.info("Appointment updated successfully")
        
        return AppointmentUpdateResponse(
            success=True,
            appointment=updated_appointment,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update appointment: {str(e)}",
        )


@router.delete(
    "/{session_id}/appointment/{appointment_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete (remove) an appointment",
    description="Permanently removes an appointment request from the session.",
)
async def delete_appointment(session_id: str, appointment_id: str):
    """
    Delete an appointment request.
    
    Args:
        session_id: Session identifier
        appointment_id: Appointment to remove
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Deleting appointment {appointment_id} from session {session_id}")
        
        appointment_agent = get_appointment_agent()
        deleted = appointment_agent.delete_appointment(session_id, appointment_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment '{appointment_id}' not found",
            )
        
        return {"success": True, "message": f"Appointment {appointment_id} removed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete appointment: {str(e)}",
        )


@router.get(
    "/{session_id}/appointments/requested-count",
    status_code=status.HTTP_200_OK,
    summary="Get count of requested appointments",
    description="Returns the badge count for 'My Appointment Requests' sidebar. "
                "Per instructionagent.md Section 5 - UI binding.",
)
async def get_requested_appointment_count(session_id: str):
    """
    Get count of appointments with status 'requested' for sidebar badge.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Dict with count
    """
    try:
        appointment_agent = get_appointment_agent()
        count = appointment_agent.get_requested_count(session_id)
        
        return {"count": count, "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Failed to get appointment count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get appointment count: {str(e)}",
        )


@router.post(
    "/{session_id}/location",
    status_code=status.HTTP_200_OK,
    summary="Update session location",
    description="Updates user location in session (from 'Add Location' chip).",
)
async def update_session_location(session_id: str, location: UserLocation):
    """
    Update user location in session.
    
    Args:
        session_id: Session identifier
        location: UserLocation with city, state, lat, lng
        
    Returns:
        Updated session
    """
    try:
        session_data = get_or_create_session(session_id)
        session_data["user_location"] = location.dict()
        
        logger.info(f"Updated location for session {session_id}: {location.city}")
        
        return {"success": True, "location": location.dict()}
        
    except Exception as e:
        logger.error(f"Failed to update location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update location: {str(e)}",
        )


@router.post(
    "/{session_id}/patient-profile",
    status_code=status.HTTP_200_OK,
    summary="Update patient profile",
    description="Updates patient profile in session (from 'Patient Details' chip).",
)
async def update_patient_profile(session_id: str, profile: PatientProfile):
    """
    Update patient profile in session.
    
    Args:
        session_id: Session identifier
        profile: PatientProfile with age, comorbidities, budget_inr, insurance
        
    Returns:
        Updated session
    """
    try:
        session_data = get_or_create_session(session_id)
        session_data["patient_profile"] = profile.dict()
        
        logger.info(f"Updated patient profile for session {session_id}")
        
        return {"success": True, "profile": profile.dict()}
        
    except Exception as e:
        logger.error(f"Failed to update patient profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update patient profile: {str(e)}",
        )
