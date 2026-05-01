#!/usr/bin/env python
"""Test script to verify Neo4j database connectivity and knowledge graph status.

USAGE:
    python test_neo4j_connection.py          # Run all tests
    python test_neo4j_connection.py --quick  # Quick connection test only
    python test_neo4j_connection.py --seed   # Test and seed sample data
"""

import sys
import logging
import argparse

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_connection():
    """Test basic Neo4j connection."""
    logger.info("=" * 70)
    logger.info("🧪 TEST 1: Basic Neo4j Connection")
    logger.info("=" * 70)
    
    try:
        from neo4j import GraphDatabase
        
        uri = settings.NEO4J_URI
        user = settings.NEO4J_USER
        password = settings.NEO4J_PASSWORD
        
        logger.info(f"URI: {uri}")
        logger.info(f"User: {user}")
        logger.info(f"Password: {'*' * len(password) if password else 'NOT SET'}")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1 as num")
            record = result.single()
            assert record["num"] == 1
        
        driver.close()
        logger.info("✅ Basic connection successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False


def test_neo4j_client():
    """Test Neo4jClient wrapper."""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 TEST 2: Neo4jClient Wrapper")
    logger.info("=" * 70)
    
    try:
        from app.knowledge_graph.neo4j_client import Neo4jClient
        
        client = Neo4jClient()
        logger.info("✅ Neo4jClient initialized")
        
        # Test health check
        health = client.health_check()
        if health:
            logger.info("✅ Health check passed")
        else:
            logger.warning("⚠️  Health check failed")
            
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Neo4jClient test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_schema():
    """Verify graph schema (constraints and node types)."""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 TEST 3: Graph Schema Verification")
    logger.info("=" * 70)
    
    try:
        from app.knowledge_graph.neo4j_client import Neo4jClient
        
        client = Neo4jClient()
        
        # Check constraints
        constraints = client.execute_query("SHOW CONSTRAINTS")
        constraint_list = list(constraints)
        logger.info(f"Constraints found: {len(constraint_list)}")
        for c in constraint_list:
            logger.info(f"  - {c.get('name', 'unnamed')}: {c.get('type', 'unknown')}")
        
        # Check node labels
        labels_result = client.execute_query("""
            CALL db.labels() YIELD label 
            RETURN collect(label) as labels
        """)
        labels = list(labels_result)[0]["labels"] if labels_result else []
        logger.info(f"\nNode labels: {labels}")
        
        # Count nodes by label
        logger.info("\nNode counts:")
        for label in labels:
            count_result = client.execute_query(f"MATCH (n:{label}) RETURN count(n) as cnt")
            count = list(count_result)[0]["cnt"] if count_result else 0
            logger.info(f"  - {label}: {count} nodes")
        
        # Check relationship types
        rels_result = client.execute_query("""
            CALL db.relationshipTypes() YIELD relationshipType 
            RETURN collect(relationshipType) as types
        """)
        rel_types = list(rels_result)[0]["types"] if rels_result else []
        logger.info(f"\nRelationship types: {rel_types}")
        
        client.close()
        
        if len(labels) > 0:
            logger.info("✅ Schema verification passed!")
            return True
        else:
            logger.warning("⚠️  No node labels found - database may be empty")
            return False
            
    except Exception as e:
        logger.error(f"❌ Schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_rag_engine():
    """Test GraphRAG engine integration."""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 TEST 4: GraphRAG Engine Integration")
    logger.info("=" * 70)
    
    try:
        from app.knowledge_graph.graph_rag import GraphRAGEngine
        
        engine = GraphRAGEngine()
        logger.info("✅ GraphRAGEngine initialized")
        
        # Test search with sample query
        logger.info("\n📡 Testing search with: 'knee replacement in Nagpur'")
        result = engine.search(
            entities=["knee replacement"],
            location="nagpur",
            icd10_codes=["Z47.1"]
        )
        
        logger.info(f"\n--- SEARCH RESULTS ---")
        logger.info(f"Procedure: {result.get('procedure', 'N/A')}")
        logger.info(f"ICD-10 Code: {result.get('icd10_code', 'N/A')}")
        logger.info(f"Hospitals found: {len(result.get('hospitals', []))}")
        
        for i, hospital in enumerate(result.get('hospitals', [])[:3], 1):
            logger.info(f"  {i}. {hospital.get('name', 'Unknown')} - {hospital.get('cost_min', 0)}-{hospital.get('cost_max', 0)} INR")
        
        if result.get('hospitals'):
            logger.info("✅ GraphRAG search successful!")
        else:
            logger.warning("⚠️  No hospitals found - data may need to be seeded")
        
        engine.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ GraphRAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def seed_sample_data():
    """Seed sample data if database is empty."""
    logger.info("\n" + "=" * 70)
    logger.info("🌱 SEEDING SAMPLE DATA")
    logger.info("=" * 70)
    
    try:
        from app.knowledge_graph.schema_setup import seed_knowledge_graph
        
        seed_knowledge_graph()
        logger.info("✅ Sample data seeded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ner_pipeline():
    """Test NER pipeline with Neo4j integration."""
    logger.info("\n" + "=" * 70)
    logger.info("🧪 TEST 5: NER Pipeline Integration")
    logger.info("=" * 70)
    
    try:
        from app.nlp.ner_pipeline import NERPipeline
        
        ner = NERPipeline()
        logger.info("✅ NERPipeline initialized")
        
        # Test extraction
        text = "I need knee replacement surgery in Nagpur. I have diabetes."
        logger.info(f"\n📡 Testing extraction on: '{text}'")
        
        entities = ner.extract(text)
        logger.info(f"\n--- EXTRACTED ENTITIES (SANITIZED) ---")
        logger.info(f"Symptoms detected: {len(entities.get('symptoms', []))}")
        logger.info(f"Procedures detected: {len(entities.get('procedures', []))}")
        logger.info(f"Body parts detected: {len(entities.get('body_parts', []))}")
        logger.info(f"Conditions detected: {len(entities.get('conditions', []))}")
        
        if entities.get('procedures') or entities.get('symptoms'):
            logger.info("✅ NER extraction successful!")
            return True
        else:
            logger.warning("⚠️  No entities extracted")
            return False
            
    except Exception as e:
        logger.error(f"❌ NER test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Test Neo4j database connectivity')
    parser.add_argument('--quick', '-q', action='store_true', help='Quick connection test only')
    parser.add_argument('--seed', '-s', action='store_true', help='Seed sample data')
    args = parser.parse_args()
    
    logger.info("\n" + "=" * 70)
    logger.info("NEO4J DATABASE CONNECTION TEST")
    logger.info("=" * 70)
    
    # Test 1: Basic connection
    if not test_basic_connection():
        logger.error("\n❌ CRITICAL: Cannot connect to Neo4j!")
        logger.error("   Check:")
        logger.error("   1. Neo4j is running (neo4j start)")
        logger.error("   2. NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env")
        return False
    
    if args.quick:
        logger.info("\n✅ Quick test complete - Neo4j is accessible!")
        return True
    
    # Run full test suite
    results = {
        "Basic Connection": True,  # We already passed this
        "Neo4jClient": test_neo4j_client(),
        "Schema": test_graph_schema(),
        "GraphRAG": test_graph_rag_engine(),
        "NER Pipeline": test_ner_pipeline(),
    }
    
    # Seed data if requested
    if args.seed:
        results["Data Seeding"] = seed_sample_data()
        # Re-test schema after seeding
        if results["Data Seeding"]:
            logger.info("\n🔄 Re-testing schema after seeding...")
            results["Schema (Post-Seed)"] = test_graph_schema()
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED - NEO4J IS FULLY OPERATIONAL!")
        return True
    elif passed >= total // 2:
        logger.info("\n⚠️  PARTIAL SUCCESS - Some tests failed")
        return True
    else:
        logger.info("\n❌ MOST TESTS FAILED - Check configuration")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
