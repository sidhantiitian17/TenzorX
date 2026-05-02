"""
Procedure Detection Agent

Real-time LLM-powered agent that detects medical procedures from any user query,
even if the procedure is not in the predefined catalog. Returns structured
clinical mapping with ICD-10, SNOMED CT, and category.

Used as a fallback when the hardcoded procedure detection list doesn't match.
"""

import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.core.nvidia_client import NvidiaClient

logger = logging.getLogger(__name__)


@dataclass
class ProcedureDetectionResult:
    """Structured procedure detection result."""
    user_query: str
    procedure: str
    category: str
    icd10_code: str
    icd10_label: str
    snomed_code: str
    confidence: float
    confidence_factors: list
    rationale: str


PROCEDURE_DETECTION_PROMPT = """You are a medical procedure detection specialist for Indian healthcare.

TASK:
Analyze the user's health query and extract the primary medical procedure or condition.
Even if the query is vague, symptoms-only, or uses layman's terms, map it to the most
appropriate canonical medical procedure.

OUTPUT FORMAT (JSON only, no markdown):
{
    "procedure": "Canonical procedure name (e.g., Nephrolithiasis Treatment, Cardiac Catheterization)",
    "category": "Medical specialty (e.g., Urology, Cardiology, Orthopedics, General Surgery, etc.)",
    "icd10_code": "Valid ICD-10 CM code",
    "icd10_label": "Full official ICD-10 description",
    "snomed_code": "Valid SNOMED CT concept ID",
    "confidence": 0.0-1.0,
    "confidence_factors": [
        {"key": "factor_name", "label": "Human readable", "score": 0-100}
    ],
    "rationale": "Brief explanation of how you interpreted this query"
}

RULES:
1. Map vague symptom descriptions to likely procedures (e.g., "back pain with blood in urine" → "Nephrolithiasis Treatment")
2. Use standard medical terminology for procedure names
3. ICD-10 codes must be valid CM format (e.g., N20.0, I25.10)
4. SNOMED codes must be valid concept IDs (numeric)
5. Confidence < 0.5 if query is extremely vague or ambiguous
6. For unknown conditions, use best-match ICD-10 from the same body system
7. NEVER return "Unknown" - always provide your best medical mapping

EXAMPLE MAPPINGS:
- "I have kidney stones" → Nephrolithiasis Treatment, Urology, N20.0, 9557008
- "sharp pain in lower back, blood in urine" → Nephrolithiasis Treatment, Urology, N20.0, 9557008
- "chest pain and shortness of breath" → Cardiac Evaluation, Cardiology, R07.9, 29857009
- "need knee replacement surgery" → Total Knee Arthroplasty, Orthopedics, M17.11, 179344001
- " blurry vision, seeing halos" → Cataract Evaluation, Ophthalmology, H26.9, 193570009
- "stomach pain after eating spicy food" → Dyspepsia Management, Gastroenterology, K30, 162116004
- "constant headaches and dizziness" → Headache Evaluation, Neurology, R51, 25064002

Now analyze this query and respond with valid JSON only:
User Query: {user_query}
"""


class ProcedureDetectionAgent:
    """Agent for real-time procedure detection from any user query."""

    def __init__(self, nvidia_client: Optional[NvidiaClient] = None):
        self.nvidia_client = nvidia_client or NvidiaClient()
        logger.info("ProcedureDetectionAgent initialized")

    def detect(self, user_query: str) -> ProcedureDetectionResult:
        """
        Detect procedure from user query using LLM.

        Args:
            user_query: Raw user query string

        Returns:
            ProcedureDetectionResult with structured clinical mapping
        """
        if not user_query or not user_query.strip():
            return self._default_result(user_query)

        try:
            prompt = PROCEDURE_DETECTION_PROMPT.format(user_query=user_query.strip())

            logger.info(f"Detecting procedure for query: {user_query[:50]}...")

            # Call LLM via NVIDIA client
            response_text = self.nvidia_client.complete(
                system_message="You are a medical coding assistant. Return only valid JSON.",
                user_message=prompt,
                temperature=0.2,  # Lower temperature for more consistent coding
                max_tokens=500
            )

            # Parse JSON response
            result_data = self._parse_response(response_text)

            if result_data:
                return ProcedureDetectionResult(
                    user_query=user_query,
                    procedure=result_data.get("procedure", "Medical Consultation"),
                    category=result_data.get("category", "General Medicine"),
                    icd10_code=result_data.get("icd10_code", ""),
                    icd10_label=result_data.get("icd10_label", ""),
                    snomed_code=result_data.get("snomed_code", ""),
                    confidence=result_data.get("confidence", 0.5),
                    confidence_factors=result_data.get("confidence_factors", []),
                    rationale=result_data.get("rationale", "LLM-based procedure detection")
                )
            else:
                logger.warning("Failed to parse LLM response, using default")
                return self._default_result(user_query)

        except Exception as e:
            logger.error(f"Error detecting procedure: {e}")
            return self._default_result(user_query)

    def _parse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response into structured data."""
        try:
            # Clean up response - remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            text = text.strip()

            # Parse JSON
            data = json.loads(text)

            # Validate required fields
            required = ["procedure", "category", "icd10_code"]
            for field in required:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return None

            return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected parsing error: {e}")
            return None

    def _default_result(self, user_query: str) -> ProcedureDetectionResult:
        """Return default result when detection fails."""
        return ProcedureDetectionResult(
            user_query=user_query or "",
            procedure="Medical Consultation",
            category="General Medicine",
            icd10_code="Z71.9",
            icd10_label="Person encountering health services in unspecified circumstances",
            snomed_code="185424001",
            confidence=0.3,
            confidence_factors=[
                {"key": "query_unclear", "label": "Query unclear or empty", "score": 30}
            ],
            rationale="Default fallback due to detection failure or empty query"
        )


# Singleton instance for reuse
_procedure_detection_agent: Optional[ProcedureDetectionAgent] = None


def get_procedure_detection_agent() -> ProcedureDetectionAgent:
    """Get or create singleton procedure detection agent."""
    global _procedure_detection_agent
    if _procedure_detection_agent is None:
        _procedure_detection_agent = ProcedureDetectionAgent()
    return _procedure_detection_agent
