# Knowledge Graph Implementation Strategy
### AI-Powered Healthcare Navigator & Cost Estimator
> Strictly derived from: *Architecting an AI-Powered Healthcare Navigator and Cost Estimator: A Comprehensive Implementation Strategy*

---

## Table of Contents

1. [Overview & Architectural Role](#1-overview--architectural-role)
2. [Technology Stack Selection](#2-technology-stack-selection)
3. [Graph Schema Design — Node & Relationship Taxonomy](#3-graph-schema-design--node--relationship-taxonomy)
4. [Data Ingestion Pipeline](#4-data-ingestion-pipeline)
5. [Medical Ontology Integration (ICD-10 / SNOMED CT)](#5-medical-ontology-integration-icd-10--snomed-ct)
6. [NER Pipeline → Graph Population](#6-ner-pipeline--graph-population)
7. [LangChain Orchestration Layer — Cypher Query Generation](#7-langchain-orchestration-layer--cypher-query-generation)
8. [Vector Index Layer (Hybrid GraphRAG)](#8-vector-index-layer-hybrid-graphrag)
9. [Graph Traversal Logic — Clinical Pathway Resolution](#9-graph-traversal-logic--clinical-pathway-resolution)
10. [Geographic Pricing Nodes & Cost Multiplier Logic](#10-geographic-pricing-nodes--cost-multiplier-logic)
11. [Comorbidity & Age Adjustment Sub-Graph](#11-comorbidity--age-adjustment-sub-graph)
12. [Multi-Source Data Fusion Score — Graph Aggregation](#12-multi-source-data-fusion-score--graph-aggregation)
13. [Appointment Availability Proxy — Queuing Theory in the Graph](#13-appointment-availability-proxy--queuing-theory-in-the-graph)
14. [RAG Confidence Scoring — Groundedness Validation](#14-rag-confidence-scoring--groundedness-validation)
15. [XAI Integration — SHAP on Graph Outputs](#15-xai-integration--shap-on-graph-outputs)
16. [Session Management & Multi-Turn Memory](#16-session-management--multi-turn-memory)
17. [End-to-End Request Flow Diagram](#17-end-to-end-request-flow-diagram)
18. [Implementation Checklist](#18-implementation-checklist)

---

## 1. Overview & Architectural Role

The Knowledge Graph (KG) is the **foundational intelligence layer** of the entire healthcare navigator platform. It is not a peripheral component — it is the single source of deterministic truth from which all other modules (cost estimation, hospital ranking, loan pre-underwriting, insurance transparency) draw their structured facts.

### Why a Knowledge Graph Over Plain Vector RAG?

Traditional vector-only RAG pipelines rely entirely on semantic similarity search. While effective for fuzzy text matching, they **cannot** capture:

- Deterministic clinical relationships (e.g., *Symptom X → always requires Diagnostic Y before Procedure Z*)
- Hierarchical medical classifications (ICD-10 parent-child codes)
- Multi-hop traversals (Patient Location → Nearby Hospital → Specialist Department → Available Procedure → Cost Range)
- Financial relationship chains (Procedure Cost → Geographic Multiplier → Comorbidity Multiplier → DTI Risk Band)

By implementing a **GraphRAG hybrid architecture** using Neo4j, the system merges:
- **Structured symbolic reasoning** via Cypher graph traversal
- **Unstructured text retrieval** via an embedded vector index

This dual-layer architecture guarantees that patient queries receive both logically consistent clinical pathways AND contextually enriched, up-to-date guidance.

---

## 2. Technology Stack Selection

| Component | Technology | Purpose |
|---|---|---|
| Graph Database | **Neo4j** (property graph model) | Stores all clinical, geographic, financial, and provider nodes & relationships |
| Graph Query Language | **Cypher** | Deterministic traversal of clinical and financial pathways |
| LLM Orchestration | **LangChain** (`GraphCypherQAChain`) | Translates natural language queries into Cypher; manages agentic flow |
| NER Engine | Custom NER model (spaCy / Hugging Face) | Extracts medical entities from free-text user input |
| Medical Ontology | **ICD-10-CM JSON** (2022, CMS-sourced via GitHub) | Maps colloquial symptoms to standardized diagnostic codes |
| Vector Index | Neo4j vector index (or FAISS sidecar) | Retrieves unstructured clinical guidelines, reviews, and protocol updates |
| Frontend | **Streamlit** | Renders the patient-facing dashboard and comparison panes |
| Geo-Spatial | **Geopy** + **Leaflet.js** (via streamlit-folium) | Resolves user locations and plots hospital markers |
| XAI | **SHAP** (TreeExplainer / KernelExplainer) + **LIME** | Explains graph-driven recommendation scores to end users |

---

## 3. Graph Schema Design — Node & Relationship Taxonomy

This section defines every **node type** and **relationship type** that must be created in Neo4j before ingestion begins.

### 3.1 Node Types

```
(:Symptom)
  Properties: name, icd10_code, severity_hint, body_region

(:Disease)
  Properties: name, icd10_code, icd10_description, category

(:Procedure)
  Properties: name, procedure_code, type [surgical|diagnostic|therapeutic],
              avg_duration_hours, requires_icu [boolean]

(:CostComponent)
  Properties: phase [pre_procedure|procedure|hospital_stay|post_procedure],
              description, base_cost_min_inr, base_cost_max_inr

(:Hospital)
  Properties: name, tier [Premium|Mid-tier|Budget], city, state,
              city_tier [1|2|3], lat, lon, nabh_accredited [boolean],
              jci_accredited [boolean], total_beds, bed_turnover_rate,
              overall_star_rating, fusion_score

(:Specialist)
  Properties: name, department, qualification, active [boolean]

(:Geography)
  Properties: city_name, state, city_tier [1|2|3],
              geo_adjustment_factor (γ_geo), icu_daily_rate_inr

(:Comorbidity)
  Properties: condition_name, icd10_code, cost_multiplier_weight (ω_i),
              risk_category [ASCVD|HF|CKD|Diabetes|Other]

(:InsuranceTier)
  Properties: hospital_id, insurer_name, empaneled [boolean],
              avg_reimbursement_rate, cashless_success_rate

(:ReviewAspect)
  Properties: hospital_id, aspect [doctors|staff|facilities|affordability],
              vader_compound_score, lda_topic_label
```

### 3.2 Relationship Types

```
(:Symptom)-[:INDICATES]->(:Disease)
(:Disease)-[:REQUIRES_WORKUP]->(:Procedure)       // diagnostic procedures
(:Disease)-[:TREATED_BY]->(:Procedure)            // interventional procedures
(:Procedure)-[:HAS_COST_COMPONENT]->(:CostComponent)
(:Procedure)-[:PRECEDES]->(:Procedure)            // pathway sequencing
(:Hospital)-[:LOCATED_IN]->(:Geography)
(:Hospital)-[:OFFERS_PROCEDURE]->(:Procedure)
(:Hospital)-[:EMPLOYS]->(:Specialist)
(:Specialist)-[:SPECIALIZES_IN]->(:Disease)
(:Hospital)-[:HAS_REVIEW_ASPECT]->(:ReviewAspect)
(:Hospital)-[:COVERED_BY]->(:InsuranceTier)
(:Comorbidity)-[:ELEVATES_COST_FOR]->(:Procedure)
(:Geography)-[:APPLIES_MULTIPLIER_TO]->(:CostComponent)
```

---

## 4. Data Ingestion Pipeline

Data flows into the Knowledge Graph through three parallel ingestion tracks.

### Track A — Structured Clinical Data

**Source:** ICD-10-CM 2022 JSON (GitHub: `smog1210/2022-ICD-10-CM-JSON`, originally from CMS.gov)

**Steps:**

1. Download the ICD-10-CM JSON file.
2. Parse each entry to extract: `code`, `description`, `parent_code`, `leaf [boolean]`.
3. Create `(:Disease)` nodes for all leaf-level diagnostic codes.
4. Create `(:Symptom)` nodes for codes in the R-block (symptoms, signs, abnormal findings).
5. Create `[:INDICATES]` relationships from symptom codes to their parent disease chapters using ICD-10 hierarchical logic.
6. Seed `(:Procedure)` nodes from a curated procedure registry (CPT-equivalent codes for Indian context): at minimum include Angioplasty, Total Knee Replacement (TKR), Coronary Artery Bypass Grafting (CABG), Dialysis, Appendectomy.
7. Create `[:TREATED_BY]` and `[:REQUIRES_WORKUP]` relationships manually or via a mapping config file.

**Sample Cypher — Disease Node Creation:**
```cypher
MERGE (d:Disease {icd10_code: $code})
SET d.name = $description,
    d.category = $category
```

**Sample Cypher — Symptom → Disease:**
```cypher
MATCH (s:Symptom {icd10_code: $symptom_code})
MATCH (d:Disease {icd10_code: $disease_code})
MERGE (s)-[:INDICATES]->(d)
```

### Track B — Hospital & Geographic Data

**Source:** Synthetic dataset seeded from publicly available hospital directories (NHA, state health portals), enriched with the Kearney India Healthcare Index for geographic multipliers.

**Steps:**

1. For each hospital record, create a `(:Hospital)` node with all properties listed in §3.1.
2. Resolve the hospital's city to a `(:Geography)` node using the city-tier mapping table (see §10).
3. Link `(:Hospital)-[:LOCATED_IN]->(:Geography)`.
4. For each specialist on record, create `(:Specialist)` nodes and link with `[:EMPLOYS]`.
5. Link `(:Hospital)-[:OFFERS_PROCEDURE]->(:Procedure)` for each procedure the hospital is verified to perform.

### Track C — Sentiment & Review Data

**Source:** Google Maps API, healthcare forums (scraped & pre-processed).

**Steps:**

1. Run ABSA (Aspect-Based Sentiment Analysis) pipeline offline — see §12 for scoring.
2. For each hospital, create four `(:ReviewAspect)` nodes (one per aspect dimension).
3. Store VADER compound score and LDA topic label on each `(:ReviewAspect)` node.
4. Link `(:Hospital)-[:HAS_REVIEW_ASPECT]->(:ReviewAspect)`.

---

## 5. Medical Ontology Integration (ICD-10 / SNOMED CT)

The ICD-10 integration is the **controlled vocabulary anchor** of the entire system. Every entity extracted by the NER pipeline must resolve to a canonical ICD-10 code before any graph traversal begins.

### 5.1 Lookup Dictionary Construction

```python
import json

with open("icd10cm_2022.json", "r") as f:
    icd_data = json.load(f)

# Build lookup: {description_lower: icd10_code}
icd_lookup = {
    entry["description"].lower(): entry["code"]
    for entry in icd_data
    if entry.get("leaf", False)
}
```

### 5.2 Colloquial → ICD-10 Mapping

The NER model extracts raw phrases (e.g., *"severe chest pain"*, *"knee swelling"*). These pass through a two-step resolution:

1. **Exact match** against `icd_lookup`.
2. **Fuzzy match** (RapidFuzz or sentence-transformers cosine similarity) for phrases not in the dictionary.

**Example resolution:**
```
User input: "severe chest pain radiating to left arm"
NER extracts: ["chest pain", "left arm"]
ICD-10 resolve:
  "chest pain" → R07.9 (Chest pain, unspecified)
  Graph traversal: R07.9 → [:INDICATES] → I25 (Chronic ischemic heart disease)
  I25 → [:TREATED_BY] → Angioplasty / CABG
```

### 5.3 SNOMED CT Extension (Optional Phase 2)

For higher clinical fidelity, SNOMED CT concept IDs can be added as an additional property on `(:Disease)` and `(:Symptom)` nodes (`snomed_id`). This enables cross-referencing with international clinical guidelines loaded into the vector index.

---

## 6. NER Pipeline → Graph Population

### 6.1 NER Model Configuration

Use a medical NER model (e.g., `en_core_sci_lg` from scispaCy, or a fine-tuned BERT variant) with the following entity labels:

| NER Label | Maps To | Example |
|---|---|---|
| `CONDITION` | `(:Disease)` node | "coronary artery disease" |
| `SYMPTOM` | `(:Symptom)` node | "chest pain", "shortness of breath" |
| `BODY_PART` | Traversal hint | "left knee", "heart" |
| `PROCEDURE` | `(:Procedure)` node | "angioplasty", "knee replacement" |
| `MEDICATION` | Contextual enrichment | "metformin", "statins" |

### 6.2 Pipeline Flow

```
User free-text input
        ↓
[NER Model] → extracts entities with labels
        ↓
[ICD-10 Lookup] → resolves each entity to a canonical code
        ↓
[Neo4j Node Match] → MATCH (:Symptom {icd10_code: $resolved_code})
        ↓
[Cypher Traversal] → traverse INDICATES / TREATED_BY relationships
        ↓
[Procedure + Cost Nodes Retrieved]
```

---

## 7. LangChain Orchestration Layer — Cypher Query Generation

### 7.1 GraphCypherQAChain Setup

LangChain's `GraphCypherQAChain` is the primary orchestration component that translates the enriched user prompt (post-NER, post-ICD-10 resolution) into executable Cypher queries.

```python
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_anthropic import ChatAnthropic

graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password=NEO4J_PASSWORD
)

llm = ChatAnthropic(model="claude-sonnet-4-20250514")

chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    validate_cypher=True,          # prevents hallucinated node labels
    return_intermediate_steps=True # needed for RAG confidence scoring
)
```

### 7.2 Schema Injection (System Prompt)

The LLM must receive the full graph schema in its system prompt to generate valid Cypher. Inject the schema as follows:

```python
SCHEMA_PROMPT = """
You are a Cypher query expert for a Neo4j healthcare knowledge graph.
Node labels: Symptom, Disease, Procedure, CostComponent, Hospital,
             Specialist, Geography, Comorbidity, InsuranceTier, ReviewAspect
Key relationships:
  (Symptom)-[:INDICATES]->(Disease)
  (Disease)-[:TREATED_BY]->(Procedure)
  (Procedure)-[:HAS_COST_COMPONENT]->(CostComponent)
  (Hospital)-[:LOCATED_IN]->(Geography)
  (Hospital)-[:OFFERS_PROCEDURE]->(Procedure)
  (Hospital)-[:HAS_REVIEW_ASPECT]->(ReviewAspect)
  (Comorbidity)-[:ELEVATES_COST_FOR]->(Procedure)
Always MATCH by icd10_code property when filtering diseases or symptoms.
Never RETURN more than 10 nodes in a single query. Use LIMIT.
"""
```

### 7.3 Example Generated Cypher Queries

**Query: Find hospitals offering Angioplasty near Raipur (Tier 3):**
```cypher
MATCH (h:Hospital)-[:OFFERS_PROCEDURE]->(p:Procedure {name: "Angioplasty"})
MATCH (h)-[:LOCATED_IN]->(g:Geography {city_name: "Raipur"})
MATCH (h)-[:HAS_REVIEW_ASPECT]->(r:ReviewAspect {aspect: "doctors"})
RETURN h.name, h.tier, h.nabh_accredited, h.fusion_score,
       r.vader_compound_score, g.geo_adjustment_factor
ORDER BY h.fusion_score DESC
LIMIT 5
```

**Query: Get cost breakdown for Angioplasty:**
```cypher
MATCH (p:Procedure {name: "Angioplasty"})-[:HAS_COST_COMPONENT]->(c:CostComponent)
RETURN c.phase, c.description, c.base_cost_min_inr, c.base_cost_max_inr
ORDER BY c.phase
```

**Query: Apply comorbidity multiplier for heart failure patient:**
```cypher
MATCH (co:Comorbidity {condition_name: "Heart Failure"})-[:ELEVATES_COST_FOR]->(p:Procedure {name: "Angioplasty"})
RETURN co.cost_multiplier_weight AS omega_i
```

---

## 8. Vector Index Layer (Hybrid GraphRAG)

Alongside the deterministic graph, a **vector index** is embedded within Neo4j (or as a FAISS sidecar) to handle unstructured content retrieval.

### 8.1 What Goes Into the Vector Index

| Document Type | Example Content |
|---|---|
| Clinical guidelines | Updated AHA/ACC protocols for CAD management |
| Hospital policy documents | Room rent capping policies, cashless empanelment notices |
| Unstructured patient reviews | Raw Google Maps review text (pre-ABSA) |
| Drug/consumable pricing updates | NPPA (National Pharmaceutical Pricing Authority) notifications |

### 8.2 Embedding & Indexing

```python
from langchain_community.vectorstores import Neo4jVector
from langchain_anthropic import AnthropicEmbeddings

vector_store = Neo4jVector.from_existing_graph(
    embedding=AnthropicEmbeddings(),
    url="bolt://localhost:7687",
    username="neo4j",
    password=NEO4J_PASSWORD,
    index_name="healthcare_vector_index",
    node_label="Document",
    text_node_properties=["content"],
    embedding_node_property="embedding"
)
retriever = vector_store.as_retriever(search_kwargs={"k": 5})
```

### 8.3 Hybrid Retrieval Execution

When a user query arrives, the LangChain agent triggers **both** retrievers in parallel:

1. **Cypher traversal** → deterministic structured facts (costs, pathways, hospital data)
2. **Vector similarity search** → unstructured contextual enrichment (recent guidelines, reviews)

Both result sets are merged into a single enriched context payload sent to the LLM for final response generation.

---

## 9. Graph Traversal Logic — Clinical Pathway Resolution

This is the core clinical reasoning engine of the KG. It implements the multi-hop traversal that maps a patient's colloquial symptom description to a full, sequenced treatment pathway with associated costs.

### 9.1 Traversal Algorithm (Step-by-Step)

```
Step 1: NER extracts symptom entities from user input
Step 2: ICD-10 lookup resolves to canonical codes (e.g., R07.9)
Step 3: MATCH (:Symptom {icd10_code: "R07.9"})
Step 4: Traverse [:INDICATES] → reach (:Disease) node (e.g., I25 - Ischemic Heart Disease)
Step 5: Traverse [:REQUIRES_WORKUP] → collect diagnostic procedures
          e.g., ECG, Stress Test, Echocardiogram, Diagnostic Angiography
Step 6: Traverse [:TREATED_BY] → collect interventional procedures
          e.g., Angioplasty, CABG
Step 7: For each procedure, traverse [:HAS_COST_COMPONENT] → collect all CostComponent nodes
Step 8: Apply geographic multiplier (γ_geo) from linked (:Geography) node
Step 9: Apply comorbidity multipliers (Σ ω_i C_i) if comorbidities declared
Step 10: Return structured pathway matrix to LangChain agent for LLM formatting
```

### 9.2 Clinical Pathway Matrix Output Structure

The KG traversal must return data in this structure to enable the UI to render the phase-by-phase breakdown table:

```json
{
  "procedure": "Angioplasty",
  "disease": "Coronary Artery Disease",
  "pathway": [
    {
      "phase": "pre_procedure",
      "components": ["ECG", "Stress Test", "Echocardiogram", "Diagnostic Angiography"],
      "cost_min_inr": 10000,
      "cost_max_inr": 30000
    },
    {
      "phase": "procedure",
      "components": ["Balloon Angioplasty", "Drug-Eluting Stent Placement"],
      "cost_min_inr": 100000,
      "cost_max_inr": 250000
    },
    {
      "phase": "hospital_stay",
      "components": ["ICU Monitoring", "General Ward Recovery"],
      "cost_min_inr": 20000,
      "cost_max_inr": 60000
    },
    {
      "phase": "post_procedure",
      "components": ["Anti-platelets", "Statins", "Follow-up Consultations"],
      "cost_min_inr": 10000,
      "cost_max_inr": 30000
    }
  ]
}
```

### 9.3 Pathway Sequencing ([:PRECEDES] Traversal)

The `[:PRECEDES]` relationship enforces the **clinical ordering** of procedures. The traversal must respect this ordering:

```cypher
MATCH path = (start:Procedure {name: "Diagnostic Angiography"})
             -[:PRECEDES*1..5]->
             (end:Procedure {name: "Angioplasty"})
RETURN [node IN nodes(path) | node.name] AS ordered_pathway
```

This prevents the system from ever presenting a patient with a post-operative step before the procedure itself.

---

## 10. Geographic Pricing Nodes & Cost Multiplier Logic

### 10.1 Geography Node Seeding

Seed the `(:Geography)` nodes with the following benchmark values derived from the multi-site Indian healthcare cost study and the Kearney India Healthcare Index:

| City Tier | Example Cities | γ_geo (Multiplier) | ICU Daily Rate (₹) |
|---|---|---|---|
| Tier 1 | Mumbai, Delhi, Bangalore, Chennai | 1.00 (baseline) | 5,534 |
| Tier 2 | Nagpur, Jaipur, Surat, Lucknow | 0.917 | 5,427 |
| Tier 3 | Raipur, Ahmedabad (smaller), Nashik | 0.833 | 2,638 |

### 10.2 Adjusted Cost Formula (Stored as Graph Procedure)

The cost adjustment formula applied during graph traversal:

```
Adjusted_Cost = (Base_Clinical_Rate × γ_geo) + (Predicted_Days × Room_Rate × γ_geo)
```

**Implementation:** Store `γ_geo` on the `(:Geography)` node. During the Cypher traversal in Step 8 of §9.1, multiply all `CostComponent` values by the `γ_geo` retrieved from the linked `(:Geography)` node.

```cypher
MATCH (h:Hospital {name: $hospital_name})-[:LOCATED_IN]->(g:Geography)
MATCH (p:Procedure {name: $procedure_name})-[:HAS_COST_COMPONENT]->(c:CostComponent)
RETURN c.phase,
       c.base_cost_min_inr * g.geo_adjustment_factor AS adjusted_min,
       c.base_cost_max_inr * g.geo_adjustment_factor AS adjusted_max
```

### 10.3 Concrete Example

A Total Knee Replacement (TKR) baseline (Tier 1): ₹3,00,000

| City | γ_geo | Adjusted Estimate |
|---|---|---|
| Mumbai / Delhi (Tier 1) | 1.00 | ₹3,00,000 |
| Nagpur (Tier 2) | 0.917 | ₹2,75,000 |
| Raipur (Tier 3) | 0.833 | ₹2,50,000 |

---

## 11. Comorbidity & Age Adjustment Sub-Graph

### 11.1 Comorbidity Nodes to Seed

Seed the following `(:Comorbidity)` nodes with empirically derived weights from epidemiological literature:

| Condition | ICD-10 Code | ω_i (Weight) | Multiplier vs. Baseline |
|---|---|---|---|
| ASCVD (Atherosclerotic Cardiovascular Disease) | I25 | 0.55 | 2.2× |
| Heart Failure | I50 | 0.825 | 3.3× |
| Chronic Kidney Disease | N18 | 0.675 | 2.7× |
| Diabetes Mellitus (Type 2) | E11 | 0.40 | Elevated surgical risk |

> **Note:** The multiplier weights above are relative to the no-comorbidity baseline. The ω_i values stored on the graph are the **additive contingency weights** used in the formula below.

### 11.2 Final Estimated Cost Formula

```
Final_Estimated_Cost = Adjusted_Cost × (1 + Σ(ω_i × C_i))
```

Where:
- `C_i = 1` if the patient declares the comorbidity, `0` otherwise
- `ω_i` = weight stored on the `(:Comorbidity)` node
- The summation runs over all declared comorbidities

### 11.3 Cypher — Comorbidity Multiplier Retrieval

```cypher
MATCH (co:Comorbidity)-[:ELEVATES_COST_FOR]->(p:Procedure {name: $procedure_name})
WHERE co.condition_name IN $declared_comorbidities
RETURN SUM(co.cost_multiplier_weight) AS total_comorbidity_weight
```

**Python application logic:**

```python
def calculate_final_cost(adjusted_cost_min, adjusted_cost_max, total_omega):
    multiplier = 1 + total_omega
    return {
        "final_min": adjusted_cost_min * multiplier,
        "final_max": adjusted_cost_max * multiplier,
        "contingency_added_pct": total_omega * 100
    }
```

### 11.4 Age Adjustment

Age is treated as a soft modifier. Patients above 65 years receive an additional flat weight of `ω_age = 0.15` added to the summation, reflecting statistically elevated complication rates and longer recovery periods.

---

## 12. Multi-Source Data Fusion Score — Graph Aggregation

The `fusion_score` property on each `(:Hospital)` node is computed by aggregating four normalized sub-scores from the graph. This computation runs as a **batch Neo4j job** (triggered nightly or on data updates) and stores the result directly on the node.

### 12.1 Weighted Score Formula

```
Fusion_Score = (0.40 × Clinical_Score)
             + (0.25 × Reputation_Score)
             + (0.20 × Accessibility_Score)
             + (0.15 × Affordability_Score)
```

### 12.2 Component Score Computation

**Clinical Score (40%):**
```cypher
// Based on: procedure volume proxy + accreditation status
MATCH (h:Hospital)-[:OFFERS_PROCEDURE]->(p:Procedure)
WITH h, COUNT(p) AS procedure_count
RETURN h.name,
       (procedure_count / 20.0) * 0.6 +
       (CASE WHEN h.nabh_accredited THEN 0.3 ELSE 0.0 END) +
       (CASE WHEN h.jci_accredited THEN 0.1 ELSE 0.0 END) AS clinical_raw
```

**Reputation Score (25%):**
```cypher
MATCH (h:Hospital)-[:HAS_REVIEW_ASPECT]->(r:ReviewAspect)
WITH h, AVG(r.vader_compound_score) AS avg_vader,
     h.overall_star_rating AS stars
RETURN h.name,
       (avg_vader * 0.6) + ((stars / 5.0) * 0.4) AS reputation_raw
```

**Accessibility Score (20%):**
Combines geo-distance from patient (computed in Python via geopy) and the Appointment Availability Proxy (see §13).
```python
# In Python post-graph-retrieval:
from geopy.distance import geodesic

distance_km = geodesic((patient_lat, patient_lon), (hospital_lat, hospital_lon)).km
# Normalize: closer = higher score (inverse sigmoid)
import math
distance_score = 1 / (1 + math.exp(0.1 * (distance_km - 10)))
accessibility_score = (distance_score * 0.6) + (availability_proxy_score * 0.4)
```

**Affordability Score (15%):**
```cypher
MATCH (h:Hospital)-[:COVERED_BY]->(i:InsuranceTier)
RETURN h.name,
       AVG(i.cashless_success_rate) AS cashless_score,
       h.tier AS pricing_tier
```
Map pricing tier to score: `Budget → 1.0`, `Mid-tier → 0.7`, `Premium → 0.4`.

### 12.3 Min-Max Normalization (Mandatory)

All raw sub-scores must be normalized to [0, 1] before applying weights:

```python
def min_max_normalize(value, min_val, max_val):
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)
```

Apply this across all hospitals in the result set before computing the final fusion score.

### 12.4 Storing the Score

```cypher
MATCH (h:Hospital {name: $hospital_name})
SET h.fusion_score = $computed_fusion_score,
    h.score_updated_at = datetime()
```

---

## 13. Appointment Availability Proxy — Queuing Theory in the Graph

Since real-time API scheduling data does not exist across the Indian hospital ecosystem, the KG computes an **Appointment Availability Proxy** from structural data already stored on graph nodes.

### 13.1 Input Parameters (From Graph)

```cypher
MATCH (h:Hospital {name: $hospital_name})-[:EMPLOYS]->(s:Specialist)
WHERE s.department = $target_department
RETURN h.total_beds,
       h.bed_turnover_rate,
       COUNT(s) AS specialist_count,
       h.has_emergency_unit
```

### 13.2 Proxy Classification Logic

```python
def compute_availability_proxy(total_beds, bed_turnover_rate,
                                specialist_count, has_emergency_unit):
    if has_emergency_unit:
        return {"label": "24/7 emergency available ✅", "score": 1.0}

    throughput_index = (total_beds * bed_turnover_rate) / max(specialist_count, 1)

    if throughput_index > 150:
        return {"label": "Appointments usually available within 2-3 days", "score": 0.9}
    elif throughput_index > 80:
        return {"label": "Estimated waiting time: 4-7 days", "score": 0.6}
    else:
        return {"label": "Waiting time: 1-2 weeks", "score": 0.3}
```

### 13.3 Severity Override

If the Symptom Severity Classifier (§13.4) returns **Red (Emergency)**, the Appointment Availability Proxy is **bypassed** and the system unconditionally:
1. Filters hospitals to those with `has_emergency_unit = true`
2. Displays `"24/7 emergency available ✅"` for all shown results

### 13.4 Symptom Severity Classification (Graph-Integrated)

The LLM-based severity classifier operates on NER-extracted symptoms and uses the graph to validate clinical urgency heuristics:

```python
SEVERITY_PROMPT = """
You are a clinical triage assistant. Given the following symptoms extracted 
from a patient query, classify severity as EXACTLY one of:
RED (Emergency), YELLOW (Urgent), GREEN (Elective).

Symptoms: {symptoms}

Rules:
- Chest pain + left arm radiation = RED
- Difficulty breathing + cyanosis = RED  
- Fever > 3 days + joint pain = YELLOW
- Elective orthopedic consultation = GREEN

Output format: {{"severity": "RED|YELLOW|GREEN", "reason": "<brief clinical rationale>"}}
This is a routing tool only. Do not provide diagnosis or medical advice.
"""
```

---

## 14. RAG Confidence Scoring — Groundedness Validation

Every response generated by the LangChain agent must pass through a confidence scoring gate before being displayed to the user.

### 14.1 Confidence Score Formula

```
S = (0.4 × Faithfulness) + (0.3 × Contextual_Relevancy) + (0.3 × Answer_Relevancy)
```

### 14.2 Metric Definitions

| Metric | What It Measures | How to Compute |
|---|---|---|
| **Faithfulness** | Is every claim in the LLM response logically derivable from the retrieved Neo4j context? | Use DeepEval `FaithfulnessMetric` or Evidently AI LLM judge |
| **Contextual Relevancy** | Did the Cypher query + vector retrieval return information actually relevant to the user's query? | Cross-reference retrieved node labels against the NER-extracted entities |
| **Answer Relevancy** | Does the final response directly answer the user's question without drifting? | Use DeepEval `AnswerRelevancyMetric` |

### 14.3 Safety Threshold & UI Behavior

```python
CONFIDENCE_THRESHOLD = 0.70

def evaluate_and_display(response, confidence_score):
    if confidence_score < CONFIDENCE_THRESHOLD:
        st.warning("⚠️ Low confidence response. Data may be incomplete.")
        st.info("This system provides decision support only and does not "
                "constitute medical advice or diagnosis.")
    return response
```

### 14.4 Hallucination Prevention Checklist

The `validate_cypher=True` flag on `GraphCypherQAChain` is the first line of defense — it rejects Cypher referencing node labels or properties not in the schema. Additionally:

- All hospital names in responses must be verifiable via `MATCH (:Hospital {name: $name}) RETURN count(*) > 0`
- All cost figures must trace back to a `(:CostComponent)` node — no LLM-generated cost values are accepted
- Any response containing a specific ICD-10 code must match a code present in the graph

---

## 15. XAI Integration — SHAP on Graph Outputs

### 15.1 SHAP for Fusion Score Explanation

SHAP (SHapley Additive exPlanations) is applied to the **Multi-Source Data Fusion Score** to explain to the user *why* a specific hospital was ranked where it was.

```python
import shap
import numpy as np

# Feature vector for a hospital recommendation
features = np.array([[
    clinical_score,      # 40% weight
    reputation_score,    # 25% weight
    accessibility_score, # 20% weight
    affordability_score  # 15% weight
]])

feature_names = ["Clinical", "Reputation", "Accessibility", "Affordability"]
weights = np.array([0.40, 0.25, 0.20, 0.15])

# For a linear weighted model, SHAP values = weight × (feature - baseline)
baseline = np.array([0.5, 0.5, 0.5, 0.5])  # neutral baseline
shap_values = weights * (features[0] - baseline)

# Render waterfall plot in Streamlit
shap.waterfall_plot(
    shap.Explanation(
        values=shap_values,
        base_values=0.5,
        data=features[0],
        feature_names=feature_names
    )
)
```

**UI Output:** A waterfall plot showing, for example:
> "High Clinical Score (+0.19) and strong Accessibility (+0.14) pushed the score up. Affordability (-0.05) slightly reduced it."

### 15.2 LIME for Symptom Severity Explanation

LIME (Local Interpretable Model-agnostic Explanations) is applied to the **Symptom Severity Classifier** to explain why a query was flagged as Emergency.

```python
from lime.lime_text import LimeTextExplainer

explainer = LimeTextExplainer(class_names=["GREEN", "YELLOW", "RED"])

def predict_severity(texts):
    # Wrapper around the LLM severity classifier
    return [classify_severity(t) for t in texts]

explanation = explainer.explain_instance(
    user_query_text,
    predict_severity,
    num_features=6
)

# In Streamlit: highlight the triggering tokens
st.write("**Why this was flagged as Emergency:**")
for feature, weight in explanation.as_list():
    if weight > 0.1:
        st.markdown(f"🔴 `{feature}` — contributed strongly to Emergency classification")
```

---

## 16. Session Management & Multi-Turn Memory

The KG-backed agentic system must maintain conversation context across multi-turn interactions without cross-contaminating sessions in a multi-user Streamlit deployment.

### 16.1 Session-Isolated History

```python
from langchain_community.chat_message_histories import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Session store — keyed by unique session ID
session_store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]

# Bind the KG-powered chain to session history
chain_with_history = RunnableWithMessageHistory(
    graph_cypher_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)
```

### 16.2 Persistent Context Variables (Per Session)

The following variables must persist across turns within a session and be re-injected into each Cypher query:

```python
session_context = {
    "identified_procedure": None,      # e.g., "Angioplasty"
    "identified_disease": None,        # e.g., "Coronary Artery Disease"
    "declared_comorbidities": [],      # e.g., ["Diabetes", "Heart Failure"]
    "patient_age": None,
    "patient_city": None,
    "city_tier": None,
    "declared_income_monthly": None,
    "declared_existing_emis": None,
    "severity_flag": None              # RED | YELLOW | GREEN
}
```

When a user says "Will my diabetes affect this?" in turn 3, the agent accesses `session_context["identified_procedure"]` and `session_context["identified_disease"]` from turn 1, and adds `"Diabetes"` to `session_context["declared_comorbidities"]` — then re-traverses the comorbidity sub-graph without requiring the user to repeat context.

---

## 17. End-to-End Request Flow Diagram

```
USER INPUT (natural language)
        │
        ▼
┌─────────────────────┐
│   NER Pipeline      │  → Extracts: Symptoms, Conditions, Body Parts, Procedures
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  ICD-10 Lookup      │  → Resolves entities to canonical codes
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ Severity Classifier │  → RED / YELLOW / GREEN (LLM prompt-engineered)
└─────────────────────┘
        │
        ├─── RED ──────────────────────────────────────────────┐
        │                                                       │
        ▼                                                       ▼
┌───────────────────────────┐                   ┌──────────────────────────┐
│  LangChain GraphCypher    │                   │  Emergency Hospital Filter│
│  QAChain                  │                   │  (has_emergency_unit=true)│
│  ↓ Generates Cypher       │                   └──────────────────────────┘
│  ↓ Queries Neo4j KG       │
│  ↓ Traverses:             │
│    Symptom→Disease        │
│    Disease→Procedure      │
│    Procedure→CostComponent│
│    Hospital→Geography     │
│    Hospital→ReviewAspect  │
│    Comorbidity multipliers│
└───────────────────────────┘
        │                    │
        ▼                    ▼
┌─────────────┐    ┌──────────────────┐
│ Structured  │    │  Vector Index    │
│ Graph Data  │    │  (Unstructured   │
│ (Cypher)    │    │   Guidelines)    │
└─────────────┘    └──────────────────┘
        │                    │
        └──────────┬─────────┘
                   ▼
        ┌────────────────────┐
        │  Merged Context    │
        │  Payload → LLM     │
        └────────────────────┘
                   │
                   ▼
        ┌────────────────────┐
        │ RAG Confidence     │
        │ Scoring Gate       │
        │ (S ≥ 0.70 to pass) │
        └────────────────────┘
                   │
                   ▼
        ┌────────────────────┐
        │  Streamlit UI      │
        │  • Pathway table   │
        │  • Hospital compare│
        │  • SHAP waterfall  │
        │  • Leaflet map     │
        │  • DTI/EMI matrix  │
        └────────────────────┘
```

---

## 18. Implementation Checklist

Use this checklist to track KG implementation progress end-to-end.

### Phase 1 — Graph Database Setup
- [ ] Install Neo4j (Community or Enterprise)
- [ ] Configure bolt endpoint, credentials, APOC plugins
- [ ] Define and apply all node label constraints (`CREATE CONSTRAINT`)
- [ ] Create indexes on high-query properties: `icd10_code`, `city_name`, `procedure_name`

### Phase 2 — Data Ingestion
- [ ] Download ICD-10-CM 2022 JSON from CMS / GitHub
- [ ] Run Track A ingestion script → Disease, Symptom, Procedure nodes
- [ ] Run Track B ingestion → Hospital, Geography, Specialist nodes
- [ ] Seed Comorbidity nodes with ω_i weights
- [ ] Seed CostComponent nodes with base cost ranges (Angioplasty, TKR minimum)
- [ ] Run Track C ingestion → ReviewAspect nodes (post-ABSA)

### Phase 3 — Relationship Creation
- [ ] Create all `[:INDICATES]` relationships (Symptom → Disease)
- [ ] Create all `[:TREATED_BY]` relationships (Disease → Procedure)
- [ ] Create all `[:REQUIRES_WORKUP]` relationships
- [ ] Create `[:PRECEDES]` chain for each clinical pathway
- [ ] Create `[:HAS_COST_COMPONENT]` relationships
- [ ] Create `[:LOCATED_IN]` relationships (Hospital → Geography)
- [ ] Create `[:OFFERS_PROCEDURE]` relationships
- [ ] Create `[:EMPLOYS]` relationships (Hospital → Specialist)
- [ ] Create `[:ELEVATES_COST_FOR]` relationships (Comorbidity → Procedure)
- [ ] Create `[:COVERED_BY]` relationships (Hospital → InsuranceTier)

### Phase 4 — LangChain Integration
- [ ] Install: `langchain`, `langchain-community`, `neo4j`, `langchain-anthropic`
- [ ] Configure `Neo4jGraph` connection
- [ ] Build `GraphCypherQAChain` with schema prompt injection
- [ ] Implement `RunnableWithMessageHistory` with session ID isolation
- [ ] Test multi-turn context persistence (procedure → comorbidity follow-up)

### Phase 5 — NER & Ontology Pipeline
- [ ] Install scispaCy or configure medical NER model
- [ ] Build ICD-10 lookup dictionary (exact + fuzzy match)
- [ ] Validate end-to-end: "chest pain" → R07.9 → I25 → Angioplasty

### Phase 6 — Vector Index
- [ ] Embed clinical guideline documents into Neo4j vector index
- [ ] Validate hybrid retrieval (Cypher + vector in parallel)

### Phase 7 — Scoring & XAI
- [ ] Implement batch Fusion Score computation job
- [ ] Validate min-max normalization across hospital result sets
- [ ] Integrate SHAP waterfall plot into Streamlit sidebar
- [ ] Integrate LIME explanation for severity classifier output

### Phase 8 — RAG Confidence Gate
- [ ] Integrate DeepEval or Evidently AI metrics
- [ ] Set confidence threshold at 0.70
- [ ] Implement UI warning banner for low-confidence responses
- [ ] Validate `validate_cypher=True` blocks hallucinated labels

### Phase 9 — Geographic & Financial Engines
- [ ] Validate γ_geo multipliers for all three city tiers
- [ ] Implement DTI calculator on top of KG cost estimates
- [ ] Validate EMI range generation across 12/24/36 month tenures
- [ ] Test insurance cashless cross-reference via `(:InsuranceTier)` nodes

---

*This document is strictly derived from the implementation strategy as specified in the source architecture paper. All cost figures, multipliers, weights, and formulas are sourced directly from the referenced document.*
