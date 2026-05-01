#!/usr/bin/env python
"""Check what data is in Neo4j."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.knowledge_graph.neo4j_client import Neo4jClient

def main():
    client = Neo4jClient()
    
    print("="*70)
    print("CHECKING NEO4J DATA")
    print("="*70)
    print()
    
    # Check procedures
    print("[1] Procedures in Neo4j:")
    result = client.run_query('MATCH (p:Procedure) RETURN p.name AS name LIMIT 10')
    for r in result:
        print(f"  - {r['name']}")
    print()
    
    # Check cost components
    print("[2] Cost components:")
    result = client.run_query('MATCH (cc:CostComponent) RETURN cc.component_id AS id LIMIT 10')
    for r in result:
        print(f"  - {r['id']}")
    print()
    
    # Check hospitals
    print("[3] Hospitals in Nagpur:")
    result = client.run_query('''
        MATCH (h:Hospital)-[:LOCATED_IN]->(g:Geography)
        WHERE toLower(g.city_name) = "nagpur"
        RETURN h.name AS name, h.id AS id
    ''')
    for r in result:
        print(f"  - {r['name']} ({r['id']})")
    print()
    
    # Check OFFERS_PROCEDURE relationships
    print("[4] Hospital-Procedure relationships:")
    result = client.run_query('''
        MATCH (h:Hospital)-[r:OFFERS_PROCEDURE]->(p:Procedure)
        RETURN h.name AS hospital, p.name AS procedure LIMIT 5
    ''')
    for r in result:
        print(f"  - {r['hospital']} -> {r['procedure']}")
    print()
    
    # Count nodes
    print("[5] Node counts:")
    for label in ['Procedure', 'Hospital', 'CostComponent', 'Geography']:
        result = client.run_query(f'MATCH (n:{label}) RETURN count(n) AS cnt')
        count = result[0]['cnt'] if result else 0
        print(f"  - {label}: {count}")
    print()
    
    client.close()
    print("="*70)
    print("CHECK COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
