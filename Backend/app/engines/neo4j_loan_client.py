"""
Neo4j Loan Client for NBFC Risk Band Integration.

Integrates loan eligibility engine with Neo4j NBFCRiskBand nodes.
Replaces hardcoded interest rates with graph-queried values.
"""

import logging
from typing import Dict, Any, Optional

from app.knowledge_graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class Neo4jLoanClient:
    """
    Client for querying NBFCRiskBand nodes from Neo4j graph.
    
    Per instructioncreate.md Section 6:
    - BAND_LOW: DTI 0-30%, 12-13% interest
    - BAND_MEDIUM: DTI 30-40%, 13-15% interest  
    - BAND_HIGH: DTI 40-50%, 15-16% interest
    - BAND_CRITICAL: DTI 50-100%, no loan
    """
    
    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        self.client = neo4j_client or Neo4jClient()
    
    def get_risk_band_by_dti(self, dti: float) -> Dict[str, Any]:
        """
        Query Neo4j for the NBFCRiskBand matching the given DTI ratio.
        
        Args:
            dti: Debt-to-Income ratio as percentage (0-100)
            
        Returns:
            Dict with risk band properties, or fallback if graph unavailable
        """
        try:
            cypher = """
            MATCH (b:NBFCRiskBand)
            WHERE b.dti_min <= $dti AND $dti < b.dti_max
            RETURN b.band_id AS band_id,
                   b.dti_min AS dti_min,
                   b.dti_max AS dti_max,
                   b.risk_flag AS risk_flag,
                   b.underwriting_label AS underwriting_label,
                   b.interest_rate_min AS interest_rate_min,
                   b.interest_rate_max AS interest_rate_max,
                   b.approval_likelihood AS approval_likelihood,
                   b.cta_text AS cta_text,
                   b.loan_coverage_pct AS loan_coverage_pct
            """
            results = self.client.run_query(cypher, {"dti": dti})
            
            if results:
                return results[0]
            else:
                logger.warning(f"No NBFCRiskBand found for DTI {dti}, using fallback")
                return self._fallback_band(dti)
                
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}, using fallback")
            return self._fallback_band(dti)
    
    def get_all_risk_bands(self) -> list[Dict[str, Any]]:
        """Query all NBFCRiskBand nodes from the graph."""
        try:
            cypher = """
            MATCH (b:NBFCRiskBand)
            RETURN b.band_id AS band_id,
                   b.dti_min AS dti_min,
                   b.dti_max AS dti_max,
                   b.risk_flag AS risk_flag,
                   b.underwriting_label AS underwriting_label,
                   b.interest_rate_min AS interest_rate_min,
                   b.interest_rate_max AS interest_rate_max,
                   b.approval_likelihood AS approval_likelihood,
                   b.cta_text AS cta_text,
                   b.loan_coverage_pct AS loan_coverage_pct
            ORDER BY b.dti_min
            """
            return self.client.run_query(cypher)
        except Exception as e:
            logger.error(f"Failed to query risk bands: {e}")
            return []
    
    def _fallback_band(self, dti: float) -> Dict[str, Any]:
        """
        Fallback band calculation when Neo4j is unavailable.
        Matches the hardcoded logic in loan_engine.py
        """
        if dti < 30:
            return {
                "band_id": "BAND_LOW",
                "dti_min": 0.0,
                "dti_max": 30.0,
                "risk_flag": "LOW",
                "underwriting_label": "Strong repayment capacity; very high approval likelihood",
                "interest_rate_min": 12.0,
                "interest_rate_max": 13.0,
                "approval_likelihood": "VERY HIGH",
                "cta_text": "Aap eligible hain — Apply Now",
                "loan_coverage_pct": 0.80
            }
        elif dti < 40:
            return {
                "band_id": "BAND_MEDIUM",
                "dti_min": 30.0,
                "dti_max": 40.0,
                "risk_flag": "MEDIUM",
                "underwriting_label": "Manageable debt load; conditional approval likely",
                "interest_rate_min": 13.0,
                "interest_rate_max": 15.0,
                "approval_likelihood": "LIKELY",
                "cta_text": "Proceed with Standard Application",
                "loan_coverage_pct": 0.80
            }
        elif dti < 50:
            return {
                "band_id": "BAND_HIGH",
                "dti_min": 40.0,
                "dti_max": 50.0,
                "risk_flag": "HIGH",
                "underwriting_label": "Strained capacity; requires manual review or co-applicant",
                "interest_rate_min": 15.0,
                "interest_rate_max": 16.0,
                "approval_likelihood": "MANUAL REVIEW",
                "cta_text": "Flag for Manual Review",
                "loan_coverage_pct": 0.70
            }
        else:
            return {
                "band_id": "BAND_CRITICAL",
                "dti_min": 50.0,
                "dti_max": 100.0,
                "risk_flag": "CRITICAL",
                "underwriting_label": "Overleveraged; loan approval unlikely without restructuring",
                "interest_rate_min": -1.0,
                "interest_rate_max": -1.0,
                "approval_likelihood": "UNLIKELY",
                "cta_text": "Recommend Alternate Financing",
                "loan_coverage_pct": 0.0
            }


# Module-level singleton for easy import
_default_loan_client: Optional[Neo4jLoanClient] = None


def get_loan_client() -> Neo4jLoanClient:
    """Get or create the default Neo4jLoanClient instance."""
    global _default_loan_client
    if _default_loan_client is None:
        _default_loan_client = Neo4jLoanClient()
    return _default_loan_client
