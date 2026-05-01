"""
Data Validation & Integrity Checks for Knowledge Graph.

Per instructioncreate.md Section 18:
Run these after all seed data is loaded to verify graph integrity.
"""

import logging
from typing import Dict, List, Any, Tuple
from app.knowledge_graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class GraphValidator:
    """
    Validates the knowledge graph structure and data integrity.
    
    Implements all checks from instructioncreate.md Section 18.
    """
    
    def __init__(self, client: Neo4jClient = None):
        self.client = client or Neo4jClient()
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all validation checks and return summary.
        
        Returns:
            Dict with check results and overall status
        """
        checks = {
            "diseases_have_procedures": self.check_diseases_have_procedures(),
            "procedures_have_phases": self.check_procedures_have_phases(),
            "phases_have_costs": self.check_phases_have_costs(),
            "hospitals_have_fusion_scores": self.check_hospitals_have_fusion_scores(),
            "cities_linked_to_tiers": self.check_cities_linked_to_tiers(),
            "symptoms_map_to_diseases": self.check_symptoms_map_to_diseases(),
            "nbfc_bands_contiguous": self.check_nbfc_bands_contiguous(),
            "graph_connectivity": self.check_graph_connectivity(),
        }
        
        # Overall status: pass if all checks pass
        all_passed = all(check["passed"] for check in checks.values())
        
        return {
            "all_passed": all_passed,
            "checks": checks,
            "summary": self._generate_summary(checks)
        }
    
    def check_diseases_have_procedures(self) -> Dict[str, Any]:
        """
        Check 1: All Diseases have at least one linked Procedure.
        
        Per instructioncreate.md Section 18, Check 1.
        """
        result = self.client.run_query("""
            MATCH (d:Disease)
            WHERE NOT (d)-[:REQUIRES_PROCEDURE|REQUIRES_WORKUP|TREATED_BY]->(:Procedure)
            RETURN d.icd10_code as code, d.name as name
        """)
        
        passed = len(result) == 0
        return {
            "name": "Diseases have Procedures",
            "passed": passed,
            "count": len(result),
            "issues": result[:5]  # First 5 issues only
        }
    
    def check_procedures_have_phases(self) -> Dict[str, Any]:
        """
        Check 2: All Procedures have complete 4-phase pathways.
        
        Per instructioncreate.md Section 18, Check 2.
        """
        result = self.client.run_query("""
            MATCH (p:Procedure)
            WITH p, size((p)-[:HAS_PHASE]->()) AS phase_count
            WHERE phase_count < 4
            RETURN p.name as procedure, phase_count
        """)
        
        passed = len(result) == 0
        return {
            "name": "Procedures have 4-phase pathways",
            "passed": passed,
            "count": len(result),
            "issues": result[:5]
        }
    
    def check_phases_have_costs(self) -> Dict[str, Any]:
        """
        Check 3: All Phases have at least one CostComponent.
        
        Per instructioncreate.md Section 18, Check 3.
        """
        result = self.client.run_query("""
            MATCH (ph:PathwayPhase)
            WHERE NOT (ph)-[:HAS_COST_COMPONENT]->(:CostComponent)
            RETURN ph.phase_id as phase_id, ph.phase_name as name
        """)
        
        passed = len(result) == 0
        return {
            "name": "Phases have Cost Components",
            "passed": passed,
            "count": len(result),
            "issues": result[:5]
        }
    
    def check_hospitals_have_fusion_scores(self) -> Dict[str, Any]:
        """
        Check 4: All Hospitals have computed fusion scores.
        
        Per instructioncreate.md Section 18, Check 4.
        """
        result = self.client.run_query("""
            MATCH (h:Hospital)
            WHERE h.fusion_score = 0.0 OR h.fusion_score IS NULL
            RETURN h.name as name, h.id as id
        """)
        
        passed = len(result) == 0
        return {
            "name": "Hospitals have Fusion Scores",
            "passed": passed,
            "count": len(result),
            "issues": result[:5]
        }
    
    def check_cities_linked_to_tiers(self) -> Dict[str, Any]:
        """
        Check 5: All Cities linked to a GeographicTier.
        
        Per instructioncreate.md Section 18, Check 5.
        """
        result = self.client.run_query("""
            MATCH (c:City)
            WHERE NOT (c)-[:CITY_BELONGS_TO]->(:GeographicTier)
            RETURN c.name as unlinked_city
        """)
        
        passed = len(result) == 0
        return {
            "name": "Cities linked to GeographicTier",
            "passed": passed,
            "count": len(result),
            "issues": result[:5]
        }
    
    def check_symptoms_map_to_diseases(self) -> Dict[str, Any]:
        """
        Check 6: All Symptoms map to at least one Disease.
        
        Per instructioncreate.md Section 18, Check 6.
        """
        result = self.client.run_query("""
            MATCH (s:Symptom)
            WHERE NOT (s)-[:INDICATES]->(:Disease)
            RETURN s.name as orphan_symptom
        """)
        
        passed = len(result) == 0
        return {
            "name": "Symptoms map to Diseases",
            "passed": passed,
            "count": len(result),
            "issues": result[:5]
        }
    
    def check_nbfc_bands_contiguous(self) -> Dict[str, Any]:
        """
        Check 7: NBFCRiskBand DTI ranges are contiguous.
        
        Per instructioncreate.md Section 18, Check 7.
        """
        result = self.client.run_query("""
            MATCH (b:NBFCRiskBand)
            RETURN b.band_id as band_id, b.dti_min as dti_min, b.dti_max as dti_max
            ORDER BY b.dti_min
        """)
        
        # Check that ranges are contiguous (min of next = max of current)
        issues = []
        for i in range(len(result) - 1):
            current_max = result[i]["dti_max"]
            next_min = result[i + 1]["dti_min"]
            if current_max != next_min:
                issues.append({
                    "band": result[i]["band_id"],
                    "next_band": result[i + 1]["band_id"],
                    "gap": f"{current_max} != {next_min}"
                })
        
        passed = len(issues) == 0 and len(result) == 4
        return {
            "name": "NBFCRiskBand DTI ranges contiguous",
            "passed": passed,
            "count": len(issues),
            "issues": issues,
            "bands": result
        }
    
    def check_graph_connectivity(self) -> Dict[str, Any]:
        """
        Check 8: Graph connectivity summary.
        
        Per instructioncreate.md Section 18, Check 8.
        """
        nodes = self.client.run_query("""
            MATCH (n)
            RETURN labels(n)[0] AS label, count(n) AS node_count
            ORDER BY node_count DESC
        """)
        
        relationships = self.client.run_query("""
            MATCH ()-[r]->()
            RETURN type(r) AS relationship, count(r) AS count
            ORDER BY count DESC
        """)
        
        total_nodes = sum(n["node_count"] for n in nodes)
        total_relationships = sum(r["count"] for r in relationships)
        
        # Minimum thresholds per plan acceptance criteria
        min_nodes = 100
        min_relationships = 200
        
        passed = total_nodes >= min_nodes and total_relationships >= min_relationships
        
        return {
            "name": "Graph Connectivity Summary",
            "passed": passed,
            "total_nodes": total_nodes,
            "total_relationships": total_relationships,
            "node_breakdown": nodes,
            "relationship_breakdown": relationships[:10],  # Top 10
            "issues": []
        }
    
    def _generate_summary(self, checks: Dict[str, Any]) -> str:
        """Generate a human-readable summary of check results."""
        passed = sum(1 for c in checks.values() if c["passed"])
        total = len(checks)
        
        lines = [
            f"Validation Summary: {passed}/{total} checks passed",
            ""
        ]
        
        for name, check in checks.items():
            status = "✓" if check["passed"] else "✗"
            lines.append(f"{status} {check['name']}: {check.get('count', 0)} issues")
        
        return "\n".join(lines)


def run_validation() -> bool:
    """
    Run all validation checks and log results.
    
    Returns:
        True if all checks passed, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("Running Knowledge Graph Validation Checks")
    logger.info("=" * 60)
    
    validator = GraphValidator()
    results = validator.run_all_checks()
    
    logger.info("\n" + results["summary"])
    
    if results["all_passed"]:
        logger.info("\n✓ All validation checks passed!")
    else:
        logger.warning("\n✗ Some validation checks failed. See details above.")
        
        # Log failed check details
        for name, check in results["checks"].items():
            if not check["passed"] and check.get("issues"):
                logger.warning(f"\n{name} issues:")
                for issue in check["issues"][:3]:
                    logger.warning(f"  - {issue}")
    
    logger.info("=" * 60)
    return results["all_passed"]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_validation()
    exit(0 if success else 1)
