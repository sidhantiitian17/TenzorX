# ICD-10 Feature Testing Plan
## Healthcare AI Navigator — Verification & Validation

---

## Overview

This testing plan verifies that the ICD-10 Named Entity Recognition integration is
correctly implemented and that all nine downstream features continue to function
as designed. Tests are organized in the exact order of the application pipeline.

**Root error being resolved:**
```
WARNING - ICD-10 data file not found: data/icd10_2022.json
ERROR   - ICD-10 data file not found in any location
```

**Pass Criteria:** All CRITICAL tests must pass. HIGH tests should pass before
production deployment. MEDIUM tests are regression guards.

---

## Test Suite 1 — ICD-10 Data File & Loader

### TC-01 | ICD-10 File Exists After Setup Script
**Priority:** CRITICAL
**Command:**
```bash
python setup_data.py
```
**Assertions:**
- [ ] Exit code is 0 (no exceptions)
- [ ] `data/icd10_2022.json` exists on disk
- [ ] File size > 1 MB
- [ ] File is valid JSON (not truncated)

**Expected log output:**
```
INFO - ICD-10 download successful. Total codes: XXXXX
```

---

### TC-02 | ICD-10 Loader Returns Non-Empty Index
**Priority:** CRITICAL
**Code:**
```python
from src.icd10_loader import load_icd10

index = load_icd10()
assert isinstance(index, dict), "Index must be a dict"
assert len(index) > 100, f"Index too small: {len(index)} keywords"
print(f"PASS: Index loaded with {len(index)} keywords")
```
**Expected:** `PASS: Index loaded with XXXX keywords`

---

### TC-03 | Loader Falls Back to Minimal Dataset When Full File Missing
**Priority:** CRITICAL
**Setup:** Temporarily rename `data/icd10_2022.json` to `data/icd10_2022.json.bak`
**Code:**
```python
import importlib, src.icd10_loader as m
m._icd10_index = None          # clear singleton
index = m.load_icd10()
assert len(index) > 0, "Fallback index must not be empty"
print(f"PASS: Fallback loaded with {len(index)} keywords")
```
**Expected:** App does not crash; loads from `data/icd10_fallback.json`
**Teardown:** Restore `data/icd10_2022.json.bak` → `data/icd10_2022.json`

---

### TC-04 | Loader Raises RuntimeError When Both Files Missing
**Priority:** HIGH
**Setup:** Remove both JSON files
**Code:**
```python
try:
    from src.icd10_loader import load_icd10
    load_icd10()
    print("FAIL: Should have raised RuntimeError")
except RuntimeError as e:
    print(f"PASS: RuntimeError raised — {e}")
```
**Expected:** `PASS: RuntimeError raised — ICD-10 data unavailable. Run python setup_data.py...`

---

### TC-05 | Loader is Idempotent (Singleton Caching Works)
**Priority:** HIGH
**Code:**
```python
import time
from src.icd10_loader import load_icd10

t1 = time.time(); load_icd10(); t1 = time.time() - t1
t2 = time.time(); load_icd10(); t2 = time.time() - t2

assert t2 < t1 * 0.01, "Second load should be nearly instant (cached)"
print(f"PASS: First load {t1:.3f}s, cached load {t2:.6f}s")
```

---

## Test Suite 2 — ICD-10 Lookup Function

### TC-06 | Chest Pain Maps to Correct ICD Code
**Priority:** CRITICAL
**Code:**
```python
from src.icd10_loader import lookup_icd10

results = lookup_icd10("chest pain", top_k=3)
codes = [r["code"] for r in results]
assert any(c.startswith("R07") or c.startswith("I") for c in codes), \
    f"Expected cardiac/chest codes, got: {codes}"
print(f"PASS: chest pain → {results}")
```
**Expected result contains:** `R07.9` or `I21.x` or similar

---

### TC-07 | Knee Pain Maps to Orthopedic Codes
**Priority:** CRITICAL
**Code:**
```python
from src.icd10_loader import lookup_icd10

results = lookup_icd10("knee pain replacement", top_k=3)
codes = [r["code"] for r in results]
assert any(c.startswith("M17") for c in codes), \
    f"Expected M17.x orthopedic codes, got: {codes}"
print(f"PASS: knee pain → {results}")
```

