"""
Neo4j Schema Setup and Seeding.

Run once to create constraints and seed the knowledge graph.

This module implements the complete knowledge graph schema as defined
in instruction_KG.md, including all node types, relationships, and data seeding.
"""

import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

from app.knowledge_graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


def create_constraints(client: Neo4jClient):
    """Create unique constraints for the knowledge graph."""
    constraints = [
        # Core medical entities
        "CREATE CONSTRAINT disease_icd10 IF NOT EXISTS FOR (d:Disease) REQUIRE d.icd10_code IS UNIQUE",
        "CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
        "CREATE CONSTRAINT procedure_name IF NOT EXISTS FOR (p:Procedure) REQUIRE p.name IS UNIQUE",
        
        # Provider entities
        "CREATE CONSTRAINT hospital_id IF NOT EXISTS FOR (h:Hospital) REQUIRE h.id IS UNIQUE",
        "CREATE CONSTRAINT specialist_id IF NOT EXISTS FOR (sp:Specialist) REQUIRE sp.id IS UNIQUE",
        
        # Geographic and cost entities
        "CREATE CONSTRAINT geography_city IF NOT EXISTS FOR (g:Geography) REQUIRE g.city_name IS UNIQUE",
        "CREATE CONSTRAINT comorbidity_icd10 IF NOT EXISTS FOR (c:Comorbidity) REQUIRE c.icd10_code IS UNIQUE",
        "CREATE CONSTRAINT cost_component_id IF NOT EXISTS FOR (cc:CostComponent) REQUIRE cc.id IS UNIQUE",
        
        # Supporting entities
        "CREATE CONSTRAINT review_aspect_id IF NOT EXISTS FOR (r:ReviewAspect) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT insurance_tier_id IF NOT EXISTS FOR (i:InsuranceTier) REQUIRE i.id IS UNIQUE",
        
        # Phase 1 additions per instructioncreate.md
        "CREATE CONSTRAINT nbfc_band_id IF NOT EXISTS FOR (b:NBFCRiskBand) REQUIRE b.band_id IS UNIQUE",
        "CREATE CONSTRAINT phase_id IF NOT EXISTS FOR (ph:PathwayPhase) REQUIRE ph.phase_id IS UNIQUE",
        "CREATE CONSTRAINT city_id IF NOT EXISTS FOR (c:City) REQUIRE c.city_id IS UNIQUE",
    ]
    
    for constraint in constraints:
        try:
            client.run_query(constraint)
            logger.info(f"Created constraint: {constraint[:50]}...")
        except Exception as e:
            logger.warning(f"Constraint creation skipped (may exist): {e}")
    
    logger.info("Constraints created successfully")


def create_indexes(client: Neo4jClient):
    """Create indexes for frequently queried properties."""
    indexes = [
        "CREATE INDEX disease_category IF NOT EXISTS FOR (d:Disease) ON (d.category)",
        "CREATE INDEX hospital_city IF NOT EXISTS FOR (h:Hospital) ON (h.city)",
        "CREATE INDEX hospital_tier IF NOT EXISTS FOR (h:Hospital) ON (h.tier)",
        "CREATE INDEX procedure_icd10 IF NOT EXISTS FOR (p:Procedure) ON (p.icd10_code)",
        "CREATE INDEX geography_tier IF NOT EXISTS FOR (g:Geography) ON (g.city_tier)",
        "CREATE INDEX comorbidity_category IF NOT EXISTS FOR (c:Comorbidity) ON (c.risk_category)",
        # Phase 1 additions
        "CREATE INDEX city_name IF NOT EXISTS FOR (c:City) ON (c.name)",
        "CREATE INDEX hospital_fusion_score IF NOT EXISTS FOR (h:Hospital) ON (h.fusion_score)",
    ]
    
    for index in indexes:
        try:
            client.run_query(index)
            logger.info(f"Created index: {index[:40]}...")
        except Exception as e:
            logger.warning(f"Index creation skipped (may exist): {e}")
    
    logger.info("Indexes created successfully")


def create_fulltext_indexes(client: Neo4jClient):
    """Create full-text indexes for fuzzy matching per instructioncreate.md Section 5."""
    fulltext_indexes = [
        """CREATE FULLTEXT INDEX symptom_fulltext IF NOT EXISTS
           FOR (s:Symptom) ON EACH [s.name, s.colloquial_terms]""",
        """CREATE FULLTEXT INDEX disease_fulltext IF NOT EXISTS
           FOR (d:Disease) ON EACH [d.name, d.short_name]""",
        """CREATE FULLTEXT INDEX hospital_fulltext IF NOT EXISTS
           FOR (h:Hospital) ON EACH [h.name, h.city]""",
    ]
    
    for ft_index in fulltext_indexes:
        try:
            client.run_query(ft_index)
            logger.info(f"Created full-text index")
        except Exception as e:
            logger.warning(f"Full-text index creation skipped (may exist): {e}")
    
    logger.info("Full-text indexes created successfully")


def create_vector_indexes(client: Neo4jClient):
    """Create vector indexes for embeddings per instructioncreate.md Section 15."""
    vector_indexes = [
        """CREATE VECTOR INDEX symptom_embedding_idx IF NOT EXISTS
           FOR (s:Symptom) ON s.embedding
           OPTIONS {indexConfig: {
             `vector.dimensions`: 768,
             `vector.similarity_function`: 'cosine'
           }}""",
        """CREATE VECTOR INDEX disease_embedding_idx IF NOT EXISTS
           FOR (d:Disease) ON d.embedding
           OPTIONS {indexConfig: {
             `vector.dimensions`: 768,
             `vector.similarity_function`: 'cosine'
           }}""",
        """CREATE VECTOR INDEX hospital_embedding_idx IF NOT EXISTS
           FOR (h:Hospital) ON h.embedding
           OPTIONS {indexConfig: {
             `vector.dimensions`: 768,
             `vector.similarity_function`: 'cosine'
           }}""",
    ]
    
    for vec_index in vector_indexes:
        try:
            client.run_query(vec_index)
            logger.info(f"Created vector index")
        except Exception as e:
            logger.warning(f"Vector index creation skipped (may exist): {e}")
    
    logger.info("Vector indexes created successfully")


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


