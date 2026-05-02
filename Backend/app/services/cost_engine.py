"""
Cost estimation engine for procedure pricing and clinical contingencies.

This module provides a deterministic MVP implementation for base pricing and
comorbidity-driven cost adjustments. It is structured so the logic can later be
replaced with hospital tariff feeds, geospatial multipliers, or actuarial models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PROCEDURE_BASE_PRICES_INR: dict[str, float] = {
    "angioplasty": 200_000.0,
    "coronary artery bypass graft": 450_000.0,
    "total knee replacement": 280_000.0,
    "cataract surgery": 45_000.0,
    "appendectomy": 120_000.0,
    "nephrolithiasis": 150_000.0,
    "kidney stone removal": 150_000.0,
    "pcnl": 180_000.0,
    "urs": 120_000.0,
    "diabetes management": 80_000.0,
    "thyroid surgery": 200_000.0,
    "hernia repair": 100_000.0,
    "cholecystectomy": 150_000.0,
    "hysterectomy": 200_000.0,
    "cabg": 450_000.0,
    "heart bypass": 450_000.0,
    "knee arthroscopy": 80_000.0,
    "hip replacement": 350_000.0,
    "spine surgery": 300_000.0,
    "general consultation": 15_000.0,
}

# Component cost breakdown ratios as percentages of base cost
# Keys: procedure, doctor_fees, hospital_stay, diagnostics, medicines, contingency
PROCEDURE_COMPONENT_RATIOS: dict[str, dict[str, float]] = {
    "angioplasty": {"procedure": 0.45, "doctor_fees": 0.12, "hospital_stay": 0.22, "diagnostics": 0.10, "medicines": 0.06, "contingency": 0.05},
    "coronary artery bypass graft": {"procedure": 0.50, "doctor_fees": 0.10, "hospital_stay": 0.20, "diagnostics": 0.08, "medicines": 0.07, "contingency": 0.05},
    "cabg": {"procedure": 0.50, "doctor_fees": 0.10, "hospital_stay": 0.20, "diagnostics": 0.08, "medicines": 0.07, "contingency": 0.05},
    "heart bypass": {"procedure": 0.50, "doctor_fees": 0.10, "hospital_stay": 0.20, "diagnostics": 0.08, "medicines": 0.07, "contingency": 0.05},
    "total knee replacement": {"procedure": 0.48, "doctor_fees": 0.10, "hospital_stay": 0.20, "diagnostics": 0.08, "medicines": 0.09, "contingency": 0.05},
    "knee replacement": {"procedure": 0.48, "doctor_fees": 0.10, "hospital_stay": 0.20, "diagnostics": 0.08, "medicines": 0.09, "contingency": 0.05},
    "hip replacement": {"procedure": 0.48, "doctor_fees": 0.10, "hospital_stay": 0.20, "diagnostics": 0.08, "medicines": 0.09, "contingency": 0.05},
    "cataract surgery": {"procedure": 0.40, "doctor_fees": 0.15, "hospital_stay": 0.15, "diagnostics": 0.12, "medicines": 0.13, "contingency": 0.05},
    "appendectomy": {"procedure": 0.42, "doctor_fees": 0.12, "hospital_stay": 0.25, "diagnostics": 0.10, "medicines": 0.06, "contingency": 0.05},
    "nephrolithiasis": {"procedure": 0.40, "doctor_fees": 0.10, "hospital_stay": 0.20, "diagnostics": 0.15, "medicines": 0.10, "contingency": 0.05},
    "kidney stone removal": {"procedure": 0.40, "doctor_fees": 0.10, "hospital_stay": 0.20, "diagnostics": 0.15, "medicines": 0.10, "contingency": 0.05},
    "pcnl": {"procedure": 0.45, "doctor_fees": 0.10, "hospital_stay": 0.18, "diagnostics": 0.12, "medicines": 0.10, "contingency": 0.05},
    "urs": {"procedure": 0.35, "doctor_fees": 0.12, "hospital_stay": 0.15, "diagnostics": 0.20, "medicines": 0.13, "contingency": 0.05},
    "diabetes management": {"procedure": 0.20, "doctor_fees": 0.25, "hospital_stay": 0.05, "diagnostics": 0.30, "medicines": 0.15, "contingency": 0.05},
    "thyroid surgery": {"procedure": 0.45, "doctor_fees": 0.12, "hospital_stay": 0.20, "diagnostics": 0.10, "medicines": 0.08, "contingency": 0.05},
    "hernia repair": {"procedure": 0.42, "doctor_fees": 0.12, "hospital_stay": 0.22, "diagnostics": 0.09, "medicines": 0.10, "contingency": 0.05},
    "hernia": {"procedure": 0.42, "doctor_fees": 0.12, "hospital_stay": 0.22, "diagnostics": 0.09, "medicines": 0.10, "contingency": 0.05},
    "cholecystectomy": {"procedure": 0.45, "doctor_fees": 0.10, "hospital_stay": 0.20, "diagnostics": 0.10, "medicines": 0.10, "contingency": 0.05},
    "hysterectomy": {"procedure": 0.48, "doctor_fees": 0.10, "hospital_stay": 0.20, "diagnostics": 0.08, "medicines": 0.09, "contingency": 0.05},
    "spine surgery": {"procedure": 0.50, "doctor_fees": 0.10, "hospital_stay": 0.18, "diagnostics": 0.10, "medicines": 0.07, "contingency": 0.05},
    "knee arthroscopy": {"procedure": 0.40, "doctor_fees": 0.15, "hospital_stay": 0.15, "diagnostics": 0.15, "medicines": 0.10, "contingency": 0.05},
    "general consultation": {"procedure": 0.10, "doctor_fees": 0.50, "hospital_stay": 0.0, "diagnostics": 0.25, "medicines": 0.10, "contingency": 0.05},
    "default_procedure": {"procedure": 0.42, "doctor_fees": 0.12, "hospital_stay": 0.20, "diagnostics": 0.11, "medicines": 0.10, "contingency": 0.05},
}

COMORBIDITY_CONTINGENCY_WEIGHTS: dict[str, float] = {
    "diabetes": 0.15,
    "heart failure": 0.30,
    "hypertension": 0.05,
    "chronic kidney disease": 0.20,
    "copd": 0.12,
    "cardiac": 0.20,
    "kidney disease": 0.18,
    "asthma": 0.10,
    "obesity": 0.08,
}

# Component key mapping for frontend
COMPONENT_KEY_MAP = {
    "procedure": "procedure",
    "doctor_fees": "doctor_fees",
    "hospital_stay": "hospital_stay",
    "diagnostics": "diagnostics",
    "medicines": "medicines",
    "contingency": "contingency",
}

GEOGRAPHIC_MULTIPLIERS: dict[str, float] = {
    "tier-1": 1.20,
    "tier-2": 1.08,
    "tier-3": 0.95,
}


@dataclass(frozen=True, slots=True)
class CostEstimate:
    """Structured cost estimation output for downstream consumers."""

    base_cost: float
    adjusted_cost: float
    breakdown: dict[str, Any]


def _normalize_text(value: str) -> str:
    """Normalize free-text inputs for deterministic matching."""

    return " ".join(value.lower().split())


def _resolve_base_price(procedure_name: str) -> tuple[float, str]:
    """Resolve a mock base price for a known procedure."""

    normalized_name = _normalize_text(procedure_name)
    if normalized_name in PROCEDURE_BASE_PRICES_INR:
        return PROCEDURE_BASE_PRICES_INR[normalized_name], normalized_name

    # Check for partial matches
    for key, value in PROCEDURE_BASE_PRICES_INR.items():
        if key in normalized_name:
            return value, key
    
    # Check if any word in procedure name matches keys
    words = normalized_name.split()
    for word in words:
        if word in PROCEDURE_BASE_PRICES_INR:
            return PROCEDURE_BASE_PRICES_INR[word], word
        # Check partial matches for each word
        for key, value in PROCEDURE_BASE_PRICES_INR.items():
            if word in key or key in word:
                return value, key

    return 150_000.0, "default_procedure"


def _get_component_ratios(procedure_key: str) -> dict[str, float]:
    """Get component cost ratios for a procedure."""
    normalized_key = _normalize_text(procedure_key)
    
    # Direct lookup
    if normalized_key in PROCEDURE_COMPONENT_RATIOS:
        return PROCEDURE_COMPONENT_RATIOS[normalized_key]
    
    # Partial match
    for key, ratios in PROCEDURE_COMPONENT_RATIOS.items():
        if key in normalized_key or normalized_key in key:
            return ratios
    
    # Default ratios
    return PROCEDURE_COMPONENT_RATIOS.get("default_procedure", {
        "procedure": 0.42, "doctor_fees": 0.12, "hospital_stay": 0.20,
        "diagnostics": 0.11, "medicines": 0.10, "contingency": 0.05
    })


def estimate_component_costs(
    procedure_name: str,
    base_cost: float,
    geo_multiplier: float = 1.0,
    contingency_multiplier: float = 1.0,
) -> dict[str, dict[str, float]]:
    """Estimate costs for each component of a procedure.
    
    Returns a dict with component keys mapped to {min, max} cost ranges.
    Components: procedure, doctor_fees, hospital_stay, diagnostics, medicines, contingency
    """
    # Get component ratios
    procedure_key = _resolve_base_price(procedure_name)[1]
    ratios = _get_component_ratios(procedure_key)
    
    # Calculate component costs with some variation for min/max
    components = {}
    for component, ratio in ratios.items():
        base_component_cost = base_cost * ratio
        # Apply multipliers
        adjusted_cost = base_component_cost * geo_multiplier * contingency_multiplier
        # Create min/max range (±15% around adjusted cost)
        min_cost = round(adjusted_cost * 0.85, 0)
        max_cost = round(adjusted_cost * 1.15, 0)
        
        components[component] = {
            "min": int(min_cost),
            "max": int(max_cost),
            "ratio": ratio,
        }
    
    return components


def estimate_procedure_cost(
    procedure_name: str,
    known_comorbidities: list[str] | None = None,
    location_tier: str | None = None,
) -> CostEstimate:
    """Estimate the final procedure cost with comorbidity and geo adjustments.

    Args:
        procedure_name: Natural-language procedure label such as angioplasty.
        known_comorbidities: Optional list of patient comorbidities.
        location_tier: Optional city tier used to apply a geo multiplier.

    Returns:
        CostEstimate with base_cost, adjusted_cost, and a detailed breakdown.
    """

    base_cost, resolved_procedure_key = _resolve_base_price(procedure_name)
    normalized_comorbidities = [
        _normalize_text(comorbidity) for comorbidity in (known_comorbidities or [])
    ]

    contingency_multiplier = 1.0
    matched_comorbidities: list[dict[str, Any]] = []
    for comorbidity, weight in COMORBIDITY_CONTINGENCY_WEIGHTS.items():
        if comorbidity in normalized_comorbidities:
            contingency_multiplier += weight
            matched_comorbidities.append(
                {
                    "comorbidity": comorbidity,
                    "weight": weight,
                    "impact": f"+{int(weight * 100)}%",
                }
            )

    geo_multiplier = 1.0
    resolved_tier = None
    if location_tier:
        resolved_tier = _normalize_text(location_tier)
        geo_multiplier = GEOGRAPHIC_MULTIPLIERS.get(resolved_tier, 1.0)

    adjusted_cost = round(base_cost * contingency_multiplier * geo_multiplier, 2)

    # Calculate component-level breakdown
    component_costs = estimate_component_costs(
        procedure_name=procedure_name,
        base_cost=base_cost,
        geo_multiplier=geo_multiplier,
        contingency_multiplier=contingency_multiplier,
    )
    
    breakdown = {
        "procedure": resolved_procedure_key,
        "base_price_inr": base_cost,
        "comorbidity_multiplier": round(contingency_multiplier, 4),
        "geo_multiplier": round(geo_multiplier, 4),
        "matched_comorbidities": matched_comorbidities,
        "location_tier": resolved_tier,
        "component_costs": component_costs,
        "reason": (
            "Base price adjusted using known comorbidity contingencies"
            + (" and geographic pricing" if location_tier else "")
        ),
    }

    return CostEstimate(
        base_cost=base_cost,
        adjusted_cost=adjusted_cost,
        breakdown=breakdown,
    )


def estimate_procedure_cost_dict(
    procedure_name: str,
    known_comorbidities: list[str] | None = None,
    location_tier: str | None = None,
) -> dict[str, Any]:
    """Convenience wrapper that returns a plain dictionary payload."""

    estimate = estimate_procedure_cost(
        procedure_name=procedure_name,
        known_comorbidities=known_comorbidities,
        location_tier=location_tier,
    )
    return {
        "base_cost": estimate.base_cost,
        "adjusted_cost": estimate.adjusted_cost,
        "breakdown": estimate.breakdown,
        "component_costs": estimate.breakdown.get("component_costs", {}),
    }


def format_cost_breakdown_for_frontend(
    component_costs: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    """Format component costs for frontend display.
    
    Maps internal component keys to frontend labels.
    """
    label_map = {
        "procedure": "Procedure / Surgery",
        "doctor_fees": "Doctor Fees",
        "hospital_stay": "Hospital Stay",
        "diagnostics": "Diagnostics",
        "medicines": "Medicines",
        "contingency": "Contingency",
    }
    
    breakdown_items = []
    for key, label in label_map.items():
        cost_data = component_costs.get(key, {"min": 0, "max": 0})
        breakdown_items.append({
            "label": label,
            "min": int(cost_data.get("min", 0)),
            "max": int(cost_data.get("max", 0)),
        })
    
    return breakdown_items


def estimate_cost_with_fallback(
    procedure_name: str,
    pathway_cost_data: dict[str, Any] | None = None,
    known_comorbidities: list[str] | None = None,
    location_tier: str | None = None,
) -> dict[str, Any]:
    """Estimate costs using pathway data (KG) if available, otherwise use cost engine.
    
    This is the main entry point for cost estimation that combines KG and cost engine data.
    
    Args:
        procedure_name: Name of the procedure
        pathway_cost_data: Optional cost data from Knowledge Graph pathway
        known_comorbidities: List of patient comorbidities
        location_tier: City tier for geographic multiplier
        
    Returns:
        Dict with total_cost_range, component_breakdown, and metadata
    """
    # Try to use Knowledge Graph pathway data first
    if pathway_cost_data:
        total_min = pathway_cost_data.get("total_min", 0)
        total_max = pathway_cost_data.get("total_max", 0)
        
        if total_min > 0 and total_max > 0:
            # Use KG data for total, but get component breakdown from cost engine
            cost_estimate = estimate_procedure_cost(
                procedure_name=procedure_name,
                known_comorbidities=known_comorbidities,
                location_tier=location_tier,
            )
            
            # Scale component costs to match KG total
            kg_total_avg = (total_min + total_max) / 2
            engine_total = cost_estimate.adjusted_cost
            scale_factor = kg_total_avg / engine_total if engine_total > 0 else 1.0
            
            component_costs = cost_estimate.breakdown.get("component_costs", {})
            scaled_components = {}
            for key, costs in component_costs.items():
                scaled_components[key] = {
                    "min": int(costs["min"] * scale_factor),
                    "max": int(costs["max"] * scale_factor),
                    "ratio": costs.get("ratio", 0),
                }
            
            return {
                "total_cost_range": {"min": int(total_min), "max": int(total_max)},
                "typical_range": {"min": int(total_min * 0.9), "max": int(total_max * 1.1)},
                "component_costs": scaled_components,
                "breakdown_items": format_cost_breakdown_for_frontend(scaled_components),
                "source": "knowledge_graph_with_component_scaling",
                "geo_multiplier": cost_estimate.breakdown.get("geo_multiplier", 1.0),
                "comorbidity_multiplier": cost_estimate.breakdown.get("comorbidity_multiplier", 1.0),
            }
    
    # Fallback to cost engine
    cost_estimate = estimate_procedure_cost(
        procedure_name=procedure_name,
        known_comorbidities=known_comorbidities,
        location_tier=location_tier,
    )
    
    component_costs = cost_estimate.breakdown.get("component_costs", {})
    
    return {
        "total_cost_range": {
            "min": int(cost_estimate.adjusted_cost * 0.85),
            "max": int(cost_estimate.adjusted_cost * 1.15),
        },
        "typical_range": {
            "min": int(cost_estimate.adjusted_cost * 0.9),
            "max": int(cost_estimate.adjusted_cost * 1.1),
        },
        "component_costs": component_costs,
        "breakdown_items": format_cost_breakdown_for_frontend(component_costs),
        "source": "cost_engine",
        "geo_multiplier": cost_estimate.breakdown.get("geo_multiplier", 1.0),
        "comorbidity_multiplier": cost_estimate.breakdown.get("comorbidity_multiplier", 1.0),
    }
