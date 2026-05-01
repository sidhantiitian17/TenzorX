"""
Pytest tests for Neo4j Knowledge Graph implementation.

Tests NBFCRiskBand, clinical pathways, constraints, indexes, and seed functions.
"""

import pytest
import os
from pathlib import Path

# Ensure we can import from app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.knowledge_graph.neo4j_client import Neo4jClient
from app.knowledge_graph.schema_setup import (
    create_constraints,
    create_indexes,
    create_fulltext_indexes,
    create_vector_indexes,
    seed_nbfc_risk_bands,
    seed_geographic_tiers,
    seed_cities,
    seed_departments,
    seed_insurance_policies,
    seed_pathway_phases,
    setup_schema,
)
from app.engines.neo4j_loan_client import Neo4jLoanClient, get_loan_client


# Skip all tests if Neo4j is not available
pytestmark = pytest.mark.skipif(
    not os.getenv("NEO4J_URI"),
    reason="Neo4j not configured - set NEO4J_URI environment variable"
)


class TestNeo4jConnection:
    """Test basic Neo4j connectivity."""
    
    def test_client_initialization(self):
        """Test that Neo4jClient can be initialized."""
        client = Neo4jClient()
        assert client is not None
        assert client.driver is not None
        client.close()
    
    def test_simple_query(self):
        """Test that basic queries execute successfully."""
        client = Neo4jClient()
        result = client.run_query("RETURN 1 as num")
        assert result == [{"num": 1}]
        client.close()


class TestNBFCRiskBand:
    """Test NBFCRiskBand node creation and DTI lookup per instructioncreate.md Section 6."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Provide a Neo4j client for the test class."""
        client = Neo4jClient()
        yield client
        client.close()
    
    @pytest.fixture(scope="class")
    def loan_client(self, client):
        """Provide a Neo4jLoanClient for the test class."""
        return Neo4jLoanClient(client)
    
    def test_seed_nbfc_risk_bands(self, client):
        """Test that NBFCRiskBand nodes are created correctly."""
        # Clean up any existing nodes (DETACH DELETE removes relationships too)
        client.run_query("MATCH (b:NBFCRiskBand) DETACH DELETE b")
        
        # Seed the risk bands
        seed_nbfc_risk_bands(client)
        
        # Verify all 4 bands were created
        result = client.run_query("MATCH (b:NBFCRiskBand) RETURN count(b) as count")
        assert result[0]["count"] == 4
    
    def test_nbfc_risk_band_properties(self, client):
        """Test that NBFCRiskBand nodes have correct properties."""
        # Get BAND_LOW
        result = client.run_query(
            "MATCH (b:NBFCRiskBand {band_id: 'BAND_LOW'}) RETURN b"
        )
        assert len(result) == 1
        band = result[0]["b"]
        assert band["dti_min"] == 0.0
        assert band["dti_max"] == 30.0
        assert band["risk_flag"] == "LOW"
        assert band["interest_rate_min"] == 12.0
        assert band["interest_rate_max"] == 13.0
        assert band["approval_likelihood"] == "VERY HIGH"
        assert band["loan_coverage_pct"] == 0.80
    
    def test_get_risk_band_by_dti_low(self, loan_client):
        """Test DTI lookup returns correct band for low risk."""
        band = loan_client.get_risk_band_by_dti(25.0)
        assert band["band_id"] == "BAND_LOW"
        assert band["risk_flag"] == "LOW"
    
    def test_get_risk_band_by_dti_medium(self, loan_client):
        """Test DTI lookup returns correct band for medium risk."""
        band = loan_client.get_risk_band_by_dti(35.0)
        assert band["band_id"] == "BAND_MEDIUM"
        assert band["risk_flag"] == "MEDIUM"
    
    def test_get_risk_band_by_dti_high(self, loan_client):
        """Test DTI lookup returns correct band for high risk."""
        band = loan_client.get_risk_band_by_dti(45.0)
        assert band["band_id"] == "BAND_HIGH"
        assert band["risk_flag"] == "HIGH"
    
    def test_get_risk_band_by_dti_critical(self, loan_client):
        """Test DTI lookup returns correct band for critical risk."""
        band = loan_client.get_risk_band_by_dti(60.0)
        assert band["band_id"] == "BAND_CRITICAL"
        assert band["risk_flag"] == "CRITICAL"
    
    def test_fallback_band(self, loan_client):
        """Test fallback band when Neo4j unavailable."""
        # Test fallback for various DTI values
        low = loan_client._fallback_band(20.0)
        assert low["band_id"] == "BAND_LOW"
        
        critical = loan_client._fallback_band(75.0)
        assert critical["band_id"] == "BAND_CRITICAL"


