"""
Fusion Score Computation for Hospital Ranking.

Per instruction_KG.md Section 12:
Computes Multi-Source Data Fusion Score by aggregating four normalized sub-scores:
- Clinical Score (40%): procedure volume + accreditation
- Reputation Score (25%): VADER sentiment + star rating
- Accessibility Score (20%): geo-distance + availability proxy
- Affordability Score (15%): cashless success rate + pricing tier
"""

import logging
import math
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.knowledge_graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class FusionScorer:
    """Computes fusion scores for hospital ranking."""
    
    # Weights per instruction_KG.md Section 12.1
    WEIGHTS = {
        "clinical": 0.40,
        "reputation": 0.25,
        "accessibility": 0.20,
        "affordability": 0.15
    }
    
    def __init__(self, client: Neo4jClient):
        self.client = client
    
    def compute_all_hospital_scores(self):
        """Compute and store fusion scores for all hospitals."""
        logger.info("Starting batch fusion score computation...")
        
        # Get all hospitals
        hospitals = self.client.run_query("""
            MATCH (h:Hospital)
            RETURN h.id AS hospital_id, h.name AS name
        """)
        
        for hospital in hospitals:
            score = self.compute_hospital_score(hospital["hospital_id"])
            self._store_score(hospital["hospital_id"], score)
        
        logger.info(f"Computed fusion scores for {len(hospitals)} hospitals")
    
    def compute_hospital_score(self, hospital_id: str) -> Dict[str, Any]:
        """
        Compute fusion score for a single hospital.
        
        Returns dict with raw scores, normalized scores, and final weighted score.
        """
        # Get raw component scores
        clinical_raw = self._compute_clinical_score(hospital_id)
        reputation_raw = self._compute_reputation_score(hospital_id)
        accessibility_raw = self._compute_accessibility_score(hospital_id)
        affordability_raw = self._compute_affordability_score(hospital_id)
        
        # Get all scores for min-max normalization
        all_hospitals = self.client.run_query("""
            MATCH (h:Hospital)
            RETURN h.id AS id
        """)
        
        all_scores = {
            "clinical": [],
            "reputation": [],
            "accessibility": [],
            "affordability": []
        }
        
        for h in all_hospitals:
            if h["id"] != hospital_id:
                all_scores["clinical"].append(self._compute_clinical_score(h["id"]))
                all_scores["reputation"].append(self._compute_reputation_score(h["id"]))
                all_scores["accessibility"].append(self._compute_accessibility_score(h["id"]))
                all_scores["affordability"].append(self._compute_affordability_score(h["id"]))
        
        # Normalize scores
        clinical_norm = self._min_max_normalize(clinical_raw, all_scores["clinical"])
        reputation_norm = self._min_max_normalize(reputation_raw, all_scores["reputation"])
        accessibility_norm = self._min_max_normalize(accessibility_raw, all_scores["accessibility"])
        affordability_norm = self._min_max_normalize(affordability_raw, all_scores["affordability"])
        
        # Compute weighted final score
        final_score = (
            self.WEIGHTS["clinical"] * clinical_norm +
            self.WEIGHTS["reputation"] * reputation_norm +
            self.WEIGHTS["accessibility"] * accessibility_norm +
            self.WEIGHTS["affordability"] * affordability_norm
        )
        
        return {
            "final_score": round(final_score, 3),
            "clinical": {
                "raw": round(clinical_raw, 3),
                "normalized": round(clinical_norm, 3)
            },
            "reputation": {
                "raw": round(reputation_raw, 3),
                "normalized": round(reputation_norm, 3)
            },
            "accessibility": {
                "raw": round(accessibility_raw, 3),
                "normalized": round(accessibility_norm, 3)
            },
            "affordability": {
                "raw": round(affordability_raw, 3),
                "normalized": round(affordability_norm, 3)
            },
            "computed_at": datetime.now().isoformat()
        }
    
    def _compute_clinical_score(self, hospital_id: str) -> float:
        """
        Clinical Score (40% weight).
        
        Based on:
        - Procedure volume (60%)
        - NABH accreditation (30%)
        - JCI accreditation (10%)
        """
        result = self.client.run_query("""
            MATCH (h:Hospital {id: $hospital_id})-[:OFFERS_PROCEDURE]->(p:Procedure)
            RETURN COUNT(p) AS procedure_count,
                   h.nabh_accredited AS nabh,
                   h.jci_accredited AS jci
        """, {"hospital_id": hospital_id})
        
        if not result:
            return 0.0
        
        data = result[0]
        proc_count = data["procedure_count"]
        nabh = data["nabh"] or False
        jci = data["jci"] or False
        
        # Procedure count score (normalized to max 20 procedures = 1.0)
        proc_score = min(proc_count / 20.0, 1.0) * 0.6
        
        # Accreditation scores
        nabh_score = 0.3 if nabh else 0.0
        jci_score = 0.1 if jci else 0.0
        
        return proc_score + nabh_score + jci_score
    
    def _compute_reputation_score(self, hospital_id: str) -> float:
        """
        Reputation Score (25% weight).
        
        Based on:
        - Average VADER compound score (60%)
        - Overall star rating (40%)
        """
        result = self.client.run_query("""
            MATCH (h:Hospital {id: $hospital_id})-[:HAS_REVIEW_ASPECT]->(r:ReviewAspect)
            RETURN AVG(r.vader_compound_score) AS avg_vader,
                   h.overall_star_rating AS stars
        """, {"hospital_id": hospital_id})
        
        if not result:
            return 0.0
        
        data = result[0]
        avg_vader = data["avg_vader"] or 0.0
        stars = data["stars"] or 3.0
        
        # VADER score normalized from [-1, 1] to [0, 1]
        vader_norm = (avg_vader + 1) / 2
        vader_score = vader_norm * 0.6
        
        # Star rating normalized from [0, 5] to [0, 1]
        stars_norm = stars / 5.0
        stars_score = stars_norm * 0.4
        
        return vader_score + stars_score
    
    def _compute_accessibility_score(self, hospital_id: str) -> float:
        """
        Accessibility Score (20% weight).
        
        Based on:
        - Bed turnover rate (proxy for capacity)
        - Total beds
        - Specialist count
        - Emergency unit availability
        
        Note: Geographic distance is computed at query time, not stored.
        """
        result = self.client.run_query("""
            MATCH (h:Hospital {id: $hospital_id})
            RETURN h.total_beds AS beds,
                   h.bed_turnover_rate AS turnover,
                   h.specialists_count AS specialists,
                   h.has_emergency_unit AS emergency
        """, {"hospital_id": hospital_id})
        
        if not result:
            return 0.0
        
        data = result[0]
        beds = data["beds"] or 100
        turnover = data["turnover"] or 2.0
        specialists = data["specialists"] or 2
        emergency = data["emergency"] or False
        
        # Throughput index per instruction_KG.md Section 13.2
        throughput_index = (beds * turnover) / max(specialists, 1)
        
        # Normalize throughput (150+ = best)
        throughput_score = min(throughput_index / 150.0, 1.0) * 0.7
        
        # Emergency unit bonus
        emergency_score = 0.3 if emergency else 0.0
        
        return throughput_score + emergency_score
    
    def _compute_affordability_score(self, hospital_id: str) -> float:
        """
        Affordability Score (15% weight).
        
        Based on:
        - Average cashless success rate (60%)
        - Pricing tier (40%)
        
        Pricing tier mapping: Budget=1.0, Mid-tier=0.7, Premium=0.4
        """
        result = self.client.run_query("""
            MATCH (h:Hospital {id: $hospital_id})-[:COVERED_BY]->(i:InsuranceTier)
            RETURN AVG(i.cashless_success_rate) AS avg_cashless,
                   h.tier AS pricing_tier
        """, {"hospital_id": hospital_id})
        
        if not result:
            return 0.0
        
        data = result[0]
        avg_cashless = data["avg_cashless"] or 0.8
        tier = data["pricing_tier"] or "mid"
        
        # Cashless success score
        cashless_score = avg_cashless * 0.6
        
        # Pricing tier score
        tier_scores = {
            "budget": 1.0,
            "mid": 0.7,
            "mid-tier": 0.7,
            "premium": 0.4
        }
        tier_score = tier_scores.get(tier.lower(), 0.5) * 0.4
        
        return cashless_score + tier_score
    
    def _min_max_normalize(self, value: float, all_values: List[float]) -> float:
        """Min-max normalize a value against a list of values to [0, 1]."""
        if not all_values:
            return 0.5
        
        min_val = min(all_values)
        max_val = max(all_values)
        
        if max_val == min_val:
            return 0.5
        
        return (value - min_val) / (max_val - min_val)
    
    def _store_score(self, hospital_id: str, score: Dict[str, Any]):
        """Store computed fusion score on Hospital node."""
        self.client.run_query("""
            MATCH (h:Hospital {id: $hospital_id})
            SET h.fusion_score = $final_score,
                h.fusion_clinical = $clinical,
                h.fusion_reputation = $reputation,
                h.fusion_accessibility = $accessibility,
                h.fusion_affordability = $affordability,
                h.score_updated_at = datetime()
        """, {
            "hospital_id": hospital_id,
            "final_score": score["final_score"],
            "clinical": score["clinical"]["normalized"],
            "reputation": score["reputation"]["normalized"],
            "accessibility": score["accessibility"]["normalized"],
            "affordability": score["affordability"]["normalized"]
        })
