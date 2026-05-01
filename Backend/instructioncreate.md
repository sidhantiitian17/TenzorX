# Neo4j Knowledge Graph: Creation & Population Instructions
## Healthcare AI Navigator & Cost Estimator (GraphRAG Backend)

---

## Table of Contents

1. [Overview & Architecture Philosophy](#1-overview--architecture-philosophy)
2. [Prerequisites & Environment Setup](#2-prerequisites--environment-setup)
3. [Schema Design: Node Labels & Properties](#3-schema-design-node-labels--properties)
4. [Schema Design: Relationship Types](#4-schema-design-relationship-types)
5. [Constraints & Indexes](#5-constraints--indexes)
6. [Seed Data: Core Medical Ontology](#6-seed-data-core-medical-ontology)
7. [Seed Data: Disease & Symptom Nodes](#7-seed-data-disease--symptom-nodes)
8. [Seed Data: Clinical Procedure Pathways](#8-seed-data-clinical-procedure-pathways)
9. [Seed Data: Geographic Pricing Tiers](#9-seed-data-geographic-pricing-tiers)
10. [Seed Data: Hospital & Facility Nodes](#10-seed-data-hospital--facility-nodes)
11. [Seed Data: Comorbidity Cost Multipliers](#11-seed-data-comorbidity-cost-multipliers)
12. [Seed Data: Specialist & Department Nodes](#12-seed-data-specialist--department-nodes)
13. [Seed Data: Insurance & NBFC Financing Rules](#13-seed-data-insurance--nbfc-financing-rules)
14. [Connecting the Graph: Relationship Cypher Scripts](#14-connecting-the-graph-relationship-cypher-scripts)
15. [Vector Index for Hybrid RAG Retrieval](#15-vector-index-for-hybrid-rag-retrieval)
16. [LangChain Agent Query Patterns (Cypher Templates)](#16-langchain-agent-query-patterns-cypher-templates)
17. [ICD-10 Bulk Import Pipeline](#17-icd-10-bulk-import-pipeline)
18. [Data Validation & Integrity Checks](#18-data-validation--integrity-checks)
19. [Maintenance & Update Procedures](#19-maintenance--update-procedures)

---

## 1. Overview & Architecture Philosophy

### Purpose of This Knowledge Graph

This Neo4j property graph serves as the **deterministic reasoning backbone** of the Healthcare AI Navigator. Unlike a pure vector similarity search, the Knowledge Graph (KG) encodes **explicit, traversable relationships** between:

- Patient-reported **symptoms** → mapped **ICD-10 disease codes**
- ICD-10 diseases → required **clinical procedures**
- Procedures → **phase-by-phase cost components**
- Cost components → **geographic pricing adjustments** by city tier
- Comorbidities → **cost multiplier weights (ωᵢ)** for financial estimation
- Hospitals/Facilities → **multi-source fusion scoring** components
- Hospitals → **specialist rosters**, **bed capacity**, and **availability proxies**
- Insurance sub-limits → **cashless pre-authorization eligibility**
- NBFC risk bands → **loan EMI eligibility rules**

### GraphRAG Hybrid Retrieval Flow

```
User Natural Language Query
        │
        ▼
   NER Pipeline (SpaCy/Transformers)
        │  extracts: symptoms, body parts, procedures, location
        ▼
  LangChain Orchestration Layer
        │
   ┌────┴────┐
   │         │
Cypher    Vector
Query     Index
(Neo4j)   (Semantic)
   │         │
   └────┬────┘
        │  merged enriched context
        ▼
  LLM Response Generation
  (with RAG Confidence Scoring)
```

The graph is traversed **deterministically** for structured data (costs, pathways, eligibility rules) and the vector index retrieves **unstructured contextual data** (clinical guidelines, hospital reviews sentiment scores).

---

## 2. Prerequisites & Environment Setup

### 2.1 Neo4j Installation

```bash
# Option A: Docker (Recommended for Development)
docker run \
  --name neo4j-healthcare \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/healthcareAI@2025 \
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
  -e NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.* \
  -v $HOME/neo4j/data:/data \
  -v $HOME/neo4j/logs:/logs \
  -v $HOME/neo4j/import:/var/lib/neo4j/import \
  neo4j:5.18.0

# Option B: Neo4j Aura (Managed Cloud — Production)
# Sign up at: https://neo4j.com/cloud/platform/aura-graph-database/
# Recommended Tier: AuraDB Professional (for vector index support)
```

### 2.2 Python Environment

```bash
pip install neo4j==5.18.0
pip install langchain==0.2.0
pip install langchain-community==0.2.0
pip install langchain-neo4j==0.1.0
pip install openai==1.30.0          # or anthropic sdk
pip install sentence-transformers==3.0.0
pip install pandas==2.2.0
pip install requests==2.31.0
```

### 2.3 Python Connection Boilerplate

```python
from neo4j import GraphDatabase

URI      = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "healthcareAI@2025"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def run_query(cypher: str, params: dict = {}):
    with driver.session(database="neo4j") as session:
        result = session.run(cypher, params)
        return [record.data() for record in result]

# Verify connection
run_query("RETURN 'Neo4j Healthcare KG Connected' AS status")
```

---

## 3. Schema Design: Node Labels & Properties

### 3.1 Complete Node Label Catalogue

| Label | Purpose | Primary Key |
|---|---|---|
| `Symptom` | Patient-reported clinical symptoms | `symptom_id` |
| `AnatomicalEntity` | Body parts / organ systems | `entity_id` |
| `Disease` | ICD-10 mapped disease classifications | `icd10_code` |
| `Procedure` | Surgical / diagnostic procedures | `procedure_id` |
| `PathwayPhase` | Sequential stages within a treatment pathway | `phase_id` |
| `CostComponent` | Individual cost line items per phase | `component_id` |
| `GeographicTier` | City tier classification with pricing factors | `tier_id` |
| `City` | Specific cities with coordinates | `city_id` |
| `Hospital` | Healthcare facility nodes | `hospital_id` |
| `Department` | Clinical departments within hospitals | `dept_id` |
| `Specialist` | Doctors with specialty and availability | `specialist_id` |
| `Comorbidity` | Concurrent conditions with cost multipliers | `comorbidity_id` |
| `InsurancePolicy` | Policy types with sub-limits | `policy_id` |
| `NBFCRiskBand` | Loan eligibility risk tiers | `band_id` |
| `MedicalOntology` | ICD-10 / SNOMED CT concept anchors | `ontology_id` |
| `ClinicalGuideline` | Treatment protocols (unstructured text for RAG) | `guideline_id` |
| `HospitalReviewSummary` | ABSA-processed sentiment scores | `review_id` |

### 3.2 Node Property Specifications

#### `Symptom`
```cypher
// Properties:
// symptom_id        STRING  (e.g., "SYM_001")
// name              STRING  (e.g., "chest pain")
// colloquial_terms  LIST    (e.g., ["seene mein dard", "heart pain", "chest tightness"])
// severity_hint     STRING  ("RED" | "YELLOW" | "GREEN")
// anatomical_region STRING  (e.g., "thoracic")
// icd10_hint        STRING  (e.g., "R07")  — top-level ICD code hint
// embedding         LIST<FLOAT>  — vector embedding for semantic search
```

#### `Disease`
```cypher
// Properties:
// icd10_code         STRING  (e.g., "I25.1") — PRIMARY KEY
// name               STRING  (e.g., "Atherosclerotic heart disease of native coronary artery")
// short_name         STRING  (e.g., "Coronary Artery Disease")
// category           STRING  (e.g., "Cardiovascular", "Orthopedic", "Neurological")
// severity_class     STRING  ("CHRONIC" | "ACUTE" | "CRITICAL")
// common_comorbidities LIST  (e.g., ["Diabetes Mellitus", "Hypertension"])
// embedding          LIST<FLOAT>
```

#### `Procedure`
```cypher
// Properties:
// procedure_id       STRING  (e.g., "PROC_001")
// name               STRING  (e.g., "Percutaneous Coronary Intervention (Angioplasty)")
// short_name         STRING  (e.g., "Angioplasty")
// specialty_required STRING  (e.g., "Cardiology")
// is_elective        BOOLEAN
// is_emergency_capable BOOLEAN
// base_duration_days INTEGER (average hospital stay in days)
// nabh_procedure_code STRING
// embedding          LIST<FLOAT>
```

#### `PathwayPhase`
```cypher
// Properties:
// phase_id           STRING  (e.g., "PHASE_ANGIO_01")
// procedure_id_ref   STRING  (foreign key ref to Procedure)
// phase_name         STRING  (e.g., "Pre-Procedure Diagnostics")
// phase_order        INTEGER (1, 2, 3, 4 — sequential ordering)
// phase_type         STRING  ("PRE" | "SURGICAL" | "HOSPITAL_STAY" | "POST")
// typical_duration   STRING  (e.g., "1-3 days", "same day", "4-6 weeks")
// is_mandatory       BOOLEAN
```

#### `CostComponent`
```cypher
// Properties:
// component_id         STRING  (e.g., "COST_ANGIO_PRE_001")
// phase_id_ref         STRING
// description          STRING  (e.g., "Diagnostic Angiography")
// base_cost_min_inr    INTEGER (e.g., 10000)
// base_cost_max_inr    INTEGER (e.g., 30000)
// tier1_multiplier     FLOAT   (e.g., 1.0)
// tier2_multiplier     FLOAT   (e.g., 0.92)
// tier3_multiplier     FLOAT   (e.g., 0.75)
// is_insurance_covered BOOLEAN
// cost_driver          STRING  (e.g., "stent_type", "room_type", "implant_grade")
// variants             LIST    (e.g., ["Bare-Metal Stent", "Drug-Eluting Stent"])
// variant_cost_delta   MAP     (e.g., {Drug-Eluting: 50000, Bare-Metal: 0})
```

#### `GeographicTier`
```cypher
// Properties:
// tier_id            STRING  ("TIER_1" | "TIER_2" | "TIER_3")
// tier_name          STRING  (e.g., "Tier 1 Metro")
// cost_multiplier    FLOAT   (e.g., 1.0, 0.92, 0.83)
// icu_bed_day_cost   INTEGER (e.g., 5534, 5427, 2638)
// specialist_density STRING  ("HIGH" | "MEDIUM" | "LOW")
// example_cities     LIST    (e.g., ["Mumbai", "Delhi", "Bangalore"])
```

#### `Hospital`
```cypher
// Properties:
// hospital_id          STRING  (e.g., "HOSP_001")
// name                 STRING
// city                 STRING
// state                STRING
// tier                 STRING  ("TIER_1" | "TIER_2" | "TIER_3")
// latitude             FLOAT
// longitude            FLOAT
// total_beds           INTEGER
// icu_beds             INTEGER
// segment              STRING  ("PREMIUM" | "MID_TIER" | "BUDGET")
// is_nabh_accredited   BOOLEAN
// is_jci_accredited    BOOLEAN
// bed_turnover_rate    FLOAT   (annual bed turnovers per bed)
// cashless_insurers    LIST    (empanelled insurer names)
// has_emergency        BOOLEAN
// has_24hr_pharmacy    BOOLEAN
// clinical_score       FLOAT   (0.0 - 1.0, normalized)
// reputation_score     FLOAT   (0.0 - 1.0, from ABSA pipeline)
// accessibility_score  FLOAT   (0.0 - 1.0)
// affordability_score  FLOAT   (0.0 - 1.0)
// fusion_score         FLOAT   (weighted composite: 0.0 - 1.0)
// embedding            LIST<FLOAT>
```

#### `Comorbidity`
```cypher
// Properties:
// comorbidity_id     STRING  (e.g., "COMRB_001")
// name               STRING  (e.g., "Atherosclerotic Cardiovascular Disease")
// short_name         STRING  (e.g., "ASCVD")
// icd10_code         STRING  (e.g., "I25")
// cost_multiplier_weight FLOAT (ωᵢ — empirically derived, e.g., 1.2 means 20% cost increase)
// risk_category      STRING  ("HIGH" | "MEDIUM" | "LOW")
// increases_icu_stay BOOLEAN
// requires_specialist STRING  (e.g., "Nephrologist")
```

#### `NBFCRiskBand`
```cypher
// Properties:
// band_id              STRING  (e.g., "BAND_LOW")
// dti_min              FLOAT   (e.g., 0.0)
// dti_max              FLOAT   (e.g., 30.0)
// risk_flag            STRING  ("LOW" | "MEDIUM" | "HIGH" | "CRITICAL")
// underwriting_label   STRING  (e.g., "Strong repayment capacity")
// interest_rate_min    FLOAT   (e.g., 12.0)
// interest_rate_max    FLOAT   (e.g., 13.0)
// approval_likelihood  STRING  ("VERY HIGH" | "LIKELY" | "MANUAL REVIEW" | "UNLIKELY")
// cta_text             STRING  (e.g., "Aap eligible hain — Apply Now")
// loan_coverage_pct    FLOAT   (e.g., 0.80 — loan covers 80% of procedure cost)
```

---

## 4. Schema Design: Relationship Types

| Relationship | From → To | Key Properties |
|---|---|---|
| `INDICATES` | Symptom → Disease | `confidence: FLOAT`, `is_primary: BOOLEAN` |
| `AFFECTS` | Symptom → AnatomicalEntity | `severity: STRING` |
| `REQUIRES_PROCEDURE` | Disease → Procedure | `is_first_line: BOOLEAN`, `clinical_guideline_ref: STRING` |
| `HAS_PHASE` | Procedure → PathwayPhase | `phase_order: INTEGER` |
| `HAS_COST_COMPONENT` | PathwayPhase → CostComponent | — |
| `ADJUSTED_BY` | CostComponent → GeographicTier | `adjusted_min: INTEGER`, `adjusted_max: INTEGER` |
| `LOCATED_IN` | Hospital → City | `distance_km: FLOAT` |
| `CITY_BELONGS_TO` | City → GeographicTier | — |
| `OFFERS_PROCEDURE` | Hospital → Procedure | `annual_volume: INTEGER`, `success_rate: FLOAT` |
| `HAS_DEPARTMENT` | Hospital → Department | `bed_count: INTEGER` |
| `HAS_SPECIALIST` | Department → Specialist | `active: BOOLEAN` |
| `SPECIALIZES_IN` | Specialist → Disease | `years_experience: INTEGER` |
| `COMPLICATED_BY` | Disease → Comorbidity | `interaction_severity: STRING` |
| `MULTIPLIED_BY` | CostComponent → Comorbidity | `weight_omega: FLOAT` |
| `ELIGIBLE_FOR_BAND` | Hospital → NBFCRiskBand | — |
| `COVERS_PROCEDURE` | InsurancePolicy → Procedure | `sub_limit_inr: INTEGER`, `room_rent_cap: INTEGER` |
| `MAPPED_TO` | Symptom → MedicalOntology | `ontology_type: STRING` ("ICD10" \| "SNOMED") |
| `CLASSIFIED_AS` | Disease → MedicalOntology | `code: STRING` |
| `HAS_SENTIMENT` | Hospital → HospitalReviewSummary | `as_of_date: DATE` |

---

## 5. Constraints & Indexes

Run these **first**, before any data insertion:

```cypher
// ─── UNIQUENESS CONSTRAINTS ───────────────────────────────────────────────────
CREATE CONSTRAINT symptom_id_unique IF NOT EXISTS
  FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE;

CREATE CONSTRAINT disease_icd10_unique IF NOT EXISTS
  FOR (d:Disease) REQUIRE d.icd10_code IS UNIQUE;

CREATE CONSTRAINT procedure_id_unique IF NOT EXISTS
  FOR (p:Procedure) REQUIRE p.procedure_id IS UNIQUE;

CREATE CONSTRAINT phase_id_unique IF NOT EXISTS
  FOR (ph:PathwayPhase) REQUIRE ph.phase_id IS UNIQUE;

CREATE CONSTRAINT component_id_unique IF NOT EXISTS
  FOR (c:CostComponent) REQUIRE c.component_id IS UNIQUE;

CREATE CONSTRAINT hospital_id_unique IF NOT EXISTS
  FOR (h:Hospital) REQUIRE h.hospital_id IS UNIQUE;

CREATE CONSTRAINT comorbidity_id_unique IF NOT EXISTS
  FOR (cm:Comorbidity) REQUIRE cm.comorbidity_id IS UNIQUE;

CREATE CONSTRAINT city_id_unique IF NOT EXISTS
  FOR (c:City) REQUIRE c.city_id IS UNIQUE;

CREATE CONSTRAINT nbfc_band_id_unique IF NOT EXISTS
  FOR (b:NBFCRiskBand) REQUIRE b.band_id IS UNIQUE;

// ─── LOOKUP INDEXES ───────────────────────────────────────────────────────────
CREATE INDEX symptom_name_idx IF NOT EXISTS FOR (s:Symptom) ON (s.name);
CREATE INDEX disease_short_name_idx IF NOT EXISTS FOR (d:Disease) ON (d.short_name);
CREATE INDEX disease_category_idx IF NOT EXISTS FOR (d:Disease) ON (d.category);
CREATE INDEX procedure_name_idx IF NOT EXISTS FOR (p:Procedure) ON (p.name);
CREATE INDEX hospital_city_idx IF NOT EXISTS FOR (h:Hospital) ON (h.city);
CREATE INDEX hospital_tier_idx IF NOT EXISTS FOR (h:Hospital) ON (h.tier);
CREATE INDEX hospital_segment_idx IF NOT EXISTS FOR (h:Hospital) ON (h.segment);
CREATE INDEX hospital_fusion_score_idx IF NOT EXISTS FOR (h:Hospital) ON (h.fusion_score);
CREATE INDEX comorbidity_name_idx IF NOT EXISTS FOR (cm:Comorbidity) ON (cm.name);

// ─── FULLTEXT INDEX (for NER fallback fuzzy matching) ─────────────────────────
CREATE FULLTEXT INDEX symptom_fulltext IF NOT EXISTS
  FOR (s:Symptom) ON EACH [s.name, s.colloquial_terms];

CREATE FULLTEXT INDEX disease_fulltext IF NOT EXISTS
  FOR (d:Disease) ON EACH [d.name, d.short_name];

CREATE FULLTEXT INDEX hospital_fulltext IF NOT EXISTS
  FOR (h:Hospital) ON EACH [h.name, h.city];
```

---

## 6. Seed Data: Core Medical Ontology

```cypher
// ─── GEOGRAPHIC TIERS ─────────────────────────────────────────────────────────
MERGE (t1:GeographicTier {tier_id: "TIER_1"})
SET t1 += {
  tier_name: "Tier 1 Metro",
  cost_multiplier: 1.0,
  icu_bed_day_cost: 5534,
  specialist_density: "HIGH",
  example_cities: ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Pune"]
};

MERGE (t2:GeographicTier {tier_id: "TIER_2"})
SET t2 += {
  tier_name: "Tier 2 City",
  cost_multiplier: 0.92,
  icu_bed_day_cost: 5427,
  specialist_density: "MEDIUM",
  example_cities: ["Nagpur", "Surat", "Lucknow", "Indore", "Bhopal", "Coimbatore", "Vadodara", "Agra"]
};

MERGE (t3:GeographicTier {tier_id: "TIER_3"})
SET t3 += {
  tier_name: "Tier 3 City",
  cost_multiplier: 0.83,
  icu_bed_day_cost: 2638,
  specialist_density: "LOW",
  example_cities: ["Raipur", "Ahmedabad satellite", "Bilaspur", "Durg", "Korba", "Ambikapur", "Ratlam"]
};

// ─── NBFC RISK BANDS ─────────────────────────────────────────────────────────
MERGE (b1:NBFCRiskBand {band_id: "BAND_LOW"})
SET b1 += {
  dti_min: 0.0, dti_max: 30.0,
  risk_flag: "LOW",
  underwriting_label: "Strong repayment capacity; very high approval likelihood",
  interest_rate_min: 12.0, interest_rate_max: 13.0,
  approval_likelihood: "VERY HIGH",
  cta_text: "Aap eligible hain — Apply Now",
  loan_coverage_pct: 0.80
};

MERGE (b2:NBFCRiskBand {band_id: "BAND_MEDIUM"})
SET b2 += {
  dti_min: 30.0, dti_max: 40.0,
  risk_flag: "MEDIUM",
  underwriting_label: "Manageable debt load; conditional approval likely",
  interest_rate_min: 13.0, interest_rate_max: 15.0,
  approval_likelihood: "LIKELY",
  cta_text: "Proceed with Standard Application",
  loan_coverage_pct: 0.80
};

MERGE (b3:NBFCRiskBand {band_id: "BAND_HIGH"})
SET b3 += {
  dti_min: 40.0, dti_max: 50.0,
  risk_flag: "HIGH",
  underwriting_label: "Strained capacity; requires manual review or co-applicant",
  interest_rate_min: 15.0, interest_rate_max: 16.0,
  approval_likelihood: "MANUAL REVIEW",
  cta_text: "Flag for Manual Review",
  loan_coverage_pct: 0.70
};

MERGE (b4:NBFCRiskBand {band_id: "BAND_CRITICAL"})
SET b4 += {
  dti_min: 50.0, dti_max: 100.0,
  risk_flag: "CRITICAL",
  underwriting_label: "Overleveraged; loan approval unlikely without restructuring",
  interest_rate_min: -1.0, interest_rate_max: -1.0,
  approval_likelihood: "UNLIKELY",
  cta_text: "Recommend Alternate Financing",
  loan_coverage_pct: 0.0
};
```

---

## 7. Seed Data: Disease & Symptom Nodes

```cypher
// ══════════════════════════════════════════════════════════════
// CARDIOVASCULAR DOMAIN
// ══════════════════════════════════════════════════════════════

// ─── SYMPTOMS ────────────────────────────────────────────────
MERGE (s1:Symptom {symptom_id: "SYM_001"})
SET s1 += {
  name: "chest pain",
  colloquial_terms: ["seene mein dard", "chest tightness", "heart pain", "seena dard", "chest discomfort"],
  severity_hint: "RED",
  anatomical_region: "thoracic",
  icd10_hint: "R07"
};

MERGE (s2:Symptom {symptom_id: "SYM_002"})
SET s2 += {
  name: "chest pain radiating to left arm",
  colloquial_terms: ["baaye haath mein dard", "left arm pain with chest", "arm radiation"],
  severity_hint: "RED",
  anatomical_region: "thoracic",
  icd10_hint: "R07.9"
};

MERGE (s3:Symptom {symptom_id: "SYM_003"})
SET s3 += {
  name: "shortness of breath",
  colloquial_terms: ["saans lene mein takleef", "breathlessness", "dyspnea", "saans phoolna"],
  severity_hint: "YELLOW",
  anatomical_region: "pulmonary",
  icd10_hint: "R06.0"
};

MERGE (s4:Symptom {symptom_id: "SYM_004"})
SET s4 += {
  name: "palpitations",
  colloquial_terms: ["dil ki dhadkan tej hona", "heart racing", "irregular heartbeat"],
  severity_hint: "YELLOW",
  anatomical_region: "cardiac",
  icd10_hint: "R00.2"
};

MERGE (s5:Symptom {symptom_id: "SYM_005"})
SET s5 += {
  name: "difficulty breathing",
  colloquial_terms: ["saans ki takleef", "can't breathe", "breathing difficulty"],
  severity_hint: "RED",
  anatomical_region: "pulmonary",
  icd10_hint: "R06"
};

// ─── ORTHOPEDIC SYMPTOMS ──────────────────────────────────────
MERGE (s6:Symptom {symptom_id: "SYM_006"})
SET s6 += {
  name: "severe knee pain",
  colloquial_terms: ["ghutne mein dard", "knee pain", "ghutna dard", "knee ache"],
  severity_hint: "YELLOW",
  anatomical_region: "knee_joint",
  icd10_hint: "M25.56"
};

MERGE (s7:Symptom {symptom_id: "SYM_007"})
SET s7 += {
  name: "knee swelling",
  colloquial_terms: ["ghutne ki sujan", "swollen knee", "knee inflammation"],
  severity_hint: "YELLOW",
  anatomical_region: "knee_joint",
  icd10_hint: "M25.46"
};

MERGE (s8:Symptom {symptom_id: "SYM_008"})
SET s8 += {
  name: "inability to walk",
  colloquial_terms: ["chalna mushkil", "can't walk", "walking difficulty", "mobility loss"],
  severity_hint: "YELLOW",
  anatomical_region: "lower_extremity",
  icd10_hint: "R26.2"
};

// ─── DISEASES ────────────────────────────────────────────────
MERGE (d1:Disease {icd10_code: "I25.1"})
SET d1 += {
  name: "Atherosclerotic heart disease of native coronary artery with angina pectoris",
  short_name: "Coronary Artery Disease",
  category: "Cardiovascular",
  severity_class: "CHRONIC",
  common_comorbidities: ["Diabetes Mellitus", "Hypertension", "Dyslipidemia"]
};

MERGE (d2:Disease {icd10_code: "I21.9"})
SET d2 += {
  name: "Acute myocardial infarction, unspecified",
  short_name: "Heart Attack (MI)",
  category: "Cardiovascular",
  severity_class: "ACUTE",
  common_comorbidities: ["Hypertension", "Diabetes Mellitus", "ASCVD"]
};

MERGE (d3:Disease {icd10_code: "I50.9"})
SET d3 += {
  name: "Heart failure, unspecified",
  short_name: "Heart Failure",
  category: "Cardiovascular",
  severity_class: "CHRONIC",
  common_comorbidities: ["Kidney Disease", "Diabetes Mellitus", "ASCVD"]
};

MERGE (d4:Disease {icd10_code: "M17.11"})
SET d4 += {
  name: "Primary osteoarthritis, right knee",
  short_name: "Knee Osteoarthritis",
  category: "Orthopedic",
  severity_class: "CHRONIC",
  common_comorbidities: ["Obesity", "Diabetes Mellitus", "Hypertension"]
};

MERGE (d5:Disease {icd10_code: "M17.12"})
SET d5 += {
  name: "Primary osteoarthritis, left knee",
  short_name: "Knee Osteoarthritis (Left)",
  category: "Orthopedic",
  severity_class: "CHRONIC",
  common_comorbidities: ["Obesity", "Diabetes Mellitus", "Hypertension"]
};

MERGE (d6:Disease {icd10_code: "E11.9"})
SET d6 += {
  name: "Type 2 diabetes mellitus without complications",
  short_name: "Type 2 Diabetes",
  category: "Endocrine",
  severity_class: "CHRONIC",
  common_comorbidities: ["Hypertension", "Dyslipidemia", "CKD"]
};

MERGE (d7:Disease {icd10_code: "N18.9"})
SET d7 += {
  name: "Chronic kidney disease, unspecified",
  short_name: "Chronic Kidney Disease",
  category: "Nephrology",
  severity_class: "CHRONIC",
  common_comorbidities: ["Diabetes Mellitus", "Hypertension", "Heart Failure"]
};
```

---

## 8. Seed Data: Clinical Procedure Pathways

```cypher
// ══════════════════════════════════════════════════════════════
// PROCEDURE: ANGIOPLASTY (PCI)
// ══════════════════════════════════════════════════════════════

MERGE (proc1:Procedure {procedure_id: "PROC_001"})
SET proc1 += {
  name: "Percutaneous Coronary Intervention",
  short_name: "Angioplasty / PCI",
  specialty_required: "Cardiology",
  is_elective: false,
  is_emergency_capable: true,
  base_duration_days: 3,
  nabh_procedure_code: "CARD-PCI-001",
  base_cost_min_inr: 140000,
  base_cost_max_inr: 340000
};

// ─── PATHWAY PHASES: ANGIOPLASTY ─────────────────────────────
MERGE (ph1:PathwayPhase {phase_id: "PHASE_ANGIO_01"})
SET ph1 += {
  procedure_id_ref: "PROC_001",
  phase_name: "Pre-Procedure Diagnostics",
  phase_order: 1,
  phase_type: "PRE",
  typical_duration: "1-3 days",
  is_mandatory: true
};

MERGE (ph2:PathwayPhase {phase_id: "PHASE_ANGIO_02"})
SET ph2 += {
  procedure_id_ref: "PROC_001",
  phase_name: "Interventional Procedure",
  phase_order: 2,
  phase_type: "SURGICAL",
  typical_duration: "2-4 hours",
  is_mandatory: true
};

MERGE (ph3:PathwayPhase {phase_id: "PHASE_ANGIO_03"})
SET ph3 += {
  procedure_id_ref: "PROC_001",
  phase_name: "Hospitalization / ICU Monitoring",
  phase_order: 3,
  phase_type: "HOSPITAL_STAY",
  typical_duration: "2-5 days",
  is_mandatory: true
};

MERGE (ph4:PathwayPhase {phase_id: "PHASE_ANGIO_04"})
SET ph4 += {
  procedure_id_ref: "PROC_001",
  phase_name: "Post-Procedure Care",
  phase_order: 4,
  phase_type: "POST",
  typical_duration: "4-8 weeks",
  is_mandatory: true
};

// ─── COST COMPONENTS: ANGIOPLASTY ────────────────────────────
MERGE (cc1:CostComponent {component_id: "COST_ANGIO_PRE_001"})
SET cc1 += {
  phase_id_ref: "PHASE_ANGIO_01",
  description: "Pre-Procedure Diagnostics (ECG, Stress Test, Echocardiogram, Diagnostic Angiography)",
  base_cost_min_inr: 10000,
  base_cost_max_inr: 30000,
  tier1_multiplier: 1.0,
  tier2_multiplier: 0.92,
  tier3_multiplier: 0.83,
  is_insurance_covered: true,
  cost_driver: "test_complexity"
};

MERGE (cc2:CostComponent {component_id: "COST_ANGIO_SURG_001"})
SET cc2 += {
  phase_id_ref: "PHASE_ANGIO_02",
  description: "Balloon Angioplasty / Stent Placement",
  base_cost_min_inr: 100000,
  base_cost_max_inr: 250000,
  tier1_multiplier: 1.0,
  tier2_multiplier: 0.92,
  tier3_multiplier: 0.83,
  is_insurance_covered: true,
  cost_driver: "stent_type",
  variants: ["Bare-Metal Stent (BMS)", "Drug-Eluting Stent (DES)", "Bioresorbable Scaffold"],
  variant_cost_delta: "{\"Bare-Metal Stent\": 0, \"Drug-Eluting Stent\": 50000, \"Bioresorbable Scaffold\": 80000}"
};

MERGE (cc3:CostComponent {component_id: "COST_ANGIO_HOSP_001"})
SET cc3 += {
  phase_id_ref: "PHASE_ANGIO_03",
  description: "ICU Monitoring and General Ward Recovery",
  base_cost_min_inr: 20000,
  base_cost_max_inr: 60000,
  tier1_multiplier: 1.0,
  tier2_multiplier: 0.92,
  tier3_multiplier: 0.48,
  is_insurance_covered: true,
  cost_driver: "room_type",
  variants: ["ICU", "HDU", "General Ward"],
  variant_cost_delta: "{\"ICU\": 5534, \"HDU\": 3000, \"General Ward\": 1500}"
};

MERGE (cc4:CostComponent {component_id: "COST_ANGIO_POST_001"})
SET cc4 += {
  phase_id_ref: "PHASE_ANGIO_04",
  description: "Medications (Anti-platelets, Statins), Consumables, Follow-up Consultations",
  base_cost_min_inr: 10000,
  base_cost_max_inr: 30000,
  tier1_multiplier: 1.0,
  tier2_multiplier: 0.95,
  tier3_multiplier: 0.90,
  is_insurance_covered: false,
  cost_driver: "medication_duration"
};

// ══════════════════════════════════════════════════════════════
// PROCEDURE: TOTAL KNEE REPLACEMENT (TKR)
// ══════════════════════════════════════════════════════════════

MERGE (proc2:Procedure {procedure_id: "PROC_002"})
SET proc2 += {
  name: "Total Knee Replacement",
  short_name: "TKR",
  specialty_required: "Orthopedics",
  is_elective: true,
  is_emergency_capable: false,
  base_duration_days: 5,
  nabh_procedure_code: "ORTHO-TKR-001",
  base_cost_min_inr: 200000,
  base_cost_max_inr: 450000
};

MERGE (ph5:PathwayPhase {phase_id: "PHASE_TKR_01"})
SET ph5 += {
  procedure_id_ref: "PROC_002",
  phase_name: "Pre-Surgical Evaluation",
  phase_order: 1,
  phase_type: "PRE",
  typical_duration: "3-7 days",
  is_mandatory: true
};

MERGE (ph6:PathwayPhase {phase_id: "PHASE_TKR_02"})
SET ph6 += {
  procedure_id_ref: "PROC_002",
  phase_name: "Core Surgery",
  phase_order: 2,
  phase_type: "SURGICAL",
  typical_duration: "2-3 hours",
  is_mandatory: true
};

MERGE (ph7:PathwayPhase {phase_id: "PHASE_TKR_03"})
SET ph7 += {
  procedure_id_ref: "PROC_002",
  phase_name: "Post-Surgical Hospitalization",
  phase_order: 3,
  phase_type: "HOSPITAL_STAY",
  typical_duration: "4-7 days",
  is_mandatory: true
};

MERGE (ph8:PathwayPhase {phase_id: "PHASE_TKR_04"})
SET ph8 += {
  procedure_id_ref: "PROC_002",
  phase_name: "Physiotherapy & Rehabilitation",
  phase_order: 4,
  phase_type: "POST",
  typical_duration: "6-12 weeks",
  is_mandatory: true
};

// Cost Components for TKR
MERGE (cc5:CostComponent {component_id: "COST_TKR_PRE_001"})
SET cc5 += {
  phase_id_ref: "PHASE_TKR_01",
  description: "Pre-surgical Blood Work, X-rays, MRI, Cardiologist Clearance",
  base_cost_min_inr: 8000,
  base_cost_max_inr: 20000,
  tier1_multiplier: 1.0,
  tier2_multiplier: 0.92,
  tier3_multiplier: 0.83,
  is_insurance_covered: true,
  cost_driver: "test_panel"
};

MERGE (cc6:CostComponent {component_id: "COST_TKR_SURG_001"})
SET cc6 += {
  phase_id_ref: "PHASE_TKR_02",
  description: "Knee Implant + Surgical Procedure",
  base_cost_min_inr: 130000,
  base_cost_max_inr: 360000,
  tier1_multiplier: 1.0,
  tier2_multiplier: 0.92,
  tier3_multiplier: 0.83,
  is_insurance_covered: true,
  cost_driver: "implant_grade",
  variants: ["Conventional Implant", "High-Flexion Implant (Imported)", "Robotic-Assisted Navigation"],
  variant_cost_delta: "{\"Conventional Implant\": 0, \"High-Flexion Implant\": 80000, \"Robotic-Assisted Navigation\": 120000}"
};

MERGE (cc7:CostComponent {component_id: "COST_TKR_HOSP_001"})
SET cc7 += {
  phase_id_ref: "PHASE_TKR_03",
  description: "ICU and General Ward Stay (4-7 nights)",
  base_cost_min_inr: 30000,
  base_cost_max_inr: 70000,
  tier1_multiplier: 1.0,
  tier2_multiplier: 0.92,
  tier3_multiplier: 0.83,
  is_insurance_covered: true,
  cost_driver: "room_type"
};

MERGE (cc8:CostComponent {component_id: "COST_TKR_POST_001"})
SET cc8 += {
  phase_id_ref: "PHASE_TKR_04",
  description: "Physiotherapy Sessions, Mobility Aids, Follow-up OPD Visits",
  base_cost_min_inr: 15000,
  base_cost_max_inr: 40000,
  tier1_multiplier: 1.0,
  tier2_multiplier: 0.92,
  tier3_multiplier: 0.85,
  is_insurance_covered: false,
  cost_driver: "physio_duration"
};
```

---

## 9. Seed Data: Geographic Pricing Tiers

```cypher
// ─── CITIES ──────────────────────────────────────────────────

// Tier 1 Cities
MERGE (c1:City {city_id: "CITY_MUM"})  SET c1 += {name: "Mumbai",    state: "Maharashtra",      latitude: 19.0760, longitude: 72.8777};
MERGE (c2:City {city_id: "CITY_DEL"})  SET c2 += {name: "Delhi",     state: "Delhi",             latitude: 28.7041, longitude: 77.1025};
MERGE (c3:City {city_id: "CITY_BLR"})  SET c3 += {name: "Bangalore", state: "Karnataka",         latitude: 12.9716, longitude: 77.5946};
MERGE (c4:City {city_id: "CITY_HYD"})  SET c4 += {name: "Hyderabad", state: "Telangana",         latitude: 17.3850, longitude: 78.4867};
MERGE (c5:City {city_id: "CITY_CHN"})  SET c5 += {name: "Chennai",   state: "Tamil Nadu",        latitude: 13.0827, longitude: 80.2707};

// Tier 2 Cities
MERGE (c6:City {city_id: "CITY_NGP"})  SET c6 += {name: "Nagpur",    state: "Maharashtra",      latitude: 21.1458, longitude: 79.0882};
MERGE (c7:City {city_id: "CITY_IND"})  SET c7 += {name: "Indore",    state: "Madhya Pradesh",   latitude: 22.7196, longitude: 75.8577};
MERGE (c8:City {city_id: "CITY_LKO"})  SET c8 += {name: "Lucknow",   state: "Uttar Pradesh",    latitude: 26.8467, longitude: 80.9462};
MERGE (c9:City {city_id: "CITY_BHP"})  SET c9 += {name: "Bhopal",    state: "Madhya Pradesh",   latitude: 23.2599, longitude: 77.4126};

// Tier 3 Cities (Chhattisgarh Focus — Platform's Home Region)
MERGE (c10:City {city_id: "CITY_RAI"}) SET c10 += {name: "Raipur",   state: "Chhattisgarh",    latitude: 21.2514, longitude: 81.6296};
MERGE (c11:City {city_id: "CITY_DRG"}) SET c11 += {name: "Durg",     state: "Chhattisgarh",    latitude: 21.1904, longitude: 81.2849};
MERGE (c12:City {city_id: "CITY_BLS"}) SET c12 += {name: "Bilaspur", state: "Chhattisgarh",    latitude: 22.0797, longitude: 82.1409};
MERGE (c13:City {city_id: "CITY_KRB"}) SET c13 += {name: "Korba",    state: "Chhattisgarh",    latitude: 22.3595, longitude: 82.7501};

// ─── CITY → TIER RELATIONSHIPS ────────────────────────────────
MATCH (t1:GeographicTier {tier_id: "TIER_1"}), (t2:GeographicTier {tier_id: "TIER_2"}), (t3:GeographicTier {tier_id: "TIER_3"})

// Tier 1
MATCH (c:City) WHERE c.city_id IN ["CITY_MUM","CITY_DEL","CITY_BLR","CITY_HYD","CITY_CHN"]
MERGE (c)-[:CITY_BELONGS_TO]->(t1);

// Tier 2
MATCH (c:City) WHERE c.city_id IN ["CITY_NGP","CITY_IND","CITY_LKO","CITY_BHP"]
MERGE (c)-[:CITY_BELONGS_TO]->(t2);

// Tier 3
MATCH (c:City) WHERE c.city_id IN ["CITY_RAI","CITY_DRG","CITY_BLS","CITY_KRB"]
MERGE (c)-[:CITY_BELONGS_TO]->(t3);
```

---

## 10. Seed Data: Hospital & Facility Nodes

```cypher
// ══════════════════════════════════════════════════════════════
// SAMPLE HOSPITAL DATA (Expand with real NPI/facility data)
// ══════════════════════════════════════════════════════════════

// ─── RAIPUR (CHHATTISGARH) ───────────────────────────────────
MERGE (h1:Hospital {hospital_id: "HOSP_RAI_001"})
SET h1 += {
  name: "Ramkrishna Care Hospital",
  city: "Raipur", state: "Chhattisgarh", tier: "TIER_3",
  latitude: 21.2425, longitude: 81.6273,
  total_beds: 750, icu_beds: 80,
  segment: "PREMIUM",
  is_nabh_accredited: true,
  is_jci_accredited: false,
  bed_turnover_rate: 48.5,
  cashless_insurers: ["Star Health", "New India Assurance", "HDFC Ergo", "ICICI Lombard"],
  has_emergency: true,
  has_24hr_pharmacy: true,
  clinical_score: 0.82,
  reputation_score: 0.78,
  accessibility_score: 0.85,
  affordability_score: 0.70,
  fusion_score: 0.0  // computed below
};

MERGE (h2:Hospital {hospital_id: "HOSP_RAI_002"})
SET h2 += {
  name: "Shri Narayana Hospital Raipur",
  city: "Raipur", state: "Chhattisgarh", tier: "TIER_3",
  latitude: 21.2587, longitude: 81.6193,
  total_beds: 300, icu_beds: 40,
  segment: "MID_TIER",
  is_nabh_accredited: true,
  is_jci_accredited: false,
  bed_turnover_rate: 42.0,
  cashless_insurers: ["Star Health", "United India", "Oriental Insurance"],
  has_emergency: true,
  has_24hr_pharmacy: true,
  clinical_score: 0.74,
  reputation_score: 0.80,
  accessibility_score: 0.88,
  affordability_score: 0.82,
  fusion_score: 0.0
};

// ─── DURG (CHHATTISGARH) ─────────────────────────────────────
MERGE (h3:Hospital {hospital_id: "HOSP_DRG_001"})
SET h3 += {
  name: "Sparsh Multispecialty Hospital Durg",
  city: "Durg", state: "Chhattisgarh", tier: "TIER_3",
  latitude: 21.1884, longitude: 81.2800,
  total_beds: 200, icu_beds: 25,
  segment: "MID_TIER",
  is_nabh_accredited: false,
  is_jci_accredited: false,
  bed_turnover_rate: 38.0,
  cashless_insurers: ["Star Health", "New India Assurance"],
  has_emergency: true,
  has_24hr_pharmacy: false,
  clinical_score: 0.65,
  reputation_score: 0.72,
  accessibility_score: 0.90,
  affordability_score: 0.88,
  fusion_score: 0.0
};

// ─── NAGPUR (TIER 2 REFERENCE) ────────────────────────────────
MERGE (h4:Hospital {hospital_id: "HOSP_NGP_001"})
SET h4 += {
  name: "Wockhardt Hospital Nagpur",
  city: "Nagpur", state: "Maharashtra", tier: "TIER_2",
  latitude: 21.1397, longitude: 79.0892,
  total_beds: 450, icu_beds: 60,
  segment: "PREMIUM",
  is_nabh_accredited: true,
  is_jci_accredited: false,
  bed_turnover_rate: 52.0,
  cashless_insurers: ["Star Health", "HDFC Ergo", "ICICI Lombard", "Bajaj Allianz", "Aditya Birla"],
  has_emergency: true,
  has_24hr_pharmacy: true,
  clinical_score: 0.88,
  reputation_score: 0.83,
  accessibility_score: 0.72,
  affordability_score: 0.65,
  fusion_score: 0.0
};

// ─── COMPUTE FUSION SCORES (Run after all hospitals inserted) ─
// Formula: 0.40*clinical + 0.25*reputation + 0.20*accessibility + 0.15*affordability
MATCH (h:Hospital)
SET h.fusion_score = round(
  (0.40 * h.clinical_score) +
  (0.25 * h.reputation_score) +
  (0.20 * h.accessibility_score) +
  (0.15 * h.affordability_score),
  3
);

// ─── LINK HOSPITALS TO CITIES ─────────────────────────────────
MATCH (h:Hospital {city: "Raipur"}), (c:City {city_id: "CITY_RAI"})  MERGE (h)-[:LOCATED_IN]->(c);
MATCH (h:Hospital {city: "Durg"}),   (c:City {city_id: "CITY_DRG"})  MERGE (h)-[:LOCATED_IN]->(c);
MATCH (h:Hospital {city: "Nagpur"}), (c:City {city_id: "CITY_NGP"})  MERGE (h)-[:LOCATED_IN]->(c);
```

---

## 11. Seed Data: Comorbidity Cost Multipliers

```cypher
// ══════════════════════════════════════════════════════════════
// COMORBIDITY NODES WITH EMPIRICAL COST MULTIPLIERS (ωᵢ)
// Based on epidemiological research cited in the PDF
// Sources: PMC9703659 (ASCVD/HF/CKD multipliers)
// ══════════════════════════════════════════════════════════════

MERGE (cm1:Comorbidity {comorbidity_id: "COMRB_001"})
SET cm1 += {
  name: "Atherosclerotic Cardiovascular Disease",
  short_name: "ASCVD",
  icd10_code: "I25",
  cost_multiplier_weight: 1.2,   // ωᵢ = 1.2 → 20% increase (2.2x total vs baseline)
  risk_category: "HIGH",
  increases_icu_stay: true,
  requires_specialist: "Cardiologist"
};

MERGE (cm2:Comorbidity {comorbidity_id: "COMRB_002"})
SET cm2 += {
  name: "Heart Failure",
  short_name: "HF",
  icd10_code: "I50",
  cost_multiplier_weight: 2.3,   // ωᵢ = 2.3 → (3.3x total expenditure vs baseline)
  risk_category: "HIGH",
  increases_icu_stay: true,
  requires_specialist: "Cardiologist"
};

MERGE (cm3:Comorbidity {comorbidity_id: "COMRB_003"})
SET cm3 += {
  name: "Chronic Kidney Disease",
  short_name: "CKD",
  icd10_code: "N18",
  cost_multiplier_weight: 1.7,   // ωᵢ = 1.7 → (2.7x total expenditure vs baseline)
  risk_category: "HIGH",
  increases_icu_stay: true,
  requires_specialist: "Nephrologist"
};

MERGE (cm4:Comorbidity {comorbidity_id: "COMRB_004"})
SET cm4 += {
  name: "Type 2 Diabetes Mellitus",
  short_name: "T2DM",
  icd10_code: "E11",
  cost_multiplier_weight: 0.35,  // ωᵢ = 0.35 → 35% cost increase
  risk_category: "MEDIUM",
  increases_icu_stay: false,
  requires_specialist: "Endocrinologist"
};

MERGE (cm5:Comorbidity {comorbidity_id: "COMRB_005"})
SET cm5 += {
  name: "Hypertension",
  short_name: "HTN",
  icd10_code: "I10",
  cost_multiplier_weight: 0.15,  // ωᵢ = 0.15 → 15% cost increase
  risk_category: "MEDIUM",
  increases_icu_stay: false,
  requires_specialist: "Cardiologist"
};

MERGE (cm6:Comorbidity {comorbidity_id: "COMRB_006"})
SET cm6 += {
  name: "Morbid Obesity",
  short_name: "Obesity",
  icd10_code: "E66.01",
  cost_multiplier_weight: 0.25,  // ωᵢ = 0.25 → 25% cost increase (longer OR time, specialized implants)
  risk_category: "MEDIUM",
  increases_icu_stay: false,
  requires_specialist: "Bariatrician"
};

MERGE (cm7:Comorbidity {comorbidity_id: "COMRB_007"})
SET cm7 += {
  name: "Dyslipidemia",
  short_name: "Dyslipidemia",
  icd10_code: "E78.5",
  cost_multiplier_weight: 0.10,
  risk_category: "LOW",
  increases_icu_stay: false,
  requires_specialist: null
};

// ─── LINK DISEASES TO COMORBIDITIES ──────────────────────────
MATCH (d:Disease {icd10_code: "I25.1"}), (cm:Comorbidity)
WHERE cm.comorbidity_id IN ["COMRB_004", "COMRB_005", "COMRB_007", "COMRB_001"]
MERGE (d)-[:COMPLICATED_BY {interaction_severity: "HIGH"}]->(cm);

MATCH (d:Disease {icd10_code: "M17.11"}), (cm:Comorbidity)
WHERE cm.comorbidity_id IN ["COMRB_004", "COMRB_005", "COMRB_006"]
MERGE (d)-[:COMPLICATED_BY {interaction_severity: "MEDIUM"}]->(cm);

MATCH (d:Disease {icd10_code: "I50.9"}), (cm:Comorbidity)
WHERE cm.comorbidity_id IN ["COMRB_003", "COMRB_004", "COMRB_001"]
MERGE (d)-[:COMPLICATED_BY {interaction_severity: "HIGH"}]->(cm);
```

---

## 12. Seed Data: Specialist & Department Nodes

```cypher
// ─── DEPARTMENTS ─────────────────────────────────────────────
MERGE (dept1:Department {dept_id: "DEPT_CARD"})
SET dept1 += {name: "Cardiology",    specialty: "Cardiovascular",  requires_nabh: true};

MERGE (dept2:Department {dept_id: "DEPT_ORTHO"})
SET dept2 += {name: "Orthopedics",   specialty: "Musculoskeletal", requires_nabh: false};

MERGE (dept3:Department {dept_id: "DEPT_NEPH"})
SET dept3 += {name: "Nephrology",    specialty: "Renal",           requires_nabh: false};

MERGE (dept4:Department {dept_id: "DEPT_ENDO"})
SET dept4 += {name: "Endocrinology", specialty: "Metabolic",       requires_nabh: false};

MERGE (dept5:Department {dept_id: "DEPT_EMRG"})
SET dept5 += {name: "Emergency & Trauma", specialty: "Multi",     requires_nabh: true};

// ─── HOSPITAL → DEPARTMENT (with bed counts for queuing proxy) ─
MATCH (h:Hospital {hospital_id: "HOSP_RAI_001"})
MATCH (d1:Department {dept_id: "DEPT_CARD"})
MATCH (d2:Department {dept_id: "DEPT_ORTHO"})
MATCH (d5:Department {dept_id: "DEPT_EMRG"})
MERGE (h)-[:HAS_DEPARTMENT {bed_count: 40, active_specialists: 5}]->(d1)
MERGE (h)-[:HAS_DEPARTMENT {bed_count: 30, active_specialists: 4}]->(d2)
MERGE (h)-[:HAS_DEPARTMENT {bed_count: 20, active_specialists: 8}]->(d5);

MATCH (h:Hospital {hospital_id: "HOSP_RAI_002"})
MATCH (d1:Department {dept_id: "DEPT_CARD"})
MATCH (d2:Department {dept_id: "DEPT_ORTHO"})
MERGE (h)-[:HAS_DEPARTMENT {bed_count: 20, active_specialists: 2}]->(d1)
MERGE (h)-[:HAS_DEPARTMENT {bed_count: 15, active_specialists: 2}]->(d2);

MATCH (h:Hospital {hospital_id: "HOSP_DRG_001"})
MATCH (d1:Department {dept_id: "DEPT_CARD"})
MERGE (h)-[:HAS_DEPARTMENT {bed_count: 10, active_specialists: 1}]->(d1);

// ─── APPOINTMENT AVAILABILITY PROXY LOGIC ────────────────────
// Derive waiting time category based on specialist count + bed occupancy
// This can also be computed dynamically in LangChain agent using a Cypher query

// Waiting time classification rule stored as node property:
// Large Corporate (>=5 specialists) → "2-3 days"
// Mid-tier (2 specialists, high occupancy) → "4-7 days"
// Small clinic (1 specialist) → "1-2 weeks"
// Has Emergency Unit → "24/7 emergency available ✅"

MATCH (h:Hospital)-[rel:HAS_DEPARTMENT]->(d:Department {dept_id: "DEPT_CARD"})
WITH h, rel.active_specialists AS spec_count, h.has_emergency AS has_er
SET h.cardiology_waiting_proxy = CASE
  WHEN has_er = true THEN "24/7 emergency available ✅"
  WHEN spec_count >= 5 THEN "Appointments usually available within 2-3 days"
  WHEN spec_count >= 2 THEN "Estimated waiting time: 4-7 days"
  ELSE "Waiting time: 1-2 weeks"
END;

MATCH (h:Hospital)-[rel:HAS_DEPARTMENT]->(d:Department {dept_id: "DEPT_ORTHO"})
WITH h, rel.active_specialists AS spec_count
SET h.ortho_waiting_proxy = CASE
  WHEN spec_count >= 4 THEN "Appointments usually available within 2-3 days"
  WHEN spec_count >= 2 THEN "Estimated waiting time: 4-7 days"
  ELSE "Waiting time: 1-2 weeks"
END;
```

---

## 13. Seed Data: Insurance & NBFC Financing Rules

```cypher
// ─── INSURANCE POLICY TYPES ───────────────────────────────────
MERGE (ins1:InsurancePolicy {policy_id: "INS_BASIC"})
SET ins1 += {
  policy_name: "Basic Mediclaim",
  sum_insured_max_inr: 300000,
  room_rent_cap_pct: 1.0,        // 1% of sum insured per day
  icu_cap_pct: 2.0,
  covers_pre_existing: false,
  waiting_period_months: 48,
  cashless_available: true,
  typical_copay_pct: 0.0
};

MERGE (ins2:InsurancePolicy {policy_id: "INS_STANDARD"})
SET ins2 += {
  policy_name: "Standard Health Insurance (5L)",
  sum_insured_max_inr: 500000,
  room_rent_cap_pct: 1.0,
  icu_cap_pct: 2.0,
  covers_pre_existing: true,
  waiting_period_months: 24,
  cashless_available: true,
  typical_copay_pct: 0.0
};

MERGE (ins3:InsurancePolicy {policy_id: "INS_PREMIUM"})
SET ins3 += {
  policy_name: "Super Top-Up / Premium Plan (10L+)",
  sum_insured_max_inr: 1000000,
  room_rent_cap_pct: 0.0,        // No room rent capping
  icu_cap_pct: 0.0,
  covers_pre_existing: true,
  waiting_period_months: 12,
  cashless_available: true,
  typical_copay_pct: 0.0
};

MERGE (ins4:InsurancePolicy {policy_id: "INS_GOVT_PMJAY"})
SET ins4 += {
  policy_name: "PM-JAY (Ayushman Bharat)",
  sum_insured_max_inr: 500000,
  room_rent_cap_pct: 0.0,
  icu_cap_pct: 0.0,
  covers_pre_existing: true,
  waiting_period_months: 0,
  cashless_available: true,
  typical_copay_pct: 0.0,
  eligibility_note: "Below Poverty Line families only"
};

// ─── PROCEDURE ↔ INSURANCE COVERAGE ──────────────────────────
MATCH (p1:Procedure {procedure_id: "PROC_001"}), (ins:InsurancePolicy)
WHERE ins.policy_id IN ["INS_STANDARD", "INS_PREMIUM", "INS_GOVT_PMJAY"]
MERGE (ins)-[:COVERS_PROCEDURE {
  sub_limit_inr: 200000,
  requires_pre_auth: true,
  typical_approval_time_hrs: 4
}]->(p1);

MATCH (p2:Procedure {procedure_id: "PROC_002"}), (ins:InsurancePolicy)
WHERE ins.policy_id IN ["INS_STANDARD", "INS_PREMIUM", "INS_GOVT_PMJAY"]
MERGE (ins)-[:COVERS_PROCEDURE {
  sub_limit_inr: 150000,
  requires_pre_auth: true,
  typical_approval_time_hrs: 6
}]->(p2);
```

---

## 14. Connecting the Graph: Relationship Cypher Scripts

```cypher
// ══════════════════════════════════════════════════════════════
// STEP 1: SYMPTOM → DISEASE EDGES
// ══════════════════════════════════════════════════════════════

MATCH (s1:Symptom {symptom_id: "SYM_001"}), (d1:Disease {icd10_code: "I25.1"})
MERGE (s1)-[:INDICATES {confidence: 0.75, is_primary: true}]->(d1);

MATCH (s2:Symptom {symptom_id: "SYM_002"}), (d2:Disease {icd10_code: "I21.9"})
MERGE (s2)-[:INDICATES {confidence: 0.92, is_primary: true}]->(d2);

MATCH (s2:Symptom {symptom_id: "SYM_002"}), (d1:Disease {icd10_code: "I25.1"})
MERGE (s2)-[:INDICATES {confidence: 0.80, is_primary: false}]->(d1);

MATCH (s3:Symptom {symptom_id: "SYM_003"}), (d3:Disease {icd10_code: "I50.9"})
MERGE (s3)-[:INDICATES {confidence: 0.70, is_primary: true}]->(d3);

MATCH (s6:Symptom {symptom_id: "SYM_006"}), (d4:Disease {icd10_code: "M17.11"})
MERGE (s6)-[:INDICATES {confidence: 0.85, is_primary: true}]->(d4);

MATCH (s7:Symptom {symptom_id: "SYM_007"}), (d4:Disease {icd10_code: "M17.11"})
MERGE (s7)-[:INDICATES {confidence: 0.72, is_primary: false}]->(d4);

// ══════════════════════════════════════════════════════════════
// STEP 2: DISEASE → PROCEDURE EDGES
// ══════════════════════════════════════════════════════════════

MATCH (d1:Disease {icd10_code: "I25.1"}), (p1:Procedure {procedure_id: "PROC_001"})
MERGE (d1)-[:REQUIRES_PROCEDURE {
  is_first_line: true,
  clinical_guideline_ref: "ACC/AHA 2021 PCI Guidelines"
}]->(p1);

MATCH (d2:Disease {icd10_code: "I21.9"}), (p1:Procedure {procedure_id: "PROC_001"})
MERGE (d2)-[:REQUIRES_PROCEDURE {
  is_first_line: true,
  clinical_guideline_ref: "STEMI Primary PCI Protocol"
}]->(p1);

MATCH (d4:Disease {icd10_code: "M17.11"}), (p2:Procedure {procedure_id: "PROC_002"})
MERGE (d4)-[:REQUIRES_PROCEDURE {
  is_first_line: false,
  clinical_guideline_ref: "NICE NG226: Osteoarthritis Management"
}]->(p2);

MATCH (d5:Disease {icd10_code: "M17.12"}), (p2:Procedure {procedure_id: "PROC_002"})
MERGE (d5)-[:REQUIRES_PROCEDURE {
  is_first_line: false,
  clinical_guideline_ref: "NICE NG226: Osteoarthritis Management"
}]->(p2);

// ══════════════════════════════════════════════════════════════
// STEP 3: PROCEDURE → PHASE → COST COMPONENT CHAINS
// ══════════════════════════════════════════════════════════════

// Angioplasty chain
MATCH (p:Procedure {procedure_id: "PROC_001"})
MATCH (ph1:PathwayPhase {phase_id: "PHASE_ANGIO_01"})
MATCH (ph2:PathwayPhase {phase_id: "PHASE_ANGIO_02"})
MATCH (ph3:PathwayPhase {phase_id: "PHASE_ANGIO_03"})
MATCH (ph4:PathwayPhase {phase_id: "PHASE_ANGIO_04"})
MERGE (p)-[:HAS_PHASE {phase_order: 1}]->(ph1)
MERGE (p)-[:HAS_PHASE {phase_order: 2}]->(ph2)
MERGE (p)-[:HAS_PHASE {phase_order: 3}]->(ph3)
MERGE (p)-[:HAS_PHASE {phase_order: 4}]->(ph4);

MATCH (ph1:PathwayPhase {phase_id: "PHASE_ANGIO_01"}), (cc1:CostComponent {component_id: "COST_ANGIO_PRE_001"})
MERGE (ph1)-[:HAS_COST_COMPONENT]->(cc1);
MATCH (ph2:PathwayPhase {phase_id: "PHASE_ANGIO_02"}), (cc2:CostComponent {component_id: "COST_ANGIO_SURG_001"})
MERGE (ph2)-[:HAS_COST_COMPONENT]->(cc2);
MATCH (ph3:PathwayPhase {phase_id: "PHASE_ANGIO_03"}), (cc3:CostComponent {component_id: "COST_ANGIO_HOSP_001"})
MERGE (ph3)-[:HAS_COST_COMPONENT]->(cc3);
MATCH (ph4:PathwayPhase {phase_id: "PHASE_ANGIO_04"}), (cc4:CostComponent {component_id: "COST_ANGIO_POST_001"})
MERGE (ph4)-[:HAS_COST_COMPONENT]->(cc4);

// TKR chain
MATCH (p:Procedure {procedure_id: "PROC_002"})
MATCH (ph5:PathwayPhase {phase_id: "PHASE_TKR_01"})
MATCH (ph6:PathwayPhase {phase_id: "PHASE_TKR_02"})
MATCH (ph7:PathwayPhase {phase_id: "PHASE_TKR_03"})
MATCH (ph8:PathwayPhase {phase_id: "PHASE_TKR_04"})
MERGE (p)-[:HAS_PHASE {phase_order: 1}]->(ph5)
MERGE (p)-[:HAS_PHASE {phase_order: 2}]->(ph6)
MERGE (p)-[:HAS_PHASE {phase_order: 3}]->(ph7)
MERGE (p)-[:HAS_PHASE {phase_order: 4}]->(ph8);

// ══════════════════════════════════════════════════════════════
// STEP 4: HOSPITAL → PROCEDURE CAPABILITIES
// ══════════════════════════════════════════════════════════════

MATCH (h:Hospital {hospital_id: "HOSP_RAI_001"}), (p1:Procedure {procedure_id: "PROC_001"})
MERGE (h)-[:OFFERS_PROCEDURE {annual_volume: 380, success_rate: 0.97}]->(p1);

MATCH (h:Hospital {hospital_id: "HOSP_RAI_001"}), (p2:Procedure {procedure_id: "PROC_002"})
MERGE (h)-[:OFFERS_PROCEDURE {annual_volume: 220, success_rate: 0.96}]->(p2);

MATCH (h:Hospital {hospital_id: "HOSP_RAI_002"}), (p1:Procedure {procedure_id: "PROC_001"})
MERGE (h)-[:OFFERS_PROCEDURE {annual_volume: 180, success_rate: 0.95}]->(p1);

MATCH (h:Hospital {hospital_id: "HOSP_NGP_001"}), (p1:Procedure {procedure_id: "PROC_001"})
MERGE (h)-[:OFFERS_PROCEDURE {annual_volume: 620, success_rate: 0.98}]->(p1);

MATCH (h:Hospital {hospital_id: "HOSP_NGP_001"}), (p2:Procedure {procedure_id: "PROC_002"})
MERGE (h)-[:OFFERS_PROCEDURE {annual_volume: 450, success_rate: 0.97}]->(p2);
```

---

## 15. Vector Index for Hybrid RAG Retrieval

```cypher
// ══════════════════════════════════════════════════════════════
// CREATE VECTOR INDEXES (Neo4j 5.11+ required)
// embedding dimension = 1536 (OpenAI) or 768 (MiniLM-L6)
// ══════════════════════════════════════════════════════════════

CREATE VECTOR INDEX symptom_embedding_idx IF NOT EXISTS
FOR (s:Symptom) ON s.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 768,
  `vector.similarity_function`: 'cosine'
}};

CREATE VECTOR INDEX disease_embedding_idx IF NOT EXISTS
FOR (d:Disease) ON d.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 768,
  `vector.similarity_function`: 'cosine'
}};

CREATE VECTOR INDEX hospital_embedding_idx IF NOT EXISTS
FOR (h:Hospital) ON h.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 768,
  `vector.similarity_function`: 'cosine'
}};

CREATE VECTOR INDEX guideline_embedding_idx IF NOT EXISTS
FOR (g:ClinicalGuideline) ON g.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 768,
  `vector.similarity_function`: 'cosine'
}};
```

### Python Embedding Population Script

```python
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "healthcareAI@2025"))

def embed_nodes(label: str, text_field: str, extra_fields: list = []):
    with driver.session() as session:
        nodes = session.run(
            f"MATCH (n:{label}) RETURN n.{text_field} AS text, "
            + ", ".join([f"n.{f} AS {f}" for f in ["symptom_id","icd10_code","hospital_id","procedure_id"] if f != text_field])
            + f", elementId(n) AS eid"
        ).data()

        for node in nodes:
            combined_text = " ".join([str(node.get(f, "")) for f in [text_field] + extra_fields if node.get(f)])
            embedding = model.encode(combined_text).tolist()
            session.run(
                f"MATCH (n:{label}) WHERE elementId(n) = $eid SET n.embedding = $emb",
                {"eid": node["eid"], "emb": embedding}
            )
        print(f"Embedded {len(nodes)} {label} nodes.")

embed_nodes("Symptom",  "name",       extra_fields=["colloquial_terms"])
embed_nodes("Disease",  "short_name", extra_fields=["name", "category"])
embed_nodes("Hospital", "name",       extra_fields=["city", "state"])
embed_nodes("Procedure","short_name", extra_fields=["name"])
```

---

## 16. LangChain Agent Query Patterns (Cypher Templates)

These Cypher queries are invoked by the `GraphCypherQAChain` in LangChain when the agent needs deterministic graph traversal:

### Q1 — Symptom → Disease → Procedure → Cost (Full Pathway)

```cypher
// Agent Query: "What treatment and costs for [SYMPTOM] in [CITY]?"
MATCH (s:Symptom)-[:INDICATES]->(d:Disease)-[:REQUIRES_PROCEDURE]->(proc:Procedure)
MATCH (proc)-[:HAS_PHASE]->(phase:PathwayPhase)-[:HAS_COST_COMPONENT]->(cost:CostComponent)
MATCH (city:City {name: $city_name})-[:CITY_BELONGS_TO]->(tier:GeographicTier)
WHERE s.name CONTAINS $symptom OR any(t IN s.colloquial_terms WHERE toLower(t) CONTAINS toLower($symptom))
RETURN
  d.short_name AS disease,
  d.icd10_code AS icd10,
  proc.short_name AS procedure,
  proc.base_cost_min_inr AS total_min,
  proc.base_cost_max_inr AS total_max,
  tier.cost_multiplier AS geo_multiplier,
  toInteger(proc.base_cost_min_inr * tier.cost_multiplier) AS adjusted_min,
  toInteger(proc.base_cost_max_inr * tier.cost_multiplier) AS adjusted_max,
  collect({
    phase: phase.phase_name,
    order: phase.phase_order,
    component: cost.description,
    min: toInteger(cost.base_cost_min_inr * tier.cost_multiplier),
    max: toInteger(cost.base_cost_max_inr * tier.cost_multiplier),
    variants: cost.variants
  }) AS cost_breakdown
ORDER BY phase.phase_order
```

### Q2 — Hospital Ranking by Fusion Score for a Procedure in a City

```cypher
// Agent Query: "Best hospitals for [PROCEDURE] near [CITY]?"
MATCH (h:Hospital)-[:LOCATED_IN]->(c:City {name: $city_name})
MATCH (h)-[:OFFERS_PROCEDURE]->(proc:Procedure)
WHERE proc.short_name CONTAINS $procedure_name OR proc.name CONTAINS $procedure_name
RETURN
  h.hospital_id,
  h.name AS hospital,
  h.segment AS tier_segment,
  h.fusion_score,
  h.clinical_score,
  h.reputation_score,
  h.accessibility_score,
  h.affordability_score,
  h.cardiology_waiting_proxy AS waiting_time,
  h.is_nabh_accredited AS nabh,
  h.cashless_insurers,
  h.latitude, h.longitude,
  proc.base_cost_min_inr AS base_min,
  proc.base_cost_max_inr AS base_max
ORDER BY h.fusion_score DESC
LIMIT 5
```

### Q3 — Comorbidity-Adjusted Cost Calculation

```cypher
// Agent Query: "Angioplasty cost for patient with heart failure and diabetes in Raipur?"
MATCH (proc:Procedure {procedure_id: $procedure_id})
MATCH (city:City {name: $city_name})-[:CITY_BELONGS_TO]->(tier:GeographicTier)
MATCH (cm:Comorbidity)
WHERE cm.name IN $comorbidity_list
WITH proc, tier, collect(cm.cost_multiplier_weight) AS weights
WITH proc, tier, weights,
  toInteger(proc.base_cost_min_inr * tier.cost_multiplier) AS adj_min,
  toInteger(proc.base_cost_max_inr * tier.cost_multiplier) AS adj_max,
  reduce(total = 0.0, w IN weights | total + w) AS total_omega
RETURN
  adj_min AS geo_adjusted_min,
  adj_max AS geo_adjusted_max,
  toInteger(adj_min * (1 + total_omega)) AS final_estimated_min,
  toInteger(adj_max * (1 + total_omega)) AS final_estimated_max,
  total_omega AS comorbidity_multiplier_sum,
  tier.tier_name AS geographic_tier,
  tier.cost_multiplier AS geo_factor
```

### Q4 — NBFC Loan Eligibility Check

```cypher
// Agent Query: Evaluate loan eligibility for given financial profile
WITH $monthly_income AS income,
     $existing_emis AS existing_emis,
     $procedure_cost AS proc_cost,
     $loan_tenure_months AS tenure
WITH income, existing_emis, proc_cost, tenure,
  proc_cost * 0.80 AS loan_amount
WITH income, existing_emis, loan_amount, tenure,
  round((loan_amount * 0.012 * power(1.012, tenure)) / (power(1.012, tenure) - 1), 0) AS proposed_emi
WITH income, existing_emis, proposed_emi,
  round(((existing_emis + proposed_emi) / income) * 100, 2) AS dti_ratio
MATCH (band:NBFCRiskBand)
WHERE band.dti_min <= dti_ratio < band.dti_max
RETURN
  dti_ratio,
  proposed_emi,
  band.risk_flag AS risk_level,
  band.interest_rate_min AS rate_min,
  band.interest_rate_max AS rate_max,
  band.approval_likelihood,
  band.cta_text,
  band.underwriting_label
```

### Q5 — Symptom Severity Classification Context Fetch

```cypher
// Fetch severity context for LLM Symptom Severity Classifier
MATCH (s:Symptom)
WHERE s.name CONTAINS $query_symptom
  OR any(term IN s.colloquial_terms WHERE toLower(term) CONTAINS toLower($query_symptom))
RETURN
  s.name AS symptom,
  s.severity_hint AS recommended_triage,
  s.icd10_hint AS icd10_prefix,
  s.anatomical_region
ORDER BY
  CASE s.severity_hint WHEN 'RED' THEN 0 WHEN 'YELLOW' THEN 1 ELSE 2 END
LIMIT 3
```

---

## 17. ICD-10 Bulk Import Pipeline

```python
"""
Bulk import ICD-10-CM codes from the smog1210/2022-ICD-10-CM-JSON GitHub repository.
Source: https://github.com/smog1210/2022-ICD-10-CM-JSON
"""
import requests, json
from neo4j import GraphDatabase

ICD10_URL = "https://raw.githubusercontent.com/smog1210/2022-ICD-10-CM-JSON/main/icd10cm_codes_2022.json"
driver    = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "healthcareAI@2025"))

# Download ICD-10 JSON
response = requests.get(ICD10_URL, timeout=60)
icd_data = response.json()  # List of {code: str, description: str}

# Filter to clinically relevant top-level chapters
RELEVANT_PREFIXES = [
    "I",   # Circulatory diseases
    "M",   # Musculoskeletal diseases
    "E",   # Endocrine/Metabolic diseases
    "N",   # Genitourinary diseases
    "R",   # Symptoms and signs
    "J",   # Respiratory diseases
    "K",   # Digestive diseases
    "C",   # Neoplasms
    "G",   # Nervous system diseases
    "Z",   # Health status factors
]

def should_import(code: str) -> bool:
    return any(code.startswith(prefix) for prefix in RELEVANT_PREFIXES)

filtered = [entry for entry in icd_data if should_import(entry["code"])]
print(f"Importing {len(filtered)} ICD-10 codes out of {len(icd_data)} total")

# Batch upsert into Neo4j as MedicalOntology nodes
BATCH_SIZE = 500
def batch_import(records):
    with driver.session() as session:
        session.run("""
            UNWIND $records AS rec
            MERGE (m:MedicalOntology {ontology_id: "ICD10_" + rec.code})
            SET m.code        = rec.code,
                m.description = rec.description,
                m.ontology_type = "ICD10",
                m.chapter       = left(rec.code, 1)
        """, {"records": records})

for i in range(0, len(filtered), BATCH_SIZE):
    batch = filtered[i:i+BATCH_SIZE]
    batch_import(batch)
    print(f"Imported batch {i//BATCH_SIZE + 1}")

# Link existing Disease nodes to MedicalOntology
with driver.session() as session:
    session.run("""
        MATCH (d:Disease), (m:MedicalOntology)
        WHERE m.code = d.icd10_code
           OR m.code STARTS WITH left(d.icd10_code, 3)
        MERGE (d)-[:CLASSIFIED_AS {code: m.code}]->(m)
    """)
    print("Diseases linked to ICD-10 ontology nodes.")

print("ICD-10 import complete.")
```

---

## 18. Data Validation & Integrity Checks

Run these after all seed data is loaded:

```cypher
// ─── CHECK 1: All Diseases have at least one linked Procedure ────
MATCH (d:Disease)
WHERE NOT (d)-[:REQUIRES_PROCEDURE]->()
RETURN d.short_name AS disease_without_procedure, d.icd10_code;

// ─── CHECK 2: All Procedures have complete 4-phase pathways ──────
MATCH (p:Procedure)
WITH p, size((p)-[:HAS_PHASE]->()) AS phase_count
WHERE phase_count < 4
RETURN p.short_name AS incomplete_procedure, phase_count;

// ─── CHECK 3: All Phases have at least one CostComponent ─────────
MATCH (ph:PathwayPhase)
WHERE NOT (ph)-[:HAS_COST_COMPONENT]->()
RETURN ph.phase_name AS phase_without_cost, ph.phase_id;

// ─── CHECK 4: All Hospitals have computed fusion scores ───────────
MATCH (h:Hospital)
WHERE h.fusion_score = 0.0 OR h.fusion_score IS NULL
RETURN h.name, h.hospital_id;

// ─── CHECK 5: All Cities linked to a GeographicTier ──────────────
MATCH (c:City)
WHERE NOT (c)-[:CITY_BELONGS_TO]->()
RETURN c.name AS unlinked_city;

// ─── CHECK 6: All Symptoms map to at least one Disease ───────────
MATCH (s:Symptom)
WHERE NOT (s)-[:INDICATES]->()
RETURN s.name AS orphan_symptom;

// ─── CHECK 7: NBFCRiskBand DTI ranges are contiguous ─────────────
MATCH (b:NBFCRiskBand)
RETURN b.band_id, b.dti_min, b.dti_max, b.risk_flag
ORDER BY b.dti_min;

// ─── CHECK 8: Graph connectivity summary ─────────────────────────
MATCH (n) RETURN labels(n)[0] AS label, count(n) AS node_count ORDER BY node_count DESC;
MATCH ()-[r]->() RETURN type(r) AS relationship, count(r) AS count ORDER BY count DESC;
```

---

## 19. Maintenance & Update Procedures

### 19.1 Updating Hospital Fusion Scores (Run Weekly)

```cypher
// Recalculate after ABSA pipeline updates reputation_score
MATCH (h:Hospital)
SET h.fusion_score = round(
  (0.40 * coalesce(h.clinical_score, 0)) +
  (0.25 * coalesce(h.reputation_score, 0)) +
  (0.20 * coalesce(h.accessibility_score, 0)) +
  (0.15 * coalesce(h.affordability_score, 0)),
  3
);
```

### 19.2 Updating Waiting Time Proxies (Run Daily)

```cypher
// Refresh appointment availability proxy for all hospitals
MATCH (h:Hospital)-[rel:HAS_DEPARTMENT]->(d:Department {dept_id: "DEPT_CARD"})
WITH h, rel.active_specialists AS spec_count
SET h.cardiology_waiting_proxy = CASE
  WHEN h.has_emergency = true THEN "24/7 emergency available ✅"
  WHEN spec_count >= 5 THEN "Appointments usually available within 2-3 days"
  WHEN spec_count >= 2 THEN "Estimated waiting time: 4-7 days"
  ELSE "Waiting time: 1-2 weeks"
END;
```

### 19.3 Adding a New Hospital

```cypher
// Template for adding a new hospital
MERGE (h:Hospital {hospital_id: "HOSP_NEW_001"})
SET h += {
  name: "Hospital Name Here",
  city: "City Name",
  state: "State Name",
  tier: "TIER_2",          // TIER_1 | TIER_2 | TIER_3
  latitude: 0.0000,
  longitude: 0.0000,
  total_beds: 0,
  icu_beds: 0,
  segment: "MID_TIER",     // PREMIUM | MID_TIER | BUDGET
  is_nabh_accredited: false,
  is_jci_accredited: false,
  bed_turnover_rate: 40.0,
  cashless_insurers: [],
  has_emergency: false,
  has_24hr_pharmacy: false,
  clinical_score: 0.60,    // Assign based on accreditation + volume
  reputation_score: 0.60,  // Populate from ABSA pipeline output
  accessibility_score: 0.70,
  affordability_score: 0.75
};
// Then run the fusion score recalculation query above.
// Then MERGE (h)-[:LOCATED_IN]->(city), (h)-[:OFFERS_PROCEDURE]->(proc), etc.
```

### 19.4 Adding a New Procedure

```cypher
// Step 1: Create Procedure node
MERGE (proc:Procedure {procedure_id: "PROC_NEW"})
SET proc += { name: "...", short_name: "...", specialty_required: "...", ... };

// Step 2: Create 4 PathwayPhase nodes (PRE, SURGICAL, HOSPITAL_STAY, POST)
// Step 3: Create CostComponent nodes per phase
// Step 4: Link: Disease -[:REQUIRES_PROCEDURE]-> Procedure -[:HAS_PHASE]-> Phase -[:HAS_COST_COMPONENT]-> Cost
// Step 5: Link: Hospital -[:OFFERS_PROCEDURE]-> Procedure (for all capable hospitals)
// Step 6: Embed the procedure node using the Python embedding script
```

---

## Summary Checklist

| Step | Task | Status |
|---|---|---|
| 1 | Neo4j 5.18+ running with APOC + GDS plugins | ☐ |
| 2 | Run all `CREATE CONSTRAINT` and `CREATE INDEX` statements | ☐ |
| 3 | Seed GeographicTier and NBFCRiskBand nodes | ☐ |
| 4 | Seed Symptom and Disease nodes (with ICD-10 codes) | ☐ |
| 5 | Seed Procedure, PathwayPhase, and CostComponent nodes | ☐ |
| 6 | Seed City nodes and link to GeographicTiers | ☐ |
| 7 | Seed Hospital nodes and compute fusion scores | ☐ |
| 8 | Seed Comorbidity nodes with empirical ωᵢ weights | ☐ |
| 9 | Seed Department nodes and link to hospitals | ☐ |
| 10 | Seed InsurancePolicy nodes and link to procedures | ☐ |
| 11 | Run all relationship-creation Cypher scripts | ☐ |
| 12 | Create vector indexes | ☐ |
| 13 | Run Python embedding population script | ☐ |
| 14 | Bulk import ICD-10-CM codes via Python pipeline | ☐ |
| 15 | Run all data validation integrity checks | ☐ |
| 16 | Test LangChain Cypher query templates against live graph | ☐ |
| 17 | Configure LangChain `Neo4jGraph` connection in application | ☐ |

---

*This document is the single source of truth for the Healthcare AI Navigator's Neo4j knowledge graph. All LangChain agents, GraphCypherQAChain instances, and RAG retrieval pipelines must reference this schema to ensure deterministic, clinically grounded graph traversal.*