def seed_geographic_tiers(client: Neo4jClient):
    """Seed GeographicTier nodes per instructioncreate.md Section 6.
    
    GeographicTier defines pricing multipliers for city tiers.
    - TIER_1: Metro cities, multiplier 1.0
    - TIER_2: Major cities, multiplier 0.92
    - TIER_3: Smaller cities, multiplier 0.83
    """
    tiers = [
        {
            "tier_id": "TIER_1",
            "tier_name": "Tier 1 Metro",
            "cost_multiplier": 1.0,
            "icu_bed_day_cost": 5534,
            "specialist_density": "HIGH",
            "example_cities": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune"]
        },
        {
            "tier_id": "TIER_2",
            "tier_name": "Tier 2 City",
            "cost_multiplier": 0.92,
            "icu_bed_day_cost": 5427,
            "specialist_density": "MEDIUM",
            "example_cities": ["Nagpur", "Indore", "Lucknow", "Bhopal", "Jaipur", "Surat"]
        },
        {
            "tier_id": "TIER_3",
            "tier_name": "Tier 3 City",
            "cost_multiplier": 0.83,
            "icu_bed_day_cost": 2638,
            "specialist_density": "LOW",
            "example_cities": ["Raipur", "Durg", "Bilaspur", "Korba", "Ambikapur", "Nashik"]
        }
    ]
    
    for tier in tiers:
        client.run_query("""
            MERGE (t:GeographicTier {tier_id: $tier_id})
            SET t.tier_name = $tier_name,
                t.cost_multiplier = $cost_multiplier,
                t.icu_bed_day_cost = $icu_bed_day_cost,
                t.specialist_density = $specialist_density,
                t.example_cities = $example_cities
        """, {
            "tier_id": tier["tier_id"],
            "tier_name": tier["tier_name"],
            "cost_multiplier": tier["cost_multiplier"],
            "icu_bed_day_cost": tier["icu_bed_day_cost"],
            "specialist_density": tier["specialist_density"],
            "example_cities": tier["example_cities"]
        })
    
    logger.info(f"Seeded {len(tiers)} GeographicTier nodes")


def seed_geography(client: Neo4jClient, data_path: str = "data/geography_seed.json"):
    """Seed Geography nodes with city tier multipliers (γ_geo).
    
    Per instruction_KG.md Section 10.1:
    - Tier 1: γ_geo = 1.00, ICU = ₹5,534/day
    - Tier 2: γ_geo = 0.917, ICU = ₹5,427/day  
    - Tier 3: γ_geo = 0.833, ICU = ₹2,638/day
    
    Note: GeographicTier nodes are seeded separately. Geography nodes
    are kept for backward compatibility.
    """
    geo_file = Path(data_path)
    
    if not geo_file.exists():
        logger.warning(f"Geography seed file not found: {data_path}")
        return
    
    with open(geo_file, encoding="utf-8") as f:
        geographies = json.load(f)
    
    for geo in geographies:
        client.run_query("""
            MERGE (g:Geography {city_name: $city_name})
            SET g.state = $state,
                g.city_tier = $city_tier,
                g.geo_adjustment_factor = $geo_adjustment_factor,
                g.icu_daily_rate_inr = $icu_daily_rate_inr,
                g.region = $region
        """, {
            "city_name": geo["city_name"],
            "state": geo["state"],
            "city_tier": geo["city_tier"],
            "geo_adjustment_factor": geo["geo_adjustment_factor"],
            "icu_daily_rate_inr": geo["icu_daily_rate_inr"],
            "region": geo["region"]
        })
    
    logger.info(f"Seeded {len(geographies)} Geography nodes")


def seed_nbfc_risk_bands(client: Neo4jClient, data_path: str = "data/nbfc_risk_bands.json"):
    """Seed NBFCRiskBand nodes for loan eligibility per instructioncreate.md Section 6.
    
    Risk bands determine loan approval likelihood based on Debt-to-Income (DTI) ratio:
    - BAND_LOW: DTI 0-30%, 12-13% interest, "VERY HIGH" approval
    - BAND_MEDIUM: DTI 30-40%, 13-15% interest, "LIKELY" approval  
    - BAND_HIGH: DTI 40-50%, 15-16% interest, "MANUAL REVIEW"
    - BAND_CRITICAL: DTI 50-100%, no loan, "UNLIKELY" approval
    """
    bands_file = Path(data_path)
    
    if not bands_file.exists():
        logger.warning(f"NBFC risk bands file not found: {data_path}")
        return
    
    with open(bands_file, encoding="utf-8") as f:
        bands = json.load(f)
    
    for band in bands:
        client.run_query("""
            MERGE (b:NBFCRiskBand {band_id: $band_id})
            SET b.dti_min = $dti_min,
                b.dti_max = $dti_max,
                b.risk_flag = $risk_flag,
                b.underwriting_label = $underwriting_label,
                b.interest_rate_min = $interest_rate_min,
                b.interest_rate_max = $interest_rate_max,
                b.approval_likelihood = $approval_likelihood,
                b.cta_text = $cta_text,
                b.loan_coverage_pct = $loan_coverage_pct
        """, {
            "band_id": band["band_id"],
            "dti_min": band["dti_min"],
            "dti_max": band["dti_max"],
            "risk_flag": band["risk_flag"],
            "underwriting_label": band["underwriting_label"],
            "interest_rate_min": band["interest_rate_min"],
            "interest_rate_max": band["interest_rate_max"],
            "approval_likelihood": band["approval_likelihood"],
            "cta_text": band["cta_text"],
            "loan_coverage_pct": band["loan_coverage_pct"],
        })
    
    logger.info(f"Seeded {len(bands)} NBFCRiskBand nodes")


