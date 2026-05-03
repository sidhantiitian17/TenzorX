# 🏥 AI-Powered Healthcare Navigator & Cost Estimator

> A decision-intelligence platform that transforms fragmented healthcare information into transparent, personalized clinical and financial guidance — built for India's Tier 2 and Tier 3 cities.

---

## 📌 Problem Statement

India's healthcare ecosystem suffers from deep structural fragmentation and information asymmetry. Patients in non-metro cities face three compounding challenges:

- **Clinical opacity** — difficulty identifying the right facility and treatment pathway
- **Financial anxiety** — no reliable way to anticipate procedure costs, especially with comorbidities
- **Lending friction** — NBFC healthcare loan underwriting takes 7–21 days, incompatible with urgent medical needs

This platform is designed as a **"Kayak for Healthcare"** — translating raw patient intent into structured clinical pathways, scoring providers through multi-source intelligence, and generating comorbidity-adjusted financial estimates.

---

## ✨ Key Features

### 🧠 Clinical Intelligence
| Feature | Description |
|---|---|
| **GraphRAG Engine** | Neo4j knowledge graph fused with vector RAG for deterministic symptom-to-pathway traversal |
| **Medical NER + ICD-10 Mapping** | Parses free-text input and maps to standardized ICD-10-CM codes |
| **Symptom Severity Classifier** | LLM-powered triage — Red (Emergency), Yellow (Urgent), Green (Elective) |
| **Treatment Pathway Explainer** | Phase-by-phase clinical roadmap with per-component cost breakdown |

### 💰 Financial Intelligence
| Feature | Description |
|---|---|
| **Geographic Pricing Adjustment** | Cost multipliers calibrated by city tier (Tier 1/2/3) |
| **Comorbidity Cost Adjustment** | Epidemiologically grounded multipliers for diabetes, heart failure, kidney disease, etc. |
| **NBFC Loan Pre-Underwriting** | Instant DTI-based loan eligibility assessment across 12/24/36-month tenures |
| **Cashless Insurance Estimator** | Component-level billing breakdown for insurer pre-authorization |

#### 🔢 Core Financial Formulas

**Comorbidity-Adjusted Cost Estimation**

The final cost estimate accounts for all active comorbid conditions using empirically derived weight coefficients:

$$\text{Final\_Estimated\_Cost} = \text{Adjusted\_Cost} \times \left(1 + \sum_{i=1}^{n} \omega_i C_i\right)$$

Where:
- `Adjusted_Cost` = base procedure cost after geographic tier multiplier
- `ωᵢ` = empirically derived weight for comorbidity `i` (e.g., Heart Failure → 3.3×, Kidney Disease → 2.7×, Diabetes → 1.5×)
- `Cᵢ` = binary flag (1 if condition is present, 0 otherwise)
- `n` = total number of comorbid conditions declared by the user

**NBFC Loan Pre-Underwriting (DTI Ratio)**

Loan eligibility is assessed instantly using the Debt-to-Income ratio, the primary metric used by Indian NBFCs:

$$\text{DTI\_Ratio} = \frac{\text{Existing\_EMIs} + \text{Proposed\_Medical\_EMI}}{\text{Gross\_Monthly\_Income}} \times 100$$

| DTI Range | Risk Band | Approval Likelihood | Interest Rate |
|---|---|---|---|
| < 30% | 🟢 Low Risk | Very High | 12–13% |
| 30–40% | 🟡 Medium Risk | Conditional | 13–15% |
| 40–50% | 🟠 High Risk | Manual Review | 15–16% |
| > 50% | 🔴 Critical Risk | Unlikely | N/A |

### 🏨 Provider Discovery
| Feature | Description |
|---|---|
| **Multi-Source Fusion Score** | Composite ranking: Clinical (40%) + Reputation (25%) + Accessibility (20%) + Affordability (15%) |
| **Aspect-Based Sentiment Analysis** | ABSA via XGBoost + VADER across doctor quality, staff, facilities, and affordability |
| **Appointment Availability Proxy** | Queuing-theory-based wait time estimates without real-time API dependency |
| **Geo-Spatial Intelligence** | Geopy geocoding + Leaflet.js interactive hospital map |

