"""
Agents module for LangChain-based AI agents.

Provides conversational memory, severity classification, and the main healthcare agent.
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

__all__ = [
    "get_session_history",
    "get_session_messages_as_dicts",
    "add_user_message",
    "add_ai_message",
    "clear_session",
    "SeverityClassifier",
    "EMERGENCY_KEYWORDS",
    "HealthcareAgent",
    "AGENT_SYSTEM_PROMPT",
]
