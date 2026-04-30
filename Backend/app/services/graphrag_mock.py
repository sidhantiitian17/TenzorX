"""
Mock GraphRAG data layer.

This module simulates a deterministic graph traversal over clinical pathways
so the backend can evolve toward Neo4j-backed GraphRAG without changing the
service contract used by the orchestration layer.
"""

from __future__ import annotations

from typing import Any


_CLINICAL_PATHWAYS: dict[str, dict[str, Any]] = {
    "I25.1": {
        "icd_code": "I25.1",
        "pathway_name": "Coronary Artery Disease Care Pathway",
        "specialty": "Cardiology",
        "care_stages": [
            {
                "name": "Pre-Procedure Diagnostics",
                "node": "cardiac_diagnostics",
                "details": ["ECG", "troponin", "echocardiography", "angiography review"],
            },
            {
                "name": "Surgical Procedure (Angioplasty)",
                "node": "angioplasty",
                "details": ["cath lab preparation", "stent placement", "hemodynamic monitoring"],
            },
            {
                "name": "Hospital Stay",
                "node": "inpatient_recovery",
                "details": ["ICU/step-down monitoring", "antiplatelet therapy", "vital sign surveillance"],
            },
            {
                "name": "Post-Procedure Care",
                "node": "post_discharge_followup",
                "details": ["cardiac rehab", "medication adherence", "follow-up visit"],
            },
        ],
        "edges": [
            ("cardiac_diagnostics", "angioplasty"),
            ("angioplasty", "inpatient_recovery"),
            ("inpatient_recovery", "post_discharge_followup"),
        ],
    },
    "M17.11": {
        "icd_code": "M17.11",
        "pathway_name": "Total Knee Replacement Pathway",
        "specialty": "Orthopedics",
        "care_stages": [
            {
                "name": "Pre-Operative Assessment",
                "node": "pre_op_assessment",
                "details": ["x-ray", "anesthesia clearance", "mobility evaluation"],
            },
            {
                "name": "Surgical Procedure (Total Knee Replacement)",
                "node": "tkr_surgery",
                "details": ["prosthetic implantation", "operative monitoring", "blood loss management"],
            },
            {
                "name": "Inpatient Rehabilitation",
                "node": "rehabilitation",
                "details": ["physiotherapy", "pain control", "ambulation training"],
            },
            {
                "name": "Post-Operative Follow-Up",
                "node": "follow_up",
                "details": ["wound review", "range of motion monitoring", "home exercise program"],
            },
        ],
        "edges": [
            ("pre_op_assessment", "tkr_surgery"),
            ("tkr_surgery", "rehabilitation"),
            ("rehabilitation", "follow_up"),
        ],
    },
    "E11.9": {
        "icd_code": "E11.9",
        "pathway_name": "Type 2 Diabetes Management Pathway",
        "specialty": "Endocrinology",
        "care_stages": [
            {
                "name": "Baseline Evaluation",
                "node": "baseline_evaluation",
                "details": ["HbA1c", "fasting glucose", "renal function"],
            },
            {
                "name": "Medication Planning",
                "node": "medication_planning",
                "details": ["metformin optimization", "lifestyle counseling", "risk stratification"],
            },
            {
                "name": "Monitoring and Follow-Up",
                "node": "monitoring",
                "details": ["home glucose logs", "retinal screening", "foot exams"],
            },
        ],
        "edges": [
            ("baseline_evaluation", "medication_planning"),
            ("medication_planning", "monitoring"),
        ],
    },
}


def _resolve_icd_key(icd_code: str) -> str | None:
    """Resolve the canonical ICD key used by the mock graph."""

    normalized = icd_code.strip().upper()
    if normalized in _CLINICAL_PATHWAYS:
        return normalized

    prefix = normalized.split(".")[0]
    if prefix in _CLINICAL_PATHWAYS:
        return prefix

    return None


def get_clinical_pathway(icd_code: str) -> dict[str, Any]:
    """Return a deterministic clinical pathway for a mock ICD-10 code.

    The response is shaped like a small graph traversal result so the module can
    be replaced later by a real Neo4j Cypher query without changing consumers.
    """

    resolved_key = _resolve_icd_key(icd_code)
    if resolved_key is None:
        return {
            "icd_code": icd_code.strip().upper(),
            "pathway_name": "General Supportive Care Pathway",
            "specialty": "General Medicine",
            "care_stages": [],
            "edges": [],
            "traversal": ["ICD-10 lookup", "No deterministic pathway found"],
            "is_mock": True,
        }

    pathway = _CLINICAL_PATHWAYS[resolved_key]
    traversal = [f"ICD-10:{resolved_key}"]
    traversal.extend(stage["node"] for stage in pathway["care_stages"])

    return {
        **pathway,
        "traversal": traversal,
        "is_mock": True,
    }
