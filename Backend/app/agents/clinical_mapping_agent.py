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

RULES:
- If query is vague, make best educated guess and lower confidence
- For symptoms without explicit condition, map to most likely condition
- Use standard medical terminology
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
        
        Args:
            user_query: The user's health query
            
        Returns:
            ClinicalMappingResult with procedure, category, codes, and confidence
        """
        try:
            # Call LLM for clinical mapping
            response = self.llm.simple_prompt(
                prompt=f"{CLINICAL_MAPPING_PROMPT}\n\nUser: \"{user_query}\"",
                system_prompt="You are a precise medical coding assistant. Return only valid JSON.",
                temperature=0.1,
                max_tokens=1024,
            )

            # Parse JSON response
            mapping_data = self._parse_llm_response(response)

            # Build result
            return ClinicalMappingResult(
                user_query=user_query,
                procedure=mapping_data.get("procedure", "General Consultation"),
                category=mapping_data.get("category", "General Medicine"),
                icd10_code=mapping_data.get("icd10_code", "Z71.9"),
                icd10_label=mapping_data.get("icd10_label", "Person consulting for advice"),
                snomed_code=mapping_data.get("snomed_code", "N/A"),
                confidence=mapping_data.get("confidence", 0.5),
                confidence_factors=mapping_data.get("confidence_factors", []),
                mapping_rationale=mapping_data.get("rationale", ""),
            )

        except Exception as e:
            logger.error(f"Clinical mapping failed: {e}")
            # Return safe defaults
            return ClinicalMappingResult(
                user_query=user_query,
                procedure="General Consultation",
                category="General Medicine",
                icd10_code="Z71.9",
                icd10_label="Person consulting for advice",
                snomed_code="N/A",
                confidence=0.3,
                confidence_factors=[
                    {"key": "fallback", "label": "Fallback mapping due to error", "score": 30}
                ],
                mapping_rationale="Error in mapping, using safe defaults",
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
        
        # If SNOMED is missing, try to get it from LLM
        snomed = icd10_data.get("snomed_code", "")
        if not snomed:
            llm_result = agent.map_query(user_query)
            snomed = llm_result.snomed_code

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

    # Incomplete or no GraphRAG data - use LLM agent
    logger.info(f"Using LLM clinical mapping for query: {user_query[:50]}...")
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
