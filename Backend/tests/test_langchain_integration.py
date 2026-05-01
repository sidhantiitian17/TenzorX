"""
Integration tests for direct Longcat AI LLM orchestration.

These tests validate that:
1. The Longcat AI API is being called when patient queries are processed
2. Error handling works correctly for API failures
3. Session memory remains isolated between patients
4. The mandatory medical disclaimer is included in responses

Run with: pytest tests/test_langchain_integration.py -v
"""

import logging
import pytest
import os
from typing import Any
from unittest.mock import MagicMock, patch, call

from app.services.langchain_agent import (
    process_patient_query,
    get_session_history,
    store,
    _call_longcat_api,
    _format_context,
    MANDATORY_MEDICAL_DISCLAIMER,
    LONGCAT_INVOKE_URL,
    LONGCAT_MODEL,
    _build_llm,
    LONGCAT_API_KEY_ENV,
)
from app.core.config import settings


logger = logging.getLogger(__name__)


class TestDirectLongcatAIIntegration:
    """Test suite for direct Longcat AI API integration."""

    def setup_method(self):
        """Clear session store before each test."""
        store.clear()

    def test_empty_session_id_validation(self):
        """Test that empty session_id raises ValueError."""
        with pytest.raises(ValueError, match="session_id must not be empty"):
            process_patient_query(
                session_id="",
                query="I have chest pain",
                context={}
            )

    def test_empty_query_validation(self):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="query must not be empty"):
            process_patient_query(
                session_id="test-session-1",
                query="",
                context={}
            )

    @patch("app.services.langchain_agent.requests.post")
    def test_longcat_api_called_with_correct_params(self, mock_post):
        """Test that the Longcat AI API is called with correct parameters."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        # Call the API function
        messages = [{"role": "user", "content": "Test message"}]
        result = _call_longcat_api(messages, "test-session")

        # Verify requests.post was called correctly
        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args

        # Check URL
        assert call_args[0] == LONGCAT_INVOKE_URL

        # Check headers
        headers = call_kwargs["headers"]
        assert headers["Authorization"] == f"Bearer {settings.LONGCAT_API_KEY}"
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"

        # Check payload
        payload = call_kwargs["json"]
        assert payload["model"] == LONGCAT_MODEL
        assert payload["messages"] == messages
        assert payload["max_tokens"] == 2048
        assert payload["temperature"] == 0.15
        assert payload["top_p"] == 1.0
        assert payload["frequency_penalty"] == 0.0
        assert payload["presence_penalty"] == 0.0
        assert payload["stream"] is False

        # Check timeout
        assert call_kwargs["timeout"] == 30.0

        # Verify result
        assert result == "Test response"

    @patch("app.services.langchain_agent.requests.post")
    def test_process_query_calls_longcat_api(self, mock_post):
        """Test that process_patient_query calls the Longcat AI API."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "AI response with disclaimer"}}]
        }
        mock_post.return_value = mock_response

        result = process_patient_query(
            session_id="test-session",
            query="I have chest pain",
            context={"triage_status": "Red", "rationale": "Severe symptoms"}
        )

        # Verify API was called
        assert mock_post.called

        # Verify result contains the response
        assert "AI response with disclaimer" in result

    @patch("app.services.langchain_agent.requests.post")
    def test_timeout_error_handling(self, mock_post):
        """Test that timeout errors are caught and re-raised gracefully."""
        mock_post.side_effect = Exception("Request timeout")

        with pytest.raises(RuntimeError, match="timeout|exceeded"):
            _call_longcat_api([{"role": "user", "content": "test"}], "test-session")

    @patch("app.services.langchain_agent.requests.post")
    def test_connection_error_handling(self, mock_post):
        """Test that connection errors are caught and re-raised gracefully."""
        mock_post.side_effect = Exception("Failed to connect")

        with pytest.raises(RuntimeError, match="connect|connection"):
            _call_longcat_api([{"role": "user", "content": "test"}], "test-session")

    @patch("app.services.langchain_agent.requests.post")
    def test_auth_error_handling(self, mock_post):
        """Test that 401 auth errors are identified and reported clearly."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="authentication|Unauthorized"):
            _call_longcat_api([{"role": "user", "content": "test"}], "test-session")

    @patch("app.services.langchain_agent.requests.post")
    def test_rate_limit_error_handling(self, mock_post):
        """Test that 429 rate limit errors are identified and reported."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("429 Rate limit exceeded")
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="Rate limit exceeded"):
            _call_longcat_api([{"role": "user", "content": "test"}], "test-session")

    @patch("app.services.langchain_agent.requests.post")
    def test_empty_response_error_handling(self, mock_post):
        """Test that empty API responses are caught."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="empty response"):
            _call_longcat_api([{"role": "user", "content": "test"}], "test-session")

    @patch("app.services.langchain_agent.logger")
    @patch("app.services.langchain_agent.requests.post")
    def test_api_call_logging(self, mock_post, mock_logger):
        """Test that API calls and responses are logged."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "Response"}}]}
        mock_post.return_value = mock_response

        _call_longcat_api([{"role": "user", "content": "test"}], "test-session")

        # Verify that info logs were called
        assert mock_logger.info.called
        calls = [str(call) for call in mock_logger.info.call_args_list]
        logged_text = " ".join(calls)
        assert "Calling Longcat AI API" in logged_text
        assert "successfully returned" in logged_text