class TestGeographicTier:
    """Test GeographicTier and City nodes per instructioncreate.md Section 6 & 9."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Provide a Neo4j client for the test class."""
        client = Neo4jClient()
        yield client
        client.close()
    
    def test_seed_geographic_tiers(self, client):
        """Test that GeographicTier nodes are created correctly."""
        # Clean up (DETACH DELETE removes relationships too)
        client.run_query("MATCH (t:GeographicTier) DETACH DELETE t")
        
        # Seed tiers
        seed_geographic_tiers(client)
        
        # Verify all 3 tiers created
        result = client.run_query("MATCH (t:GeographicTier) RETURN count(t) as count")
        assert result[0]["count"] == 3
    
    def test_geographic_tier_properties(self, client):
        """Test that GeographicTier nodes have correct properties."""
        result = client.run_query(
            "MATCH (t:GeographicTier {tier_id: 'TIER_1'}) RETURN t"
        )
        assert len(result) == 1
        tier = result[0]["t"]
        assert tier["cost_multiplier"] == 1.0
        assert tier["icu_bed_day_cost"] == 5534
        assert tier["specialist_density"] == "HIGH"
    
    def test_tier_2_multiplier(self, client):
        """Test Tier 2 has correct multiplier."""
        result = client.run_query(
            "MATCH (t:GeographicTier {tier_id: 'TIER_2'}) RETURN t.cost_multiplier as mult"
        )
        assert result[0]["mult"] == 0.92
    
    def test_tier_3_multiplier(self, client):
        """Test Tier 3 has correct multiplier."""
        result = client.run_query(
            "MATCH (t:GeographicTier {tier_id: 'TIER_3'}) RETURN t.cost_multiplier as mult"
        )
        assert result[0]["mult"] == 0.83


class TestPathwayPhase:
    """Test PathwayPhase nodes for clinical pathways per instructioncreate.md Section 8."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Provide a Neo4j client for the test class."""
        client = Neo4jClient()
        # Clean up - use DETACH DELETE to remove relationships too
        client.run_query("MATCH (ph:PathwayPhase) DETACH DELETE ph")
        yield client
        client.close()
    
    def test_seed_pathway_phases(self, client):
        """Test that PathwayPhase nodes are created for all 6 procedures."""
        seed_pathway_phases(client)
        
        # Count phases (6 procedures × 4 phases = 24)
        result = client.run_query("MATCH (ph:PathwayPhase) RETURN count(ph) as count")
        assert result[0]["count"] == 24
    
    def test_angioplasty_phases(self, client):
        """Test Angioplasty has correct 4 phases."""
        result = client.run_query("""
            MATCH (p:Procedure {name: 'Angioplasty'})-[:HAS_PHASE]->(ph:PathwayPhase)
            RETURN ph.phase_order as order, ph.phase_name as name
            ORDER BY ph.phase_order
        """)
        assert len(result) == 4
        assert result[0]["order"] == 1
        assert result[3]["order"] == 4
    
    def test_phase_types(self, client):
        """Test that phases have correct types."""
        result = client.run_query("""
            MATCH (ph:PathwayPhase)
            RETURN DISTINCT ph.phase_type as type
        """)
        types = [r["type"] for r in result]
        assert "PRE" in types
        assert "SURGICAL" in types
        assert "HOSPITAL_STAY" in types
        assert "POST" in types
    
    def test_phase_has_mandatory_flag(self, client):
        """Test that phases have is_mandatory property."""
        result = client.run_query("""
            MATCH (ph:PathwayPhase {phase_id: 'PHASE_ANGIO_01'})
            RETURN ph.is_mandatory as mandatory
        """)
        assert result[0]["mandatory"] == True


