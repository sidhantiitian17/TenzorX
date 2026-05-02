"""
Treatment Pathway Engine (Gap 9 Resolver).

Generates clinical pathway steps for a given procedure.
Costs are in INR (pre-geographic adjustment).
"""

import json
import logging
from typing import List, Dict, Any

from app.core.nvidia_client import NvidiaClient

logger = logging.getLogger(__name__)


PATHWAY_PROMPT = """You are a clinical pathway expert for Indian hospitals.
Given a medical procedure name and ICD-10 code, output ONLY a valid JSON array
of pathway steps. No preamble, no markdown, just JSON.

Each step object:
{
  "step": 1,
  "name": "Pre-operative Assessment",
  "description": "Blood tests, ECG, imaging",
  "typical_duration": "1-2 days",
  "cost_range": {"min": 3000, "max": 10000},
  "responsible_party": "Diagnostics Lab / Hospital"
}

Follow this standard pathway structure:
1. Pre-procedure Diagnostics
2. Specialist Consultation
3. Core Procedure / Surgery
4. Hospital / ICU Stay
5. Post-procedure Monitoring
6. Discharge & Follow-up Care"""


CLINICAL_PHASES_PROMPT = """You are a clinical pathway expert for Indian patients.
Given a medical procedure and its pathway steps, categorize them into 5 clinical phases
and provide patient-friendly explanations.

Output ONLY valid JSON in this exact format:
{
  "clinical_phases": [
    {
      "phase": "consultation",
      "name": "Specialist Consultation",
      "description": "Initial meeting with specialist to discuss condition and treatment options",
      "activities": ["Medical history review", "Physical examination", "Treatment discussion"],
      "cost_min": 500,
      "cost_max": 2000,
      "duration": "30-60 minutes",
      "responsible_party": "Specialist Doctor",
      "llm_explanation": "This is your first meeting with the specialist who will review your condition, discuss the procedure in detail, and answer your questions. Bring all previous medical reports."
    },
    {
      "phase": "diagnostics",
      "name": "Pre-Procedure Diagnostics",
      "description": "Tests and scans to assess your health before the procedure",
      "activities": ["Blood tests", "ECG", "X-ray/MRI", "Other imaging"],
      "cost_min": 3000,
      "cost_max": 10000,
      "duration": "1-2 days",
      "responsible_party": "Diagnostics Lab / Hospital",
      "llm_explanation": "These tests help the doctor understand your current health status and identify any risks before the procedure. You may need to fast before some tests."
    },
    {
      "phase": "procedure",
      "name": "Core Procedure / Surgery",
      "description": "The main medical intervention or surgery",
      "activities": ["Anesthesia", "Surgical procedure", "Implant placement if applicable"],
      "cost_min": 80000,
      "cost_max": 200000,
      "duration": "2-4 hours",
      "responsible_party": "Surgical Team / Hospital",
      "llm_explanation": "This is the main treatment phase. You will be under anesthesia during the procedure. The surgical team will monitor you throughout. Family can wait in the designated area."
    },
    {
      "phase": "observation_stay",
      "name": "Hospital / ICU Stay",
      "description": "Post-procedure monitoring and recovery in the hospital",
      "activities": ["ICU monitoring", "Ward recovery", "Pain management", "Medication administration"],
      "cost_min": 20000,
      "cost_max": 60000,
      "duration": "3-5 days",
      "responsible_party": "Hospital Nursing Staff",
      "llm_explanation": "After the procedure, you'll be monitored closely to ensure proper recovery. The duration depends on the procedure type and your response to treatment. Visitors may be allowed during visiting hours."
    },
    {
      "phase": "follow_up_medication",
      "name": "Follow-up Care & Medication",
      "description": "Post-discharge care, medications, and rehabilitation",
      "activities": ["Medication pickup", "Physiotherapy sessions", "Follow-up consultations", "Wound care"],
      "cost_min": 10000,
      "cost_max": 30000,
      "duration": "6-8 weeks",
      "responsible_party": "Patient / Home Care",
      "llm_explanation": "Recovery continues at home with medications and therapy. Regular follow-ups with the doctor are crucial to monitor healing. Follow all medication instructions carefully."
    }
  ]
}

The 5 phases must be: consultation, diagnostics, procedure, observation_stay, follow_up_medication"""


