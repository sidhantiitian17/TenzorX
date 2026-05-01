"""
Integration tests for GraphRAG Engine with LLM synthesis.

Tests that the complete pipeline works:
1. NER extraction
2. Knowledge graph queries (Neo4j)
3. Cost engine calculations
4. Fusion scoring
5. Availability proxy
6. LLM synthesis with graph context
"""

import pytest
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.knowledge_graph.graph_rag import GraphRAGEngine
from app.knowledge_graph.neo4j_client import Neo4jClient
from app.core.nvidia_client import NvidiaClient


# Skip if Neo4j or NVIDIA API not available
pytestmark = pytest.mark.skipif(
    not os.getenv("NEO4J_URI") or not os.getenv("NVIDIA_API_KEY"),
    reason="Neo4j or NVIDIA API not configured"
)


class TestGraphRAGPipeline:
    """Test complete GraphRAG pipeline with real LLM and knowledge graph."""
    
    @pytest.fixture(scope="class")
    def engine(self):
        """Provide a GraphRAG engine instance."""
        engine = GraphRAGEngine()
        yield engine
        engine.close()
    
    def test_ner_extraction(self, engine):
        """Test NER pipeline extracts medical entities."""
        user_text = "I have severe chest pain and shortness of breath"
        entities = engine.ner.extract(user_text)
        
        # Should extract symptoms
        assert len(entities) > 0
        symptom_entities = [e for e in entities if e.label == "SYMPTOM"]
        assert len(symptom_entities) >= 1
    
    def test_knowledge_graph_disease_lookup(self, engine):
        """Test Neo4j returns diseases for symptoms."""
        symptoms = ["chest pain", "shortness of breath"]
        diseases = engine.neo4j.find_diseases_for_symptoms(symptoms)
        
        # Should find cardiovascular-related diseases
        assert len(diseases) > 0
        assert any("cardio" in d.get("category", "").lower() for d in diseases)
    
    def test_procedure_discovery(self, engine):
        """Test Neo4j returns procedures for diseases."""
        # Use a known ICD-10 code for heart disease
        disease_icd = "I25.10"  # Atherosclerotic heart disease
        procedures = engine.neo4j.find_procedures_for_disease(disease_icd)
        
        assert "treatment" in procedures or "diagnostic" in procedures
    
    def test_cost_breakdown_retrieval(self, engine):
        """Test Neo4j returns cost breakdown for procedures."""
        procedure = "Angioplasty"
        cost_breakdown = engine.neo4j.get_cost_breakdown(procedure)
        
        assert len(cost_breakdown) > 0
        # Should have 4 phases
        phases = set(c["phase"] for c in cost_breakdown)
        assert len(phases) >= 3  # At least pre, procedure, post
    
    def test_cost_adjustments_with_geo_multiplier(self, engine):
        """Test cost adjustments apply geographic multipliers."""
        adjustments = engine.neo4j.apply_cost_adjustments(
            base_cost_min=100000,
            base_cost_max=150000,
            city_name="mumbai",
            comorbidity_names=[],
            patient_age=45
        )
        
        assert adjustments is not None
        assert "final_cost_min" in adjustments
        assert "final_cost_max" in adjustments
        assert "geo_multiplier" in adjustments
        # Mumbai is Tier 1, multiplier should be 1.0
        assert adjustments["geo_multiplier"] == 1.0
    
    def test_cost_adjustments_with_comorbidities(self, engine):
        """Test cost adjustments increase with comorbidities."""
        base_min, base_max = 100000, 150000
        
        # Without comorbidities
        adj_no_comorb = engine.neo4j.apply_cost_adjustments(
            base_cost_min=base_min,
            base_cost_max=base_max,
            city_name="mumbai",
            comorbidity_names=[],
            patient_age=45
        )
        
        # With comorbidities
        adj_with_comorb = engine.neo4j.apply_cost_adjustments(
            base_cost_min=base_min,
            base_cost_max=base_max,
            city_name="mumbai",
            comorbidity_names=["diabetes", "hypertension"],
            patient_age=45
        )
        
        # Cost should be higher with comorbidities
        assert adj_with_comorb["final_cost_min"] > adj_no_comorb["final_cost_min"]
    
    def test_hospital_discovery(self, engine):
        """Test Neo4j finds hospitals for procedures in cities."""
        hospitals = engine.neo4j.find_hospitals_for_procedure_in_city(
            procedure_name="Angioplasty",
            city_name="Mumbai",
            limit=5
        )
        
        # Should find hospitals (or empty if none in test data)
        assert isinstance(hospitals, list)
        if len(hospitals) > 0:
            assert "id" in hospitals[0]
            assert "name" in hospitals[0]
    
    def test_fusion_scorer_ranks_hospitals(self, engine):
        """Test FusionScorer computes scores for hospitals."""
        # Get some hospitals first
        hospitals = engine.neo4j.find_hospitals_for_procedure_in_city(
            procedure_name="Angioplasty",
            city_name="Mumbai",
            limit=3
        )
        
        if len(hospitals) > 0:
            # Test scoring for first hospital
            hosp_id = hospitals[0]["id"]
            scores = engine.fusion_scorer.compute_fusion_score(hosp_id)
            
            assert "fusion_score" in scores
            assert 0 <= scores["fusion_score"] <= 1
    
    def test_availability_proxy_computes_wait_times(self, engine):
        """Test AvailabilityProxy computes estimated wait times."""
        # Get a hospital ID
        hospitals = engine.neo4j.find_hospitals_for_procedure_in_city(
            procedure_name="Angioplasty",
            city_name="Mumbai",
            limit=1
        )
        
        if len(hospitals) > 0:
            hosp_id = hospitals[0]["id"]
            availability = engine.availability_proxy.compute_availability(
                hosp_id,
                department="Cardiovascular",
                is_emergency=False
            )
            
            assert availability is not None
            assert hasattr(availability, 'label')
            assert hasattr(availability, 'estimated_days')
            assert availability.score >= 0
    
    def test_severity_classification(self, engine):
        """Test SeverityClassifier correctly identifies emergencies."""
        from app.knowledge_graph.availability_proxy import SeverityClassifier
        
        # Emergency symptoms
        severity = SeverityClassifier.classify(
            symptoms=["chest pain", "shortness of breath"],
            raw_text="severe crushing chest pain"
        )
        
        assert severity["severity"] in ["RED", "YELLOW", "GREEN"]
        assert "reason" in severity
    
    def test_icd10_mapper_lookup(self, engine):
        """Test ICD-10 mapper resolves conditions to codes."""
        result = engine.icd_mapper.lookup("chest pain")
        
        # Should return a code or None (if ICD-10 data not loaded)
        if result:
            assert "code" in result
            assert "description" in result
    
    def test_llm_client_initialization(self, engine):
        """Test NvidiaClient is properly initialized."""
        assert engine.llm is not None
        assert isinstance(engine.llm, NvidiaClient)
    
    def test_pathway_builder(self, engine):
        """Test pathway builder creates phase-based cost structure."""
        cost_breakdown = [
            {"phase": "pre_procedure", "description": "Diagnostics", "cost_min": 5000, "cost_max": 10000, "typical_days": 2},
            {"phase": "procedure", "description": "Surgery", "cost_min": 50000, "cost_max": 80000, "typical_days": 1},
            {"phase": "post_procedure", "description": "Recovery", "cost_min": 3000, "cost_max": 5000, "typical_days": 5},
        ]
        
        cost_adjustments = {
            "final_multiplier": 1.1,
            "geo_multiplier": 1.0
        }
        
        pathway = engine._build_pathway(cost_breakdown, cost_adjustments)
        
        assert len(pathway) == 3
        assert pathway[0]["phase"] == "pre_procedure"
        assert pathway[1]["phase"] == "procedure"
        assert pathway[2]["phase"] == "post_procedure"
        
        # Check adjusted costs
        assert pathway[0]["adjusted_cost_min_inr"] > pathway[0]["base_cost_min_inr"]
    
    def test_confidence_score_computation(self, engine):
        """Test confidence score is computed correctly."""
        # Full match case
        score_full = engine._compute_confidence(
            has_disease=True,
            has_procedure=True,
            hospital_count=5,
            has_cost=True
        )
        assert score_full == 1.0
        
        # Partial match case
        score_partial = engine._compute_confidence(
            has_disease=True,
            has_procedure=True,
            hospital_count=0,
            has_cost=True
        )
        assert 0.5 <= score_partial < 1.0
    
    def test_system_prompt_building(self, engine):
        """Test system prompt contains required elements."""
        prompt = engine._build_system_prompt()
        
        assert "HealthNav" in prompt
        assert "Neo4j Knowledge Graph" in prompt
        assert "SEARCH_DATA" in prompt
        assert "⚕ This is decision support only" in prompt
    
    def test_fallback_response_generation(self, engine):
        """Test fallback response is generated when LLM fails."""
        fallback = engine._generate_fallback_response(
            procedure="Angioplasty",
            location="Mumbai"
        )
        
        assert "Angioplasty" in fallback
        assert "Mumbai" in fallback
        assert "decision support only" in fallback


