"""
Age & Comorbidity Cost Adjustment Engine (Gap 6 Resolver).

Adjusts cost estimates for patient age and comorbidities.
Formula: Final_Estimated_Cost = Adjusted_Cost × (1 + Σ ωᵢCᵢ)
"""

from typing import Dict, Any, List, Optional


class ComorbidityEngine:
    """
    Adjusts cost estimates for patient age and comorbidities.
    Based on epidemiological research on cost uplift factors.
    """

    # Comorbidity weights (ωᵢ)
    COMORBIDITY_WEIGHTS = {
        "diabetes": {"weight": 0.25, "icu_prob_uplift": 0.08},
        "hypertension": {"weight": 0.10, "icu_prob_uplift": 0.03},
        "cardiac_history": {"weight": 0.40, "icu_prob_uplift": 0.15},
        "heart_failure": {"weight": 0.55, "icu_prob_uplift": 0.20},
        "kidney_disease": {"weight": 0.40, "icu_prob_uplift": 0.12},
        "renal_disease": {"weight": 0.40, "icu_prob_uplift": 0.12},
        "ascvd": {"weight": 0.35, "icu_prob_uplift": 0.10},
        "obesity": {"weight": 0.15, "icu_prob_uplift": 0.05},
        "copd": {"weight": 0.20, "icu_prob_uplift": 0.07},
    }

    # Age risk bands
    AGE_RISK = {
        (0, 40): 0.00,
        (40, 60): 0.05,
        (60, 70): 0.12,
        (70, 80): 0.20,
        (80, 120): 0.30,
    }

    def _age_weight(self, age: Optional[int]) -> float:
        """Get risk weight based on age."""
        if age is None:
            return 0.05  # Default moderate uplift
        for (lo, hi), weight in self.AGE_RISK.items():
            if lo <= age < hi:
                return weight
        return 0.05

    def adjust(
        self,
        cost_estimate: Dict[str, Any],
        comorbidities: List[str],
        age: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Apply comorbidity and age adjustments to a cost estimate.
        Returns the final estimate with risk_adjustments list.
        """
        comorbidities_lower = [c.lower().strip().replace(" ", "_") for c in comorbidities]

        total_weight = self._age_weight(age)
        risk_adjustments = []

        for comorbidity in comorbidities_lower:
            if comorbidity in self.COMORBIDITY_WEIGHTS:
                w = self.COMORBIDITY_WEIGHTS[comorbidity]
                total_weight += w["weight"]
                risk_adjustments.append({
                    "factor": comorbidity,
                    "weight": w["weight"],
                    "icu_probability_uplift": w["icu_prob_uplift"],
                    "impact": self._impact_label(w["weight"]),
                })

        # Apply: Final = Adjusted_Cost × (1 + Σ ωᵢCᵢ)
        multiplier = 1 + total_weight
        adjusted = {}

        if "total" in cost_estimate:
            t = cost_estimate["total"]
            adjusted["total"] = {
                "min": round(t["min"] * multiplier),
                "max": round(t["max"] * multiplier),
                "typical_min": round(t.get("typical_min", t["min"]) * multiplier),
                "typical_max": round(t.get("typical_max", t["max"]) * multiplier),
            }

        if "breakdown" in cost_estimate:
            adjusted["breakdown"] = {}
            for component, values in cost_estimate["breakdown"].items():
                adjusted["breakdown"][component] = {
                    "min": round(values["min"] * multiplier),
                    "max": round(values["max"] * multiplier),
                }
                if "nights" in values:
                    adjusted["breakdown"][component]["nights"] = values["nights"]

        adjusted["comorbidity_multiplier"] = round(multiplier, 3)
        adjusted["risk_adjustments"] = risk_adjustments
        adjusted["comorbidity_warnings"] = [
            f"{ra['factor'].replace('_',' ').title()}: {ra['impact']}"
            for ra in risk_adjustments
        ]

        return {**cost_estimate, **adjusted}

    def get_impact(self, condition: str) -> Optional[Dict[str, Any]]:
        """Get impact details for a comorbidity condition.
        
        Args:
            condition: Comorbidity name
            
        Returns:
            Dict with impact details or None if not found
        """
        condition_lower = condition.lower().strip().replace(" ", "_")
        if condition_lower in self.COMORBIDITY_WEIGHTS:
            w = self.COMORBIDITY_WEIGHTS[condition_lower]
            return {
                "condition": condition,
                "weight": w["weight"],
                "min_add": int(w["weight"] * 10000),  # Estimated cost addition
                "max_add": int(w["weight"] * 30000),
                "impact": self._impact_label(w["weight"]),
            }
        return None

    def _impact_label(self, weight: float) -> str:
        """Get human-readable impact label for a weight."""
        if weight >= 0.40:
            return "High cost impact — significantly increases complications risk"
        elif weight >= 0.20:
            return "Moderate cost impact — may require extended ICU stay"
        return "Low-moderate cost impact — increases monitoring requirements"