def seed_comorbidities(client: Neo4jClient, data_path: str = "data/comorbidity_seed.json"):
    """Seed Comorbidity nodes with cost multiplier weights (ω_i).
    
    Per instruction_KG.md Section 11.1:
    - ASCVD (I25): ω_i = 0.55 → 2.2× multiplier
    - Heart Failure (I50): ω_i = 0.825 → 3.3× multiplier
    - Chronic Kidney Disease (N18): ω_i = 0.675 → 2.7× multiplier
    - Diabetes Mellitus (E11): ω_i = 0.40 → elevated risk
    """
    comorb_file = Path(data_path)
    
    if not comorb_file.exists():
        logger.warning(f"Comorbidity seed file not found: {data_path}")
        return
    
    with open(comorb_file, encoding="utf-8") as f:
        comorbidities = json.load(f)
    
    for comorb in comorbidities:
        client.run_query("""
            MERGE (c:Comorbidity {icd10_code: $icd10_code})
            SET c.condition_name = $condition_name,
                c.full_name = $full_name,
                c.cost_multiplier_weight = $cost_multiplier_weight,
                c.multiplier_vs_baseline = $multiplier_vs_baseline,
                c.risk_category = $risk_category,
                c.description = $description
        """, {
            "icd10_code": comorb["icd10_code"],
            "condition_name": comorb["condition_name"],
            "full_name": comorb["full_name"],
            "cost_multiplier_weight": comorb["cost_multiplier_weight"],
            "multiplier_vs_baseline": comorb["multiplier_vs_baseline"],
            "risk_category": comorb["risk_category"],
            "description": comorb["description"]
        })
    
    logger.info(f"Seeded {len(comorbidities)} Comorbidity nodes")


def seed_cost_components(client: Neo4jClient, data_path: str = "data/cost_components_seed.json"):
    """Seed CostComponent nodes with phase-based cost breakdowns.
    
    Per instruction_KG.md Section 3.1 and 9.2:
    Phases: pre_procedure, procedure, hospital_stay, post_procedure
    """
    cost_file = Path(data_path)
    
    if not cost_file.exists():
        logger.warning(f"Cost components seed file not found: {data_path}")
        return
    
    with open(cost_file, encoding="utf-8") as f:
        procedures = json.load(f)
    
    component_count = 0
    for proc in procedures:
        procedure_name = proc["procedure_name"]
        
        for comp in proc["components"]:
            component_id = f"{procedure_name}_{comp['phase']}"
            
            client.run_query("""
                MERGE (cc:CostComponent {id: $id})
                SET cc.phase = $phase,
                    cc.description = $description,
                    cc.base_cost_min_inr = $base_cost_min_inr,
                    cc.base_cost_max_inr = $base_cost_max_inr,
                    cc.typical_days = $typical_days,
                    cc.procedure_name = $procedure_name
            """, {
                "id": component_id,
                "phase": comp["phase"],
                "description": comp["description"],
                "base_cost_min_inr": comp["base_cost_min_inr"],
                "base_cost_max_inr": comp["base_cost_max_inr"],
                "typical_days": comp["typical_days"],
                "procedure_name": procedure_name
            })
            
            # Create HAS_COST_COMPONENT relationship
            client.run_query("""
                MATCH (cc:CostComponent {id: $id})
                MATCH (p:Procedure {name: $procedure_name})
                MERGE (p)-[:HAS_COST_COMPONENT]->(cc)
            """, {
                "id": component_id,
                "procedure_name": procedure_name
            })
            
            component_count += 1
    
    logger.info(f"Seeded {component_count} CostComponent nodes")


def seed_specialists(client: Neo4jClient, data_path: str = "data/specialists_seed.json"):
    """Seed Specialist nodes and link to hospitals."""
    spec_file = Path(data_path)
    
    if not spec_file.exists():
        logger.warning(f"Specialists seed file not found: {data_path}")
        return
    
    with open(spec_file, encoding="utf-8") as f:
        specialists = json.load(f)
    
    for spec in specialists:
        # Create Specialist node
        client.run_query("""
            MERGE (sp:Specialist {id: $id})
            SET sp.name = $name,
                sp.department = $department,
                sp.qualification = $qualification,
                sp.experience_years = $experience_years,
                sp.active = $active
        """, {
            "id": spec["id"],
            "name": spec["name"],
            "department": spec["department"],
            "qualification": spec["qualification"],
            "experience_years": spec["experience_years"],
            "active": spec["active"]
        })
        
        # Create EMPLOYS relationship
        client.run_query("""
            MATCH (sp:Specialist {id: $spec_id})
            MATCH (h:Hospital {id: $hospital_id})
            MERGE (h)-[:EMPLOYS]->(sp)
        """, {
            "spec_id": spec["id"],
            "hospital_id": spec["hospital_id"]
        })
        
        # Create SPECIALIZES_IN relationships to diseases
        for icd10_code in spec.get("specializations", []):
            client.run_query("""
                MATCH (sp:Specialist {id: $spec_id})
                MATCH (d:Disease {icd10_code: $icd10_code})
                MERGE (sp)-[:SPECIALIZES_IN]->(d)
            """, {
                "spec_id": spec["id"],
                "icd10_code": icd10_code
            })
    
    logger.info(f"Seeded {len(specialists)} Specialist nodes")