### 🔍 Transparency & Safety
| Feature | Description |
|---|---|
| **SHAP Explanations** | Waterfall plots showing exactly why a hospital was ranked where it was |
| **LIME for NLP** | Token-level explanation of why a symptom triggered emergency routing |
| **RAG Confidence Scoring** | Contextual Relevancy + Answer Relevancy + Faithfulness — flags low-confidence responses |

---

## 🏗️ Architecture Overview

```
User Query (Natural Language)
        │
        ▼
┌─────────────────────┐
│   LangChain Agent   │  ← ConversationBufferMemory (session-isolated)
│   (Multi-turn)      │
└────────┬────────────┘
         │
    ┌────▼─────┐     ┌──────────────────────┐
    │ NER/ICD  │────▶│  Neo4j GraphRAG       │
    │ Pipeline │     │  (Symptom → Pathway)  │
    └──────────┘     └──────────┬───────────┘
                                │
              ┌─────────────────▼──────────────────┐
              │         Decision Engine             │
              │  ┌──────────┐  ┌─────────────────┐ │
              │  │ Severity │  │ Cost Estimator  │ │
              │  │Classifier│  │ (Geo + Comorbid)│ │
              │  └──────────┘  └─────────────────┘ │
              │  ┌──────────┐  ┌─────────────────┐ │
              │  │   NBFC   │  │ Fusion Scorer   │ │
              │  │Underwrite│  │ (4-component)   │ │
              │  └──────────┘  └─────────────────┘ │
              └─────────────────┬──────────────────┘
                                │
              ┌─────────────────▼──────────────────┐
              │       Streamlit Dashboard           │
              │  Side-by-side comparison │ Map view │
              │  SHAP/LIME visualizations│ RAG score│
              └────────────────────────────────────┘
```

---

## 🧩 Technology Stack

| Layer | Technology |
|---|---|
| **Orchestration** | LangChain (AgentExecutor, RunnableWithMessageHistory) |
| **Knowledge Graph** | Neo4j (Cypher queries via GraphCypherQAChain) |
| **Vector Store** | Neo4j Vector Index |
| **LLM** | OpenAI GPT-4 / Claude (configurable) |
| **NER** | spaCy / AWS Comprehend Medical |
| **Medical Ontology** | ICD-10-CM JSON (2022), SNOMED CT |
| **Sentiment Analysis** | XGBoost + TF-IDF, VADER, LDA |
| **Geo-Spatial** | Geopy (Nominatim/GoogleV3) + Leaflet.js via streamlit-folium |
| **Explainability** | SHAP (TreeExplainer/KernelExplainer), LIME |
| **RAG Evaluation** | DeepEval / Evidently AI |
| **Frontend** | Streamlit |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Neo4j 5.x (local or AuraDB)
- OpenAI API key (or compatible LLM provider)

### Installation

```bash
git clone https://github.com/your-org/healthcare-navigator.git
cd healthcare-navigator
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
GEOCODING_API_KEY=your_google_maps_key   # optional, Nominatim works without a key
```

### Seed the Knowledge Graph

```bash
python scripts/seed_graph.py          # loads disease/procedure/hospital nodes
python scripts/load_icd10.py          # imports ICD-10-CM JSON into Neo4j
```

### Run the Application       

