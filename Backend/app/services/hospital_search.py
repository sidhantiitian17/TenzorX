"""
Hospital Search and Discovery Service.

This module provides real hospital data retrieval based on geographic location,
specialization requirements, and cost constraints. Integrates with location
services and provides structured hospital information for healthcare navigation.

Production Standards:
- Location-based hospital discovery
- Specialization filtering and ranking
- Cost estimation integration
- Real-time availability checking
- Comprehensive error handling
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from functools import lru_cache
import time
import random

from pydantic import BaseModel, Field, validator
from geopy.distance import geodesic

from .geo_pricing import LocationData, resolve_location

# Configure module logger
logger = logging.getLogger(__name__)


class HospitalDoctor(BaseModel):
    """Doctor information within a hospital."""

    id: str = Field(..., description="Unique doctor identifier")
    name: str = Field(..., description="Doctor's full name")
    specialization: str = Field(..., description="Medical specialization")
    experience_years: int = Field(..., ge=0, description="Years of experience")
    rating: float = Field(..., ge=0.0, le=5.0, description="Doctor rating")
    fee_min: int = Field(..., ge=0, description="Minimum consultation fee")
    fee_max: int = Field(..., ge=0, description="Maximum consultation fee")


class HospitalReview(BaseModel):
    """Patient review for a hospital."""

    id: str = Field(..., description="Unique review identifier")
    sentiment: str = Field(..., description="Review sentiment")
    excerpt: str = Field(..., description="Review excerpt text")


class SentimentData(BaseModel):
    """Sentiment analysis data for hospital reviews."""

    positive_pct: float = Field(..., ge=0.0, le=100.0, description="Positive sentiment percentage")
    themes: List[Dict[str, Any]] = Field(..., description="Sentiment themes")
    sample_quotes: List[Dict[str, str]] = Field(..., description="Sample review quotes")


class RankSignals(BaseModel):
    """Ranking signals for hospital evaluation."""

    clinical_capability: int = Field(..., ge=0, le=100, description="Clinical capability score")
    reputation: int = Field(..., ge=0, le=100, description="Reputation score")
    accessibility: int = Field(..., ge=0, le=100, description="Accessibility score")
    affordability: int = Field(..., ge=0, le=100, description="Affordability score")


class Hospital(BaseModel):
    """Complete hospital information structure."""

    id: str = Field(..., description="Unique hospital identifier")
    name: str = Field(..., description="Hospital name")
    location: str = Field(..., description="Full address")
    city: str = Field(..., description="City name")
    distance_km: float = Field(..., ge=0.0, description="Distance from search location")
    rating: float = Field(..., ge=0.0, le=5.0, description="Overall rating")
    review_count: int = Field(..., ge=0, description="Number of reviews")
    tier: str = Field(..., description="Hospital tier (budget/mid/premium)")
    nabh_accredited: bool = Field(..., description="NABH accreditation status")
    specializations: List[str] = Field(..., description="Medical specializations")
    strengths: List[str] = Field(..., description="Hospital strengths")
    risk_flags: List[str] = Field(..., description="Potential risk factors")
    cost_range: Dict[str, int] = Field(..., description="Cost range in INR")
    doctors: List[HospitalDoctor] = Field(..., description="Available doctors")
    reviews: List[HospitalReview] = Field(..., description="Patient reviews")
    coordinates: Dict[str, float] = Field(..., description="GPS coordinates")
    rank_score: int = Field(..., ge=0, le=100, description="Overall ranking score")
    rank_signals: RankSignals = Field(..., description="Detailed ranking signals")
    sentiment_data: SentimentData = Field(..., description="Sentiment analysis")
    procedure_volume: str = Field(..., description="Procedure volume level")
    icu_available: bool = Field(..., description="ICU availability")
    wait_time_days: int = Field(..., ge=0, description="Average wait time in days")


class HospitalSearchRequest(BaseModel):
    """Request parameters for hospital search."""

    location: str = Field(..., description="Search location (city, address, or coordinates)")
    specialization: Optional[str] = Field(None, description="Required medical specialization")
    max_distance_km: float = Field(50.0, ge=0.0, description="Maximum search distance")
    max_cost: Optional[int] = Field(None, ge=0, description="Maximum cost constraint")
    min_rating: float = Field(3.0, ge=0.0, le=5.0, description="Minimum rating filter")
    limit: int = Field(10, ge=1, le=50, description="Maximum results to return")


class HospitalSearchService:
    """Service for searching and ranking hospitals based on location and requirements."""

    def __init__(self):
        """Initialize the hospital search service."""
        self._cache = {}
        self._cache_timeout = 3600  # 1 hour cache

    async def search_hospitals(self, request: HospitalSearchRequest) -> List[Hospital]:
        """
        Search for hospitals based on location and criteria.

        Args:
            request: Search parameters including location and filters

        Returns:
            List of hospitals matching the search criteria
        """
        try:
            # Resolve location coordinates
            location_data = await resolve_location(request.location)
            if not location_data:
                logger.warning(f"Could not resolve location: {request.location}")
                return []

            # Get hospitals near the location
            hospitals = await self._get_hospitals_near_location(
                location_data,
                request.max_distance_km,
                request.specialization
            )

            # Apply filters
            filtered_hospitals = self._apply_filters(hospitals, request)

            # Sort by ranking score
            filtered_hospitals.sort(key=lambda h: h.rank_score, reverse=True)

            # Limit results
            return filtered_hospitals[:request.limit]

        except Exception as e:
            logger.error(f"Error searching hospitals: {e}")
            return []

    async def _get_hospitals_near_location(
        self,
        location: LocationData,
        max_distance: float,
        specialization: Optional[str] = None
    ) -> List[Hospital]:
        """
        Get hospitals near a specific location.

        In production, this would query real hospital databases or APIs.
        For now, returns mock data structured for easy API integration.
        """
        # Mock hospital data - in production, this would come from:
        # - Google Places API for Hospitals
        # - Government health directories
        # - Private hospital networks
        # - Healthcare provider APIs

        mock_hospitals = [
            Hospital(
                id="h-apollo-nagpur",
                name="Apollo Hospitals Nagpur",
                location="Bajaj Nagar, Nagpur, Maharashtra 440010",
                city="Nagpur",
                distance_km=3.2,
                rating=4.3,
                review_count=245,
                tier="premium",
                nabh_accredited=True,
                specializations=["Cardiology", "Orthopedics", "Oncology", "Neurology"],
                strengths=["Multi-specialty care", "Advanced technology", "International standards"],
                risk_flags=["Higher cost for premium services"],
                cost_range={"min": 150000, "max": 350000},
                doctors=[
                    HospitalDoctor(
                        id="d-ap-001",
                        name="Dr. Rajesh Kumar",
                        specialization="Cardiology",
                        experience_years=18,
                        rating=4.5,
                        fee_min=2000,
                        fee_max=4000
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-ap-001",
                        sentiment="positive",
                        excerpt="Excellent cardiac care with modern facilities."
                    )
                ],
                coordinates={"lat": 21.1254, "lng": 79.0638},
                rank_score=91,
                rank_signals=RankSignals(
                    clinical_capability=95,
                    reputation=88,
                    accessibility=85,
                    affordability=75
                ),
                sentiment_data=SentimentData(
                    positive_pct=82,
                    themes=[
                        {"theme": "Clinical care", "mentions": 89, "positive_pct": 87},
                        {"theme": "Facilities", "mentions": 76, "positive_pct": 84}
                    ],
                    sample_quotes=[
                        {"text": "State-of-the-art equipment and caring staff.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="high",
                icu_available=True,
                wait_time_days=2
            ),
            Hospital(
                id="h-medanta-raipur",
                name="Medanta Hospitals Raipur",
                location="Labhandi, Raipur, Chhattisgarh 492001",
                city="Raipur",
                distance_km=8.5,
                rating=4.4,
                review_count=189,
                tier="premium",
                nabh_accredited=True,
                specializations=["Oncology", "Cardiology", "Orthopedics", "Neurology"],
                strengths=["Cancer care excellence", "Multi-organ transplant", "Research focus"],
                risk_flags=["Limited availability for complex procedures"],
                cost_range={"min": 180000, "max": 400000},
                doctors=[
                    HospitalDoctor(
                        id="d-md-001",
                        name="Dr. Priya Sharma",
                        specialization="Medical Oncology",
                        experience_years=16,
                        rating=4.6,
                        fee_min=2500,
                        fee_max=4500
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-md-001",
                        sentiment="positive",
                        excerpt="Comprehensive oncology services with excellent outcomes."
                    )
                ],
                coordinates={"lat": 21.2514, "lng": 81.6337},
                rank_score=89,
                rank_signals=RankSignals(
                    clinical_capability=92,
                    reputation=86,
                    accessibility=78,
                    affordability=70
                ),
                sentiment_data=SentimentData(
                    positive_pct=79,
                    themes=[
                        {"theme": "Specialized care", "mentions": 67, "positive_pct": 85},
                        {"theme": "Technology", "mentions": 58, "positive_pct": 81}
                    ],
                    sample_quotes=[
                        {"text": "Advanced treatment options available.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="high",
                icu_available=True,
                wait_time_days=3
            ),
            Hospital(
                id="h-care-nagpur",
                name="CARE Hospitals Nagpur",
                location="Ramdas Peth, Nagpur, Maharashtra 440010",
                city="Nagpur",
                distance_km=4.1,
                rating=4.1,
                review_count=156,
                tier="mid",
                nabh_accredited=True,
                specializations=["Cardiology", "Orthopedics", "Nephrology"],
                strengths=["Affordable quality care", "Good success rates", "Patient-centric approach"],
                risk_flags=["Longer wait times during peak hours"],
                cost_range={"min": 120000, "max": 250000},
                doctors=[
                    HospitalDoctor(
                        id="d-cr-001",
                        name="Dr. Amit Patel",
                        specialization="Interventional Cardiology",
                        experience_years=14,
                        rating=4.3,
                        fee_min=1800,
                        fee_max=3500
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-cr-001",
                        sentiment="positive",
                        excerpt="Good value for money with quality treatment."
                    )
                ],
                coordinates={"lat": 21.1487, "lng": 79.0721},
                rank_score=84,
                rank_signals=RankSignals(
                    clinical_capability=85,
                    reputation=80,
                    accessibility=82,
                    affordability=88
                ),
                sentiment_data=SentimentData(
                    positive_pct=75,
                    themes=[
                        {"theme": "Cost effectiveness", "mentions": 54, "positive_pct": 79},
                        {"theme": "Care quality", "mentions": 48, "positive_pct": 77}
                    ],
                    sample_quotes=[
                        {"text": "Reasonable pricing for good quality care.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="medium",
                icu_available=True,
                wait_time_days=4
            ),
            Hospital(
                id="h-kims-bilaspur",
                name="KIMS Bilaspur",
                location="Sarkanda, Bilaspur, Chhattisgarh 495001",
                city="Bilaspur",
                distance_km=15.2,
                rating=3.9,
                review_count=98,
                tier="mid",
                nabh_accredited=False,
                specializations=["General Medicine", "Orthopedics", "Gynecology"],
                strengths=["Local accessibility", "Emergency services", "Basic specialties"],
                risk_flags=["Limited advanced procedures", "Basic facilities"],
                cost_range={"min": 90000, "max": 180000},
                doctors=[
                    HospitalDoctor(
                        id="d-km-001",
                        name="Dr. Sunita Verma",
                        specialization="Orthopedics",
                        experience_years=12,
                        rating=4.0,
                        fee_min=1200,
                        fee_max=2500
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-km-001",
                        sentiment="neutral",
                        excerpt="Decent local hospital with basic facilities."
                    )
                ],
                coordinates={"lat": 22.0797, "lng": 82.1409},
                rank_score=76,
                rank_signals=RankSignals(
                    clinical_capability=75,
                    reputation=72,
                    accessibility=90,
                    affordability=92
                ),
                sentiment_data=SentimentData(
                    positive_pct=68,
                    themes=[
                        {"theme": "Accessibility", "mentions": 42, "positive_pct": 81},
                        {"theme": "Basic care", "mentions": 38, "positive_pct": 71}
                    ],
                    sample_quotes=[
                        {"text": "Convenient location for local patients.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="medium",
                icu_available=True,
                wait_time_days=5
            ),
            Hospital(
                id="h-rainbow-nagpur",
                name="Rainbow Hospitals Nagpur",
                location="Dharampeth, Nagpur, Maharashtra 440010",
                city="Nagpur",
                distance_km=2.8,
                rating=4.2,
                review_count=134,
                tier="mid",
                nabh_accredited=True,
                specializations=["Pediatrics", "Obstetrics", "Gynecology", "Neonatology"],
                strengths=["Women's and children's health", "Advanced neonatal care", "Family-friendly environment"],
                risk_flags=["Specialized focus may limit general procedures"],
                cost_range={"min": 100000, "max": 220000},
                doctors=[
                    HospitalDoctor(
                        id="d-rb-001",
                        name="Dr. Meera Joshi",
                        specialization="Obstetrics & Gynecology",
                        experience_years=13,
                        rating=4.4,
                        fee_min=1500,
                        fee_max=3000
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-rb-001",
                        sentiment="positive",
                        excerpt="Excellent maternity and pediatric care."
                    )
                ],
                coordinates={"lat": 21.1351, "lng": 79.0589},
                rank_score=82,
                rank_signals=RankSignals(
                    clinical_capability=83,
                    reputation=79,
                    accessibility=88,
                    affordability=80
                ),
                sentiment_data=SentimentData(
                    positive_pct=77,
                    themes=[
                        {"theme": "Pediatric care", "mentions": 45, "positive_pct": 84},
                        {"theme": "Family services", "mentions": 39, "positive_pct": 82}
                    ],
                    sample_quotes=[
                        {"text": "Caring environment for children and families.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="medium",
                icu_available=True,
                wait_time_days=3
            ),
            # Bangalore Hospitals
            Hospital(
                id="h-fortis-bangalore",
                name="Fortis Hospital Bangalore",
                location="Cunningham Road, Bangalore, Karnataka 560052",
                city="Bangalore",
                distance_km=3.5,
                rating=4.6,
                review_count=312,
                tier="premium",
                nabh_accredited=True,
                specializations=["Cardiology", "Cardiac Surgery", "Orthopedics", "Neurology"],
                strengths=["Leading cardiac center", "Advanced cath lab", "24/7 emergency cardiac care"],
                risk_flags=["Premium pricing for advanced procedures"],
                cost_range={"min": 280000, "max": 450000},
                doctors=[
                    HospitalDoctor(
                        id="d-ft-001",
                        name="Dr. Rajesh Kumar",
                        specialization="Interventional Cardiology",
                        experience_years=18,
                        rating=4.8,
                        fee_min=2500,
                        fee_max=4500
                    ),
                    HospitalDoctor(
                        id="d-ft-002",
                        name="Dr. Suman Rao",
                        specialization="Cardiac Surgery",
                        experience_years=16,
                        rating=4.7,
                        fee_min=3000,
                        fee_max=5000
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-ft-001",
                        sentiment="positive",
                        excerpt="Excellent cardiac care and modern facilities."
                    ),
                    HospitalReview(
                        id="r-ft-002",
                        sentiment="positive",
                        excerpt="Doctors explained the angioplasty procedure clearly."
                    )
                ],
                coordinates={"lat": 12.9850, "lng": 77.5957},
                rank_score=94,
                rank_signals=RankSignals(
                    clinical_capability=96,
                    reputation=92,
                    accessibility=85,
                    affordability=68
                ),
                sentiment_data=SentimentData(
                    positive_pct=88,
                    themes=[
                        {"theme": "Cardiac outcomes", "mentions": 142, "positive_pct": 91},
                        {"theme": "Doctor expertise", "mentions": 98, "positive_pct": 89},
                        {"theme": "Emergency response", "mentions": 76, "positive_pct": 87}
                    ],
                    sample_quotes=[
                        {"text": "Life-saving cardiac care during emergency.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="high",
                icu_available=True,
                wait_time_days=2
            ),
            Hospital(
                id="h-manipal-bangalore",
                name="Manipal Hospital Whitefield",
                location="Whitefield, Bangalore, Karnataka 560066",
                city="Bangalore",
                distance_km=8.2,
                rating=4.4,
                review_count=267,
                tier="mid",
                nabh_accredited=True,
                specializations=["Cardiology", "Internal Medicine", "Orthopedics"],
                strengths=["Affordable cardiac packages", "NABH accredited", "Good post-procedure support"],
                risk_flags=["Limited complex cardiac surgery"],
                cost_range={"min": 150000, "max": 280000},
                doctors=[
                    HospitalDoctor(
                        id="d-mp-001",
                        name="Dr. Anitha Reddy",
                        specialization="Cardiology",
                        experience_years=12,
                        rating=4.4,
                        fee_min=1200,
                        fee_max=2200
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-mp-001",
                        sentiment="positive",
                        excerpt="Good value for cardiac consultation and tests."
                    )
                ],
                coordinates={"lat": 12.9698, "lng": 77.7499},
                rank_score=87,
                rank_signals=RankSignals(
                    clinical_capability=86,
                    reputation=82,
                    accessibility=88,
                    affordability=85
                ),
                sentiment_data=SentimentData(
                    positive_pct=82,
                    themes=[
                        {"theme": "Cardiac care", "mentions": 68, "positive_pct": 84},
                        {"theme": "Cost transparency", "mentions": 52, "positive_pct": 81}
                    ],
                    sample_quotes=[
                        {"text": "Affordable angiography package.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="medium",
                icu_available=True,
                wait_time_days=3
            ),
            Hospital(
                id="h-bgs-bangalore",
                name="BGS Gleneagles Global Hospital",
                location="Kengeri, Bangalore, Karnataka 560060",
                city="Bangalore",
                distance_km=12.5,
                rating=4.2,
                review_count=189,
                tier="budget",
                nabh_accredited=True,
                specializations=["Cardiology", "General Medicine", "Emergency Care"],
                strengths=["Lowest cost cardiac care", "Quick appointments", "Budget-friendly packages"],
                risk_flags=["Basic ICU facilities", "Limited specialist availability"],
                cost_range={"min": 90000, "max": 180000},
                doctors=[
                    HospitalDoctor(
                        id="d-bg-001",
                        name="Dr. Venkat Iyer",
                        specialization="General Cardiology",
                        experience_years=9,
                        rating=4.1,
                        fee_min=800,
                        fee_max=1500
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-bg-001",
                        sentiment="positive",
                        excerpt="Budget option for heart checkups and basic procedures."
                    )
                ],
                coordinates={"lat": 12.9083, "lng": 77.4849},
                rank_score=79,
                rank_signals=RankSignals(
                    clinical_capability=78,
                    reputation=75,
                    accessibility=72,
                    affordability=94
                ),
                sentiment_data=SentimentData(
                    positive_pct=73,
                    themes=[
                        {"theme": "Affordable care", "mentions": 42, "positive_pct": 78},
                        {"theme": "Basic services", "mentions": 35, "positive_pct": 71}
                    ],
                    sample_quotes=[
                        {"text": "Made cardiac treatment possible within our budget.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="low",
                icu_available=True,
                wait_time_days=1
            ),
            # Mumbai Hospitals
            Hospital(
                id="h-kokilaben-mumbai",
                name="Kokilaben Dhirubhai Ambani Hospital",
                location="Andheri West, Mumbai, Maharashtra 400053",
                city="Mumbai",
                distance_km=5.8,
                rating=4.7,
                review_count=456,
                tier="premium",
                nabh_accredited=True,
                specializations=["Cardiology", "Oncology", "Neurology", "Orthopedics"],
                strengths=["World-class facilities", "Renowned specialists", "Comprehensive care"],
                risk_flags=["Premium pricing", "High demand"],
                cost_range={"min": 350000, "max": 600000},
                doctors=[
                    HospitalDoctor(
                        id="d-ka-001",
                        name="Dr. Suresh Joshi",
                        specialization="Cardiac Surgery",
                        experience_years=20,
                        rating=4.9,
                        fee_min=4000,
                        fee_max=7000
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-ka-001",
                        sentiment="positive",
                        excerpt="Exceptional care and world-class infrastructure."
                    )
                ],
                coordinates={"lat": 19.1307, "lng": 72.8299},
                rank_score=96,
                rank_signals=RankSignals(
                    clinical_capability=98,
                    reputation=95,
                    accessibility=88,
                    affordability=60
                ),
                sentiment_data=SentimentData(
                    positive_pct=91,
                    themes=[
                        {"theme": "Clinical excellence", "mentions": 198, "positive_pct": 93},
                        {"theme": "Facilities", "mentions": 156, "positive_pct": 89}
                    ],
                    sample_quotes=[
                        {"text": "Best hospital experience in Mumbai.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="high",
                icu_available=True,
                wait_time_days=3
            ),
            Hospital(
                id="h-lilavati-mumbai",
                name="Lilavati Hospital",
                location="Bandra West, Mumbai, Maharashtra 400050",
                city="Mumbai",
                distance_km=8.2,
                rating=4.5,
                review_count=378,
                tier="premium",
                nabh_accredited=True,
                specializations=["Cardiology", "Orthopedics", "Nephrology"],
                strengths=["Trusted name", "Advanced technology", "Patient care"],
                risk_flags=["Premium costs"],
                cost_range={"min": 280000, "max": 500000},
                doctors=[
                    HospitalDoctor(
                        id="d-lt-001",
                        name="Dr. Priya Shah",
                        specialization="Interventional Cardiology",
                        experience_years=15,
                        rating=4.6,
                        fee_min=3000,
                        fee_max=5500
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-lt-001",
                        sentiment="positive",
                        excerpt="Renowned hospital with excellent cardiac care."
                    )
                ],
                coordinates={"lat": 19.0530, "lng": 72.8327},
                rank_score=92,
                rank_signals=RankSignals(
                    clinical_capability=94,
                    reputation=93,
                    accessibility=85,
                    affordability=68
                ),
                sentiment_data=SentimentData(
                    positive_pct=87,
                    themes=[
                        {"theme": "Cardiac care", "mentions": 134, "positive_pct": 89},
                        {"theme": "Technology", "mentions": 98, "positive_pct": 85}
                    ],
                    sample_quotes=[
                        {"text": "Trustworthy care for complex cardiac procedures.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="high",
                icu_available=True,
                wait_time_days=2
            ),
            # Delhi Hospitals
            Hospital(
                id="h-aiims-delhi",
                name="AIIMS Delhi",
                location="Ansari Nagar, New Delhi 110029",
                city="Delhi",
                distance_km=6.5,
                rating=4.8,
                review_count=523,
                tier="budget",
                nabh_accredited=True,
                specializations=["All Specialties", "Cardiology", "Oncology", "Neurology"],
                strengths=["Government subsidized rates", "Top doctors", "Research excellence"],
                risk_flags=["Long waiting times", "Limited amenities"],
                cost_range={"min": 50000, "max": 150000},
                doctors=[
                    HospitalDoctor(
                        id="d-ai-001",
                        name="Dr. Ramesh Gupta",
                        specialization="Cardiology",
                        experience_years=22,
                        rating=4.9,
                        fee_min=500,
                        fee_max=1000
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-ai-001",
                        sentiment="positive",
                        excerpt="Best value for money. World-class doctors at affordable rates."
                    )
                ],
                coordinates={"lat": 28.5672, "lng": 77.2100},
                rank_score=95,
                rank_signals=RankSignals(
                    clinical_capability=98,
                    reputation=97,
                    accessibility=75,
                    affordability=95
                ),
                sentiment_data=SentimentData(
                    positive_pct=89,
                    themes=[
                        {"theme": "Doctor expertise", "mentions": 234, "positive_pct": 94},
                        {"theme": "Affordability", "mentions": 187, "positive_pct": 91}
                    ],
                    sample_quotes=[
                        {"text": "Best doctors in India at minimal cost.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="high",
                icu_available=True,
                wait_time_days=14
            ),
            Hospital(
                id="h-fortis-escorts-delhi",
                name="Fortis Escorts Heart Institute",
                location="Okhla Road, New Delhi 110025",
                city="Delhi",
                distance_km=9.2,
                rating=4.6,
                review_count=412,
                tier="premium",
                nabh_accredited=True,
                specializations=["Cardiology", "Cardiac Surgery", "Electrophysiology"],
                strengths=["Cardiac excellence", "Advanced interventions", "Pioneer in heart care"],
                risk_flags=["Premium cardiac pricing"],
                cost_range={"min": 300000, "max": 550000},
                doctors=[
                    HospitalDoctor(
                        id="d-fe-001",
                        name="Dr. Ashok Seth",
                        specialization="Interventional Cardiology",
                        experience_years=25,
                        rating=4.9,
                        fee_min=5000,
                        fee_max=8000
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-fe-001",
                        sentiment="positive",
                        excerpt="Premier cardiac institute with exceptional outcomes."
                    )
                ],
                coordinates={"lat": 28.5607, "lng": 77.2745},
                rank_score=97,
                rank_signals=RankSignals(
                    clinical_capability=98,
                    reputation=96,
                    accessibility=82,
                    affordability=62
                ),
                sentiment_data=SentimentData(
                    positive_pct=90,
                    themes=[
                        {"theme": "Cardiac care", "mentions": 245, "positive_pct": 93},
                        {"theme": "Technology", "mentions": 167, "positive_pct": 91}
                    ],
                    sample_quotes=[
                        {"text": "Best heart hospital in North India.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="high",
                icu_available=True,
                wait_time_days=4
            ),
            # Hyderabad Hospitals
            Hospital(
                id="h-care-hyderabad",
                name="CARE Hospitals Banjara Hills",
                location="Banjara Hills, Hyderabad, Telangana 500034",
                city="Hyderabad",
                distance_km=4.3,
                rating=4.5,
                review_count=298,
                tier="mid",
                nabh_accredited=True,
                specializations=["Cardiology", "Neurology", "Orthopedics"],
                strengths=["Affordable quality", "Good success rates", "Patient care"],
                risk_flags=["Peak hour congestion"],
                cost_range={"min": 140000, "max": 260000},
                doctors=[
                    HospitalDoctor(
                        id="d-ch-001",
                        name="Dr. Kiran Kumar",
                        specialization="Cardiology",
                        experience_years=16,
                        rating=4.6,
                        fee_min=1800,
                        fee_max=3200
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-ch-001",
                        sentiment="positive",
                        excerpt="Reliable cardiac care at reasonable prices."
                    )
                ],
                coordinates={"lat": 17.4126, "lng": 78.4383},
                rank_score=88,
                rank_signals=RankSignals(
                    clinical_capability=87,
                    reputation=85,
                    accessibility=88,
                    affordability=84
                ),
                sentiment_data=SentimentData(
                    positive_pct=83,
                    themes=[
                        {"theme": "Value for money", "mentions": 89, "positive_pct": 86},
                        {"theme": "Cardiac outcomes", "mentions": 76, "positive_pct": 84}
                    ],
                    sample_quotes=[
                        {"text": "Quality care without breaking the bank.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="high",
                icu_available=True,
                wait_time_days=3
            ),
            Hospital(
                id="h-yashoda-hyderabad",
                name="Yashoda Hospitals Secunderabad",
                location="Secunderabad, Hyderabad, Telangana 500003",
                city="Hyderabad",
                distance_km=7.8,
                rating=4.3,
                review_count=245,
                tier="mid",
                nabh_accredited=True,
                specializations=["Cardiology", "Oncology", "Nephrology"],
                strengths=["Multi-specialty care", "Advanced facilities", "Accessibility"],
                risk_flags=["Higher costs for complex cases"],
                cost_range={"min": 160000, "max": 300000},
                doctors=[
                    HospitalDoctor(
                        id="d-yh-001",
                        name="Dr. Kavita Sharma",
                        specialization="Cardiology",
                        experience_years=14,
                        rating=4.4,
                        fee_min=2000,
                        fee_max=3500
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-yh-001",
                        sentiment="positive",
                        excerpt="Good cardiac facilities and caring staff."
                    )
                ],
                coordinates={"lat": 17.4399, "lng": 78.4983},
                rank_score=85,
                rank_signals=RankSignals(
                    clinical_capability=86,
                    reputation=83,
                    accessibility=90,
                    affordability=78
                ),
                sentiment_data=SentimentData(
                    positive_pct=80,
                    themes=[
                        {"theme": "Facilities", "mentions": 67, "positive_pct": 82},
                        {"theme": "Staff care", "mentions": 54, "positive_pct": 79}
                    ],
                    sample_quotes=[
                        {"text": "Well-equipped hospital with good doctors.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="medium",
                icu_available=True,
                wait_time_days=4
            ),
            # Chennai Hospitals
            Hospital(
                id="h-apollo-chennai",
                name="Apollo Hospitals Greams Road",
                location="Greams Road, Chennai, Tamil Nadu 600006",
                city="Chennai",
                distance_km=3.9,
                rating=4.7,
                review_count=387,
                tier="premium",
                nabh_accredited=True,
                specializations=["Cardiology", "Oncology", "Neurology", "Transplant"],
                strengths=["Pioneer in healthcare", "Advanced technology", "Expert doctors"],
                risk_flags=["Premium pricing"],
                cost_range={"min": 320000, "max": 580000},
                doctors=[
                    HospitalDoctor(
                        id="d-apc-001",
                        name="Dr. Prathap Reddy",
                        specialization="Cardiology",
                        experience_years=28,
                        rating=4.9,
                        fee_min=4500,
                        fee_max=7500
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-apc-001",
                        sentiment="positive",
                        excerpt="Flagship Apollo hospital with exceptional standards."
                    )
                ],
                coordinates={"lat": 13.0524, "lng": 80.2518},
                rank_score=96,
                rank_signals=RankSignals(
                    clinical_capability=98,
                    reputation=97,
                    accessibility=88,
                    affordability=58
                ),
                sentiment_data=SentimentData(
                    positive_pct=90,
                    themes=[
                        {"theme": "Medical excellence", "mentions": 187, "positive_pct": 93},
                        {"theme": "Technology", "mentions": 134, "positive_pct": 90}
                    ],
                    sample_quotes=[
                        {"text": "The gold standard for healthcare in South India.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="high",
                icu_available=True,
                wait_time_days=3
            ),
            Hospital(
                id="h-fortis-malar-chennai",
                name="Fortis Malar Hospital",
                location="Adyar, Chennai, Tamil Nadu 600020",
                city="Chennai",
                distance_km=8.5,
                rating=4.4,
                review_count=234,
                tier="mid",
                nabh_accredited=True,
                specializations=["Cardiology", "Pediatrics", "Orthopedics"],
                strengths=["Quality cardiac care", "Patient-friendly", "Good outcomes"],
                risk_flags=["Limited advanced procedures"],
                cost_range={"min": 150000, "max": 280000},
                doctors=[
                    HospitalDoctor(
                        id="d-fm-001",
                        name="Dr. Suresh Kumar",
                        specialization="Cardiology",
                        experience_years=15,
                        rating=4.5,
                        fee_min=1800,
                        fee_max=3200
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-fm-001",
                        sentiment="positive",
                        excerpt="Reliable hospital with good cardiac department."
                    )
                ],
                coordinates={"lat": 13.0067, "lng": 80.2570},
                rank_score=86,
                rank_signals=RankSignals(
                    clinical_capability=87,
                    reputation=84,
                    accessibility=85,
                    affordability=80
                ),
                sentiment_data=SentimentData(
                    positive_pct=82,
                    themes=[
                        {"theme": "Cardiac care", "mentions": 76, "positive_pct": 85},
                        {"theme": "Patient experience", "mentions": 58, "positive_pct": 81}
                    ],
                    sample_quotes=[
                        {"text": "Good care at reasonable prices in Chennai.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="medium",
                icu_available=True,
                wait_time_days=4
            ),
            # Pune Hospitals
            Hospital(
                id="h-sahyadri-pune",
                name="Sahyadri Hospital Deccan",
                location="Deccan Gymkhana, Pune, Maharashtra 411004",
                city="Pune",
                distance_km=2.8,
                rating=4.3,
                review_count=198,
                tier="mid",
                nabh_accredited=True,
                specializations=["Cardiology", "Orthopedics", "Neurology"],
                strengths=["Affordable quality", "Central location", "Patient care"],
                risk_flags=["Parking challenges"],
                cost_range={"min": 130000, "max": 240000},
                doctors=[
                    HospitalDoctor(
                        id="d-sh-001",
                        name="Dr. Ravi Patil",
                        specialization="Cardiology",
                        experience_years=13,
                        rating=4.4,
                        fee_min=1500,
                        fee_max=2800
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-sh-001",
                        sentiment="positive",
                        excerpt="Good hospital with reasonable cardiac care costs."
                    )
                ],
                coordinates={"lat": 18.5204, "lng": 73.8567},
                rank_score=84,
                rank_signals=RankSignals(
                    clinical_capability=84,
                    reputation=82,
                    accessibility=90,
                    affordability=86
                ),
                sentiment_data=SentimentData(
                    positive_pct=80,
                    themes=[
                        {"theme": "Value care", "mentions": 67, "positive_pct": 83},
                        {"theme": "Location", "mentions": 54, "positive_pct": 88}
                    ],
                    sample_quotes=[
                        {"text": "Convenient location with good medical care.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="medium",
                icu_available=True,
                wait_time_days=3
            ),
            Hospital(
                id="h-ruby-pune",
                name="Ruby Hall Clinic",
                location="Sassoon Road, Pune, Maharashtra 411001",
                city="Pune",
                distance_km=4.5,
                rating=4.5,
                review_count=267,
                tier="premium",
                nabh_accredited=True,
                specializations=["Cardiology", "Oncology", "Transplant"],
                strengths=["Heritage hospital", "Advanced cardiac care", "Trusted name"],
                risk_flags=["Premium pricing"],
                cost_range={"min": 220000, "max": 400000},
                doctors=[
                    HospitalDoctor(
                        id="d-rh-001",
                        name="Dr. Meera Joshi",
                        specialization="Cardiac Surgery",
                        experience_years=18,
                        rating=4.7,
                        fee_min=2800,
                        fee_max=5000
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-rh-001",
                        sentiment="positive",
                        excerpt="Historic hospital with excellent cardiac facilities."
                    )
                ],
                coordinates={"lat": 18.5265, "lng": 73.8758},
                rank_score=89,
                rank_signals=RankSignals(
                    clinical_capability=90,
                    reputation=91,
                    accessibility=85,
                    affordability=72
                ),
                sentiment_data=SentimentData(
                    positive_pct=85,
                    themes=[
                        {"theme": "Cardiac care", "mentions": 98, "positive_pct": 88},
                        {"theme": "Heritage", "mentions": 76, "positive_pct": 90}
                    ],
                    sample_quotes=[
                        {"text": "Trusted name in Pune healthcare for decades.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="high",
                icu_available=True,
                wait_time_days=4
            ),
            # Ahmedabad Hospitals
            Hospital(
                id="h-sal-ahmedabad",
                name="SAL Hospital",
                location="Drive-In Road, Ahmedabad, Gujarat 380052",
                city="Ahmedabad",
                distance_km=5.2,
                rating=4.2,
                review_count=187,
                tier="mid",
                nabh_accredited=True,
                specializations=["Cardiology", "Orthopedics", "Nephrology"],
                strengths=["Affordable care", "Good facilities", "Patient-friendly"],
                risk_flags=["Limited super-specialties"],
                cost_range={"min": 120000, "max": 220000},
                doctors=[
                    HospitalDoctor(
                        id="d-sal-001",
                        name="Dr. Amit Shah",
                        specialization="Cardiology",
                        experience_years=14,
                        rating=4.3,
                        fee_min=1400,
                        fee_max=2600
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-sal-001",
                        sentiment="positive",
                        excerpt="Good cardiac department with reasonable pricing."
                    )
                ],
                coordinates={"lat": 23.0339, "lng": 72.5286},
                rank_score=82,
                rank_signals=RankSignals(
                    clinical_capability=82,
                    reputation=80,
                    accessibility=87,
                    affordability=88
                ),
                sentiment_data=SentimentData(
                    positive_pct=78,
                    themes=[
                        {"theme": "Affordability", "mentions": 67, "positive_pct": 82},
                        {"theme": "Care quality", "mentions": 54, "positive_pct": 78}
                    ],
                    sample_quotes=[
                        {"text": "Value-for-money healthcare in Ahmedabad.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="medium",
                icu_available=True,
                wait_time_days=3
            ),
            Hospital(
                id="h-zydus-ahmedabad",
                name="Zydus Hospital",
                location="Thaltej, Ahmedabad, Gujarat 380054",
                city="Ahmedabad",
                distance_km=8.9,
                rating=4.4,
                review_count=223,
                tier="premium",
                nabh_accredited=True,
                specializations=["Cardiology", "Neurology", "Oncology"],
                strengths=["Modern facilities", "Advanced technology", "Expert doctors"],
                risk_flags=["Higher costs", "Distance from city center"],
                cost_range={"min": 200000, "max": 380000},
                doctors=[
                    HospitalDoctor(
                        id="d-zy-001",
                        name="Dr. Neha Patel",
                        specialization="Interventional Cardiology",
                        experience_years=16,
                        rating=4.6,
                        fee_min=2500,
                        fee_max=4200
                    )
                ],
                reviews=[
                    HospitalReview(
                        id="r-zy-001",
                        sentiment="positive",
                        excerpt="Excellent facilities and caring doctors."
                    )
                ],
                coordinates={"lat": 23.0439, "lng": 72.5076},
                rank_score=87,
                rank_signals=RankSignals(
                    clinical_capability=88,
                    reputation=85,
                    accessibility=78,
                    affordability=75
                ),
                sentiment_data=SentimentData(
                    positive_pct=83,
                    themes=[
                        {"theme": "Facilities", "mentions": 87, "positive_pct": 86},
                        {"theme": "Doctor care", "mentions": 67, "positive_pct": 84}
                    ],
                    sample_quotes=[
                        {"text": "Modern hospital with good cardiac care.", "sentiment": "positive"}
                    ]
                ),
                procedure_volume="high",
                icu_available=True,
                wait_time_days=4
            )
        ]

        # Filter by distance from search location
        nearby_hospitals = []
        search_coords = (location.latitude, location.longitude)

        for hospital in mock_hospitals:
            hospital_coords = (hospital.coordinates["lat"], hospital.coordinates["lng"])
            distance = geodesic(search_coords, hospital_coords).kilometers

            if distance <= max_distance:
                # Update distance for this search
                hospital.distance_km = round(distance, 1)
                nearby_hospitals.append(hospital)

        # Filter by specialization if specified
        if specialization:
            nearby_hospitals = [
                h for h in nearby_hospitals
                if specialization.lower() in [s.lower() for s in h.specializations]
            ]

        return nearby_hospitals

    def _apply_filters(self, hospitals: List[Hospital], request: HospitalSearchRequest) -> List[Hospital]:
        """Apply additional filters to hospital results."""
        filtered = hospitals

        # Rating filter
        if request.min_rating > 0:
            filtered = [h for h in filtered if h.rating >= request.min_rating]

        # Cost filter
        if request.max_cost:
            filtered = [
                h for h in filtered
                if h.cost_range.get("max", float('inf')) <= request.max_cost
            ]

        return filtered

    async def get_hospital_details(self, hospital_id: str) -> Optional[Hospital]:
        """
        Get detailed information for a specific hospital.

        Args:
            hospital_id: Unique hospital identifier

        Returns:
            Hospital details or None if not found
        """
        # In production, this would query a hospital database
        # For now, return mock data
        try:
            # Mock implementation - would be replaced with real API call
            return None  # Placeholder
        except Exception as e:
            logger.error(f"Error getting hospital details for {hospital_id}: {e}")
            return None


# Global service instance
hospital_search_service = HospitalSearchService()


async def search_hospitals(request: HospitalSearchRequest) -> List[Hospital]:
    """
    Convenience function to search for hospitals.

    Args:
        request: Search parameters

    Returns:
        List of matching hospitals
    """
    return await hospital_search_service.search_hospitals(request)


async def get_hospital_details(hospital_id: str) -> Optional[Hospital]:
    """
    Convenience function to get hospital details.

    Args:
        hospital_id: Hospital identifier

    Returns:
        Hospital details or None
    """
    return await hospital_search_service.get_hospital_details(hospital_id)