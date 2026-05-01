# Healthcare AI Navigator — ICD-10 Fix & Full Application Prompt

## Document Purpose

This prompt specification ensures that the **ICD-10 Named Entity Recognition (NER) feature**
is correctly implemented and that every downstream component in the Healthcare AI Navigator
continues to operate in the exact flow described in the architectural strategy document.

The root error being resolved is:

```
WARNING - ICD-10 data file not found: data/icd10_2022.json
ERROR   - ICD-10 data file not found in any location
```

---

## 1. Project Context & Role

You are implementing a production-grade **AI-powered Healthcare Navigator and Cost Estimator**
targeting Tier 2 and Tier 3 Indian cities. The system is described as a "Kayak for Healthcare" —
it translates raw patient intent into standardized clinical pathways, scores providers through
transparent multi-source intelligence, and generates comorbidity-adjusted financial estimates.

The full technology stack is:

- **GraphRAG** (Neo4j + LangChain) — knowledge graph traversal
- **NER + ICD-10 Medical Ontology** — symptom standardization ← **THIS IS BROKEN**
- **LangChain Agentic AI** — multi-turn memory management
- **Symptom Severity Classifier** — LLM prompt-engineered triage
- **Cost Estimation Engine** — geographic + comorbidity adjustments
- **NBFC Loan Pre-Underwriting Engine** — DTI-based financial eligibility
- **Aspect-Based Sentiment Analysis (ABSA)** — patient review scoring
- **Appointment Availability Proxy** — queuing-theory-based wait time
- **Multi-Source Data Fusion Score** — weighted provider ranking
- **Geo-Spatial Intelligence** (geopy + Leaflet.js) — distance and mapping
- **Explainable AI** (LIME + SHAP) — transparent recommendations
- **RAG Confidence Scoring** — hallucination safeguard

---

## 2. The ICD-10 Feature — What It Must Do

### 2.1 Role in the Pipeline

The ICD-10 integration is the **bridge between free-text patient language and structured
clinical reasoning**. Without it, all downstream features (cost estimation, pathway generation,
provider scoring) receive unvalidated, non-standardized inputs.

**Flow position:**

```
User Free-Text Input
        ↓
  NER Pipeline  (extracts symptoms, conditions, body parts, procedures)
        ↓
  ICD-10 Lookup  ← BROKEN HERE
        ↓
  Standardized Clinical Code (e.g., I25.10 for Coronary Artery Disease)
        ↓
  GraphRAG Cypher Query + Cost Engine + Pathway Generator
```

### 2.2 Expected Behavior

When a user types: `"I have severe chest pain radiating to my left arm"`

1. **NER** extracts: `["severe chest pain", "left arm", "radiating"]`
2. **ICD-10 Lookup** maps: `"chest pain" → R07.9`, cross-linked to `I21.x (Myocardial Infarction)`
3. **Severity Classifier** reads the ICD code → flags as `RED (Emergency)`
4. **Pathway Generator** maps Angioplasty clinical phases
5. **Cost Engine** applies geographic + comorbidity multipliers

---

## 3. Fix Specification — ICD-10 Data File

### 3.1 Problem Diagnosis

The application looks for the ICD-10 data at `data/icd10_2022.json` but finds nothing.
This can happen because:

- The file was never downloaded/created
- The path is wrong relative to where the app runs
- The JSON was downloaded but placed in the wrong directory
- The file was excluded from version control (`.gitignore`)

### 3.2 Required Directory Structure

Enforce this structure in the project root:

```
project_root/
├── app.py                   # Streamlit entry point
├── data/
│   ├── icd10_2022.json      # ← PRIMARY location the app checks
│   └── icd10_fallback.json  # ← Backup minimal dataset (see Section 3.4)
├── src/
│   ├── ner_pipeline.py
│   ├── icd10_loader.py      # ← New module (see Section 3.5)
│   ├── cost_engine.py
│   ├── graph_rag.py
│   └── ...
├── requirements.txt
└── prompt.md
```

### 3.3 Downloading the ICD-10 JSON (Automated Setup Script)

Add a `setup_data.py` script at project root. This must be run once before the app starts,
or triggered automatically on first launch if the file is missing.

