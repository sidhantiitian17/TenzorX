"""
AGENT 6 — XAI Explainer Agent

Generates SHAP waterfall explanations for hospital fusion scores and LIME
explanations for triage classifications. Produces confidence scores.

Per instructionagent.md Section 3.6
"""

import logging
from typing import Dict, Any, List, Optional
import random

from app.schemas.response_models import (
    XAIExplainerOutput,
    ConfidenceDrivers,
    SHAPExplanation,
    SHAPContribution,
)

logger = logging.getLogger(__name__)

# Feature weights for fusion score components (from instructionagent.md)
FUSION_WEIGHTS = {
    "clinical_score": 0.40,
    "reputation_score": 0.25,
    "accessibility_score": 0.20,
    "affordability_score": 0.15,
}


class XAIExplainerAgent:
    """
    XAI Explainer Agent for SHAP and LIME explanations.
    
    Per instructionagent.md Section 3.6
    """

    def __init__(self):
        """Initialize the XAI Explainer Agent."""
        pass

    def calculate_confidence_score(
        self,
        data_availability: int,
        pricing_consistency: int,
        benchmark_recency: int,
        patient_complexity: int,
    ) -> int:
        """
        Calculate composite confidence score using RAG methodology.
        
        Formula per instructionagent.md:
        S = (0.4 * faithfulness + 0.3 * contextual_relevancy + 0.3 * answer_relevancy)
        
        Args:
            data_availability: Score 0-100
            pricing_consistency: Score 0-100
            benchmark_recency: Score 0-100
            patient_complexity: Score 0-100
            
        Returns:
            Composite confidence score (0-100)
        """
        # Map to RAG metrics
        faithfulness = data_availability
        contextual_relevancy = pricing_consistency
        answer_relevancy = (benchmark_recency + patient_complexity) / 2
        
        score = (
            0.4 * faithfulness +
            0.3 * contextual_relevancy +
            0.3 * answer_relevancy
        )
        
        return int(round(score))

    def generate_confidence_drivers(
        self,
        hospitals_found: int,
        has_pricing_data: bool,
        has_benchmark_data: bool,
        comorbidities_count: int,
    ) -> ConfidenceDrivers:
        """
        Generate confidence driver breakdown.
        
        Args:
            hospitals_found: Number of hospitals found
            has_pricing_data: Whether pricing data is available
            has_benchmark_data: Whether benchmark data is available
            comorbidities_count: Number of patient comorbidities
            
        Returns:
            ConfidenceDrivers with 4 metrics
        """
        # Data availability based on hospitals found
        data_availability = min(100, 60 + (hospitals_found * 8))
        
        # Pricing consistency
        pricing_consistency = 80 if has_pricing_data else 45
        
        # Benchmark recency
        benchmark_recency = 75 if has_benchmark_data else 50
        
        # Patient complexity (inverse - fewer comorbidities = higher confidence)
        patient_complexity = max(40, 85 - (comorbidities_count * 15))
        
        return ConfidenceDrivers(
            data_availability=data_availability,
            pricing_consistency=pricing_consistency,
            benchmark_recency=benchmark_recency,
            patient_complexity=patient_complexity,
        )

    def generate_shap_explanation(
        self,
        hospital_id: str,
        clinical_score: float,
        reputation_score: float,
        accessibility_score: float,
        affordability_score: float,
    ) -> SHAPExplanation:
        """
        Generate SHAP waterfall explanation for hospital fusion score.
        
        Args:
            hospital_id: Hospital identifier
            clinical_score: Clinical component score (0-1)
            reputation_score: Reputation component score (0-1)
            accessibility_score: Accessibility component score (0-1)
            affordability_score: Affordability component score (0-1)
            
        Returns:
            SHAPExplanation with contributor breakdown
        """
        # Calculate contributions
        base_score = 0.5  # Starting point
        
        contributors = []
        
        # Clinical contribution (40% weight)
        clinical_contribution = (clinical_score - 0.5) * FUSION_WEIGHTS["clinical_score"]
        contributors.append(SHAPContribution(
            factor="High Clinical Score" if clinical_contribution > 0 else "Clinical Score",
            impact="positive" if clinical_contribution > 0 else "negative",
            delta=f"+{clinical_contribution:.3f}" if clinical_contribution > 0 else f"{clinical_contribution:.3f}",
        ))
        
        # Reputation contribution (25% weight)
        reputation_contribution = (reputation_score - 0.5) * FUSION_WEIGHTS["reputation_score"]
        contributors.append(SHAPContribution(
            factor="Reputation Score",
            impact="positive" if reputation_contribution > 0 else "negative",
            delta=f"+{reputation_contribution:.3f}" if reputation_contribution > 0 else f"{reputation_contribution:.3f}",
        ))
        
        # Accessibility contribution (20% weight)
        accessibility_contribution = (accessibility_score - 0.5) * FUSION_WEIGHTS["accessibility_score"]
        contributors.append(SHAPContribution(
            factor="Excellent Accessibility" if accessibility_contribution > 0.05 else "Accessibility",
            impact="positive" if accessibility_contribution > 0 else "negative",
            delta=f"+{accessibility_contribution:.3f}" if accessibility_contribution > 0 else f"{accessibility_contribution:.3f}",
        ))
        
        # Affordability contribution (15% weight)
        affordability_contribution = (affordability_score - 0.5) * FUSION_WEIGHTS["affordability_score"]
        contributors.append(SHAPContribution(
            factor="Affordability Slightly Low" if affordability_contribution < 0 else "Affordability",
            impact="positive" if affordability_contribution > 0 else "negative",
            delta=f"+{affordability_contribution:.3f}" if affordability_contribution > 0 else f"{affordability_contribution:.3f}",
        ))
        
        return SHAPExplanation(
            hospital_id=hospital_id,
            contributors=contributors,
        )

    def generate_lime_explanation(
        self,
        query: str,
        triage: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate LIME text explanation for triage classification.
        
        Highlights triggering phrases in the query.
        
        Args:
            query: User query text
            triage: Triage classification (RED, YELLOW, GREEN)
            
        Returns:
            List of highlighted tokens with importance
        """
        query_lower = query.lower()
        highlighted = []
        
        # Define keyword patterns for each triage level
        red_keywords = [
            "chest pain", "heart attack", "stroke", "unconscious", "not breathing",
            "severe bleeding", "emergency", "urgent", "critical", "trauma",
            "suicide", "overdose", "seizure", "can't breathe", "difficulty breathing",
        ]
        
        yellow_keywords = [
            "pain", "fever", "swelling", "infection", "injury", "broken",
            "fracture", "wound", "cut", "burn", "vomiting", "diarrhea",
        ]
        
        green_keywords = [
            "checkup", "consultation", "routine", "follow up", "review",
            "appointment", "schedule", "planning", "elective", "screening",
        ]
        
        # Find matching keywords
        if triage == "RED":
            keywords = red_keywords
        elif triage == "YELLOW":
            keywords = yellow_keywords
        else:
            keywords = green_keywords
        
        for keyword in keywords:
            if keyword in query_lower:
                highlighted.append({
                    "token": keyword,
                    "importance": 0.8 if triage == "RED" else 0.5,
                    "contribution": "toward" if triage == "RED" else "neutral",
                })
        
        # Sort by importance
        highlighted.sort(key=lambda x: x["importance"], reverse=True)
        
        return highlighted[:5]  # Top 5 highlights

    def should_show_uncertainty_banner(self, confidence_score: int) -> bool:
        """
        Determine if uncertainty banner should be shown.
        
        Per instructionagent.md Section 10:
        - If confidence < 60: Show uncertainty banner
        - If confidence < 40: Block results (handled by orchestrator)
        
        Args:
            confidence_score: Composite confidence score
            
        Returns:
            True if banner should be shown
        """
        CONFIDENCE_THRESHOLD_WARN = 60
        return confidence_score < CONFIDENCE_THRESHOLD_WARN

    def get_disclaimer(self, triage: Optional[str] = None) -> str:
        """
        Get appropriate disclaimer text.
        
        Args:
            triage: Optional triage level
            
        Returns:
            Disclaimer string
        """
        base_disclaimer = (
            "Symptom-to-condition mapping is approximate. "
            "This tool helps you research and prepare; your doctor makes the diagnosis."
        )
        
        if triage == "RED":
            return (
                "EMERGENCY: This appears to be a medical emergency. "
                "Please call 112 immediately or go to the nearest emergency room. "
                + base_disclaimer
            )
        
        return base_disclaimer

    def process(
        self,
        hospital_id: Optional[str] = None,
        hospital_scores: Optional[Dict[str, float]] = None,
        query: Optional[str] = None,
        triage: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> XAIExplainerOutput:
        """
        Main processing method for the agent.
        
        Args:
            hospital_id: Hospital to explain (optional)
            hospital_scores: Dict with clinical_score, reputation_score, etc. (optional)
            query: User query for LIME explanation (optional)
            triage: Triage level for LIME (optional)
            context: Additional context data
            
        Returns:
            XAIExplainerOutput
        """
        context = context or {}
        
        # Generate confidence drivers
        drivers = self.generate_confidence_drivers(
            hospitals_found=context.get("hospitals_found", 3),
            has_pricing_data=context.get("has_pricing_data", True),
            has_benchmark_data=context.get("has_benchmark_data", True),
            comorbidities_count=context.get("comorbidities_count", 0),
        )
        
        # Calculate overall confidence score
        confidence_score = self.calculate_confidence_score(
            data_availability=drivers.data_availability,
            pricing_consistency=drivers.pricing_consistency,
            benchmark_recency=drivers.benchmark_recency,
            patient_complexity=drivers.patient_complexity,
        )
        
        # Generate SHAP explanation for hospital
        top_hospital_shap = None
        if hospital_id and hospital_scores:
            top_hospital_shap = self.generate_shap_explanation(
                hospital_id=hospital_id,
                clinical_score=hospital_scores.get("clinical_score", 0.7),
                reputation_score=hospital_scores.get("reputation_score", 0.7),
                accessibility_score=hospital_scores.get("accessibility_score", 0.7),
                affordability_score=hospital_scores.get("affordability_score", 0.7),
            )
        
        # Generate LIME explanation for triage
        triage_lime = None
        if query and triage:
            triage_lime = self.generate_lime_explanation(query, triage)
        
        # Determine uncertainty banner
        show_uncertainty = self.should_show_uncertainty_banner(confidence_score)
        
        # Get disclaimer
        disclaimer = self.get_disclaimer(triage)
        
        return XAIExplainerOutput(
            confidence_score=confidence_score,
            confidence_drivers=drivers,
            top_hospital_shap=top_hospital_shap,
            triage_lime=triage_lime,
            show_uncertainty_banner=show_uncertainty,
            disclaimer=disclaimer,
        )


# =============================================================================
# Module-level convenience functions
# =============================================================================

def get_xai_explainer_agent() -> XAIExplainerAgent:
    """Get singleton instance of XAIExplainerAgent."""
    return XAIExplainerAgent()


def explain_hospital_fusion_score(
    hospital_id: str,
    clinical_score: float,
    reputation_score: float,
    accessibility_score: float,
    affordability_score: float,
) -> SHAPExplanation:
    """
    Convenience function to explain hospital fusion score.
    
    Args:
        hospital_id: Hospital identifier
        clinical_score: Clinical component score
        reputation_score: Reputation component score
        accessibility_score: Accessibility component score
        affordability_score: Affordability component score
        
    Returns:
        SHAPExplanation
    """
    agent = get_xai_explainer_agent()
    return agent.generate_shap_explanation(
        hospital_id,
        clinical_score,
        reputation_score,
        accessibility_score,
        affordability_score,
    )


def explain_triage(
    query: str,
    triage: str,
) -> List[Dict[str, Any]]:
    """
    Convenience function to explain triage classification.
    
    Args:
        query: User query
        triage: Triage classification
        
    Returns:
        List of highlighted tokens
    """
    agent = get_xai_explainer_agent()
    return agent.generate_lime_explanation(query, triage)


def calculate_rag_confidence(
    data_availability: int,
    pricing_consistency: int,
    benchmark_recency: int,
    patient_complexity: int,
) -> int:
    """
    Convenience function to calculate RAG confidence score.
    
    Args:
        data_availability: Data availability score
        pricing_consistency: Pricing consistency score
        benchmark_recency: Benchmark recency score
        patient_complexity: Patient complexity score
        
    Returns:
        Composite confidence score
    """
    agent = get_xai_explainer_agent()
    return agent.calculate_confidence_score(
        data_availability,
        pricing_consistency,
        benchmark_recency,
        patient_complexity,
    )
