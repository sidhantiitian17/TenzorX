"""
Request Models (Pydantic).

Defines request schemas for API endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PatientProfile(BaseModel):
    """Patient profile for personalization - per instructionagent.md Section 2.1."""
    age: Optional[int] = None
    gender: Optional[str] = None
    comorbidities: List[str] = []
    budget_max: Optional[float] = None
    budget_inr: Optional[float] = None  # Frontend uses budget_inr
    lat: Optional[float] = None
    lon: Optional[float] = None
    location: Optional[str] = None
    insurance: Optional[bool] = False
    insurance_type: Optional[str] = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint - per instructionagent.md Section 6."""
    session_id: str = Field(..., description="Unique session identifier per user")
    message: str = Field(..., min_length=1, max_length=2000)
    location: Optional[str] = None
    patient_profile: Optional[PatientProfile] = None
    lender_mode: bool = False
    
    class Config:
        # Allow extra fields for forward compatibility
        extra = "allow"


class CostRequest(BaseModel):
    """Request model for cost estimation."""
    procedure: str
    city: str
    comorbidities: Optional[List[str]] = []
    age: Optional[int] = None


class LoanRequest(BaseModel):
    """Request model for loan eligibility."""
    total_treatment_cost: float = Field(..., gt=0)
    gross_monthly_income: float = Field(..., gt=0)
    existing_emis: float = Field(default=0, ge=0)


class CompareRequest(BaseModel):
    """Request model for hospital comparison."""
    hospital_ids: List[str] = Field(..., min_length=2, max_length=3)
    procedure: str
    user_lat: Optional[float] = None
    user_lon: Optional[float] = None
    budget_max: Optional[float] = None
