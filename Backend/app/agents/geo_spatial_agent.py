"""
AGENT 5 — Geo-Spatial Agent

Resolves user location strings to coordinates, geocodes hospital addresses,
feeds Leaflet.js map, and calculates distances.

Per instructionagent.md Section 3.5
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from geopy.geocoders import Nominatim, GoogleV3
from geopy.distance import geodesic

from app.core.config import settings
from app.schemas.response_models import (
    GeoSpatialOutput,
    UserCoords,
    MapConfig,
)

logger = logging.getLogger(__name__)

# City tier mapping (simplified - expand as needed)
CITY_TIERS = {
    # Tier 1 (Metro)
    "mumbai": 1, "delhi": 1, "bangalore": 1, "bengaluru": 1,
    "hyderabad": 1, "chennai": 1, "kolkata": 1, "pune": 1,
    "ahmedabad": 1, "surat": 1,
    # Tier 2 (Major cities)
    "nagpur": 2, "jaipur": 2, "lucknow": 2, "kanpur": 2, "nashik": 2,
    "aurangabad": 2, "indore": 2, "bhopal": 2, "visakhapatnam": 2,
    "vadodara": 2, "ludhiana": 2, "coimbatore": 2, "madurai": 2,
    "mangalore": 2, "mysore": 2, "trivandrum": 2, "kochi": 2,
    # Tier 3 (Default for others)
}

# Map colors by hospital tier
TIER_COLORS = {
    "premium": "#3B82F6",    # Blue
    "mid-tier": "#8B5CF6",   # Purple
    "mid_tier": "#8B5CF6",   # Alias
    "budget": "#10B981",     # Green
}


@dataclass
class LocationResult:
    """Result of geocoding a location."""
    lat: float
    lng: float
    city: str
    state: str
    tier: int
    formatted_address: str


class GeoSpatialAgent:
    """
    Geo-Spatial Agent for location resolution and map data generation.
    
    Per instructionagent.md Section 3.5
    """

    def __init__(self, use_google: bool = False):
        """
        Initialize geocoding engines.
        
        Args:
            use_google: Whether to use Google Maps (if key available)
        """
        self.use_google = use_google and settings.GOOGLE_MAPS_API_KEY
        
        if self.use_google:
            self.geocoder = GoogleV3(
                api_key=settings.GOOGLE_MAPS_API_KEY,
                user_agent="healthnav-india"
            )
        else:
            self.geocoder = Nominatim(
                user_agent=settings.NOMINATIM_USER_AGENT or "healthnav-india"
            )

    def geocode_location(self, location_string: str) -> Optional[LocationResult]:
        """
        Resolve location string to coordinates.
        
        Args:
            location_string: City name or address (e.g., "Nagpur", "Mumbai, Maharashtra")
            
        Returns:
            LocationResult with coordinates and metadata, or None if failed
        """
        try:
            # Add India context if not present
            query = location_string
            if "india" not in location_string.lower():
                query = f"{location_string}, India"

            location = self.geocoder.geocode(query)
            
            if not location:
                logger.warning(f"Could not geocode: {location_string}")
                return None

            # Extract city from address or use input
            address_parts = location.address.split(", ")
            city = self._extract_city(address_parts, location_string)
            state = self._extract_state(address_parts)
            
            # Determine tier
            tier = self._get_city_tier(city)

            return LocationResult(
                lat=location.latitude,
                lng=location.longitude,
                city=city,
                state=state,
                tier=tier,
                formatted_address=location.address,
            )

        except Exception as e:
            logger.error(f"Geocoding error for '{location_string}': {e}")
            return None

    def _extract_city(self, address_parts: List[str], original_query: str) -> str:
        """Extract city name from address parts."""
        if len(address_parts) >= 2:
            # Usually the second-to-last part before state
            return address_parts[-3] if len(address_parts) >= 3 else address_parts[0]
        return original_query.split(",")[0].strip().title()

    def _extract_state(self, address_parts: List[str]) -> str:
        """Extract state name from address parts."""
        if len(address_parts) >= 2:
            return address_parts[-2] if "India" in address_parts[-1] else address_parts[-1]
        return "Unknown"

    def _get_city_tier(self, city: str) -> int:
        """
        Determine city tier for geo-pricing.
        
        Args:
            city: City name
            
        Returns:
            Tier number (1, 2, or 3)
        """
        city_lower = city.lower().strip()
        return CITY_TIERS.get(city_lower, 3)  # Default to tier 3

    def calculate_distance(
        self,
        user_lat: float,
        user_lng: float,
        hospital_lat: float,
        hospital_lng: float,
    ) -> float:
        """
        Calculate distance between user and hospital.
        
        Args:
            user_lat: User latitude
            user_lng: User longitude
            hospital_lat: Hospital latitude
            hospital_lng: Hospital longitude
            
        Returns:
            Distance in kilometers
        """
        try:
            distance = geodesic(
                (user_lat, user_lng),
                (hospital_lat, hospital_lng)
            ).km
            return round(distance, 1)
        except Exception as e:
            logger.error(f"Distance calculation error: {e}")
            return 0.0

    def generate_hospital_markers(
        self,
        hospitals: List[Dict[str, Any]],
        user_lat: float,
        user_lng: float,
    ) -> List[Dict[str, Any]]:
        """
        Generate map markers for hospitals.
        
        Args:
            hospitals: List of hospital dictionaries
            user_lat: User latitude
            user_lng: User longitude
            
        Returns:
            List of map marker dictionaries
        """
        markers = []
        
        for h in hospitals:
            try:
                tier = h.get("tier", "mid-tier").lower().replace("-", "_")
                color = TIER_COLORS.get(tier, "#6B7CFF")
                
                # Calculate distance
                h_lat = h.get("lat")
                h_lng = h.get("lng")
                
                if h_lat is not None and h_lng is not None:
                    distance = self.calculate_distance(user_lat, user_lng, h_lat, h_lng)
                else:
                    distance = h.get("distance_km", 0)
                
                # Format cost label
                cost_min = h.get("cost_min", 0)
                cost_max = h.get("cost_max", 0)
                if cost_min and cost_max:
                    cost_label = f"Rs {cost_min/100000:.1f}L – Rs {cost_max/100000:.1f}L"
                else:
                    cost_label = "Contact for pricing"
                
                marker = {
                    "id": h.get("id", ""),
                    "lat": h_lat,
                    "lng": h_lng,
                    "name": h.get("name", ""),
                    "tier": h.get("tier", "mid-tier"),
                    "color": color,
                    "cost_label": cost_label,
                    "distance_km": distance,
                    "rating": h.get("rating", 0),
                    "nabh": h.get("nabh", False),
                }
                markers.append(marker)
                
            except Exception as e:
                logger.error(f"Error generating marker for hospital: {e}")
                continue
        
        return markers

    def create_map_config(
        self,
        user_lat: float,
        user_lng: float,
        zoom: int = 13,
    ) -> MapConfig:
        """
        Create map configuration for Leaflet.js.
        
        Args:
            user_lat: Center latitude
            user_lng: Center longitude
            zoom: Zoom level
            
        Returns:
            MapConfig
        """
        return MapConfig(
            center=[user_lat, user_lng],
            zoom=zoom,
            tile_layer="OpenStreetMap",
            legend={
                "Premium": TIER_COLORS["premium"],
                "Mid-range": TIER_COLORS["mid-tier"],
                "Budget": TIER_COLORS["budget"],
            },
        )

    def process(
        self,
        location_string: str,
        hospitals: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[GeoSpatialOutput]:
        """
        Main processing method for the agent.
        
        Args:
            location_string: User's location query
            hospitals: Optional list of hospitals to generate markers for
            
        Returns:
            GeoSpatialOutput or None if geocoding fails
        """
        # Geocode user location
        location_result = self.geocode_location(location_string)
        if not location_result:
            return None

        user_coords = UserCoords(
            lat=location_result.lat,
            lng=location_result.lng,
        )

        # Generate hospital markers if hospitals provided
        hospital_markers = []
        if hospitals:
            hospital_markers = self.generate_hospital_markers(
                hospitals,
                location_result.lat,
                location_result.lng,
            )

        # Create map config
        map_config = self.create_map_config(
            location_result.lat,
            location_result.lng,
        )

        return GeoSpatialOutput(
            user_coords=user_coords,
            city_tier=location_result.tier,
            hospital_markers=hospital_markers,
            map_config=map_config,
        )

    def get_city_tier(self, city: str) -> int:
        """
        Public method to get city tier.
        
        Args:
            city: City name
            
        Returns:
            Tier number (1, 2, or 3)
        """
        return self._get_city_tier(city)


# =============================================================================
# Module-level convenience functions
# =============================================================================

def get_geo_spatial_agent(use_google: bool = False) -> GeoSpatialAgent:
    """Get singleton instance of GeoSpatialAgent."""
    return GeoSpatialAgent(use_google=use_google)


def geocode_city(city: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to geocode a city.
    
    Args:
        city: City name
        
    Returns:
        Dict with lat, lng, tier, state or None
    """
    agent = get_geo_spatial_agent()
    result = agent.geocode_location(city)
    
    if result:
        return {
            "lat": result.lat,
            "lng": result.lng,
            "city": result.city,
            "state": result.state,
            "tier": result.tier,
        }
    return None


def calculate_distance_km(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
) -> float:
    """
    Convenience function to calculate distance.
    
    Args:
        lat1, lng1: First point
        lat2, lng2: Second point
        
    Returns:
        Distance in kilometers
    """
    agent = get_geo_spatial_agent()
    return agent.calculate_distance(lat1, lng1, lat2, lng2)


def get_city_tier(city: str) -> int:
    """
    Convenience function to get city tier.
    
    Args:
        city: City name
        
    Returns:
        Tier number (1, 2, or 3)
    """
    agent = get_geo_spatial_agent()
    return agent.get_city_tier(city)
