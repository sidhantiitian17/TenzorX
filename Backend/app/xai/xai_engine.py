"""
XAI Engine - Explainable AI module (TC-28 to TC-29).

Provides SHAP and LIME explanations for model predictions.
"""

from typing import Dict, Any
from app.xai.shap_explainer import FusionSHAPExplainer
from app.xai.lime_explainer import SeverityLIMEExplainer


def generate_shap_explanation(scores: dict[str, float]) -> dict[str, Any]:
    """
    Generate SHAP waterfall explanation for fusion scores.
    
    Args:
        scores: Dict with keys like clinical, reputation, accessibility, affordability
        
    Returns:
        Dict with waterfall_data and final_score
    """
    # Normalize scores to 0-100 scale for the explainer
    hospital = {
        "id": "test_hospital",
        "name": "Test Hospital",
        "rank_signals": {
            "clinical_capability": scores.get("clinical", 0.5) * 100,
            "reputation": scores.get("reputation", 0.5) * 100,
            "accessibility": scores.get("accessibility", 0.5) * 100,
            "affordability": scores.get("affordability", 0.5) * 100,
        }
    }
    
    explainer = FusionSHAPExplainer()
    result = explainer.explain(hospital)
    
    return {
        "waterfall_data": result["waterfall"],
        "final_score": result["final_score"],
        "base_value": result["base_value"],
    }


def explain_severity_with_lime(text: str, predicted_severity: str) -> dict[str, Any]:
    """
    Explain severity classification using LIME-style token highlighting.
    
    Args:
        text: Original user input text
        predicted_severity: The predicted severity (RED, YELLOW, GREEN)
        
    Returns:
        Dict with highlighted_tokens and explanation
    """
    explainer = SeverityLIMEExplainer()
    result = explainer.explain(text, predicted_severity)
    
    # Extract highlighted tokens from key_terms
    highlighted = [
        term["term"] 
        for term in result.get("key_terms", [])
        if term.get("influence") in ["high", "medium"]
    ]
    
    return {
        "highlighted_tokens": highlighted,
        "key_terms": result.get("key_terms", []),
        "explanation": result.get("explanation", ""),
    }
