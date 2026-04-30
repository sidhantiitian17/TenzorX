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
}

COMORBIDITY_CONTINGENCY_WEIGHTS: dict[str, float] = {
    "diabetes": 0.15,
    "heart failure": 0.30,
    "hypertension": 0.05,
    "chronic kidney disease": 0.20,
    "copd": 0.12,
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

    for key, value in PROCEDURE_BASE_PRICES_INR.items():
        if key in normalized_name:
            return value, key

    return 150_000.0, "default_procedure"


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

    breakdown = {
        "procedure": resolved_procedure_key,
        "base_price_inr": base_cost,
        "comorbidity_multiplier": round(contingency_multiplier, 4),
        "geo_multiplier": round(geo_multiplier, 4),
        "matched_comorbidities": matched_comorbidities,
        "location_tier": resolved_tier,
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
    }