---

### TC-08 | Diabetes Maps to E11 Code
**Priority:** HIGH
**Code:**
```python
from src.icd10_loader import lookup_icd10

results = lookup_icd10("diabetes mellitus type 2", top_k=3)
codes = [r["code"] for r in results]
assert any(c.startswith("E11") for c in codes), \
    f"Expected E11.x diabetes codes, got: {codes}"
print(f"PASS: diabetes → {results}")
```

---

### TC-09 | Unknown Symptom Returns Empty List (No Crash)
**Priority:** HIGH
**Code:**
```python
from src.icd10_loader import lookup_icd10

results = lookup_icd10("xyzzy nonsense symptom that does not exist")
assert isinstance(results, list), "Must return a list"
assert len(results) == 0, f"Expected empty list, got: {results}"
print("PASS: Unknown symptom returns empty list gracefully")
```

---

### TC-10 | Lookup Returns Correct Schema
**Priority:** HIGH
**Code:**
```python
from src.icd10_loader import lookup_icd10

results = lookup_icd10("heart failure", top_k=2)
for r in results:
    assert "code" in r, f"Missing 'code' key: {r}"
    assert "description" in r, f"Missing 'description' key: {r}"
    assert len(r["code"]) >= 3, f"ICD code too short: {r['code']}"
print(f"PASS: Schema correct — {results}")
```

---

## Test Suite 3 — NER Pipeline with ICD-10 Integration

### TC-11 | NER Extracts Entities from Free Text
**Priority:** CRITICAL
**Code:**
```python
from src.ner_pipeline import extract_and_standardize

result = extract_and_standardize("I have severe chest pain radiating to my left arm")
assert "entities" in result
assert len(result["entities"]) > 0, "NER must extract at least one entity"
print(f"PASS: NER extracted {len(result['entities'])} entities")
```

---

### TC-12 | NER Output Contains ICD-10 Codes
**Priority:** CRITICAL
**Code:**
```python
from src.ner_pipeline import extract_and_standardize

result = extract_and_standardize("I have severe chest pain")
for entity in result["entities"]:
    assert "primary_code" in entity, f"Missing primary_code in: {entity}"
    assert "icd_codes" in entity, f"Missing icd_codes in: {entity}"
assert len(result["icd_summary"]) > 0, "icd_summary must not be empty"
print(f"PASS: ICD codes extracted: {result['icd_summary']}")
```

---

### TC-13 | NER Handles Empty Input Gracefully
**Priority:** HIGH
**Code:**
```python
from src.ner_pipeline import extract_and_standardize

result = extract_and_standardize("")
assert result["entities"] == [], "Empty input should give empty entities"
print("PASS: Empty input handled gracefully")
```

---

### TC-14 | NER Handles Hindi/Mixed Language Input
**Priority:** MEDIUM
**Input:** `"mujhe seene mein dard ho raha hai"` (Hindi: "I have chest pain")
**Expected:** At least soft entity extraction; no exception raised
**Code:**
```python
from src.ner_pipeline import extract_and_standardize

try:
    result = extract_and_standardize("mujhe seene mein dard ho raha hai")
    print(f"PASS: Mixed language handled. Entities: {result['entities']}")
except Exception as e:
    print(f"FAIL: Exception on Hindi input — {e}")
```

---

## Test Suite 4 — Severity Classifier

### TC-15 | Chest Pain Radiating to Arm → RED
**Priority:** CRITICAL
**Code:**
```python
from src.severity_classifier import classify_severity

severity = classify_severity(
    entities=[{"primary_code": "R07.4"}, {"primary_code": "I21.9"}],
    raw_text="severe chest pain radiating to left arm"
)
assert severity == "RED", f"Expected RED, got {severity}"
print("PASS: Emergency symptoms correctly classified as RED")
```

---

### TC-16 | Knee Pain for Elective Surgery → GREEN
**Priority:** CRITICAL
**Code:**
```python
from src.severity_classifier import classify_severity

severity = classify_severity(
    entities=[{"primary_code": "M17.11"}],
    raw_text="knee pain, considering replacement surgery"
)
assert severity == "GREEN", f"Expected GREEN, got {severity}"
print("PASS: Elective procedure correctly classified as GREEN")
```

