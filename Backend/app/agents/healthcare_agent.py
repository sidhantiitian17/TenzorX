"""
Healthcare Agent - Main conversational orchestrator.

Integrates NER, GraphRAG, cost engines, and LLM for structured responses.
"""

import re
import json
import logging
from typing import Dict, Any, Optional

from app.core.nvidia_client import NvidiaClient
from app.agents.memory_manager import (
    get_session_messages_as_dicts,
    add_user_message,
    add_ai_message,
)
from app.agents.severity_classifier import SeverityClassifier
from app.knowledge_graph.graph_rag import GraphRAGEngine
from app.engines.cost_engine import CostEngine
from app.engines.geo_pricing import GeoPricingEngine
from app.engines.comorbidity_engine import ComorbidityEngine
from app.engines.fusion_score import FusionScoreEngine

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """You are HealthNav — an AI healthcare navigator for Indian patients.
You operate as a multi-turn conversational agent with memory.

YOUR CAPABILITIES:
- Find and rank hospitals for medical procedures
- Estimate treatment costs at component level
- Explain treatment pathways in plain language
- Guide users on insurance and loan options
- Map symptoms/conditions to ICD-10 codes

STRICT RULES:
1. NEVER diagnose. NEVER prescribe. Decision support only.
2. Always end with: "⚕ This is decision support only — consult a qualified doctor."
3. If emergency keywords present, start with <EMERGENCY>true</EMERGENCY>.
4. All cost figures: ranges only. Format: Rs X – Rs Y.
5. Include <SEARCH_DATA>{...}</SEARCH_DATA> for hospital/cost queries.
6. Use simple, jargon-free language for Tier 2/3 city users."""


class HealthcareAgent:
    """Main conversational agent orchestrating all engines."""

    def __init__(self):
        self.llm = NvidiaClient(temperature=0.15, max_tokens=2048)
        self.severity_classifier = SeverityClassifier()
        self.graph_rag = GraphRAGEngine()
        self.cost_engine = CostEngine()
        self.geo_engine = GeoPricingEngine()
        self.comorbidity_engine = ComorbidityEngine()
        self.fusion_engine = FusionScoreEngine()

    def process(
        self,
        session_id: str,
        user_message: str,
        location: str = "",
        patient_profile: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Process user message and return structured response."""
        patient_profile = patient_profile or {}

        # Step 1: Severity check
        severity = self.severity_classifier.classify(user_message)

        # Step 2: Add to session memory
        add_user_message(session_id, user_message)
        history = get_session_messages_as_dicts(session_id)

        # Step 3: GraphRAG query
        rag_result = self.graph_rag.query(user_message, location, patient_profile)

        # Step 4: Cost estimation if procedure identified
        cost_estimate = {}
        if rag_result.get("procedure") and location:
            city_tier = self.geo_engine.get_city_tier(location)
            base_cost = self.cost_engine.estimate(
                procedure=rag_result["procedure"],
                city_tier=city_tier,
            )
            geo_adjusted = self.geo_engine.apply_multiplier(base_cost, city_tier)
            final_cost = self.comorbidity_engine.adjust(
                geo_adjusted,
                comorbidities=patient_profile.get("comorbidities", []),
                age=patient_profile.get("age"),
            )
            cost_estimate = final_cost

        # Step 5: Score hospitals
        hospitals_scored = []
        if rag_result.get("hospitals_raw"):
            hospitals_scored = self.fusion_engine.score_and_rank(
                hospitals=rag_result["hospitals_raw"],
                procedure=rag_result.get("procedure", ""),
                user_lat=patient_profile.get("lat"),
                user_lon=patient_profile.get("lon"),
                budget_max=patient_profile.get("budget_max"),
            )

        # Step 6: LLM synthesis
        enrichment = f"""
[AGENT CONTEXT]
Severity: {severity}
Procedure: {rag_result.get('procedure')}
ICD-10: {rag_result.get('icd10', {})}
Hospitals found: {len(hospitals_scored)}
Cost computed: {bool(cost_estimate)}
Comorbidities: {patient_profile.get('comorbidities', [])}
"""
        messages_for_llm = history[:-1] if len(history) > 1 else []
        messages_for_llm.append({
            "role": "user",
            "content": history[-1]["content"] + "\n\n" + enrichment if history else enrichment,
        })

        try:
            llm_narrative = self.llm.chat(
                messages=messages_for_llm,
                system_prompt=AGENT_SYSTEM_PROMPT,
            )
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            llm_narrative = self._generate_fallback_response(rag_result, severity)

        # Step 7: Save AI response
        add_ai_message(session_id, llm_narrative)

        # Step 8: Parse SEARCH_DATA
        search_data = self._parse_search_data(llm_narrative)

        # Merge engine outputs
        if cost_estimate:
            search_data["cost_estimate"] = cost_estimate
        if hospitals_scored:
            search_data["hospitals"] = hospitals_scored
        if rag_result.get("icd10"):
            icd = rag_result["icd10"]
            search_data["icd10_code"] = icd.get("code", "")
            search_data["icd10_label"] = icd.get("label", "")
            search_data["snomed_code"] = icd.get("snomed_code", "")

        return {
            "session_id": session_id,
            "narrative": self._strip_search_data(llm_narrative),
            "search_data": search_data,
            "severity": severity,
            "is_emergency": severity == "RED",
        }

    def _parse_search_data(self, llm_text: str) -> Dict:
        """Extract SEARCH_DATA JSON from LLM response."""
        match = re.search(r"<SEARCH_DATA>(.*?)</SEARCH_DATA>", llm_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        return {}

    def _strip_search_data(self, text: str) -> str:
        """Remove XML tags from response."""
        clean = re.sub(r"<SEARCH_DATA>.*?</SEARCH_DATA>", "", text, flags=re.DOTALL)
        clean = re.sub(r"<EMERGENCY>.*?</EMERGENCY>", "", clean, flags=re.DOTALL)
        return clean.strip()

    def _generate_fallback_response(self, rag_result: Dict, severity: str) -> str:
        """Generate fallback when LLM fails."""
        procedure = rag_result.get("procedure", "your procedure")
        base = f"I can help you with information about {procedure}."
        if severity == "RED":
            base += "\n\n🚨 This appears to be an emergency. Please call 112 or go to the nearest hospital immediately."
        base += "\n\n⚕ This is decision support only — consult a qualified doctor."
        return base
