"""
Geospatial Pricing and Location Adjustment Service.

This module implements geographic pricing adjustments using geopy for location
resolution and tier-based cost scaling. Handles unstructured location strings
and applies geographic pricing formulas for accurate cost estimation.

Production Standards:
- Robust geocoding with fallback strategies
- Comprehensive error handling for API failures
- Strict type hints and Pydantic validation
- Caching for geocoding results
- Tier-based pricing logic with mathematical precision
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from functools import lru_cache
import time

from pydantic import BaseModel, Field, validator
from geopy.geocoders import Nominatim, GoogleV3
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Configure module logger
logger = logging.getLogger(__name__)


class LocationData(BaseModel):
    """Structured location data with coordinates."""

    address: str = Field(..., description="Original address string")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    city: Optional[str] = Field(None, description="Extracted city name")
    state: Optional[str] = Field(None, description="Extracted state name")
    country: Optional[str] = Field(None, description="Extracted country name")
    tier: str = Field(..., description="City tier classification")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Geocoding confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Geocoding metadata")

    @validator('tier')
    def validate_tier(cls, v):
        """Validate city tier is one of expected values."""
        valid_tiers = {'Tier-1', 'Tier-2', 'Tier-3'}
        if v not in valid_tiers:
            raise ValueError(f"tier must be one of {valid_tiers}")
        return v


class PricingAdjustment(BaseModel):
    """Geographic pricing adjustment result."""

    base_cost: float = Field(..., ge=0, description="Original base cost")
    adjusted_cost: float = Field(..., ge=0, description="Geographically adjusted cost")
    adjustment_factor: float = Field(..., ge=0, description="Adjustment multiplier")
    tier_multiplier: float = Field(..., ge=0, description="Tier-based multiplier")
    distance_factor: float = Field(..., ge=0, description="Distance-based adjustment")
    breakdown: Dict[str, float] = Field(..., description="Cost breakdown components")
    location_data: LocationData = Field(..., description="Resolved location information")


class GeoPricingError(Exception):
    """Base exception for geo-pricing operations."""
    pass


class GeocodingError(GeoPricingError):
    """Raised when geocoding operations fail."""
    pass


class PricingCalculationError(GeoPricingError):
    """Raised when pricing calculations fail."""
    pass


class GeoPricingService:
    """
    Production geospatial pricing adjustment service.

    Uses geopy for location resolution and implements geographic pricing
    formulas with tier-based cost scaling for accurate healthcare cost estimation.
    """

    # Tier-based cost multipliers (relative to Tier-1)
    TIER_MULTIPLIERS = {
        'Tier-1': 1.0,    # Mumbai, Delhi, Bangalore, Chennai, Kolkata
        'Tier-2': 0.75,   # Pune, Ahmedabad, Jaipur, Lucknow, etc.
        'Tier-3': 0.5     # Smaller cities and towns
    }

    # Major Tier-1 cities in India
    TIER_1_CITIES = {
        'mumbai', 'delhi', 'bangalore', 'bengaluru', 'chennai', 'kolkata',
        'hyderabad', 'pune', 'ahmedabad', 'surat', 'jaipur', 'lucknow',
        'kanpur', 'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam',
        'pimpri-chinchwad', 'patna', 'vadodara', 'ghaziabad', 'ludhiana',
        'agra', 'nashik', 'faridabad', 'meerut', 'rajkot', 'kalyan-dombivli',
        'vasai-virar', 'varanasi', 'srinagar', 'aurangabad', 'dhanbad',
        'amritsar', 'navi mumbai', 'allahabad', 'howrah', 'ranchi', 'jabalpur'
    }

    # Major Tier-2 cities
    TIER_2_CITIES = {
        'coimbatore', 'jodhpur', 'madurai', 'raipur', 'kota', 'guwahati',
        'chandigarh', 'solapur', 'hubballi', 'mysore', 'tiruchirappalli',
        'bareilly', 'aligarh', 'tiruppur', 'moradabad', 'jhansi', 'gorakhpur',
        'bhubaneswar', 'jalandhar', 'warangal', 'guntur', 'bhiwandi',
        'amalner', 'noida', 'jamshedpur', 'bhilai', 'cuttack', 'firozabad',
        'kochi', 'nellore', 'bhavnagar', 'dehradun', 'durgapur', 'asansol',
        'rourkela', 'nanded', 'kolhapur', 'ajmer', 'akola', 'gulbargar',
        'jamnagar', 'ujjain', 'loni', 'siliguri', 'jhansi', 'ulhasnagar'
    }

    def __init__(self, google_api_key: Optional[str] = None):
        """
        Initialize geo-pricing service with geocoding providers.

        Args:
            google_api_key: Google Maps API key for enhanced geocoding
        """
        self.logger = logging.getLogger(__name__)

        # Initialize geocoding providers
        self.nominatim = Nominatim(
            user_agent="TenzorX-Healthcare-Navigator/1.0",
            timeout=10
        )

        if google_api_key:
            self.google_geocoder = GoogleV3(api_key=google_api_key, timeout=10)
            self.logger.info("✅ Google Geocoding initialized")
        else:
            self.google_geocoder = None
            self.logger.warning("⚠️ Google Geocoding not available - using Nominatim only")

        # Pricing constants
        self.geographic_adjustment_factor = 0.05  # Ygeo in formula
        self.distance_decay_factor = 0.02  # Distance-based adjustment

        self.logger.info("✅ Geo-Pricing Service initialized")

    def _extract_location_components(self, address: str) -> Dict[str, str]:
        """
        Extract city, state, and country from address string.

        Args:
            address: Raw address string

        Returns:
            Dictionary with extracted components
        """
        # Clean and normalize address
        address = address.lower().strip()

        # Remove common prefixes/suffixes
        address = re.sub(r'\b(pincode|pin|zip)\s*\d+', '', address)
        address = re.sub(r'\b(near|beside|opposite|behind)\b.*', '', address)

        components = {}

        # Try to extract city (look for known city names)
        for city in self.TIER_1_CITIES | self.TIER_2_CITIES:
            if city in address:
                components['city'] = city.title()
                break

        # Extract state (common Indian states)
        states = ['maharashtra', 'karnataka', 'tamil nadu', 'delhi', 'gujarat',
                 'rajasthan', 'uttar pradesh', 'west bengal', 'telangana', 'punjab']
        for state in states:
            if state in address:
                components['state'] = state.title()
                break

        components['country'] = 'India'  # Default for Indian healthcare

        return components

    def _determine_city_tier(self, city: str, state: str = "") -> str:
        """
        Determine city tier based on classification lists.

        Args:
            city: City name
            state: State name (for additional context)

        Returns:
            City tier classification
        """
        city_lower = city.lower().replace('-', ' ')

        if city_lower in self.TIER_1_CITIES:
            return 'Tier-1'
        elif city_lower in self.TIER_2_CITIES:
            return 'Tier-2'
        else:
            # Default to Tier-3 for unknown cities
            return 'Tier-3'

    @lru_cache(maxsize=1000)
    def _geocode_location(self, address: str) -> Tuple[float, float, Dict[str, Any]]:
        """
        Geocode address to coordinates using available providers.

        Args:
            address: Address string to geocode

        Returns:
            Tuple of (latitude, longitude, metadata)

        Raises:
            GeocodingError: If geocoding fails
        """
        try:
            self.logger.debug(f"🔍 Geocoding address: {address}")

            # Try Google Geocoding first (if available)
            if self.google_geocoder:
                try:
                    google_result = self.google_geocoder.geocode(address, country_codes=['IN'])
                    if google_result:
                        metadata = {
                            'provider': 'google',
                            'confidence': 0.95,
                            'raw_address': google_result.address
                        }
                        self.logger.debug("✅ Google geocoding successful")
                        return google_result.latitude, google_result.longitude, metadata
                except (GeocoderTimedOut, GeocoderServiceError) as e:
                    self.logger.warning(f"⚠️ Google geocoding failed: {e}")

            # Fallback to Nominatim
            try:
                nominatim_result = self.nominatim.geocode(address, country_codes=['IN'])
                if nominatim_result:
                    metadata = {
                        'provider': 'nominatim',
                        'confidence': 0.80,
                        'raw_address': nominatim_result.address
                    }
                    self.logger.debug("✅ Nominatim geocoding successful")
                    return nominatim_result.latitude, nominatim_result.longitude, metadata
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                self.logger.error(f"❌ Nominatim geocoding failed: {e}")
                raise GeocodingError(f"All geocoding providers failed for address: {address}") from e

            # If no results from any provider
            raise GeocodingError(f"No geocoding results found for address: {address}")

        except Exception as e:
            self.logger.error(f"❌ Geocoding failed for {address}: {e}")
            raise GeocodingError(f"Geocoding failed: {e}") from e

    def resolve_location(self, address: str) -> LocationData:
        """
        Resolve unstructured location string to structured location data.

        Args:
            address: Raw address string (e.g., "Tier 2 city name")

        Returns:
            Structured location data with coordinates and tier

        Raises:
            GeocodingError: If location resolution fails
        """
        try:
            self.logger.info(f"🔍 Resolving location: {address}")

            # Extract location components
            components = self._extract_location_components(address)

            # Geocode to get coordinates
            lat, lon, geo_metadata = self._geocode_location(address)

            # Determine city tier
            city = components.get('city', '')
            state = components.get('state', '')
            tier = self._determine_city_tier(city, state)

            # Calculate geocoding confidence
            base_confidence = geo_metadata.get('confidence', 0.8)
            tier_confidence = 1.0 if tier in ['Tier-1', 'Tier-2'] else 0.7
            final_confidence = min(base_confidence * tier_confidence, 1.0)

            location_data = LocationData(
                address=address,
                latitude=round(lat, 6),
                longitude=round(lon, 6),
                city=city,
                state=state,
                country=components.get('country', 'India'),
                tier=tier,
                confidence=round(final_confidence, 3),
                metadata={
                    'geocoding_provider': geo_metadata.get('provider'),
                    'extraction_method': 'rule_based',
                    'geocoding_timestamp': time.time(),
                    **geo_metadata
                }
            )

            self.logger.info(f"✅ Location resolved: {city}, {state} ({tier}) - Confidence: {final_confidence:.3f}")
            return location_data

        except Exception as e:
            self.logger.error(f"❌ Location resolution failed for {address}: {e}")
            raise GeocodingError(f"Location resolution failed: {e}") from e

    def calculate_geographic_pricing(self,
                                   base_clinical_rate: float,
                                   predicted_days: int,
                                   room_rate: float,
                                   location_data: LocationData) -> PricingAdjustment:
        """
        Calculate geographic pricing adjustment using the specified formula.

        Formula: Adjusted_Cost = Base_Clinical_Rate * Ygeo + (Predicted_Days * Room_Rate)

        Args:
            base_clinical_rate: Base clinical procedure cost
            predicted_days: Expected length of stay
            room_rate: Daily room rate
            location_data: Resolved location data

        Returns:
            Pricing adjustment with breakdown

        Raises:
            PricingCalculationError: If calculation fails
        """
        try:
            self.logger.info(f"💰 Calculating geographic pricing for {location_data.city}")

            # Get tier multiplier
            tier_multiplier = self.TIER_MULTIPLIERS[location_data.tier]

            # Apply geographic adjustment factor (Ygeo)
            y_geo = self.geographic_adjustment_factor

            # Calculate base clinical cost with geographic adjustment
            clinical_cost_adjusted = base_clinical_rate * (1 + y_geo)

            # Calculate hospitalization cost
            hospitalization_cost = predicted_days * room_rate

            # Apply tier-based scaling (dramatically reduce for Tier-3)
            tier_adjusted_clinical = clinical_cost_adjusted * tier_multiplier
            tier_adjusted_hospitalization = hospitalization_cost * tier_multiplier

            # Calculate total adjusted cost
            total_adjusted_cost = tier_adjusted_clinical + tier_adjusted_hospitalization

            # Calculate adjustment factor
            adjustment_factor = total_adjusted_cost / (base_clinical_rate + hospitalization_cost) if (base_clinical_rate + hospitalization_cost) > 0 else 1.0

            # Distance-based adjustment (optional, for future use)
            distance_factor = 1.0  # Placeholder for distance-based adjustments

            breakdown = {
                'base_clinical_rate': base_clinical_rate,
                'clinical_cost_adjusted': clinical_cost_adjusted,
                'tier_adjusted_clinical': tier_adjusted_clinical,
                'hospitalization_cost': hospitalization_cost,
                'tier_adjusted_hospitalization': tier_adjusted_hospitalization,
                'tier_multiplier': tier_multiplier,
                'geographic_adjustment': y_geo,
                'predicted_days': predicted_days,
                'room_rate': room_rate
            }

            pricing_adjustment = PricingAdjustment(
                base_cost=base_clinical_rate + hospitalization_cost,
                adjusted_cost=round(total_adjusted_cost, 2),
                adjustment_factor=round(adjustment_factor, 3),
                tier_multiplier=tier_multiplier,
                distance_factor=distance_factor,
                breakdown=breakdown,
                location_data=location_data
            )

            self.logger.info(f"✅ Pricing calculated: ₹{total_adjusted_cost:,.0f} (factor: {adjustment_factor:.3f})")
            return pricing_adjustment

        except Exception as e:
            self.logger.error(f"❌ Pricing calculation failed: {e}")
            raise PricingCalculationError(f"Pricing calculation failed: {e}") from e

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the geo-pricing service.

        Returns:
            Dictionary with component status
        """
        try:
            # Test geocoding with a known location
            test_location = self.resolve_location("Mumbai, Maharashtra, India")
            geocoding_healthy = (
                isinstance(test_location.latitude, float) and
                isinstance(test_location.longitude, float) and
                test_location.tier == 'Tier-1'
            )

            # Test pricing calculation
            test_pricing = self.calculate_geographic_pricing(
                base_clinical_rate=100000,
                predicted_days=5,
                room_rate=5000,
                location_data=test_location
            )
            pricing_healthy = (
                test_pricing.adjusted_cost > 0 and
                test_pricing.adjustment_factor > 0
            )

            return {
                "status": "healthy" if geocoding_healthy and pricing_healthy else "unhealthy",
                "components": {
                    "geocoding": "healthy" if geocoding_healthy else "unhealthy",
                    "pricing_calculation": "healthy" if pricing_healthy else "unhealthy",
                    "google_geocoding": "available" if self.google_geocoder else "unavailable"
                },
                "tier_multipliers": self.TIER_MULTIPLIERS,
                "supported_cities": {
                    "tier_1_count": len(self.TIER_1_CITIES),
                    "tier_2_count": len(self.TIER_2_CITIES)
                }
            }

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global service instance for module-level convenience functions
_geo_pricing_service: Optional[GeoPricingService] = None


def _get_geo_pricing_service() -> GeoPricingService:
    """Get or create the global geo-pricing service instance."""
    global _geo_pricing_service
    if _geo_pricing_service is None:
        _geo_pricing_service = GeoPricingService()
    return _geo_pricing_service


async def resolve_location(address: str) -> Optional[LocationData]:
    """
    Resolve unstructured location string to structured location data.

    This is a convenience function that wraps GeoPricingService.resolve_location
    for use by other modules.

    Args:
        address: Raw address string (e.g., "Nagpur, Maharashtra")

    Returns:
        Structured location data with coordinates and tier, or None if resolution fails
    """
    try:
        service = _get_geo_pricing_service()
        # Run the synchronous resolve_location in a thread pool
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, service.resolve_location, address)
        return result
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Location resolution failed for {address}: {e}")
        return None