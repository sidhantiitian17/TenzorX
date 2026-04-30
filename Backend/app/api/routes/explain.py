"""
Explainability API route.

Provides XAI explanations for hospital rankings.
"""

from fastapi import APIRouter, HTTPException
from app.xai.shap_explainer import FusionSHAPExplainer
from app.knowledge_graph.neo4j_client import Neo4jClient
from app.engines.fusion_score import FusionScoreEngine

router = APIRouter()
shap_explainer = FusionSHAPExplainer()
neo4j = Neo4jClient()
fusion_engine = FusionScoreEngine()


@router.get("/{hospital_id}")
async def explain_hospital(hospital_id: str, procedure: str = "general"):
    """
    Get SHAP explanation for a hospital's fusion score.
    """
    try:
        # Get hospital data
        hospital = neo4j.get_hospital_by_id(hospital_id)
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        # Compute fusion score to get rank_signals
        scored = fusion_engine.compute_score(hospital, procedure)
        
        # Generate explanation
        explanation = shap_explainer.explain(scored)
        return {"shap_explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
