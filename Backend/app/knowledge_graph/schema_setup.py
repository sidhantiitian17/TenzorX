"""
Neo4j Schema Setup and Seeding.

Run once to create constraints and seed the knowledge graph.
"""

import json
import os
import logging
from pathlib import Path

from app.knowledge_graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


def create_constraints(client: Neo4jClient):
    """Create unique constraints for the knowledge graph."""
    constraints = [
        "CREATE CONSTRAINT condition_icd10 IF NOT EXISTS FOR (c:Condition) REQUIRE c.icd10_code IS UNIQUE",
        "CREATE CONSTRAINT hospital_id IF NOT EXISTS FOR (h:Hospital) REQUIRE h.id IS UNIQUE",
        "CREATE CONSTRAINT procedure_name IF NOT EXISTS FOR (p:Procedure) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT city_name IF NOT EXISTS FOR (ci:City) REQUIRE ci.name IS UNIQUE",
        "CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
    ]
    
    for constraint in constraints:
        try:
            client.run_query(constraint)
            logger.info(f"Created constraint: {constraint[:50]}...")
        except Exception as e:
            logger.warning(f"Constraint creation skipped (may exist): {e}")
    
    logger.info("Constraints created successfully")


def seed_procedures(client: Neo4jClient, data_path: str = "data/procedure_benchmarks.json"):
    """Seed procedures and cost benchmarks from JSON file."""
    benchmarks_file = Path(data_path)
    
    if not benchmarks_file.exists():
        logger.warning(f"Procedure benchmarks file not found: {data_path}")
        return
    
    with open(benchmarks_file, encoding="utf-8") as f:
        benchmarks = json.load(f)

    for proc in benchmarks:
        # Create Procedure node
        client.run_query("""
            MERGE (p:Procedure {name: $name})
            SET p.icd10_code = $icd10_code,
                p.typical_duration_hrs = $duration_hrs,
                p.hospital_stay_days = $stay_days
        """, {
            "name": proc["procedure"],
            "icd10_code": proc.get("icd10_code", ""),
            "duration_hrs": proc.get("duration_hrs", 2),
            "stay_days": proc.get("stay_days", "1-2")
        })

        # Create City nodes and CostBenchmark relationships
        for tier, costs in proc.get("city_tier", {}).items():
            # Create/merge City node
            client.run_query("""
                MERGE (ci:City {name: $tier})
                SET ci.tier = $tier
            """, {"tier": tier})
            
            # Create CostBenchmark with relationships
            client.run_query("""
                MERGE (cb:CostBenchmark {procedure: $name, city_tier: $tier})
                SET cb.min_inr = $min_inr,
                    cb.max_inr = $max_inr,
                    cb.typical_inr = $typical_inr
                WITH cb
                MATCH (p:Procedure {name: $name})
                MATCH (ci:City {name: $tier})
                MERGE (cb)-[:BENCHMARKS]->(p)
                MERGE (cb)-[:FOR_CITY]->(ci)
            """, {
                "name": proc["procedure"],
                "tier": tier,
                "min_inr": costs.get("min", 0),
                "max_inr": costs.get("max", 0),
                "typical_inr": costs.get("typical", 0),
            })

    logger.info(f"Seeded {len(benchmarks)} procedures")


