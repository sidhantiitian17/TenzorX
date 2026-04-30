"""
Medical entity recognition and ICD-10 mapping service.

This module provides an MVP dictionary-backed mapper that converts extracted
symptoms into approximate ICD-10-CM codes for downstream routing and analytics.
"""

from __future__ import annotations

from typing import Iterable


ICD10_MOCK_LOOKUP: dict[str, str] = {
    "severe chest pain": "I25.1",
    "chest pain": "R07.9",
    "radiating arm pain": "R52",
    "shortness of breath": "R06.02",
    "difficulty breathing": "R06.00",
    "fever": "R50.9",
    "diabetes": "E11.9",
    "hypertension": "I10",
    "abdominal pain": "R10.9",
    "vomiting": "R11.10",
    "cough": "R05.9",
    "infection": "B99.9",
    "swelling": "R60.9",
}


def _normalize_symptom(symptom: str) -> str:
    """Normalize symptom text for deterministic dictionary lookup."""

    return " ".join(symptom.lower().split())


def map_symptoms_to_icd10(extracted_symptoms: Iterable[str]) -> dict[str, str]:
    """Map extracted symptom phrases to mock ICD-10 codes.

    Args:
        extracted_symptoms: A sequence of symptom phrases extracted from NLP.

    Returns:
        Dictionary mapping each symptom phrase to an ICD-10 code when available.
        Unmatched symptoms are excluded so downstream consumers only receive
        resolved entities.
    """

    mapped_codes: dict[str, str] = {}
    for symptom in extracted_symptoms:
        normalized_symptom = _normalize_symptom(symptom)
        icd10_code = ICD10_MOCK_LOOKUP.get(normalized_symptom)
        if icd10_code:
            mapped_codes[symptom] = icd10_code

    return mapped_codes
