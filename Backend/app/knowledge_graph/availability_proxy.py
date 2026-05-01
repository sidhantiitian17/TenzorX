"""
Appointment Availability Proxy - Queuing Theory Implementation.

Per instruction_KG.md Section 13:
Since real-time API scheduling data does not exist across the Indian hospital ecosystem,
the KG computes an Appointment Availability Proxy from structural data stored on graph nodes.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.knowledge_graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


@dataclass
class AvailabilityResult:
    """Result of availability proxy computation."""
    label: str
    score: float
    estimated_days: int
    has_emergency: bool


class AvailabilityProxy:
    """
    Computes appointment availability proxy using queuing theory principles.
    
    Based on:
    - Total beds available
    - Bed turnover rate
    - Specialist count per department
    - Emergency unit availability
    """
    
    def __init__(self, client: Neo4jClient):
        self.client = client
    
    def compute_availability(
        self, 
        hospital_id: str, 
        department: Optional[str] = None,
        is_emergency: bool = False
    ) -> AvailabilityResult:
        """
        Compute availability proxy for a hospital.
        
        Per instruction_KG.md Section 13.2:
        - throughput_index = (total_beds × bed_turnover_rate) / max(specialist_count, 1)
        - Classify based on throughput_index thresholds
        
        Args:
            hospital_id: Hospital identifier
            department: Target department (optional)
            is_emergency: Whether this is an emergency query
            
        Returns:
            AvailabilityResult with label, score, and estimated waiting time
        """
        # Get hospital data
        hospital_data = self._get_hospital_data(hospital_id)
        
        if not hospital_data:
            logger.warning(f"Hospital not found: {hospital_id}")
            return AvailabilityResult(
                label="Data unavailable",
                score=0.0,
                estimated_days=14,
                has_emergency=False
            )
        
        # Emergency override - if emergency unit exists and query is emergency
        if hospital_data.get("has_emergency_unit", False) and is_emergency:
            return AvailabilityResult(
                label="24/7 emergency available ✅",
                score=1.0,
                estimated_days=0,
                has_emergency=True
            )
        
        # Get specialist count (filtered by department if specified)
        specialist_count = self._get_specialist_count(hospital_id, department)
        
        # Compute throughput index
        total_beds = hospital_data.get("total_beds", 100)
        bed_turnover_rate = hospital_data.get("bed_turnover_rate", 2.0)
        
        throughput_index = (total_beds * bed_turnover_rate) / max(specialist_count, 1)
        
        logger.debug(f"Hospital {hospital_id}: throughput_index={throughput_index:.1f}")
        
        # Classify based on throughput_index thresholds
        # Per instruction_KG.md Section 13.2
        if throughput_index > 150:
            return AvailabilityResult(
                label="Appointments usually available within 2-3 days",
                score=0.9,
                estimated_days=3,
                has_emergency=hospital_data.get("has_emergency_unit", False)
            )
        elif throughput_index > 80:
            return AvailabilityResult(
                label="Estimated waiting time: 4-7 days",
                score=0.6,
                estimated_days=6,
                has_emergency=hospital_data.get("has_emergency_unit", False)
            )
        else:
            return AvailabilityResult(
                label="Waiting time: 1-2 weeks",
                score=0.3,
                estimated_days=10,
                has_emergency=hospital_data.get("has_emergency_unit", False)
            )
    
    def _get_hospital_data(self, hospital_id: str) -> Optional[Dict[str, Any]]:
        """Get hospital structural data for availability calculation."""
        result = self.client.run_query("""
            MATCH (h:Hospital {id: $hospital_id})
            RETURN h.total_beds AS total_beds,
                   h.bed_turnover_rate AS bed_turnover_rate,
                   h.has_emergency_unit AS has_emergency_unit
        """, {"hospital_id": hospital_id})
        
        return result[0] if result else None
    
    def _get_specialist_count(self, hospital_id: str, department: Optional[str] = None) -> int:
        """Get specialist count for a hospital, optionally filtered by department."""
        if department:
            result = self.client.run_query("""
                MATCH (h:Hospital {id: $hospital_id})-[:EMPLOYS]->(sp:Specialist)
                WHERE toLower(sp.department) = toLower($department)
                   OR toLower(sp.department) CONTAINS toLower($department)
                RETURN count(sp) AS specialist_count
            """, {
                "hospital_id": hospital_id,
                "department": department
            })
        else:
            result = self.client.run_query("""
                MATCH (h:Hospital {id: $hospital_id})-[:EMPLOYS]->(sp:Specialist)
                WHERE sp.active = true OR sp.active IS NULL
                RETURN count(sp) AS specialist_count
            """, {"hospital_id": hospital_id})
        
        return result[0]["specialist_count"] if result else 2  # Default to 2
    
    def compute_for_hospitals(
        self,
        hospital_ids: list,
        department: Optional[str] = None,
        is_emergency: bool = False
    ) -> Dict[str, AvailabilityResult]:
        """
        Compute availability for multiple hospitals.
        
        Args:
            hospital_ids: List of hospital IDs
            department: Target department (optional)
            is_emergency: Whether this is an emergency query
            
        Returns:
            Dict mapping hospital_id to AvailabilityResult
        """
        results = {}
        for hosp_id in hospital_ids:
            results[hosp_id] = self.compute_availability(
                hosp_id, department, is_emergency
            )
        return results


# Severity classification per instruction_KG.md Section 13.4
class SeverityClassifier:
    """Classifies symptom severity for emergency routing."""
    
    # Emergency keywords that trigger RED severity
    EMERGENCY_PATTERNS = {
        "RED": [
            ("chest pain", "left arm"),
            ("chest pain", "radiating"),
            ("difficulty breathing",),
            ("shortness of breath", "cyanosis"),
            ("unconscious",),
            ("severe bleeding",),
            ("stroke",),
            ("heart attack",),
            ("seizure", "prolonged"),
        ],
        "YELLOW": [
            ("fever", "more than 3 days"),
            ("fever", "joint pain"),
            ("severe pain",),
            ("persistent vomiting",),
            ("dehydration",),
        ]
    }
    
    @classmethod
    def classify(cls, symptoms: list, user_query: str) -> Dict[str, Any]:
        """
        Classify symptom severity based on keywords.
        
        Returns:
            Dict with severity (RED/YELLOW/GREEN) and reason
        """
        query_lower = user_query.lower()
        symptoms_lower = [s.lower() for s in symptoms]
        
        # Check RED patterns
        for pattern in cls.EMERGENCY_PATTERNS["RED"]:
            if all(p in query_lower or any(p in s for s in symptoms_lower) for p in pattern):
                return {
                    "severity": "RED",
                    "reason": f"Emergency keywords detected: {', '.join(pattern)}"
                }
        
        # Check YELLOW patterns
        for pattern in cls.EMERGENCY_PATTERNS["YELLOW"]:
            if all(p in query_lower or any(p in s for s in symptoms_lower) for p in pattern):
                return {
                    "severity": "YELLOW",
                    "reason": f"Urgent symptoms detected: {', '.join(pattern)}"
                }
        
        # Default to GREEN (elective)
        return {
            "severity": "GREEN",
            "reason": "Symptoms appear non-urgent. Schedule routine consultation."
        }
