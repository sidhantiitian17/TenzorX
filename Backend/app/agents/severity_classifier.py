"""
Symptom Severity Classifier (Gap Resolver).

Classifies user queries as RED (Emergency), YELLOW (Urgent), or GREEN (Elective).
Uses two-stage approach: keyword override + LLM classification.
"""

import re
import logging
from typing import Set

from app.core.nvidia_client import NvidiaClient

logger = logging.getLogger(__name__)

# Emergency keywords that always trigger RED
EMERGENCY_KEYWORDS: Set[str] = {
    "chest pain", "heart attack", "stroke", "unconscious", "unresponsive",
    "heavy bleeding", "can't breathe", "cannot breathe", "shortness of breath sudden",
    "severe pain", "collapse", "collapsed", "paralysis", "sudden numbness",
    "vision loss", "loss of consciousness", "difficulty breathing",
    "radiating pain left arm", "jaw pain", "cardiac arrest", "heart failure",
    "seizure", "convulsions", "poisoning", "overdose", "suicide",
    "severe burn", "choking", "drowning", "electrocution",
    "gunshot", "stab wound", "head trauma", "skull fracture",
}

SEVERITY_SYSTEM_PROMPT = """You are a medical triage classifier. Classify the patient's input into EXACTLY one of:
- RED: Life-threatening emergency requiring immediate care (call 112)
- YELLOW: Urgent, needs care within 24-48 hours
- GREEN: Elective, can be planned at convenience

Return ONLY the word RED, YELLOW, or GREEN. Nothing else.

Examples:
"chest pain radiating to left arm" -> RED
"severe headache and vomiting for 3 hours" -> YELLOW
"knee replacement cost in Nagpur" -> GREEN
"high fever for 2 days" -> YELLOW
"want to know about diabetes management" -> GREEN
"unconscious patient" -> RED"""


class SeverityClassifier:
    """Two-stage symptom severity classifier."""

    def __init__(self):
        self.llm = NvidiaClient(temperature=0.0, max_tokens=10)

    def classify(self, user_text: str) -> str:
        """Returns 'RED', 'YELLOW', or 'GREEN'. RED always overrides."""
        text_lower = user_text.lower()

        # Stage 1: Keyword override
        for keyword in EMERGENCY_KEYWORDS:
            if keyword in text_lower:
                return "RED"

        # Stage 2: LLM classification
        try:
            response = self.llm.simple_prompt(
                prompt=f"Classify: {user_text}",
                system_prompt=SEVERITY_SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=10,
            )
            severity = response.strip().upper()
            if severity in {"RED", "YELLOW", "GREEN"}:
                return severity
        except Exception:
            pass

        return "GREEN"  # Safe default
