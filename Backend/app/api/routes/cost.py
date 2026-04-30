"""
Cost Estimation API route.

Provides cost estimates with full engine pipeline.
"""

from fastapi import APIRouter
from app.schemas.request_models import CostRequest
from app.engines.cost_engine import CostEngine
from app.engines.geo_pricing import GeoPricingEngine
from app.engines.comorbidity_engine import ComorbidityEngine
from app.engines.pathway_engine import PathwayEngine

router = APIRouter()
cost_engine = CostEngine()
geo_engine = GeoPricingEngine()
comorbidity_engine = ComorbidityEngine()
pathway_engine = PathwayEngine()


@router.post("")
async def estimate_cost(request: CostRequest):
    """
    Estimate treatment cost with geographic and comorbidity adjustments.
    """
    city_tier = geo_engine.get_city_tier(request.city)
    base = cost_engine.estimate(request.procedure, city_tier)
    geo_adjusted = geo_engine.apply_multiplier(base, city_tier)
    final = comorbidity_engine.adjust(
        geo_adjusted,
        comorbidities=request.comorbidities or [],
        age=request.age,
    )
    pathway = pathway_engine.get_pathway(request.procedure)
    return {"cost_estimate": final, "pathway": pathway}
