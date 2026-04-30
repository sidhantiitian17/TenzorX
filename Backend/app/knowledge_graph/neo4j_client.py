"""
Neo4j Graph Database Client.

Provides connectivity and query execution for the medical knowledge graph.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Neo4j client for knowledge graph operations.
    Manages connection pooling and Cypher query execution.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
        )
        logger.info(f"Neo4j client initialized: {self.uri}")

    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()
        logger.info("Neo4j connection closed")

    def run_query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results as a list of dictionaries.
        
        Args:
            cypher: The Cypher query string
            params: Query parameters
            
        Returns:
            List of record dictionaries
        """
        params = params or {}
        with self.driver.session() as session:
            result = session.run(cypher, **params)
            return [dict(record) for record in result]

    def find_conditions_for_symptoms(self, symptom_names: List[str]) -> List[Dict[str, Any]]:
        """
        Traverse symptom -> condition edges.
        
        Args:
            symptom_names: List of symptom names to match
            
        Returns:
            List of conditions ordered by symptom match count
        """
        cypher = """
        MATCH (s:Symptom)-[:INDICATES]->(c:Condition)
        WHERE toLower(s.name) IN $symptom_names
        RETURN c.icd10_code AS icd10_code,
               c.icd10_label AS icd10_label,
               c.snomed_code AS snomed_code,
               c.category AS category,
               count(s) AS symptom_match_count
        ORDER BY symptom_match_count DESC
        LIMIT 5
        """
        return self.run_query(cypher, {"symptom_names": [s.lower() for s in symptom_names]})

    def find_procedures_for_condition(self, icd10_code: str) -> List[Dict[str, Any]]:
        """
        Traverse condition -> procedure edges.
        
        Args:
            icd10_code: ICD-10 code of the condition
            
        Returns:
            List of procedures that treat the condition
        """
        cypher = """
        MATCH (c:Condition {icd10_code: $icd10_code})-[:TREATED_BY]->(p:Procedure)
        RETURN p.name AS procedure_name,
               p.icd10_code AS icd10_code,
               p.typical_duration_hrs AS duration_hrs,
               p.hospital_stay_days AS stay_days
        """
        return self.run_query(cypher, {"icd10_code": icd10_code})

    def find_hospitals_for_procedure_in_city(
        self, 
        procedure_name: str, 
        city: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find hospitals that perform a procedure in a given city.
        
        Args:
            procedure_name: Name of the procedure
            city: City name
            limit: Maximum number of results
            
        Returns:
            List of hospitals with their properties
        """
        cypher = """
        MATCH (p:Procedure {name: $procedure_name})<-[:PERFORMED_AT]-(h:Hospital)-[:LOCATED_IN]->(ci:City)
        WHERE toLower(ci.name) = toLower($city)
        RETURN h.id AS id,
               h.name AS name,
               h.tier AS tier,
               h.nabh AS nabh_accredited,
               h.rating AS rating,
               h.bed_count AS bed_count,
               h.lat AS lat,
               h.lon AS lon,
               ci.geo_multiplier AS geo_multiplier
        ORDER BY h.rating DESC
        LIMIT $limit
        """
        return self.run_query(cypher, {
            "procedure_name": procedure_name,
            "city": city,
            "limit": limit
        })

    def get_cost_benchmark(self, procedure_name: str, city_tier: str) -> Dict[str, Any]:
        """
        Retrieve cost benchmarks for a procedure in a city tier.
        
        Args:
            procedure_name: Name of the procedure
            city_tier: City tier (metro, tier2, tier3)
            
        Returns:
            Cost benchmark dictionary or empty dict if not found
        """
        cypher = """
        MATCH (cb:CostBenchmark)-[:BENCHMARKS]->(p:Procedure {name: $procedure_name})
        WHERE cb.city_tier = $city_tier
        RETURN cb.min_inr AS min_inr,
               cb.max_inr AS max_inr,
               cb.typical_inr AS typical_inr,
               cb.breakdown AS breakdown
        LIMIT 1
        """
        results = self.run_query(cypher, {
            "procedure_name": procedure_name,
            "city_tier": city_tier
        })
        return results[0] if results else {}

    def get_hospital_by_id(self, hospital_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific hospital.
        
        Args:
            hospital_id: Unique hospital identifier
            
        Returns:
            Hospital details or None if not found
        """
        cypher = """
        MATCH (h:Hospital {id: $hospital_id})-[:LOCATED_IN]->(c:City)
        OPTIONAL MATCH (h)<-[:PRACTICES_AT]-(d:Doctor)
        RETURN h.id AS id,
               h.name AS name,
               h.tier AS tier,
               h.nabh AS nabh_accredited,
               h.rating AS rating,
               h.bed_count AS bed_count,
               h.lat AS lat,
               h.lon AS lon,
               c.name AS city,
               c.tier AS city_tier,
               collect(d {.*}) AS doctors
        """
        results = self.run_query(cypher, {"hospital_id": hospital_id})
        return results[0] if results else None
