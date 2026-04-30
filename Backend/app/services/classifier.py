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