---

### TC-17 | RED Severity Overrides Budget Filters
**Priority:** HIGH
**Code:**
```python
from src.routing_logic import get_provider_filters

filters = get_provider_filters(severity="RED", budget=5000)
assert filters.get("emergency_only") is True, "RED must trigger emergency-only filter"
assert "budget" not in filters or filters["budget"] is None, \
    "Budget filter must be overridden for RED"
print("PASS: RED severity overrides budget filters")
```

---

## Test Suite 5 — Cost Estimation Engine

### TC-18 | Geographic Multiplier Applied Correctly
**Priority:** CRITICAL
**Code:**
```python
from src.cost_engine import calculate_adjusted_cost

base = 300000   # ₹3,00,000 knee replacement baseline (Tier 1)
tier2 = calculate_adjusted_cost(base_cost=base, city_tier=2)
tier3 = calculate_adjusted_cost(base_cost=base, city_tier=3)

assert 250000 <= tier2 <= 285000, f"Tier 2 expected ~₹2,75,000, got {tier2}"
assert 230000 <= tier3 <= 260000, f"Tier 3 expected ~₹2,50,000, got {tier3}"
print(f"PASS: Tier 2 = ₹{tier2:,} | Tier 3 = ₹{tier3:,}")
```

---

### TC-19 | Comorbidity Multiplier Increases Cost
**Priority:** CRITICAL
**Code:**
```python
from src.cost_engine import calculate_final_cost

base_cost = 200000
no_comorbidity = calculate_final_cost(adjusted_cost=base_cost, comorbidities=[])
with_hf = calculate_final_cost(
    adjusted_cost=base_cost,
    comorbidities=["heart_failure"]
)

assert with_hf > no_comorbidity, "Heart failure must increase cost"
# Heart failure multiplier = 3.3x per research data
assert with_hf >= no_comorbidity * 1.5, \
    f"Heart failure cost increase insufficient: {with_hf} vs {no_comorbidity}"
print(f"PASS: No comorbidity = ₹{no_comorbidity:,} | With HF = ₹{with_hf:,}")
```

---

### TC-20 | Angioplasty Pathway Phases Are Generated
**Priority:** HIGH
**Code:**
```python
from src.pathway_generator import generate_pathway

pathway = generate_pathway(icd_code="I25.10", procedure="angioplasty")
phase_names = [p["phase"] for p in pathway]

required_phases = ["pre_diagnostics", "procedure", "hospitalization", "post_care"]
for phase in required_phases:
    assert phase in phase_names, f"Missing phase: {phase}"
print(f"PASS: Angioplasty pathway has {len(pathway)} phases: {phase_names}")
```

---

## Test Suite 6 — NBFC Loan Pre-Underwriting

### TC-21 | DTI < 30% Classified as Low Risk
**Priority:** HIGH
**Code:**
```python
from src.loan_engine import calculate_dti_band

result = calculate_dti_band(
    monthly_income=80000,
    existing_emis=5000,
    loan_amount=200000,
    tenure_months=24
)
assert result["risk_band"] == "LOW", f"Expected LOW, got {result['risk_band']}"
assert result["interest_rate_min"] <= 13.0
print(f"PASS: DTI = {result['dti']:.1f}% → {result['risk_band']} Risk")
```

---

### TC-22 | DTI > 50% Classified as Critical Risk
**Priority:** HIGH
**Code:**
```python
from src.loan_engine import calculate_dti_band

result = calculate_dti_band(
    monthly_income=20000,
    existing_emis=12000,
    loan_amount=200000,
    tenure_months=12
)
assert result["risk_band"] == "CRITICAL", f"Expected CRITICAL, got {result['risk_band']}"
assert result.get("cta") == "Recommend Alternate Financing"
print(f"PASS: DTI = {result['dti']:.1f}% → CRITICAL Risk correctly flagged")
```

---

## Test Suite 7 — Streamlit UI