```python
# setup_data.py
"""
Downloads the 2022 ICD-10-CM JSON from the official CMS-derived GitHub repository.
Source: https://github.com/smog1210/2022-ICD-10-CM-JSON
"""

import os
import json
import urllib.request
import logging

logger = logging.getLogger(__name__)

ICD10_URL = (
    "https://raw.githubusercontent.com/smog1210/2022-ICD-10-CM-JSON"
    "/main/icd10cm_codes_2022.json"
)
DATA_DIR = "data"
ICD10_PATH = os.path.join(DATA_DIR, "icd10_2022.json")


def download_icd10():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(ICD10_PATH):
        logger.info(f"ICD-10 data already exists at {ICD10_PATH}")
        return True
    try:
        logger.info(f"Downloading ICD-10 data from {ICD10_URL} ...")
        urllib.request.urlretrieve(ICD10_URL, ICD10_PATH)
        # Validate it is valid JSON
        with open(ICD10_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"ICD-10 download successful. Total codes: {len(data)}")
        return True
    except Exception as e:
        logger.error(f"Failed to download ICD-10 data: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    download_icd10()
```

### 3.4 Fallback Minimal Dataset

If the download fails (offline environment, network restrictions), the application must NOT
crash. Create `data/icd10_fallback.json` with a minimal set covering the most common
conditions the navigator handles:

```json
[
  {"code": "R07.9",  "description": "Chest pain, unspecified"},
  {"code": "R07.4",  "description": "Chest pain on breathing"},
  {"code": "I25.10", "description": "Atherosclerotic heart disease of native coronary artery without angina pectoris"},
  {"code": "I21.9",  "description": "Acute myocardial infarction, unspecified"},
  {"code": "M17.11", "description": "Primary osteoarthritis, right knee"},
  {"code": "M17.12", "description": "Primary osteoarthritis, left knee"},
  {"code": "E11.9",  "description": "Type 2 diabetes mellitus without complications"},
  {"code": "I50.9",  "description": "Heart failure, unspecified"},
  {"code": "N18.9",  "description": "Chronic kidney disease, unspecified"},
  {"code": "I10",    "description": "Essential (primary) hypertension"},
  {"code": "J44.1",  "description": "Chronic obstructive pulmonary disease with acute exacerbation"},
  {"code": "K80.20", "description": "Calculus of gallbladder without cholecystitis"},
  {"code": "N20.0",  "description": "Calculus of kidney"},
  {"code": "G43.909","description": "Migraine, unspecified"},
  {"code": "R51",    "description": "Headache"},
  {"code": "M54.5",  "description": "Low back pain"},
  {"code": "R10.9",  "description": "Unspecified abdominal pain"},
  {"code": "R05",    "description": "Cough"},
  {"code": "R06.0",  "description": "Dyspnoea"},
  {"code": "R55",    "description": "Syncope and collapse"}
]
```

### 3.5 ICD-10 Loader Module (`src/icd10_loader.py`)

Replace any inline loading logic with this dedicated, fault-tolerant module:

```python
# src/icd10_loader.py
"""
Fault-tolerant ICD-10 data loader.
Search priority:
  1. data/icd10_2022.json       (full dataset)
  2. data/icd10_fallback.json   (minimal bundled dataset)
  3. Auto-download attempt      (calls setup_data.py logic)
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SEARCH_PATHS = [
    "data/icd10_2022.json",
    "data/icd10_fallback.json",
    os.path.join(os.path.dirname(__file__), "..", "data", "icd10_2022.json"),
    os.path.join(os.path.dirname(__file__), "..", "data", "icd10_fallback.json"),
]

_icd10_index: Optional[dict] = None   # lazy-loaded singleton


def _build_index(raw: list) -> dict:
    """
    Build a keyword → [ICD codes] lookup dictionary.
    Supports both list-of-dicts and nested dict formats from the GitHub repo.
    """
    index = {}
    for entry in raw:
        # Handle both {"code": ..., "description": ...} and {"code": ..., "desc": ...}
        code = entry.get("code", entry.get("Code", ""))
        desc = entry.get("description", entry.get("desc", entry.get("Description", "")))
        if not code or not desc:
            continue
        # Index every meaningful word in the description
        for word in desc.lower().split():
            if len(word) > 3:   # skip stopwords by length heuristic
                index.setdefault(word, []).append({"code": code, "description": desc})
    return index


def load_icd10() -> dict:
    """
    Returns keyword index. Tries all paths. Auto-downloads if missing.
    Raises RuntimeError only if ALL fallbacks fail.
    """
    global _icd10_index
    if _icd10_index is not None:
        return _icd10_index

    for path in SEARCH_PATHS:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                # Normalize: if the JSON root is a dict with a list inside
                if isinstance(raw, dict):
                    raw = raw.get("codes", raw.get("data", list(raw.values())[0]))
                _icd10_index = _build_index(raw)
                logger.info(
                    f"ICD-10 loaded from '{path}'. "
                    f"Index size: {len(_icd10_index)} keywords."
                )
                return _icd10_index
            except Exception as e:
                logger.warning(f"Failed to load ICD-10 from '{path}': {e}")

    # Last resort: attempt download
    logger.warning("ICD-10 file not found in any location. Attempting download...")
    try:
        from setup_data import download_icd10
        if download_icd10():
            return load_icd10()   # recursive retry after download
    except Exception as e:
        logger.error(f"Auto-download failed: {e}")

    raise RuntimeError(
        "ICD-10 data unavailable. Run `python setup_data.py` to download it. "
        "Alternatively, ensure 'data/icd10_fallback.json' exists."
    )


def lookup_icd10(symptom_phrase: str, top_k: int = 3) -> list[dict]:
    """
    Maps a symptom phrase to the top_k most likely ICD-10 codes.

    Args:
        symptom_phrase: Free-text symptom, e.g. "severe chest pain"
        top_k: Maximum number of ICD codes to return

    Returns:
        List of dicts: [{"code": "R07.9", "description": "Chest pain, unspecified"}, ...]
    """
    index = load_icd10()
    scores: dict[str, dict] = {}

    keywords = symptom_phrase.lower().split()
    for word in keywords:
        matches = index.get(word, [])
        for match in matches:
            code = match["code"]
            scores[code] = scores.get(code, {"code": code, "description": match["description"], "score": 0})
            scores[code]["score"] += 1

    ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    return [{"code": r["code"], "description": r["description"]} for r in ranked[:top_k]]
```

