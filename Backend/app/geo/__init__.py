"""
Geo module for spatial intelligence.

Provides geocoding and distance calculation utilities.
"""

from app.geo.geocoder import Geocoder
from app.geo.distance_calc import haversine_km

__all__ = ["Geocoder", "haversine_km"]
