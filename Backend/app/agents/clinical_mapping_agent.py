"""
Clinical Mapping Agent

Generates structured clinical mapping using LLM when GraphRAG
returns incomplete or missing data.

Performs:
1. Procedure extraction/interpretation from user query
2. Medical category classification
3. ICD-10 code mapping
4. SNOMED CT code mapping
5. Confidence scoring
"""

import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.core.nvidia_client import NvidiaClient

logger = logging.getLogger(__name__)


@dataclass
class ClinicalMappingResult:
    """Structured clinical mapping result."""
    user_query: str
    procedure: str
    category: str
    icd10_code: str
    icd10_label: str
    snomed_code: str
    confidence: float
    confidence_factors: list
    mapping_rationale: str


CLINICAL_MAPPING_PROMPT = """You are a medical coding assistant specializing in Indian healthcare.
Given a user's health query, extract and map the clinical information.

TASK:
1. Identify the PRIMARY medical procedure or condition from the query
2. Classify into medical category (e.g., Cardiology, Orthopedics, General Medicine, etc.)
3. Map to most appropriate ICD-10 CM code
4. Map to SNOMED CT code if available
5. Provide confidence score (0.0-1.0) based on query clarity
6. Explain your mapping rationale

RESPONSE FORMAT (JSON only):
{
    "procedure": "Canonical procedure name (e.g., Angioplasty, Total Knee Replacement)",
    "category": "Medical specialty category",
    "icd10_code": "ICD-10 CM code (e.g., I25.10)",
    "icd10_label": "Full ICD-10 description",
    "snomed_code": "SNOMED CT code or 'N/A' if not applicable",
    "confidence": 0.85,
    "confidence_factors": [
        {"key": "explicit_mention", "label": "Explicit procedure mention", "score": 90},
        {"key": "symptom_match", "label": "Symptom-to-condition mapping", "score": 80}
    ],
    "rationale": "Brief explanation of how you interpreted the query"
}

CRITICAL RULES:
- NEVER return the user's raw query text as the procedure name
- ALWAYS extract a canonical medical procedure/condition name
- If query is vague, make best educated guess and lower confidence
- For symptoms without explicit condition, map to most likely condition
- Use standard medical terminology (e.g., "Nephrolithiasis Treatment" NOT "I have kidney stone...")
- ICD-10 codes must be valid CM codes
- SNOMED codes should be valid concept IDs when available
- Confidence < 0.5 if query is completely unclear

EXAMPLE 1:
User: "I have diabetes, need to understand my diagnosis"
{
    "procedure": "Diabetes Mellitus Management",
    "category": "Endocrinology",
    "icd10_code": "E11.9",
    "icd10_label": "Type 2 diabetes mellitus without complications",
    "snomed_code": "44054006",
    "confidence": 0.82,
    "confidence_factors": [
        {"key": "condition_explicit", "label": "Condition explicitly stated", "score": 95},
        {"key": "management_context", "label": "Management context inferred", "score": 70}
    ],
    "rationale": "User explicitly mentions diabetes diagnosis and seeks understanding, indicating diabetes management/education context"
}

EXAMPLE 2:
User: "I have kidney stones, suggest me nearby treatment options"
{
    "procedure": "Nephrolithiasis Treatment",
    "category": "Urology",
    "icd10_code": "N20.0",
    "icd10_label": "Calculus of kidney",
    "snomed_code": "9557008",
    "confidence": 0.88,
    "confidence_factors": [
        {"key": "condition_explicit", "label": "Condition explicitly stated", "score": 95},
        {"key": "treatment_intent", "label": "Treatment intent clear", "score": 85}
    ],
    "rationale": "User explicitly states kidney stones (nephrolithiasis) and requests treatment options"
}

EXAMPLE 3 - AVOID THIS MISTAKE:
User: "I have kidney stone, tell me treatment option"
WRONG: {"procedure": "I have kidney stone, tell me treatment option", ...} ❌
RIGHT: {"procedure": "Nephrolithiasis Treatment", ...} ✓

Now process this query:"""


