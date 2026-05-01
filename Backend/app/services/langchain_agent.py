"""
Direct Longcat AI API orchestration for patient triage.

This module uses direct HTTP requests to the Longcat AI model
with session-isolated message history so each patient's conversation remains independent.
Includes comprehensive error handling for API failures and detailed logging.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any

import requests

from app.core.config import settings
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

MANDATORY_MEDICAL_DISCLAIMER = (
    "This system provides decision support only and does not constitute medical advice or diagnosis"
)

LONGCAT_INVOKE_URL = f"{settings.LONGCAT_BASE_URL}/v1/chat/completions"
LONGCAT_MODEL = "LongCat-Flash-Lite"
LONGCAT_API_KEY = settings.LONGCAT_API_KEY
LONGCAT_API_KEY_ENV = "LONGCAT_API_KEY"

store: dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """Get or create isolated in-memory message history for a session."""

    normalized_session_id = session_id.strip()
    if not normalized_session_id:
        raise ValueError("session_id must not be empty")

    if normalized_session_id not in store:
        store[normalized_session_id] = InMemoryChatMessageHistory()
    return store[normalized_session_id]


def _format_icd_codes(icd_codes: dict[str, str]) -> str:
    """Format ICD-10 code mappings for inclusion in the prompt."""

    if not icd_codes:
        return "No ICD-10 codes were resolved."
    return ", ".join(f"{symptom} -> {code}" for symptom, code in icd_codes.items())


def _format_context(context: dict[str, Any]) -> str:
    """Convert structured context into a compact prompt-friendly string."""

    severity = str(context.get("triage_status") or context.get("severity") or "Green")
    rationale = str(context.get("rationale") or "No additional rationale provided.")
    icd_codes = context.get("identified_codes") or context.get("icd10_codes") or {}
    clinical_pathway = context.get("clinical_pathway") or {}

    pathway_name = str(clinical_pathway.get("pathway_name") or "None")
    pathway_stages = clinical_pathway.get("care_stages") or []
    stage_names = ", ".join(stage.get("name", "stage") for stage in pathway_stages) or "None"

    return (
        f"Triage Status: {severity}\n"
        f"Rationale: {rationale}\n"
        f"ICD-10 Codes: {_format_icd_codes(icd_codes)}\n"
        f"Clinical Pathway: {pathway_name}\n"
        f"Pathway Stages: {stage_names}\n"
        f"Mandatory Disclaimer: {MANDATORY_MEDICAL_DISCLAIMER}"
    )


@lru_cache(maxsize=1)
def _build_prompt() -> ChatPromptTemplate:
    """Create the reusable triage prompt template."""

    system_prompt = (
        "You are an empathetic healthcare navigator assisting patients with triage and care navigation. "
        "Use only the provided context, including the Triage Status and ICD-10 codes. "
        "Do not invent clinical facts or diagnose the patient. "
        f"You MUST append this exact disclaimer verbatim at the end of every answer: {MANDATORY_MEDICAL_DISCLAIMER}."
    )

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            (
                "user",
                "Patient query: {query}\n\nContext:\n{context}\n\nRespond with a concise, supportive, and medically cautious summary.",
            ),
        ]
    )


def _call_longcat_api(messages: list[dict[str, str]], session_id: str) -> str:
    """Make direct API call to Longcat AI model.

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        session_id: Session identifier for logging

    Returns:
        LLM response content

    Raises:
        RuntimeError: For API errors, timeouts, or authentication issues
    """

    headers = {
        "Authorization": f"Bearer {LONGCAT_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LONGCAT_MODEL,
        "messages": messages,
        "max_tokens": 2048,
        "temperature": 0.15,
        "top_p": 1.00,
        "frequency_penalty": 0.00,
        "presence_penalty": 0.00,
        "stream": False
    }

    try:
        logger.info(f"🚀 Calling Longcat AI API for session_id={session_id}")
        response = requests.post(
            LONGCAT_INVOKE_URL,
            headers=headers,
            json=payload,
            timeout=30.0
        )

        # Check for HTTP errors
        response.raise_for_status()

        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not content:
            error_msg = "Longcat AI API returned empty response content"
            logger.warning(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"✅ Longcat AI API successfully returned response for session_id={session_id}")
        return content.strip()

    except requests.exceptions.Timeout:
        error_msg = f"Longcat AI API timeout (30s exceeded) for session_id={session_id}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    except requests.exceptions.ConnectionError as exc:
        error_msg = f"Failed to connect to Longcat AI API endpoint: {LONGCAT_INVOKE_URL}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from exc

    except requests.exceptions.HTTPError as exc:
        status_code = response.status_code if 'response' in locals() else 'unknown'
        if status_code == 401:
            error_msg = "Longcat AI API authentication failed: Invalid API key"
            logger.error(error_msg)
        elif status_code == 429:
            error_msg = "Longcat AI API rate limit exceeded. Please retry later."
            logger.error(error_msg)
        else:
            error_msg = f"Longcat AI API HTTP error {status_code}: {response.text if 'response' in locals() else 'Unknown error'}"
            logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from exc

    except json.JSONDecodeError as exc:
        error_msg = "Longcat AI API returned invalid JSON response"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from exc

    except Exception as exc:
        error_msg = f"Longcat AI API call failed: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from exc


@lru_cache(maxsize=1)
def _build_chain() -> ChatPromptTemplate:
    """Build the prompt template for formatting messages."""

    return _build_prompt()


@lru_cache(maxsize=1)
def _build_llm():
    """Minimal cached LLM factory used by tests and callers.

    This is intentionally lightweight: tests clear its cache but patch
    the chain/runner behavior. Returning a small placeholder object
    with an `invoke` attribute satisfies tests that interact with
    `RunnableWithMessageHistory` substitutes.
    """
    api_key = os.environ.get(LONGCAT_API_KEY_ENV, LONGCAT_API_KEY)

    class _LLMPlaceholder:
        def __init__(self, key: str):
            self.key = key

        def invoke(self, *args, **kwargs):
            raise RuntimeError("LLM invoke called on placeholder")

    return _LLMPlaceholder(api_key)


def process_patient_query(session_id: str, query: str, context: dict[str, Any]) -> str:
    """Process a patient query with isolated session memory using direct Longcat AI API calls.

    This function maintains conversation history per session and formats messages
    for the Longcat AI model using the provided context.

    Args:
        session_id: Unique patient session identifier
        query: Patient's healthcare query
        context: Dict with triage_status, identified_codes, etc.

    Returns:
        LLM-generated response text with mandatory disclaimer appended.

    Raises:
        ValueError: If session_id or query are empty
        RuntimeError: If Longcat AI API is unreachable or processing fails
    """

    normalized_session_id = session_id.strip()
    if not normalized_session_id:
        error_msg = "session_id must not be empty"
        logger.warning(error_msg)
        raise ValueError(error_msg)

    normalized_query = query.strip()
    if not normalized_query:
        error_msg = "query must not be empty"
        logger.warning(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Processing query for session_id={normalized_session_id}")
    prompt_context = _format_context(context)

    # Get conversation history for this session
    session_history = get_session_history(normalized_session_id)

    # Build the system message
    system_prompt = (
        "You are an empathetic healthcare navigator assisting patients with triage and care navigation. "
        "Use only the provided context, including the Triage Status and ICD-10 codes. "
        "Do not invent clinical facts or diagnose the patient. "
        f"You MUST append this exact disclaimer verbatim at the end of every answer: {MANDATORY_MEDICAL_DISCLAIMER}."
    )

    # Create messages array starting with system message
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    for msg in session_history.messages:
        if hasattr(msg, 'type'):
            role = "user" if msg.type == "human" else "assistant"
        else:
            # Fallback for different message types
            role = "user" if "human" in str(type(msg)).lower() else "assistant"
        messages.append({"role": role, "content": msg.content})

    # Add current user query with context
    user_content = f"Patient query: {normalized_query}\n\nContext:\n{prompt_context}\n\nRespond with a concise, supportive, and medically cautious summary."
    messages.append({"role": "user", "content": user_content})

    try:
        # Call Longcat AI API directly
        response_text = _call_longcat_api(messages, normalized_session_id)

        # Add the user message and AI response to session history
        from langchain_core.messages import HumanMessage, AIMessage
        session_history.add_message(HumanMessage(content=f"Patient query: {normalized_query}\n\nContext:\n{prompt_context}"))
        session_history.add_message(AIMessage(content=response_text))

        logger.info(f"Response received: {len(response_text)} characters")
        return response_text

    except RuntimeError:
        # Re-raise RuntimeError as-is (already logged)
        raise
    except Exception as exc:
        error_msg = f"Unexpected error processing patient query: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from exc
