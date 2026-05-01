"""
Neo4j Graph Database Client.

Provides connectivity and query execution for the medical knowledge graph.
Implements queries per instruction_KG.md for GraphRAG hybrid architecture.
"""

import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Neo4j client for knowledge graph operations.
    Manages connection pooling and Cypher query execution.
    Implements the GraphRAG architecture from instruction_KG.md.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.uri = uri or settings.NEO4J_URI
        self.user = user or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD
        self.driver = None
        self._disabled = False
        
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )
            # Test connection
            self.driver.verify_connectivity()
            logger.info(f"Neo4j client initialized: {self.uri}")
        except Exception as e:
            logger.warning(f"Neo4j connection failed (graph features disabled): {e}")
            self._disabled = True

    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
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
            
        Raises:
            RuntimeError: If Neo4j is disabled or not connected
        """
        if self._disabled or self.driver is None:
            raise RuntimeError("Neo4j is not available - graph queries disabled")
        
        params = params or {}
        with self.driver.session() as session:
            result = session.run(cypher, **params)
            return [dict(record) for record in result]

    def find_diseases_for_symptoms(self, symptom_names: List[str]) -> List[Dict[str, Any]]:
        """
        Traverse symptom -> disease edges per instruction_KG.md Section 9.
        
        Args:
            symptom_names: List of symptom names to match
            
        Returns:
            List of diseases ordered by symptom match count
        """
        cypher = """
        MATCH (s:Symptom)-[:INDICATES]->(d:Disease)
        WHERE toLower(s.name) IN $symptom_names
        RETURN d.icd10_code AS icd10_code,
               d.name AS name,
               d.icd10_description AS icd10_description,
               d.category AS category,
               count(s) AS symptom_match_count
        ORDER BY symptom_match_count DESC
        LIMIT 5
        """
        return self.run_query(cypher, {"symptom_names": [s.lower() for s in symptom_names]})

    def find_procedures_for_disease(self, icd10_code: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Traverse disease -> procedure edges per instruction_KG.md Section 9.
        Returns both diagnostic (REQUIRES_WORKUP) and treatment (TREATED_BY) procedures.
        
        Args:
            icd10_code: ICD-10 code of the disease
            
        Returns:
            Dict with 'diagnostic' and 'treatment' procedure lists
        """
        # Get diagnostic procedures
        diagnostic_cypher = """
        MATCH (d:Disease {icd10_code: $icd10_code})-[:REQUIRES_WORKUP]->(p:Procedure)
        RETURN p.name AS procedure_name,
               p.procedure_code AS procedure_code,
               p.icd10_code AS icd10_code,
               p.type AS procedure_type,
               p.typical_cost_inr AS typical_cost
        ORDER BY p.name
        """
        diagnostic = self.run_query(diagnostic_cypher, {"icd10_code": icd10_code})
        
        # Get treatment procedures
        treatment_cypher = """
        MATCH (d:Disease {icd10_code: $icd10_code})-[:TREATED_BY]->(p:Procedure)
        RETURN p.name AS procedure_name,
               p.procedure_code AS procedure_code,
               p.icd10_code AS icd10_code,
               p.type AS procedure_type,
               p.requires_icu AS requires_icu
        ORDER BY p.name
        """
        treatment = self.run_query(treatment_cypher, {"icd10_code": icd10_code})
        
        return {
            "diagnostic": diagnostic,
            "treatment": treatment
        }

    def get_clinical_pathway(self, disease_icd10: str) -> Dict[str, Any]:
        """
        Get full clinical pathway for a disease per instruction_KG.md Section 9.
        
        Returns ordered pathway from diagnostic → treatment procedures
        with phase-based cost breakdowns.
        
        Args:
            disease_icd10: ICD-10 code of the disease
            
        Returns:
            Clinical pathway dict with procedures and costs
        """
        cypher = """
        MATCH (d:Disease {icd10_code: $disease_icd10})
        OPTIONAL MATCH (d)-[:REQUIRES_WORKUP]->(diag:Procedure)
        OPTIONAL MATCH (d)-[:TREATED_BY]->(tx:Procedure)
        OPTIONAL MATCH path = (diag)-[:PRECEDES*0..5]->(tx)
        WITH d, diag, tx, 
             CASE WHEN path IS NOT NULL THEN nodes(path) ELSE [diag, tx] END AS path_nodes
        RETURN d.icd10_code AS disease_code,
               d.name AS disease_name,
               d.icd10_description AS disease_description,
               collect(DISTINCT diag.name) AS diagnostic_procedures,
               collect(DISTINCT tx.name) AS treatment_procedures,
               collect(DISTINCT [n IN path_nodes | n.name]) AS procedure_sequences
        """
        return self.run_query(cypher, {"disease_icd10": disease_icd10})

    # Legacy method for backward compatibility
    def find_conditions_for_symptoms(self, symptom_names: List[str]) -> List[Dict[str, Any]]:
        """Legacy alias for find_diseases_for_symptoms."""
        return self.find_diseases_for_symptoms(symptom_names)

    # Legacy method for backward compatibility  
    def find_procedures_for_condition(self, icd10_code: str) -> List[Dict[str, Any]]:
        """Legacy alias returning treatment procedures only."""
        result = self.find_procedures_for_disease(icd10_code)
        return result.get("treatment", [])

    def find_hospitals_for_procedure_in_city(
        self, 
        procedure_name: str, 
        city: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find hospitals that offer a procedure in a given city.
        Per instruction_KG.md Section 9 and 12.
        
        Args:
            procedure_name: Name of the procedure
            city: City name
            limit: Maximum number of results
            
        Returns:
            List of hospitals with fusion scores and properties
        """
        cypher = """
        MATCH (p:Procedure {name: $procedure_name})<-[:OFFERS_PROCEDURE]-(h:Hospital)-[:LOCATED_IN]->(g:Geography)
        WHERE toLower(g.city_name) = toLower($city)
        OPTIONAL MATCH (h)-[:HAS_REVIEW_ASPECT]->(r:ReviewAspect {aspect: "doctors"})
        RETURN h.id AS id,
               h.name AS name,
               h.tier AS tier,
               h.nabh_accredited AS nabh_accredited,
               h.jci_accredited AS jci_accredited,
               h.rating AS rating,
               h.overall_star_rating AS overall_star_rating,
               h.fusion_score AS fusion_score,
               h.bed_count AS bed_count,
               h.has_emergency_unit AS has_emergency,
               h.lat AS lat,
               h.lon AS lon,
               g.city_name AS city,
               g.city_tier AS city_tier,
               g.geo_adjustment_factor AS geo_multiplier,
               r.vader_compound_score AS doctor_rating
        ORDER BY h.fusion_score DESC, h.rating DESC
        LIMIT $limit
        """
        return self.run_query(cypher, {
            "procedure_name": procedure_name,
            "city": city,
            "limit": limit
        })

    def get_geographic_multiplier(self, city_name: str) -> Dict[str, Any]:
        """
        Get geographic cost multiplier (γ_geo) for a city.
        Per instruction_KG.md Section 10.
        
        Args:
            city_name: City name
            
        Returns:
            Dict with geo_adjustment_factor and ICU rate
        """
        cypher = """
        MATCH (g:Geography {city_name: $city_name})
        RETURN g.city_name AS city,
               g.city_tier AS tier,
               g.geo_adjustment_factor AS gamma_geo,
               g.icu_daily_rate_inr AS icu_rate
        """
        results = self.run_query(cypher, {"city_name": city_name})
        return results[0] if results else {"gamma_geo": 1.0, "icu_rate": 5534}

    def get_comorbidity_multipliers(
        self, 
        procedure_name: str, 
        comorbidity_names: List[str]
    ) -> Dict[str, Any]:
        """
        Get comorbidity cost multipliers (ω_i) for a procedure.
        Per instruction_KG.md Section 11.
        
        Formula: Σ ω_i × C_i where C_i = 1 if comorbidity declared
        
        Args:
            procedure_name: Name of the procedure
            comorbidity_names: List of declared comorbidity condition names
            
        Returns:
            Dict with total_omega and individual weights
        """
        cypher = """
        MATCH (c:Comorbidity)-[:ELEVATES_COST_FOR]->(p:Procedure {name: $procedure_name})
        WHERE c.condition_name IN $comorbidity_names
        RETURN c.condition_name AS condition,
               c.cost_multiplier_weight AS omega_i,
               c.icd10_code AS icd10
        """
        weights = self.run_query(cypher, {
            "procedure_name": procedure_name,
            "comorbidity_names": comorbidity_names
        })
        
        total_omega = sum(w["omega_i"] for w in weights)
        
        return {
            "total_omega": total_omega,
            "individual_weights": weights,
            "multiplier": 1 + total_omega
        }

    def get_cost_breakdown(self, procedure_name: str) -> List[Dict[str, Any]]:
        """
        Get phase-based cost breakdown for a procedure.
        Per instruction_KG.md Section 9.2.
        
        Phases: pre_procedure, procedure, hospital_stay, post_procedure
        
        Args:
            procedure_name: Name of the procedure
            
        Returns:
            List of cost components by phase
        """
        cypher = """
        MATCH (p:Procedure {name: $procedure_name})-[:HAS_COST_COMPONENT]->(cc:CostComponent)
        RETURN cc.phase AS phase,
               cc.description AS description,
               cc.base_cost_min_inr AS cost_min,
               cc.base_cost_max_inr AS cost_max,
               cc.typical_days AS typical_days
        ORDER BY CASE cc.phase
            WHEN 'pre_procedure' THEN 1
            WHEN 'procedure' THEN 2
            WHEN 'hospital_stay' THEN 3
            WHEN 'post_procedure' THEN 4
            ELSE 5
        END
        """
        return self.run_query(cypher, {"procedure_name": procedure_name})

    def apply_cost_adjustments(
        self,
        base_cost_min: float,
        base_cost_max: float,
        city_name: str,
        comorbidity_names: List[str],
        patient_age: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Apply all cost adjustments per instruction_KG.md Sections 10-11.
        
        Formula:
        - Adjusted_Cost = Base × γ_geo
        - Final_Estimated_Cost = Adjusted × (1 + Σ ω_i + ω_age if age > 65)
        
        Args:
            base_cost_min: Base minimum cost
            base_cost_max: Base maximum cost
            city_name: Patient's city for geographic multiplier
            comorbidity_names: List of declared comorbidities
            patient_age: Patient age (adds 0.15 if > 65)
            
        Returns:
            Dict with adjusted and final costs
        """
        # Get geographic multiplier
        geo = self.get_geographic_multiplier(city_name)
        gamma_geo = geo.get("gamma_geo", 1.0)
        
        # Apply geographic adjustment
        adjusted_min = base_cost_min * gamma_geo
        adjusted_max = base_cost_max * gamma_geo
        
        # Get comorbidity multipliers
        comorb_data = {"total_omega": 0.0}
        if comorbidity_names:
            # Find the main procedure from context (simplified)
            comorb_data = self.get_comorbidity_multipliers(
                "Angioplasty",  # Default, should be passed from context
                comorbidity_names
            )
        
        total_omega = comorb_data.get("total_omega", 0.0)
        
        # Add age adjustment if applicable
        age_weight = 0.15 if patient_age and patient_age > 65 else 0.0
        
        # Calculate final multiplier
        final_multiplier = 1 + total_omega + age_weight
        
        # Calculate final costs
        final_min = adjusted_min * final_multiplier
        final_max = adjusted_max * final_multiplier
        
        return {
            "base_cost_min": base_cost_min,
            "base_cost_max": base_cost_max,
            "geo_multiplier": gamma_geo,
            "adjusted_min": round(adjusted_min, 2),
            "adjusted_max": round(adjusted_max, 2),
            "comorbidity_weight": total_omega,
            "age_weight": age_weight,
            "final_multiplier": round(final_multiplier, 3),
            "final_cost_min": round(final_min, 2),
            "final_cost_max": round(final_max, 2),
            "contingency_pct": round((final_multiplier - 1) * 100, 1)
        }

    def get_cost_benchmark(self, procedure_name: str, city_tier: str) -> Dict[str, Any]:
        """
        Retrieve cost benchmarks for a procedure in a city tier.
        Legacy method - use get_cost_breakdown for full phase-based costs.
        
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
               cb.typical_inr AS typical_inr
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
        Includes specialists, review aspects, and insurance coverage.
        
        Args:
            hospital_id: Unique hospital identifier
            
        Returns:
            Hospital details or None if not found
        """
        cypher = """
        MATCH (h:Hospital {id: $hospital_id})-[:LOCATED_IN]->(g:Geography)
        OPTIONAL MATCH (h)-[:EMPLOYS]->(sp:Specialist)
        OPTIONAL MATCH (h)-[:HAS_REVIEW_ASPECT]->(r:ReviewAspect)
        OPTIONAL MATCH (h)-[:COVERED_BY]->(i:InsuranceTier)
        OPTIONAL MATCH (h)-[:OFFERS_PROCEDURE]->(p:Procedure)
        RETURN h.id AS id,
               h.name AS name,
               h.tier AS tier,
               h.nabh_accredited AS nabh_accredited,
               h.jci_accredited AS jci_accredited,
               h.rating AS rating,
               h.overall_star_rating AS overall_star_rating,
               h.fusion_score AS fusion_score,
               h.bed_count AS bed_count,
               h.total_beds AS total_beds,
               h.bed_turnover_rate AS bed_turnover_rate,
               h.lat AS lat,
               h.lon AS lon,
               h.has_emergency_unit AS has_emergency,
               h.has_icu AS has_icu,
               g.city_name AS city,
               g.city_tier AS city_tier,
               g.geo_adjustment_factor AS geo_multiplier,
               collect(DISTINCT sp {.*}) AS specialists,
               collect(DISTINCT r {.*}) AS review_aspects,
               collect(DISTINCT i {.*}) AS insurance_tiers,
               collect(DISTINCT p.name) AS procedures
        """
        results = self.run_query(cypher, {"hospital_id": hospital_id})
        return results[0] if results else None

    def get_hospitals_with_fusion_score(
        self,
        procedure_name: Optional[str] = None,
        city_name: Optional[str] = None,
        min_score: float = 0.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get hospitals ranked by fusion score.
        Per instruction_KG.md Section 12.
        
        Args:
            procedure_name: Filter by procedure (optional)
            city_name: Filter by city (optional)
            min_score: Minimum fusion score threshold
            limit: Maximum results
            
        Returns:
            List of hospitals ordered by fusion score
        """
        cypher = """
        MATCH (h:Hospital)
        WHERE h.fusion_score >= $min_score
        """
        
        params = {"min_score": min_score, "limit": limit}
        
        if procedure_name:
            cypher += """
            MATCH (h)-[:OFFERS_PROCEDURE]->(p:Procedure {name: $procedure_name})
            """
            params["procedure_name"] = procedure_name
        
        if city_name:
            cypher += """
            MATCH (h)-[:LOCATED_IN]->(g:Geography {city_name: $city_name})
            """
            params["city_name"] = city_name
        
        cypher += """
        OPTIONAL MATCH (h)-[:HAS_REVIEW_ASPECT]->(r:ReviewAspect)
        RETURN h.id AS id,
               h.name AS name,
               h.tier AS tier,
               h.fusion_score AS fusion_score,
               h.fusion_clinical AS clinical_score,
               h.fusion_reputation AS reputation_score,
               h.fusion_accessibility AS accessibility_score,
               h.fusion_affordability AS affordability_score,
               h.city AS city,
               h.rating AS rating,
               h.has_emergency_unit AS has_emergency,
               avg(r.vader_compound_score) AS avg_sentiment
        ORDER BY h.fusion_score DESC
        LIMIT $limit
        """
        
        return self.run_query(cypher, params)
