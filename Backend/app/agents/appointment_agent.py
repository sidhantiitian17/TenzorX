"""
AGENT 7 — Appointment & Paperwork Agent

Generates procedure-specific appointment checklists, form templates, and manages
appointment requests stored in session.

Per instructionagent.md Section 3.7
"""

import uuid
import logging
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime

from app.core.nvidia_client import NvidiaClient
from app.schemas.response_models import (
    AppointmentChecklist,
    AppointmentRequest,
    AppointmentPaperworkOutput,
    ChecklistForm,
)

logger = logging.getLogger(__name__)

# In-memory session storage for appointments (replace with Redis in production)
_appointment_store: Dict[str, List[AppointmentRequest]] = {}

CHECKLIST_GENERATION_PROMPT = """You are a healthcare preparation assistant for Indian patients.

For a patient undergoing {procedure} at a {tier} hospital in India, generate:

1. A document checklist (5-7 items, India-specific)
2. Three questions the patient should ask their doctor
3. Three common forms they may need to fill

Consider:
- Insurance/TPA requirements
- Government ID requirements (Aadhaar, PAN)
- Medical history documents
- Financial documentation for loans/schemes
- Pre-op test reports

Output ONLY valid JSON in this exact format:
{{
  "documents": ["item 1", "item 2", ...],
  "questions": ["question 1", "question 2", ...],
  "forms": [{{"name": "form name", "generate_url": "/api/form-template/form-name"}}, ...]
}}

Do not include any other text outside the JSON."""


