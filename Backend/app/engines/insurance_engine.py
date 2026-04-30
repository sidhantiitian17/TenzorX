"""
Insurance Cashless Integration Engine (Gap 2 Resolver).

Objective arbitration layer for cashless insurance pre-authorization.
Classifies hospitals into segments and predicts OOP expenses.
"""

from typing import Dict, Any


class InsuranceEngine:
    """
    Objective arbitration layer for cashless insurance pre-authorization.
    Addresses the IRDAI 'cashless everywhere' initiative friction.
    """

    # Room rent capping thresholds by policy type (INR/day)
    ROOM_RENT_CAPS = {
        "basic": 1000,
        "standard": 3000,
        "premium": 6000,
        "no_cap": 999999,
    }

    # Hospital tier base room rates
    HOSPITAL_ROOM_RATES = {
        "budget": {"general_ward": 800, "semi_private": 1500, "private": 2500},
        "mid": {"general_ward": 1500, "semi_private": 3000, "private": 5000},
        "premium": {"general_ward": 3000, "semi_private": 6000, "private": 10000},
    }

    def estimate_cashless_eligibility(
        self,
        hospital_tier: str,
        procedure_cost: Dict[str, Any],
        policy_type: str,
        stay_nights: int,
        policy_sum_assured: float,
    ) -> Dict[str, Any]:
        """
        Estimate cashless pre-authorization likelihood and OOP exposure.
        """
        room_cap = self.ROOM_RENT_CAPS.get(policy_type, 3000)
        room_rates = self.HOSPITAL_ROOM_RATES.get(hospital_tier, self.HOSPITAL_ROOM_RATES["mid"])

        # Room rent OOP calculation
        actual_room_rate = room_rates["private"]
        room_oop = max(0, (actual_room_rate - room_cap) * stay_nights)

        # Total claim vs sum assured
        total_min = procedure_cost.get("total", {}).get("min", 0)
        total_max = procedure_cost.get("total", {}).get("max", 0)
        coverage_min = max(0, min(total_min - room_oop, policy_sum_assured))
        coverage_max = max(0, min(total_max - room_oop, policy_sum_assured))
        oop_min = total_min - coverage_min
        oop_max = total_max - coverage_max

        # Cashless approval likelihood
        if total_max <= policy_sum_assured * 0.7:
            cashless_likelihood = "High"
            approval_note = "Well within policy limits — pre-authorization likely within 4-6 hours."
        elif total_max <= policy_sum_assured:
            cashless_likelihood = "Moderate"
            approval_note = "Within limits but close to sum assured — attach all supporting documents."
        else:
            cashless_likelihood = "Low"
            approval_note = "Estimated cost exceeds sum assured — partial cashless + reimbursement likely."

        return {
            "hospital_tier": hospital_tier,
            "policy_type": policy_type,
            "room_rent_cap_per_day": room_cap,
            "actual_room_rate": actual_room_rate,
            "room_rent_oop_total": room_oop,
            "estimated_coverage_range": {"min": round(coverage_min), "max": round(coverage_max)},
            "estimated_oop_range": {"min": round(oop_min), "max": round(oop_max)},
            "cashless_likelihood": cashless_likelihood,
            "approval_note": approval_note,
            "documents_required": [
                "Policy document + health card",
                "Doctor's prescription / referral",
                "Hospital admission form",
                "Pre-authorization request form",
                "Photo ID (Aadhar)",
            ],
        }