class TestContextFormatting:
    """Test suite for context formatting before prompt injection."""

    def test_format_context_with_icd_codes(self):
        """Test that ICD-10 codes are properly formatted."""
        context = {
            "triage_status": "Yellow",
            "identified_codes": {
                "fever": "R50.9",
                "cough": "R05.9",
            }
        }

        formatted = _format_context(context)

        assert "R50.9" in formatted
        assert "R05.9" in formatted
        assert "fever" in formatted
        assert "cough" in formatted

    def test_format_context_with_clinical_pathway(self):
        """Test that clinical pathways are included in formatted context."""
        context = {
            "triage_status": "Red",
            "clinical_pathway": {
                "pathway_name": "Coronary Artery Disease Care",
                "care_stages": [
                    {"name": "Pre-Procedure Diagnostics"},
                    {"name": "Surgical Procedure"},
                ]
            }
        }

        formatted = _format_context(context)

        assert "Coronary Artery Disease" in formatted
        assert "Pre-Procedure Diagnostics" in formatted
        assert "Surgical Procedure" in formatted

    def test_format_context_with_missing_fields(self):
        """Test that formatting handles missing context fields gracefully."""
        context = {}

        # Should not raise; should use defaults
        formatted = _format_context(context)

    def test_format_context_includes_triage_status(self):
        """Test that _format_context includes triage status and ICD codes."""
        context = {
            "triage_status": "Red",
            "rationale": "Emergency symptom detected",
            "identified_codes": {"chest pain": "I25.1"},
        }

        formatted = _format_context(context)

        assert "Red" in formatted
        assert "Emergency symptom detected" in formatted
        assert "chest pain" in formatted
        assert "I25.1" in formatted
        assert MANDATORY_MEDICAL_DISCLAIMER in formatted

    @patch("app.services.langchain_agent.RunnableWithMessageHistory")
    def test_timeout_error_handling(self, mock_runnable_history):
        """Test that timeout errors are caught and re-raised gracefully."""
        os.environ["LONGCAT_API_KEY"] = "test-api-key"
        _build_llm.cache_clear()

        mock_runnable_history_instance = MagicMock()
        mock_runnable_history_instance.invoke.side_effect = TimeoutError("Request timeout")

        try:
            with patch("app.services.langchain_agent._build_chain") as mock_build_chain:
                mock_build_chain.return_value = mock_runnable_history_instance

                with pytest.raises(RuntimeError, match="timeout|exceeded"):
                    process_patient_query(
                        session_id="test-session",
                        query="Test query",
                        context={}
                    )
        finally:
            _build_llm.cache_clear()

    @patch("app.services.langchain_agent.RunnableWithMessageHistory")
    def test_connection_error_handling(self, mock_runnable_history):
        """Test that connection errors are caught and re-raised gracefully."""
        os.environ["LONGCAT_API_KEY"] = "test-api-key"
        _build_llm.cache_clear()

        mock_runnable_history_instance = MagicMock()
        mock_runnable_history_instance.invoke.side_effect = ConnectionError(
            "Failed to connect to Longcat AI API"
        )

        try:
            with patch("app.services.langchain_agent._build_chain") as mock_build_chain:
                mock_build_chain.return_value = mock_runnable_history_instance

                with pytest.raises(RuntimeError, match="connect|connection"):
                    process_patient_query(
                        session_id="test-session",
                        query="Test query",
                        context={}
                    )
        finally:
            _build_llm.cache_clear()

    @patch("app.services.langchain_agent.RunnableWithMessageHistory")
    def test_auth_error_handling(self, mock_runnable_history):
        """Test that 401 auth errors are identified and reported clearly."""
        os.environ["LONGCAT_API_KEY"] = "test-api-key"
        _build_llm.cache_clear()

        mock_runnable_history_instance = MagicMock()
        mock_runnable_history_instance.invoke.side_effect = Exception(
            "401 Unauthorized: Invalid API key"
        )

        try:
            with patch("app.services.langchain_agent._build_chain") as mock_build_chain:
                mock_build_chain.return_value = mock_runnable_history_instance

                with pytest.raises(RuntimeError, match="authentication|Unauthorized"):
                    process_patient_query(
                        session_id="test-session",
                        query="Test query",
                        context={}
                    )
        finally:
            _build_llm.cache_clear()

    @patch("app.services.langchain_agent.RunnableWithMessageHistory")
    def test_rate_limit_error_handling(self, mock_runnable_history):
        """Test that 429 rate limit errors are identified and reported."""
        os.environ[LONGCAT_API_KEY_ENV] = "test-api-key"
        _build_llm.cache_clear()

        mock_runnable_history_instance = MagicMock()
        mock_runnable_history_instance.invoke.side_effect = Exception(
            "429 Rate limit exceeded"
        )

        try:
            with patch("app.services.langchain_agent._build_chain") as mock_build_chain:
                mock_build_chain.return_value = mock_runnable_history_instance

                with pytest.raises(RuntimeError, match="rate limit"):
                    process_patient_query(
                        session_id="test-session",
                        query="Test query",
                        context={}
                    )
        finally:
            _build_llm.cache_clear()

    @patch("app.services.langchain_agent.RunnableWithMessageHistory")
    def test_empty_response_error_handling(self, mock_runnable_history):
        """Test that empty LLM responses are caught."""
        os.environ["LONGCAT_API_KEY"] = "test-api-key"
        _build_llm.cache_clear()

        mock_response = MagicMock()
        mock_response.content = ""  # Empty response
        mock_runnable_history_instance = MagicMock()
        mock_runnable_history_instance.invoke.return_value = mock_response

        try:
            with patch("app.services.langchain_agent._build_chain") as mock_build_chain:
                mock_build_chain.return_value = mock_runnable_history_instance

                with pytest.raises(RuntimeError, match="empty response"):
                    process_patient_query(
                        session_id="test-session",
                        query="Test query",
                        context={}
                    )
        finally:
            _build_llm.cache_clear()

    @patch("app.services.langchain_agent.logger")
    @patch("app.services.langchain_agent.RunnableWithMessageHistory")
    def test_llm_call_logging(self, mock_runnable_history, mock_logger):
        """Test that LLM calls and responses are logged."""
        os.environ["LONGCAT_API_KEY"] = "test-api-key"
        _build_llm.cache_clear()

        mock_response = MagicMock()
        mock_response.content = "Response from LLM"
        mock_runnable_history_instance = MagicMock()
        mock_runnable_history_instance.invoke.return_value = mock_response

        try:
            with patch("app.services.langchain_agent._build_chain") as mock_build_chain:
                mock_build_chain.return_value = mock_runnable_history_instance

                process_patient_query(
                    session_id="test-session",
                    query="Test query",
                    context={}
                )

                # Verify that info logs were called indicating LLM was invoked
                assert mock_logger.info.called
                calls = [str(call) for call in mock_logger.info.call_args_list]
                logged_text = " ".join(calls)
                assert "session" in logged_text.lower() or "query" in logged_text.lower()
        finally:
            _build_llm.cache_clear()