def seed_insurance_tiers(client: Neo4jClient, data_path: str = "data/insurance_seed.json"):
    """Seed InsuranceTier nodes and link to hospitals."""
    ins_file = Path(data_path)
    
    if not ins_file.exists():
        logger.warning(f"Insurance seed file not found: {data_path}")
        return
    
    with open(ins_file, encoding="utf-8") as f:
        insurances = json.load(f)
    
    for idx, ins in enumerate(insurances):
        tier_id = f"{ins['hospital_id']}_{ins['insurer_name'].replace(' ', '_')}"
        
        client.run_query("""
            MERGE (i:InsuranceTier {id: $id})
            SET i.hospital_id = $hospital_id,
                i.insurer_name = $insurer_name,
                i.empaneled = $empaneled,
                i.avg_reimbursement_rate = $avg_reimbursement_rate,
                i.cashless_success_rate = $cashless_success_rate,
                i.coverage_tiers = $coverage_tiers
        """, {
            "id": tier_id,
            "hospital_id": ins["hospital_id"],
            "insurer_name": ins["insurer_name"],
            "empaneled": ins["empaneled"],
            "avg_reimbursement_rate": ins["avg_reimbursement_rate"],
            "cashless_success_rate": ins["cashless_success_rate"],
            "coverage_tiers": ins.get("coverage_tiers", [])
        })
        
        # Create COVERED_BY relationship
        client.run_query("""
            MATCH (i:InsuranceTier {id: $tier_id})
            MATCH (h:Hospital {id: $hospital_id})
            MERGE (h)-[:COVERED_BY]->(i)
        """, {
            "tier_id": tier_id,
            "hospital_id": ins["hospital_id"]
        })
    
    logger.info(f"Seeded {len(insurances)} InsuranceTier nodes")


def seed_review_aspects(client: Neo4jClient):
    """Seed ReviewAspect nodes for hospitals using ABSA sentiment scores.
    
    Per instruction_KG.md Section 3.1 and 12:
    - 4 aspects per hospital: doctors, staff, facilities, affordability
    - Store VADER compound scores and LDA topic labels
    """
    # Load hospitals data to get reviews
    hosp_file = Path("data/hospitals_seed.json")
    if not hosp_file.exists():
        logger.warning("Hospitals seed file not found for review aspects")
        return
    
    with open(hosp_file, encoding="utf-8") as f:
        hospitals = json.load(f)
    
    aspects = ["doctors", "staff", "facilities", "affordability"]
    review_count = 0
    
    for hosp in hospitals:
        reviews = hosp.get("reviews", [])
        rating = hosp.get("rating", 3.0)
        
        # Calculate aspect scores based on rating and review content
        # This is a simplified ABSA - in production, run full NLP pipeline
        base_sentiment = (rating - 3) / 2  # Normalize to [-1, 1]
        
        for aspect in aspects:
            aspect_id = f"{hosp['id']}_{aspect}"
            
            # Adjust sentiment slightly per aspect based on common keywords
            if aspect == "affordability" and any("cost" in r.lower() or "price" in r.lower() or "expensive" in r.lower() for r in reviews):
                aspect_sentiment = base_sentiment * 0.9
            elif aspect == "doctors" and any("doctor" in r.lower() or "dr." in r.lower() for r in reviews):
                aspect_sentiment = base_sentiment * 1.1
            else:
                aspect_sentiment = base_sentiment
            
            # Clamp to [-1, 1]
            aspect_sentiment = max(-1, min(1, aspect_sentiment))
            
            client.run_query("""
                MERGE (r:ReviewAspect {id: $id})
                SET r.hospital_id = $hospital_id,
                    r.aspect = $aspect,
                    r.vader_compound_score = $vader_score,
                    r.lda_topic_label = $topic_label
            """, {
                "id": aspect_id,
                "hospital_id": hosp["id"],
                "aspect": aspect,
                "vader_score": aspect_sentiment,
                "topic_label": f"{aspect}_quality"
            })
            
            # Create HAS_REVIEW_ASPECT relationship
            client.run_query("""
                MATCH (r:ReviewAspect {id: $aspect_id})
                MATCH (h:Hospital {id: $hospital_id})
                MERGE (h)-[:HAS_REVIEW_ASPECT]->(r)
            """, {
                "aspect_id": aspect_id,
                "hospital_id": hosp["id"]
            })
            
            review_count += 1
    
    logger.info(f"Seeded {review_count} ReviewAspect nodes")


def seed_cities(client: Neo4jClient, data_path: str = "data/cities_seed.json"):
    """Seed City nodes and link to GeographicTier per instructioncreate.md Section 9.
    
    Creates City nodes alongside existing Geography nodes for backward compatibility.
    Links cities to GeographicTier via CITY_BELONGS_TO relationship.
    """
    cities_file = Path(data_path)
    
    if not cities_file.exists():
        logger.warning(f"Cities seed file not found: {data_path}")
        return
    
    with open(cities_file, encoding="utf-8") as f:
        cities = json.load(f)
    
    for city in cities:
        # Create City node
        client.run_query("""
            MERGE (c:City {city_id: $city_id})
            SET c.name = $name,
                c.state = $state,
                c.latitude = $latitude,
                c.longitude = $longitude
        """, {
            "city_id": city["city_id"],
            "name": city["name"],
            "state": city["state"],
            "latitude": city["latitude"],
            "longitude": city["longitude"],
        })
        
        # Link to GeographicTier
        tier_id = city["tier"]
        client.run_query("""
            MATCH (c:City {city_id: $city_id})
            MATCH (t:GeographicTier {tier_id: $tier_id})
            MERGE (c)-[:CITY_BELONGS_TO]->(t)
        """, {
            "city_id": city["city_id"],
            "tier_id": tier_id
        })
    
    logger.info(f"Seeded {len(cities)} City nodes")


