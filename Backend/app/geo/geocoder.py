"""
Geocoder module.

Resolves city names, neighborhoods, or pin codes to lat/lon coordinates.
Primary: Nominatim (free, no API key needed)
Fallback: GoogleV3 (requires GOOGLE_MAPS_KEY in env)
"""

import os
import logging
from typing import Optional, Dict, Any

try:
    from geopy.geocoders import Nominatim, GoogleV3
    from geopy.exc import GeocoderTimedOut
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class Geocoder:
    """
    Resolves location strings to lat/lon coordinates.
    Primary: Nominatim (free)
    Fallback: GoogleV3 (requires API key)
    """

    def __init__(self):
        self.nominatim = None
        self.google = None
        
        if GEOPY_AVAILABLE:
            self.nominatim = Nominatim(
                user_agent=os.getenv("NOMINATIM_USER_AGENT", "tenzorx_healthnav/1.0")
            )
            google_key = os.getenv("GOOGLE_MAPS_KEY")
            if google_key:
                self.google = GoogleV3(api_key=google_key)

    def geocode(self, location_string: str) -> Optional[Dict[str, Any]]:
        """
        Geocode a location string.
        
        Returns {"lat": float, "lon": float, "display_name": str} or None.
        Adds ", India" suffix for better accuracy with Indian city names.
        """
        if not GEOPY_AVAILABLE:
            logger.warning("geopy not available")
            return None

        query = f"{location_string}, India"
        
        try:
            location = self.nominatim.geocode(query, timeout=10)
            if location:
                return {
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "display_name": location.address,
                }
        except Exception as e:
            logger.warning(f"Nominatim geocoding failed: {e}")

        # Fallback to Google
        if self.google:
            try:
                location = self.google.geocode(query, timeout=10)
                if location:
                    return {
                        "lat": location.latitude,
                        "lon": location.longitude,
                        "display_name": location.address,
                    }
            except Exception as e:
                logger.warning(f"Google geocoding failed: {e}")

        return None