class TestConstraints:
    """Test that constraints are created correctly."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Provide a Neo4j client for the test class."""
        client = Neo4jClient()
        yield client
        client.close()
    
    def test_constraints_exist(self, client):
        """Test that expected constraints exist."""
        result = client.run_query("SHOW CONSTRAINTS YIELD name RETURN count(name) as count")
        # Should have at least 10 constraints
        assert result[0]["count"] >= 10
    
    def test_indexes_exist(self, client):
        """Test that expected indexes exist."""
        result = client.run_query("SHOW INDEXES YIELD name RETURN count(name) as count")
        # Should have at least 8 indexes
        assert result[0]["count"] >= 8


class TestDepartment:
    """Test Department nodes per instructioncreate.md Section 12."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Provide a Neo4j client for the test class."""
        client = Neo4jClient()
        # Clean up - use DETACH DELETE to remove relationships too
        client.run_query("MATCH (d:Department) DETACH DELETE d")
        yield client
        client.close()
    
    def test_seed_departments(self, client):
        """Test that Department nodes are created."""
        seed_departments(client)
        
        result = client.run_query("MATCH (d:Department) RETURN count(d) as count")
        assert result[0]["count"] == 10
    
    def test_cardiology_department(self, client):
        """Test Cardiology department exists with correct properties."""
        result = client.run_query(
            "MATCH (d:Department {dept_id: 'DEPT_CARD'}) RETURN d"
        )
        assert len(result) == 1
        dept = result[0]["d"]
        assert dept["name"] == "Cardiology"
        assert dept["requires_nabh"] == True


class TestInsurancePolicy:
    """Test InsurancePolicy nodes per instructioncreate.md Section 13."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Provide a Neo4j client for the test class."""
        client = Neo4jClient()
        # Clean up - use DETACH DELETE to remove relationships too
        client.run_query("MATCH (p:InsurancePolicy) DETACH DELETE p")
        yield client
        client.close()
    
    def test_seed_insurance_policies(self, client):
        """Test that InsurancePolicy nodes are created."""
        seed_insurance_policies(client)
        
        result = client.run_query("MATCH (p:InsurancePolicy) RETURN count(p) as count")
        assert result[0]["count"] == 6
    
    def test_pmjay_policy(self, client):
        """Test PMJAY policy has correct properties."""
        result = client.run_query(
            "MATCH (p:InsurancePolicy {policy_id: 'INS_GOVT_PMJAY'}) RETURN p"
        )
        assert len(result) == 1
        policy = result[0]["p"]
        assert policy["sum_insured_max_inr"] == 500000
        assert policy["waiting_period_months"] == 0
        assert policy["covers_pre_existing"] == True


class TestIntegration:
    """Integration tests for the complete knowledge graph."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Provide a Neo4j client for the test class."""
        client = Neo4jClient()
        yield client
        client.close()
    
    def test_city_to_tier_relationship(self, client):
        """Test City nodes are linked to GeographicTier."""
        # Clean up and seed
        client.run_query("MATCH (c:City) DELETE c")
        seed_geographic_tiers(client)
        seed_cities(client)
        
        # Test relationship
        result = client.run_query("""
            MATCH (c:City)-[:CITY_BELONGS_TO]->(t:GeographicTier)
            RETURN count(c) as linked_cities
        """)
        assert result[0]["linked_cities"] == 19  # All cities should be linked
    
    def test_graph_connectivity_summary(self, client):
        """Test that the graph has expected node counts."""
        # Run full schema setup to ensure all nodes exist
        # Note: This is an expensive operation, consider using a fixture
        
        node_counts = client.run_query("""
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
        """)
        
        # Should have at least 10 different node types
        assert len(node_counts) >= 10
        
        # Log the counts for debugging
        print("\nNode counts:")
        for record in node_counts:
            print(f"  {record['label']}: {record['count']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
