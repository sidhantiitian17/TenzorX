"""
GraphRAG Engine - Hybrid Graph Retrieval + LLM Synthesis.

Combines deterministic Neo4j Cypher traversal with LLM-generated context
to produce enriched healthcare responses.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from app.knowledge_graph.neo4j_client import Neo4jClient
from app.core.nvidia_client import NvidiaClient
from app.nlp.ner_pipeline import NERPipeline
from app.nlp.icd10_mapper import ICD10Mapper

logger = logging.getLogger(__name__)


class GraphRAGEngine:
    """
    Hybrid GraphRAG: Cypher graph traversal + LLM synthesis.
    
    Flow: User query -> NER -> ICD-10 mapping -> Cypher -> LLM context enrichment.
    """

    def __init__(self):
        self.neo4j = Neo4jClient()
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
        Main GraphRAG entry point.
        
        1. Extract entities via NER
        2. Map to ICD-10 codes
        3. Traverse Neo4j graph
        4. Enrich with LLM
        5. Return structured result

        Returns a dict matching the frontend's SEARCH_DATA schema.
        """
        patient_profile = patient_profile or {}
        
        # Step 1: NER
        entities = self.ner.extract(user_text)
        symptoms = [e.normalized for e in entities if e.label == "SYMPTOM"]
        procedures = [e.normalized for e in entities if e.label == "PROCEDURE"]
        conditions_mentioned = [e.normalized for e in entities if e.label == "CONDITION"]

        logger.info(f"Extracted entities: {len(entities)} total, {len(symptoms)} symptoms, {len(procedures)} procedures")

        # Step 2: Graph traversal
        conditions = []
        if symptoms:
            conditions = self.neo4j.find_conditions_for_symptoms(symptoms)
            logger.info(f"Found {len(conditions)} conditions for symptoms")

        # Step 3: ICD-10 map first condition or use direct procedure
        primary_icd10: Optional[Dict[str, str]] = None
        primary_procedure: Optional[str] = None
        primary_condition: Optional[str] = None

        if conditions:
            primary_condition = conditions[0]["icd10_label"]
            primary_icd10 = {
                "code": conditions[0]["icd10_code"],
                "label": conditions[0]["icd10_label"],
                "snomed_code": conditions[0].get("snomed_code", ""),
                "category": conditions[0]["category"],
            }
            proc_results = self.neo4j.find_procedures_for_condition(conditions[0]["icd10_code"])
            primary_procedure = proc_results[0]["procedure_name"] if proc_results else None
            logger.info(f"Primary procedure from condition: {primary_procedure}")

        elif procedures:
            # Direct procedure query (e.g., "knee replacement")
            icd_result = self.icd_mapper.lookup(procedures[0])
            primary_icd10 = {
                "code": icd_result["code"] if icd_result else "Z99.89",
                "label": icd_result["description"] if icd_result else procedures[0],
                "snomed_code": "",
                "category": "Surgical Procedure",
            }
            primary_procedure = procedures[0]
            logger.info(f"Primary procedure from NER: {primary_procedure}")

        elif conditions_mentioned:
            # Try to map mentioned conditions
            icd_result = self.icd_mapper.lookup(conditions_mentioned[0])
            if icd_result:
                primary_icd10 = {
                    "code": icd_result["code"],
                    "label": icd_result["description"],
                    "snomed_code": "",
                    "category": "Condition",
                }

        # Step 4: Hospital discovery
        hospitals_raw: List[Dict[str, Any]] = []
        if primary_procedure and location:
            hospitals_raw = self.neo4j.find_hospitals_for_procedure_in_city(
                primary_procedure, location, limit=5
            )
            logger.info(f"Found {len(hospitals_raw)} hospitals for {primary_procedure} in {location}")

        # Step 5: LLM synthesis with enriched graph context
        graph_context = json.dumps({
            "entities": [e.__dict__ for e in entities],
            "conditions": conditions[:3],
            "procedure": primary_procedure,
            "icd10": primary_icd10,
            "hospitals_count": len(hospitals_raw),
            "location": location,
        }, indent=2, default=str)

        system_prompt = self._build_system_prompt()
        user_message = f"""
Patient query: {user_text}
Location: {location}
Patient profile: {json.dumps(patient_profile)}

Graph context retrieved:
{graph_context}

Produce a response with embedded <SEARCH_DATA>{{...}}</SEARCH_DATA> block.
"""
        
        try:
            llm_response = self.llm.simple_prompt(
                prompt=user_message,
                system_prompt=system_prompt,
            )
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            llm_response = self._generate_fallback_response(primary_procedure, location)

        return {
            "llm_response": llm_response,
            "entities": entities,
            "icd10": primary_icd10,
            "procedure": primary_procedure,
            "condition": primary_condition,
            "hospitals_raw": hospitals_raw,
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the GraphRAG LLM synthesis."""
        return """You are HealthNav, an AI healthcare navigator for Indian patients in Tier 2/3 cities.
You NEVER diagnose. You provide DECISION SUPPORT ONLY.
You help users find hospitals, understand costs, and navigate healthcare options.

Rules:
1. ALWAYS end responses with: "⚕ This is decision support only — not medical advice."
2. Map ALL conditions to ICD-10 and SNOMED CT codes when possible.
3. Show costs ONLY as ranges (min-max), NEVER a single number.
4. Include confidence scores (0.0-1.0) with all estimates.
5. If emergency keywords detected (chest pain, stroke, unconscious, severe bleeding),
   prepend <EMERGENCY>true</EMERGENCY>.
6. Return structured data inside <SEARCH_DATA>...</SEARCH_DATA> tags for hospital/cost queries.

SEARCH_DATA JSON must follow this exact schema:
{
  "emergency": false,
  "query_interpretation": "Brief interpretation of what the user is looking for",
  "procedure": "Identified procedure name",
  "icd10_code": "ICD-10 code",
  "icd10_label": "Human-readable condition name",
  "snomed_code": "SNOMED CT code if available",
  "medical_category": "Category of the medical issue",
  "pathway": [],
  "mapping_confidence": 0.0,
  "location": "User's location",
  "cost_estimate": {},
  "hospitals": [],
  "comorbidity_warnings": [],
  "data_sources": []
}

Be helpful, accurate, and empathetic. Use simple language suitable for patients from Tier 2/3 cities.
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
