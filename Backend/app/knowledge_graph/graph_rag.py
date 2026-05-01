"""
GraphRAG Engine - Hybrid Graph Retrieval + LLM Synthesis.

Combines deterministic Neo4j Cypher traversal with LLM-generated context
to produce enriched healthcare responses per instruction_KG.md.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from app.knowledge_graph.neo4j_client import Neo4jClient
from app.knowledge_graph.fusion_scorer import FusionScorer
from app.knowledge_graph.availability_proxy import AvailabilityProxy, SeverityClassifier
from app.core.nvidia_client import NvidiaClient
from app.nlp.ner_pipeline import NERPipeline
from app.nlp.icd10_mapper import ICD10Mapper

logger = logging.getLogger(__name__)


class GraphRAGEngine:
    """
    Hybrid GraphRAG: Cypher graph traversal + LLM synthesis.
    
    Implements the complete end-to-end flow per instruction_KG.md Section 17:
    User Input -> NER -> ICD-10 -> Severity Classifier -> Graph Traversal -> 
    Cost Adjustments -> LLM Synthesis -> Confidence Gate -> Response
    """

    def __init__(self):
        self.neo4j = Neo4jClient()
        self.fusion_scorer = FusionScorer(self.neo4j)
        self.availability_proxy = AvailabilityProxy(self.neo4j)
        self.ner = NERPipeline()
        self.icd_mapper = ICD10Mapper()
        self.llm = NvidiaClient(temperature=0.15, max_tokens=2048)

    def query(
        self, 
        user_text: str, 
        location: str, 
        patient_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main GraphRAG entry point per instruction_KG.md Section 17.
        
        Flow:
        1. NER - Extract entities from user text
        2. ICD-10 Lookup - Resolve to canonical codes
        3. Severity Classification - RED/YELLOW/GREEN triage
        4. Graph Traversal - Disease → Procedure → Cost → Hospital
        5. Cost Adjustments - Apply γ_geo + comorbidity + age weights
        6. Availability Proxy - Compute queuing estimates
        7. LLM Synthesis - Generate enriched response
        8. Confidence Gate - Validate RAG output
        
        Returns a dict matching the frontend's SEARCH_DATA schema.
        """
        patient_profile = patient_profile or {}
        patient_age = patient_profile.get("age")
        comorbidities = patient_profile.get("comorbidities", [])
        
        # Step 1: NER - Extract medical entities
        entities = self.ner.extract(user_text)
        symptoms = [e.normalized for e in entities if e.label == "SYMPTOM"]
        procedures = [e.normalized for e in entities if e.label == "PROCEDURE"]
        conditions_mentioned = [e.normalized for e in entities if e.label == "CONDITION"]

        logger.info(f"NER: {len(entities)} entities, {len(symptoms)} symptoms, {len(procedures)} procedures")

        # Step 2: Severity Classification per instruction_KG.md Section 13.4
        severity = SeverityClassifier.classify(symptoms, user_text)
        is_emergency = severity["severity"] == "RED"
        logger.info(f"Severity: {severity['severity']} - {severity['reason']}")

        # Step 3: Graph Traversal - Disease and Procedure discovery
        diseases = []
        if symptoms:
            diseases = self.neo4j.find_diseases_for_symptoms(symptoms)
            logger.info(f"Found {len(diseases)} diseases for symptoms")

        # Step 4: Determine primary disease and procedure
        primary_icd10: Optional[Dict[str, str]] = None
        primary_procedure: Optional[str] = None
        primary_disease: Optional[str] = None
        disease_icd_code: Optional[str] = None
        cost_breakdown: List[Dict] = []

        if diseases:
            primary_disease = diseases[0]["name"]
            disease_icd_code = diseases[0]["icd10_code"]
            primary_icd10 = {
                "code": diseases[0]["icd10_code"],
                "label": diseases[0]["name"],
                "description": diseases[0]["icd10_description"],
                "category": diseases[0]["category"],
            }
            
            # Get procedures for this disease
            proc_results = self.neo4j.find_procedures_for_disease(disease_icd_code)
            treatment_procs = proc_results.get("treatment", [])
            primary_procedure = treatment_procs[0]["procedure_name"] if treatment_procs else None
            logger.info(f"Primary: {primary_disease} → {primary_procedure}")

        elif procedures:
            # Direct procedure query
            primary_procedure = procedures[0]
            icd_result = self.icd_mapper.lookup(procedures[0])
            primary_icd10 = {
                "code": icd_result["code"] if icd_result else "Z99.89",
                "label": icd_result["description"] if icd_result else procedures[0],
                "category": "Surgical Procedure",
            }
            logger.info(f"Direct procedure: {primary_procedure}")

        # Step 5: Get cost breakdown with phase-based components
        cost_adjustments = None
        if primary_procedure:
            cost_breakdown = self.neo4j.get_cost_breakdown(primary_procedure)
            
            # Calculate total base cost from components
            base_min = sum(c["cost_min"] for c in cost_breakdown)
            base_max = sum(c["cost_max"] for c in cost_breakdown)
            
            # Step 6: Apply cost adjustments per instruction_KG.md Sections 10-11
            cost_adjustments = self.neo4j.apply_cost_adjustments(
                base_cost_min=base_min,
                base_cost_max=base_max,
                city_name=location,
                comorbidity_names=comorbidities,
                patient_age=patient_age
            )
            logger.info(f"Cost: ₹{cost_adjustments['final_cost_min']:,.0f} - ₹{cost_adjustments['final_cost_max']:,.0f}")

        # Step 7: Hospital discovery with fusion score ranking
        hospitals_raw: List[Dict[str, Any]] = []
        enriched_hospitals: List[Dict[str, Any]] = []
        
        if primary_procedure and location:
            hospitals_raw = self.neo4j.find_hospitals_for_procedure_in_city(
                primary_procedure, location, limit=5
            )
            logger.info(f"Found {len(hospitals_raw)} hospitals for {primary_procedure} in {location}")
            
            # Step 8: Add availability proxy for each hospital
            for hospital in hospitals_raw:
                hosp_id = hospital["id"]
                
                # Compute availability per instruction_KG.md Section 13
                availability = self.availability_proxy.compute_availability(
                    hosp_id, 
                    department=primary_icd10.get("category") if primary_icd10 else None,
                    is_emergency=is_emergency
                )
                
                # If emergency, only show hospitals with emergency units
                if is_emergency and not availability.has_emergency:
                    continue
                
                hospital["availability"] = {
                    "label": availability.label,
                    "score": availability.score,
                    "estimated_days": availability.estimated_days,
                    "has_emergency": availability.has_emergency
                }
                enriched_hospitals.append(hospital)

        # Step 9: Build clinical pathway per instruction_KG.md Section 9.2
        pathway = self._build_pathway(cost_breakdown, cost_adjustments)

        # Step 10: LLM synthesis with enriched graph context
        graph_context = json.dumps({
            "entities": [e.__dict__ for e in entities],
            "severity": severity,
            "diseases": diseases[:3],
            "disease_icd": disease_icd_code,
            "procedure": primary_procedure,
            "icd10": primary_icd10,
            "pathway": pathway,
            "cost_adjustments": cost_adjustments,
            "hospitals": enriched_hospitals,
            "location": location,
            "patient_profile": patient_profile,
        }, indent=2, default=str)

        system_prompt = self._build_system_prompt()
        user_message = f"""
Patient query: {user_text}
Location: {location}
Severity: {severity['severity']}

Graph context retrieved:
{graph_context}

Produce a response with embedded <SEARCH_DATA>{{...}}</SEARCH_DATA> block.
"""
        
        # Step 11: LLM synthesis
        try:
            llm_response = self.llm.simple_prompt(
                prompt=user_message,
                system_prompt=system_prompt,
            )
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            llm_response = self._generate_fallback_response(primary_procedure, location)

        # Step 12: Compute confidence score (simplified version of Section 14)
        confidence_score = self._compute_confidence(
            has_disease=bool(primary_disease),
            has_procedure=bool(primary_procedure),
            hospital_count=len(enriched_hospitals),
            has_cost=bool(cost_adjustments)
        )

        return {
            "llm_response": llm_response,
            "entities": entities,
            "icd10": primary_icd10,
            "procedure": primary_procedure,
            "disease": primary_disease,
            "disease_icd": disease_icd_code,
            "severity": severity,
            "pathway": pathway,
            "cost_estimate": cost_adjustments,
            "hospitals_raw": enriched_hospitals,
            "confidence_score": confidence_score,
            "confidence_threshold_met": confidence_score >= 0.70,
        }

    def _build_pathway(
        self, 
        cost_breakdown: List[Dict[str, Any]], 
        cost_adjustments: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build clinical pathway matrix per instruction_KG.md Section 9.2."""
        if not cost_breakdown or not cost_adjustments:
            return []
        
        multiplier = cost_adjustments.get("final_multiplier", 1.0) if cost_adjustments else 1.0
        geo_mult = cost_adjustments.get("geo_multiplier", 1.0) if cost_adjustments else 1.0
        
        pathway = []
        for component in cost_breakdown:
            pathway.append({
                "phase": component["phase"],
                "description": component["description"],
                "components": component["description"].split(", "),
                "base_cost_min_inr": component["cost_min"],
                "base_cost_max_inr": component["cost_max"],
                "adjusted_cost_min_inr": round(component["cost_min"] * geo_mult * multiplier, 0),
                "adjusted_cost_max_inr": round(component["cost_max"] * geo_mult * multiplier, 0),
                "typical_days": component["typical_days"]
            })
        
        return pathway

    def _compute_confidence(
        self,
        has_disease: bool,
        has_procedure: bool,
        hospital_count: int,
        has_cost: bool
    ) -> float:
        """
        Compute RAG confidence score per instruction_KG.md Section 14.
        Simplified version - full implementation would use DeepEval metrics.
        """
        score = 0.0
        
        # Faithfulness: Did we find the key entities?
        if has_disease:
            score += 0.25
        if has_procedure:
            score += 0.25
        
        # Contextual relevancy: Did we retrieve hospitals?
        if hospital_count > 0:
            score += min(hospital_count * 0.1, 0.25)
        
        # Answer relevancy: Do we have cost estimates?
        if has_cost:
            score += 0.25
        
        return round(score, 2)

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the GraphRAG LLM synthesis."""
        return """You are HealthNav, an AI healthcare navigator for Indian patients.
You use a Neo4j Knowledge Graph to provide accurate, grounded healthcare information.
You NEVER diagnose. You provide DECISION SUPPORT ONLY.

Knowledge Graph Schema you can reference:
- Disease nodes with ICD-10 codes linked to Symptoms via [:INDICATES]
- Procedures linked to Diseases via [:TREATED_BY] and [:REQUIRES_WORKUP]
- CostComponent nodes per procedure with phases: pre_procedure, procedure, hospital_stay, post_procedure
- Hospital nodes with fusion_scores (computed from clinical, reputation, accessibility, affordability)
- Geography nodes with city tier multipliers (γ_geo: Tier1=1.0, Tier2=0.917, Tier3=0.833)
- Comorbidity nodes with cost weights (ω_i) that increase procedure costs
- Specialist nodes linked to Hospitals via [:EMPLOYS]

Response Rules:
1. ALWAYS end with: "⚕ This is decision support only — not medical advice."
2. Map conditions to ICD-10 codes when possible.
3. Show costs as PHASED BREAKDOWNS (pre/procedure/stay/post) with adjusted ranges.
4. Include confidence scores (0.0-1.0) with all estimates.
5. If severity is RED, prepend <EMERGENCY>true</EMERGENCY> and emphasize immediate care.
6. Reference fusion scores when explaining hospital rankings.
7. Mention availability estimates (e.g., "Appointments usually within 2-3 days").

Cost Explanation Format:
"Estimated cost: ₹{min} - ₹{max}
  - Pre-procedure diagnostics: ₹{amount}
  - Procedure: ₹{amount}
  - Hospital stay: ₹{amount}
  - Post-procedure care: ₹{amount}
  
Adjusted for: {city} location (γ_geo={multiplier}), {comorbidities}"

SEARCH_DATA JSON schema:
{
  "emergency": boolean,
  "severity": "RED|YELLOW|GREEN",
  "query_interpretation": "string",
  "procedure": "string",
  "disease": "string",
  "icd10_code": "string",
  "icd10_label": "string",
  "medical_category": "string",
  "pathway": [{"phase": "", "components": [], "cost_min": 0, "cost_max": 0}],
  "cost_estimate": {"final_cost_min": 0, "final_cost_max": 0, "geo_multiplier": 1.0, "contingency_pct": 0},
  "location": "string",
  "hospitals": [{"id": "", "name": "", "fusion_score": 0.0, "tier": "", "availability": ""}],
  "confidence_score": 0.0,
  "data_sources": ["knowledge_graph"]
}

Be helpful, accurate, and empathetic. Use simple language.
"""

    def _generate_fallback_response(self, procedure: Optional[str], location: str) -> str:
        """Generate a fallback response when LLM fails."""
        base = "I apologize, but I'm having trouble accessing the AI service right now."
        if procedure:
            base += f" I can see you're asking about {procedure}."
        if location:
            base += f" For {location}, please consult with a local healthcare provider."
        base += "\n\n⚕ This is decision support only — not medical advice."
        return base

    def close(self):
        """Clean up resources."""
        self.neo4j.close()
