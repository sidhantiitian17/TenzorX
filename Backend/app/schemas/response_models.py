"""
Response Models (Pydantic).

Defines response schemas for API endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ConfidenceScore(BaseModel):
    """RAG confidence score breakdown."""
    composite_score: float
    faithfulness: float
    contextual_relevancy: float
    answer_relevancy: float
    rationale: str
    below_threshold: bool
    show_uncertainty_indicator: bool
    label: str


class SearchData(BaseModel):
    """Structured search data for frontend."""
    emergency: bool = False
    query_interpretation: str = ""
    procedure: str = ""
    icd10_code: str = ""
    icd10_label: str = ""
    snomed_code: str = ""
    medical_category: str = ""
    pathway: List[Dict[str, Any]] = []
    mapping_confidence: float = 0.0
    location: str = ""
    cost_estimate: Dict[str, Any] = {}
    hospitals: List[Dict[str, Any]] = []
    comorbidity_warnings: List[str] = []
    data_sources: List[str] = []


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    session_id: str
    narrative: str
    search_data: SearchData
    severity: str
    is_emergency: bool
    confidence: ConfidenceScore
