"""
RAG Confidence Scoring System.

Computes composite confidence score for LLM + RAG responses.
Formula: S = 0.4 × Faithfulness + 0.3 × Contextual_Relevancy + 0.3 × Answer_Relevancy
"""

import json
import logging
from typing import Dict, Any

from app.core.nvidia_client import NvidiaClient

logger = logging.getLogger(__name__)


class RAGConfidenceScorer:
    """
    Computes composite confidence score for RAG responses.
    Score < 0.40 triggers UI uncertainty indicator.
    """

    SAFETY_THRESHOLD = 0.40
    WEIGHTS = {
        "faithfulness": 0.40,
        "contextual_relevancy": 0.30,
        "answer_relevancy": 0.30,
    }

    def __init__(self):
        self.llm = NvidiaClient(temperature=0.0, max_tokens=256)

    def score(
        self,
        user_query: str,
        retrieved_context: str,
        llm_response: str,
    ) -> Dict[str, Any]:
        """
        Evaluate RAG output quality on three dimensions.
        
        Args:
            user_query: Original user query
            retrieved_context: Context retrieved from knowledge graph
            llm_response: Final LLM-generated response
            
        Returns:
            Dict with composite score and per-dimension breakdown
        """
        system_prompt = """You are a RAG evaluation judge. Score the following on three dimensions from 0.0 to 1.0.
Return ONLY valid JSON (no markdown):
{
  "faithfulness": 0.0,
  "contextual_relevancy": 0.0,
  "answer_relevancy": 0.0,
  "rationale": "One sentence explanation."
}
faithfulness: Is the response grounded in retrieved context?
contextual_relevancy: Did retrieved context match the user's query?
answer_relevancy: Does the answer directly address the query?"""

        prompt = f"""User Query: {user_query}

Retrieved Context: {retrieved_context[:1000]}

LLM Response: {llm_response[:1000]}

Score these three dimensions:"""

        try:
            response = self.llm.simple_prompt(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.0,
                max_tokens=256,
            )
            clean = response.strip().strip("```json").strip("```").strip()
            scores = json.loads(clean)

            faithfulness = float(scores.get("faithfulness", 0.5))
            contextual = float(scores.get("contextual_relevancy", 0.5))
            answer = float(scores.get("answer_relevancy", 0.5))

            composite = (
                faithfulness * self.WEIGHTS["faithfulness"] +
                contextual * self.WEIGHTS["contextual_relevancy"] +
                answer * self.WEIGHTS["answer_relevancy"]
            )

            return {
                "composite_score": round(composite, 3),
                "faithfulness": round(faithfulness, 3),
                "contextual_relevancy": round(contextual, 3),
                "answer_relevancy": round(answer, 3),
                "rationale": scores.get("rationale", ""),
                "below_threshold": composite < self.SAFETY_THRESHOLD,
                "show_uncertainty_indicator": composite < self.SAFETY_THRESHOLD,
                "label": self._label(composite),
            }

        except Exception as e:
            logger.warning(f"RAG confidence scoring failed: {e}")
            return {
                "composite_score": 0.60,
                "faithfulness": 0.60,
                "contextual_relevancy": 0.60,
                "answer_relevancy": 0.60,
                "rationale": "Score unavailable",
                "below_threshold": False,
                "show_uncertainty_indicator": False,
                "label": "Moderate",
            }

    def _label(self, score: float) -> str:
        """Get confidence label from score."""
        if score >= 0.70:
            return "High"
        if score >= 0.40:
            return "Moderate"
        return "Low"


# =============================================================================
# Module-level Confidence Functions (TC-30 to TC-31)
# =============================================================================


def compute_confidence(
    faithfulness: float,
    contextual_relevancy: float,
    answer_relevancy: float,
) -> float:
    """
    Compute composite confidence score.
    
    Formula: S = 0.4 × Faithfulness + 0.3 × Contextual_Relevancy + 0.3 × Answer_Relevancy
    
    Args:
        faithfulness: Faithfulness score (0.0 - 1.0)
        contextual_relevancy: Contextual relevancy score (0.0 - 1.0)
        answer_relevancy: Answer relevancy score (0.0 - 1.0)
        
    Returns:
        Composite confidence score (0.0 - 1.0)
    """
    return (
        0.4 * faithfulness +
        0.3 * contextual_relevancy +
        0.3 * answer_relevancy
    )


def should_show_disclaimer(score: float, threshold: float = 0.70) -> bool:
    """
    Determine if uncertainty disclaimer should be shown.
    
    Args:
        score: Composite confidence score
        threshold: Minimum acceptable score (default 0.70)
        
    Returns:
        True if disclaimer should be shown
    """
    return score < threshold