---

## 4. NER Pipeline Integration (`src/ner_pipeline.py`)

The NER pipeline must call `lookup_icd10()` immediately after entity extraction.
The output tuple `(entities, icd_codes)` is what flows into the LangChain agent.

```python
# src/ner_pipeline.py  — relevant section

from src.icd10_loader import lookup_icd10

def extract_and_standardize(user_text: str) -> dict:
    """
    Step 1: NER extracts raw entities.
    Step 2: ICD-10 lookup standardizes each entity.

    Returns a structured payload for the LangChain agent.
    """
    # --- Step 1: NER (use spaCy en_core_sci_sm or a regex heuristic) ---
    raw_entities = run_ner(user_text)   # returns list of strings

    # --- Step 2: ICD-10 standardization ---
    standardized = []
    for entity in raw_entities:
        icd_matches = lookup_icd10(entity, top_k=2)
        standardized.append({
            "raw_entity": entity,
            "icd_codes": icd_matches,
            "primary_code": icd_matches[0]["code"] if icd_matches else "UNKNOWN",
            "primary_description": icd_matches[0]["description"] if icd_matches else entity,
        })

    return {
        "raw_text": user_text,
        "entities": standardized,
        "icd_summary": [s["primary_code"] for s in standardized],
    }
```

---

## 5. Full Application Flow (Preserved End-to-End)

The following sequence must be maintained exactly as specified in the architecture document.
Each step references the component that implements it.

