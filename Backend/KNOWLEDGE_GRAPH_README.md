# Knowledge Graph Implementation

Complete implementation of the Neo4j Knowledge Graph per `instruction_KG.md` for the TenzorX Healthcare Navigator.

## Architecture Overview

The Knowledge Graph is the **foundational intelligence layer** implementing GraphRAG (Graph + RAG) architecture:

- **Structured symbolic reasoning** via Cypher graph traversal
- **Unstructured text retrieval** via embedded vector index
- **Hybrid cost calculation** with geographic and comorbidity adjustments

## Node Types (Section 3.1)

| Node | Properties | Purpose |
|------|------------|---------|
| `Disease` | icd10_code, name, description, category | Medical conditions |
| `Symptom` | icd10_code, name, body_region | Patient-reported symptoms |
| `Procedure` | name, procedure_code, type, icd10_code | Medical procedures |
| `CostComponent` | id, phase, description, base_cost_min/max_inr, typical_days | Phase-based costs |
| `Hospital` | id, name, tier, nabh/jci_accredited, fusion_score, bed_turnover_rate | Healthcare providers |
| `Geography` | city_name, state, city_tier, geo_adjustment_factor (γ_geo), icu_daily_rate_inr | Location multipliers |
| `Comorbidity` | condition_name, icd10_code, cost_multiplier_weight (ω_i), risk_category | Cost-elevating conditions |
| `Specialist` | id, name, department, qualification, experience_years, active | Doctors |
| `InsuranceTier` | id, hospital_id, insurer_name, empaneled, cashless_success_rate | Coverage data |
| `ReviewAspect` | id, hospital_id, aspect, vader_compound_score, lda_topic_label | ABSA sentiment |

## Relationship Types (Section 3.2)

```
(:Symptom)-[:INDICATES]->(:Disease)
(:Disease)-[:REQUIRES_WORKUP]->(:Procedure)       // Diagnostic
(:Disease)-[:TREATED_BY]->(:Procedure)            // Treatment
(:Procedure)-[:HAS_COST_COMPONENT]->(:CostComponent)
(:Procedure)-[:PRECEDES]->(:Procedure)            // Sequencing
(:Hospital)-[:LOCATED_IN]->(:Geography)
(:Hospital)-[:OFFERS_PROCEDURE]->(:Procedure)
(:Hospital)-[:EMPLOYS]->(:Specialist)
(:Specialist)-[:SPECIALIZES_IN]->(:Disease)
(:Hospital)-[:HAS_REVIEW_ASPECT]->(:ReviewAspect)
(:Hospital)-[:COVERED_BY]->(:InsuranceTier)
(:Comorbidity)-[:ELEVATES_COST_FOR]->(:Procedure)
```

## Data Files

### Seed Data (JSON)
- `geography_seed.json` - 18 cities with tier multipliers
- `comorbidity_seed.json` - 8 conditions with cost weights
- `cost_components_seed.json` - Phase-based costs for 6 procedures
- `specialists_seed.json` - 10 doctors linked to hospitals
- `insurance_seed.json` - 12 insurer-hospital relationships
- `disease_procedure_mapping.json` - Clinical pathways
- `hospitals_seed.json` - 8 hospitals with fusion score inputs
- `procedure_benchmarks.json` - Base cost data

## Implementation Components

### Core Modules

| File | Purpose |
|------|---------|
| `neo4j_client.py` | Graph database queries and cost calculations |
| `schema_setup.py` | Constraints, indexes, and data seeding |
| `graph_rag.py` | Hybrid retrieval + LLM synthesis engine |
| `fusion_scorer.py` | Multi-source hospital ranking scores |
| `availability_proxy.py` | Queuing theory appointment estimates |

### Key Features

#### 1. Geographic Cost Adjustment (Section 10)
```python
# Formula: Adjusted_Cost = Base × γ_geo
geo = neo4j.get_geographic_multiplier("Raipur")
# Returns: {gamma_geo: 0.833, icu_rate: 2638}
```

#### 2. Comorbidity Cost Adjustment (Section 11)
```python
# Formula: Final_Cost = Adjusted × (1 + Σ ω_i + ω_age if >65)
comorb = neo4j.get_comorbidity_multipliers(
    "Angioplasty", 
    ["Diabetes", "Heart Failure"]
)
# Returns: {total_omega: 1.225, multiplier: 2.225}
```

#### 3. Fusion Score Computation (Section 12)
```
Fusion_Score = 0.40×Clinical + 0.25×Reputation + 0.20×Accessibility + 0.15×Affordability
```
Components:
- **Clinical**: Procedure count, NABH/JCI accreditation
- **Reputation**: VADER sentiment + star rating
- **Accessibility**: Bed turnover rate, specialist count
- **Affordability**: Cashless success rate, pricing tier

#### 4. Availability Proxy (Section 13)
```python
# Formula: throughput_index = (beds × turnover) / max(specialists, 1)
availability = proxy.compute_availability(hospital_id)
# Returns labels: "2-3 days", "4-7 days", "1-2 weeks", "24/7 emergency"
```

