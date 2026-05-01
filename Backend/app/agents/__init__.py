"""
Agents module for LangChain-based AI agents.

Provides conversational memory, severity classification, and the main healthcare agent.
Per instructionagent.md specification.
"""

from app.agents.memory_manager import (
    get_session_history,
    get_session_messages_as_dicts,
    add_user_message,
    add_ai_message,
    clear_session,
)
from app.agents.severity_classifier import SeverityClassifier, EMERGENCY_KEYWORDS
from app.agents.healthcare_agent import HealthcareAgent, AGENT_SYSTEM_PROMPT
from app.agents.geo_spatial_agent import GeoSpatialAgent, geocode_city, get_city_tier
from app.agents.xai_explainer_agent import XAIExplainerAgent, explain_hospital_fusion_score
from app.agents.appointment_agent import AppointmentAgent, get_session_appointments
from app.agents.master_orchestrator import MasterOrchestrator, get_master_orchestrator

__all__ = [
    # Memory management
    "get_session_history",
    "get_session_messages_as_dicts",
    "add_user_message",
    "add_ai_message",
    "clear_session",
    # Agents
    "SeverityClassifier",
    "EMERGENCY_KEYWORDS",
    "HealthcareAgent",
    "AGENT_SYSTEM_PROMPT",
    "GeoSpatialAgent",
    "geocode_city",
    "get_city_tier",
    "XAIExplainerAgent",
    "explain_hospital_fusion_score",
    "AppointmentAgent",
    "get_session_appointments",
    "MasterOrchestrator",
    "get_master_orchestrator",
]
