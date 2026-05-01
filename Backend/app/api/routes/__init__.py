"""
Route collection for the API surface.

Per instructionagent.md Section 6 - All API endpoints.
"""

from .triage import router as triage_router
from .hospitals import router as hospitals_router
from .chat import router as chat_router
from .cost import router as cost_router
from .loan import router as loan_router
from .compare import router as compare_router
from .explain import router as explain_router
from .emi import router as emi_router
from .session import router as session_router
from .feedback import router as feedback_router
from .save_result import router as save_result_router
from .form_template import router as form_template_router
from .lender import router as lender_router
from .websocket import router as websocket_router

__all__ = [
    # Existing routes
    "triage_router",
    "hospitals_router",
    "chat_router",
    "cost_router",
    "loan_router",
    "compare_router",
    "explain_router",
    # New routes per instructionagent.md
    "emi_router",
    "session_router",
    "feedback_router",
    "save_result_router",
    "form_template_router",
    "lender_router",
    "websocket_router",
]