#### 5. Clinical Pathway (Section 9)
```json
{
  "procedure": "Angioplasty",
  "pathway": [
    {"phase": "pre_procedure", "components": ["ECG", "Stress Test"], "cost": "₹10,000-30,000"},
    {"phase": "procedure", "components": ["Balloon Angioplasty"], "cost": "₹100,000-250,000"},
    {"phase": "hospital_stay", "components": ["ICU Monitoring"], "cost": "₹20,000-60,000"},
    {"phase": "post_procedure", "components": ["Anti-platelets"], "cost": "₹10,000-30,000"}
  ]
}
```

## Setup Instructions

### 1. Install Neo4j
```bash
# Docker
'docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest'

# Or download from https://neo4j.com/download/
```

### 2. Configure Environment
```bash
# Backend/.env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 3. Run Schema Setup
```bash
cd Backend
python -m app.knowledge_graph.schema_setup
```

This creates:
- All constraints and indexes
- Geography nodes with γ_geo multipliers
- Comorbidity nodes with ω_i weights
- CostComponent nodes with phase breakdowns
- Hospital nodes with fusion score defaults
- Specialist, InsuranceTier, ReviewAspect nodes
- Complete relationship network

### 4. Compute Fusion Scores
```python
from app.knowledge_graph import compute_fusion_scores
compute_fusion_scores()
```

## Query Examples

### Find hospitals for a procedure
```python
from app.knowledge_graph import Neo4jClient

client = Neo4jClient()
hospitals = client.find_hospitals_for_procedure_in_city(
    "Angioplasty", "Raipur", limit=5
)
# Returns hospitals ranked by fusion_score with availability info
```

### Get cost estimate with adjustments
```python
# Get phase-based cost breakdown
breakdown = client.get_cost_breakdown("Angioplasty")

# Calculate adjusted costs
cost = client.apply_cost_adjustments(
    base_cost_min=sum(c["cost_min"] for c in breakdown),
    base_cost_max=sum(c["cost_max"] for c in breakdown),
    city_name="Raipur",
    comorbidity_names=["Diabetes", "Heart Failure"],
    patient_age=70
)
# Returns: {final_cost_min: 362000, final_cost_max: 906000, ...}
```

### Full GraphRAG query
```python
from app.knowledge_graph import GraphRAGEngine

engine = GraphRAGEngine()
result = engine.query(
    user_text="I have chest pain and I'm diabetic. Need angioplasty in Raipur.",
    location="Raipur",
    patient_profile={"age": 65, "comorbidities": ["Diabetes"]}
)
# Returns: {llm_response, icd10, procedure, disease, severity, pathway, cost_estimate, hospitals_raw, confidence_score}
```

## End-to-End Flow (Section 17)

```
USER INPUT
    ↓
[NER Pipeline] → extracts: Symptoms, Conditions, Procedures
    ↓
[ICD-10 Lookup] → resolves to canonical codes
    ↓
[Severity Classifier] → RED/YELLOW/GREEN triage
    ↓
[Graph Traversal]
    Symptom → [:INDICATES] → Disease
    Disease → [:TREATED_BY] → Procedure
    Procedure → [:HAS_COST_COMPONENT] → CostComponent
    Hospital → [:LOCATED_IN] → Geography (γ_geo)
    Comorbidity → [:ELEVATES_COST_FOR] → Procedure (ω_i)
    ↓
[Cost Adjustment] → Base × γ_geo × (1 + Σ ω_i)
    ↓
[Fusion Score Ranking] → Hospital selection
    ↓
[Availability Proxy] → Queuing estimates
    ↓
[LLM Synthesis] → Enriched response
    ↓
[Confidence Gate] → S ≥ 0.70 to pass
    ↓
RESPONSE
```

## Testing

### Unit Tests
```bash
cd Backend
pytest tests/ -v
```

### Integration Test
```python
# Verify graph connectivity
from app.knowledge_graph import Neo4jClient

client = Neo4jClient()

# Test symptom → disease → procedure
result = client.run_query("""
    MATCH (s:Symptom {name: 'chest pain'})-[:INDICATES]->(d:Disease)-[:TREATED_BY]->(p:Procedure)
    RETURN s.name, d.name, p.name
""")
print(result)

# Test cost adjustments
geo = client.get_geographic_multiplier("Raipur")
assert geo["gamma_geo"] == 0.833

# Test comorbidity weights
comorb = client.get_comorbidity_multipliers("Angioplasty", ["Diabetes Mellitus Type 2"])
assert comorb["total_omega"] == 0.40
```

## References

- `instruction_KG.md` - Full architecture specification
- Neo4j Cypher Manual: https://neo4j.com/docs/cypher-manual/
- GraphRAG Paper: https://microsoft.github.io/graphrag/

## Implementation Status

✅ All node types from Section 3.1
✅ All relationship types from Section 3.2
✅ Geography multipliers (Section 10)
✅ Comorbidity weights (Section 11)
✅ Fusion score computation (Section 12)
✅ Availability proxy (Section 13)
✅ Clinical pathway traversal (Section 9)
✅ GraphRAG integration (Sections 6-8)
✅ Cost adjustment formulas (Sections 10-11)
