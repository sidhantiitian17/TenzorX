"""
Response Models (Pydantic).

Defines response schemas for API endpoints per instructionagent.md specification.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Core Confidence & XAI Models
# ============================================================================

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


class ConfidenceDrivers(BaseModel):
    """Confidence driver breakdown per instructionagent.md Section 3.6"""
    data_availability: int
    pricing_consistency: int
    benchmark_recency: int
    patient_complexity: int


class SHAPContribution(BaseModel):
    """SHAP contribution for a single factor"""
    factor: str
    impact: Literal["positive", "negative"]
    delta: str


class SHAPExplanation(BaseModel):
    """SHAP waterfall explanation for hospital fusion scores"""
    hospital_id: str
    contributors: List[SHAPContribution]


class XAIExplainerOutput(BaseModel):
    """XAI Explainer Agent output per instructionagent.md Section 3.6"""
    confidence_score: int
    confidence_drivers: ConfidenceDrivers
    top_hospital_shap: Optional[SHAPExplanation] = None
    triage_lime: Optional[List[Dict[str, Any]]] = None
    show_uncertainty_banner: bool
    disclaimer: str


# ============================================================================
# NER + Triage Agent Output
# ============================================================================

class NERTriageOutput(BaseModel):
    """NER + Triage Agent output per instructionagent.md Section 3.1"""
    agent: str = "ner_triage"
    canonical_procedure: str
    category: str
    icd10: str
    snomed_ct: str
    city: str
    city_tier: int
    budget_inr: Optional[int] = None
    triage: Literal["RED", "YELLOW", "GREEN"]
    mapping_confidence: int
    extracted_comorbidities: List[str]


# ============================================================================
# Clinical Pathway Agent Output
# ============================================================================

class PathwayStep(BaseModel):
    """Single step in treatment pathway"""
    step: int
    name: str
    duration: str
    cost_min: int
    cost_max: int


class ComorbidityImpact(BaseModel):
    """Comorbidity cost impact"""
    condition: str
    add_min: int
    add_max: int


class ClinicalPathwayOutput(BaseModel):
    """Clinical Pathway Agent output per instructionagent.md Section 3.2"""
    agent: str = "clinical_pathway"
    pathway_steps: List[PathwayStep]
    total_min: int
    total_max: int
    comorbidity_impacts: List[ComorbidityImpact]
    cost_confidence: int
    geo_adjustment_note: str


# ============================================================================
# Hospital Discovery Agent Output
# ============================================================================

class ABSAScores(BaseModel):
    """Aspect-Based Sentiment Analysis scores"""
    doctors_services: float
    staff_services: float
    hospital_facilities: float
    affordability: float


class HospitalSHAPExplanation(BaseModel):
    """SHAP explanation embedded in hospital output"""
    clinical_contribution: str
    accessibility_contribution: str
    affordability_contribution: str


class HospitalOutput(BaseModel):
    """Single hospital in discovery results"""
    id: str
    name: str
    address: str
    lat: float
    lng: float
    distance_km: float
    tier: Literal["budget", "mid-tier", "premium"]
    rating: float
    nabh: bool
    cost_min: int
    cost_max: int
    cost_confidence: int
    fusion_score: float
    tags: List[str]
    appointment_proxy: str
    specialties: List[str]
    absa_scores: ABSAScores
    shap_explanation: HospitalSHAPExplanation


class MapMarker(BaseModel):
    """Map marker for Leaflet.js"""
    id: str
    lat: float
    lng: float
    tier: str
    color: str


class HospitalDiscoveryOutput(BaseModel):
    """Hospital Discovery Agent output per instructionagent.md Section 3.3"""
    agent: str = "hospital_discovery"
    result_count: int
    hospitals: List[HospitalOutput]
    map_markers: List[MapMarker]


# ============================================================================
# Financial Engine Agent Output
# ============================================================================

class EMICalculatorOutput(BaseModel):
    """EMI calculation result"""
    loan_amount: int
    tenure_months: int
    annual_rate_pct: float
    monthly_emi: int
    total_repayment: int


class CostRange(BaseModel):
    """Min-max cost range"""
    min: int
    max: int


class TierCostComparison(BaseModel):
    """Cost comparison by hospital tier"""
    budget: CostRange
    mid_tier: CostRange
    premium: CostRange


class DTIAssessment(BaseModel):
    """DTI risk assessment per instructionagent.md"""
    risk_level: Literal["Low", "Medium", "High", "Critical"]
    rate_range: str
    cta: str
    dti_percentage: float


class GovernmentScheme(BaseModel):
    """Government healthcare scheme"""
    name: str
    coverage: str
    url: str
    eligibility: str


class LendingPartner(BaseModel):
    """Lending partner for medical loans"""
    name: str
    range: str
    tat: str


class CostBreakdownItem(BaseModel):
    """Item in cost breakdown"""
    label: str
    min: int
    max: int


class FinancialEngineOutput(BaseModel):
    """Financial Engine Agent output per instructionagent.md Section 3.4"""
    agent: str = "financial_engine"
    total_cost_range: CostRange
    typical_range: CostRange
    tier_cost_comparison: TierCostComparison
    emi_calculator: EMICalculatorOutput
    dti_assessment: Optional[DTIAssessment] = None
    government_schemes: List[GovernmentScheme]
    lending_partners: List[LendingPartner]
    cost_breakdown_items: List[CostBreakdownItem]
    comorbidity_surcharges: List[ComorbidityImpact]


# ============================================================================
# Geo-Spatial Agent Output
# ============================================================================

class UserCoords(BaseModel):
    """User coordinates"""
    lat: float
    lng: float


class MapConfig(BaseModel):
    """Map configuration for Leaflet.js"""
    center: List[float]
    zoom: int
    tile_layer: str
    legend: Dict[str, str]


class GeoSpatialOutput(BaseModel):
    """Geo-Spatial Agent output per instructionagent.md Section 3.5"""
    agent: str = "geo_spatial"
    user_coords: UserCoords
    city_tier: int
    hospital_markers: List[Dict[str, Any]]
    map_config: MapConfig


# ============================================================================
# Appointment & Paperwork Agent Output
# ============================================================================

class ChecklistForm(BaseModel):
    """Form template reference"""
    name: str
    generate_url: str


class AppointmentChecklist(BaseModel):
    """Generated checklist for appointment"""
    documents: List[str]
    questions: List[str]
    forms: List[ChecklistForm]


class AppointmentRequest(BaseModel):
    """Appointment request stored in session"""
    id: str
    doctor_name: str
    hospital_name: str
    date: str
    time: str
    status: Literal["requested", "confirmed", "cancelled"]
    procedure: str


class AppointmentPaperworkOutput(BaseModel):
    """Appointment & Paperwork Agent output per instructionagent.md Section 3.7"""
    agent: str = "appointment_paperwork"
    checklist: AppointmentChecklist
    appointment_requests: List[AppointmentRequest]


# ============================================================================
# Master Response Schema
# ============================================================================

class ChatResponseData(BaseModel):
    """Chat response for Master Response Schema"""
    message: str = ""
    timestamp: str = ""
    triage_level: Literal["RED", "YELLOW", "GREEN"] = "GREEN"
    offline_mode: bool = False
    confidence_score: Optional[float] = None
    disclaimer: Optional[str] = None
    
    class Config:
        extra = "allow"


class ResultsPanelData(BaseModel):
    """Results panel data for Master Response Schema"""
    visible: bool = True
    active_tab: Literal["list", "map"] = "list"
    clinical_interpretation: Optional[NERTriageOutput] = None
    pathway: Optional[ClinicalPathwayOutput] = None
    cost_estimate: Optional[FinancialEngineOutput] = None
    hospitals: Optional[HospitalDiscoveryOutput] = None
    map_data: Optional[GeoSpatialOutput] = None
    xai: Optional[XAIExplainerOutput] = None
    checklist: Optional[AppointmentChecklist] = None
    financial_assistance: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"


class SessionUpdates(BaseModel):
    """Session updates for Master Response Schema"""
    last_procedure: Optional[str] = None
    history_entry: str = ""
    
    class Config:
        extra = "allow"


class MasterResponse(BaseModel):
    """Master Orchestrator output schema per instructionagent.md Section 4.3"""
    chat_response: ChatResponseData = Field(default_factory=ChatResponseData)
    results_panel: ResultsPanelData = Field(default_factory=ResultsPanelData)
    session_updates: SessionUpdates = Field(default_factory=SessionUpdates)
    
    class Config:
        extra = "allow"


# ============================================================================
# Legacy Models (maintained for compatibility)
# ============================================================================

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


# ============================================================================
# EMI Endpoint Models
# ============================================================================

class EMIRequest(BaseModel):
    """Request for EMI calculation"""
    principal: float = Field(..., gt=0)
    annual_rate_pct: float = Field(..., gt=0)
    tenure_months: int = Field(..., ge=6, le=60)


class EMIResponse(BaseModel):
    """Response from EMI calculation"""
    monthly_emi: int
    total_repayment: int


# ============================================================================
# Session Endpoint Models
# ============================================================================

class PatientProfile(BaseModel):
    """Patient profile for personalization"""
    age: Optional[int] = None
    comorbidities: List[str] = []
    budget_inr: Optional[int] = None
    insurance: bool = False


class UserLocation(BaseModel):
    """User location data"""
    city: str
    state: str
    lat: float
    lng: float


class SessionState(BaseModel):
    """Full session state per instructionagent.md Section 2.1"""
    session_id: str
    user_location: Optional[UserLocation] = None
    patient_profile: PatientProfile
    conversation_history: List[Dict[str, Any]] = []
    last_procedure: Optional[str] = None
    last_results: Optional[Dict[str, Any]] = None
    saved_results: List[Dict[str, Any]] = []
    appointment_requests: List[AppointmentRequest] = []


class AppointmentStatusUpdate(BaseModel):
    """Request to update appointment status"""
    appointment_id: str
    status: Literal["requested", "confirmed", "cancelled"]


class AppointmentUpdateResponse(BaseModel):
    """Response from appointment status update"""
    success: bool
    appointment: AppointmentRequest


# ============================================================================
# Feedback Endpoint Models
# ============================================================================

class FeedbackRequest(BaseModel):
    """Request for feedback submission per instructionagent.md Section 6"""
    session_id: str
    original_query: str
    mapped_procedure: str
    user_correction: str


class FeedbackResponse(BaseModel):
    """Response from feedback submission"""
    success: bool
    message: str


# ============================================================================
# Save Result Endpoint Models
# ============================================================================

class SaveResultRequest(BaseModel):
    """Request to save current results"""
    session_id: str
    result_data: Dict[str, Any]


class SaveResultResponse(BaseModel):
    """Response from save result"""
    success: bool
    saved_count: int


# ============================================================================
# Lender/Insurer Mode Models
# ============================================================================

class LenderUnderwriteRequest(BaseModel):
    """Request for lender underwrite per instructionagent.md Section 7"""
    procedure: str
    city: str
    patient_income_monthly: float
    existing_emis: float
    loan_amount_requested: float
    tenure_months: int


class HospitalTierDistribution(BaseModel):
    """Pricing tier distribution for a geography"""
    tier: str
    hospital_count: int
    avg_cost_min: int
    avg_cost_max: int


class LenderUnderwriteResponse(BaseModel):
    """Response for lender underwrite"""
    procedure: str
    city: str
    dti_assessment: DTIAssessment
    tier_distribution: List[HospitalTierDistribution]
    shap_attribution: Optional[Dict[str, Any]] = None
    recommendation: str