### TC-23 | Streamlit App Starts Without Errors
**Priority:** CRITICAL
**Command:**
```bash
streamlit run app.py --server.headless true &
sleep 5
curl -s http://localhost:8501/healthz | grep -q "ok"
```
**Expected:** HTTP 200 and no ICD-10 error banner in app logs

---

### TC-24 | ICD-10 Status Shown in Sidebar
**Priority:** HIGH
**Manual Test:**
1. Open `http://localhost:8501`
2. Check sidebar for message: `✅ ICD-10 Ontology loaded (X,XXX clinical keywords)`
**Expected:** Green success indicator visible in sidebar

---

### TC-25 | App Displays Error Banner When ICD-10 Missing
**Priority:** HIGH
**Setup:** Delete `data/icd10_2022.json` and `data/icd10_fallback.json`
**Manual Test:**
1. Restart the Streamlit app
2. Verify a red error banner appears
3. Verify the app halts (does not partially load)
**Expected:** Error message instructs user to run `python setup_data.py`
**Teardown:** Restore data files

---

### TC-26 | Side-by-Side Hospital Comparison Renders (Gap 8)
**Priority:** HIGH
**Manual Test:**
1. Enter query: `"knee replacement surgery in Raipur"`
2. Verify at least 2 hospital columns appear side by side
3. Each column must show: Cost Range, Distance, Fusion Score, Key Strengths
**Expected:** `st.columns()` layout renders correctly with no Streamlit warnings

---

### TC-27 | Multi-Turn Memory Retains Comorbidity Context
**Priority:** HIGH
**Manual Test Sequence:**
1. Turn 1: `"I need knee replacement surgery"`
2. Turn 2: `"I also have diabetes"`
3. Turn 3: `"What will be the total cost?"`
**Expected:** Turn 3 cost estimate must be HIGHER than a diabetic-free estimate;
the agent must not ask "what procedure are you asking about?"

---

## Test Suite 8 — Explainable AI

### TC-28 | SHAP Waterfall Plot Generates for Top Hospital
**Priority:** MEDIUM
**Code:**
```python
from src.xai_engine import generate_shap_explanation

scores = {
    "clinical": 0.88,
    "reputation": 0.75,
    "accessibility": 0.90,
    "affordability": 0.85
}
explanation = generate_shap_explanation(scores)
assert "waterfall_data" in explanation
assert explanation["final_score"] == pytest.approx(0.847, abs=0.01)
print(f"PASS: SHAP explanation generated. Final score = {explanation['final_score']}")
```

---

### TC-29 | LIME Highlights Correct Trigger Words for RED Classification
**Priority:** MEDIUM
**Code:**
```python
from src.xai_engine import explain_severity_with_lime

explanation = explain_severity_with_lime(
    text="chest pain radiating to the left arm",
    predicted_severity="RED"
)
highlighted = explanation["highlighted_tokens"]
assert any("chest" in t or "pain" in t for t in highlighted), \
    f"Expected chest/pain in highlights, got: {highlighted}"
print(f"PASS: LIME highlighted tokens: {highlighted}")
```

---

## Test Suite 9 — RAG Confidence Scoring

### TC-30 | Confidence Score Formula is Correct
**Priority:** HIGH
**Code:**
```python
from src.rag_evaluator import compute_confidence

score = compute_confidence(
    faithfulness=0.9,
    contextual_relevancy=0.8,
    answer_relevancy=0.85
)
expected = 0.4 * 0.9 + 0.3 * 0.8 + 0.3 * 0.85   # = 0.855
assert abs(score - expected) < 0.001, f"Score mismatch: {score} vs {expected}"
print(f"PASS: Confidence score = {score:.3f}")
```

---

### TC-31 | Low Confidence Triggers Disclaimer Display
**Priority:** HIGH
**Code:**
```python
from src.rag_evaluator import compute_confidence, should_show_disclaimer

score = compute_confidence(faithfulness=0.4, contextual_relevancy=0.5, answer_relevancy=0.5)
assert should_show_disclaimer(score), \
    f"Score {score:.2f} should trigger disclaimer but didn't"
print(f"PASS: Score {score:.2f} correctly triggers disclaimer")
```

---

## Test Execution Summary Matrix

