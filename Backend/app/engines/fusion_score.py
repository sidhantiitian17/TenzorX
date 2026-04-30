"""
Multi-Source Data Fusion Score Engine (Gap 7 Resolver).

Aggregates Clinical, Reputation, Accessibility, and Affordability signals
into a single normalized Multi-Source Data Fusion Score (0-1).

Weights: Clinical 40%, Reputation 25%, Accessibility 20%, Affordability 15%
"""

import math
from typing import List, Dict, Any, Optional

from app.geo.distance_calc import haversine_km
from app.engines.availability_proxy import AvailabilityProxy


class FusionScoreEngine:
    """
    Aggregates multi-source signals into a single normalized Fusion Score (0-1).
    """

    WEIGHTS = {
        "clinical": 0.40,
        "reputation": 0.25,
        "accessibility": 0.20,
        "affordability": 0.15,
    }

    def __init__(self):
        self.availability_proxy = AvailabilityProxy()

    def _min_max_normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Min-max normalize a value to [0, 1]."""
        if max_val == min_val:
            return 0.5
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    def _sigmoid(self, x: float, k: float = 5.0) -> float:
        """Sigmoid mapping for smooth normalization."""
        return 1 / (1 + math.exp(-k * (x - 0.5)))

    def _clinical_score(self, hospital: Dict[str, Any], procedure: str) -> float:
        """Assess specialization relevance, NABH accreditation, and procedure volume."""
        score = 0.0
        specializations = [s.lower() for s in hospital.get("specializations", [])]
        procedure_lower = procedure.lower()

        # Specialization match
        for spec in specializations:
            if any(word in spec for word in procedure_lower.split()):
                score += 0.5
                break

        # NABH accreditation bonus
        if hospital.get("nabh_accredited", False):
            score += 0.3

        # Bed count proxy for volume
        beds = hospital.get("bed_count", 100)
        volume_score = self._min_max_normalize(beds, 50, 500)
        score += volume_score * 0.2

        return min(1.0, score)

    def _reputation_score(self, hospital: Dict[str, Any]) -> float:
        """Fuse public star ratings + ABSA sentiment score."""
        rating = hospital.get("rating", 3.0)
        rating_normalized = self._min_max_normalize(rating, 1.0, 5.0)

        sentiment = hospital.get("sentiment", {})
        absa_score = sentiment.get("reputation_score", 50) / 100.0

        return (rating_normalized * 0.55) + (absa_score * 0.45)

    def _accessibility_score(
        self,
        hospital: Dict[str, Any],
        user_lat: Optional[float],
        user_lon: Optional[float],
    ) -> float:
        """Combine geographic distance with appointment availability proxy."""
        # Distance component
        if user_lat and user_lon and hospital.get("lat") and hospital.get("lon"):
            dist_km = haversine_km(user_lat, user_lon, hospital["lat"], hospital["lon"])
            dist_score = self._min_max_normalize(dist_km, 0, 50)
            dist_score = 1.0 - dist_score  # Invert: shorter = better
        else:
            dist_score = 0.5

        # Availability proxy component
        avail = self.availability_proxy.estimate(
            total_beds=hospital.get("bed_count", 100),
            specialists_in_department=hospital.get("specialists_count", 2),
            has_emergency_unit=hospital.get("has_emergency", False),
            hospital_tier=hospital.get("tier", "mid"),
        )
        wait_score = {
            "emergency": 1.0,
            "low_wait": 0.85,
            "medium_wait": 0.55,
            "high_wait": 0.25,
        }.get(avail["wait_category"], 0.5)

        return (dist_score * 0.6) + (wait_score * 0.4)

    def _affordability_score(self, hospital: Dict[str, Any], budget_max: Optional[float]) -> float:
        """Measure alignment with patient budget + pricing transparency."""
        cost_min = hospital.get("cost_range", {}).get("min", 0)
        cost_max = hospital.get("cost_range", {}).get("max", 999999)
        cost_typical = (cost_min + cost_max) / 2

        if budget_max and budget_max > 0:
            if cost_typical <= budget_max:
                within_budget_score = 1.0
            elif cost_min <= budget_max:
                within_budget_score = 0.6
            else:
                within_budget_score = max(0.1, 1 - (cost_typical - budget_max) / budget_max)
        else:
            tier_scores = {"budget": 0.9, "mid": 0.7, "premium": 0.4}
            within_budget_score = tier_scores.get(hospital.get("tier", "mid"), 0.7)

        # NABH cashless insurance track record bonus
        cashless_bonus = 0.1 if hospital.get("nabh_accredited", False) else 0.0

        return min(1.0, within_budget_score + cashless_bonus)

    def compute_score(
        self,
        hospital: Dict[str, Any],
        procedure: str,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        budget_max: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Compute full fusion score for a single hospital."""
        clinical = self._clinical_score(hospital, procedure)
        reputation = self._reputation_score(hospital)
        accessibility = self._accessibility_score(hospital, user_lat, user_lon)
        affordability = self._affordability_score(hospital, budget_max)

        fusion = (
            clinical * self.WEIGHTS["clinical"] +
            reputation * self.WEIGHTS["reputation"] +
            accessibility * self.WEIGHTS["accessibility"] +
            affordability * self.WEIGHTS["affordability"]
        )

        return {
            **hospital,
            "rank_score": round(fusion, 3),
            "rank_signals": {
                "clinical_capability": round(clinical * 100),
                "reputation": round(reputation * 100),
                "accessibility": round(accessibility * 100),
                "affordability": round(affordability * 100),
            },
            "confidence": round(fusion, 2),
        }

    def score_and_rank(
        self,
        hospitals: List[Dict[str, Any]],
        procedure: str,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        budget_max: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Score and rank all hospitals. Returns list sorted by rank_score descending."""
        scored = [
            self.compute_score(h, procedure, user_lat, user_lon, budget_max)
            for h in hospitals
        ]
        return sorted(scored, key=lambda h: h["rank_score"], reverse=True)
