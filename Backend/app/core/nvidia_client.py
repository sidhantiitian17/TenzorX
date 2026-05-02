"""
Canonical Longcat AI LLM Client.

This is the SINGLE POINT OF CONTACT for all LLM calls in the TenzorX backend.
No module may call the Longcat API directly — always import and call through LLMClient.
This enforces consistent error handling, logging, and token tracking.

Uses Longcat AI with OpenAI-compatible API format.
"""

import os
import logging
from typing import Optional, List, Dict, Any
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

LONGCAT_API_URL = os.getenv(
    "LONGCAT_API_URL",
    f"{settings.LONGCAT_BASE_URL}/v1/chat/completions"
).strip().replace('\n', '')
LONGCAT_API_KEY = os.getenv("LONGCAT_API_KEY", settings.LONGCAT_API_KEY)
LONGCAT_MODEL = os.getenv(
    "LONGCAT_MODEL",
    "LongCat-Flash-Lite"
)


class LLMClient:
    """
    Canonical Longcat AI LLM client. All LLM calls in TenzorX backend
    must go through this class. Supports single-turn and multi-turn calls.
    
    Uses Longcat AI OpenAI-compatible API format.
    """
    
    # Backwards compatibility alias
    NvidiaClient = None

    def __init__(
        self,
        model: str = LONGCAT_MODEL,
        temperature: float = 0.15,
        max_tokens: int = 2048,
        top_p: float = 1.00,
        stream: bool = False,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.stream = stream
        self.headers = {
            "Authorization": f"Bearer {LONGCAT_API_KEY}",
            "Accept": "text/event-stream" if stream else "application/json",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a chat completion request to the NVIDIA API.

        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            system_prompt: Optional system message prepended as role=system
            temperature: Override instance temperature
            max_tokens: Override instance max_tokens

        Returns:
            The text content of the model's reply (stripped).

        Raises:
            RuntimeError: If the API call fails or returns non-200.
        """
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": 0.00,
            "presence_penalty": 0.00,
            "stream": self.stream,
        }

        # Check if API key is configured
        if not LONGCAT_API_KEY or LONGCAT_API_KEY == "your-longcat-api-key-here":
            error_msg = "Longcat AI API key not configured - LLM features unavailable"
            logger.warning(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"🌐 Calling Longcat AI LLM API: {LONGCAT_API_URL}")
        try:
            # Use a session with connection timeout to fail fast on DNS/SSL issues
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                max_retries=0,  # No retries for fast failure
            )
            session.mount('https://', adapter)
            session.mount('http://', adapter)
            
            response = session.post(
                LONGCAT_API_URL,
                headers=self.headers,
                json=payload,
                timeout=(0.5, 1)  # (connect timeout, read timeout) - aggressive for <10s total
            )
            response.raise_for_status()
            logger.info(f"✅ Longcat AI LLM API response received: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Longcat AI API request failed: {e}")
            raise RuntimeError(f"Longcat AI LLM API error: {e}") from e

        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Longcat AI API response structure: {data}")
            raise RuntimeError("Malformed response from Longcat AI API") from e

        logger.debug(f"LLMClient response: {content[:200]}...")
        return content

    def simple_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Convenience wrapper for a single user-turn prompt."""
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            **kwargs,
        )


# Backwards compatibility: NvidiaClient is an alias for LLMClient
NvidiaClient = LLMClient


# Module-level default instance for easy import
default_client = NvidiaClient()
