# HealthNav — Agent Instruction Manual (`instructionagent.md`)

> **HealthNav** · *Compare. Estimate. Decide.*
> Deployed Frontend: [https://tenzor-x.vercel.app/](https://tenzor-x.vercel.app/)
> Architecture Source: `Healthcare_AI_Solution_Strategy.pdf`

---

## 0. Document Purpose

This file is the **single source of truth** for every AI agent, orchestration layer, data pipeline, and frontend binding in the HealthNav platform. It is written so that a developer reading only this file can implement the complete backend and connect it to the existing Next.js / React frontend without any other reference document.

Every section maps directly to:
1. A named agent or sub-system
2. Its input schema (what the frontend sends)
3. Its output schema (what the frontend renders)
4. Its internal reasoning steps (how the LLM/logic processes it)
5. The gap it addresses from the architecture PDF

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HealthNav Frontend (Next.js)                         │
│  Chat Panel │ Results Panel (List/Map) │ Sidebar │ Financial Overlay         │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │  HTTP / WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MASTER ORCHESTRATOR AGENT (LangChain)                    │
│  Session Manager │ Intent Router │ Multi-Turn Memory │ Response Formatter    │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┬───────────────────┘
   │          │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼          ▼
[NER +    [Clinical  [Hospital  [Financial [Geo-      [XAI
 Triage    Pathway    Discovery  Engine]    Spatial    Explainer]
 Agent]    Agent]     Agent]                Agent]
```

### Technology Stack
| Layer | Technology |
|---|---|
| LLM | `claude-sonnet-4-20250514` (primary), fallback to offline static data |
| Orchestration | LangChain `RunnableWithMessageHistory` + LangGraph |
| Knowledge Graph | Neo4j (GraphRAG + Cypher traversal) |
| Vector Store | Neo4j vector index (embedding: `text-embedding-3-small`) |
| NER | spaCy `en_core_web_trf` + custom medical NER model |
| Ontologies | ICD-10-CM JSON (smog1210/2022-ICD-10-CM-JSON), SNOMED CT |
| Geo | `geopy` (Nominatim / GoogleV3) + Leaflet.js (`streamlit-folium`) |
| Sentiment | XGBoost + TF-IDF + VADER (ABSA pipeline) |
| XAI | SHAP `TreeExplainer` + LIME text perturbation |
| API | FastAPI (Python backend) |
| Frontend | Next.js / React (deployed on Vercel) |

---

## 2. Session & Memory Management

### 2.1 Session Initialization

Every user session must generate a unique `session_id` (UUID v4). All agents share state through this session object.

```python
# REQUIRED session state schema
session = {
    "session_id": "uuid-v4",
    "user_location": {"city": str, "state": str, "lat": float, "lng": float},
    "patient_profile": {
        "age": int | None,
        "comorbidities": list[str],  # e.g. ["diabetes", "cardiac history"]
        "budget_inr": int | None,
        "insurance": bool
    },
    "conversation_history": [],  # LangChain message list
    "last_procedure": str | None,  # e.g. "Total Knee Arthroplasty (TKA)"
    "last_results": dict | None,   # last agent output (for follow-ups)
    "saved_results": list[dict],
    "appointment_requests": list[dict]
}
```

**Why this matters for the frontend:**
- The sidebar **"My Appointment Requests"** badge count = `len(session["appointment_requests"])`
- **"Saved Results"** sidebar section = `session["saved_results"]`
- **"History"** sidebar = last N `conversation_history` user messages
- The bottom bar chips **"Add Location"**, **"Patient Details"**, **"Set Budget"** write into `session["user_location"]`, `session["patient_profile"]`, `session["patient_profile"]["budget_inr"]`

### 2.2 Multi-Turn Memory (Gap addressed: Conversational Continuity)

Use `RunnableWithMessageHistory` with a session-scoped `InMemoryChatMessageHistory`:

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import InMemoryChatMessageHistory

store = {}  # In-memory; replace with Redis for production

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

chain_with_history = RunnableWithMessageHistory(
    master_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)
```

**Critical:** Never use global state; always bind to `session_id` to prevent cross-user contamination in concurrent deployments.

---

## 3. Agent Definitions

---

### AGENT 1 — NER + Triage Agent

**Responsibility:** Parse the raw user text query. Extract all clinical entities. Classify urgency. Map to ICD-10 / SNOMED CT.

**Triggered by:** Every new user message arriving at the chat input.

**Input (from frontend):**
```json
{
  "raw_query": "Knee replacement near Nagpur under Rs 2 lakh",
  "session_id": "abc-123",
  "patient_profile": { "comorbidities": ["diabetes"] }
}
```

**Internal Processing Steps:**

1. **NER Extraction** — Run spaCy pipeline:
   - Extract: `condition`, `body_part`, `procedure`, `city`, `budget_inr`, `symptoms`
   - Example output: `{ "procedure": "knee replacement", "city": "Nagpur", "budget_inr": 200000 }`

2. **ICD-10 Lookup** — Query the ICD-10-CM JSON vocabulary:
   ```python
   icd_map = load_icd10_json("2022-ICD-10-CM.json")
   icd_code = fuzzy_lookup(icd_map, extracted_condition)
   # Returns: { "code": "M17.11", "description": "Primary osteoarthritis, right knee" }
   ```

3. **SNOMED CT Mapping** — Map to SNOMED concept ID:
   ```python
   snomed_id = snomed_lookup(icd_code)
   # Returns: "179344001"
   ```

4. **Procedure Standardization** — Canonical procedure name:
   ```python
   std_procedure = canonical_procedure_map["knee replacement"]
   # Returns: "Total Knee Arthroplasty (TKA)"
   ```

5. **Symptom Severity Classification** (LLM Prompt Engineering):
   ```
   SYSTEM: You are a clinical triage assistant. Given the extracted symptoms and
   procedure request, classify urgency as exactly one of: RED, YELLOW, GREEN.
   RED = emergency (chest pain+left arm, stroke symptoms, acute trauma)
   YELLOW = urgent (significant pain, progressive symptoms)
   GREEN = elective (planned surgery, routine consultation)
   Output ONLY a JSON: {"triage": "GREEN", "reasoning": "..."}
   Do not provide diagnosis or treatment advice.
   ```
   - If `triage == "RED"`: Override all geo/budget filters; set `appointment_proxy = "24/7 emergency available ✅"`

**Output (sent to Master Orchestrator):**
```json
{
  "agent": "ner_triage",
  "canonical_procedure": "Total Knee Arthroplasty (TKA)",
  "category": "Orthopedic Surgery",
  "icd10": "M17.11 — Primary osteoarthritis, right knee",
  "snomed_ct": "179344001",
  "city": "Nagpur",
  "city_tier": 2,
  "budget_inr": 200000,
  "triage": "GREEN",
  "mapping_confidence": 86,
  "extracted_comorbidities": ["diabetes"]
}
```

**Frontend Binding — Results Panel "Clinical Interpretation" Section:**
```
Your query: [raw_query]
Mapping Confidence: [mapping_confidence]%
Procedure: [canonical_procedure]   Category: [category]
ICD-10: [icd10]                    SNOMED CT: [snomed_ct]
```

---

### AGENT 2 — Clinical Pathway Agent

**Responsibility:** Generate the step-by-step treatment pathway with per-phase cost ranges for the identified procedure. Adjust for comorbidities (Gap 9, Gap 6).

**Triggered by:** NER Agent output when triage is YELLOW or GREEN.

**Input:**
```json
{
  "canonical_procedure": "Total Knee Arthroplasty (TKA)",
  "city_tier": 2,
  "comorbidities": ["diabetes", "cardiac history"],
  "age": null
}
```

**Internal Processing Steps:**

1. **GraphRAG Pathway Retrieval** — Cypher query to Neo4j:
   ```cypher
   MATCH (proc:Procedure {name: "Total Knee Arthroplasty"})
   -[:HAS_PATHWAY]->(phase:PathwayPhase)
   RETURN phase.name, phase.duration, phase.cost_min, phase.cost_max
   ORDER BY phase.sequence
   ```

2. **Geographic Cost Adjustment** (Gap 5):
   ```python
   TIER_MULTIPLIERS = { 1: 1.00, 2: 0.68, 3: 0.55 }
   gamma_geo = TIER_MULTIPLIERS[city_tier]
   adj_cost = base_cost * gamma_geo + (predicted_days * room_rate * gamma_geo)
   ```

3. **Comorbidity Cost Adjustment** (Gap 6):
   ```python
   COMORBIDITY_WEIGHTS = {
       "diabetes":          {"min_add": 10000,  "max_add": 30000},
       "cardiac history":   {"min_add": 40000,  "max_add": 150000},
       "heart failure":     {"multiplier": 3.3},
       "kidney disease":    {"multiplier": 2.7},
       "ascvd":             {"multiplier": 2.2}
   }
   # Final cost: Adjusted_Cost × (1 + Σ ωᵢCᵢ)
   ```

4. **LLM Pathway Enrichment** — Use LLM to generate patient-friendly explanations of each phase:
   ```
   SYSTEM: You are a patient-education assistant. Given this clinical pathway phase,
   write 1 sentence explaining what happens to the patient in plain language.
   Output JSON only: {"plain_explanation": "..."}
   ```

**Output:**
```json
{
  "agent": "clinical_pathway",
  "pathway_steps": [
    { "step": 1, "name": "Pre-op assessment",      "duration": "1-2 days",   "cost_min": 3000,   "cost_max": 8000  },
    { "step": 2, "name": "Implant selection",       "duration": "1 day",      "cost_min": 20000,  "cost_max": 60000 },
    { "step": 3, "name": "Surgery",                 "duration": "2-3 hrs",    "cost_min": 80000,  "cost_max": 120000},
    { "step": 4, "name": "Hospital recovery",       "duration": "3-5 days",   "cost_min": 30000,  "cost_max": 60000 },
    { "step": 5, "name": "Physiotherapy follow-up", "duration": "6-12 weeks", "cost_min": 5000,   "cost_max": 15000 }
  ],
  "total_min": 138000,
  "total_max": 242000,
  "comorbidity_impacts": [
    { "condition": "diabetes",        "add_min": 10000, "add_max": 30000  },
    { "condition": "cardiac history", "add_min": 40000, "add_max": 150000 }
  ],
  "cost_confidence": 74,
  "geo_adjustment_note": "Cost adjusted for Nagpur (tier2). Approximately 32% lower than metro benchmarks."
}
```

**Frontend Binding — Results Panel "Treatment Pathway" Section:**
- Render each `pathway_steps` item as an arrow-connected step card
- Render `comorbidity_impacts` as warning badges below the cost breakdown
- Render `geo_adjustment_note` as a callout below the cost estimate
- Render `cost_confidence` as the confidence badge on the cost card

---

### AGENT 3 — Hospital Discovery Agent

**Responsibility:** Find, score, and rank hospitals for the procedure in the given city. Produce the Multi-Source Data Fusion Score for each. (Gaps 1, 4, 7, 8)

**Triggered by:** Clinical Pathway Agent output.

**Input:**
```json
{
  "canonical_procedure": "Total Knee Arthroplasty (TKA)",
  "city": "Nagpur",
  "lat": 21.1458,
  "lng": 79.0882,
  "budget_inr": 200000,
  "tier_filter": "all",
  "sort": "best_match",
  "nabh_only": false
}
```

**Internal Processing Steps:**

1. **Neo4j Hospital Retrieval:**
   ```cypher
   MATCH (h:Hospital)-[:LOCATED_IN]->(c:City {name: "Nagpur"})
   MATCH (h)-[:PERFORMS]->(proc:Procedure {name: "Total Knee Arthroplasty"})
   RETURN h.name, h.address, h.lat, h.lng, h.tier, h.nabh,
          h.bed_count, h.specialist_count, h.procedure_volume, h.star_rating
   ```

2. **Geo-Distance Calculation (Gap spatial):**
   ```python
   from geopy.distance import geodesic
   distance_km = geodesic((user_lat, user_lng), (hospital_lat, hospital_lng)).km
   ```

3. **Appointment Availability Proxy (Gap 4):**
   ```python
   # Based on queuing theory / compartmental model
   def appointment_proxy(beds, occupancy_rate, specialist_count, has_er):
       if has_er:
           return "24/7 emergency available ✅"
       throughput = (beds * (1 - occupancy_rate)) / specialist_count
       if throughput > 5:    return "Appointments usually available within 2-3 days"
       elif throughput > 2:  return "Estimated waiting time: 4-7 days"
       else:                 return "Waiting time: 1-2 weeks"
   ```

4. **ABSA Sentiment Score (Gap 1):**
   ```python
   # Run VADER + XGBoost on scraped Google Maps / forum reviews
   absa_scores = {
       "doctors_services": 0.82,
       "staff_services": 0.71,
       "hospital_facilities": 0.78,
       "affordability": 0.69
   }
   reputation_score = weighted_avg(absa_scores)
   ```

5. **Multi-Source Data Fusion Score (Gap 7):**
   ```python
   # All sub-scores normalized via min-max + sigmoid mapping to [0,1]
   fusion_score = (
       0.40 * clinical_score    +   # procedure volume, NABH/JCI
       0.25 * reputation_score  +   # ABSA + star rating
       0.20 * accessibility_score+  # distance + appointment proxy
       0.15 * affordability_score   # budget match + pricing transparency
   )
   # Example: 0.40×0.88 + 0.25×0.75 + 0.20×0.90 + 0.15×0.85 = 0.847
   ```

6. **Hospital Cost Estimation per tier:**
   ```python
   TIER_COST_RANGES = {
       "budget":  (80000,  140000),
       "mid-tier":(120000, 220000),
       "premium": (250000, 450000)
   }
   ```

**Output:**
```json
{
  "agent": "hospital_discovery",
  "result_count": 3,
  "hospitals": [
    {
      "id": "hosp_001",
      "name": "ABC Heart & Ortho Institute",
      "address": "Civil Lines, Nagpur, Maharashtra",
      "lat": 21.155, "lng": 79.091,
      "distance_km": 5.2,
      "tier": "mid-tier",
      "rating": 4.5,
      "nabh": true,
      "cost_min": 140000, "cost_max": 220000,
      "cost_confidence": 75,
      "fusion_score": 0.847,
      "tags": ["High Procedure Volume", "NABH Accredited", "In Budget"],
      "appointment_proxy": "Appointments usually available within 2-3 days",
      "specialties": ["Orthopedics"],
      "absa_scores": {
        "doctors_services": 0.82,
        "staff_services": 0.71,
        "hospital_facilities": 0.78,
        "affordability": 0.69
      },
      "shap_explanation": {
        "clinical_contribution": "+0.12",
        "accessibility_contribution": "+0.09",
        "affordability_contribution": "-0.02"
      }
    }
  ],
  "map_markers": [
    { "id": "hosp_001", "lat": 21.155, "lng": 79.091, "tier": "mid-tier", "color": "#6B7CFF" }
  ]
}
```

**Frontend Binding:**
- **List View:** Render each hospital card with name, address, distance, tier badge, rating stars, cost range, confidence badge, tags, "View Details" and "Compare" buttons
- **Map View:** Plot `map_markers` on Leaflet map with color coded by `tier` (Premium = blue, Mid-range = purple, Budget = green). Clicking a marker opens cost breakdown sidebar pane
- **Filter chips:** "All Tiers", "Premium", "Mid-tier", "Budget", "NABH Only" filter `hospitals` array by `tier` and `nabh` fields
- **Sort dropdown:** "Best Match" = sort by `fusion_score` DESC; "Distance" = sort by `distance_km` ASC

---

### AGENT 4 — Financial Engine Agent

**Responsibility:** Calculate EMI, assess loan eligibility via DTI, surface government schemes, produce per-hospital cost breakdown. (Gaps 2, 3)

**Triggered by:** Hospital Discovery Agent output OR when user clicks "View Cost Breakdown" / "Financial Assistance Guide".

**Input:**
```json
{
  "procedure_cost_estimate": 200000,
  "patient_income_monthly": null,
  "existing_emis": null,
  "loan_tenure_months": 24,
  "city": "Nagpur",
  "hospital_tier": "mid-tier",
  "comorbidities": ["diabetes"]
}
```

**Internal Processing Steps:**

1. **Loan Amount Calculation:**
   ```python
   LOAN_COVERAGE = 0.80
   loan_amount = procedure_cost_estimate * LOAN_COVERAGE
   ```

2. **EMI Calculation (Reducing Balance):**
   ```python
   def calculate_emi(principal, annual_rate_pct, months):
       r = (annual_rate_pct / 100) / 12
       emi = principal * r * (1+r)**months / ((1+r)**months - 1)
       return round(emi)
   
   # Compute for tenures: 12, 24, 36 months
   # Default rate bands: 12%-16% based on DTI
   ```

3. **DTI Risk Banding (Gap 3 — NBFC Pre-Underwriting):**
   ```python
   if income and existing_emis:
       dti = (existing_emis + proposed_emi) / monthly_income * 100
       if   dti < 30:  risk = "Low";      rate = "12-13%"; cta = "Aap eligible hain — Apply Now"
       elif dti < 40:  risk = "Medium";   rate = "13-15%"; cta = "Proceed with Standard Application"
       elif dti < 50:  risk = "High";     rate = "15-16%"; cta = "Flag for Manual Review"
       else:           risk = "Critical"; rate = "N/A";    cta = "Recommend Alternate Financing"
   ```

4. **Insurance Cashless Pre-Auth Estimate (Gap 2):**
   ```python
   # Compare hospital tier pricing vs known insurer reimbursement caps
   out_of_pocket = max(0, procedure_cost_min - insurer_cap_for_tier)
   cashless_likely = procedure_cost_min <= insurer_cap_for_tier
   ```

5. **Government Scheme Eligibility:**
   ```python
   SCHEMES = [
       { "name": "Ayushman Bharat PM-JAY", "coverage": "Up to Rs 5L/year",
         "url": "https://pmjay.gov.in", "eligibility": "BPL/low-income families" },
       { "name": "National Health Authority", "url": "https://nhp.gov.in" },
       { "name": "State Health Scheme Portal", "url": "https://cghs.gov.in" }
   ]
   ```

6. **Lending Partners (static config — only indicative):**
   ```python
   LENDERS = [
       { "name": "Tata Capital Health Loan",    "range": "Rs 50K - Rs 5L",  "tat": "24-72 hrs"   },
       { "name": "Bajaj Finserv Health EMI",     "range": "Rs 30K - Rs 7L",  "tat": "Same day"    },
       { "name": "HDFC Bank Medical Loan",       "range": "Rs 1L - Rs 10L",  "tat": "1-3 days"    }
   ]
   ```

**Output:**
```json
{
  "agent": "financial_engine",
  "total_cost_range": { "min": 138000, "max": 242000 },
  "typical_range":    { "min": 149040, "max": 212960 },
  "tier_cost_comparison": {
    "budget":   { "min": 80000,  "max": 140000 },
    "mid_tier": { "min": 120000, "max": 220000 },
    "premium":  { "min": 250000, "max": 450000 }
  },
  "emi_calculator": {
    "loan_amount": 160000,
    "tenure_months": 24,
    "annual_rate_pct": 12.5,
    "monthly_emi": 9461,
    "total_repayment": 227075
  },
  "dti_assessment": null,
  "government_schemes": [...],
  "lending_partners": [...],
  "cost_breakdown_items": [
    { "label": "Pre-op assessment",      "min": 3000,  "max": 8000   },
    { "label": "Implant selection",      "min": 20000, "max": 60000  },
    { "label": "Surgery",                "min": 80000, "max": 120000 },
    { "label": "Hospital recovery",      "min": 30000, "max": 60000  },
    { "label": "Physiotherapy",          "min": 5000,  "max": 15000  }
  ],
  "comorbidity_surcharges": [
    { "condition": "diabetes",        "add_min": 10000, "add_max": 30000  },
    { "condition": "cardiac history", "add_min": 40000, "add_max": 150000 }
  ]
}
```

**Frontend Binding:**
- **"Estimated Cost" card:** Render `total_cost_range`, `typical_range`, `cost_confidence`, `geo_adjustment_note`
- **"Compare cost by hospital tier"** table: `tier_cost_comparison`
- **"EMI Calculator"** interactive widget: slider inputs write back to this agent; `monthly_emi` and `total_repayment` update in real-time
- **"Financial Assistance Guide":** `government_schemes` + `lending_partners`
- **"View Cost Breakdown"** modal: `cost_breakdown_items` as itemized list
- **"What may increase cost?"** section: `comorbidity_surcharges`
- **"Export Estimate (TXT)"** button: serialize `emi_calculator` + `cost_breakdown_items` to plain text

---

### AGENT 5 — Geo-Spatial Agent

**Responsibility:** Resolve user location strings to coordinates. Geocode hospital addresses. Feed Leaflet.js map. (Integrated into Gap spatial intelligence)

**Triggered by:** Any location input (chat mention of city, "Add Location" chip click, map interaction).

**Input:**
```json
{ "location_string": "Nagpur" }
```

**Processing:**
```python
from geopy.geocoders import GoogleV3, Nominatim

geolocator = GoogleV3(api_key=GOOGLE_MAPS_KEY)
location = geolocator.geocode("Nagpur, Maharashtra, India")
coords = { "lat": location.latitude, "lng": location.longitude,
           "city": "Nagpur", "state": "Maharashtra", "tier": 2 }
```

**Output to Frontend (Map Tab):**
```json
{
  "agent": "geo_spatial",
  "user_coords": { "lat": 21.1458, "lng": 79.0882 },
  "city_tier": 2,
  "hospital_markers": [
    { "id": "hosp_001", "lat": 21.155, "lng": 79.091,
      "name": "ABC Heart & Ortho Institute", "tier": "mid-tier",
      "color": "#6B7CFF", "cost_label": "Rs 1.4L – Rs 2.2L" }
  ],
  "map_config": {
    "center": [21.1458, 79.0882],
    "zoom": 13,
    "tile_layer": "OpenStreetMap",
    "legend": {
      "Premium": "#3B82F6",
      "Mid-range": "#8B5CF6",
      "Budget": "#10B981"
    }
  }
}
```

**Frontend Binding:**
- The **Map tab** (`List | Map` toggle) renders using this output
- Clicking a hospital marker fires a callback that loads that hospital's full detail into the comparison pane
- Legend overlay colors match `map_config.legend`

---

### AGENT 6 — XAI Explainer Agent

**Responsibility:** Generate SHAP waterfall explanations for hospital fusion scores and LIME explanations for triage classifications. Produce the confidence score displayed throughout the UI.

**Triggered by:** After Hospital Discovery Agent completes, for the top-ranked hospital. Also triggered on any RED triage classification.

**Processing:**

```python
import shap

# SHAP for Fusion Score explanation
explainer = shap.TreeExplainer(fusion_model)
shap_values = explainer.shap_values(hospital_feature_vector)

shap_explanation = {
    "clinical_score":      { "value": 0.88, "shap": +0.120 },
    "reputation_score":    { "value": 0.75, "shap": +0.078 },
    "accessibility_score": { "value": 0.90, "shap": +0.095 },
    "affordability_score": { "value": 0.85, "shap": -0.020 }
}

# LIME for triage text classification
from lime.lime_text import LimeTextExplainer
lime_explainer = LimeTextExplainer(class_names=["GREEN","YELLOW","RED"])
lime_exp = lime_explainer.explain_instance(user_query, triage_classifier.predict_proba)
highlighted_tokens = lime_exp.as_list()
```

**RAG Confidence Scoring:**
```python
# Three-metric composite (DeepEval / EvidentlyAI methodology)
S = (0.4 * faithfulness_score +
     0.3 * contextual_relevancy_score +
     0.3 * answer_relevancy_score)

if S < CONFIDENCE_THRESHOLD:  # e.g. 0.60
    show_uncertainty_banner = True
    disclaimer = "This system provides decision support only and does not constitute medical advice or diagnosis."
```

**Output:**
```json
{
  "agent": "xai_explainer",
  "confidence_score": 74,
  "confidence_drivers": {
    "data_availability": 82,
    "pricing_consistency": 76,
    "benchmark_recency": 71,
    "patient_complexity": 68
  },
  "top_hospital_shap": {
    "hospital_id": "hosp_001",
    "contributors": [
      { "factor": "High Clinical Score",      "impact": "positive", "delta": "+0.120" },
      { "factor": "Excellent Accessibility",  "impact": "positive", "delta": "+0.095" },
      { "factor": "Affordability Slightly Low","impact": "negative","delta": "-0.020" }
    ]
  },
  "triage_lime": null,
  "show_uncertainty_banner": false,
  "disclaimer": "Symptom-to-condition mapping is approximate. This tool helps you research and prepare; your doctor makes the diagnosis."
}
```

**Frontend Binding:**
- **Confidence badge** on Clinical Interpretation card = `confidence_score`%
- **"Confidence drivers"** sub-section = render 4 progress bars from `confidence_drivers`
- **Disclaimer text** below Clinical Interpretation = `disclaimer`
- **"Correct this interpretation"** link = triggers a feedback POST to backend flagging the mapping as incorrect
- **SHAP waterfall** in "View Details" hospital modal = `top_hospital_shap.contributors`

---

### AGENT 7 — Appointment & Paperwork Agent

**Responsibility:** Generate procedure-specific appointment checklists, common form templates, questions to ask the doctor, and process appointment requests stored in the session. (Gap 4)

**Triggered by:** User clicks "Ask AI for More Help", downloads checklist, or clicks "View Details" on a hospital.

**LLM Prompt for Checklist:**
```
SYSTEM: You are a healthcare preparation assistant. For a patient undergoing
{canonical_procedure} at a {tier} hospital in India, generate:
1. A document checklist (5-7 items, India-specific)
2. Three questions the patient should ask their doctor
3. Three common forms they may need to fill

Output ONLY valid JSON:
{
  "documents": [...],
  "questions": [...],
  "forms": [{"name": "...", "generate_url": "..."}]
}
```

**Appointment Request Schema (stored in session):**
```json
{
  "doctor_name": "Dr. Harsh Kulkarni",
  "hospital_name": "ABC Heart & Ortho Institute",
  "date": "Fri, 17 Apr",
  "time": "12:30 PM",
  "status": "requested",  // "requested" | "confirmed" | "cancelled"
  "procedure": "Total Knee Arthroplasty (TKA)"
}
```

**Frontend Binding:**
- **Sidebar "My Appointment Requests"** card = renders `appointment_requests` from session
- Sidebar badge count = `appointment_requests.filter(s => s.status === "requested").length`
- **"Mark Confirmed"** / **"Cancel"** / **"Remove"** buttons mutate the session appointment object
- **"Download Checklist"** button serializes the checklist to PDF or TXT

---

## 4. Master Orchestrator Agent

The **Master Orchestrator** is the central LangChain agent that receives every user message, routes to sub-agents, assembles responses, and formats them for the dual-panel frontend (Chat Panel + Results Panel).

### 4.1 Intent Classification

```python
INTENTS = {
    "HOSPITAL_SEARCH":    ["find hospital", "near", "best hospital", "recommend"],
    "COST_ESTIMATE":      ["cost", "price", "how much", "budget", "afford", "lakh"],
    "PROCEDURE_INFO":     ["what is", "explain", "how does", "angioplasty", "arthroplasty"],
    "FINANCIAL_HELP":     ["loan", "EMI", "insurance", "scheme", "Ayushman"],
    "APPOINTMENT":        ["appointment", "book", "schedule", "Dr."],
    "COMORBIDITY_QUERY":  ["diabetes", "affect", "cardiac", "safe", "risk"],
    "TRIAGE_EMERGENCY":   ["chest pain", "radiating", "can't breathe", "unconscious"]
}
```

### 4.2 Agent Routing Logic

```python
def route(intent, session):
    if intent == "TRIAGE_EMERGENCY":
        return [NERTriageAgent(triage_mode="emergency")]

    if intent in ["HOSPITAL_SEARCH", "COST_ESTIMATE"]:
        return [
            NERTriageAgent(),
            ClinicalPathwayAgent(),
            HospitalDiscoveryAgent(),
            FinancialEngineAgent(),
            GeoSpatialAgent(),
            XAIExplainerAgent()
        ]

    if intent == "PROCEDURE_INFO":
        return [NERTriageAgent(), ClinicalPathwayAgent()]

    if intent == "FINANCIAL_HELP":
        return [FinancialEngineAgent()]

    if intent == "APPOINTMENT":
        return [AppointmentPaperworkAgent()]
```

### 4.3 Master Response Schema

The orchestrator assembles a **single JSON response** sent to the frontend. The frontend splits it into the Chat Panel (left) and Results Panel (right).

```json
{
  "chat_response": {
    "message": "I interpreted your query as **Total Knee Arthroplasty (TKA)** and found **3 hospitals** in Nagpur.\n\nEstimated range: **Rs 1,38,000 – Rs 2,42,000** with confidence **74%**.\n\nDecision support only. Please consult a qualified doctor before making medical decisions.",
    "timestamp": "12:55 pm",
    "triage_level": "GREEN",
    "offline_mode": false
  },
  "results_panel": {
    "visible": true,
    "active_tab": "list",
    "clinical_interpretation": { /* NER Agent output */ },
    "pathway": { /* Clinical Pathway Agent output */ },
    "cost_estimate": { /* Financial Engine Agent output */ },
    "hospitals": [ /* Hospital Discovery Agent output */ ],
    "map_data": { /* Geo-Spatial Agent output */ },
    "xai": { /* XAI Explainer Agent output */ },
    "checklist": { /* Appointment Agent output */ },
    "financial_assistance": { /* Financial Engine schemes + lenders */ }
  },
  "session_updates": {
    "last_procedure": "Total Knee Arthroplasty (TKA)",
    "history_entry": "Knee replacement near Nagpur | 12:55 pm"
  }
}
```

### 4.4 Offline Fallback Mode

When the LLM API is unavailable, the system switches to offline static data mode:

```python
OFFLINE_FLAG = "*(Using offline data – backend LLM service unavailable)*"

# Use pre-computed procedure → hospital mappings from a JSON cache
# Display the OFFLINE_FLAG string in the chat bubble
# Confidence scores are capped at 70% in offline mode
```

---

## 5. Frontend ↔ Agent Data Binding Reference

This table maps every visible UI element on [https://tenzor-x.vercel.app/](https://tenzor-x.vercel.app/) to its agent source.

| UI Element | Location | Agent | Field |
|---|---|---|---|
| Suggested query chips | Homepage center | Static config | `homepage_suggestions[]` |
| Chat message bubble (assistant) | Chat panel | Master Orchestrator | `chat_response.message` |
| Offline warning text | Chat bubble | Master Orchestrator | `chat_response.offline_mode` → `OFFLINE_FLAG` |
| "Add Location" chip | Bottom bar | Geo-Spatial Agent | Sets `session.user_location` |
| "Patient Details" chip | Bottom bar | NER Triage Agent | Sets `session.patient_profile` |
| "Set Budget" chip | Bottom bar | Financial Engine | Sets `session.patient_profile.budget_inr` |
| City tag (Nagpur, MH) | Top nav | Geo-Spatial Agent | `session.user_location.city` |
| History sidebar items | Left sidebar | Session Manager | `session.conversation_history` |
| Saved Results sidebar | Left sidebar | Session Manager | `session.saved_results` |
| Appointment Requests sidebar | Left sidebar | Appointment Agent | `session.appointment_requests` |
| Badge count on Appointments | Left sidebar | Appointment Agent | Count of `status=requested` |
| Mark Confirmed / Cancel | Sidebar card | Appointment Agent | Mutates appointment `status` |
| Results count ("3 results") | Results header | Hospital Discovery | `result_count` |
| List / Map toggle | Results header | Geo-Spatial Agent | Switches `active_tab` |
| Expand / Collapse button | Results header | Frontend state | UI only |
| Sort dropdown | Results filter bar | Hospital Discovery | Re-sort `hospitals[]` by field |
| Distance filter | Results filter bar | Geo-Spatial Agent | Filter by `distance_km` |
| Rating filter | Results filter bar | Hospital Discovery | Filter by `rating` |
| Tier filter chips | Results filter bar | Hospital Discovery | Filter by `tier` |
| NABH Only filter | Results filter bar | Hospital Discovery | Filter by `nabh=true` |
| Mapping Confidence % | Clinical Interpretation | NER Triage Agent | `mapping_confidence` |
| Procedure name | Clinical Interpretation | NER Triage Agent | `canonical_procedure` |
| Category | Clinical Interpretation | NER Triage Agent | `category` |
| ICD-10 code | Clinical Interpretation | NER Triage Agent | `icd10` |
| SNOMED CT code | Clinical Interpretation | NER Triage Agent | `snomed_ct` |
| Typical Pathway steps | Clinical Interpretation | Clinical Pathway Agent | `pathway_steps[]` |
| "Correct this interpretation" | Clinical Interpretation | Feedback endpoint | POST `/api/feedback` |
| Cost total range | Cost Estimate card | Financial Engine | `total_cost_range` |
| Typical cost range | Cost Estimate card | Financial Engine | `typical_range` |
| Cost confidence badge | Cost Estimate card | XAI Explainer | `confidence_score` |
| Tier cost comparison table | Cost Estimate card | Financial Engine | `tier_cost_comparison` |
| Confidence drivers bars | Cost Estimate card | XAI Explainer | `confidence_drivers` |
| Geo adjustment note | Cost Estimate card | Clinical Pathway Agent | `geo_adjustment_note` |
| "View Cost Breakdown" | Cost Estimate card | Financial Engine | `cost_breakdown_items[]` |
| Comorbidity impacts | Cost Estimate card | Financial Engine | `comorbidity_surcharges[]` |
| "What may increase cost?" | Cost Estimate card | Financial Engine | `comorbidity_surcharges[]` |
| "Export Estimate (TXT)" | Cost Estimate card | Financial Engine | Serialize `emi_calculator` + breakdown |
| Hospital card name | Hospital list | Hospital Discovery | `hospitals[i].name` |
| Hospital card address | Hospital list | Hospital Discovery | `hospitals[i].address` |
| Hospital rating stars | Hospital list | Hospital Discovery | `hospitals[i].rating` |
| NABH badge | Hospital card | Hospital Discovery | `hospitals[i].nabh` |
| Tier badge | Hospital card | Hospital Discovery | `hospitals[i].tier` |
| Distance badge | Hospital card | Geo-Spatial Agent | `hospitals[i].distance_km` |
| Hospital cost range | Hospital card | Financial Engine | `hospitals[i].cost_min / cost_max` |
| Hospital confidence badge | Hospital card | XAI Explainer | `hospitals[i].cost_confidence` |
| Hospital tags | Hospital card | Hospital Discovery | `hospitals[i].tags[]` |
| "View Details" button | Hospital card | All agents | Opens full detail modal |
| "Compare" button | Hospital card | Hospital Discovery | Side-by-side comparison (Gap 8) |
| Leaflet map | Map tab | Geo-Spatial Agent | `map_data.hospital_markers[]` |
| Map legend | Map tab | Geo-Spatial Agent | `map_config.legend` |
| Colored map markers | Map tab | Geo-Spatial Agent | `marker.color` by `tier` |
| Document checklist | Checklist section | Appointment Agent | `checklist.documents[]` |
| Doctor questions | Checklist section | Appointment Agent | `checklist.questions[]` |
| Form generate buttons | Checklist section | Appointment Agent | `checklist.forms[]` |
| "Download Checklist" button | Checklist section | Appointment Agent | Serialize to PDF/TXT |
| Govt scheme links | Financial Assistance | Financial Engine | `government_schemes[]` |
| Lending partner rows | Financial Assistance | Financial Engine | `lending_partners[]` |
| EMI slider (amount) | EMI Calculator | Financial Engine | Input → recalculate EMI |
| EMI slider (rate) | EMI Calculator | Financial Engine | Input → recalculate EMI |
| EMI tenure slider | EMI Calculator | Financial Engine | Input → recalculate EMI |
| "Estimated monthly EMI" | EMI Calculator | Financial Engine | `emi_calculator.monthly_emi` |
| "Total repayment" | EMI Calculator | Financial Engine | `emi_calculator.total_repayment` |
| Data source credits | Bottom of results | Static config | `data_sources[]` |

---

## 6. API Endpoint Specification

All endpoints are served from the Python FastAPI backend.

### `POST /api/chat`
Main entry point. Receives user message, runs the full agent pipeline.

**Request:**
```json
{
  "message": "Knee replacement near Nagpur under Rs 2 lakh",
  "session_id": "abc-123",
  "patient_profile": { "comorbidities": ["diabetes", "cardiac history"] }
}
```

**Response:** Master Orchestrator output schema (Section 4.3)

---

### `GET /api/session/{session_id}`
Returns current session state (for frontend hydration on refresh).

---

### `PATCH /api/session/{session_id}/appointment`
Updates an appointment request status.

**Request:**
```json
{ "appointment_id": "appt_001", "status": "confirmed" }
```

---

### `POST /api/emi-calculate`
Real-time EMI recalculation (called by frontend sliders without going through LLM).

**Request:**
```json
{ "principal": 200000, "annual_rate_pct": 12.5, "tenure_months": 24 }
```

**Response:**
```json
{ "monthly_emi": 9461, "total_repayment": 227075 }
```

---

### `POST /api/feedback`
Captures "Correct this interpretation" submissions.

**Request:**
```json
{
  "session_id": "abc-123",
  "original_query": "Knee replacement near Nagpur",
  "mapped_procedure": "Total Knee Arthroplasty (TKA)",
  "user_correction": "Actually I meant partial knee replacement"
}
```

---

### `POST /api/save-result`
Saves the current result set to the session's `saved_results`.

---

### `GET /api/form-template/{form_name}`
Returns a pre-filled PDF form template for download.
`form_name` one of: `patient_registration`, `medical_history_declaration`, `consent_for_surgery`

---

## 7. Lender / Insurer Mode

A separate dashboard view for B2B users (lenders and insurers). Activated from the sidebar "Lender / Insurer Mode" toggle.

**Features (subset of agents, different UI layout):**
- Financial Engine Agent → DTI assessment table (full risk band matrix)
- Hospital Discovery Agent → Pricing tier distribution for a procedure + geography
- XAI Explainer → SHAP feature attribution for pre-authorization decisions
- No appointment / checklist features

**API endpoint:** `POST /api/lender/underwrite`
```json
{
  "procedure": "Total Knee Arthroplasty (TKA)",
  "city": "Nagpur",
  "patient_income_monthly": 50000,
  "existing_emis": 5000,
  "loan_amount_requested": 160000,
  "tenure_months": 24
}
```

---

## 8. Data Sources & Update Cadence

| Source | Data Type | Update Frequency | Agent Consumer |
|---|---|---|---|
| NHA Procedure Benchmark Categories | Procedure costs | Quarterly | Clinical Pathway Agent |
| Public Hospital Directories | Hospital metadata | Monthly | Hospital Discovery Agent |
| NABH Accreditation Registry | Accreditation status | Monthly | Hospital Discovery Agent |
| ICD-10-CM JSON (smog1210/GitHub) | Medical ontology | Annually | NER Triage Agent |
| SNOMED CT API | Medical ontology | Quarterly | NER Triage Agent |
| Google Maps / Healthcare Forums | Patient reviews | Weekly (scraped) | ABSA Sentiment pipeline |
| Kearney India Healthcare Index | Geo pricing multipliers | Annually | Clinical Pathway Agent |
| Ayushman Bharat PM-JAY | Scheme eligibility | Quarterly | Financial Engine Agent |

---

## 9. Gap Resolution Checklist

| Gap # | Description | Resolving Agent(s) | Status |
|---|---|---|---|
| Gap 1 | Patient review quality signal | Hospital Discovery (ABSA pipeline) | ✅ |
| Gap 2 | Insurance cashless transparency | Financial Engine (insurer pre-auth) | ✅ |
| Gap 3 | NBFC loan pre-underwriting | Financial Engine (DTI engine) | ✅ |
| Gap 4 | Appointment availability | Hospital Discovery (proxy logic) + Appointment Agent | ✅ |
| Gap 5 | Geographic pricing adjustment | Clinical Pathway Agent (γ_geo multiplier) | ✅ |
| Gap 6 | Age + comorbidity cost adjustment | Clinical Pathway Agent (Σ ωᵢCᵢ formula) | ✅ |
| Gap 7 | Multi-source fusion ranking | Hospital Discovery (4-dimension fusion score) | ✅ |
| Gap 8 | Side-by-side hospital comparison | Hospital Discovery + Frontend (Compare button) | ✅ |
| Gap 9 | Treatment pathway explanation | Clinical Pathway Agent (sequential phase matrix) | ✅ |

---

## 10. Safety, Ethics & Disclaimers

### Mandatory Disclaimers (must appear in every session)
1. **Global banner (top of page):** `"HealthNav provides decision support only, not medical advice. Always consult a qualified doctor before making health decisions."`
2. **Below Clinical Interpretation:** `"Symptom-to-condition mapping is approximate. The same symptoms may indicate different conditions. This tool helps you research and prepare; your doctor makes the diagnosis."`
3. **In every chat response:** `"Decision support only. Please consult a qualified doctor before making medical decisions."`
4. **On EMI Calculator:** `"These are indicative figures. Confirm final rates with lenders."`
5. **On all cost estimates:** Include confidence score + note that estimates vary by individual clinical factors.

### Triage Override Rules
- If NER Triage Agent returns `triage = "RED"`: immediately display emergency contact numbers and disable budget/geo filtering
- The LIME explanation for RED triage must highlight the triggering phrase in the UI

### Confidence Threshold Enforcement
- If `xai_explainer.confidence_score < 60`: Display yellow uncertainty banner in Results panel
- If `xai_explainer.confidence_score < 40`: Block results display; show "Insufficient data for this query. Please refine your search."

---

## 11. Environment Variables

```env
# LLM
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=1000

# Knowledge Graph
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# Geocoding
GOOGLE_MAPS_API_KEY=...
NOMINATIM_USER_AGENT=healthnav-india

# Vector Embeddings
OPENAI_API_KEY=sk-...   # for text-embedding-3-small

# Session Store (production)
REDIS_URL=redis://...

# Feature Flags
OFFLINE_FALLBACK_ENABLED=true
CONFIDENCE_THRESHOLD_WARN=60
CONFIDENCE_THRESHOLD_BLOCK=40
```

---

## 12. Deployment Notes

- **Frontend:** Vercel (Next.js) at `https://tenzor-x.vercel.app/`
- **Backend:** FastAPI on Railway / Render / AWS Lambda — must be reachable at `NEXT_PUBLIC_API_URL`
- **Neo4j:** AuraDB free tier for dev; AuraDB Enterprise for production
- **CORS:** Backend must allow `https://tenzor-x.vercel.app` as origin
- **WebSocket:** For streaming LLM responses (chat typing indicator), use `/ws/chat/{session_id}`
- **Rate Limiting:** 10 req/min per session_id on `/api/chat` to prevent abuse

---

*Last updated: May 2026 · HealthNav India · Architecture v1.0*
