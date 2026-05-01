"""
Canonical NVIDIA LLM Client.

This is the SINGLE POINT OF CONTACT for all LLM calls in the TenzorX backend.
No module may call the NVIDIA API directly — always import and call through NvidiaClient.
This enforces consistent error handling, logging, and token tracking.
"""

import os
import logging
from typing import Optional, List, Dict, Any
import requests

logger = logging.getLogger(__name__)

NVIDIA_API_URL = os.getenv(
    "NVIDIA_API_URL", 
    "https://integrate.api.nvidia.com/v1/chat/completions"
)
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MODEL = os.getenv(
    "NVIDIA_MODEL", 
    "mistralai/mistral-large-3-675b-instruct-2512"
)


class NvidiaClient:
    """
    Canonical NVIDIA LLM client. All LLM calls in TenzorX backend
    must go through this class. Supports single-turn and multi-turn calls.
    """

    def __init__(
        self,
        model: str = NVIDIA_MODEL,
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
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
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

        logger.info(f"🌐 Calling NVIDIA LLM API: {NVIDIA_API_URL}")
        try:
            response = requests.post(
                NVIDIA_API_URL, 
                headers=self.headers, 
                json=payload, 
                timeout=60
            )
            response.raise_for_status()
            logger.info(f"✅ NVIDIA LLM API response received: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ NVIDIA API request failed: {e}")
            raise RuntimeError(f"NVIDIA LLM API error: {e}") from e

        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected NVIDIA API response structure: {data}")
            raise RuntimeError("Malformed response from NVIDIA API") from e

        logger.debug(f"NvidiaClient response: {content[:200]}...")
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


# Module-level default instance for easy import
default_client = NvidiaClient()
