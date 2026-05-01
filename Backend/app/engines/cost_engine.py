"""
Cost Engine - Base cost estimation for medical procedures.

Provides component-level cost breakdowns in INR (Tier 1 metro baseline).
"""

from typing import Dict, Any


class CostEngine:
    """
    Generates component-level cost breakdowns for medical procedures.
    Costs are BASE rates (Tier 1 metro) before geographic adjustment.
    """

    # Base benchmark data (INR, Tier 1 metro baseline)
    BASE_BENCHMARKS: Dict[str, Dict[str, Any]] = {
        "angioplasty": {
            "total": {"min": 120000, "max": 300000, "typical_min": 150000, "typical_max": 200000},
            "breakdown": {
                "procedure": {"min": 100000, "max": 250000},
                "doctor_fees": {"min": 15000, "max": 30000},
                "hospital_stay": {"min": 20000, "max": 60000, "nights": "3-5"},
                "diagnostics": {"min": 10000, "max": 30000},
                "medicines": {"min": 5000, "max": 15000},
                "contingency": {"min": 10000, "max": 40000},
            },
        },
        "total knee arthroplasty": {
            "total": {"min": 150000, "max": 450000, "typical_min": 200000, "typical_max": 300000},
            "breakdown": {
                "procedure": {"min": 90000, "max": 200000},
                "doctor_fees": {"min": 15000, "max": 30000},
                "hospital_stay": {"min": 25000, "max": 60000, "nights": "4-6"},
                "diagnostics": {"min": 8000, "max": 15000},
                "medicines": {"min": 5000, "max": 12000},
                "contingency": {"min": 10000, "max": 30000},
            },
        },
        "cataract surgery": {
            "total": {"min": 15000, "max": 60000, "typical_min": 20000, "typical_max": 40000},
            "breakdown": {
                "procedure": {"min": 10000, "max": 45000},
                "doctor_fees": {"min": 2000, "max": 8000},
                "hospital_stay": {"min": 0, "max": 5000, "nights": "0-1"},
                "diagnostics": {"min": 1500, "max": 5000},
                "medicines": {"min": 1000, "max": 3000},
                "contingency": {"min": 500, "max": 2000},
            },
        },
        "dialysis": {
            "total": {"min": 3000, "max": 8000, "typical_min": 4000, "typical_max": 6000},
            "breakdown": {
                "procedure": {"min": 2000, "max": 5000},
                "doctor_fees": {"min": 500, "max": 1000},
                "hospital_stay": {"min": 0, "max": 1000, "nights": "0"},
                "diagnostics": {"min": 300, "max": 800},
                "medicines": {"min": 200, "max": 500},
                "contingency": {"min": 100, "max": 500},
            },
        },
        "cabg": {
            "total": {"min": 150000, "max": 500000, "typical_min": 200000, "typical_max": 350000},
            "breakdown": {
                "procedure": {"min": 100000, "max": 350000},
                "doctor_fees": {"min": 25000, "max": 60000},
                "hospital_stay": {"min": 40000, "max": 100000, "nights": "7-10"},
                "diagnostics": {"min": 15000, "max": 40000},
                "medicines": {"min": 10000, "max": 25000},
                "contingency": {"min": 20000, "max": 80000},
            },
        },
    }

    def estimate(self, procedure: str, city_tier: str = "tier2") -> Dict[str, Any]:
        """
        Return base cost estimate for a procedure.
        This is BEFORE geographic multiplier and comorbidity adjustments.
        """
        procedure_lower = procedure.lower().strip()

        # Find matching benchmark
        benchmark = None
        for key, data in self.BASE_BENCHMARKS.items():
            if key in procedure_lower or procedure_lower in key:
                benchmark = data
                break

        if not benchmark:
            # Generic estimate for unknown procedures
            benchmark = {
                "total": {"min": 20000, "max": 150000, "typical_min": 50000, "typical_max": 100000},
                "breakdown": {
                    "procedure": {"min": 10000, "max": 80000},
                    "doctor_fees": {"min": 3000, "max": 15000},
                    "hospital_stay": {"min": 5000, "max": 30000, "nights": "1-3"},
                    "diagnostics": {"min": 1000, "max": 10000},
                    "medicines": {"min": 500, "max": 5000},
                    "contingency": {"min": 500, "max": 10000},
                },
            }

        return {
            "procedure": procedure,
            "city_tier": city_tier,
            "confidence": 0.0,
            **benchmark,
        }


# =============================================================================
# Module-level Cost Functions (TC-18 to TC-19)
# =============================================================================

# Geographic multipliers (γ_geo)
GEO_MULTIPLIERS = {
    1: 1.00,  # Tier 1: Mumbai, Delhi, Bangalore (baseline)
    2: 0.92,  # Tier 2: Nagpur, Jaipur, Lucknow
    3: 0.83,  # Tier 3: Raipur, Ahmedabad, Patna
}

# Comorbidity multipliers (ωᵢ)
COMORBIDITY_MULTIPLIERS = {
    "heart_failure": 3.3,
    "hf": 3.3,
    "i50.9": 3.3,
    "diabetes": 0.8,
    "dm": 0.8,
    "e11.9": 0.8,
    "hypertension": 0.5,
    "htn": 0.5,
    "i10": 0.5,
    "ckd": 1.5,
    "n18.9": 1.5,
    "copd": 1.2,
    "j44.1": 1.2,
    "ascvd": 1.2,
    "i25.10": 1.2,
}


def calculate_adjusted_cost(base_cost: float, city_tier: int) -> float:
    """
    Calculate cost adjusted for geographic tier.
    
    Formula: Adjusted_Cost = Base_Cost × γ_geo
    
    Args:
        base_cost: Base cost in INR (Tier 1 baseline)
        city_tier: 1, 2, or 3
        
    Returns:
        Adjusted cost in INR
    """
    multiplier = GEO_MULTIPLIERS.get(city_tier, 0.92)  # Default to Tier 2
    return round(base_cost * multiplier)


def calculate_final_cost(adjusted_cost: float, comorbidities: list[str]) -> float:
    """
    Calculate final cost with comorbidity adjustments.
    
    Formula: Final_Cost = Adjusted_Cost × (1 + Σ ωᵢCᵢ)
    
    Args:
        adjusted_cost: Geographic-adjusted cost
        comorbidities: List of comorbidity names/codes
        
    Returns:
        Final cost in INR
    """
    if not comorbidities:
        return round(adjusted_cost)
    
    total_multiplier = 1.0
    for comorbidity in comorbidities:
        key = comorbidity.lower().strip()
        mult = COMORBIDITY_MULTIPLIERS.get(key, 0.0)
        total_multiplier += mult
    
    return round(adjusted_cost * total_multiplier)