```
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1 — User Input (Streamlit Chat Interface)                     │
│  User types free-text query in their native language or English.    │
│  LangChain RunnableWithMessageHistory maintains session context.    │
│  Session ID prevents cross-user state leakage in multi-user mode.  │
└──────────────────────────┬──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2 — NER Pipeline  (src/ner_pipeline.py)                       │
│  Extracts: symptoms | body parts | conditions | procedures          │
│  Tool: spaCy with en_core_sci_sm OR custom regex entity rules       │
└──────────────────────────┬──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3 — ICD-10 Ontology Lookup  (src/icd10_loader.py)  ← FIXED   │
│  Maps raw NER entities → ICD-10-CM codes (2022 edition)            │
│  Output: standardized clinical codes + descriptions                 │
│  Fallback: minimal bundled JSON if full dataset unavailable         │
└──────────────────────────┬──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4 — Symptom Severity Classifier (LLM Prompt Engineering)      │
│  Input: ICD codes + raw entities                                    │
│  Output: RED (Emergency) | YELLOW (Urgent) | GREEN (Elective)       │
│  RED overrides all filters → triggers 24/7 emergency display        │
│  Ethical constraint: adds disclaimer — not medical advice           │
└──────────────────────────┬──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 5 — GraphRAG Query  (Neo4j + LangChain Cypher Chain)          │
│  ICD codes → Cypher query → graph traversal                         │
│  Traverses: Symptom → Diagnosis → Procedure → Hospital              │
│  Parallel: vector index retrieves unstructured clinical guidelines  │
└──────────────────────────┬──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 6 — Treatment Pathway Generator  (Gap 9)                      │
│  Maps procedure to clinical phases:                                 │
│    Pre-Diagnostics → Surgery → Hospitalization → Post-Care         │
│  Attaches cost ranges per phase (geographic + comorbidity adjusted) │
└──────────────────────────┬──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 7 — Cost Estimation Engine  (Gap 5 + Gap 6)                   │
│                                                                     │
│  Adjusted_Cost = Base_Clinical_Rate × γ_geo                        │
│               + (Predicted_Days × Room_Rate)                        │
│                                                                     │
│  Final_Cost = Adjusted_Cost × (1 + Σ ωᵢCᵢ)                        │
│    where Cᵢ = comorbidity present flag                              │
│          ωᵢ = empirical weight (ASCVD=1.2, HF=2.3, DM=0.8, etc.)  │
│                                                                     │
│  Geographic multiplier (γ_geo):                                     │
│    Tier 1 (Mumbai/Delhi)  = 1.00                                    │
│    Tier 2 (Nagpur/Jaipur) = 0.92                                    │
│    Tier 3 (Raipur/etc.)   = 0.83                                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 8 — Provider Scoring (Multi-Source Data Fusion, Gap 7)        │
│                                                                     │
│  Fusion Score =                                                     │
│    0.40 × Clinical Score  (NABH/JCI + procedure volume)            │
│    0.25 × Reputation Score (ABSA sentiment on reviews)             │
│    0.20 × Accessibility Score (distance + wait time proxy)         │
│    0.15 × Affordability Score (price tier + cashless track record)  │
│                                                                     │
│  All sub-scores min-max normalized → [0, 1]                         │
└──────────────────────────┬──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 9 — NBFC Loan Pre-Underwriting  (Gap 3)                       │
│                                                                     │
│  DTI = (Existing_EMIs + Proposed_Medical_EMI) / Monthly_Income     │
│  Loan covers up to 80% of estimated procedure cost                  │
│  EMI calculated across 12 / 24 / 36 month tenures                   │
│                                                                     │
│  DTI Bands:                                                         │
│    < 30%  → Low Risk   → 12–13% interest → "Apply Now"             │
│    30–40% → Medium     → 13–15%          → Standard Application    │
│    40–50% → High Risk  → 15–16%          → Manual Review           │
│    > 50%  → Critical   → N/A             → Alternate Financing      │
└──────────────────────────┬──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 10 — Insurance Cashless Estimator  (Gap 2)                    │
│  Classifies hospitals: Premium | Mid-tier | Budget                  │
│  Cross-references patient policy sub-limits (room rent caps, etc.)  │
│  Predicts OOP expense and pre-authorization likelihood              │
└──────────────────────────┬──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 11 — RAG Confidence Scoring                                   │
│                                                                     │
│  S = 0.4 × Faithfulness                                             │
│    + 0.3 × Contextual_Relevancy                                     │
│    + 0.3 × Answer_Relevancy                                         │
│                                                                     │
│  If S < threshold → display uncertainty flag + mandatory disclaimer │
│  "This system provides decision support only and does not           │
│   constitute medical advice or diagnosis."                          │
└──────────────────────────┬──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 12 — Streamlit UI Output  (Gap 8)                             │
│  st.columns(n) → side-by-side hospital comparison                  │
│  Leaflet.js map → color-coded markers by Fusion Score              │
│  SHAP waterfall plot → why this hospital ranked #1                 │
│  LIME highlights → which symptom words triggered emergency routing  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. LangChain Agent System Prompt (Updated for ICD-10 Awareness)

Use this system prompt for the LangChain agent. It must be passed in every call to
`RunnableWithMessageHistory`.

```
You are a Healthcare Decision Intelligence Assistant for the Indian market,
with deep expertise in clinical pathways, medical cost estimation, and
healthcare navigation across Tier 1, Tier 2, and Tier 3 cities.

CORE RULES:
1. You are NOT a doctor. You do NOT provide diagnoses or medical advice.
   Every response involving symptoms MUST end with:
   "⚠️ This is decision support only and does not constitute medical advice or diagnosis."

2. You always operate on ICD-10 standardized codes, not raw symptom text.
   When a user describes symptoms, you refer to their ICD-10-mapped entities
   (provided to you in the context payload) as the basis for all cost and
   pathway estimations.

