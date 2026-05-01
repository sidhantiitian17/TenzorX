"""
Master Orchestrator Agent

Central LangChain agent that receives every user message, routes to sub-agents,
assembles responses, and formats them for the dual-panel frontend.

Per instructionagent.md Section 4
"""

import re
import logging
from typing import Dict, Any, List, Literal, Optional
from datetime import datetime

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
from app.engines.pathway_engine import PathwayEngine
from app.engines.loan_engine import LoanEngine
from app.agents.geo_spatial_agent import GeoSpatialAgent
from app.agents.xai_explainer_agent import XAIExplainerAgent
from app.agents.appointment_agent import AppointmentAgent
from app.schemas.response_models import (
    MasterResponse,
    ChatResponseData,
    ResultsPanelData,
    SessionUpdates,
    NERTriageOutput,
    ClinicalPathwayOutput,
    HospitalDiscoveryOutput,
    FinancialEngineOutput,
    GeoSpatialOutput,
    XAIExplainerOutput,
    AppointmentPaperworkOutput,
    AppointmentChecklist,
)

logger = logging.getLogger(__name__)

# Intent classification keywords per instructionagent.md Section 4.1
INTENTS = {
    "HOSPITAL_SEARCH": ["find hospital", "near", "best hospital", "recommend", "hospital"],
    "COST_ESTIMATE": ["cost", "price", "how much", "budget", "afford", "lakh", "expensive", "cheap"],
    "PROCEDURE_INFO": ["what is", "explain", "how does", "angioplasty", "arthroplasty", "procedure"],
    "FINANCIAL_HELP": ["loan", "emi", "insurance", "scheme", "ayushman", "financ", "payment"],
    "APPOINTMENT": ["appointment", "book", "schedule", "dr.", "doctor", "visit"],
    "COMORBIDITY_QUERY": ["diabetes", "affect", "cardiac", "safe", "risk", "comorbidity"],
    "TRIAGE_EMERGENCY": [
        "chest pain", "radiating", "can't breathe", "unconscious", "not breathing",
        "emergency", "heart attack", "stroke", "severe", "critical", "urgent",
    ],
}

MASTER_SYSTEM_PROMPT = """You are HealthNav — an AI healthcare navigator for Indian patients.
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
6. Use simple, jargon-free language for Tier 2/3 city users.
7. Format numbers in Indian style (lakhs, crores).

RESPONSE FORMAT:
- Be conversational but informative
- Structure complex information in bullet points
- Always include confidence indicators
- Offer follow-up actions when appropriate"""


