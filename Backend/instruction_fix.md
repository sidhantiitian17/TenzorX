# Healthcare AI Navigator — Bug Fix Instructions

**Document:** `instruction_fix.md`  
**Project:** AI-Powered Healthcare Navigator and Cost Estimator  
**Architecture Reference:** GraphRAG + LangChain + Neo4j + ICD-10-CM + Streamlit  
**Issues Addressed:** 3 critical bugs causing data pipeline failures  

---

## Table of Contents

1. [Bug #1 — Graph Schema Mismatch: `OFFERS_PROCEDURE` Relationship Missing](#bug-1)
2. [Bug #2 — ICD-10 Generic Fallback: Returns Z99.89 Instead of Specific Codes](#bug-2)
3. [Bug #3 — Cost Data Flow: LLM Hallucinating Estimates When KG Data Is Absent](#bug-3)
4. [Regression Test Checklist](#regression-test-checklist)

---

<a name="bug-1"></a>
## Bug #1 — Graph Schema Mismatch: `OFFERS_PROCEDURE` Relationship Missing

### Symptom

Hospital queries consistently return **0 results**. The LangChain agent generates syntactically valid Cypher queries but traversal halts because the expected `OFFERS_PROCEDURE` relationship does not exist in the Neo4j graph. Example failing query:

```cypher
MATCH (h:Hospital)-[:OFFERS_PROCEDURE]->(p:Procedure {name: "Angioplasty"})
RETURN h.name, h.city, h.tier, h.nabh_accredited
```

This returns an empty result set even when Hospital and Procedure nodes are correctly populated.

---

### Root Cause Analysis

The Neo4j property graph schema stores interconnected nodes for **symptoms, diseases, procedures, hospitals, and geographic coordinates**. The graph traversal logic relies on deterministic edge traversal from `Procedure` nodes back to `Hospital` nodes. If the ingestion pipeline that seeds the graph created the `Hospital` and `Procedure` nodes independently (e.g., from two separate CSV imports) without explicitly creating the linking relationship, the relationship layer is simply absent — nodes exist but are disconnected islands.

Secondary causes to rule out:

- **Case sensitivity:** Neo4j relationship types are case-sensitive. `OFFERS_PROCEDURE` ≠ `offers_procedure` ≠ `OffersProcedure`.
- **Directionality error:** The relationship may have been created in reverse (`Procedure→Hospital` instead of `Hospital→Procedure`), making undirected queries succeed but directed ones fail.
- **Partial ingestion:** Only a subset of hospitals had the relationship seeded (e.g., Tier 1 hospitals only), causing Tier 2/3 queries to return empty.

---

### Diagnostic Steps

Run the following Cypher queries directly in the **Neo4j Browser** or via `neo4j.session.run()` to confirm the issue before applying fixes:

**Step 1 — Verify node counts:**
```cypher
MATCH (h:Hospital) RETURN count(h) AS hospital_count;
MATCH (p:Procedure) RETURN count(p) AS procedure_count;
```

**Step 2 — Verify relationship existence and count:**
```cypher
MATCH ()-[r:OFFERS_PROCEDURE]->() RETURN count(r) AS rel_count;
```
> If `rel_count` is `0`, the relationship is entirely absent. If it is lower than expected, ingestion was partial.

**Step 3 — Check for alternative relationship names (typos/variants):**
```cypher
CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType;
```

**Step 4 — Check directionality:**
```cypher
MATCH (p:Procedure)-[r:OFFERS_PROCEDURE]->(h:Hospital) RETURN count(r);
```
> If this returns a non-zero count but the original query returns 0, the relationship direction is inverted.

---

### Fix Instructions

#### Fix A — Re-seed the `OFFERS_PROCEDURE` relationship (primary fix)

If your ingestion source is a CSV/JSON mapping file of hospitals to procedures, run the following Cypher in a seeding script **after** all nodes have been created:

```cypher
// Load from a CSV with columns: hospital_id, procedure_name
LOAD CSV WITH HEADERS FROM 'file:///hospital_procedures.csv' AS row
MATCH (h:Hospital {hospital_id: row.hospital_id})
MATCH (p:Procedure {name: row.procedure_name})
MERGE (h)-[:OFFERS_PROCEDURE]->(p)
```

If the mapping data lives in a Python dictionary/dataframe in your ingestion script:

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def seed_offers_procedure(tx, hospital_id, procedure_name):
    tx.run(
        """
        MATCH (h:Hospital {hospital_id: $hospital_id})
        MATCH (p:Procedure {name: $procedure_name})
        MERGE (h)-[:OFFERS_PROCEDURE]->(p)
        """,
        hospital_id=hospital_id,
        procedure_name=procedure_name,
    )

with driver.session() as session:
    for row in hospital_procedure_mappings:  # your list of dicts
        session.execute_write(seed_offers_procedure, row["hospital_id"], row["procedure_name"])
```

> **Use `MERGE` not `CREATE`** to make the seeding script safely re-runnable (idempotent).

#### Fix B — Update the LangChain Cypher prompt template (defensive fix)

In your `GraphCypherQAChain` or custom LangChain prompt that generates Cypher, add schema-grounding instructions so the LLM cannot invent relationship names:

```python
CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Cypher query generator for a healthcare knowledge graph.
The graph schema is STRICTLY as follows:
  Nodes: Hospital, Procedure, Symptom, Disease, Geography
  Relationships:
    (Hospital)-[:OFFERS_PROCEDURE]->(Procedure)
    (Disease)-[:TREATED_BY]->(Procedure)
    (Symptom)-[:INDICATES]->(Disease)
    (Hospital)-[:LOCATED_IN]->(Geography)

ONLY use the relationship types listed above. Do not invent new relationship names.

User question: {question}
Cypher query:
"""
```

#### Fix C — Add a fallback query with undirected relationship matching

As a short-term resilience patch while Fix A is being validated in production, update the Cypher template to use undirected matching:

```cypher
// Undirected fallback — catches reversed relationships
MATCH (h:Hospital)-[:OFFERS_PROCEDURE]-(p:Procedure {name: $procedure_name})
RETURN h.name, h.city, h.tier, h.nabh_accredited, h.latitude, h.longitude
```

> Remove the undirected fallback once Fix A is confirmed and directionality is standardised.

#### Fix D — Add a graph health-check assertion on application startup

In your Streamlit `app.py` or initialization module, add the following check so the misconfiguration is caught at boot time rather than silently at query time:

```python
def assert_graph_schema_health(driver):
    with driver.session() as session:
        result = session.run(
            "MATCH ()-[r:OFFERS_PROCEDURE]->() RETURN count(r) AS cnt"
        )
        count = result.single()["cnt"]
        if count == 0:
            raise RuntimeError(
                "[GRAPH SCHEMA ERROR] No OFFERS_PROCEDURE relationships found in Neo4j. "
                "Run the hospital-procedure seeding script before starting the application."
            )
```

---

### Verification

After applying fixes, run these acceptance queries:

```cypher
// Should return > 0
MATCH (h:Hospital)-[:OFFERS_PROCEDURE]->(p:Procedure) RETURN count(*);

// Should return specific hospitals
MATCH (h:Hospital)-[:OFFERS_PROCEDURE]->(p:Procedure {name: "Angioplasty"})
RETURN h.name, h.city, h.tier LIMIT 5;

// Validate geographic join is intact
MATCH (h:Hospital)-[:OFFERS_PROCEDURE]->(p:Procedure {name: "Total Knee Replacement"})
MATCH (h)-[:LOCATED_IN]->(g:Geography)
RETURN h.name, g.city_tier, g.city_name LIMIT 5;
```

---

<a name="bug-2"></a>
## Bug #2 — ICD-10 Generic Fallback: Returns Z99.89 Instead of Specific Diagnosis Codes

### Symptom

The NER pipeline returns `Z99.89` ("Dependence on other enabling machines and devices") — a generic catch-all residual code — instead of clinically specific codes such as:

- `I25.10` (Atherosclerotic heart disease — Coronary Artery Disease)
- `M17.11` (Primary osteoarthritis, right knee — for TKR pathway)
- `I21.9` (Acute myocardial infarction — for emergency routing)

Because the ICD-10 code is the **"inflexible foundation upon which all subsequent cost estimates, pathway definitions, and provider matches are calculated"**, a wrong code causes the entire downstream pipeline — cost estimation, KG traversal, severity classification — to compute against the wrong procedure.

---

### Root Cause Analysis

The NER-to-ICD-10 mapping pipeline has three probable failure points:

1. **NER entity extraction failure:** The NER model extracted the symptom text but the extracted entity string does not lexically match any key in the ICD-10-CM JSON lookup dictionary (e.g., extracted `"chest pain radiating"` but the dictionary only has `"chest pain"`).

2. **JSON lookup logic falls through to default:** The lookup function catches a `KeyError` or `None` and returns a hardcoded default value of `Z99.89` instead of raising an error or attempting fuzzy matching.

3. **Tokenisation mismatch with the 2022 ICD-10-CM JSON schema:** The GitHub repository (`smog1210/2022-ICD-10-CM-JSON`) uses hierarchical code keys. If the lookup logic searches the flat code list instead of traversing the hierarchy, leaf-level specificity is lost and the system falls back to the nearest parent — or the catch-all.

---

### Diagnostic Steps

**Step 1 — Isolate NER extraction output before the ICD lookup:**
```python
# Temporarily add this debug logging in your NER pipeline
import logging
logging.basicConfig(level=logging.DEBUG)

entities = ner_model.extract(user_input)
logging.debug(f"[NER OUTPUT] Extracted entities: {entities}")
```

Run a known test case: input `"I have severe chest pain that goes to my left arm"` and inspect what entity strings are being passed to the ICD lookup. Expected: `["chest pain", "left arm pain"]` or similar.

**Step 2 — Test the ICD lookup function in isolation:**
```python
code = icd_lookup("chest pain radiating to left arm")
print(code)  # Should be R07.9 or closer to I20/I21 range, not Z99.89
```

**Step 3 — Inspect the JSON structure being queried:**
```python
import json
with open("icd10cm_2022.json") as f:
    icd_data = json.load(f)
print(type(icd_data))          # dict or list?
print(list(icd_data.keys())[:10])  # Inspect top-level keys
```

---

### Fix Instructions

#### Fix A — Replace exact-match lookup with fuzzy/semantic matching

The current lookup likely uses `dict.get(entity_string, "Z99.89")`. Replace with a two-stage approach: exact match first, then fuzzy match via `rapidfuzz`:

```python
from rapidfuzz import process, fuzz
import json

# Load ICD-10 data once at module level
with open("icd10cm_2022.json") as f:
    icd_raw = json.load(f)

# Build a flat {description: code} lookup dict from the JSON hierarchy
def build_icd_lookup(icd_data: dict) -> dict:
    lookup = {}
    def recurse(node):
        if isinstance(node, dict):
            if "desc" in node and "code" in node:
                lookup[node["desc"].lower()] = node["code"]
            for v in node.values():
                recurse(v)
        elif isinstance(node, list):
            for item in node:
                recurse(item)
    recurse(icd_data)
    return lookup

ICD_LOOKUP = build_icd_lookup(icd_raw)
ICD_DESCRIPTIONS = list(ICD_LOOKUP.keys())

def map_entity_to_icd10(entity: str, score_threshold: int = 70) -> dict:
    """
    Maps a NER-extracted entity string to an ICD-10 code.
    Returns a dict with 'code', 'description', and 'match_score'.
    Falls back to flagging low-confidence matches rather than returning Z99.89.
    """
    entity_lower = entity.lower().strip()

    # Stage 1: Exact match
    if entity_lower in ICD_LOOKUP:
        return {
            "code": ICD_LOOKUP[entity_lower],
            "description": entity_lower,
            "match_score": 100,
            "match_type": "exact"
        }

    # Stage 2: Fuzzy match using token sort ratio
    best_match, score, _ = process.extractOne(
        entity_lower,
        ICD_DESCRIPTIONS,
        scorer=fuzz.token_sort_ratio
    )

    if score >= score_threshold:
        return {
            "code": ICD_LOOKUP[best_match],
            "description": best_match,
            "match_score": score,
            "match_type": "fuzzy"
        }

    # Stage 3: Low confidence — return structured flag, NOT a silent Z99.89
    return {
        "code": None,
        "description": entity,
        "match_score": score,
        "match_type": "unmatched",
        "warning": f"No ICD-10 match found above threshold ({score_threshold}) for: '{entity}'"
    }
```

#### Fix B — Add a clinical synonym pre-processing layer

Common patient language does not map cleanly to ICD-10 descriptions. Add a synonym expansion dictionary consulted *before* the fuzzy lookup:

```python
SYMPTOM_SYNONYMS = {
    "chest pain": ["angina", "chest tightness", "chest pressure", "thoracic pain"],
    "chest pain radiating to left arm": ["angina pectoris", "ischemic chest pain"],
    "knee pain": ["knee joint pain", "gonalgia"],
    "difficulty breathing": ["dyspnea", "shortness of breath", "breathlessness"],
    "heart attack": ["myocardial infarction", "acute MI", "cardiac arrest"],
    "sugar": ["diabetes mellitus", "hyperglycemia"],
    "bp": ["hypertension", "high blood pressure"],
}

def expand_synonyms(entity: str) -> list[str]:
    entity_lower = entity.lower().strip()
    expanded = [entity_lower]
    for canonical, synonyms in SYMPTOM_SYNONYMS.items():
        if entity_lower in synonyms or entity_lower == canonical:
            expanded.append(canonical)
            expanded.extend(synonyms)
    return list(set(expanded))

def map_entity_to_icd10_with_expansion(entity: str) -> dict:
    candidates = expand_synonyms(entity)
    best_result = None
    for candidate in candidates:
        result = map_entity_to_icd10(candidate)
        if best_result is None or result["match_score"] > best_result["match_score"]:
            best_result = result
        if result["match_score"] == 100:
            break
    return best_result
```

#### Fix C — Integrate ICD result confidence into the RAG Confidence Score

Per the architecture, the Confidence Score formula is:

```
S = 0.4 × Faithfulness + 0.3 × Context_Relevancy + 0.3 × Answer_Relevancy
```

Extend the upstream pipeline to penalise low-confidence ICD-10 mappings so they surface to the user rather than silently corrupting cost estimates:

```python
def compute_icd_confidence_penalty(icd_result: dict) -> float:
    """Returns a multiplier (0.0–1.0) to apply to the RAG confidence score."""
    if icd_result["match_type"] == "exact":
        return 1.0
    elif icd_result["match_type"] == "fuzzy":
        return icd_result["match_score"] / 100.0
    else:  # unmatched
        return 0.0

# In your confidence scoring function:
icd_penalty = compute_icd_confidence_penalty(icd_result)
adjusted_confidence = base_confidence_score * icd_penalty

if adjusted_confidence < CONFIDENCE_THRESHOLD:
    display_uncertainty_banner(
        f"Low-confidence medical classification for: '{entity}'. "
        "Cost estimates may be imprecise. Please describe your condition in more detail."
    )
```

#### Fix D — Eliminate the silent Z99.89 default

Search your entire codebase for the hardcoded fallback and remove it:

```python
# REMOVE THIS PATTERN:
icd_code = icd_lookup_dict.get(entity, "Z99.89")

# REPLACE WITH:
icd_result = map_entity_to_icd10_with_expansion(entity)
icd_code = icd_result["code"]  # Will be None if unmatched — handle explicitly
```

---

### Verification

Run the following unit tests against the updated lookup function:

```python
test_cases = [
    ("chest pain radiating to left arm", "I"),   # Ischemic heart disease range
    ("severe knee pain walking",          "M"),   # Musculoskeletal range
    ("difficulty breathing",              "R"),   # Respiratory symptoms range
    ("diabetes",                          "E"),   # Endocrine range
    ("high blood pressure",              "I10"),  # Exact hypertension code
]

for entity, expected_prefix in test_cases:
    result = map_entity_to_icd10_with_expansion(entity)
    assert result["code"] is not None, f"FAIL: No code returned for '{entity}'"
    assert result["code"].startswith(expected_prefix), (
        f"FAIL: '{entity}' → {result['code']} (expected prefix '{expected_prefix}')"
    )
    assert result["code"] != "Z99.89", f"FAIL: Generic fallback returned for '{entity}'"
    print(f"PASS: '{entity}' → {result['code']} ({result['description']}) [{result['match_score']}%]")
```

---

<a name="bug-3"></a>
## Bug #3 — Cost Data Flow: LLM Hallucinating Estimates When KG Data Is Missing

### Symptom

When the Neo4j Knowledge Graph cannot find cost data for a requested procedure/geography combination (due to Bug #1 or sparse data coverage), the LangChain LLM agent silently generates **plausible-sounding but fabricated cost estimates** rather than surfacing a data-missing warning. This is a direct violation of the Faithfulness (Groundedness) requirement of the RAG Confidence Scoring System.

Examples of hallucinated outputs observed:
- Generating a cost range of `₹1,80,000–₹2,20,000` for a procedure when no KG record exists for that city tier.
- Returning named hospitals that do not exist in the Neo4j graph.

---

### Root Cause Analysis

The `GraphCypherQAChain` (or equivalent LangChain chain) pipeline has two sequential steps: **(1) retrieve context from Neo4j**, **(2) pass context + question to the LLM for synthesis**. If step 1 returns an empty context (`[]` or `""`), step 2 still receives the original question and the LLM, lacking any grounding data, answers from parametric memory — i.e., it hallucinates.

This directly contradicts the **Faithfulness** metric requirement: *"the LLM's output must be logically implied by, and strictly extractable from, the retrieved Neo4j context."*

---

### Diagnostic Steps

**Step 1 — Log the raw retrieval context before LLM synthesis:**
```python
# Intercept the context payload sent to the LLM
def debug_retrieval(cypher_query: str, driver) -> list:
    with driver.session() as session:
        result = session.run(cypher_query)
        records = [dict(r) for r in result]
    print(f"[KG RETRIEVAL] Query: {cypher_query}")
    print(f"[KG RETRIEVAL] Records returned: {len(records)}")
    print(f"[KG RETRIEVAL] Data: {records}")
    return records
```

If `records` is `[]` and the LLM still returns a cost estimate — that is the hallucination path confirmed.

**Step 2 — Test the Faithfulness metric programmatically:**
```python
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase

test_case = LLMTestCase(
    input="What is the cost of angioplasty in Raipur?",
    actual_output=llm_response,
    retrieval_context=[""]  # Simulate empty KG retrieval
)
metric = FaithfulnessMetric(threshold=0.7)
metric.measure(test_case)
print(metric.score)  # Expected: near 0 when KG is empty but LLM still answers
```

---

### Fix Instructions

#### Fix A — Implement a mandatory KG retrieval gate

Add an explicit empty-context guard in the LangChain chain **before** the LLM synthesis step. The LLM must not be invoked when retrieval returns no records:

```python
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import AIMessage

EMPTY_CONTEXT_RESPONSE = (
    "I was unable to find verified cost data for this procedure in the requested location. "
    "The estimates shown below are based on national benchmark ranges only and carry "
    "**lower confidence**. Please verify with the hospital directly.\n\n"
    "{fallback_estimate}"
)

def retrieval_gate(inputs: dict) -> dict:
    """
    Blocks LLM synthesis if KG returned no records.
    Routes to the deterministic cost engine fallback instead.
    """
    context = inputs.get("context", [])

    if not context or context == "I don't know" or len(context) == 0:
        procedure = inputs.get("procedure", "requested procedure")
        city_tier = inputs.get("city_tier", "Tier 2")
        fallback = deterministic_cost_fallback(procedure, city_tier)
        inputs["llm_blocked"] = True
        inputs["fallback_response"] = EMPTY_CONTEXT_RESPONSE.format(
            fallback_estimate=fallback
        )
    else:
        inputs["llm_blocked"] = False

    return inputs

# Integrate into the LangChain pipeline
chain = (
    retrieval_runnable          # Neo4j GraphCypherQAChain
    | RunnableLambda(retrieval_gate)
    | RunnableLambda(conditional_llm_invoke)  # Only invokes LLM if not blocked
)
```

#### Fix B — Build a deterministic cost fallback engine

When KG data is absent, cost estimates must come from the **structured benchmark table** defined in the strategy document, not from the LLM. Implement a static lookup as the fallback:

```python
# Based on the cost data from the implementation strategy document
PROCEDURE_COST_BENCHMARKS = {
    "Angioplasty": {
        "components": {
            "Pre-Procedure Diagnostics": (10_000, 30_000),
            "Surgical Procedure (DES)":  (1_00_000, 2_50_000),
            "Hospital Stay (ICU + Ward)": (20_000, 60_000),
            "Post-Procedure Care":        (10_000, 30_000),
        },
        "tier_multipliers": {"Tier 1": 1.0, "Tier 2": 0.95, "Tier 3": 0.75},
    },
    "Total Knee Replacement": {
        "components": {
            "Pre-Surgical Evaluation":    (8_000, 20_000),
            "Surgery (Standard Implant)": (1_50_000, 3_00_000),
            "Surgery (Robotic-Assisted)": (3_00_000, 4_50_000),
            "Post-Op Physiotherapy":      (15_000, 40_000),
        },
        "tier_multipliers": {"Tier 1": 1.0, "Tier 2": 0.916, "Tier 3": 0.833},
    },
}

def deterministic_cost_fallback(procedure: str, city_tier: str) -> str:
    """
    Returns a formatted cost breakdown from benchmark data.
    Called ONLY when KG retrieval returns empty results.
    Confidence is explicitly marked as LOW.
    """
    if procedure not in PROCEDURE_COST_BENCHMARKS:
        return "No benchmark data available for this procedure."

    data = PROCEDURE_COST_BENCHMARKS[procedure]
    multiplier = data["tier_multipliers"].get(city_tier, 0.9)
    lines = [f"**Benchmark Cost Estimate — {procedure} ({city_tier})**\n",
             "_Source: National benchmark data. Not retrieved from verified hospital records._\n"]

    total_min, total_max = 0, 0
    for component, (low, high) in data["components"].items():
        adj_low  = int(low  * multiplier)
        adj_high = int(high * multiplier)
        total_min += adj_low
        total_max += adj_high
        lines.append(f"- **{component}:** ₹{adj_low:,} – ₹{adj_high:,}")

    lines.append(f"\n**Estimated Total: ₹{total_min:,} – ₹{total_max:,}**")
    lines.append("\n⚠️ Confidence: **LOW** — Verify directly with the hospital.")
    return "\n".join(lines)
```

#### Fix C — Apply the comorbidity adjustment to fallback estimates too

The fallback engine must honour the **Age and Comorbidity Cost Adjustment (Gap 6)** formula:

```
Final_Estimated_Cost = Adjusted_Cost × (1 + Σ ωᵢCᵢ)
```

Implement this so the fallback is still medically accurate even without KG data:

```python
COMORBIDITY_WEIGHTS = {
    "cardiovascular_disease": 2.2,
    "heart_failure":          3.3,
    "kidney_disease":         2.7,
    "diabetes":               1.4,
    "hypertension":           1.2,
}

def apply_comorbidity_adjustment(
    base_cost_range: tuple[int, int],
    comorbidities: list[str]
) -> tuple[int, int]:
    """
    Applies the comorbidity multiplier to a (min, max) cost tuple.
    Only the upper bound is expanded — lower bound stays at baseline.
    """
    if not comorbidities:
        return base_cost_range

    total_weight = sum(
        COMORBIDITY_WEIGHTS.get(c.lower().replace(" ", "_"), 0)
        for c in comorbidities
    )
    # Only upper bound is adjusted (heightened worst-case risk)
    adjusted_max = int(base_cost_range[1] * (1 + (total_weight - 1) * 0.3))
    return (base_cost_range[0], adjusted_max)
```

#### Fix D — Surface the Confidence Score badge on the Streamlit UI

The RAG Confidence Scoring System formula is:
```
S = 0.4 × Faithfulness + 0.3 × Context_Relevancy + 0.3 × Answer_Relevancy
```

When the KG retrieval gate is triggered (empty context), force `Faithfulness = 0` and surface the uncertainty indicator mandated by the architecture:

```python
def compute_confidence_score(
    faithfulness: float,
    context_relevancy: float,
    answer_relevancy: float,
    kg_retrieved: bool
) -> dict:
    if not kg_retrieved:
        faithfulness = 0.0  # No KG data = cannot be grounded

    score = (
        0.4 * faithfulness +
        0.3 * context_relevancy +
        0.3 * answer_relevancy
    )

    return {
        "score": round(score, 3),
        "kg_retrieved": kg_retrieved,
        "low_confidence": score < 0.6,
        "badge_color": "green" if score >= 0.8 else "orange" if score >= 0.6 else "red",
    }

# In Streamlit:
def render_confidence_badge(confidence: dict):
    if confidence["low_confidence"]:
        st.warning(
            "⚠️ **Low Confidence Response** — "
            "This system provides decision support only and does not constitute "
            "medical advice or diagnosis. Cost estimates are based on national "
            "benchmarks, not verified hospital data.",
            icon="⚠️"
        )
    else:
        st.success(
            f"✅ Confidence Score: {confidence['score']:.0%} "
            f"(Grounded in verified hospital records)",
            icon="✅"
        )
```

---

### Verification

Run end-to-end tests for the three scenarios:

```python
# Test 1: KG data present → LLM should synthesise from context (high confidence)
response = agent.invoke({"query": "angioplasty cost in Mumbai", "mock_kg_empty": False})
assert response["confidence"]["score"] >= 0.7
assert response["confidence"]["kg_retrieved"] == True

# Test 2: KG data absent → fallback engine activates (low confidence, no hallucination)
response = agent.invoke({"query": "angioplasty cost in Durg", "mock_kg_empty": True})
assert response["confidence"]["kg_retrieved"] == False
assert response["confidence"]["low_confidence"] == True
assert "₹" in response["output"]               # Fallback still provides estimate
assert "Verify" in response["output"]           # Warning is present
assert "Z99.89" not in response["output"]       # ICD fallback not leaking

# Test 3: Comorbidity adjustment applied in fallback path
response = agent.invoke({
    "query": "angioplasty cost in Raipur",
    "comorbidities": ["heart_failure", "diabetes"],
    "mock_kg_empty": True
})
# Upper bound should be higher than baseline Raipur estimate
assert response["cost_range"]["max"] > 2_00_000
```

---

<a name="regression-test-checklist"></a>
## Regression Test Checklist

Run all items below after applying the three fixes to confirm no regressions:

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | Query `MATCH ()-[:OFFERS_PROCEDURE]->() RETURN count(*)` in Neo4j | Count > 0 |
| 2 | NER input: `"chest pain left arm"` | ICD code starts with `I`, not `Z99.89` |
| 3 | NER input: `"knee pain walking"` | ICD code starts with `M` |
| 4 | Hospital search for "Angioplasty" in any tier | Returns ≥ 1 hospital result |
| 5 | Hospital search in city with no KG data | Returns fallback estimate with ⚠️ badge |
| 6 | Cost estimate with comorbidities (heart failure + diabetes) | Upper bound > baseline estimate |
| 7 | Confidence score with empty KG context | Score < 0.6, `low_confidence = True` |
| 8 | Emergency query: `"chest pain radiating to left arm"` | Severity = Red, triggers 24/7 routing |
| 9 | Multi-turn: Ask about knee replacement, then `"will my diabetes affect this?"` | Agent recalls procedure context without re-statement |
| 10 | Streamlit multi-user: Two concurrent sessions | No session state cross-talk (separate `InMemoryChatMessageHistory`) |

---

*This document should be reviewed alongside the full architecture specification before implementation. All code samples assume Python 3.10+, Neo4j 5.x, LangChain ≥ 0.2, and `rapidfuzz ≥ 3.0`.*