def seed_hospitals(client: Neo4jClient, data_path: str = "data/hospitals_seed.json"):
    """Seed hospitals from JSON file."""
    hospitals_file = Path(data_path)
    
    if not hospitals_file.exists():
        logger.warning(f"Hospitals seed file not found: {data_path}")
        return
    
    with open(hospitals_file, encoding="utf-8") as f:
        hospitals = json.load(f)

    for hosp in hospitals:
        # Create City if not exists
        city_name = hosp.get("city", "unknown")
        client.run_query("""
            MERGE (ci:City {name: $city})
            SET ci.tier = $city_tier
        """, {
            "city": city_name,
            "city_tier": hosp.get("tier", "mid")
        })
        
        # Create Hospital node
        client.run_query("""
            MERGE (h:Hospital {id: $id})
            SET h.name = $name,
                h.tier = $tier,
                h.nabh = $nabh,
                h.rating = $rating,
                h.bed_count = $bed_count,
                h.lat = $lat,
                h.lon = $lon,
                h.has_emergency = $has_emergency,
                h.has_icu = $has_icu,
                h.specialists_count = $specialists_count
            WITH h
            MATCH (ci:City {name: $city})
            MERGE (h)-[:LOCATED_IN]->(ci)
        """, {
            "id": hosp["id"],
            "name": hosp["name"],
            "tier": hosp.get("tier", "mid"),
            "nabh": hosp.get("nabh_accredited", False),
            "rating": hosp.get("rating", 3.0),
            "bed_count": hosp.get("bed_count", 100),
            "lat": hosp.get("lat", 0.0),
            "lon": hosp.get("lon", 0.0),
            "has_emergency": hosp.get("has_emergency", False),
            "has_icu": hosp.get("has_icu", False),
            "specialists_count": hosp.get("specialists_count", 2),
            "city": city_name,
        })
        
        # Link hospital to procedures it performs
        for spec in hosp.get("specializations", []):
            client.run_query("""
                MATCH (h:Hospital {id: $hospital_id})
                MATCH (p:Procedure)
                WHERE p.name CONTAINS $spec
                MERGE (p)<-[:PERFORMED_AT]-(h)
            """, {
                "hospital_id": hosp["id"],
                "spec": spec.lower()
            })

    logger.info(f"Seeded {len(hospitals)} hospitals")


def seed_symptoms_and_conditions(client: Neo4jClient):
    """Seed common symptoms and their condition mappings."""
    
    # Common symptom -> condition mappings
    mappings = [
        ("chest pain", "I25.10", "Atherosclerotic heart disease", "Cardiovascular"),
        ("breathlessness", "R06.0", "Dyspnea", "Respiratory"),
        ("shortness of breath", "R06.0", "Dyspnea", "Respiratory"),
        ("knee pain", "M17.1", "Osteoarthritis of knee", "Musculoskeletal"),
        ("hip pain", "M16.1", "Osteoarthritis of hip", "Musculoskeletal"),
        ("back pain", "M54.5", "Low back pain", "Musculoskeletal"),
        ("blurred vision", "H53.8", "Visual disturbances", "Ophthalmological"),
        ("high fever", "R50.9", "Fever, unspecified", "General"),
        ("fatigue", "R53", "Malaise and fatigue", "General"),
        ("swelling", "R22", "Localized swelling", "General"),
        ("numbness", "R20", "Disturbances of skin sensation", "Neurological"),
        ("palpitations", "R00.2", "Palpitations", "Cardiovascular"),
        ("dizziness", "R42", "Dizziness and giddiness", "Neurological"),
    ]
    
    for symptom, icd10_code, icd10_label, category in mappings:
        # Create Symptom node
        client.run_query("""
            MERGE (s:Symptom {name: $symptom})
        """, {"symptom": symptom.lower()})
        
        # Create Condition node
        client.run_query("""
            MERGE (c:Condition {icd10_code: $icd10_code})
            SET c.icd10_label = $icd10_label,
                c.category = $category
        """, {
            "icd10_code": icd10_code,
            "icd10_label": icd10_label,
            "category": category
        })
        
        # Create INDICATES relationship
        client.run_query("""
            MATCH (s:Symptom {name: $symptom})
            MATCH (c:Condition {icd10_code: $icd10_code})
            MERGE (s)-[:INDICATES]->(c)
        """, {
            "symptom": symptom.lower(),
            "icd10_code": icd10_code
        })
    
    logger.info(f"Seeded {len(mappings)} symptom-condition mappings")


def setup_schema(seed_data: bool = True):
    """
    Main setup function. Run this once to initialize the knowledge graph.
    
    Args:
        seed_data: Whether to seed the graph with initial data
    """
    client = Neo4jClient()
    
    try:
        logger.info("Starting Neo4j schema setup...")
        create_constraints(client)
        
        if seed_data:
            seed_procedures(client)
            seed_hospitals(client)
            seed_symptoms_and_conditions(client)
        
        logger.info("Schema setup complete!")
        
    except Exception as e:
        logger.error(f"Schema setup failed: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_schema(seed_data=True)
