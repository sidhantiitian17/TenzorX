# HealthNav — Backend ↔ Frontend Verification Manual

> **Frontend:** https://tenzor-x.vercel.app/  
> **Architecture Source:** `Healthcare_AI_Solution_Strategy.pdf` + `instructionagent.md`  
> **Purpose:** Step-by-step checklist to confirm every UI element is receiving real data from the backend agents and API routes — zero hardcoded/mocked data in production.

---

## Table of Contents

1. [Pre-Flight Environment Checks](#1-pre-flight-environment-checks)
2. [API Endpoint Smoke Tests](#2-api-endpoint-smoke-tests)
3. [Agent Pipeline Verification](#3-agent-pipeline-verification)
4. [Frontend Component → Backend Binding Map](#4-frontend-component--backend-binding-map)
5. [LLM Integration Tests](#5-llm-integration-tests)
6. [WebSocket Streaming Test](#6-websocket-streaming-test)
7. [Session & Memory Continuity Tests](#7-session--memory-continuity-tests)
8. [Financial Engine Verification](#8-financial-engine-verification)
9. [Geo-Spatial Agent Verification](#9-geo-spatial-agent-verification)
10. [XAI Explainer Verification](#10-xai-explainer-verification)
11. [Appointment Agent Verification](#11-appointment-agent-verification)
12. [Lender / Insurer Mode Verification](#12-lender--insurer-mode-verification)
13. [Safety & Disclaimer Verification](#13-safety--disclaimer-verification)
14. [Regression Test Matrix](#14-regression-test-matrix)
15. [Common Failure Modes & Fixes](#15-common-failure-modes--fixes)

---

## 1. Pre-Flight Environment Checks

Before running any functional tests, confirm all infrastructure is live and variables are set.

### 1.1 Environment Variables

Verify that all required environment variables are present in the backend deployment (Railway / Render / AWS Lambda):

```bash
# Run on the backend server (or check deployment dashboard)
echo $ANTHROPIC_API_KEY          # Must start with sk-ant-
echo $LLM_MODEL                  # Must be: claude-sonnet-4-20250514
echo $LLM_MAX_TOKENS             # Must be: 1000
echo $NEO4J_URI                  # Must be: bolt://... or neo4j+s://...
echo $NEO4J_USER                 # Must be: neo4j
echo $NEO4J_PASSWORD             # Must be non-empty
echo $GOOGLE_MAPS_API_KEY        # Must be non-empty
echo $NOMINATIM_USER_AGENT       # Must be: healthnav-india
echo $OPENAI_API_KEY             # Must start with sk- (for embeddings)
echo $REDIS_URL                  # Must be: redis://... (production)
echo $OFFLINE_FALLBACK_ENABLED   # Must be: true
echo $CONFIDENCE_THRESHOLD_WARN  # Must be: 60
echo $CONFIDENCE_THRESHOLD_BLOCK # Must be: 40
```

**Expected result:** All variables print non-empty values. Any empty variable = deployment is broken.

### 1.2 CORS Configuration

The backend MUST list `https://tenzor-x.vercel.app` as an allowed origin in `main.py`:

```python
# Verify in Backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tenzor-x.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Test:** Open browser DevTools → Network tab on `https://tenzor-x.vercel.app/` → make a chat request → inspect Response Headers for:
```
Access-Control-Allow-Origin: https://tenzor-x.vercel.app
```
**Failure sign:** Any `CORS` error in browser console = frontend cannot receive backend data.

### 1.3 Backend Health Check

```bash
curl -X GET https://<YOUR_BACKEND_URL>/health
# Expected: {"status": "ok", "version": "1.0", "llm": "claude-sonnet-4-20250514"}
```

### 1.4 Neo4j Connectivity

```bash
# From the backend server
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('$NEO4J_URI', auth=('$NEO4J_USER', '$NEO4J_PASSWORD'))
driver.verify_connectivity()
print('Neo4j: OK')
"
# Expected: Neo4j: OK
```

### 1.5 Frontend API URL Binding

In the Next.js frontend code, confirm `NEXT_PUBLIC_API_URL` points to the live backend:

```bash
# In Vercel dashboard → Settings → Environment Variables
NEXT_PUBLIC_API_URL=https://<YOUR_BACKEND_URL>
```

**Test:** Open browser console on `https://tenzor-x.vercel.app/` and run:
```javascript
console.log(process.env.NEXT_PUBLIC_API_URL)
// Must NOT be undefined or localhost
```

---

## 2. API Endpoint Smoke Tests

Run these `curl` commands against your live backend. Replace `<BACKEND_URL>` throughout.

### 2.1 POST /api/chat — Master Entry Point

**File:** `Backend/app/agents/master_orchestrator.py` + all routes

```bash
curl -X POST https://<BACKEND_URL>/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Knee replacement near Nagpur under Rs 2 lakh",
    "session_id": "test-session-001",
    "patient_profile": { "comorbidities": ["diabetes"] }
  }'
```

**Expected Response Shape (from `Backend/app/schemas/response_models.py`):**
```json
{
  "session_id": "test-session-001",
  "chat_response": {
    "message": "...",
    "triage": "GREEN",
    "confidence_score": 82,
    "disclaimer": "Decision support only. Please consult a qualified doctor..."
  },
  "clinical_interpretation": {
    "canonical_procedure": "Total Knee Arthroplasty (TKA)",
    "category": "Orthopedic Surgery",
    "icd10": "M17.11 — Primary osteoarthritis, right knee",
    "snomed_ct": "179344001",
    "mapping_confidence": 86
  },
  "treatment_pathway": { ... },
  "cost_estimate": { ... },
  "hospitals": [ ... ],
  "map_data": { ... },
  "financial_assistance": { ... },
  "appointment_checklist": { ... },
  "xai_explanation": { ... }
}
```

**Failure signs:**
- `500 Internal Server Error` → Agent crash; check backend logs
- `{"detail": "..."}` FastAPI validation error → Schema mismatch
- Response missing `clinical_interpretation` → NER Agent not connected
- Response missing `hospitals` → Hospital Discovery Agent not connected
- Response with empty `map_data` → Geo-Spatial Agent not connected

---

### 2.2 GET /api/session/{session_id}

**File:** `Backend/app/api/routes/session.py`

```bash
curl -X GET https://<BACKEND_URL>/api/session/test-session-001
```

**Expected:**
```json
{
  "session_id": "test-session-001",
  "user_location": { "city": "Nagpur", "state": "MH", "lat": 21.14, "lng": 79.08 },
  "patient_profile": { "comorbidities": ["diabetes"], "budget_inr": 200000 },
  "conversation_history": [ ... ],
  "saved_results": [],
  "appointment_requests": []
}
```

**Frontend Binding:** Sidebar badge for "My Appointment Requests" = `len(appointment_requests)`. If this endpoint returns `404` or empty data after a chat, the sidebar will always show 0 appointments even after booking.

---

### 2.3 PATCH /api/session/{session_id}/appointment

**File:** `Backend/app/api/routes/session.py`

```bash
curl -X PATCH https://<BACKEND_URL>/api/session/test-session-001/appointment \
  -H "Content-Type: application/json" \
  -d '{"appointment_id": "appt_001", "status": "confirmed"}'
```

**Expected:** `{"status": "updated", "appointment_id": "appt_001"}`

**Failure sign:** If PATCH returns `405 Method Not Allowed`, the route is defined as POST — fix in `session.py`.

---

### 2.4 POST /api/emi-calculate

**File:** `Backend/app/api/routes/emi.py`

```bash
curl -X POST https://<BACKEND_URL>/api/emi-calculate \
  -H "Content-Type: application/json" \
  -d '{"principal": 200000, "annual_rate_pct": 12.5, "tenure_months": 24}'
```

**Expected:**
```json
{"monthly_emi": 9461, "total_repayment": 227075}
```

**Manual Verification Formula:**
```
monthly_rate = 12.5 / 100 / 12 = 0.010417
EMI = 200000 * 0.010417 * (1.010417^24) / ((1.010417^24) - 1)
    ≈ 9,461 ✅
total = 9461 * 24 = 227,064 (allow ±50 for rounding)
```

**Frontend Binding:** "Estimated monthly EMI" and "Total repayment" fields in the EMI Calculator section. If this endpoint is broken, sliders will show stale or zero values.

---

### 2.5 POST /api/feedback

**File:** `Backend/app/api/routes/feedback.py`

```bash
curl -X POST https://<BACKEND_URL>/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-001",
    "original_query": "Knee replacement near Nagpur",
    "mapped_procedure": "Total Knee Arthroplasty (TKA)",
    "user_correction": "Actually I meant partial knee replacement"
  }'
```

**Expected:** `{"status": "received", "feedback_id": "fb_..."}`

**Frontend Binding:** "Correct this interpretation" link below the Clinical Interpretation card. A `500` here silently fails — add a visible toast notification on the frontend.

---

### 2.6 POST /api/save-result

**File:** `Backend/app/api/routes/save_result.py`

```bash
curl -X POST https://<BACKEND_URL>/api/save-result \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-001", "result_snapshot": {"procedure": "TKA", "city": "Nagpur"}}'
```

**Expected:** `{"status": "saved", "saved_id": "sv_..."}`

**Frontend Binding:** "Saved Results" sidebar section. After saving, immediately call `GET /api/session/{session_id}` and verify `saved_results` array is non-empty.

---

### 2.7 GET /api/form-template/{form_name}

**File:** `Backend/app/api/routes/form_template.py`

Test all three form types:

```bash
curl -O https://<BACKEND_URL>/api/form-template/patient_registration
curl -O https://<BACKEND_URL>/api/form-template/medical_history_declaration
curl -O https://<BACKEND_URL>/api/form-template/consent_for_surgery
```

**Expected:** Each returns a downloadable PDF file.  
**Check:** `Content-Type: application/pdf` in response headers.  
**Frontend Binding:** "Generate Form" buttons in the Appointment Checklist section. If the route returns `404`, the buttons will trigger broken download links.

---

### 2.8 POST /api/lender/underwrite

**File:** `Backend/app/api/routes/lender.py`

```bash
curl -X POST https://<BACKEND_URL>/api/lender/underwrite \
  -H "Content-Type: application/json" \
  -d '{
    "procedure": "Total Knee Arthroplasty (TKA)",
    "city": "Nagpur",
    "patient_income_monthly": 50000,
    "existing_emis": 5000,
    "loan_amount_requested": 160000,
    "tenure_months": 24
  }'
```

**Expected:**
```json
{
  "dti_ratio": 23.9,
  "risk_flag": "Low Risk",
  "underwriting_assessment": "Strong repayment capacity; very high approval likelihood.",
  "estimated_interest_rate_band": "12% - 13%",
  "call_to_action": "Aap eligible hain — Apply Now",
  "emi_breakdown": { "12_months": 14222, "24_months": 7555, "36_months": 5329 },
  "shap_explanation": { ... }
}
```

**DTI Manual Check:**
```
proposed_emi = 160000 * (12.5/1200) * (1+12.5/1200)^24 / ((1+12.5/1200)^24-1) ≈ 7,569
DTI = (5000 + 7569) / 50000 * 100 ≈ 25.1% → Low Risk ✅
```

---

### 2.9 WebSocket /ws/chat/{session_id}

**File:** `Backend/app/api/routes/websocket.py`

```bash
# Use websocat or a browser WebSocket client
wscat -c wss://<BACKEND_URL>/ws/chat/test-session-001
# Then type:
{"message": "What is angioplasty?"}
# Expected: streaming tokens arriving incrementally as separate JSON frames
```

**Expected frame format:**
```json
{"type": "token", "content": "Angio"}
{"type": "token", "content": "plasty"}
{"type": "done", "full_response": "Angioplasty is..."}
```

**Frontend Binding:** The chat typing indicator / streaming text. Without WebSocket, the frontend must fall back to polling — verify fallback exists.

---

## 3. Agent Pipeline Verification

Each agent must be independently testable. The following tests call the internal agent logic directly (useful in a test environment before the full API is wired up).

### 3.1 NER + Triage Agent

**File:** `Backend/app/agents/__init__.py` → references individual agent modules

```python
# test_ner_agent.py
from app.agents.master_orchestrator import run_ner_triage

result = run_ner_triage(
    raw_query="severe chest pain radiating to left arm",
    session_id="test-001",
    patient_profile={}
)

assert result["triage"] == "RED", f"Expected RED triage, got {result['triage']}"
assert "canonical_procedure" in result
assert result["icd10"].startswith("I")   # Cardiac ICD-10 codes start with I
print("NER Triage Agent: PASS ✅")
```

**Additional triage tests:**

| Input Query | Expected `triage` | Expected ICD-10 Prefix |
|---|---|---|
| `"knee replacement near Nagpur"` | `GREEN` | `M17` |
| `"difficulty breathing, high fever"` | `YELLOW` | `J` or `R` |
| `"chest pain radiating left arm"` | `RED` | `I20` or `I21` |
| `"diabetes checkup"` | `GREEN` | `E11` |
| `"stroke symptoms, face drooping"` | `RED` | `I63` |

**Failure sign:** If `triage == "RED"` queries return `GREEN`, the safety override is broken — emergency routing will not trigger.

---

### 3.2 Clinical Pathway Agent

**File:** `Backend/app/agents/master_orchestrator.py`

```python
# test_pathway_agent.py
from app.agents.master_orchestrator import run_clinical_pathway

result = run_clinical_pathway(
    canonical_procedure="Total Knee Arthroplasty (TKA)",
    city_tier=2,
    comorbidities=["diabetes"],
    age=55
)

# Verify all phases exist
phases = [p["phase"] for p in result["pathway"]]
assert "Pre-Surgical Evaluation" in phases
assert "Core Surgery" in phases
assert "Post-Operative Recovery" in phases

# Verify comorbidity multiplier is applied (cost > base)
base_cost = 300000  # ₹3L base for Tier 2
assert result["total_estimated_cost"]["max"] > base_cost, \
    "Comorbidity adjustment not applied"

# Verify geographic adjustment for Tier 2
assert result["geo_adjustment_factor"] < 1.0, \
    "Tier 2 factor should be < 1.0 (less than Tier 1)"

print("Clinical Pathway Agent: PASS ✅")
```

**Cost range sanity checks (from PDF research):**

| Procedure | City | Expected Range (₹) |
|---|---|---|
| Angioplasty (drug-eluting stent) | Tier 1 | 1,00,000 – 2,50,000 |
| Angioplasty (drug-eluting stent) | Tier 2 | 85,000 – 2,10,000 |
| Total Knee Replacement | Tier 1 | 2,00,000 – 4,50,000 |
| Total Knee Replacement | Tier 2 | 1,75,000 – 4,00,000 |
| Total Knee Replacement | Tier 3 | 1,50,000 – 3,50,000 |

---

### 3.3 Hospital Discovery Agent (ABSA + Fusion Score)

**File:** `Backend/app/agents/master_orchestrator.py`

```python
# test_hospital_discovery_agent.py
from app.agents.master_orchestrator import run_hospital_discovery

result = run_hospital_discovery(
    canonical_procedure="Total Knee Arthroplasty (TKA)",
    city="Nagpur",
    city_tier=2,
    budget_inr=200000,
    patient_location={"lat": 21.14, "lng": 79.08}
)

hospitals = result["hospitals"]
assert len(hospitals) >= 3, "Must return at least 3 hospitals"

for h in hospitals:
    # Verify fusion score components
    assert 0 <= h["fusion_score"]["clinical"] <= 1
    assert 0 <= h["fusion_score"]["reputation"] <= 1
    assert 0 <= h["fusion_score"]["accessibility"] <= 1
    assert 0 <= h["fusion_score"]["affordability"] <= 1

    # Verify weighted sum
    expected_total = (
        h["fusion_score"]["clinical"] * 0.40 +
        h["fusion_score"]["reputation"] * 0.25 +
        h["fusion_score"]["accessibility"] * 0.20 +
        h["fusion_score"]["affordability"] * 0.15
    )
    assert abs(h["fusion_score"]["total"] - expected_total) < 0.01, \
        f"Fusion score math wrong for {h['name']}"

# Verify sorted by fusion score descending
scores = [h["fusion_score"]["total"] for h in hospitals]
assert scores == sorted(scores, reverse=True), "Hospitals not sorted by score"

# Verify ABSA sentiment scores
for h in hospitals:
    assert "sentiment" in h
    for dimension in ["doctors", "staff", "facilities", "affordability"]:
        assert dimension in h["sentiment"]

print("Hospital Discovery Agent: PASS ✅")
```

---

### 3.4 Financial Engine Agent

**File:** `Backend/app/agents/master_orchestrator.py` + `Backend/app/api/routes/emi.py`

```python
# test_financial_engine.py
from app.agents.master_orchestrator import run_financial_engine

result = run_financial_engine(
    total_cost=200000,
    city="Nagpur",
    patient_profile={
        "monthly_income": 40000,
        "existing_emis": 3000,
        "has_insurance": False,
        "comorbidities": ["diabetes"]
    }
)

# DTI verification
loan_amount = 200000 * 0.80  # 80% of cost
proposed_emi_24m = result["emi_options"]["24_months"]
expected_dti = (3000 + proposed_emi_24m) / 40000 * 100
assert abs(result["dti_ratio"] - expected_dti) < 1.0

# Risk band assignment
if expected_dti < 30:
    assert result["risk_flag"] == "Low Risk"
elif expected_dti < 40:
    assert result["risk_flag"] == "Medium Risk"
elif expected_dti < 50:
    assert result["risk_flag"] == "High Risk"
else:
    assert result["risk_flag"] == "Critical Risk"

# Government schemes present
assert len(result["government_schemes"]) > 0
assert any("Ayushman" in s["name"] for s in result["government_schemes"])

# Lending partners present
assert len(result["lending_partners"]) > 0

print("Financial Engine Agent: PASS ✅")
```

---

### 3.5 Geo-Spatial Agent

**File:** `Backend/app/agents/geo_spatial_agent.py`

```python
# test_geo_spatial_agent.py
from app.agents.geo_spatial_agent import run_geo_spatial

result = run_geo_spatial(
    user_input_location="Nagpur",
    hospitals=[
        {"name": "Hospital A", "lat": 21.15, "lng": 79.09},
        {"name": "Hospital B", "lat": 21.10, "lng": 79.05},
    ]
)

# Geocoding
assert result["user_location"]["lat"] is not None
assert result["user_location"]["city"] == "Nagpur"
assert result["user_location"]["city_tier"] == 2

# Distance calculation
for marker in result["map_data"]["hospital_markers"]:
    assert "distance_km" in marker
    assert marker["distance_km"] > 0

# Map config
assert "center" in result["map_data"]["map_config"]
assert "zoom" in result["map_data"]["map_config"]
assert "legend" in result["map_data"]["map_config"]

# Color coding by tier
for marker in result["map_data"]["hospital_markers"]:
    assert marker["color"] in ["green", "blue", "orange", "red"]

print("Geo-Spatial Agent: PASS ✅")
```

---

### 3.6 XAI Explainer Agent

**File:** `Backend/app/agents/xai_explainer_agent.py`

```python
# test_xai_agent.py
from app.agents.xai_explainer_agent import run_xai_explainer

result = run_xai_explainer(
    top_hospital={
        "name": "Test Hospital",
        "fusion_score": {
            "clinical": 0.88,
            "reputation": 0.75,
            "accessibility": 0.90,
            "affordability": 0.85,
            "total": 0.847
        }
    },
    triage_query="chest pain radiating to left arm",
    triage_result="RED"
)

# SHAP waterfall
shap = result["shap_waterfall"]
assert len(shap["features"]) >= 4  # clinical, reputation, accessibility, affordability
assert all("value" in f and "contribution" in f for f in shap["features"])

# LIME text highlights (only present for non-GREEN triage)
lime = result["lime_highlights"]
assert len(lime["highlighted_tokens"]) > 0
assert any(t["text"] in ["chest pain", "chest", "pain", "left arm"]
           for t in lime["highlighted_tokens"])

# Confidence score
assert 0 <= result["confidence_score"] <= 100

print("XAI Explainer Agent: PASS ✅")
```

---

### 3.7 Appointment Agent

**File:** `Backend/app/agents/appointment_agent.py`

```python
# test_appointment_agent.py
from app.agents.appointment_agent import run_appointment_agent

result = run_appointment_agent(
    canonical_procedure="Total Knee Arthroplasty (TKA)",
    top_hospital={"name": "Test Hospital", "bed_count": 200, "specialists": 3},
    triage="GREEN"
)

# Availability proxy
proxy = result["availability_proxy"]
assert proxy["wait_time_display"] in [
    "Appointments usually available within 2-3 days",
    "Estimated waiting time: 4-7 days",
    "Waiting time: 1-2 weeks",
    "24/7 emergency available ✅"
]

# Checklist
assert len(result["checklist"]["documents"]) > 0
assert len(result["checklist"]["questions"]) > 0
assert len(result["checklist"]["forms"]) > 0

# Form names must match /api/form-template endpoints
valid_forms = {"patient_registration", "medical_history_declaration", "consent_for_surgery"}
for form in result["checklist"]["forms"]:
    assert form["form_id"] in valid_forms

print("Appointment Agent: PASS ✅")
```

---

## 4. Frontend Component → Backend Binding Map

For each visible UI element on `https://tenzor-x.vercel.app/`, verify it is populated from a backend response field and NOT from hardcoded/static data.

### 4.1 Chat Panel

| UI Element | Expected Data Source | Verification Method |
|---|---|---|
| Chat input submit | `POST /api/chat` | Open Network tab, send a message, confirm XHR to `/api/chat` |
| AI response text | `response.chat_response.message` | Inspect response JSON, confirm text matches chat bubble |
| Typing indicator | WebSocket `/ws/chat/{session_id}` | Confirm `token` frames arrive before `done` frame |
| Suggestion chips (e.g. "Knee replacement near Nagpur...") | Static config in frontend (acceptable) | These are examples, not backend-driven — OK |
| Disclaimer below response | `response.chat_response.disclaimer` | Check disclaimer text is from backend schema, not hardcoded |

### 4.2 Results Panel — Clinical Interpretation Section

| UI Element | Backend Field | Test |
|---|---|---|
| "Procedure" label | `clinical_interpretation.canonical_procedure` | Send "knee replacement" → must show "Total Knee Arthroplasty (TKA)" |
| "Category" label | `clinical_interpretation.category` | Must show "Orthopedic Surgery" |
| "ICD-10" code | `clinical_interpretation.icd10` | Must show valid ICD-10 code (e.g. "M17.11") |
| "SNOMED CT" value | `clinical_interpretation.snomed_ct` | Must show numeric SNOMED ID |
| "Mapping Confidence" % bar | `clinical_interpretation.mapping_confidence` | Bar width must match backend value |
| "Correct this interpretation" link | `POST /api/feedback` | Clicking must fire a POST to feedback endpoint |

### 4.3 Results Panel — Treatment Pathway

| UI Element | Backend Field | Test |
|---|---|---|
| Phase cards (Pre, Surgery, Post...) | `treatment_pathway.phases[]` | Verify each phase card corresponds to a backend phase object |
| Phase cost range | `phases[].cost_range.min` / `max` | Values must be in ₹ and within research-validated ranges |
| Phase description | `phases[].description` | Must be LLM-generated, not static string |
| Comorbidity warning tag | `treatment_pathway.comorbidity_note` | Only appears when `patient_profile.comorbidities` is non-empty |
| Total estimated cost | `cost_estimate.total.min` / `max` | Must equal sum of phase ranges + comorbidity multiplier |
| Confidence indicator | `xai_explainer.confidence_score` | Yellow badge if <60, red/blocked if <40 |

### 4.4 Results Panel — Hospital Cards (List View)

| UI Element | Backend Field | Test |
|---|---|---|
| Hospital name | `hospitals[].name` | Must match real hospital in the city queried |
| Distance (km) | `hospitals[].distance_km` | Must be computed from user location; change location → distance changes |
| Fusion score badge | `hospitals[].fusion_score.total` | Must be between 0–1; should match manual formula |
| Accreditation tags (NABH, JCI) | `hospitals[].accreditations[]` | Only show if hospital actually has accreditation |
| Wait time proxy | `hospitals[].appointment_proxy` | Must match queuing model output |
| Cost range | `hospitals[].cost_estimate.min` / `max` | Must vary by hospital tier |
| ABSA sentiment tags | `hospitals[].sentiment` | "Doctors: Positive", etc. — from ABSA pipeline |
| "Compare" button | Triggers side-by-side UI | Selecting two hospitals must show comparison panel populated from `hospitals[]` |
| "View Details" button | Opens modal | Modal data from `hospitals[].detail` |

### 4.5 Results Panel — Map View (Leaflet.js)

| UI Element | Backend Field | Test |
|---|---|---|
| Map center | `map_data.map_config.center` | Must center on user's geocoded city |
| Hospital markers | `map_data.hospital_markers[]` | Count must match `hospitals[]` count |
| Marker color | `hospitals[].tier` | Green = Premium, Blue = Mid-tier, Orange = Budget |
| Marker click → panel update | `hospitals[].fusion_score + cost_estimate` | Click marker → side panel updates WITHOUT new API call |
| Map legend | `map_data.map_config.legend` | Must be dynamically driven, not hardcoded HTML |

```javascript
// Browser console test on the map page:
// After loading results, inspect the Leaflet markers
document.querySelectorAll('.leaflet-marker-icon').length
// Must equal the number of hospitals returned from backend
```

### 4.6 Sidebar

| UI Element | Backend Field | Test |
|---|---|---|
| "My Appointment Requests" badge | `session.appointment_requests.length` | Book an appointment → badge increments |
| Saved Results list | `session.saved_results[]` | Click save → item appears |
| History list | `session.conversation_history` user messages | Each chat turn adds an entry |
| "Add Location" chip | Writes to `session.user_location` | After saving, re-query → new location used in geo-spatial |
| "Patient Details" chip | Writes to `session.patient_profile` | After saving age/comorbidities, pathway agent uses them |
| "Set Budget" chip | Writes to `session.patient_profile.budget_inr` | After setting budget, affordability score adjusts |
| Dark Mode toggle | Frontend only (localStorage) | Acceptable — no backend call needed |
| Lender / Insurer Mode toggle | Switches dashboard view; calls `POST /api/lender/underwrite` | Toggle → network tab shows lender endpoint called |

### 4.7 Financial Assistance Section

| UI Element | Backend Field | Test |
|---|---|---|
| Government scheme rows | `financial_assistance.government_schemes[]` | Must include Ayushman Bharat PM-JAY for eligible patients |
| Lending partner rows | `financial_assistance.lending_partners[]` | Must show real NBFC names with interest rate bands |
| DTI assessment | `financial_assistance.dti_ratio` + `risk_flag` | Must match manual DTI calculation |
| "Apply Now" CTA | `financial_assistance.call_to_action` | Button text must come from backend risk band mapping |

### 4.8 EMI Calculator

| UI Element | Backend Field | Verification |
|---|---|---|
| Principal slider | User input → `POST /api/emi-calculate` | Move slider → new API call fires |
| Interest rate slider | User input → `POST /api/emi-calculate` | Move slider → API call fires |
| Tenure slider (12/24/36 months) | User input → `POST /api/emi-calculate` | Change tenure → API call fires |
| Monthly EMI display | `emi_response.monthly_emi` | Must match formula; see Section 2.4 |
| Total repayment display | `emi_response.total_repayment` | Must equal `monthly_emi × tenure_months` |
| Disclaimer text | `"These are indicative figures..."` | Must appear below calculator |

**EMI Debounce Test:** Drag the principal slider quickly — the frontend must debounce API calls (300–500ms) to avoid flooding `/api/emi-calculate`. Check Network tab for call frequency.

### 4.9 Appointment Checklist Section

| UI Element | Backend Field | Test |
|---|---|---|
| Document checklist items | `appointment_checklist.documents[]` | Must be specific to the procedure, not generic |
| Doctor questions list | `appointment_checklist.questions[]` | Must relate to the identified condition |
| "Generate Form" buttons | `appointment_checklist.forms[]` → `GET /api/form-template/{form_name}` | Button click → file download from backend |
| "Download Checklist" button | Serializes checklist to PDF | Must trigger download, not open a new page |
| Availability proxy text | `appointment_checklist.availability_proxy.wait_time_display` | Must match queuing model output |

### 4.10 XAI / Explainability Section

| UI Element | Backend Field | Test |
|---|---|---|
| SHAP waterfall chart | `xai_explanation.shap_waterfall.features[]` | Each bar corresponds to a feature (clinical, reputation, etc.) |
| SHAP bar values | `feature.contribution` | Bars must be proportional to contribution values |
| LIME highlighted text | `xai_explanation.lime_highlights.highlighted_tokens[]` | Triggering phrases must be highlighted in the displayed query |
| Confidence score display | `xai_explanation.confidence_score` | Must match formula: `0.4×Faithfulness + 0.3×ContextRelevancy + 0.3×AnswerRelevancy` |
| Uncertainty banner | Shown if `confidence_score < 60` | Test with an ambiguous query; banner must appear |
| Blocked results state | Shown if `confidence_score < 40` | Test with a completely garbled query |

---

## 5. LLM Integration Tests

These tests verify that the Anthropic API (`claude-sonnet-4-20250514`) is actively generating responses and not serving cached or mocked data.

### 5.1 LLM Connectivity Test

```python
# test_llm_connectivity.py
import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    messages=[{
        "role": "user",
        "content": "Respond ONLY with: HEALTHNAV_LLM_OK"
    }]
)

assert "HEALTHNAV_LLM_OK" in response.content[0].text
print("LLM Connectivity: PASS ✅")
```

### 5.2 Triage Prompt Test (LLM-Driven)

```python
# test_llm_triage_prompt.py
# Verify the triage classifier uses the LLM and returns valid JSON
import json

triage_response = call_triage_agent("sudden severe headache with vision loss")
data = json.loads(triage_response)

assert data["triage"] in ["RED", "YELLOW", "GREEN"]
assert "reasoning" in data
assert data["triage"] == "RED"   # Stroke symptoms → must be RED
print("LLM Triage Prompt: PASS ✅")
```

### 5.3 Response Freshness Test

Each `/api/chat` call with a slightly different query must produce a different LLM response. This rules out full response caching that would prevent the LLM from actually running:

```bash
# Send two near-identical queries with slight variations
curl -X POST .../api/chat -d '{"message": "knee replacement Nagpur", ...}'
curl -X POST .../api/chat -d '{"message": "knee surgery Nagpur", ...}'

# The chat_response.message text must differ meaningfully between the two
```

### 5.4 Hallucination Guard Test (RAG Confidence)

```python
# Send a completely unknown query to trigger low confidence
result = call_chat_api("XYZ123 procedure in fake city Zorton")
assert result["xai_explanation"]["confidence_score"] < 60
# Frontend must show yellow uncertainty banner for this response
print("RAG Confidence Guard: PASS ✅")
```

---

## 6. WebSocket Streaming Test

**File:** `Backend/app/api/routes/websocket.py`

```javascript
// Run in browser console on https://tenzor-x.vercel.app/
const ws = new WebSocket('wss://<BACKEND_URL>/ws/chat/browser-test-001');

ws.onopen = () => {
    ws.send(JSON.stringify({ message: "What is angioplasty?" }));
};

const tokens = [];
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Frame:', data);
    if (data.type === 'token') tokens.push(data.content);
    if (data.type === 'done') {
        console.log('Full response:', tokens.join(''));
        console.log('Token count:', tokens.length);
        // Token count > 1 confirms streaming is working
        console.assert(tokens.length > 5, 'Streaming not working — only 1 token received');
    }
};

ws.onerror = (e) => console.error('WebSocket error:', e);
```

**Pass criteria:**
- Multiple `token` frames received before `done`
- Full response is medically coherent
- No `403` or `426` (Upgrade Required) errors

---

## 7. Session & Memory Continuity Tests

These tests verify that multi-turn conversation context is maintained across messages.

### Test 7.1 — Comorbidity Context Persistence

```
Turn 1: "I need a knee replacement near Nagpur"
Turn 2: "Will my diabetes affect this?"
```

**Expected:** Turn 2 response must reference "knee replacement" and "diabetes" together without the user restating the procedure. The cost estimate in Turn 2 must include a comorbidity multiplier.

**Check in response:** `treatment_pathway.comorbidity_note` must be non-null and mention diabetes.

**Failure sign:** Turn 2 response asks "What procedure are you asking about?" → session memory is broken.

### Test 7.2 — Budget Filter Persistence

```
Turn 1: "Knee replacement hospitals in Nagpur"
Turn 2: "Set my budget to Rs 2.5 lakh"
Turn 3: "Show me options again"
```

**Expected:** Turn 3 hospital list must only show hospitals with `cost_estimate.min <= 250000`. Budget is applied from session, not re-sent in the message.

### Test 7.3 — Location Update

```
Turn 1: "Heart bypass hospitals near Raipur"
  → hospitals must be in/near Raipur
Turn 2: [User clicks "Add Location" and sets Nagpur]
Turn 3: "Show me more options"
  → hospitals must now be in/near Nagpur
```

**Failure sign:** Turn 3 still returns Raipur hospitals → session location update is not being read by the Geo-Spatial Agent.

### Test 7.4 — Cross-Session Isolation

Open two browser tabs simultaneously with different queries:
- Tab A: "Knee replacement Nagpur"
- Tab B: "Heart bypass Raipur"

Each tab must have a different `session_id`. Tab A responses must never reference "heart bypass." Tab B responses must never reference "knee replacement."

**Failure sign:** Data leaks between tabs → the global `store = {}` in `get_session_history` is not properly scoped to `session_id`.

---

## 8. Financial Engine Verification

### 8.1 DTI Risk Band Matrix Test

Run all four DTI thresholds and verify correct risk classification:

| Monthly Income | Existing EMIs | Loan | Tenure | Expected DTI | Expected Risk Flag |
|---|---|---|---|---|---|
| ₹80,000 | ₹5,000 | ₹1,60,000 | 24 months | ~19% | Low Risk |
| ₹50,000 | ₹8,000 | ₹1,60,000 | 24 months | ~34% | Medium Risk |
| ₹40,000 | ₹10,000 | ₹1,60,000 | 24 months | ~44% | High Risk |
| ₹30,000 | ₹12,000 | ₹1,60,000 | 24 months | ~58% | Critical Risk |

### 8.2 Comorbidity Cost Multiplier Test

```python
# Base cost for TKA Tier 1
base = run_clinical_pathway("Total Knee Arthroplasty (TKA)", city_tier=1, comorbidities=[])
base_max = base["cost_estimate"]["max"]

# With diabetes comorbidity
with_dm = run_clinical_pathway("Total Knee Arthroplasty (TKA)", city_tier=1, comorbidities=["diabetes"])
dm_max = with_dm["cost_estimate"]["max"]

# Diabetes multiplier should add ~20-40% (ωᵢ weight from PDF)
assert dm_max > base_max * 1.10, "Diabetes comorbidity multiplier not applied"
assert dm_max < base_max * 2.00, "Comorbidity multiplier unreasonably large"
print("Comorbidity Multiplier: PASS ✅")
```

### 8.3 Geographic Multiplier Test

```python
tier1 = run_clinical_pathway("Angioplasty", city_tier=1, comorbidities=[])
tier2 = run_clinical_pathway("Angioplasty", city_tier=2, comorbidities=[])
tier3 = run_clinical_pathway("Angioplasty", city_tier=3, comorbidities=[])

assert tier1["cost_estimate"]["max"] > tier2["cost_estimate"]["max"] > tier3["cost_estimate"]["max"], \
    "Geographic pricing order wrong: Tier 1 > Tier 2 > Tier 3 expected"
print("Geographic Multiplier Order: PASS ✅")
```

---

## 9. Geo-Spatial Agent Verification

**File:** `Backend/app/agents/geo_spatial_agent.py`

### 9.1 Geocoding Accuracy Test

| Input String | Expected City | Expected Tier | Expected Lat (approx) | Expected Lng (approx) |
|---|---|---|---|---|
| `"Nagpur"` | Nagpur | 2 | 21.14 | 79.08 |
| `"Raipur"` | Raipur | 2 | 21.25 | 81.62 |
| `"Mumbai"` | Mumbai | 1 | 19.07 | 72.87 |
| `"Ambikapur"` | Ambikapur | 3 | 23.11 | 83.19 |

```python
for city, expected_tier, exp_lat, exp_lng in [
    ("Nagpur", 2, 21.14, 79.08),
    ("Raipur", 2, 21.25, 81.62),
]:
    result = run_geocoding(city)
    assert result["city_tier"] == expected_tier
    assert abs(result["lat"] - exp_lat) < 0.5
    assert abs(result["lng"] - exp_lng) < 0.5
print("Geocoding Accuracy: PASS ✅")
```

### 9.2 Distance Calculation Test

```python
# Nagpur (21.14, 79.08) to Hospital A (21.15, 79.09)
dist = calculate_distance(21.14, 79.08, 21.15, 79.09)
# Haversine formula: should be ~1.5 km
assert 1.0 < dist < 2.5, f"Distance calculation wrong: {dist} km"
print("Distance Calculation: PASS ✅")
```

### 9.3 Map Marker Color Logic

```python
# Premium hospital (Clinical score > 0.8) → Green marker
# Mid-tier → Blue marker
# Budget → Orange marker
# Emergency capable → Red marker (for triage RED queries)
for hospital in result["hospitals"]:
    if hospital["tier"] == "Premium":
        assert hospital["map_marker"]["color"] == "green"
    elif hospital["tier"] == "Mid-tier":
        assert hospital["map_marker"]["color"] == "blue"
    elif hospital["tier"] == "Budget":
        assert hospital["map_marker"]["color"] == "orange"
```

---

## 10. XAI Explainer Verification

**File:** `Backend/app/agents/xai_explainer_agent.py`

### 10.1 SHAP Score Math Verification

For a hospital with known component scores:
```
Clinical = 0.88, Reputation = 0.75, Accessibility = 0.90, Affordability = 0.85

Expected total = (0.88 × 0.40) + (0.75 × 0.25) + (0.90 × 0.20) + (0.85 × 0.15)
               = 0.352 + 0.1875 + 0.18 + 0.1275
               = 0.847
```

```python
hospital = {"fusion_score": {"clinical": 0.88, "reputation": 0.75, "accessibility": 0.90, "affordability": 0.85}}
xai = run_xai_explainer(hospital)
assert abs(xai["final_score"] - 0.847) < 0.001
print("SHAP Score Math: PASS ✅")
```

### 10.2 LIME Token Highlighting for RED Triage

```python
result = run_xai_explainer(
    top_hospital={...},
    triage_query="chest pain radiating to the left arm with sweating",
    triage_result="RED"
)

highlighted = [t["text"] for t in result["lime_highlights"]["highlighted_tokens"]]
# Must include the clinically significant phrases
assert any("chest pain" in h or "left arm" in h for h in highlighted), \
    "LIME must highlight the triggering clinical phrases"
print("LIME Token Highlighting: PASS ✅")
```

### 10.3 Confidence Score Formula Test

```python
# S = 0.4 × Faithfulness + 0.3 × Context_Relevancy + 0.3 × Answer_Relevancy
faithfulness = 0.85
context_relevancy = 0.70
answer_relevancy = 0.80

expected_score = (0.4 * faithfulness + 0.3 * context_relevancy + 0.3 * answer_relevancy) * 100
# = (0.34 + 0.21 + 0.24) × 100 = 79

result = run_xai_explainer(..., faithfulness=faithfulness, context_relevancy=context_relevancy, answer_relevancy=answer_relevancy)
assert abs(result["confidence_score"] - expected_score) < 2.0
print("Confidence Score Formula: PASS ✅")
```

---

## 11. Appointment Agent Verification

**File:** `Backend/app/agents/appointment_agent.py`

### 11.1 Availability Proxy Logic Test

| Hospital Beds | Specialists | Bed Occupancy | Expected Proxy Output |
|---|---|---|---|
| 500+ (large corporate) | 5+ cardiologists | Normal | "Appointments usually available within 2-3 days" |
| 150 (mid-tier) | 2 specialists | High | "Estimated waiting time: 4-7 days" |
| 30 (small clinic) | 1 specialist | Any | "Waiting time: 1-2 weeks" |
| Any (Level-1 Trauma ER) | Any | Any | "24/7 emergency available ✅" |

```python
# GREEN triage + large hospital
proxy = run_appointment_proxy(bed_count=500, specialists=5, has_emergency=False)
assert "2-3 days" in proxy

# RED triage → emergency override regardless of hospital size
proxy = run_appointment_proxy(bed_count=30, specialists=1, has_emergency=True)
assert "24/7 emergency available ✅" in proxy
print("Appointment Proxy Logic: PASS ✅")
```

### 11.2 Procedure-Specific Document Checklist

```python
tka_checklist = run_appointment_agent("Total Knee Arthroplasty (TKA)", ...)
angio_checklist = run_appointment_agent("Angioplasty", ...)

# Checklists must differ by procedure
tka_docs = {d["name"] for d in tka_checklist["documents"]}
angio_docs = {d["name"] for d in angio_checklist["documents"]}

# TKA should have ortho-specific docs
assert any("X-Ray" in d or "MRI" in d for d in tka_docs), "TKA checklist missing imaging docs"
# Angioplasty should have cardiac-specific docs
assert any("ECG" in d or "Angiography" in d for d in angio_docs), "Angio checklist missing cardiac docs"

# They should NOT be identical
assert tka_docs != angio_docs, "Checklists are procedure-agnostic — agent not customizing output"
print("Procedure-Specific Checklist: PASS ✅")
```

---

## 12. Lender / Insurer Mode Verification

**File:** `Backend/app/api/routes/lender.py`

### 12.1 Full Underwriting Response Test

```bash
curl -X POST https://<BACKEND_URL>/api/lender/underwrite \
  -d '{
    "procedure": "Angioplasty",
    "city": "Raipur",
    "patient_income_monthly": 35000,
    "existing_emis": 8000,
    "loan_amount_requested": 120000,
    "tenure_months": 24
  }'
```

**Verify:**
1. DTI correctly calculated
2. Risk flag assigned per threshold table
3. SHAP explanation present in response
4. Hospital tier distribution for Angioplasty in Raipur (Tier 2/3) present

### 12.2 Dashboard UI Switch Test

1. Go to `https://tenzor-x.vercel.app/`
2. Open sidebar → toggle "Lender / Insurer Mode"
3. Open Network tab in DevTools
4. Observe that the UI switches to the B2B layout
5. Verify that toggling mode triggers a call to `POST /api/lender/underwrite` (not `/api/chat`)
6. Verify that Appointment / Checklist sections are hidden in Lender Mode
7. Verify that DTI risk band matrix is shown
8. Verify that SHAP attribution chart is shown

---

## 13. Safety & Disclaimer Verification

### 13.1 Global Banner

Navigate to `https://tenzor-x.vercel.app/` without sending any query.

**Expected:** Banner must be visible at the top of the page:
> "HealthNav provides decision support only, not medical advice. Always consult a qualified doctor before making health decisions."

**Test:** Inspect DOM:
```javascript
document.querySelector('[data-testid="global-disclaimer"]').textContent
// Must contain "decision support only"
```

### 13.2 Per-Response Disclaimer

Send any query. Inspect `POST /api/chat` response:
```json
{
  "chat_response": {
    "disclaimer": "Decision support only. Please consult a qualified doctor before making medical decisions."
  }
}
```
This disclaimer must appear below every chat response bubble.

### 13.3 RED Triage Override Test

```
Query: "chest pain radiating to left arm with shortness of breath"
```

**Expected behavior:**
1. `triage == "RED"` in response
2. Budget and geo filters are ignored — all hospitals shown regardless
3. Emergency contact numbers displayed prominently
4. Appointment proxy shows "24/7 emergency available ✅" for ER-capable hospitals
5. LIME highlights "chest pain" and/or "left arm" in the query display
6. Standard "Compare" and sorting controls are disabled

### 13.4 Low Confidence Warning

Send a deliberately ambiguous/garbled query:
```
Query: "zxywq problem help hospital money"
```

**Expected:** `confidence_score < 60` → yellow uncertainty banner appears in Results panel above any results.

```javascript
// Check DOM for uncertainty banner
document.querySelector('[data-testid="confidence-warning"]')
// Must be visible and non-null
```

### 13.5 EMI Disclaimer

Open the EMI Calculator section. Verify this text is visible:
> "These are indicative figures. Confirm final rates with lenders."

---

## 14. Regression Test Matrix

Run this matrix after every backend deployment to ensure no regressions.

| Test ID | Query | Expected triage | Hospital count ≥ | Cost populated | Map markers ≥ | Confidence ≥ 60 | SHAP present |
|---|---|---|---|---|---|---|---|
| R01 | "Knee replacement Nagpur Rs 2 lakh" | GREEN | 3 | ✅ | 3 | ✅ | ✅ |
| R02 | "Heart bypass Raipur" | GREEN/YELLOW | 2 | ✅ | 2 | ✅ | ✅ |
| R03 | "chest pain left arm sweating" | RED | 1 | ✅ | 1 | ✅ | ✅ |
| R04 | "Best cancer hospital in Raipur" | GREEN | 2 | ✅ | 2 | ✅ | ✅ |
| R05 | "What is angioplasty?" | GREEN | 0 (informational) | N/A | 0 | ✅ | N/A |
| R06 | "Explain my diabetes diagnosis" | GREEN | 0 (informational) | N/A | 0 | ✅ | N/A |
| R07 | Completely garbled input | GREEN | 0 | N/A | 0 | ❌ (<40) | N/A |
| R08 | "Knee replacement" + set budget ₹1L → re-query | GREEN | ≥1 (in budget) | ✅ | ≥1 | ✅ | ✅ |

---

## 15. Common Failure Modes & Fixes

| Symptom | Likely Cause | Fix |
|---|---|---|
| Frontend shows blank Results panel after chat | `POST /api/chat` returning 500 | Check backend logs; verify all agents import correctly in `__init__.py` |
| Map shows no markers | Geo-Spatial Agent geocoding failure | Check `GOOGLE_MAPS_API_KEY` or `NOMINATIM_USER_AGENT` env vars |
| EMI calculator shows ₹0 | `/api/emi-calculate` not connected | Check `emi.py` route is registered in `main.py` router |
| Session data lost on page refresh | `GET /api/session/{id}` returning 404 | Verify `session.py` GET route exists and Redis is connected |
| Lender mode toggle does nothing | `POST /api/lender/underwrite` missing | Verify `lender.py` route is imported in `main.py` |
| CORS error in browser console | Backend CORS config missing Vercel origin | Add `https://tenzor-x.vercel.app` to `allow_origins` in `main.py` |
| Triage always returns GREEN for RED queries | LLM prompt not reaching Anthropic API | Check `ANTHROPIC_API_KEY` is valid and not rate-limited |
| Form download returns 404 | `/api/form-template/{name}` route broken | Verify `form_template.py` handles all 3 form names |
| Appointment badge stuck at 0 | `PATCH /api/session/.../appointment` not called on booking | Wire "Book" button click to PATCH endpoint in frontend |
| Confidence score always 100 | XAI agent returning hardcoded value | Verify `xai_explainer_agent.py` computes score from RAG metrics |
| Chat history bleeds between users | Session IDs not properly scoped | Ensure `get_session_history` uses `session_id` as key, not a global variable |
| Hospital costs identical for all cities | Geographic multiplier not applied | Verify `γ_geo` factor in `clinical_pathway_agent.py` uses `city_tier` |

---

*Last updated: May 2026 · HealthNav India · Verification Manual v1.0*  
*Run this document top-to-bottom on every major release. All 14 sections must pass before marking a release as production-ready.*