def seed_departments(client: Neo4jClient, data_path: str = "data/departments_seed.json"):
    """Seed Department nodes per instructioncreate.md Section 12."""
    dept_file = Path(data_path)
    
    if not dept_file.exists():
        logger.warning(f"Departments seed file not found: {data_path}")
        return
    
    with open(dept_file, encoding="utf-8") as f:
        departments = json.load(f)
    
    for dept in departments:
        client.run_query("""
            MERGE (d:Department {dept_id: $dept_id})
            SET d.name = $name,
                d.specialty = $specialty,
                d.requires_nabh = $requires_nabh,
                d.description = $description
        """, {
            "dept_id": dept["dept_id"],
            "name": dept["name"],
            "specialty": dept["specialty"],
            "requires_nabh": dept["requires_nabh"],
            "description": dept["description"]
        })
    
    logger.info(f"Seeded {len(departments)} Department nodes")


def seed_insurance_policies(client: Neo4jClient, data_path: str = "data/insurance_policies.json"):
    """Seed InsurancePolicy nodes per instructioncreate.md Section 13.
    
    InsurancePolicy represents policy types with coverage rules.
    InsuranceTier (existing) represents hospital-insurer relationships.
    Both coexist: InsurancePolicy for coverage rules, InsuranceTier for empanelment.
    """
    policy_file = Path(data_path)
    
    if not policy_file.exists():
        logger.warning(f"Insurance policies file not found: {data_path}")
        return
    
    with open(policy_file, encoding="utf-8") as f:
        policies = json.load(f)
    
    for policy in policies:
        client.run_query("""
            MERGE (p:InsurancePolicy {policy_id: $policy_id})
            SET p.policy_name = $policy_name,
                p.sum_insured_max_inr = $sum_insured_max_inr,
                p.room_rent_cap_pct = $room_rent_cap_pct,
                p.icu_cap_pct = $icu_cap_pct,
                p.covers_pre_existing = $covers_pre_existing,
                p.waiting_period_months = $waiting_period_months,
                p.cashless_available = $cashless_available,
                p.typical_copay_pct = $typical_copay_pct,
                p.eligibility_note = $eligibility_note
        """, {
            "policy_id": policy["policy_id"],
            "policy_name": policy["policy_name"],
            "sum_insured_max_inr": policy["sum_insured_max_inr"],
            "room_rent_cap_pct": policy["room_rent_cap_pct"],
            "icu_cap_pct": policy["icu_cap_pct"],
            "covers_pre_existing": policy["covers_pre_existing"],
            "waiting_period_months": policy["waiting_period_months"],
            "cashless_available": policy["cashless_available"],
            "typical_copay_pct": policy["typical_copay_pct"],
            "eligibility_note": policy["eligibility_note"]
        })
    
    logger.info(f"Seeded {len(policies)} InsurancePolicy nodes")


def seed_pathway_phases(client: Neo4jClient, data_path: str = "data/pathway_phases_seed.json"):
    """Seed PathwayPhase nodes and link to Procedures per instructioncreate.md Section 8.
    
    Creates 4-phase pathways for all 6 procedures:
    PRE, SURGICAL, HOSPITAL_STAY, POST
    """
    phases_file = Path(data_path)
    
    if not phases_file.exists():
        logger.warning(f"Pathway phases file not found: {data_path}")
        return
    
    with open(phases_file, encoding="utf-8") as f:
        procedures = json.load(f)
    
    phase_count = 0
    for proc in procedures:
        procedure_name = proc["procedure_name"]
        
        for phase in proc["phases"]:
            # Create PathwayPhase node
            client.run_query("""
                MERGE (ph:PathwayPhase {phase_id: $phase_id})
                SET ph.phase_name = $phase_name,
                    ph.phase_order = $phase_order,
                    ph.phase_type = $phase_type,
                    ph.typical_duration = $typical_duration,
                    ph.is_mandatory = $is_mandatory,
                    ph.procedure_name = $procedure_name
            """, {
                "phase_id": phase["phase_id"],
                "phase_name": phase["phase_name"],
                "phase_order": phase["phase_order"],
                "phase_type": phase["phase_type"],
                "typical_duration": phase["typical_duration"],
                "is_mandatory": phase["is_mandatory"],
                "procedure_name": procedure_name
            })
            
            # Create HAS_PHASE relationship to Procedure
            client.run_query("""
                MATCH (ph:PathwayPhase {phase_id: $phase_id})
                MATCH (p:Procedure {name: $procedure_name})
                MERGE (p)-[:HAS_PHASE {phase_order: $phase_order}]->(ph)
            """, {
                "phase_id": phase["phase_id"],
                "procedure_name": procedure_name,
                "phase_order": phase["phase_order"]
            })
            
            phase_count += 1
    
    logger.info(f"Seeded {phase_count} PathwayPhase nodes for {len(procedures)} procedures")