3. Severity Classification is mandatory before cost estimation:
   - RED (Emergency): Route to emergency facilities. Override budget filters.
   - YELLOW (Urgent): Proceed with standard flow, flag urgency.
   - GREEN (Elective): Standard discovery and cost estimation flow.

4. Multi-turn memory: You remember everything the user said in this session.
   If they mentioned diabetes 3 turns ago and now ask about surgery costs,
   you automatically apply the diabetes comorbidity multiplier without
   asking them to repeat it.

5. Geographic awareness: Always ask for or confirm the user's city/location
   before generating cost estimates. Apply the correct tier multiplier:
   Tier 1 (Mumbai, Delhi, Bangalore) = baseline
   Tier 2 (Nagpur, Jaipur, Lucknow) = 0.92 × baseline
   Tier 3 (Raipur, Ahmedabad, Patna) = 0.83 × baseline

6. Financial disclosure: When presenting EMI options, always show the
   DTI band the user falls into and the corresponding risk flag.

7. Confidence: If you are uncertain about any cost figure or clinical
   pathway detail, explicitly state your uncertainty. Do not hallucinate
   hospital names, costs, or clinical data.

CONTEXT PAYLOAD FORMAT (provided by the NER + ICD-10 pipeline):
{
  "user_query": "<original text>",
  "entities": [
    {
      "raw_entity": "chest pain",
      "primary_code": "R07.9",
      "primary_description": "Chest pain, unspecified",
      "icd_codes": [...]
    }
  ],
  "severity": "RED | YELLOW | GREEN",
  "location": "<city>",
  "comorbidities": ["diabetes", "hypertension"],
  "financial_profile": {"monthly_income": 0, "existing_emis": 0}
}
```

---

## 7. Streamlit App Startup Guard

In `app.py`, add an ICD-10 availability check at the very top, before any other
Streamlit widget renders:

```python
# app.py — top of file, after imports

import streamlit as st
from src.icd10_loader import load_icd10

@st.cache_resource(show_spinner="Loading ICD-10 medical ontology...")
def initialize_icd10():
    try:
        index = load_icd10()
        return {"status": "ok", "size": len(index)}
    except RuntimeError as e:
        return {"status": "error", "message": str(e)}

icd10_status = initialize_icd10()

if icd10_status["status"] == "error":
    st.error(
        f"⚠️ ICD-10 Medical Ontology could not be loaded.\n\n"
        f"**Error:** {icd10_status['message']}\n\n"
        "**Fix:** Run `python setup_data.py` in your project root, then restart the app."
    )
    st.stop()
else:
    st.sidebar.success(
        f"✅ ICD-10 Ontology loaded ({icd10_status['size']:,} clinical keywords)"
    )
```

---

## 8. Environment & Dependency Checklist

Ensure `requirements.txt` includes:

```
# Core AI / NLP
langchain>=0.2.0
langchain-openai>=0.1.0
langchain-community>=0.2.0
openai>=1.0.0
spacy>=3.7.0
# python -m spacy download en_core_sci_sm  (run separately)

# Knowledge Graph
neo4j>=5.0.0

# Geospatial
geopy>=2.4.0
folium>=0.16.0
streamlit-folium>=0.20.0

# Sentiment Analysis
vaderSentiment>=3.3.2
xgboost>=2.0.0
scikit-learn>=1.4.0

# Explainable AI
shap>=0.44.0
lime>=0.2.0

# Frontend
streamlit>=1.35.0

# Evaluation
deepeval>=0.21.0
```

---

## 9. Deployment Checklist Before Launch

- [ ] `python setup_data.py` runs successfully and creates `data/icd10_2022.json`
- [ ] `data/icd10_fallback.json` exists with minimum 20 critical condition codes
- [ ] `src/icd10_loader.py` loads without errors and returns a non-empty index
- [ ] `app.py` sidebar shows "✅ ICD-10 Ontology loaded (X keywords)"
- [ ] NER pipeline returns at least one ICD code for "chest pain"
- [ ] LangChain agent context payload contains `entities[].primary_code`
- [ ] Severity classifier correctly returns RED for "chest pain radiating to left arm"
- [ ] Cost engine applies geographic multiplier based on detected city tier
- [ ] DTI calculation runs when monthly_income and existing_emis are provided
- [ ] SHAP waterfall plot renders for the top-ranked hospital
- [ ] Confidence score disclaimer appears when S < 0.70

---

*This prompt.md is the single source of truth for restoring and validating the ICD-10
feature within the complete Healthcare AI Navigator pipeline.*