```bash
npm run dev      #for frontend
cd backend 
python -m unicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📊 Gap Resolution Map

This platform directly addresses **9 operational gaps** in the Indian healthcare decision pipeline:

| Gap | Problem | Solution |
|---|---|---|
| Gap 1 | Unstructured patient reviews ignored | Aspect-Based Sentiment Analysis (ABSA) |
| Gap 2 | Cashless insurance unpredictability | Component-level billing estimator for insurers |
| Gap 3 | NBFC loan TAT of 7–21 days | Automated DTI-based pre-underwriting (milliseconds) |
| Gap 4 | No appointment availability data | Queuing-theory proxy from bed/specialist ratios |
| Gap 5 | Pricing ignores geography | City-tier geographic cost multiplier |
| Gap 6 | No comorbidity cost adjustment | Age + condition multipliers (diabetes, HF, CKD) |
| Gap 7 | Single-metric provider ranking | 4-component normalized Fusion Score |
| Gap 8 | No side-by-side comparison | Streamlit `st.columns()` comparative dashboard |
| Gap 9 | Patients don't understand pathways | Phase-by-phase treatment + cost roadmap |

---

## 💡 Example Workflows

### Patient Flow
1. User types: *"I have severe chest pain radiating to my left arm"*
2. NER extracts entities → ICD-10 maps to Ischemic Heart Disease
3. Severity Classifier → **🔴 Red (Emergency)**
4. GraphRAG traverses: symptom → diagnosis → Angioplasty pathway
5. Cost engine applies Raipur (Tier 2) multiplier → ₹1.8L–₹2.8L estimate
6. Diabetes comorbidity flag adds 15–30% contingency
7. Dashboard shows top 3 hospitals side-by-side with SHAP waterfall

### Lender Flow
1. Lender inputs: procedure cost ₹2.5L, patient income ₹60K/month, existing EMI ₹8K
2. DTI = (8K + proposed EMI) / 60K → **28% → Low Risk**
3. Output: *"Loan ₹2.0L | EMI ₹6,200–₹18,500 | Aap eligible hain — Apply Now"*

---

## 🛡️ Ethical Safeguards

- All outputs carry a mandatory disclaimer: *"This system provides decision support only and does not constitute medical advice or diagnosis."*
- The Symptom Severity Classifier is a **routing tool only** — it does not diagnose.
- RAG Confidence Scores below threshold visually flag uncertain responses in the UI.
- SHAP/LIME explanations are always surfaced alongside recommendations.
- Session isolation prevents cross-user data leakage in multi-user deployments.

---

## 📁 Project Structure

```
healthcare-navigator/
├── app.py                        # Streamlit entry point
├── config/
│   └── settings.py               # Environment & model config
├── core/
│   ├── agent.py                  # LangChain agent + memory management
│   ├── graph_rag.py              # Neo4j GraphRAG pipeline
│   ├── ner_pipeline.py           # spaCy NER + ICD-10 mapping
│   ├── severity_classifier.py    # Red/Yellow/Green triage
│   └── cost_engine.py            # Geographic + comorbidity adjustments
├── fintech/
│   ├── loan_underwriter.py       # DTI calculator + risk banding
│   └── insurance_estimator.py    # Cashless pre-auth estimator
├── discovery/
│   ├── sentiment_absa.py         # XGBoost + VADER aspect analysis
│   ├── availability_proxy.py     # Queuing-theory wait time model
│   └── fusion_scorer.py          # 4-component normalized ranking
├── ui/
│   ├── dashboard_patient.py      # Patient/Doctor view
│   ├── dashboard_lender.py       # Lender/Insurer view
│   └── map_component.py          # Leaflet.js via streamlit-folium
├── explainability/
│   ├── shap_explainer.py         # SHAP waterfall plots
│   └── lime_explainer.py         # LIME token highlighting
├── scripts/
│   ├── seed_graph.py             # Neo4j data seeding
│   └── load_icd10.py             # ICD-10-CM JSON importer
├── data/
│   └── icd10_2022.json           # ICD-10-CM source data
├── requirements.txt
└── .env.example
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [ICD-10-CM 2022 JSON](https://github.com/smog1210/2022-ICD-10-CM-JSON) for the medical ontology source
- [Neo4j GraphRAG](https://neo4j.com/blog/developer/rag-tutorial/) for the knowledge graph architecture pattern
- [Kearney India Healthcare Index](https://www.kearney.com/industry/health/article/kearney-india-healthcare-index-a-new-outlook-for-geographic-expansion) for geographic cost benchmarks
- IRDAI's "Cashless Everywhere" initiative for insurance integration context
