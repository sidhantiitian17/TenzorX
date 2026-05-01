#!/usr/bin/env python
"""
Neo4j Data Seeding Script

Seeds the Neo4j knowledge graph with:
- Procedures and cost benchmarks
- Hospitals and their locations
- Geography and city tiers
- Cost components and pathway phases
- Disease and symptom mappings

Usage:
    python seed_neo4j_data.py
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the schema setup with data seeding."""
    print("="*70)
    print("NEO4J DATA SEEDING")
    print("="*70)
    print()
    
    try:
        from app.knowledge_graph.schema_setup import setup_schema
        from app.core.config import settings
        
        print(f"Neo4j URI: {settings.NEO4J_URI}")
        print(f"Neo4j User: {settings.NEO4J_USER}")
        print()
        
        print("Starting schema setup with data seeding...")
        print("This may take 2-3 minutes...")
        print()
        
        setup_schema(seed_data=True)
        
        print()
        print("="*70)
        print("✅ DATA SEEDING COMPLETE")
        print("="*70)
        print()
        print("Seeded data includes:")
        print("  - Procedures with cost benchmarks")
        print("  - Hospitals with locations")
        print("  - Geography and city tiers")
        print("  - Cost components")
        print("  - Disease and symptom mappings")
        print("  - Insurance tiers and review aspects")
        print()
        print("You can now run queries with real data!")
        
    except Exception as e:
        print()
        print("="*70)
        print("❌ DATA SEEDING FAILED")
        print("="*70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