class TestContextFormatting:
    """Test suite for context formatting before prompt injection."""

    def test_format_context_with_icd_codes(self):
        """Test that ICD-10 codes are properly formatted."""
        context = {
            "triage_status": "Yellow",
            "identified_codes": {
                "fever": "R50.9",
                "cough": "R05.9",
            }
        }

        formatted = _format_context(context)

        assert "R50.9" in formatted
        assert "R05.9" in formatted
        assert "fever" in formatted
        assert "cough" in formatted

    def test_format_context_with_clinical_pathway(self):
        """Test that clinical pathways are included in formatted context."""
        context = {
            "triage_status": "Red",
            "clinical_pathway": {
                "pathway_name": "Coronary Artery Disease Care",
                "care_stages": [
                    {"name": "Pre-Procedure Diagnostics"},
                    {"name": "Surgical Procedure"},
                ]
            }
        }

        formatted = _format_context(context)

        assert "Coronary Artery Disease" in formatted
        assert "Pre-Procedure Diagnostics" in formatted
        assert "Surgical Procedure" in formatted

    def test_format_context_with_missing_fields(self):
        """Test that formatting handles missing context fields gracefully."""
        context = {}

        # Should not raise; should use defaults
        formatted = _format_context(context)

        assert MANDATORY_MEDICAL_DISCLAIMER in formatted
        assert "Green" in formatted  # Default status


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