class ClinicalMappingAgent:
    """
    Agent for generating clinical mapping via LLM.
    
    Used as fallback when GraphRAG returns incomplete data.
    """

    def __init__(self, temperature: float = 0.1, max_tokens: int = 1024):
        """Initialize the Clinical Mapping Agent."""
        self.llm = NvidiaClient(temperature=temperature, max_tokens=max_tokens)

    def map_query(self, user_query: str) -> ClinicalMappingResult:
        """
        Generate clinical mapping from user query using LLM.
        
        First attempts intelligent extraction for known conditions,
        then uses LLM for enhanced mapping. Falls back to extraction
        if LLM fails or returns invalid data.
        
        Args:
            user_query: The user's health query
            
        Returns:
            ClinicalMappingResult with procedure, category, codes, and confidence
        """
        # Step 1: Always try intelligent extraction first for known conditions
        extracted_procedure = self._intelligent_procedure_extraction(user_query)
        extracted_category = self._get_category_for_procedure(extracted_procedure)
        
        # If we found a specific condition (not generic), use it as baseline
        has_specific_condition = extracted_procedure != "General Consultation"
        
        try:
            # Step 2: Call LLM for clinical mapping
            response = self.llm.simple_prompt(
                prompt=f"{CLINICAL_MAPPING_PROMPT}\n\nUser: \"{user_query}\"",
                system_prompt="You are a precise medical coding assistant. Return only valid JSON.",
                temperature=0.1,
                max_tokens=1024,
            )

            # Parse JSON response
            mapping_data = self._parse_llm_response(response)
            
            # Step 3: Validate and determine final procedure name
            llm_procedure = mapping_data.get("procedure", "")
            
            # Check if LLM returned raw query or invalid data
            llm_invalid = (
                not llm_procedure 
                or llm_procedure.lower().strip() == user_query.lower().strip()
                or len(llm_procedure) > 50
                or llm_procedure == "General Consultation"  # LLM defaulted
            )
            
            if llm_invalid and has_specific_condition:
                # Use our extracted procedure - it's better than LLM's invalid response
                logger.info(f"Using extracted procedure '{extracted_procedure}' instead of LLM result '{llm_procedure}'")
                procedure = extracted_procedure
                category = extracted_category
                confidence = min(mapping_data.get("confidence", 0.7), 0.75)
                rationale = f"LLM mapping validated against extracted procedure for: {user_query}"
            elif llm_invalid:
                # No specific condition found, use extraction fallback
                procedure = extracted_procedure
                category = extracted_category
                confidence = 0.55
                rationale = f"Procedure extracted from query: {user_query}"
            else:
                # LLM returned valid procedure
                procedure = llm_procedure
                category = mapping_data.get("category", extracted_category)
                confidence = mapping_data.get("confidence", 0.7)
                rationale = mapping_data.get("rationale", "")

            # Build result
            return ClinicalMappingResult(
                user_query=user_query,
                procedure=procedure,
                category=category,
                icd10_code=mapping_data.get("icd10_code", self._get_icd10_for_procedure(procedure)),
                icd10_label=mapping_data.get("icd10_label", self._get_icd10_label_for_procedure(procedure)),
                snomed_code=mapping_data.get("snomed_code", self._get_snomed_for_procedure(procedure)),
                confidence=confidence,
                confidence_factors=mapping_data.get("confidence_factors", self._build_confidence_factors(procedure, user_query)),
                mapping_rationale=rationale,
            )

        except Exception as e:
            logger.warning(f"LLM clinical mapping failed, using intelligent extraction: {e}")
            # Step 4: Fall back to extraction-based mapping (fast and reliable)
            return ClinicalMappingResult(
                user_query=user_query,
                procedure=extracted_procedure,
                category=extracted_category,
                icd10_code=self._get_icd10_for_procedure(extracted_procedure),
                icd10_label=self._get_icd10_label_for_procedure(extracted_procedure),
                snomed_code=self._get_snomed_for_procedure(extracted_procedure),
                confidence=0.65 if has_specific_condition else 0.5,
                confidence_factors=self._build_confidence_factors(extracted_procedure, user_query),
                mapping_rationale=f"Intelligent extraction from query (LLM unavailable): {user_query}",
            )

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM JSON response."""
        try:
            # Clean response
            clean = response.strip()
            
            # Remove markdown code blocks if present
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            
            clean = clean.strip()
            
            # Parse JSON
            return json.loads(clean)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response was: {response}")
            # Try to extract basic fields with regex as fallback
            return self._extract_fields_fallback(response)

    def _get_category_for_procedure(self, procedure: str) -> str:
        """Get medical category for a procedure name."""
        category_map = {
            "nephrolithiasis": "Urology",
            "kidney": "Urology",
            "renal": "Urology",
            "urology": "Urology",
            "cardiac": "Cardiology",
            "heart": "Cardiology",
            "coronary": "Cardiology",
            "cabg": "Cardiology",
            "angioplasty": "Cardiology",
            "hypertension": "Cardiology",
            "knee replacement": "Orthopedics",
            "knee": "Orthopedics",
            "hip": "Orthopedics",
            "orthopedic": "Orthopedics",
            "fracture": "Orthopedics",
            "arthritis": "Orthopedics",
            "spine": "Orthopedics",
            "bone": "Orthopedics",
            "joint": "Orthopedics",
            "appendectomy": "General Surgery",
            "hernia": "General Surgery",
            "cholecystectomy": "General Surgery",
            "diabetes": "Endocrinology",
            "thyroid": "Endocrinology",
            "endocrine": "Endocrinology",
            "cataract": "Ophthalmology",
            "eye": "Ophthalmology",
            "vision": "Ophthalmology",
            "cancer": "Oncology",
            "oncology": "Oncology",
            "tumor": "Oncology",
            "chemotherapy": "Oncology",
            "migraine": "Neurology",
            "headache": "Neurology",
            "neurology": "Neurology",
            "seizure": "Neurology",
            "stroke": "Neurology",
            "asthma": "Pulmonology",
            "copd": "Pulmonology",
            "pulmonology": "Pulmonology",
            "breathing": "Pulmonology",
            "ent": "ENT",
            "sinus": "ENT",
            "dental": "Dental",
            "tooth": "Dental",
            "pregnancy": "Obstetrics",
            "gynec": "Gynecology",
            "pcos": "Gynecology",
        }
        procedure_lower = procedure.lower()
        for key, category in category_map.items():
            if key in procedure_lower:
                return category
        return "General Medicine"

    def _get_icd10_for_procedure(self, procedure: str) -> str:
        """Get ICD-10 code for a procedure name."""
        icd_map = {
            "nephrolithiasis": "N20.0",
            "kidney stone": "N20.0",
            "renal stone": "N20.0",
            "calculus of kidney": "N20.0",
            "angioplasty": "I25.10",
            "coronary": "I25.10",
            "cabg": "I25.10",
            "cardiac": "I25.10",
            "knee replacement": "M17.9",
            "knee arthroplasty": "M17.9",
            "osteoarthritis": "M17.9",
            "diabetes": "E11.9",
            "type 2 diabetes": "E11.9",
            "thyroid": "E04.9",
            "cataract": "H25.9",
            "appendectomy": "K35.8",
            "hernia": "K40.9",
            "gallbladder": "K87.0",
            "cholecystectomy": "K87.0",
            "asthma": "J45.9",
            "hypertension": "I10",
            "blood pressure": "I10",
            "arthritis": "M19.90",
            "fracture": "M84.40",
            "cancer": "C80.1",
            "migraine": "G43.9",
            "headache": "R51",
            "pregnancy": "Z34.9",
            "pcos": "E28.2",
            "gynec": "Z01.4",
            "general consultation": "Z71.9",
        }
        procedure_lower = procedure.lower()
        for key, code in icd_map.items():
            if key in procedure_lower:
                return code
        return "Z71.9"  # Person consulting for advice

    def _get_icd10_label_for_procedure(self, procedure: str) -> str:
        """Get ICD-10 label for a procedure name."""
        label_map = {
            "nephrolithiasis": "Calculus of kidney",
            "kidney stone": "Calculus of kidney",
            "renal stone": "Calculus of kidney",
            "angioplasty": "Atherosclerotic heart disease",
            "cabg": "Atherosclerotic heart disease",
            "knee replacement": "Osteoarthritis of knee",
            "knee arthroplasty": "Osteoarthritis of knee",
            "diabetes": "Type 2 diabetes mellitus without complications",
            "thyroid": "Nontoxic goiter",
            "cataract": "Age-related cataract",
            "appendectomy": "Acute appendicitis",
            "hernia": "Inguinal hernia",
            "gallbladder": "Disorders of gallbladder",
            "cholecystectomy": "Disorders of gallbladder",
            "asthma": "Asthma, unspecified",
            "hypertension": "Essential hypertension",
            "blood pressure": "Essential hypertension",
            "arthritis": "Arthritis, unspecified",
            "fracture": "Pathological fracture",
            "cancer": "Malignant neoplasm, primary site unknown",
            "migraine": "Migraine, unspecified",
            "headache": "Headache",
            "pregnancy": "Supervision of normal pregnancy",
            "pcos": "Polycystic ovarian syndrome",
            "gynec": "General gynecological examination",
            "general consultation": "Person consulting for advice",
        }
        procedure_lower = procedure.lower()
        for key, label in label_map.items():
            if key in procedure_lower:
                return label
        return "Person consulting for advice"

    def _get_snomed_for_procedure(self, procedure: str) -> str:
        """Get SNOMED CT code for a procedure name."""
        snomed_map = {
            "nephrolithiasis": "9557008",
            "kidney stone": "9557008",
            "renal stone": "9557008",
            "angioplasty": "36969009",
            "cabg": "232717009",
            "knee replacement": "239873007",
            "knee arthroplasty": "239873007",
            "diabetes": "44054006",
            "type 2 diabetes": "44054006",
            "thyroid": "14304000",
            "cataract": "193570009",
            "appendectomy": "80146002",
            "hernia": "416160007",
            "gallbladder": "30640003",
            "cholecystectomy": "30640003",
            "asthma": "195967001",
            "hypertension": "38341003",
            "blood pressure": "38341003",
            "arthritis": "3723001",
            "fracture": "71620000",
            "cancer": "363346000",
            "migraine": "37796009",
            "pregnancy": "77343006",
            "pcos": "237055002",
            "gynec": "30844001",
            "general consultation": "1142906005",
        }
        procedure_lower = procedure.lower()
        for key, code in snomed_map.items():
            if key in procedure_lower:
                return code
        return "N/A"

    def _build_confidence_factors(self, procedure: str, user_query: str) -> list:
        """Build confidence factors based on extraction quality."""
        factors = []
        
        # Check if specific condition was found
        if procedure != "General Consultation":
            factors.append({
                "key": "condition_extraction",
                "label": "Condition explicitly extracted",
                "score": 90
            })
        else:
            factors.append({
                "key": "keyword_match",
                "label": "Keyword-based matching",
                "score": 50
            })
        
        # Check query clarity
        query_length = len(user_query.split())
        if query_length >= 4:
            factors.append({
                "key": "query_length",
                "label": "Query provides sufficient context",
                "score": 75
            })
        else:
            factors.append({
                "key": "query_length",
                "label": "Query context limited",
                "score": 45
            })
        
        return factors

    def _intelligent_procedure_extraction(self, user_query: str) -> str:
        """
        Intelligently extract a proper medical procedure name from user query.
        Uses keyword matching and common condition mappings.
        """
        query_lower = user_query.lower()
        
        # Common condition mappings
        condition_mappings = {
            # Kidney/Urology
            "kidney stone": "Nephrolithiasis Treatment",
            "kidney stones": "Nephrolithiasis Treatment",
            "renal calculi": "Nephrolithiasis Treatment",
            "kidney pain": "Nephrology Consultation",
            "urinary": "Urology Consultation",
            "bladder": "Urology Consultation",
            
            # Cardiac
            "heart": "Cardiac Consultation",
            "chest pain": "Cardiac Evaluation",
            "heart attack": "Cardiac Emergency Care",
            "angioplasty": "Coronary Angioplasty",
            "bypass": "CABG Surgery",
            "blood pressure": "Hypertension Management",
            
            # Orthopedic
            "knee": "Orthopedic Consultation",
            "knee replacement": "Total Knee Replacement",
            "hip": "Orthopedic Consultation",
            "fracture": "Fracture Treatment",
            "bone": "Orthopedic Consultation",
            "joint": "Orthopedic Consultation",
            "arthritis": "Arthritis Management",
            "back pain": "Spine Evaluation",
            
            # General Surgery
            "appendix": "Appendectomy",
            "hernia": "Hernia Repair",
            "gallbladder": "Cholecystectomy",
            "stone": "Lithotripsy",
            
            # Diabetes/Endocrine
            "diabetes": "Diabetes Mellitus Management",
            "sugar": "Diabetes Mellitus Management",
            "thyroid": "Thyroid Disorder Management",
            
            # Cancer
            "cancer": "Oncology Consultation",
            "tumor": "Oncology Evaluation",
            "chemotherapy": "Chemotherapy Treatment",
            
            # Neurology
            "headache": "Neurology Consultation",
            "migraine": "Migraine Treatment",
            "seizure": "Neurology Evaluation",
            "stroke": "Stroke Management",
            
            # Gastro
            "stomach": "Gastroenterology Consultation",
            "liver": "Hepatology Consultation",
            "digestion": "Gastroenterology Consultation",
            "acidity": "GERD Management",
            
            # Respiratory
            "asthma": "Asthma Management",
            "breathing": "Pulmonology Consultation",
            "lungs": "Pulmonology Consultation",
            
            # ENT
            "ear": "ENT Consultation",
            "nose": "ENT Consultation",
            "throat": "ENT Consultation",
            "sinus": "Sinus Treatment",
            
            # Eye
            "eye": "Ophthalmology Consultation",
            "vision": "Ophthalmology Consultation",
            "cataract": "Cataract Surgery",
            
            # Dental
            "tooth": "Dental Consultation",
            "teeth": "Dental Consultation",
            "dental": "Dental Treatment",
            
            # Women's Health
            "pregnancy": "Obstetrics Consultation",
            "gynec": "Gynecology Consultation",
            "menstrual": "Gynecology Consultation",
            "pcos": "PCOS Management",
            
            # General
            "fever": "General Medicine Consultation",
            "cold": "General Medicine Consultation",
            "cough": "General Medicine Consultation",
            "checkup": "Health Checkup",
            "consultation": "General Consultation",
            "treatment": "Medical Treatment",
            "surgery": "Surgical Consultation",
        }
        
        # Try to match conditions
        for keyword, procedure in condition_mappings.items():
            if keyword in query_lower:
                return procedure
        
        # If no match, try to extract noun phrases
        # Remove common filler words and extract key terms
        filler_words = [
            "i", "have", "has", "had", "me", "my", "mine", "need", "want", 
            "tell", "suggest", "recommend", "what", "where", "how", "who",
            "is", "are", "was", "were", "be", "been", "being",
            "option", "options", "treatment", "procedure", "the", "a", "an",
            "can", "could", "will", "would", "should", "may", "might",
            "please", "help", "advice", "information", "about", "for", "in",
            "at", "on", "with", "from", "to", "of", "and", "or", "but"
        ]
        
        words = query_lower.split()
        key_terms = [w for w in words if w not in filler_words and len(w) > 3]
        
        if key_terms:
            # Capitalize and join with spaces
            return " ".join([w.capitalize() for w in key_terms[:3]]) + " Consultation"
        
        return "General Consultation"

    def _extract_fields_fallback(self, response: str) -> Dict[str, Any]:
        """Extract fields from non-JSON response using simple heuristics."""
        result = {
            "procedure": "General Consultation",
            "category": "General Medicine",
            "icd10_code": "Z71.9",
            "icd10_label": "Person consulting for advice",
            "snomed_code": "N/A",
            "confidence": 0.4,
            "confidence_factors": [],
            "rationale": "Extracted from unstructured response",
        }

        # Try to find procedure
        if "procedure" in response.lower():
            # Extract line with procedure
            for line in response.split("\n"):
                if "procedure" in line.lower() and ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        result["procedure"] = parts[1].strip().strip('",')
                        break

        # Try to find category
        if "category" in response.lower():
            for line in response.split("\n"):
                if "category" in line.lower() and ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        result["category"] = parts[1].strip().strip('",')
                        break

        # Try to find ICD-10
        import re
        icd_match = re.search(r'[A-Z]\d{2}\.\d{1,2}', response)
        if icd_match:
            result["icd10_code"] = icd_match.group(0)

        # Try to find SNOMED
        snomed_match = re.search(r'\d{6,}', response)
        if snomed_match:
            result["snomed_code"] = snomed_match.group(0)

        return result


def generate_clinical_mapping(
    user_query: str,
    graph_rag_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate or enhance clinical mapping.
    
    If GraphRAG provides complete data, enhance it.
    If GraphRAG provides incomplete data, use LLM to fill gaps.
    If no GraphRAG data, generate entirely from LLM.
    
    Args:
        user_query: The user's query
        graph_rag_result: Optional result from GraphRAG
        
    Returns:
        Dict matching the frontend's ClinicalMapping schema
    """
    agent = ClinicalMappingAgent()

    # Check if GraphRAG has complete data
    has_complete_data = (
        graph_rag_result
        and graph_rag_result.get("procedure")
        and graph_rag_result.get("icd10")
        and graph_rag_result.get("icd10", {}).get("code")
    )

    if has_complete_data:
        # Use GraphRAG data, but enhance with LLM if needed
        icd10_data = graph_rag_result.get("icd10", {})
        procedure = graph_rag_result.get("procedure", "")
        
        # If SNOMED is missing, try to get it from LLM (with fallback)
        snomed = icd10_data.get("snomed_code", "")
        if not snomed:
            try:
                llm_result = agent.map_query(user_query)
                snomed = llm_result.snomed_code
            except RuntimeError:
                logger.warning("LLM unavailable for SNOMED lookup, using empty code")
                snomed = ""

        return {
            "user_query": user_query,
            "procedure": procedure,
            "category": icd10_data.get("category", "General Medicine"),
            "icd10_code": icd10_data.get("code", ""),
            "icd10_label": icd10_data.get("label", ""),
            "icd10_description": icd10_data.get("description", ""),
            "snomed_code": snomed,
            "confidence": graph_rag_result.get("confidence_score", 0.7),
            "confidence_factors": [
                {"key": "kg_match", "label": "Knowledge graph match", "score": 85},
                {"key": "icd_mapping", "label": "ICD-10 mapping", "score": 80},
            ],
            "mapping_rationale": "Mapped using knowledge graph with LLM enhancement",
        }

    # Incomplete or no GraphRAG data - use LLM agent with fallback
    logger.info(f"Using LLM clinical mapping for query: {user_query[:50]}...")
    
    try:
        llm_result = agent.map_query(user_query)
        return {
            "user_query": user_query,
            "procedure": llm_result.procedure,
            "category": llm_result.category,
            "icd10_code": llm_result.icd10_code,
            "icd10_label": llm_result.icd10_label,
            "icd10_description": llm_result.icd10_label,
            "snomed_code": llm_result.snomed_code,
            "confidence": llm_result.confidence,
            "confidence_factors": llm_result.confidence_factors,
            "mapping_rationale": llm_result.mapping_rationale,
        }
    except RuntimeError:
        # LLM unavailable - return basic keyword-based mapping
        logger.warning(f"LLM unavailable, returning keyword fallback for: {user_query[:50]}")
        return {
            "user_query": user_query,
            "procedure": user_query[:50],
            "category": "General Medicine",
            "icd10_code": "",
            "icd10_label": "",
            "icd10_description": "",
            "snomed_code": "",
            "confidence": 0.3,
            "confidence_factors": [
                {"key": "keyword_match", "label": "Keyword match (LLM unavailable)", "score": 30},
            ],
            "mapping_rationale": "Limited mapping due to LLM service unavailability",
        }
