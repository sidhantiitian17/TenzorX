"""
Distance calculation module.

Provides Haversine formula for great-circle distance calculation.
"""

import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance (km) between two lat/lon coordinates.
    Uses the Haversine formula.
    
    Args:
        lat1: Latitude of point 1
        lon1: Longitude of point 1
        lat2: Latitude of point 2
        lon2: Longitude of point 2
        
    Returns:
        Distance in kilometers
    """
    R = 6371.0  # Earth's radius in km
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)
