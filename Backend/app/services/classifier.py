"""
Symptom severity classification service.

This module provides an MVP-ready heuristic classifier that maps free-text
symptoms to a discrete urgency level for routing and decision support.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal


SeverityLabel = Literal["Red", "Yellow", "Green"]

MANDATORY_MEDICAL_DISCLAIMER = (
    "This system provides decision support only and does not constitute medical advice or diagnosis"
)


@dataclass(frozen=True, slots=True)
class SeverityClassification:
    """Structured response from the symptom severity classifier."""

    severity: SeverityLabel
    rationale: str
    disclaimer: str = MANDATORY_MEDICAL_DISCLAIMER


_RED_KEYWORDS: tuple[str, ...] = (
    "chest pain",
    "radiating arm pain",
    "shortness of breath",
    "difficulty breathing",
    "loss of consciousness",
    "severe bleeding",
    "stroke",
    "facial droop",
    "slurred speech",
)

_YELLOW_KEYWORDS: tuple[str, ...] = (
    "fever",
    "vomiting",
    "persistent cough",
    "abdominal pain",
    "moderate pain",
    "swelling",
    "infection",
)


def _normalize_text(symptoms: str | Iterable[str]) -> str:
    """Normalize a symptom payload into lowercase searchable text."""

    if isinstance(symptoms, str):
        text = symptoms
    else:
        text = " ".join(symptoms)
    return " ".join(text.lower().split())


def classify_symptom_severity(symptoms: str | Iterable[str]) -> SeverityClassification:
    """Classify symptoms into Red, Yellow, or Green severity bands.

    The classifier uses deterministic heuristics so the MVP is predictable,
    testable, and easy to replace later with an ML or LangChain-based router.
    """

    normalized = _normalize_text(symptoms)

    if any(keyword in normalized for keyword in _RED_KEYWORDS):
        return SeverityClassification(
            severity="Red",
            rationale="High-risk emergency symptom pattern detected by heuristic rules.",
        )

    if any(keyword in normalized for keyword in _YELLOW_KEYWORDS):
        return SeverityClassification(
            severity="Yellow",
            rationale="Urgent symptom pattern detected by heuristic rules.",
        )

    return SeverityClassification(
        severity="Green",
        rationale="No emergency or urgent symptom pattern detected by heuristic rules.",
    )


# =============================================================================
# ICD-10 Aware Severity Classification (TC-15 to TC-17)
# =============================================================================

# ICD-10 codes that indicate emergency (RED) conditions
_RED_ICD_PREFIXES: tuple[str, ...] = (
    "I21",  # Acute myocardial infarction
    "I22",  # Subsequent myocardial infarction
    "R07.4",  # Chest pain on breathing
    "J44.1",  # COPD with acute exacerbation
    "R55",  # Syncope and collapse
)

# ICD-10 codes for elective/orthopedic procedures (GREEN)
_GREEN_ICD_PREFIXES: tuple[str, ...] = (
    "M17",  # Primary osteoarthritis (knee/hip replacement candidates)
    "M16",  # Hip osteoarthritis
    "Z98",  # Post-procedural status (follow-up visits)
)


def classify_severity(entities: list[dict], raw_text: str) -> str:
    """
    Classify severity based on ICD-10 codes and raw text.
    
    Args:
        entities: List of entity dicts with 'primary_code' key
        raw_text: Original user input text
        
    Returns:
        "RED", "YELLOW", or "GREEN"
    """
    text_lower = raw_text.lower()
    
    # Check for emergency keywords in text
    if any(keyword in text_lower for keyword in _RED_KEYWORDS):
        return "RED"
    
    # Check for emergency ICD-10 codes
    for entity in entities:
        code = entity.get("primary_code", "")
        if code and any(code.startswith(prefix) for prefix in _RED_ICD_PREFIXES):
            return "RED"
    
    # Check for elective procedure ICD-10 codes (GREEN indicators)
    for entity in entities:
        code = entity.get("primary_code", "")
        if code and any(code.startswith(prefix) for prefix in _GREEN_ICD_PREFIXES):
            return "GREEN"
    
    # Check for yellow keywords
    if any(keyword in text_lower for keyword in _YELLOW_KEYWORDS):
        return "YELLOW"
    
    # Default to YELLOW if unknown, GREEN if empty
    if entities:
        return "YELLOW"
    return "GREEN"
