"""
Hospital Comparison Engine (Gap 8 Resolver).

Side-by-side hospital comparison logic.
Computes 'Best Value' badge and highlights meaningful differences.
"""

from typing import List, Dict, Any


class ComparisonEngine:
    """
    Side-by-side hospital comparison logic.
    Computes 'Best Value' badge and highlights meaningful differences.
    """

    def compare(self, hospitals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare 2-3 hospitals and return a structured comparison matrix.
        """
        if not 2 <= len(hospitals) <= 3:
            raise ValueError("Compare requires 2-3 hospitals")

        comparison_rows = []
        attributes = [
            ("name", "Hospital Name"),
            ("rating", "Rating (out of 5)"),
            ("nabh_accredited", "NABH Accredited"),
            ("tier", "Hospital Tier"),
            ("distance_km", "Distance"),
            ("cost_range", "Estimated Cost Range"),
            ("confidence", "Recommendation Confidence"),
            ("rank_signals.clinical_capability", "Clinical Score"),
            ("rank_signals.reputation", "Reputation Score"),
            ("rank_signals.accessibility", "Accessibility Score"),
            ("rank_signals.affordability", "Affordability Score"),
            ("has_icu", "ICU Available"),
            ("has_emergency", "24/7 Emergency"),
        ]

        for attr_key, attr_label in attributes:
            row = {"attribute": attr_label, "values": [], "highlight": False}
            values = []
            for h in hospitals:
                # Handle nested keys like "rank_signals.clinical_capability"
                if "." in attr_key:
                    parts = attr_key.split(".")
                    val = h
                    for part in parts:
                        val = val.get(part, "N/A") if isinstance(val, dict) else "N/A"
                else:
                    val = h.get(attr_key, "N/A")

                # Format values for display
                if attr_key == "cost_range":
                    val = f"Rs {val.get('min', 0):,} – Rs {val.get('max', 0):,}"
                elif attr_key == "distance_km":
                    val = f"{val:.1f} km" if isinstance(val, (int, float)) else val
                elif attr_key in ("nabh_accredited", "has_icu", "has_emergency"):
                    val = "✅ Yes" if val else "❌ No"
                elif attr_key == "confidence":
                    val = f"{int(val * 100)}%"
                elif attr_key.startswith("rank_signals."):
                    val = f"{val}/100"

                values.append(val)

            row["values"] = values

            # Highlight rows where values differ significantly
            if len(set(str(v) for v in values)) > 1:
                row["highlight"] = True

            comparison_rows.append(row)

        # Best Value badge — composite formula
        best_value_idx = self._find_best_value(hospitals)

        return {
            "hospitals": [h.get("name", "Unknown") for h in hospitals],
            "comparison_rows": comparison_rows,
            "best_value_hospital": hospitals[best_value_idx].get("name"),
            "best_value_index": best_value_idx,
            "best_value_rationale": self._best_value_rationale(hospitals[best_value_idx]),
        }

    def _find_best_value(self, hospitals: List[Dict[str, Any]]) -> int:
        """
        Best Value = (Rating × 0.4) + (1/CostMidpoint_normalized × 0.3) + (Confidence × 0.3)
        """
        scores = []
        costs = [
            (h.get("cost_range", {}).get("min", 0) + h.get("cost_range", {}).get("max", 0)) / 2
            for h in hospitals
        ]
        max_cost = max(costs) if costs else 1

        for i, h in enumerate(hospitals):
            rating_score = h.get("rating", 0) / 5.0
            cost_score = 1 - (costs[i] / max_cost)  # Invert: lower cost = higher score
            confidence_score = h.get("confidence", 0)
            composite = (rating_score * 0.4) + (cost_score * 0.3) + (confidence_score * 0.3)
            scores.append(composite)

        return scores.index(max(scores))

    def _best_value_rationale(self, hospital: Dict[str, Any]) -> str:
        """Generate rationale for why this hospital is best value."""
        tier = hospital.get("tier", "mid")
        rating = hospital.get("rating", 0)
        nabh = hospital.get("nabh_accredited", False)
        parts = []
        if rating >= 4.0:
            parts.append(f"High patient rating ({rating}★)")
        if nabh:
            parts.append("NABH accredited")
        if tier == "budget":
            parts.append("Lowest cost tier")
        elif tier == "mid":
            parts.append("Best cost-quality balance")
        return " · ".join(parts) if parts else "Best composite score"