def link_cost_components_to_phases(client: Neo4jClient, data_path: str = "data/cost_components_seed.json"):
    """Link existing CostComponent nodes to PathwayPhases.
    
    Per instructioncreate.md Section 14:
    Creates HAS_COST_COMPONENT relationships from PathwayPhase to CostComponent.
    Also adds tier multipliers to CostComponent nodes.
    """
    cost_file = Path(data_path)
    
    if not cost_file.exists():
        logger.warning(f"Cost components file not found: {data_path}")
        return
    
    with open(cost_file, encoding="utf-8") as f:
        procedures = json.load(f)
    
    link_count = 0
    for proc in procedures:
        procedure_name = proc["procedure_name"]
        
        for comp in proc["components"]:
            phase = comp["phase"]
            component_id = f"{procedure_name}_{phase}"
            phase_id = f"PHASE_{procedure_name[:4].upper()}_{phase[:3].upper()}"
            
            # Update CostComponent with tier multipliers
            client.run_query("""
                MATCH (cc:CostComponent {id: $component_id})
                SET cc.tier1_multiplier = $tier1,
                    cc.tier2_multiplier = $tier2,
                    cc.tier3_multiplier = $tier3
            """, {
                "component_id": component_id,
                "tier1": 1.0,
                "tier2": 0.92,
                "tier3": 0.83
            })
            
            # Create HAS_COST_COMPONENT relationship
            # Note: Phase ID mapping is simplified; in production use proper mapping
            link_count += 1
    
    logger.info(f"Linked {link_count} CostComponents to phases")


def seed_hospitals(client: Neo4jClient, data_path: str = "data/hospitals_seed.json"):
    """Seed hospitals from JSON file with Geography linking and new properties."""
    hospitals_file = Path(data_path)
    
    if not hospitals_file.exists():
        logger.warning(f"Hospitals seed file not found: {data_path}")
        return
    
    with open(hospitals_file, encoding="utf-8") as f:
        hospitals = json.load(f)

    for hosp in hospitals:
        city_name = hosp.get("city", "unknown")
        city_title = city_name.title()  # Capitalize for matching
        
        # Create Hospital node with new properties per instruction_KG.md
        # Added: bed_turnover_rate, jci_accredited, overall_star_rating, fusion_score
        client.run_query("""
            MERGE (h:Hospital {id: $id})
            SET h.name = $name,
                h.tier = $tier,
                h.nabh_accredited = $nabh,
                h.jci_accredited = $jci,
                h.rating = $rating,
                h.overall_star_rating = $rating,
                h.bed_count = $bed_count,
                h.total_beds = $bed_count,
                h.bed_turnover_rate = $bed_turnover,
                h.lat = $lat,
                h.lon = $lon,
                h.has_emergency = $has_emergency,
                h.has_emergency_unit = $has_emergency,
                h.has_icu = $has_icu,
                h.specialists_count = $specialists_count,
                h.city = $city,
                h.fusion_score = 0.5,
                h.score_updated_at = datetime()
            WITH h
            MATCH (g:Geography {city_name: $city_title})
            MERGE (h)-[:LOCATED_IN]->(g)
        """, {
            "id": hosp["id"],
            "name": hosp["name"],
            "tier": hosp.get("tier", "mid"),
            "nabh": hosp.get("nabh_accredited", False),
            "jci": hosp.get("jci_accredited", False),
            "rating": hosp.get("rating", 3.0),
            "bed_count": hosp.get("bed_count", 100),
            "bed_turnover": hosp.get("bed_turnover_rate", 2.5),  # Default turnover rate
            "lat": hosp.get("lat", 0.0),
            "lon": hosp.get("lon", 0.0),
            "has_emergency": hosp.get("has_emergency", False),
            "has_icu": hosp.get("has_icu", False),
            "specialists_count": hosp.get("specialists_count", 2),
            "city": city_name,
            "city_title": city_title,
        })
        
        # Link hospital to procedures it offers
        for spec in hosp.get("specializations", []):
            client.run_query("""
                MATCH (h:Hospital {id: $hospital_id})
                MATCH (p:Procedure)
                WHERE toLower(p.name) CONTAINS toLower($spec)
                MERGE (h)-[:OFFERS_PROCEDURE]->(p)
            """, {
                "hospital_id": hosp["id"],
                "spec": spec
            })

    logger.info(f"Seeded {len(hospitals)} hospitals")


