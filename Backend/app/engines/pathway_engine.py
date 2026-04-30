"""
Treatment Pathway Engine (Gap 9 Resolver).

Generates clinical pathway steps for a given procedure.
Costs are in INR (pre-geographic adjustment).
"""

import json
from typing import List, Dict, Any

from app.core.nvidia_client import NvidiaClient


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
