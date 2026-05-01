#!/usr/bin/env python
"""Debug GraphRAG queries."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO)

from app.knowledge_graph.neo4j_client import Neo4jClient

def test_neo4j_queries():
    client = Neo4jClient()
    
    print("="*70)
    print("DEBUGGING Neo4j QUERIES")
    print("="*70)
    print()
    
    print(f"Neo4j disabled: {client._disabled}")
    print()
    
    # Test 1: Get cost breakdown for knee replacement
    print("[TEST 1] Get cost breakdown for 'Total Knee Replacement':")
    try:
        result = client.get_cost_breakdown("Total Knee Replacement")
        print(f"  Result: {len(result)} components")
        for r in result[:3]:
            print(f"    - {r.get('phase')}: Rs {r.get('cost_min')} - Rs {r.get('cost_max')}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Test 2: Find hospitals in Nagpur
    print("[TEST 2] Find hospitals in 'Nagpur':")
    try:
        result = client.find_hospitals_for_procedure_in_city("Total Knee Replacement", "Nagpur", limit=5)
        print(f"  Result: {len(result)} hospitals")
        for r in result[:3]:
            print(f"    - {r.get('name')} ({r.get('city')})")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Test 3: Check if procedure exists
    print("[TEST 3] Check if 'Total Knee Replacement' procedure exists:")
    try:
        result = client.run_query('MATCH (p:Procedure {name: "Total Knee Replacement"}) RETURN p.name AS name')
        if result:
            print(f"  Found: {result[0]['name']}")
        else:
            print("  Not found")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Test 4: Check HAS_COST_COMPONENT relationship
    print("[TEST 4] Check HAS_COST_COMPONENT relationship:")
    try:
        result = client.run_query('''
            MATCH (p:Procedure {name: "Total Knee Replacement"})-[:HAS_COST_COMPONENT]->(cc:CostComponent)
            RETURN count(cc) AS cnt
        ''')
        print(f"  Cost components linked: {result[0]['cnt'] if result else 0}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Test 5: Check OFFERS_PROCEDURE relationship
    print("[TEST 5] Check OFFERS_PROCEDURE relationship for Nagpur hospitals:")
    try:
        result = client.run_query('''
            MATCH (h:Hospital)-[:LOCATED_IN]->(g:Geography)
            WHERE toLower(g.city_name) = "nagpur"
            MATCH (h)-[:OFFERS_PROCEDURE]->(p:Procedure)
            RETURN h.name AS hospital, p.name AS procedure
            LIMIT 5
        ''')
        print(f"  Hospital-Procedure pairs: {len(result)}")
        for r in result:
            print(f"    - {r['hospital']} -> {r['procedure']}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    client.close()
    print("="*70)
    print("DEBUG COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_neo4j_queries()