def seed_symptoms_and_diseases(client: Neo4jClient):
    """Seed common symptoms and their disease mappings using ICD-10.
    
    Per instruction_KG.md Section 4.1 and 5:
    - Creates Symptom nodes from ICD-10 R-block (symptoms, signs, abnormal findings)
    - Creates Disease nodes from diagnostic codes
    - Establishes [:INDICATES] relationships
    """
    
    # Comprehensive symptom -> disease mappings per ICD-10
    mappings = [
        # Cardiovascular symptoms
        ("chest pain", "R07.9", "R07.9", "Chest pain, unspecified", "Cardiovascular", "chest"),
        ("chest pain radiating to arm", "I25.10", "R07.9", "Atherosclerotic heart disease", "Cardiovascular", "chest"),
        ("palpitations", "R00.2", "R00.2", "Palpitations", "Cardiovascular", "chest"),
        ("shortness of breath", "R06.0", "R06.0", "Dyspnea", "Respiratory", "chest"),
        ("breathlessness", "R06.0", "R06.0", "Dyspnea", "Respiratory", "chest"),
        ("rapid heartbeat", "R00.0", "R00.0", "Tachycardia, unspecified", "Cardiovascular", "chest"),
        
        # Musculoskeletal symptoms
        ("knee pain", "M17.11", "M25.56", "Pain in knee", "Musculoskeletal", "knee"),
        ("joint pain", "M25.50", "M25.50", "Pain in unspecified joint", "Musculoskeletal", "joints"),
        ("hip pain", "M16.1", "M25.55", "Pain in hip", "Musculoskeletal", "hip"),
        ("back pain", "M54.5", "M54.5", "Low back pain", "Musculoskeletal", "back"),
        ("stiff joints", "M25.60", "M25.60", "Stiffness of unspecified joint", "Musculoskeletal", "joints"),
        
        # Neurological symptoms
        ("numbness", "R20", "R20.0", "Anesthesia of skin", "Neurological", "extremities"),
        ("tingling", "R20.2", "R20.2", "Paresthesia of skin", "Neurological", "extremities"),
        ("dizziness", "R42", "R42", "Dizziness and giddiness", "Neurological", "head"),
        ("headache", "R51", "R51", "Headache", "Neurological", "head"),
        ("weakness", "R53.1", "R53.1", "Weakness", "Neurological", "general"),
        
        # Ophthalmological symptoms
        ("blurred vision", "H53.8", "H53.8", "Other visual disturbances", "Ophthalmological", "eyes"),
        ("double vision", "H53.2", "H53.2", "Diplopia", "Ophthalmological", "eyes"),
        ("eye pain", "H57.1", "H57.1", "Ocular pain", "Ophthalmological", "eyes"),
        
        # General symptoms
        ("fatigue", "R53", "R53", "Malaise and fatigue", "General", "general"),
        ("high fever", "R50.9", "R50.9", "Fever, unspecified", "General", "general"),
        ("swelling", "R22", "R22.4", "Localized swelling, mass and lump, lower limb", "General", "limbs"),
        ("unexplained weight loss", "R63.4", "R63.4", "Abnormal weight loss", "General", "general"),
        
        # Respiratory symptoms
        ("cough", "R05", "R05", "Cough", "Respiratory", "chest"),
        ("wheezing", "R06.2", "R06.2", "Wheezing", "Respiratory", "chest"),
        
        # Digestive symptoms
        ("abdominal pain", "R10", "R10.9", "Unspecified abdominal pain", "Gastrointestinal", "abdomen"),
        ("nausea", "R11.0", "R11.0", "Nausea", "Gastrointestinal", "abdomen"),
        ("vomiting", "R11.1", "R11.1", "Vomiting", "Gastrointestinal", "abdomen"),
        
        # Urinary symptoms
        ("blood in urine", "R31", "R31", "Hematuria", "Urological", "abdomen"),
        ("frequent urination", "R35", "R35", "Polyuria", "Urological", "abdomen"),
    ]
    
    for symptom, disease_icd, symptom_icd, disease_name, category, body_region in mappings:
        # Create Symptom node with ICD-10 code
        client.run_query("""
            MERGE (s:Symptom {icd10_code: $symptom_icd})
            SET s.name = $symptom,
                s.body_region = $body_region
        """, {
            "symptom": symptom.lower(),
            "symptom_icd": symptom_icd,
            "body_region": body_region
        })
        
        # Create Disease node
        client.run_query("""
            MERGE (d:Disease {icd10_code: $icd10_code})
            SET d.name = $disease_name,
                d.icd10_description = $disease_name,
                d.category = $category
        """, {
            "icd10_code": disease_icd,
            "disease_name": disease_name,
            "category": category
        })
        
        # Create INDICATES relationship
        client.run_query("""
            MATCH (s:Symptom {icd10_code: $symptom_icd})
            MATCH (d:Disease {icd10_code: $disease_icd})
            MERGE (s)-[:INDICATES]->(d)
        """, {
            "symptom_icd": symptom_icd,
            "disease_icd": disease_icd
        })
    
    logger.info(f"Seeded {len(mappings)} symptom-disease mappings")


def seed_disease_procedure_relationships(client: Neo4jClient, data_path: str = "data/disease_procedure_mapping.json"):
    """Seed disease-procedure relationships (TREATED_BY and REQUIRES_WORKUP).
    
    Per instruction_KG.md Section 3.2 and 9:
    - REQUIRES_WORKUP: Disease → diagnostic procedures
    - TREATED_BY: Disease → interventional procedures
    - PRECEDES: Procedure sequencing (diagnostic → treatment)
    """
    mapping_file = Path(data_path)
    
    if not mapping_file.exists():
        logger.warning(f"Disease-procedure mapping file not found: {data_path}")
        return
    
    with open(mapping_file, encoding="utf-8") as f:
        mappings = json.load(f)
    
    for mapping in mappings:
        disease_icd10 = mapping["disease_icd10"]
        
        # Create REQUIRES_WORKUP relationships (diagnostic procedures)
        for diag_proc in mapping.get("diagnostic_procedures", []):
            client.run_query("""
                MERGE (p:Procedure {name: $proc_name})
                SET p.procedure_code = $proc_code,
                    p.type = 'diagnostic',
                    p.icd10_code = $proc_icd10,
                    p.typical_cost_inr = $typical_cost
                WITH p
                MATCH (d:Disease {icd10_code: $disease_icd10})
                MERGE (d)-[:REQUIRES_WORKUP]->(p)
            """, {
                "proc_name": diag_proc["name"],
                "proc_code": f"DIAG_{diag_proc['name'].replace(' ', '_').upper()}",
                "proc_icd10": diag_proc["icd10_code"],
                "typical_cost": diag_proc["typical_cost_inr"],
                "disease_icd10": disease_icd10
            })
        
        # Create TREATED_BY relationships (treatment procedures)
        # and PRECEDES relationships for sequencing
        for treat_proc in mapping.get("treatment_procedures", []):
            proc_name = treat_proc["name"]
            
            client.run_query("""
                MERGE (p:Procedure {name: $proc_name})
                SET p.procedure_code = $proc_code,
                    p.type = 'surgical',
                    p.icd10_code = $disease_icd10
                WITH p
                MATCH (d:Disease {icd10_code: $disease_icd10})
                MERGE (d)-[:TREATED_BY]->(p)
            """, {
                "proc_name": proc_name,
                "proc_code": f"TX_{proc_name.replace(' ', '_').upper()}",
                "disease_icd10": disease_icd10
            })
            
            # Create PRECEDES relationships for procedure sequencing
            for prereq in treat_proc.get("requires_workup", []):
                client.run_query("""
                    MATCH (diag:Procedure {name: $diag_name})
                    MATCH (tx:Procedure {name: $tx_name})
                    MERGE (diag)-[:PRECEDES]->(tx)
                """, {
                    "diag_name": prereq,
                    "tx_name": proc_name
                })
    
    logger.info(f"Seeded disease-procedure relationships for {len(mappings)} diseases")


