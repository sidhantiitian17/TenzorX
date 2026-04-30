"""
Geographic Pricing Engine (Gap 5 Resolver).

Applies geographic cost multipliers to base procedure estimates.
Formula: Adjusted_Cost = Base_Cost × geo_multiplier
"""

from typing import Dict, Any, Optional


class GeoPricingEngine:
    """
    Applies geographic cost multipliers to base procedure estimates.
    Based on Kearney India Healthcare Index and multi-site cost studies.
    """

    # City tier classification
    CITY_TIER_MAP = {
        # Metro (Tier 1) — multiplier 1.0 (baseline)
        "mumbai": "metro", "delhi": "metro", "bangalore": "metro",
        "bengaluru": "metro", "chennai": "metro", "kolkata": "metro",
        "hyderabad": "metro", "pune": "metro", "ahmedabad": "metro",
        # Tier 2 — multiplier 0.82
        "nagpur": "tier2", "raipur": "tier2", "bhopal": "tier2",
        "indore": "tier2", "nashik": "tier2", "aurangabad": "tier2",
        "surat": "tier2", "patna": "tier2", "lucknow": "tier2",
        "jaipur": "tier2", "bhubaneswar": "tier2", "coimbatore": "tier2",
        "vizag": "tier2", "visakhapatnam": "tier2",
        # Tier 3 — multiplier 0.65
        "bilaspur": "tier3", "korba": "tier3", "durg": "tier3",
        "bhilai": "tier3", "jabalpur": "tier3", "gwalior": "tier3",
        "ratlam": "tier3", "amravati": "tier3", "dhule": "tier3",
    }

    # Cost multipliers relative to metro baseline
    GEO_MULTIPLIERS = {
        "metro": 1.00,
        "tier2": 0.82,
        "tier3": 0.65,
    }

    # ICU bed-day cost benchmarks (INR/day)
    ICU_COST_PER_DAY = {
        "metro": 5534,
        "tier2": 5427,
        "tier3": 2638,
    }

    def get_city_tier(self, city: str) -> str:
        """Get tier classification for a city."""
        return self.CITY_TIER_MAP.get(city.lower().strip(), "tier2")

    def get_multiplier(self, city_tier: str) -> float:
        """Get cost multiplier for a city tier."""
        return self.GEO_MULTIPLIERS.get(city_tier, 0.82)

    def apply_multiplier(self, cost_estimate: Dict[str, Any], city_tier: str) -> Dict[str, Any]:
        """
        Scale all cost components by the geographic multiplier.
        Returns a new cost estimate dict with adjusted values.
        """
        multiplier = self.get_multiplier(city_tier)
        adjusted = {"geo_multiplier": multiplier, "city_tier": city_tier}

        # Adjust total
        if "total" in cost_estimate:
            t = cost_estimate["total"]
            adjusted["total"] = {
                "min": round(t["min"] * multiplier),
                "max": round(t["max"] * multiplier),
                "typical_min": round(t.get("typical_min", t["min"]) * multiplier),
                "typical_max": round(t.get("typical_max", t["max"]) * multiplier),
            }

        # Adjust breakdown components
        if "breakdown" in cost_estimate:
            adjusted["breakdown"] = {}
            for component, values in cost_estimate["breakdown"].items():
                adjusted["breakdown"][component] = {
                    "min": round(values["min"] * multiplier),
                    "max": round(values["max"] * multiplier),
                }
                if "nights" in values:
                    adjusted["breakdown"][component]["nights"] = values["nights"]

        adjusted["geo_adjustment"] = {
            "city_tier": city_tier,
            "multiplier": multiplier,
            "discount_vs_metro": round((1 - multiplier) * 100, 1),
        }

        return {**cost_estimate, **adjusted}