| Suite | Test ID | Feature | Priority | Type |
|-------|---------|---------|----------|------|
| 1 | TC-01 | Setup script creates file | CRITICAL | Automated |
| 1 | TC-02 | Loader returns index | CRITICAL | Automated |
| 1 | TC-03 | Fallback dataset loads | CRITICAL | Automated |
| 1 | TC-04 | RuntimeError on both missing | HIGH | Automated |
| 1 | TC-05 | Singleton caching | HIGH | Automated |
| 2 | TC-06 | Chest pain → R07.9 | CRITICAL | Automated |
| 2 | TC-07 | Knee pain → M17.x | CRITICAL | Automated |
| 2 | TC-08 | Diabetes → E11.x | HIGH | Automated |
| 2 | TC-09 | Unknown symptom → empty | HIGH | Automated |
| 2 | TC-10 | Schema validation | HIGH | Automated |
| 3 | TC-11 | NER entity extraction | CRITICAL | Automated |
| 3 | TC-12 | NER + ICD-10 integration | CRITICAL | Automated |
| 3 | TC-13 | Empty input handling | HIGH | Automated |
| 3 | TC-14 | Hindi input handling | MEDIUM | Automated |
| 4 | TC-15 | RED classification | CRITICAL | Automated |
| 4 | TC-16 | GREEN classification | CRITICAL | Automated |
| 4 | TC-17 | RED overrides budget | HIGH | Automated |
| 5 | TC-18 | Geographic multiplier | CRITICAL | Automated |
| 5 | TC-19 | Comorbidity multiplier | CRITICAL | Automated |
| 5 | TC-20 | Pathway phases generated | HIGH | Automated |
| 6 | TC-21 | DTI < 30% Low Risk | HIGH | Automated |
| 6 | TC-22 | DTI > 50% Critical Risk | HIGH | Automated |
| 7 | TC-23 | Streamlit app starts | CRITICAL | Semi-auto |
| 7 | TC-24 | ICD-10 sidebar status | HIGH | Manual |
| 7 | TC-25 | Error banner when missing | HIGH | Manual |
| 7 | TC-26 | Side-by-side comparison | HIGH | Manual |
| 7 | TC-27 | Multi-turn memory | HIGH | Manual |
| 8 | TC-28 | SHAP waterfall plot | MEDIUM | Automated |
| 8 | TC-29 | LIME token highlights | MEDIUM | Automated |
| 9 | TC-30 | Confidence formula | HIGH | Automated |
| 9 | TC-31 | Disclaimer trigger | HIGH | Automated |

---

## Quick Smoke Test (Run First After Any Change)

Run these 5 tests immediately after fixing the ICD-10 issue to confirm the core
pipeline is not broken:

```bash
python -c "
from src.icd10_loader import load_icd10, lookup_icd10
idx = load_icd10()
print(f'[1/5] ICD-10 loaded: {len(idx)} keywords')

r = lookup_icd10('chest pain')
assert r, 'No results for chest pain'
print(f'[2/5] chest pain → {r[0][\"code\"]} ({r[0][\"description\"]})')

from src.ner_pipeline import extract_and_standardize
result = extract_and_standardize('I have chest pain and diabetes')
assert result['entities'], 'NER returned no entities'
print(f'[3/5] NER entities: {result[\"icd_summary\"]}')

from src.severity_classifier import classify_severity
sev = classify_severity(result['entities'], result['raw_text'])
print(f'[4/5] Severity: {sev}')

from src.cost_engine import calculate_adjusted_cost
cost = calculate_adjusted_cost(300000, city_tier=3)
print(f'[5/5] Tier 3 cost (knee replacement): Rs {cost:,}')
print('ALL SMOKE TESTS PASSED')
"
```

**Expected output (all 5 lines print without exception):**
```
[1/5] ICD-10 loaded: XXXX keywords
[2/5] chest pain → R07.9 (Chest pain, unspecified)
[3/5] NER entities: ['R07.9', 'E11.9']
[4/5] Severity: YELLOW
[5/5] Tier 3 cost (knee replacement): Rs 249,000
ALL SMOKE TESTS PASSED
```

---

*Testing Plan Version 1.0 — Healthcare AI Navigator ICD-10 Feature Validation*