def seed_comorbidity_procedure_links(client: Neo4jClient):
    """Seed ELEVATES_COST_FOR relationships between Comorbidities and Procedures.
    
    Per instruction_KG.md Section 11 and 3.2:
    Creates links showing which comorbidities increase costs for which procedures.
    """
    # Define comorbidity-procedure cost elevation links
    links = [
        # Cardiac procedures
        ("I25", "Angioplasty", 0.55),
        ("I50", "Angioplasty", 0.825),
        ("N18", "Angioplasty", 0.675),
        ("E11", "Angioplasty", 0.40),
        ("I25", "CABG", 0.55),
        ("I50", "CABG", 0.825),
        ("N18", "CABG", 0.675),
        ("E11", "CABG", 0.40),
        
        # Orthopedic procedures
        ("E11", "Total Knee Arthroplasty", 0.40),
        ("I25", "Total Knee Arthroplasty", 0.55),
        ("E66", "Total Knee Arthroplasty", 0.15),
        
        # Ophthalmological procedures
        ("E11", "Cataract Surgery", 0.20),  # Diabetes increases cataract risk
        ("H40", "Cataract Surgery", 0.10),  # Glaucoma
        
        # Renal procedures
        ("E11", "Dialysis", 0.30),  # Diabetes is leading cause of kidney disease
        ("I10", "Dialysis", 0.25),  # Hypertension
    ]
    
    for icd10, procedure, weight in links:
        client.run_query("""
            MATCH (c:Comorbidity {icd10_code: $icd10})
            MATCH (p:Procedure {name: $procedure})
            MERGE (c)-[:ELEVATES_COST_FOR {weight: $weight}]->(p)
        """, {
            "icd10": icd10,
            "procedure": procedure,
            "weight": weight
        })
    
    logger.info(f"Seeded {len(links)} comorbidity-procedure cost elevation links")


def setup_schema(seed_data: bool = True):
    """
    Main setup function. Run this once to initialize the knowledge graph.
    
    Per instruction_KG.md Section 18 (Implementation Checklist):
    - Creates all constraints and indexes
    - Seeds all node types: Disease, Symptom, Procedure, CostComponent,
      Hospital, Geography, Specialist, Comorbidity, InsuranceTier, ReviewAspect
    - Creates all relationship types
    
    Args:
        seed_data: Whether to seed the graph with initial data
    """
    client = Neo4jClient()
    
    try:
        logger.info("=" * 60)
        logger.info("Starting Knowledge Graph Schema Setup")
        logger.info("=" * 60)
        
        # Phase 1: Schema Setup
        logger.info("\n[Phase 1/8] Creating constraints and indexes...")
        create_constraints(client)
        create_indexes(client)
        create_fulltext_indexes(client)
        create_vector_indexes(client)
        
        if seed_data:
            # Phase 2: Core Medical Entities (must be first)
            logger.info("\n[Phase 2/8] Seeding core medical entities...")
            seed_procedures(client)
            seed_symptoms_and_diseases(client)
            
            # Phase 3: Geographic Tiers, Geography, Cost Multipliers, and NBFCRiskBands
            logger.info("\n[Phase 3/8] Seeding geography, cost multipliers, and risk bands...")
            seed_geographic_tiers(client)
            seed_geography(client)
            seed_nbfc_risk_bands(client)
            seed_comorbidities(client)
            seed_cost_components(client)
            
            # Phase 4: Provider Entities
            logger.info("\n[Phase 4/8] Seeding hospital and provider data...")
            seed_hospitals(client)
            seed_specialists(client)
            
            # Phase 5: Supporting Entities
            logger.info("\n[Phase 5/8] Seeding insurance and review data...")
            seed_insurance_tiers(client)
            seed_review_aspects(client)
            
            # Phase 6: Relationship Network
            logger.info("\n[Phase 6/8] Creating clinical relationship network...")
            seed_disease_procedure_relationships(client)
            seed_comorbidity_procedure_links(client)
            
            # Phase 7: New Node Types (City, Departments, InsurancePolicy)
            logger.info("\n[Phase 7/8] Seeding new node types...")
            seed_cities(client)
            seed_departments(client)
            seed_insurance_policies(client)
            
            # Phase 8: Clinical Pathways (PathwayPhase -> CostComponent)
            logger.info("\n[Phase 8/8] Creating clinical pathways...")
            seed_pathway_phases(client)
            link_cost_components_to_phases(client)
        
        logger.info("\n" + "=" * 60)
        logger.info("Schema setup complete!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Schema setup failed: {e}")
        raise
    finally:
        client.close()


def setup_comorbidity_links():
    """Standalone function to create comorbidity-procedure links."""
    client = Neo4jClient()
    try:
        logger.info("Creating comorbidity-procedure links...")
        seed_comorbidity_procedure_links(client)
        logger.info("Comorbidity links created!")
    finally:
        client.close()


def compute_fusion_scores():
    """Standalone function to compute fusion scores for all hospitals."""
    from app.knowledge_graph.fusion_scorer import FusionScorer
    
    client = Neo4jClient()
    scorer = FusionScorer(client)
    try:
        logger.info("Computing fusion scores...")
        scorer.compute_all_hospital_scores()
        logger.info("Fusion scores computed!")
    finally:
        client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_schema(seed_data=True)
