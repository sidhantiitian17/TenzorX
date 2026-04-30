"""
SHAP Explainer for fusion score attribution.

Generates waterfall plot data for the frontend to visualize.
"""

from typing import Dict, Any, List


class FusionSHAPExplainer:
    """
    Explains the Multi-Source Data Fusion Score using SHAP-style attribution.
    Generates waterfall plot data for visualization.
    """

    FEATURE_NAMES = ["clinical_capability", "reputation", "accessibility", "affordability"]
    WEIGHTS = [0.40, 0.25, 0.20, 0.15]

    def explain(self, hospital: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SHAP-style contribution explanation for a hospital's fusion score.
        Returns data suitable for rendering a waterfall chart.
        """
        signals = hospital.get("rank_signals", {})
        raw_scores = [
            signals.get("clinical_capability", 50) / 100.0,
            signals.get("reputation", 50) / 100.0,
            signals.get("accessibility", 50) / 100.0,
            signals.get("affordability", 50) / 100.0,
        ]
        
        contributions = [raw_scores[i] * self.WEIGHTS[i] for i in range(4)]

        base_value = 0.5
        final_score = sum(contributions)

        waterfall_data = []
        running_total = base_value
        
        for i, (feature, contribution) in enumerate(zip(self.FEATURE_NAMES, contributions)):
            delta = contribution - (self.WEIGHTS[i] * 0.5)
            waterfall_data.append({
                "feature": feature.replace("_", " ").title(),
                "raw_score": round(raw_scores[i] * 100),
                "weight": self.WEIGHTS[i],
                "contribution": round(contribution, 4),
                "delta_from_baseline": round(delta, 4),
                "direction": "positive" if delta >= 0 else "negative",
                "running_total": round(running_total + delta, 3),
            })
            running_total += delta

        return {
            "hospital_id": hospital.get("id"),
            "hospital_name": hospital.get("name"),
            "base_value": base_value,
            "final_score": round(final_score, 3),
            "waterfall": waterfall_data,
            "summary": self._generate_summary(hospital, waterfall_data),
        }

    def _generate_summary(self, hospital: Dict[str, Any], waterfall: List[Dict[str, Any]]) -> str:
        """Generate human-readable summary of the explanation."""
        positives = [w["feature"] for w in waterfall if w["direction"] == "positive"]
        negatives = [w["feature"] for w in waterfall if w["direction"] == "negative"]
        
        msg = f"{hospital.get('name')} ranks here because "
        if positives:
            msg += f"its {' and '.join(positives)} pushed the score up"
        if negatives:
            msg += f", while {' and '.join(negatives)} slightly reduced it"
        return msg + "."