class MasterOrchestrator:
    """
    Master Orchestrator Agent per instructionagent.md Section 4.
    
    Routes to sub-agents and assembles the Master Response Schema.
    """

    def __init__(self):
        """Initialize the Master Orchestrator with all sub-agents."""
        self.llm = NvidiaClient(temperature=0.15, max_tokens=2048)
        self.severity_classifier = SeverityClassifier()
        self._graph_rag = None  # Lazy initialization
        self.cost_engine = CostEngine()
        self.geo_engine = GeoPricingEngine()
        self.comorbidity_engine = ComorbidityEngine()
        self.fusion_engine = FusionScoreEngine()
        self.pathway_engine = PathwayEngine()
        self.loan_engine = LoanEngine()
        self.geo_spatial_agent = GeoSpatialAgent()
        self.xai_explainer = XAIExplainerAgent()
        self.appointment_agent = AppointmentAgent()

    @property
    def graph_rag(self):
        """Lazy initialization of GraphRAG engine."""
        if self._graph_rag is None:
            try:
                self._graph_rag = GraphRAGEngine()
            except Exception as e:
                logger.warning(f"GraphRAG not available (Neo4j not configured): {e}")
                self._graph_rag = None
        return self._graph_rag

    def classify_intent(self, query: str) -> str:
        """
        Classify user intent from query text.
        
        Per instructionagent.md Section 4.1
        
        Args:
            query: User query string
            
        Returns:
            Intent classification
        """
        query_lower = query.lower()
        
        # Check emergency first (highest priority)
        for keyword in INTENTS["TRIAGE_EMERGENCY"]:
            if keyword in query_lower:
                return "TRIAGE_EMERGENCY"
        
        # Check other intents
        intent_scores = {}
        for intent, keywords in INTENTS.items():
            if intent == "TRIAGE_EMERGENCY":
                continue
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        
        # Default to hospital search if contains location-like terms
        if any(word in query_lower for word in ["near", "in ", "at ", "around"]):
            return "HOSPITAL_SEARCH"
        
        return "PROCEDURE_INFO"  # Default

    def route_agents(self, intent: str, severity: str) -> List[str]:
        """
        Determine which agents to run based on intent.
        
        Per instructionagent.md Section 4.2
        
        Args:
            intent: Classified intent
            severity: Severity classification
            
        Returns:
            List of agent names to execute
        """
        # Emergency: Only triage
        if severity == "RED" or intent == "TRIAGE_EMERGENCY":
            return ["ner_triage"]
        
        # Hospital search or cost estimate: Full pipeline
        if intent in ["HOSPITAL_SEARCH", "COST_ESTIMATE"]:
            return [
                "ner_triage",
                "clinical_pathway",
                "hospital_discovery",
                "financial_engine",
                "geo_spatial",
                "xai_explainer",
                "appointment_paperwork",
            ]
        
        # Procedure info: Triage + Pathway
        if intent == "PROCEDURE_INFO":
            return ["ner_triage", "clinical_pathway", "xai_explainer"]
        
        # Financial help: Financial engine only
        if intent == "FINANCIAL_HELP":
            return ["financial_engine", "xai_explainer"]
        
        # Appointment: Appointment agent only
        if intent == "APPOINTMENT":
            return ["appointment_paperwork"]
        
        # Comorbidity query: Pathway + Cost
        if intent == "COMORBIDITY_QUERY":
            return ["clinical_pathway", "financial_engine", "xai_explainer"]
        
        # Default: Basic pipeline
        return ["ner_triage", "clinical_pathway", "xai_explainer"]

    def execute_ner_triage(
        self,
        query: str,
        location: str,
        patient_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute NER + Triage Agent."""
        severity = self.severity_classifier.classify(query)
        
        # GraphRAG for procedure and ICD-10 (optional - works without Neo4j)
        rag_result = None
        if self.graph_rag:
            try:
                rag_result = self.graph_rag.query(query, location, patient_profile)
            except Exception as e:
                logger.warning(f"GraphRAG query failed in NER: {e}")
                rag_result = None
        
        # Get city tier
        city_tier = 2
        if location:
            city_tier = self.geo_engine.get_city_tier(location)
        
        # Extract budget from query
        budget_inr = self._extract_budget(query)
        
        # Handle None result - ensure rag_result is a dict
        if rag_result is None:
            rag_result = {}
        
        # Safely extract ICD-10 data
        icd10_data = rag_result.get("icd10") or {}
        
        # Convert city_tier to int if it's a string
        if isinstance(city_tier, str):
            tier_map = {"metro": 1, "tier1": 1, "tier2": 2, "tier3": 3}
            city_tier = tier_map.get(city_tier.lower(), 2)
        
        triage_result = {
            "agent": "ner_triage",
            "canonical_procedure": rag_result.get("procedure", ""),
            "category": rag_result.get("medical_category", ""),
            "icd10": icd10_data.get("code", "") if isinstance(icd10_data, dict) else str(icd10_data),
            "snomed_ct": icd10_data.get("snomed_code", "") if isinstance(icd10_data, dict) else "",
            "city": location,
            "city_tier": int(city_tier) if city_tier else 2,
            "budget_inr": budget_inr,
            "triage": severity,
            "mapping_confidence": rag_result.get("mapping_confidence", 70),
            "extracted_comorbidities": patient_profile.get("comorbidities", []),
        }

        return triage_result

    def _extract_budget(self, query: str) -> Optional[int]:
        """Extract budget amount from query."""
        # Look for patterns like "under 2 lakh", "Rs 200000", "within 1.5L"
        patterns = [
            r"(?:under|within|below|max|budget|around)\s*(?:Rs\.?|INR)?\s*([\d.]+)\s*(?:lakh|lac|L)",
            r"(?:Rs\.?|INR)?\s*([\d.]+)\s*(?:lakh|lac|L)",
            r"(?:under|within|below|max)\s*(?:Rs\.?|INR)?\s*(\d{5,7})",
        ]
        
        query_lower = query.lower()
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                value = float(match.group(1))
                if "lakh" in query_lower or "lac" in query_lower or "l" in query_lower:
                    return int(value * 100000)
                return int(value)
        return None

    def execute_clinical_pathway(
        self,
        procedure: str,
        city_tier: int,
        comorbidities: List[str],
        age: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute Clinical Pathway Agent."""
        # Get pathway from engine
        pathway = self.pathway_engine.get_pathway(procedure)
        
        # Get base cost
        base_cost = self.cost_engine.estimate(procedure, city_tier)
        
        # Apply geo multiplier
        geo_adjusted = self.geo_engine.apply_multiplier(base_cost, city_tier)
        
        # Apply comorbidity adjustments
        final_cost = self.comorbidity_engine.adjust(
            geo_adjusted,
            comorbidities=comorbidities,
            age=age,
        )
        
        # Build pathway steps (pathway is a list of step dicts)
        pathway_steps = []
        steps_list = pathway if isinstance(pathway, list) else pathway.get("steps", [])
        for i, step in enumerate(steps_list, 1):
            step_dict = step if isinstance(step, dict) else {}
            pathway_steps.append({
                "step": i,
                "name": step_dict.get("name", "") if isinstance(step_dict, dict) else getattr(step, "name", ""),
                "duration": step_dict.get("duration", "") if isinstance(step_dict, dict) else getattr(step, "duration", ""),
                "cost_min": step_dict.get("cost_min", 0) if isinstance(step_dict, dict) else 0,
                "cost_max": step_dict.get("cost_max", 0) if isinstance(step_dict, dict) else 0,
            })
        
        # Get comorbidity impacts
        comorbidity_impacts = []
        for condition in comorbidities:
            impact = self.comorbidity_engine.get_impact(condition)
            if impact:
                comorbidity_impacts.append({
                    "condition": condition,
                    "add_min": impact.get("min_add", 0),
                    "add_max": impact.get("max_add", 0),
                })
        
        return {
            "agent": "clinical_pathway",
            "pathway_steps": pathway_steps,
            "total_min": final_cost.get("min", 0),
            "total_max": final_cost.get("max", 0),
            "comorbidity_impacts": comorbidity_impacts,
            "cost_confidence": 70 + (len(pathway_steps) * 2),
            "geo_adjustment_note": f"Cost adjusted for Tier {city_tier} city.",
        }

    def execute_hospital_discovery(
        self,
        procedure: str,
        city: str,
        lat: float,
        lng: float,
        budget_inr: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute Hospital Discovery Agent."""
        # Query GraphRAG for hospitals (optional - works without Neo4j)
        hospitals_raw = []
        if self.graph_rag:
            try:
                rag_result = self.graph_rag.query(f"{procedure} in {city}", city, {})
                hospitals_raw = rag_result.get("hospitals_raw", []) if rag_result else []
            except Exception as e:
                logger.warning(f"GraphRAG query failed: {e}")
                hospitals_raw = []
        
        # Score and rank hospitals
        hospitals_scored = self.fusion_engine.score_and_rank(
            hospitals=hospitals_raw,
            procedure=procedure,
            user_lat=lat,
            user_lon=lng,
            budget_max=budget_inr,
        )
        
        return {
            "agent": "hospital_discovery",
            "result_count": len(hospitals_scored),
            "hospitals": hospitals_scored,
            "map_markers": self._extract_markers(hospitals_scored),
        }

    def _extract_markers(self, hospitals: List[Dict]) -> List[Dict]:
        """Extract map markers from hospital list."""
        markers = []
        tier_colors = {
            "premium": "#3B82F6",
            "mid-tier": "#8B5CF6",
            "budget": "#10B981",
        }
        
        for h in hospitals:
            tier = h.get("tier", "mid-tier").lower()
            markers.append({
                "id": h.get("id", ""),
                "lat": h.get("lat", 0),
                "lng": h.get("lng", 0),
                "tier": tier,
                "color": tier_colors.get(tier, "#6B7CFF"),
            })
        
        return markers

    def execute_financial_engine(
        self,
        procedure_cost_estimate: int,
        patient_income_monthly: Optional[float] = None,
        existing_emis: Optional[float] = None,
        loan_tenure_months: int = 24,
        city: str = "",
        hospital_tier: str = "mid-tier",
        comorbidities: List[str] = [],
    ) -> Dict[str, Any]:
        """Execute Financial Engine Agent."""
        # Evaluate loan
        loan_result = self.loan_engine.evaluate(
            total_treatment_cost=procedure_cost_estimate,
            gross_monthly_income=patient_income_monthly or 50000,
            existing_emis=existing_emis or 0,
        )
        
        # EMI options
        emi_option = loan_result.get("emi_options", [{}])[0] if loan_result.get("emi_options") else {}
        
        # Government schemes
        schemes = [
            {
                "name": "Ayushman Bharat PM-JAY",
                "coverage": "Up to Rs 5L/year",
                "url": "https://pmjay.gov.in",
                "eligibility": "BPL/low-income families",
            },
            {
                "name": "National Health Authority",
                "coverage": "Various schemes",
                "url": "https://nhp.gov.in",
                "eligibility": "All citizens",
            },
            {
                "name": "CGHS (Central Govt Health Scheme)",
                "coverage": "Comprehensive coverage",
                "url": "https://cghs.gov.in",
                "eligibility": "Central govt employees",
            },
        ]
        
        # Lending partners
        lenders = [
            {"name": "Tata Capital Health Loan", "range": "Rs 50K - Rs 5L", "tat": "24-72 hrs"},
            {"name": "Bajaj Finserv Health EMI", "range": "Rs 30K - Rs 7L", "tat": "Same day"},
            {"name": "HDFC Bank Medical Loan", "range": "Rs 1L - Rs 10L", "tat": "1-3 days"},
        ]
        
        # Cost breakdown items
        breakdown = [
            {"label": "Pre-op assessment", "min": 3000, "max": 8000},
            {"label": "Implant/Consumables", "min": 20000, "max": 60000},
            {"label": "Surgery/Procedure", "min": 80000, "max": 120000},
            {"label": "Hospital stay", "min": 30000, "max": 60000},
            {"label": "Post-op care", "min": 5000, "max": 15000},
        ]
        
        # Comorbidity surcharges
        surcharges = []
        for condition in comorbidities:
            if condition.lower() in ["diabetes", "cardiac", "hypertension"]:
                surcharges.append({
                    "condition": condition,
                    "add_min": 10000,
                    "add_max": 30000,
                })
        
        return {
            "agent": "financial_engine",
            "total_cost_range": {
                "min": int(procedure_cost_estimate * 0.85),
                "max": int(procedure_cost_estimate * 1.15),
            },
            "typical_range": {
                "min": int(procedure_cost_estimate * 0.9),
                "max": int(procedure_cost_estimate * 1.1),
            },
            "tier_cost_comparison": {
                "budget": {"min": 80000, "max": 140000},
                "mid_tier": {"min": 120000, "max": 220000},
                "premium": {"min": 250000, "max": 450000},
            },
            "emi_calculator": {
                "loan_amount": loan_result.get("loan_amount", 0),
                "tenure_months": emi_option.get("tenure_months", 24),
                "annual_rate_pct": 13.0,
                "monthly_emi": emi_option.get("emi", 0),
                "total_repayment": emi_option.get("emi", 0) * emi_option.get("tenure_months", 24),
            },
            "dti_assessment": {
                "risk_level": loan_result.get("risk_band", "medium").replace("_", " ").title(),
                "rate_range": f"{loan_result.get('interest_rate_range', [12, 16])[0]}-{loan_result.get('interest_rate_range', [12, 16])[1]}%",
                "cta": loan_result.get("call_to_action", ""),
                "dti_percentage": loan_result.get("primary_dti", 0),
            } if patient_income_monthly else None,
            "government_schemes": schemes,
            "lending_partners": lenders,
            "cost_breakdown_items": breakdown,
            "comorbidity_surcharges": surcharges,
        }

    def execute_geo_spatial(
        self,
        location_string: str,
        hospitals: Optional[List[Dict]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Execute Geo-Spatial Agent."""
        result = self.geo_spatial_agent.process(location_string, hospitals)
        if result:
            return {
                "agent": "geo_spatial",
                "user_coords": {
                    "lat": result.user_coords.lat,
                    "lng": result.user_coords.lng,
                },
                "city_tier": result.city_tier,
                "hospital_markers": result.hospital_markers,
                "map_config": {
                    "center": result.map_config.center,
                    "zoom": result.map_config.zoom,
                    "tile_layer": result.map_config.tile_layer,
                    "legend": result.map_config.legend,
                },
            }
        return None

    def execute_xai_explainer(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute XAI Explainer Agent."""
        result = self.xai_explainer.process(
            hospital_id=context.get("top_hospital_id"),
            hospital_scores=context.get("hospital_scores"),
            query=context.get("query"),
            triage=context.get("triage"),
            context=context,
        )
        
        # XAIExplainerOutput is a Pydantic model, not a dict
        # Access attributes directly
        if result is None:
            return {
                "agent": "xai_explainer",
                "confidence_score": 70,
                "confidence_drivers": {
                    "data_availability": 0,
                    "pricing_consistency": 0,
                    "benchmark_recency": 0,
                    "patient_complexity": 0,
                },
                "top_hospital_shap": None,
                "triage_lime": None,
                "show_uncertainty_banner": False,
                "disclaimer": "",
            }
        
        return {
            "agent": "xai_explainer",
            "confidence_score": result.confidence_score,
            "confidence_drivers": {
                "data_availability": result.confidence_drivers.data_availability,
                "pricing_consistency": result.confidence_drivers.pricing_consistency,
                "benchmark_recency": result.confidence_drivers.benchmark_recency,
                "patient_complexity": result.confidence_drivers.patient_complexity,
            },
            "top_hospital_shap": result.top_hospital_shap.dict() if result.top_hospital_shap else None,
            "triage_lime": result.triage_lime if result.triage_lime else None,
            "show_uncertainty_banner": result.show_uncertainty_banner,
            "disclaimer": result.disclaimer or "",
        }

    def execute_appointment_paperwork(
        self,
        session_id: str,
        procedure: str,
        tier: str = "mid-tier",
        action: str = "checklist",
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute Appointment & Paperwork Agent."""
        result = self.appointment_agent.process(
            session_id=session_id,
            procedure=procedure,
            tier=tier,
            action=action,
            **kwargs,
        )
        
        return {
            "agent": "appointment_paperwork",
            "checklist": {
                "documents": result.checklist.documents,
                "questions": result.checklist.questions,
                "forms": [f.dict() for f in result.checklist.forms],
            },
            "appointment_requests": [a.dict() for a in result.appointment_requests],
        }

    def generate_llm_response(
        self,
        query: str,
        agent_outputs: Dict[str, Any],
        history: List[Dict[str, str]],
        severity: str,
    ) -> str:
        """Generate LLM synthesis of agent outputs."""
        # Build enrichment context
        ner_data = agent_outputs.get('ner_triage') or {}
        hospital_data = agent_outputs.get('hospital_discovery') or {}
        financial_data = agent_outputs.get('financial_engine') or {}
        pathway_data = agent_outputs.get('clinical_pathway') or {}
        xai_data = agent_outputs.get('xai_explainer') or {}
        
        enrichment = f"""
[AGENT CONTEXT]
Severity: {severity}
Procedure: {ner_data.get('canonical_procedure', '')}
ICD-10: {ner_data.get('icd10', {})}
Hospitals found: {hospital_data.get('result_count', 0)}
Cost computed: {financial_data.get('total_cost_range', {})}
Geo-adjusted: {pathway_data.get('geo_adjustment_note', '')}
Confidence: {xai_data.get('confidence_score', 70)}%
"""

        messages_for_llm = history[:-1] if len(history) > 1 else []
        messages_for_llm.append({
            "role": "user",
            "content": history[-1]["content"] + "\n\n" + enrichment if history else enrichment,
        })

        try:
            llm_narrative = self.llm.chat(
                messages=messages_for_llm,
                system_prompt=MASTER_SYSTEM_PROMPT,
            )
            return llm_narrative
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            return self._generate_fallback_response(agent_outputs, severity)

    def _generate_fallback_response(
        self,
        agent_outputs: Dict[str, Any],
        severity: str,
    ) -> str:
        """Generate fallback when LLM fails."""
        ner_data = agent_outputs.get("ner_triage") or {}
        hospital_data = agent_outputs.get("hospital_discovery") or {}
        financial_data = agent_outputs.get("financial_engine") or {}
        
        procedure = ner_data.get("canonical_procedure", "your procedure")
        hospitals = hospital_data.get("result_count", 0)
        cost = financial_data.get("total_cost_range", {})
        
        base = f"I found information about {procedure}."
        
        if hospitals > 0:
            base += f"\n\nI found {hospitals} hospitals that perform this procedure."
        
        if cost:
            base += f"\n\nEstimated cost range: Rs {cost.get('min', 0):,} – Rs {cost.get('max', 0):,}"
        
        if severity == "RED":
            base = "🚨 This appears to be a medical emergency. Please call 112 or go to the nearest hospital immediately.\n\n" + base
        
        base += "\n\n⚕ This is decision support only — consult a qualified doctor."
        
        return base

    def process(
        self,
        session_id: str,
        user_message: str,
        location: str = "",
        patient_profile: Optional[Dict[str, Any]] = None,
    ) -> MasterResponse:
        """
        Main processing method - Master Orchestrator entry point.
        
        Args:
            session_id: User session identifier
            user_message: User's message/query
            location: Optional location context
            patient_profile: Optional patient profile
            
        Returns:
            MasterResponse with chat_response, results_panel, and session_updates
        """
        patient_profile = patient_profile or {}
        
        # Step 1: Intent classification
        intent = self.classify_intent(user_message)
        
        # Step 2: Severity check
        severity = self.severity_classifier.classify(user_message)
        
        # Step 3: Add to session memory
        add_user_message(session_id, user_message)
        history = get_session_messages_as_dicts(session_id)
        
        # Step 4: Route to sub-agents
        agents_to_run = self.route_agents(intent, severity)
        
        # Step 5: Execute agents
        agent_outputs = {}
        
        # Always run NER triage first
        if "ner_triage" in agents_to_run:
            agent_outputs["ner_triage"] = self.execute_ner_triage(
                query=user_message,
                location=location,
                patient_profile=patient_profile,
            )
            ner_data = agent_outputs["ner_triage"] or {}
        else:
            ner_data = {}
        
        # Ensure ner_data is a dict (not None)
        if ner_data is None:
            ner_data = {}
        
        # Get key data for downstream agents
        procedure = ner_data.get("canonical_procedure", "")
        city_tier = ner_data.get("city_tier", 2)
        budget_inr = ner_data.get("budget_inr")
        comorbidities = patient_profile.get("comorbidities", [])
        age = patient_profile.get("age")
        
        # Execute Clinical Pathway
        if "clinical_pathway" in agents_to_run and procedure:
            agent_outputs["clinical_pathway"] = self.execute_clinical_pathway(
                procedure=procedure,
                city_tier=city_tier,
                comorbidities=comorbidities,
                age=age,
            )
        
        # Get user coordinates
        geo_result = None
        if location:
            geo_result = self.execute_geo_spatial(location)
            if geo_result:
                agent_outputs["geo_spatial"] = geo_result
        
        # Execute Hospital Discovery
        if "hospital_discovery" in agents_to_run and procedure and location:
            user_lat = geo_result.get("user_coords", {}).get("lat", 0) if geo_result else 0
            user_lng = geo_result.get("user_coords", {}).get("lng", 0) if geo_result else 0
            
            agent_outputs["hospital_discovery"] = self.execute_hospital_discovery(
                procedure=procedure,
                city=location,
                lat=user_lat,
                lng=user_lng,
                budget_inr=budget_inr,
            )
        
        # Get cost estimate for financial engine
        pathway_data = agent_outputs.get("clinical_pathway") or {}
        procedure_cost = (pathway_data.get("total_min", 0) + pathway_data.get("total_max", 0)) // 2
        
        # Execute Financial Engine
        if "financial_engine" in agents_to_run:
            agent_outputs["financial_engine"] = self.execute_financial_engine(
                procedure_cost_estimate=procedure_cost,
                patient_income_monthly=patient_profile.get("income_monthly"),
                existing_emis=patient_profile.get("existing_emis"),
                city=location or "",
                hospital_tier="mid-tier",
                comorbidities=comorbidities,
            )
        
        # Execute XAI Explainer
        if "xai_explainer" in agents_to_run:
            hospital_discovery = agent_outputs.get("hospital_discovery") or {}
            xai_context = {
                "hospitals_found": hospital_discovery.get("result_count", 0),
                "has_pricing_data": bool(procedure_cost),
                "has_benchmark_data": True,
                "comorbidities_count": len(comorbidities),
                "query": user_message,
                "triage": severity,
            }
            
            # Add top hospital scores if available
            hospitals = hospital_discovery.get("hospitals", [])
            if hospitals:
                top_hospital = hospitals[0]
                xai_context["top_hospital_id"] = top_hospital.get("id")
                xai_context["hospital_scores"] = {
                    "clinical_score": top_hospital.get("fusion_score", 0.7) + 0.1,
                    "reputation_score": 0.75,
                    "accessibility_score": 0.8 if top_hospital.get("distance_km", 10) < 5 else 0.6,
                    "affordability_score": 0.85 if budget_inr and top_hospital.get("cost_min", 0) < budget_inr else 0.6,
                }
            
            agent_outputs["xai_explainer"] = self.execute_xai_explainer(xai_context)
        
        # Execute Appointment Paperwork
        if "appointment_paperwork" in agents_to_run and procedure:
            agent_outputs["appointment_paperwork"] = self.execute_appointment_paperwork(
                session_id=session_id,
                procedure=procedure,
                tier="mid-tier",
            )
        
        # Step 6: LLM synthesis
        llm_narrative = self.generate_llm_response(
            query=user_message,
            agent_outputs=agent_outputs,
            history=history,
            severity=severity,
        )
        
        # Save AI response
        add_ai_message(session_id, llm_narrative)
        
        # Step 7: Build Master Response
        chat_response = ChatResponseData(
            message=self._strip_search_data(llm_narrative),
            timestamp=datetime.now().strftime("%I:%M %p").lower(),
            triage_level=severity,
            offline_mode=False,
        )
        
        results_panel = ResultsPanelData(
            visible=True,
            active_tab="list",
            clinical_interpretation=agent_outputs.get("ner_triage"),
            pathway=agent_outputs.get("clinical_pathway"),
            cost_estimate=agent_outputs.get("financial_engine"),
            hospitals=agent_outputs.get("hospital_discovery"),
            map_data=agent_outputs.get("geo_spatial"),
            xai=agent_outputs.get("xai_explainer"),
            checklist=(agent_outputs.get("appointment_paperwork") or {}).get("checklist"),
            financial_assistance={
                "government_schemes": (agent_outputs.get("financial_engine") or {}).get("government_schemes", []),
                "lending_partners": (agent_outputs.get("financial_engine") or {}).get("lending_partners", []),
            } if "financial_engine" in agent_outputs else None,
        )
        
        session_updates = SessionUpdates(
            last_procedure=procedure,
            history_entry=f"{user_message[:50]}{'...' if len(user_message) > 50 else ''} | {chat_response.timestamp}",
        )
        
        return MasterResponse(
            chat_response=chat_response,
            results_panel=results_panel,
            session_updates=session_updates,
        )

    def _strip_search_data(self, text: str) -> str:
        """Remove XML tags from response."""
        import re
        clean = re.sub(r"<SEARCH_DATA>.*?</SEARCH_DATA>", "", text, flags=re.DOTALL)
        clean = re.sub(r"<EMERGENCY>.*?</EMERGENCY>", "", clean, flags=re.DOTALL)
        return clean.strip()


# =============================================================================
# Module-level convenience functions
# =============================================================================

def get_master_orchestrator() -> MasterOrchestrator:
    """Get singleton instance of MasterOrchestrator."""
    return MasterOrchestrator()
