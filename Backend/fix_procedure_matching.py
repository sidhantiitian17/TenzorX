#!/usr/bin/env python
"""
Fix procedure name matching in Neo4j.
Add aliases and fuzzy matching support.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.knowledge_graph.neo4j_client import Neo4jClient

def add_procedure_aliases(client):
    """Add aliases to procedures for better matching."""
    logger.info("Adding procedure aliases...")
    
    aliases = [
        ("Total Knee Replacement", ["knee replacement", "knee arthroplasty", "TKR"]),
        ("Coronary Angioplasty", ["angioplasty", "PTCA", "stent placement"]),
        ("Total Hip Replacement", ["hip replacement", "hip arthroplasty", "THR"]),
        ("Cataract Surgery", ["cataract", "phacoemulsification"]),
    ]
    
    for proc_name, alias_list in aliases:
        client.run_query("""
            MATCH (p:Procedure {name: $proc_name})
            SET p.aliases = $aliases
        """, {
            "proc_name": proc_name,
            "aliases": alias_list
        })
    
    logger.info("✅ Aliases added")


def create_fuzzy_matching_index(client):
    """Create a fulltext index for procedure matching."""
    logger.info("Creating fulltext index...")
    
    try:
        client.run_query("""
            CREATE FULLTEXT INDEX procedure_fulltext IF NOT EXISTS
            FOR (p:Procedure) ON EACH [p.name, p.aliases]
        """)
        logger.info("✅ Fulltext index created")
    except Exception as e:
        logger.warning(f"Index creation skipped (may exist): {e}")


def find_procedure_fuzzy(client, query_name):
    """Find a procedure using fuzzy matching."""
    # Try exact match first
    result = client.run_query("""
        MATCH (p:Procedure)
        WHERE toLower(p.name) = toLower($query)
           OR toLower($query) CONTAINS toLower(p.name)
           OR toLower(p.name) CONTAINS toLower($query)
        RETURN p.name AS name
        LIMIT 1
    """, {"query": query_name})
    
    if result:
        return result[0]["name"]
    
    # Try alias matching
    result = client.run_query("""
        MATCH (p:Procedure)
        WHERE ANY(alias IN p.aliases WHERE toLower(alias) = toLower($query))
           OR ANY(alias IN p.aliases WHERE toLower($query) CONTAINS toLower(alias))
        RETURN p.name AS name
        LIMIT 1
    """, {"query": query_name})
    
    if result:
        return result[0]["name"]
    
    return None


def main():
    print("="*70)
    print("FIXING PROCEDURE MATCHING")
    print("="*70)
    print()
    
    client = Neo4jClient()
    
    try:
        add_procedure_aliases(client)
        create_fuzzy_matching_index(client)
        
        print()
        print("="*70)
        print("✅ PROCEDURE MATCHING FIXED")
        print("="*70)
        print()
        
        # Test fuzzy matching
        print("Testing fuzzy matching:")
        test_queries = ["knee replacement", "angioplasty", "hip replacement"]
        for query in test_queries:
            match = find_procedure_fuzzy(client, query)
            print(f"  '{query}' -> '{match}'")
        
    except Exception as e:
        print()
        print("="*70)
        print("❌ FIX FAILED")
        print("="*70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    main()