class AppointmentAgent:
    """
    Appointment & Paperwork Agent.
    
    Generates checklists and manages appointment requests per instructionagent.md Section 3.7.
    """

    # Form template mapping
    FORM_TEMPLATES = {
        "patient_registration": "/api/form-template/patient_registration",
        "medical_history_declaration": "/api/form-template/medical_history_declaration",
        "consent_for_surgery": "/api/form-template/consent_for_surgery",
        "insurance_pre_auth": "/api/form-template/insurance_pre_auth",
    }

    def __init__(self):
        self.llm = NvidiaClient(temperature=0.2, max_tokens=1024)

    def generate_checklist(
        self,
        procedure: str,
        tier: str = "mid-tier",
    ) -> AppointmentChecklist:
        """
        Generate appointment checklist using LLM.
        
        Args:
            procedure: Canonical procedure name
            tier: Hospital tier (budget, mid-tier, premium)
            
        Returns:
            AppointmentChecklist with documents, questions, and forms
        """
        prompt = CHECKLIST_GENERATION_PROMPT.format(
            procedure=procedure,
            tier=tier,
        )

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You generate structured healthcare preparation checklists for Indian patients.",
            )
            
            # Parse JSON from response
            import json
            try:
                data = json.loads(response.strip())
                return AppointmentChecklist(
                    documents=data.get("documents", []),
                    questions=data.get("questions", []),
                    forms=[ChecklistForm(**f) for f in data.get("forms", [])],
                )
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM checklist response: {response}")
                return self._fallback_checklist(procedure)
                
        except Exception as e:
            logger.error(f"LLM checklist generation failed: {e}")
            return self._fallback_checklist(procedure)

    def _fallback_checklist(self, procedure: str) -> AppointmentChecklist:
        """Fallback checklist when LLM fails."""
        return AppointmentChecklist(
            documents=[
                "Government-issued photo ID (Aadhaar/PAN/Passport)",
                "Previous medical records and test reports",
                "Insurance card/policy document (if applicable)",
                "Income certificate for government scheme eligibility",
                "Recent passport-size photographs (2-4)",
                "Referral letter from primary care doctor (if required)",
            ],
            questions=[
                f"What are the success rates for {procedure} at this hospital?",
                "What are the potential complications and how are they managed?",
                "How long is the typical recovery period and what post-op care is needed?",
            ],
            forms=[
                ChecklistForm(name="Patient Registration Form", generate_url=self.FORM_TEMPLATES["patient_registration"]),
                ChecklistForm(name="Medical History Declaration", generate_url=self.FORM_TEMPLATES["medical_history_declaration"]),
                ChecklistForm(name="Consent for Surgery/Procedure", generate_url=self.FORM_TEMPLATES["consent_for_surgery"]),
            ],
        )

    def create_appointment_request(
        self,
        session_id: str,
        doctor_name: str,
        hospital_name: str,
        date: str,
        time: str,
        procedure: str,
    ) -> AppointmentRequest:
        """
        Create a new appointment request and store in session.
        
        Args:
            session_id: User session identifier
            doctor_name: Name of the doctor
            hospital_name: Name of the hospital
            date: Appointment date (e.g., "Fri, 17 Apr")
            time: Appointment time (e.g., "12:30 PM")
            procedure: Procedure name
            
        Returns:
            Created AppointmentRequest
        """
        appointment = AppointmentRequest(
            id=f"appt_{uuid.uuid4().hex[:8]}",
            doctor_name=doctor_name,
            hospital_name=hospital_name,
            date=date,
            time=time,
            status="requested",
            procedure=procedure,
        )

        # Store in session
        if session_id not in _appointment_store:
            _appointment_store[session_id] = []
        _appointment_store[session_id].append(appointment)

        logger.info("Created appointment request")
        return appointment

    def update_appointment_status(
        self,
        session_id: str,
        appointment_id: str,
        status: Literal["requested", "confirmed", "cancelled"],
    ) -> Optional[AppointmentRequest]:
        """
        Update appointment status.
        
        Args:
            session_id: User session identifier
            appointment_id: Appointment to update
            status: New status
            
        Returns:
            Updated AppointmentRequest or None if not found
        """
        if session_id not in _appointment_store:
            return None

        for appt in _appointment_store[session_id]:
            if appt.id == appointment_id:
                appt.status = status
                logger.info("Updated appointment status")
                return appt

        return None

    def get_appointments(
        self,
        session_id: str,
        status: Optional[str] = None,
    ) -> List[AppointmentRequest]:
        """
        Get appointments for a session.
        
        Args:
            session_id: User session identifier
            status: Optional filter by status
            
        Returns:
            List of AppointmentRequest
        """
        if session_id not in _appointment_store:
            return []

        appointments = _appointment_store[session_id]
        if status:
            appointments = [a for a in appointments if a.status == status]

        return appointments

    def get_requested_count(self, session_id: str) -> int:
        """
        Get count of requested appointments for sidebar badge.
        
        Args:
            session_id: User session identifier
            
        Returns:
            Count of appointments with status "requested"
        """
        return len(self.get_appointments(session_id, status="requested"))

    def delete_appointment(
        self,
        session_id: str,
        appointment_id: str,
    ) -> bool:
        """
        Delete (remove) an appointment from session.
        
        Args:
            session_id: User session identifier
            appointment_id: Appointment to remove
            
        Returns:
            True if deleted, False if not found
        """
        if session_id not in _appointment_store:
            return False

        original_count = len(_appointment_store[session_id])
        _appointment_store[session_id] = [
            a for a in _appointment_store[session_id] 
            if a.id != appointment_id
        ]
        
        deleted = len(_appointment_store[session_id]) < original_count
        if deleted:
            logger.info(f"Deleted appointment {appointment_id} from session {session_id}")
        
        return deleted

    def process(
        self,
        session_id: str,
        procedure: str,
        tier: str = "mid-tier",
        action: str = "checklist",
        **kwargs,
    ) -> AppointmentPaperworkOutput:
        """
        Main processing method for the agent.
        
        Args:
            session_id: User session identifier
            procedure: Canonical procedure name
            tier: Hospital tier
            action: Action to perform (checklist, create, update, list)
            **kwargs: Additional action-specific parameters
            
        Returns:
            AppointmentPaperworkOutput
        """
        checklist = self.generate_checklist(procedure, tier)
        appointments = self.get_appointments(session_id)

        # Handle specific actions
        if action == "create":
            self.create_appointment_request(
                session_id=session_id,
                doctor_name=kwargs.get("doctor_name", ""),
                hospital_name=kwargs.get("hospital_name", ""),
                date=kwargs.get("date", ""),
                time=kwargs.get("time", ""),
                procedure=procedure,
            )
            appointments = self.get_appointments(session_id)

        elif action == "update":
            self.update_appointment_status(
                session_id=session_id,
                appointment_id=kwargs.get("appointment_id", ""),
                status=kwargs.get("status", "requested"),
            )
            appointments = self.get_appointments(session_id)

        elif action == "delete":
            self.delete_appointment(
                session_id=session_id,
                appointment_id=kwargs.get("appointment_id", ""),
            )
            appointments = self.get_appointments(session_id)

        return AppointmentPaperworkOutput(
            checklist=checklist,
            appointment_requests=appointments,
        )


# =============================================================================
# Module-level convenience functions
# =============================================================================

def get_appointment_agent() -> AppointmentAgent:
    """Get singleton instance of AppointmentAgent."""
    return AppointmentAgent()


def get_session_appointments(session_id: str) -> List[AppointmentRequest]:
    """Get all appointments for a session."""
    agent = get_appointment_agent()
    return agent.get_appointments(session_id)


def get_requested_appointment_count(session_id: str) -> int:
    """Get count of requested appointments for sidebar badge."""
    agent = get_appointment_agent()
    return agent.get_requested_count(session_id)