class PathwayEngine:
    """
    Generates clinical pathway steps for a given procedure.
    Costs are in INR (pre-geographic adjustment).
    """

    STATIC_PATHWAYS = {
        "angioplasty": [
            {"step": 1, "name": "Pre-Procedure Diagnostics",
             "description": "ECG, Stress Test, Echocardiogram, Diagnostic Angiography",
             "typical_duration": "1-2 days",
             "cost_range": {"min": 10000, "max": 30000}},
            {"step": 2, "name": "Surgical Procedure",
             "description": "Balloon Angioplasty / Stent Placement (Drug-Eluting Stent)",
             "typical_duration": "2-4 hours",
             "cost_range": {"min": 100000, "max": 250000}},
            {"step": 3, "name": "Hospital Stay (ICU + Ward)",
             "description": "ICU monitoring and General Ward recovery",
             "typical_duration": "3-5 days",
             "cost_range": {"min": 20000, "max": 60000}},
            {"step": 4, "name": "Post-Procedure Care",
             "description": "Anti-platelets, statins, follow-up consultations",
             "typical_duration": "6-8 weeks",
             "cost_range": {"min": 10000, "max": 30000}},
        ],
        "total knee arthroplasty": [
            {"step": 1, "name": "Pre-Surgical Evaluation",
             "description": "X-ray, MRI, blood panel, anesthesia review",
             "typical_duration": "2-3 days",
             "cost_range": {"min": 5000, "max": 15000}},
            {"step": 2, "name": "Surgery",
             "description": "Implant selection + surgery (conventional or robotic-assisted)",
             "typical_duration": "2-3 hours",
             "cost_range": {"min": 90000, "max": 200000}},
            {"step": 3, "name": "Hospital Stay",
             "description": "3-5 nights, physiotherapy begins Day 1",
             "typical_duration": "3-5 days",
             "cost_range": {"min": 25000, "max": 60000}},
            {"step": 4, "name": "Post-Operative Physiotherapy",
             "description": "6-12 weeks outpatient physiotherapy",
             "typical_duration": "6-12 weeks",
             "cost_range": {"min": 8000, "max": 20000}},
        ],
    }

    def __init__(self):
        self.llm = NvidiaClient(temperature=0.1, max_tokens=1024)

    def get_pathway(self, procedure: str, icd10_code: str = "") -> List[Dict[str, Any]]:
        """
        Return treatment pathway for a procedure.
        Uses static data for known procedures; falls back to LLM for others.
        """
        procedure_lower = procedure.lower().strip()

        # Check static pathways first
        for key, steps in self.STATIC_PATHWAYS.items():
            if key in procedure_lower or procedure_lower in key:
                return steps

        # LLM fallback for unknown procedures
        return self._generate_via_llm(procedure, icd10_code)

    def _generate_via_llm(self, procedure: str, icd10_code: str) -> List[Dict[str, Any]]:
        """Generate pathway via LLM for unknown procedures."""
        prompt = f"Generate pathway steps for: {procedure} (ICD-10: {icd10_code})"
        try:
            response = self.llm.simple_prompt(
                prompt=prompt,
                system_prompt=PATHWAY_PROMPT,
                temperature=0.1,
                max_tokens=1024,
            )
            clean = response.strip().strip("```json").strip("```").strip()
            return json.loads(clean)
        except Exception:
            return []

    def get_clinical_phases(
        self,
        procedure: str,
        pathway_steps: List[Dict[str, Any]],
        icd10_code: str = "",
        total_min: int = 0,
        total_max: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Generate detailed clinical phases with LLM explanations.
        Uses fast fallback by default; LLM enhancement is optional for future async processing.

        Args:
            procedure: Canonical procedure name
            pathway_steps: Existing pathway steps
            icd10_code: ICD-10 code
            total_min: Total minimum cost (if available)
            total_max: Total maximum cost (if available)

        Returns:
            List of clinical phase dicts with detailed information
        """
        # Use fallback for fast response - LLM call adds too much latency for sync API
        # Fallback provides quality data instantly based on pathway steps
        return self._fallback_clinical_phases(procedure, pathway_steps, total_min, total_max)

    def _fallback_clinical_phases(
        self,
        procedure: str,
        pathway_steps: List[Dict[str, Any]],
        total_min: int = 0,
        total_max: int = 0
    ) -> List[Dict[str, Any]]:
        """Fallback clinical phases when LLM fails."""
        # Calculate total cost from steps if not provided
        if total_min == 0:
            total_min = sum(s.get("cost_min", 0) for s in pathway_steps)
        if total_max == 0:
            total_max = sum(s.get("cost_max", 0) for s in pathway_steps)
        
        # Distribute costs across phases
        return [
            {
                "phase": "consultation",
                "name": "Specialist Consultation",
                "description": "Initial meeting with specialist to discuss condition and treatment options",
                "activities": ["Medical history review", "Physical examination", "Treatment discussion"],
                "cost_min": int(total_min * 0.02),
                "cost_max": int(total_max * 0.05),
                "duration": "30-60 minutes",
                "responsible_party": "Specialist Doctor",
                "llm_explanation": "This is your first meeting with the specialist who will review your condition, discuss the procedure in detail, and answer your questions. Bring all previous medical reports."
            },
            {
                "phase": "diagnostics",
                "name": "Pre-Procedure Diagnostics",
                "description": "Tests and scans to assess your health before the procedure",
                "activities": ["Blood tests", "ECG", "X-ray/MRI", "Other imaging"],
                "cost_min": int(total_min * 0.05),
                "cost_max": int(total_max * 0.1),
                "duration": "1-2 days",
                "responsible_party": "Diagnostics Lab / Hospital",
                "llm_explanation": "These tests help the doctor understand your current health status and identify any risks before the procedure. You may need to fast before some tests."
            },
            {
                "phase": "procedure",
                "name": "Core Procedure / Surgery",
                "description": "The main medical intervention or surgery",
                "activities": ["Anesthesia", "Surgical procedure", "Implant placement if applicable"],
                "cost_min": int(total_min * 0.6),
                "cost_max": int(total_max * 0.65),
                "duration": "2-4 hours",
                "responsible_party": "Surgical Team / Hospital",
                "llm_explanation": "This is the main treatment phase. You will be under anesthesia during the procedure. The surgical team will monitor you throughout. Family can wait in the designated area."
            },
            {
                "phase": "observation_stay",
                "name": "Hospital / ICU Stay",
                "description": "Post-procedure monitoring and recovery in the hospital",
                "activities": ["ICU monitoring", "Ward recovery", "Pain management", "Medication administration"],
                "cost_min": int(total_min * 0.2),
                "cost_max": int(total_max * 0.15),
                "duration": "3-5 days",
                "responsible_party": "Hospital Nursing Staff",
                "llm_explanation": "After the procedure, you'll be monitored closely to ensure proper recovery. The duration depends on the procedure type and your response to treatment. Visitors may be allowed during visiting hours."
            },
            {
                "phase": "follow_up_medication",
                "name": "Follow-up Care & Medication",
                "description": "Post-discharge care, medications, and rehabilitation",
                "activities": ["Medication pickup", "Physiotherapy sessions", "Follow-up consultations", "Wound care"],
                "cost_min": int(total_min * 0.13),
                "cost_max": int(total_max * 0.05),
                "duration": "6-8 weeks",
                "responsible_party": "Patient / Home Care",
                "llm_explanation": "Recovery continues at home with medications and therapy. Regular follow-ups with the doctor are crucial to monitor healing. Follow all medication instructions carefully."
            }
        ]


# =============================================================================
# Module-level Pathway Generator (TC-20)
# =============================================================================


def generate_pathway(icd_code: str, procedure: str) -> list[dict]:
    """
    Generate clinical pathway phases for a procedure.
    
    Args:
        icd_code: ICD-10 code (e.g., "I25.10")
        procedure: Procedure name (e.g., "angioplasty")
        
    Returns:
        List of phase dicts with keys: phase, name, description, cost_range
    """
    engine = PathwayEngine()
    steps = engine.get_pathway(procedure, icd_code)
    
    # Map steps to standardized phases
    phase_map = {
        1: "pre_diagnostics",
        2: "procedure",
        3: "hospitalization",
        4: "post_care",
        5: "post_care",
        6: "post_care",
    }
    
    pathway = []
    for step in steps:
        phase = phase_map.get(step.get("step", 0), "other")
        pathway.append({
            "phase": phase,
            "step": step.get("step"),
            "name": step.get("name"),
            "description": step.get("description"),
            "cost_range": step.get("cost_range"),
            "typical_duration": step.get("typical_duration"),
        })
    
    return pathway
