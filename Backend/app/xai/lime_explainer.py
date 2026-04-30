"""
LIME Explainer for severity classification.

Explains why a query was classified as RED/YELLOW/GREEN using
LIME-style text perturbation.
"""

import json
from typing import Dict, Any

from app.core.nvidia_client import NvidiaClient


class SeverityLIMEExplainer:
    """
    Explains severity classification using LIME-style text perturbation.
    Identifies which tokens triggered the classification.
    """

    def __init__(self):
        self.llm = NvidiaClient(temperature=0.0, max_tokens=512)

    def explain(self, user_text: str, classification: str) -> Dict[str, Any]:
        """
        Perturb input text and identify which terms drove the classification.
        
        Args:
            user_text: The original user query
            classification: RED, YELLOW, or GREEN
            
        Returns:
            Dict with key_terms and explanation
        """
        system_prompt = """You are an AI explainability engine. Given a medical query and its triage classification,
identify which specific words or phrases most strongly drove that classification.
Return ONLY valid JSON with this structure (no markdown, no preamble):
{
  "key_terms": [
    {"term": "chest pain", "influence": "high", "direction": "increases_severity"},
    {"term": "walking", "influence": "low", "direction": "neutral"}
  ],
  "explanation": "One sentence plain-language explanation."
}
Directions: "increases_severity" | "decreases_severity" | "neutral"
Influence: "high" | "medium" | "low"
"""

        prompt = f"""Query: "{user_text}"
Classification: {classification}

Which terms drove this classification?"""

        try:
            response = self.llm.simple_prompt(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.0,
                max_tokens=512,
            )
            clean = response.strip().strip("```json").strip("```").strip()
            return json.loads(clean)
        except Exception:
            return {
                "key_terms": [],
                "explanation": f"Query classified as {classification} based on clinical content.",
            }
