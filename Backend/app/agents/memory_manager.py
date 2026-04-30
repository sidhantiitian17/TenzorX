"""
Session Memory Manager.

Manages per-session conversation memory using LangChain's InMemoryChatMessageHistory.
Ensures complete session isolation to prevent cross-user state leakage.
"""

from typing import Dict, List
import logging

try:
    from langchain_core.chat_history import InMemoryChatMessageHistory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Fallback implementation
    class InMemoryChatMessageHistory:
        def __init__(self):
            self.messages = []
        
        def add_user_message(self, content: str):
            from langchain_core.messages import HumanMessage
            self.messages.append(HumanMessage(content=content))
        
        def add_ai_message(self, content: str):
            from langchain_core.messages import AIMessage
            self.messages.append(AIMessage(content=content))

logger = logging.getLogger(__name__)

# Global session store — keyed by unique session_id
# This prevents cross-session state leakage in concurrent users
_session_store: Dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """
    Retrieve or create an isolated message history for this session.
    
    IMPORTANT: Each session_id gets its own InMemoryChatMessageHistory instance.
    This prevents cross-talk between concurrent users.
    
    Args:
        session_id: Unique session identifier (e.g., UUID from frontend)
        
    Returns:
        InMemoryChatMessageHistory instance for this session
    """
    if session_id not in _session_store:
        _session_store[session_id] = InMemoryChatMessageHistory()
        logger.debug(f"Created new session history: {session_id}")
    return _session_store[session_id]


def clear_session(session_id: str) -> None:
    """
    Clear conversation history for a session (on explicit reset).
    
    Args:
        session_id: Session to clear
    """
    if session_id in _session_store:
        del _session_store[session_id]
        logger.info(f"Cleared session: {session_id}")


def get_session_messages_as_dicts(session_id: str) -> List[Dict[str, str]]:
    """
    Export session messages in NVIDIA API format.
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of messages as [{"role": "user"|"assistant", "content": "..."}]
    """
    history = get_session_history(session_id)
    result = []
    
    for msg in history.messages:
        # Handle different message types from LangChain
        msg_type = getattr(msg, 'type', 'unknown')
        if msg_type == 'human':
            role = 'user'
        elif msg_type == 'ai':
            role = 'assistant'
        else:
            continue
            
        content = getattr(msg, 'content', str(msg))
        result.append({"role": role, "content": content})
    
    return result


def add_user_message(session_id: str, content: str) -> None:
    """
    Add a user message to session history.
    
    Args:
        session_id: Session identifier
        content: Message content
    """
    get_session_history(session_id).add_user_message(content)


def add_ai_message(session_id: str, content: str) -> None:
    """
    Add an AI message to session history.
    
    Args:
        session_id: Session identifier
        content: Message content
    """
    get_session_history(session_id).add_ai_message(content)


def get_session_count() -> int:
    """Get the number of active sessions (for monitoring)."""
    return len(_session_store)


def list_active_sessions() -> List[str]:
    """List all active session IDs (for admin/debugging)."""
    return list(_session_store.keys())