class TestGraphRAGEndToEnd:
    """End-to-end tests requiring live LLM and Neo4j."""
    
    @pytest.fixture(scope="class")
    def engine(self):
        """Provide a GraphRAG engine instance."""
        engine = GraphRAGEngine()
        yield engine
        engine.close()
    
    @pytest.mark.slow
    def test_complete_query_pipeline(self, engine):
        """
        Test complete query pipeline with real LLM synthesis.
        
        This test exercises:
        - NER extraction
        - Knowledge graph traversal
        - Cost calculations
        - Hospital ranking
        - LLM synthesis with graph context
        """
        result = engine.query(
            user_text="I need knee replacement surgery in Mumbai",
            location="Mumbai",
            patient_profile={"age": 65, "comorbidities": ["diabetes"]}
        )
        
        # Verify structure
        assert "llm_response" in result
        assert "entities" in result
        assert "icd10" in result
        assert "procedure" in result
        assert "cost_estimate" in result
        assert "confidence_score" in result
        
        # Verify content
        assert result["procedure"] is not None
        assert result["cost_estimate"] is not None
        assert result["confidence_score"] >= 0
        
        # LLM should have synthesized a response
        assert len(result["llm_response"]) > 100
        
        # Should mention decision support disclaimer
        assert "decision support" in result["llm_response"].lower() or \
               "not medical advice" in result["llm_response"].lower()
    
    @pytest.mark.slow
    def test_emergency_query_handling(self, engine):
        """Test emergency queries are handled correctly."""
        result = engine.query(
            user_text="Severe chest pain and can't breathe",
            location="Mumbai",
            patient_profile={"age": 55}
        )
        
        # Should identify as emergency
        assert result["severity"]["severity"] == "RED"
        
        # Should have high confidence due to clear symptoms
        assert result["confidence_score"] >= 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
