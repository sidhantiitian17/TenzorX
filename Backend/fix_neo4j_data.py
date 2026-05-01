#!/usr/bin/env python
"""
Fix Neo4j Data - Create missing relationships and ensure proper cost data.
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_procedure_cost_links(client):
    """Link procedures to cost components."""
    logger.info("Creating Procedure-CostComponent relationships...")
    
    # Common procedures and their cost component mappings
    procedure_costs = [
        # Knee Replacement
        ("Total Knee Replacement", [
            ("pre_procedure", "Pre-operative Assessment", 15000, 25000),
            ("procedure", "Knee Replacement Surgery", 120000, 200000),
            ("hospital_stay", "Hospital Stay (3-5 days)", 25000, 60000),
            ("post_procedure", "Post-operative Care & Physiotherapy", 8000, 20000),
        ]),
        # Angioplasty
        ("Coronary Angioplasty", [
            ("pre_procedure", "Pre-procedure Diagnostics (ECG, Angiography)", 10000, 30000),
            ("procedure", "Angioplasty with Stent Placement", 150000, 300000),
            ("hospital_stay", "Hospital Stay (2-4 days)", 20000, 50000),
            ("post_procedure", "Post-procedure Medications & Follow-up", 10000, 25000),
        ]),
        # Hip Replacement
        ("Total Hip Replacement", [
            ("pre_procedure", "Pre-operative Assessment", 15000, 25000),
            ("procedure", "Hip Replacement Surgery", 150000, 250000),
            ("hospital_stay", "Hospital Stay (3-5 days)", 25000, 60000),
            ("post_procedure", "Post-operative Care & Physiotherapy", 10000, 25000),
        ]),
    ]
    
    for proc_name, components in procedure_costs:
        for phase, desc, cost_min, cost_max in components:
            # Create CostComponent
            client.run_query("""
                MERGE (cc:CostComponent {component_id: $comp_id})
                SET cc.phase = $phase,
                    cc.description = $desc,
                    cc.base_cost_min_inr = $min,
                    cc.base_cost_max_inr = $max
            """, {
                "comp_id": f"{proc_name}_{phase}",
                "phase": phase,
                "desc": desc,
                "min": cost_min,
                "max": cost_max
            })
            
            # Link to Procedure
            client.run_query("""
                MATCH (p:Procedure {name: $proc_name})
                MATCH (cc:CostComponent {component_id: $comp_id})
                MERGE (p)-[:HAS_COST_COMPONENT]->(cc)
            """, {
                "proc_name": proc_name,
                "comp_id": f"{proc_name}_{phase}"
            })
    
    logger.info("✅ Procedure-CostComponent relationships created")


def create_hospital_procedure_links(client):
    """Link hospitals to procedures they offer."""
    logger.info("Creating Hospital-Procedure relationships...")
    
    # Hospital specializations and matching procedures
    hospital_procedures = [
        # Nagpur hospitals
        ("hosp_nagpur_001", ["Cardiac", "Orthopedic"], ["Coronary Angioplasty", "Total Knee Replacement"]),
        ("hosp_nagpur_002", ["Orthopedic", "General Surgery"], ["Total Knee Replacement", "Total Hip Replacement"]),
        # Mumbai hospitals
        ("hosp_mumbai_001", ["Cardiac", "Neurosurgery"], ["Coronary Angioplasty"]),
        ("hosp_mumbai_002", ["Orthopedic", "Joint Replacement"], ["Total Knee Replacement", "Total Hip Replacement"]),
    ]
    
    for hosp_id, specializations, procedures in hospital_procedures:
        for proc_name in procedures:
            client.run_query("""
                MATCH (h:Hospital {id: $hosp_id})
                MATCH (p:Procedure {name: $proc_name})
                MERGE (h)-[:OFFERS_PROCEDURE]->(p)
            """, {
                "hosp_id": hosp_id,
                "proc_name": proc_name
            })
    
    logger.info("✅ Hospital-Procedure relationships created")


def ensure_common_procedures_exist(client):
    """Ensure common procedures exist in the database."""
    logger.info("Ensuring common procedures exist...")
    
    common_procedures = [
        ("Total Knee Replacement", "Z47.1", "Orthopedic"),
        ("Coronary Angioplasty", "Z95.5", "Cardiac"),
        ("Total Hip Replacement", "Z47.1", "Orthopedic"),
        ("Cataract Surgery", "Z98.4", "Ophthalmology"),
    ]
    
    for name, icd10, category in common_procedures:
        client.run_query("""
            MERGE (p:Procedure {name: $name})
            SET p.icd10_code = $icd10,
                p.category = $category
        """, {
            "name": name,
            "icd10": icd10,
            "category": category
        })
    
    logger.info("✅ Common procedures ensured")


def main():
    print("="*70)
    print("FIXING NEO4J DATA")
    print("="*70)
    print()
    
    from app.knowledge_graph.neo4j_client import Neo4jClient
    
    client = Neo4jClient()
    
    try:
        # Fix the data
        ensure_common_procedures_exist(client)
        create_procedure_cost_links(client)
        create_hospital_procedure_links(client)
        
        print()
        print("="*70)
        print("✅ DATA FIX COMPLETE")
        print("="*70)
        print()
        
        # Verify
        print("Verification:")
        result = client.run_query('''
            MATCH (p:Procedure)-[:HAS_COST_COMPONENT]->(cc:CostComponent)
            RETURN p.name AS proc, count(cc) AS components
        ''')
        for r in result:
            print(f"  - {r['proc']}: {r['components']} cost components")
        
        print()
        result = client.run_query('''
            MATCH (h:Hospital)-[:OFFERS_PROCEDURE]->(p:Procedure)
            RETURN count(*) AS total_links
        ''')
        total = result[0]['total_links'] if result else 0
        print(f"  - Total Hospital-Procedure links: {total}")
        
    except Exception as e:
        print()
        print("="*70)
        print("❌ DATA FIX FAILED")
        print("="*70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
