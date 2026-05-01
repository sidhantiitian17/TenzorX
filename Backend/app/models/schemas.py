"""
Pydantic schemas for API request/response validation.

This module defines the data models for the TenzorX Healthcare Navigator API,
ensuring type safety and automatic validation for all incoming requests.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Location(BaseModel):
    """
    Geographic location for the healthcare query.
    
    Supports both city-based (tier) and coordinate-based (lat/lon) location specification.
    """
    city: Optional[str] = Field(
        None, 
        description="City name (e.g., 'Mumbai', 'Delhi')",
        min_length=1,
        max_length=100
    )
    tier: Optional[str] = Field(
        None, 
        description="City tier classification (e.g., 'Tier-1', 'Tier-2', 'Tier-3')",
        pattern="^(Tier-[1-3]|[A-Za-z]+)$"
    )
    latitude: Optional[float] = Field(
        None, 
        description="Latitude coordinate (WGS84)",
        ge=-90,
        le=90
    )
    longitude: Optional[float] = Field(
        None, 
        description="Longitude coordinate (WGS84)",
        ge=-180,
        le=180
    )
    
    class Config:
        """Pydantic config for JSON schema generation."""
        json_schema_extra = {
            "example": {
                "city": "Mumbai",
                "tier": "Tier-1",
                "latitude": 19.0760,
                "longitude": 72.8777
            }
        }


class PatientProfile(BaseModel):
    """
    Patient medical and demographic information.
    
    Captures optional personal health data to personalize cost estimates and recommendations.
    """
    age: Optional[int] = Field(
        None, 
        description="Patient age in years",
        ge=0,
        le=150
    )
    known_comorbidities: List[str] = Field(
        default_factory=list,
        description="List of known medical conditions (e.g., ['diabetes', 'hypertension'])",
        max_items=10
    )
    
    class Config:
        """Pydantic config for JSON schema generation."""
        json_schema_extra = {
            "example": {
                "age": 45,
                "known_comorbidities": ["diabetes", "hypertension"]
            }
        }


class FinancialProfile(BaseModel):
    """
    Patient financial constraints and income information.
    
    Used for personalized cost estimation and EMI calculations.
    """
    budget_limit: float = Field(
        ..., 
        description="Maximum budget for healthcare in INR",
        gt=0,
        le=10000000
    )
    gross_monthly_income: float = Field(
        ..., 
        description="Gross monthly income in INR",
        gt=0,
        le=50000000
    )
    existing_emis: float = Field(
        default=0.0,
        description="Existing monthly EMI obligations in INR",
        ge=0,
        le=10000000
    )
    
    @field_validator("existing_emis")
    @classmethod
    def validate_existing_emis(cls, v, info):
        """Ensure existing EMIs don't exceed 50% of gross monthly income."""
        if "gross_monthly_income" in info.data:
            max_emi = info.data["gross_monthly_income"] * 0.5
            if v > max_emi:
                raise ValueError(
                    f"Existing EMIs ({v}) cannot exceed 50% of gross monthly income ({max_emi})"
                )
        return v
    
    class Config:
        """Pydantic config for JSON schema generation."""
        json_schema_extra = {
            "example": {
                "budget_limit": 500000,
                "gross_monthly_income": 150000,
                "existing_emis": 25000
            }
        }


class UserQueryRequest(BaseModel):
    """
    Main API request payload for healthcare navigator queries.
    
    Combines natural language query with structured patient, financial, and location data.
    """
    query: str = Field(
        ..., 
        description="Natural language healthcare query (e.g., 'I need cardiac surgery with minimal cost')",
        min_length=10,
        max_length=1000
    )
    location: Optional[Location] = Field(
        None,
        description="Geographic location for the query"
    )
    patient_profile: Optional[PatientProfile] = Field(
        None,
        description="Patient medical and demographic information"
    )
    financial_profile: Optional[FinancialProfile] = Field(
        None,
        description="Patient financial constraints and capacity"
    )
    session_id: Optional[str] = Field(
        None,
        description="Optional session identifier for tracking multi-turn conversations",
        min_length=1,
        max_length=100
    )
    
    class Config:
        """Pydantic config for JSON schema generation."""
        json_schema_extra = {
            "example": {
                "query": "I need cardiac bypass surgery with minimal out-of-pocket cost",
                "location": {
                    "city": "Mumbai",
                    "tier": "Tier-1",
                    "latitude": 19.0760,
                    "longitude": 72.8777
                },
                "patient_profile": {
                    "age": 55,
                    "known_comorbidities": ["diabetes", "hypertension"]
                },
                "financial_profile": {
                    "budget_limit": 500000,
                    "gross_monthly_income": 150000,
                    "existing_emis": 25000
                },
                "session_id": "session_uuid_here"
            }
        }
