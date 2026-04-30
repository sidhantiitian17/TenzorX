# TenzorX — Backend Implementation Manual
## AI-Powered Healthcare Navigator & Cost Estimator

> **Stack:** Python · FastAPI · Neo4j · LangChain · NVIDIA LLM API (Mistral Large)
>
> **LLM Provider:** All LLM inference goes exclusively through `https://integrate.api.nvidia.com/v1/chat/completions`
> using model `mistralai/mistral-large-3-675b-instruct-2512`.
>
> **Core Mission:** Implement a decision-intelligence layer resolving 9 operational gaps in Indian healthcare
> access, affordability, and transparency — for Tier 2/3 cities.

---

## Table of Contents

1. [Repository Structure](#1-repository-structure)
2. [Environment & Dependencies](#2-environment--dependencies)
3. [NVIDIA LLM Client (Canonical Module)](#3-nvidia-llm-client-canonical-module)
4. [Neo4j Knowledge Graph Setup](#4-neo4j-knowledge-graph-setup)
5. [NER Pipeline & ICD-10 Ontology Integration](#5-ner-pipeline--icd-10-ontology-integration)
6. [GraphRAG Engine](#6-graphrag-engine)
7. [LangChain Agentic AI & Multi-Turn Memory](#7-langchain-agentic-ai--multi-turn-memory)
8. [Symptom Severity Classifier (Gap Resolver)](#8-symptom-severity-classifier-gap-resolver)
9. [Treatment Pathway & Cost Engine (Gap 9)](#9-treatment-pathway--cost-engine-gap-9)
10. [Geographic Pricing Adjustment (Gap 5)](#10-geographic-pricing-adjustment-gap-5)
11. [Age & Comorbidity Cost Adjustment (Gap 6)](#11-age--comorbidity-cost-adjustment-gap-6)
12. [NBFC Loan Pre-Underwriting Engine (Gap 3)](#12-nbfc-loan-pre-underwriting-engine-gap-3)
13. [Insurance Cashless Integration (Gap 2)](#13-insurance-cashless-integration-gap-2)
14. [Sentiment Analysis — ABSA Pipeline (Gap 1)](#14-sentiment-analysis--absa-pipeline-gap-1)
15. [Appointment Availability Proxy (Gap 4)](#15-appointment-availability-proxy-gap-4)
16. [Multi-Source Data Fusion Score (Gap 7)](#16-multi-source-data-fusion-score-gap-7)
17. [Hospital Comparison Engine (Gap 8)](#17-hospital-comparison-engine-gap-8)
18. [Geo-Spatial Intelligence](#18-geo-spatial-intelligence)
19. [Explainable AI — LIME & SHAP](#19-explainable-ai--lime--shap)
20. [RAG Confidence Scoring System](#20-rag-confidence-scoring-system)
21. [FastAPI Route Definitions](#21-fastapi-route-definitions)
22. [Data Models (Pydantic)](#22-data-models-pydantic)
23. [Mock Data & Seed Scripts](#23-mock-data--seed-scripts)
24. [Frontend API Contract](#24-frontend-api-contract)
25. [Deployment & Configuration](#25-deployment--configuration)

---

## 1. Repository Structure

The backend lives entirely inside the `Backend/` folder of the TenzorX repo.

```
Backend/
├── main.py                          # FastAPI app entry point
├── requirements.txt
├── .env.example
│
├── core/
│   ├── nvidia_client.py             # CANONICAL NVIDIA LLM wrapper (Section 3)
│   ├── config.py                    # All env vars and constants
│   └── exceptions.py                # Custom exceptions
│
├── knowledge_graph/
│   ├── neo4j_client.py              # Neo4j connection + Cypher helpers
│   ├── schema_setup.py              # Graph schema creation script
│   ├── graph_rag.py                 # GraphRAG orchestration
│   └── cypher_queries.py            # All Cypher query templates
│
├── nlp/
│   ├── ner_pipeline.py              # spaCy NER + custom medical NER
│   ├── icd10_mapper.py              # ICD-10 JSON lookup + SNOMED CT
│   ├── sentiment_absa.py            # ABSA sentiment analysis (Gap 1)
│   └── topic_modeler.py             # LDA topic modeling
│
├── agents/
│   ├── healthcare_agent.py          # LangChain agentic orchestrator
│   ├── memory_manager.py            # Per-session conversation memory
│   ├── severity_classifier.py       # Symptom triage (Red/Yellow/Green)
│   └── tools/
│       ├── hospital_search_tool.py
│       ├── cost_estimate_tool.py
│       ├── icd_lookup_tool.py
│       └── geo_tool.py
│
├── engines/
│   ├── pathway_engine.py            # Treatment pathway generator (Gap 9)
│   ├── cost_engine.py               # Cost estimation core
│   ├── geo_pricing.py               # Geographic multiplier (Gap 5)
│   ├── comorbidity_engine.py        # Age + comorbidity adjustment (Gap 6)
│   ├── loan_engine.py               # NBFC pre-underwriting (Gap 3)
│   ├── insurance_engine.py          # Cashless integration (Gap 2)
│   ├── availability_proxy.py        # Appointment proxy (Gap 4)
│   ├── fusion_score.py              # Multi-source data fusion (Gap 7)
│   └── comparison_engine.py         # Hospital comparison (Gap 8)
│
├── geo/
│   ├── geocoder.py                  # geopy geocoding
│   └── distance_calc.py             # Haversine + proximity scoring
│
├── xai/
│   ├── shap_explainer.py            # SHAP global/local attribution
│   └── lime_explainer.py            # LIME text perturbation
│
├── confidence/
│   └── rag_confidence.py            # RAG output confidence scoring
│
├── data/
│   ├── icd10_2022.json              # ICD-10 CM 2022 (from GitHub)
│   ├── hospitals_seed.json          # Mock hospital dataset (Section 23)
│   ├── procedure_benchmarks.json    # Cost benchmarks by tier
│   └── reviews_seed.json            # Mock patient reviews for ABSA
│
├── api/
│   ├── routes/
│   │   ├── chat.py                  # POST /api/chat
│   │   ├── hospitals.py             # GET /api/hospitals
│   │   ├── cost.py                  # POST /api/cost-estimate
│   │   ├── loan.py                  # POST /api/loan-eligibility
│   │   ├── compare.py               # POST /api/compare
│   │   └── explain.py               # GET /api/explain/{hospital_id}
│   └── middleware.py                # CORS, logging, error handling
│
└── schemas/
    ├── request_models.py
    └── response_models.py
```

**Critical architectural rule:** The `core/nvidia_client.py` module is the **single point of contact**
for all LLM calls. No module may call the NVIDIA API directly — always import and call through
`NvidiaClient`. This enforces consistent error handling, logging, and token tracking.

---

## 2. Environment & Dependencies

### 2.1 `.env.example`

```bash
# NVIDIA LLM
NVIDIA_API_KEY=nvapi-your-nvidia-api-key-here
NVIDIA_API_URL=https://integrate.api.nvidia.com/v1/chat/completions
NVIDIA_MODEL=mistralai/mistral-large-3-675b-instruct-2512

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Geocoding
NOMINATIM_USER_AGENT=tenzorx_healthnav/1.0

# App
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:3000,https://tenzor-x.vercel.app
LOG_LEVEL=INFO
```

### 2.2 `requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic==2.7.1
python-dotenv==1.0.1
httpx==0.27.0
requests==2.32.3

# LangChain
langchain==0.2.6
langchain-community==0.2.6
langchain-core==0.2.10

# Neo4j
neo4j==5.20.0
langchain-neo4j==0.1.0

# NLP
spacy==3.7.4
en-core-web-sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
scispacy==0.5.4
en-core-sci-sm @ https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_sm-0.5.4.tar.gz
vaderSentiment==3.3.2
scikit-learn==1.5.0
xgboost==2.0.3
gensim==4.3.2
nltk==3.8.1

# Geo
geopy==2.4.1

# XAI
shap==0.45.1
lime==0.2.0.1

# Utilities
numpy==1.26.4
pandas==2.2.2
scipy==1.13.1
```

---

## 3. NVIDIA LLM Client (Canonical Module)

**File:** `core/nvidia_client.py`

This is the **only module** that talks to the NVIDIA API. Every agent, classifier, and engine must
use it. Never hardcode the URL or API key elsewhere.

```python
# core/nvidia_client.py

import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

NVIDIA_API_URL = os.getenv("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1/chat/completions")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MODEL   = os.getenv("NVIDIA_MODEL", "mistralai/mistral-large-3-675b-instruct-2512")


class NvidiaClient:
    """
    Canonical NVIDIA LLM client. All LLM calls in TenzorX backend
    must go through this class. Supports single-turn and multi-turn calls.
    """

    def __init__(
        self,
        model: str = NVIDIA_MODEL,
        temperature: float = 0.15,
        max_tokens: int = 2048,
        top_p: float = 1.00,
        stream: bool = False,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.stream = stream
        self.headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "text/event-stream" if stream else "application/json",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a chat completion request to the NVIDIA API.

        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            system_prompt: Optional system message prepended as role=system
            temperature: Override instance temperature
            max_tokens: Override instance max_tokens

        Returns:
            The text content of the model's reply (stripped).

        Raises:
            RuntimeError: If the API call fails or returns non-200.
        """
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": 0.00,
            "presence_penalty": 0.00,
            "stream": self.stream,
        }

        try:
            response = requests.post(NVIDIA_API_URL, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"NVIDIA API request failed: {e}")
            raise RuntimeError(f"NVIDIA LLM API error: {e}") from e

        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected NVIDIA API response structure: {data}")
            raise RuntimeError("Malformed response from NVIDIA API") from e

        logger.debug(f"NvidiaClient response: {content[:200]}...")
        return content

    def simple_prompt(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Convenience wrapper for a single user-turn prompt."""
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            **kwargs,
        )


# Module-level default instance for easy import
default_client = NvidiaClient()
```

**Usage pattern throughout the codebase:**
```python
from core.nvidia_client import NvidiaClient

llm = NvidiaClient(temperature=0.1, max_tokens=1024)
result = llm.simple_prompt("Classify this symptom: chest pain radiating to left arm")
```

---

## 4. Neo4j Knowledge Graph Setup

**File:** `knowledge_graph/neo4j_client.py`

### 4.1 Node Types (Graph Schema)

The Neo4j graph encodes the medical-provider knowledge base as a property graph.

| Node Label | Key Properties | Purpose |
|---|---|---|
| `Symptom` | name, description, severity_hint | User-reported symptoms |
| `Condition` | icd10_code, icd10_label, snomed_code, category | Disease/diagnosis |
| `Procedure` | name, icd10_code, typical_duration_hrs, hospital_stay_days | Medical interventions |
| `Hospital` | id, name, city, tier, nabh, rating, lat, lon, bed_count | Provider nodes |
| `Doctor` | id, name, specialization, experience_yrs, rating | Individual practitioners |
| `City` | name, tier, geo_multiplier | Geographic node |
| `CostBenchmark` | procedure, city_tier, min_inr, max_inr, typical_inr | Pricing data |

### 4.2 Relationship Types

```
(Symptom)-[:INDICATES]->(Condition)
(Condition)-[:TREATED_BY]->(Procedure)
(Procedure)-[:PERFORMED_AT]->(Hospital)
(Hospital)-[:LOCATED_IN]->(City)
(Doctor)-[:PRACTICES_AT]->(Hospital)
(CostBenchmark)-[:BENCHMARKS]->(Procedure)
(CostBenchmark)-[:FOR_CITY]->(City)
```

### 4.3 Neo4j Client Implementation

```python
# knowledge_graph/neo4j_client.py

import os
from neo4j import GraphDatabase
from typing import List, Dict, Any

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USER", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "password"),
            ),
        )

    def close(self):
        self.driver.close()

    def run_query(self, cypher: str, params: dict = {}) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(cypher, **params)
            return [dict(record) for record in result]

    def find_conditions_for_symptoms(self, symptom_names: List[str]) -> List[Dict]:
        """Traverse symptom -> condition edges."""
        cypher = """
        MATCH (s:Symptom)-[:INDICATES]->(c:Condition)
        WHERE toLower(s.name) IN $symptom_names
        RETURN c.icd10_code AS icd10_code,
               c.icd10_label AS icd10_label,
               c.snomed_code AS snomed_code,
               c.category AS category,
               count(s) AS symptom_match_count
        ORDER BY symptom_match_count DESC
        LIMIT 5
        """
        return self.run_query(cypher, {"symptom_names": [s.lower() for s in symptom_names]})

    def find_procedures_for_condition(self, icd10_code: str) -> List[Dict]:
        """Traverse condition -> procedure edges."""
        cypher = """
        MATCH (c:Condition {icd10_code: $icd10_code})-[:TREATED_BY]->(p:Procedure)
        RETURN p.name AS procedure_name,
               p.icd10_code AS icd10_code,
               p.typical_duration_hrs AS duration_hrs,
               p.hospital_stay_days AS stay_days
        """
        return self.run_query(cypher, {"icd10_code": icd10_code})

    def find_hospitals_for_procedure_in_city(
        self, procedure_name: str, city: str, limit: int = 5
    ) -> List[Dict]:
        """Find hospitals that perform a procedure in a given city."""
        cypher = """
        MATCH (p:Procedure {name: $procedure_name})<-[:PERFORMED_AT]-(h:Hospital)-[:LOCATED_IN]->(ci:City)
        WHERE toLower(ci.name) = toLower($city)
        RETURN h.id AS id,
               h.name AS name,
               h.tier AS tier,
               h.nabh AS nabh_accredited,
               h.rating AS rating,
               h.bed_count AS bed_count,
               h.lat AS lat,
               h.lon AS lon,
               ci.geo_multiplier AS geo_multiplier
        ORDER BY h.rating DESC
        LIMIT $limit
        """
        return self.run_query(cypher, {
            "procedure_name": procedure_name,
            "city": city,
            "limit": limit
        })

    def get_cost_benchmark(self, procedure_name: str, city_tier: str) -> Dict:
        """Retrieve cost benchmarks for a procedure in a city tier."""
        cypher = """
        MATCH (cb:CostBenchmark)-[:BENCHMARKS]->(p:Procedure {name: $procedure_name})
        WHERE cb.city_tier = $city_tier
        RETURN cb.min_inr AS min_inr,
               cb.max_inr AS max_inr,
               cb.typical_inr AS typical_inr,
               cb.breakdown AS breakdown
        LIMIT 1
        """
        results = self.run_query(cypher, {
            "procedure_name": procedure_name,
            "city_tier": city_tier
        })
        return results[0] if results else {}
```

### 4.4 Schema Setup Script

**File:** `knowledge_graph/schema_setup.py`

Run once to create constraints and seed the graph.

```python
# knowledge_graph/schema_setup.py

from neo4j_client import Neo4jClient
import json

def create_constraints(client: Neo4jClient):
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Condition) REQUIRE c.icd10_code IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (h:Hospital) REQUIRE h.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Procedure) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ci:City) REQUIRE ci.name IS UNIQUE",
    ]
    for c in constraints:
        client.run_query(c)
    print("Constraints created.")

def seed_procedures(client: Neo4jClient):
    """Seed 12 core procedures from benchmark JSON."""
    with open("../data/procedure_benchmarks.json") as f:
        benchmarks = json.load(f)

    for proc in benchmarks:
        client.run_query("""
        MERGE (p:Procedure {name: $name})
        SET p.icd10_code = $icd10_code,
            p.typical_duration_hrs = $duration_hrs,
            p.hospital_stay_days = $stay_days
        """, proc)

        for tier, costs in proc["city_tier"].items():
            client.run_query("""
            MERGE (ci:City {name: $tier})
            SET ci.tier = $tier
            MERGE (cb:CostBenchmark {procedure: $name, city_tier: $tier})
            SET cb.min_inr = $min_inr,
                cb.max_inr = $max_inr,
                cb.typical_inr = $typical_inr
            MERGE (cb)-[:BENCHMARKS]->(p:Procedure {name: $name})
            MERGE (cb)-[:FOR_CITY]->(ci)
            """, {
                "name": proc["procedure"],
                "tier": tier,
                "min_inr": costs["min"],
                "max_inr": costs["max"],
                "typical_inr": costs["typical"]
            })

    print(f"Seeded {len(benchmarks)} procedures.")

if __name__ == "__main__":
    client = Neo4jClient()
    create_constraints(client)
    seed_procedures(client)
    client.close()
```

---

## 5. NER Pipeline & ICD-10 Ontology Integration

**File:** `nlp/ner_pipeline.py` and `nlp/icd10_mapper.py`

### 5.1 NER Pipeline

The NER pipeline uses **spaCy** with the `en_core_sci_sm` (scispaCy) model for biomedical entity
recognition, plus a custom rule-based matcher for Indian medical terminology.

```python
# nlp/ner_pipeline.py

import spacy
import re
from dataclasses import dataclass
from typing import List

@dataclass
class MedicalEntity:
    text: str
    label: str           # SYMPTOM | CONDITION | BODY_PART | PROCEDURE | DRUG
    start: int
    end: int
    normalized: str      # lowercased, stripped

class NERPipeline:
    """
    Extracts medical entities from free-text patient input.
    Uses scispaCy for biomedical NER + custom rule matcher.
    """

    # Custom symptom/procedure keywords for Indian context
    CUSTOM_SYMPTOMS = {
        "chest pain", "breathlessness", "shortness of breath",
        "radiating pain", "knee pain", "hip pain", "back pain",
        "blurred vision", "high fever", "low appetite", "fatigue",
        "swelling", "numbness", "palpitations", "dizziness",
    }

    CUSTOM_PROCEDURES = {
        "angioplasty", "bypass", "cabg", "knee replacement",
        "hip replacement", "cataract surgery", "dialysis",
        "chemotherapy", "lasik", "appendectomy", "cholecystectomy",
        "mri", "ct scan", "echocardiogram", "ecg", "ultrasound",
    }

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_sci_sm")
        except OSError:
            # Fallback to general English model
            self.nlp = spacy.load("en_core_web_sm")

    def extract(self, text: str) -> List[MedicalEntity]:
        """
        Extract medical entities from patient input text.
        Returns a deduplicated list of MedicalEntity objects.
        """
        doc = self.nlp(text.lower())
        entities: List[MedicalEntity] = []

        # spaCy / scispaCy entities
        for ent in doc.ents:
            if ent.label_ in {"DISEASE", "CHEMICAL", "PROCEDURE", "ANATOMY"}:
                label_map = {
                    "DISEASE": "CONDITION",
                    "CHEMICAL": "DRUG",
                    "ANATOMY": "BODY_PART",
                    "PROCEDURE": "PROCEDURE",
                }
                entities.append(MedicalEntity(
                    text=ent.text,
                    label=label_map.get(ent.label_, "SYMPTOM"),
                    start=ent.start_char,
                    end=ent.end_char,
                    normalized=ent.text.strip().lower(),
                ))

        # Custom rule-based matching
        text_lower = text.lower()
        for symptom in self.CUSTOM_SYMPTOMS:
            if symptom in text_lower:
                idx = text_lower.find(symptom)
                entities.append(MedicalEntity(
                    text=symptom, label="SYMPTOM",
                    start=idx, end=idx + len(symptom),
                    normalized=symptom,
                ))

        for procedure in self.CUSTOM_PROCEDURES:
            if procedure in text_lower:
                idx = text_lower.find(procedure)
                entities.append(MedicalEntity(
                    text=procedure, label="PROCEDURE",
                    start=idx, end=idx + len(procedure),
                    normalized=procedure,
                ))

        # Deduplicate by normalized text
        seen = set()
        unique = []
        for e in entities:
            if e.normalized not in seen:
                seen.add(e.normalized)
                unique.append(e)

        return unique
```

### 5.2 ICD-10 Mapper

```python
# nlp/icd10_mapper.py

import json
import os
from typing import Optional, Dict
from core.nvidia_client import NvidiaClient

class ICD10Mapper:
    """
    Maps extracted medical entity text to ICD-10 CM codes.
    Uses the 2022 ICD-10 CM JSON dataset as the controlled vocabulary.
    LLM is used for fuzzy matching when direct lookup fails.
    """

    def __init__(self, icd10_json_path: str = "data/icd10_2022.json"):
        self.llm = NvidiaClient(temperature=0.0, max_tokens=512)
        with open(icd10_json_path, encoding="utf-8") as f:
            raw = json.load(f)
        # Build a flat dict: {code: description}
        self.code_map: Dict[str, str] = self._flatten(raw)
        # Build reverse: {description_lower: code}
        self.desc_map: Dict[str, str] = {
            v.lower(): k for k, v in self.code_map.items()
        }
        print(f"ICD-10 mapper loaded: {len(self.code_map)} codes.")

    def _flatten(self, data, result=None):
        if result is None:
            result = {}
        if isinstance(data, dict):
            if "code" in data and "description" in data:
                result[data["code"]] = data["description"]
            for v in data.values():
                self._flatten(v, result)
        elif isinstance(data, list):
            for item in data:
                self._flatten(item, result)
        return result

    def lookup(self, term: str) -> Optional[Dict[str, str]]:
        """
        Step 1: Direct substring match in the description map.
        Step 2: LLM-assisted mapping if not found.
        Returns: {"code": "M17.11", "description": "Primary osteoarthritis, right knee"}
        """
        term_lower = term.lower().strip()

        # Direct match
        if term_lower in self.desc_map:
            code = self.desc_map[term_lower]
            return {"code": code, "description": self.code_map[code]}

        # Partial substring match
        for desc, code in self.desc_map.items():
            if term_lower in desc or desc in term_lower:
                return {"code": code, "description": self.code_map[code]}

        # LLM-assisted fuzzy mapping
        return self._llm_map(term)

    def _llm_map(self, term: str) -> Optional[Dict[str, str]]:
        """
        Use the NVIDIA LLM to suggest the best ICD-10 code for a given medical term.
        Returns structured output or None.
        """
        system_prompt = (
            "You are a medical coding assistant. Given a medical term or symptom, "
            "return ONLY the best matching ICD-10 CM code and its official description. "
            "Format: CODE|DESCRIPTION. Example: M17.11|Primary osteoarthritis, right knee. "
            "If unknown, return: UNKNOWN|unknown"
        )
        response = self.llm.simple_prompt(
            prompt=f"Find ICD-10 CM code for: {term}",
            system_prompt=system_prompt,
            temperature=0.0,
            max_tokens=100,
        )

        if "|" in response and "UNKNOWN" not in response.upper():
            parts = response.strip().split("|", 1)
            if len(parts) == 2:
                code, description = parts
                return {"code": code.strip(), "description": description.strip()}

        return None

    def batch_lookup(self, terms: list[str]) -> list[Dict]:
        """Map multiple terms and return all successful mappings."""
        results = []
        for term in terms:
            result = self.lookup(term)
            if result:
                results.append({"term": term, **result})
        return results
```

---

## 6. GraphRAG Engine

**File:** `knowledge_graph/graph_rag.py`

The GraphRAG engine combines deterministic Neo4j Cypher traversal with LLM-generated context,
then uses the NVIDIA LLM to generate the final response.

```python
# knowledge_graph/graph_rag.py

from knowledge_graph.neo4j_client import Neo4jClient
from nlp.ner_pipeline import NERPipeline
from nlp.icd10_mapper import ICD10Mapper
from core.nvidia_client import NvidiaClient
import json
from typing import Dict, Any

class GraphRAGEngine:
    """
    Hybrid GraphRAG: Cypher graph traversal + LLM synthesis.
    Flow: User query -> NER -> ICD-10 mapping -> Cypher -> LLM context enrichment.
    """

    def __init__(self):
        self.neo4j = Neo4jClient()
        self.ner = NERPipeline()
        self.icd_mapper = ICD10Mapper()
        self.llm = NvidiaClient(temperature=0.15, max_tokens=2048)

    def query(self, user_text: str, location: str, patient_profile: Dict = {}) -> Dict[str, Any]:
        """
        Main GraphRAG entry point.
        1. Extract entities via NER
        2. Map to ICD-10 codes
        3. Traverse Neo4j graph
        4. Enrich with LLM
        5. Return structured result

        Returns a dict matching the frontend's SEARCH_DATA schema.
        """
        # Step 1: NER
        entities = self.ner.extract(user_text)
        symptoms = [e.normalized for e in entities if e.label == "SYMPTOM"]
        procedures = [e.normalized for e in entities if e.label == "PROCEDURE"]

        # Step 2: Graph traversal
        conditions = []
        if symptoms:
            conditions = self.neo4j.find_conditions_for_symptoms(symptoms)

        # Step 3: ICD-10 map first condition or use direct procedure
        primary_icd10 = None
        primary_procedure = None

        if conditions:
            primary_icd10 = {
                "code": conditions[0]["icd10_code"],
                "label": conditions[0]["icd10_label"],
                "snomed_code": conditions[0].get("snomed_code", ""),
                "category": conditions[0]["category"],
            }
            proc_results = self.neo4j.find_procedures_for_condition(conditions[0]["icd10_code"])
            primary_procedure = proc_results[0]["procedure_name"] if proc_results else None

        elif procedures:
            # Direct procedure query (e.g., "knee replacement")
            icd_result = self.icd_mapper.lookup(procedures[0])
            primary_icd10 = {
                "code": icd_result["code"] if icd_result else "Z99.89",
                "label": icd_result["description"] if icd_result else procedures[0],
                "snomed_code": "",
                "category": "Surgical Procedure",
            }
            primary_procedure = procedures[0]

        # Step 4: Hospital discovery
        hospitals_raw = []
        if primary_procedure and location:
            hospitals_raw = self.neo4j.find_hospitals_for_procedure_in_city(
                primary_procedure, location, limit=5
            )

        # Step 5: LLM synthesis with enriched graph context
        graph_context = json.dumps({
            "entities": [e.__dict__ for e in entities],
            "conditions": conditions[:3],
            "procedure": primary_procedure,
            "icd10": primary_icd10,
            "hospitals_count": len(hospitals_raw),
        }, indent=2, default=str)

        system_prompt = self._build_system_prompt()
        user_message = f"""
Patient query: {user_text}
Location: {location}
Patient profile: {json.dumps(patient_profile)}

Graph context retrieved:
{graph_context}

Produce a response with embedded <SEARCH_DATA>{{...}}</SEARCH_DATA> block.
"""
        llm_response = self.llm.simple_prompt(
            prompt=user_message,
            system_prompt=system_prompt,
        )

        return {
            "llm_response": llm_response,
            "entities": entities,
            "icd10": primary_icd10,
            "procedure": primary_procedure,
            "hospitals_raw": hospitals_raw,
        }

    def _build_system_prompt(self) -> str:
        return """
You are HealthNav, an AI healthcare navigator for Indian patients in Tier 2/3 cities.
You NEVER diagnose. You provide DECISION SUPPORT ONLY.
You help users find hospitals, understand costs, and navigate healthcare options.

Rules:
1. ALWAYS end responses with: "This is decision support only — not medical advice."
2. Map ALL conditions to ICD-10 and SNOMED CT codes.
3. Show costs ONLY as ranges (min-max), NEVER a single number.
4. Include confidence scores (0.0-1.0) with all estimates.
5. If emergency keywords detected (chest pain, stroke, unconscious, severe bleeding),
   prepend <EMERGENCY>true</EMERGENCY>.
6. Return structured data inside <SEARCH_DATA>...</SEARCH_DATA> tags for hospital/cost queries.

SEARCH_DATA JSON must follow this exact schema and include all fields the frontend expects:
{ "emergency": false, "query_interpretation": "", "procedure": "",
  "icd10_code": "", "icd10_label": "", "snomed_code": "",
  "medical_category": "", "pathway": [], "mapping_confidence": 0.0,
  "location": "", "cost_estimate": {}, "hospitals": [], 
  "comorbidity_warnings": [], "data_sources": [] }
"""
```

---

## 7. LangChain Agentic AI & Multi-Turn Memory

**File:** `agents/healthcare_agent.py` and `agents/memory_manager.py`

### 7.1 Memory Manager (Session-Scoped)

```python
# agents/memory_manager.py

from langchain_core.chat_history import InMemoryChatMessageHistory
from typing import Dict

# Global session store — keyed by unique session_id
# This prevents cross-session state leakage in concurrent users
_session_store: Dict[str, InMemoryChatMessageHistory] = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """
    Retrieve or create an isolated message history for this session.
    IMPORTANT: Each session_id gets its own InMemoryChatMessageHistory instance.
    This prevents cross-talk between concurrent users.
    """
    if session_id not in _session_store:
        _session_store[session_id] = InMemoryChatMessageHistory()
    return _session_store[session_id]

def clear_session(session_id: str) -> None:
    """Clear conversation history for a session (on explicit reset)."""
    if session_id in _session_store:
        del _session_store[session_id]

def get_session_messages_as_dicts(session_id: str) -> list[dict]:
    """
    Export session messages in NVIDIA API format:
    [{"role": "user"|"assistant", "content": "..."}]
    """
    history = get_session_history(session_id)
    result = []
    for msg in history.messages:
        role = "user" if msg.type == "human" else "assistant"
        result.append({"role": role, "content": msg.content})
    return result

def add_user_message(session_id: str, content: str) -> None:
    get_session_history(session_id).add_user_message(content)

def add_ai_message(session_id: str, content: str) -> None:
    get_session_history(session_id).add_ai_message(content)
```

### 7.2 Healthcare Agent

```python
# agents/healthcare_agent.py

import json
import re
from typing import Dict, Any, Optional

from core.nvidia_client import NvidiaClient
from agents.memory_manager import (
    get_session_messages_as_dicts,
    add_user_message,
    add_ai_message,
)
from agents.severity_classifier import SeverityClassifier
from knowledge_graph.graph_rag import GraphRAGEngine
from engines.cost_engine import CostEngine
from engines.geo_pricing import GeoPricingEngine
from engines.comorbidity_engine import ComorbidityEngine
from engines.fusion_score import FusionScoreEngine


AGENT_SYSTEM_PROMPT = """
You are HealthNav — an AI-powered healthcare navigator for Indian patients.
You operate as a multi-turn conversational agent with memory of the full conversation.

YOUR CAPABILITIES:
- Find and rank hospitals for medical procedures
- Estimate treatment costs at component level (breakdown by procedure, stay, diagnostics, etc.)
- Explain treatment pathways in plain language
- Guide users on insurance and loan options
- Map symptoms/conditions to ICD-10 and SNOMED CT codes

STRICT RULES:
1. NEVER diagnose. NEVER prescribe. You assist decision-making only.
2. Always end your response with: "⚕ This is decision support only — consult a qualified doctor."
3. If emergency keywords present (chest pain, stroke, unconscious, heavy bleeding,
   can't breathe, severe pain, heart attack), start with <EMERGENCY>true</EMERGENCY>.
4. All cost figures: ranges only. Format: Rs X – Rs Y. Never a single number.
5. When user mentions a comorbidity (diabetes, hypertension, cardiac history, kidney disease),
   ALWAYS acknowledge it will affect cost estimates in the next message.
6. Include <SEARCH_DATA>{...}</SEARCH_DATA> for hospital/cost queries.
7. Use simple, jargon-free Hindi-English mix when helpful for Tier 2/3 city users.
8. Remember context: if user asked about knee replacement earlier, do not re-ask when
   they say "Will my diabetes affect this?" — infer from history.
"""


class HealthcareAgent:
    """
    Main conversational agent. Orchestrates NER, GraphRAG, cost engines,
    and the NVIDIA LLM to produce structured, memory-aware responses.
    """

    def __init__(self):
        self.llm = NvidiaClient(temperature=0.15, max_tokens=2048)
        self.severity_classifier = SeverityClassifier()
        self.graph_rag = GraphRAGEngine()
        self.cost_engine = CostEngine()
        self.geo_engine = GeoPricingEngine()
        self.comorbidity_engine = ComorbidityEngine()
        self.fusion_engine = FusionScoreEngine()

    def process(
        self,
        session_id: str,
        user_message: str,
        location: str = "",
        patient_profile: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Process a user message within a session context.
        Returns the full structured response for the frontend.
        """
        if patient_profile is None:
            patient_profile = {}

        # Step 1: Severity check FIRST — emergency override
        severity = self.severity_classifier.classify(user_message)

        # Step 2: Add user message to session memory
        add_user_message(session_id, user_message)

        # Step 3: Build message history for LLM
        history = get_session_messages_as_dicts(session_id)

        # Step 4: GraphRAG query
        rag_result = self.graph_rag.query(user_message, location, patient_profile)

        # Step 5: Apply cost engines if procedure identified
        cost_estimate = {}
        if rag_result.get("procedure") and location:
            city_tier = self.geo_engine.get_city_tier(location)
            base_cost = self.cost_engine.estimate(
                procedure=rag_result["procedure"],
                city_tier=city_tier,
            )
            geo_adjusted = self.geo_engine.apply_multiplier(base_cost, city_tier)
            final_cost = self.comorbidity_engine.adjust(
                geo_adjusted,
                comorbidities=patient_profile.get("comorbidities", []),
                age=patient_profile.get("age"),
            )
            cost_estimate = final_cost

        # Step 6: Score hospitals via fusion engine
        hospitals_scored = []
        if rag_result.get("hospitals_raw"):
            user_lat = patient_profile.get("lat")
            user_lon = patient_profile.get("lon")
            budget = patient_profile.get("budget_max")
            hospitals_scored = self.fusion_engine.score_and_rank(
                hospitals=rag_result["hospitals_raw"],
                procedure=rag_result.get("procedure", ""),
                user_lat=user_lat,
                user_lon=user_lon,
                budget_max=budget,
            )

        # Step 7: LLM final synthesis (full conversation history sent)
        enrichment_note = f"""
[AGENT CONTEXT INJECTION]
Severity: {severity}
Procedure: {rag_result.get('procedure')}
ICD-10: {rag_result.get('icd10', {})}
Hospitals found: {len(hospitals_scored)}
Cost estimate computed: {bool(cost_estimate)}
Patient comorbidities: {patient_profile.get('comorbidities', [])}
"""
        # Inject enrichment as a system note at end of history
        messages_for_llm = history[:-1]  # all except the last user message
        messages_for_llm.append({
            "role": "user",
            "content": history[-1]["content"] + "\n\n" + enrichment_note,
        })

        llm_narrative = self.llm.chat(
            messages=messages_for_llm,
            system_prompt=AGENT_SYSTEM_PROMPT,
        )

        # Step 8: Save AI response to memory
        add_ai_message(session_id, llm_narrative)

        # Step 9: Parse SEARCH_DATA from LLM response
        search_data = self._parse_search_data(llm_narrative)

        # Merge engine outputs into search_data
        if cost_estimate:
            search_data["cost_estimate"] = cost_estimate
        if hospitals_scored:
            search_data["hospitals"] = hospitals_scored
        if rag_result.get("icd10"):
            icd = rag_result["icd10"]
            search_data["icd10_code"] = icd.get("code", "")
            search_data["icd10_label"] = icd.get("label", "")
            search_data["snomed_code"] = icd.get("snomed_code", "")

        return {
            "session_id": session_id,
            "narrative": self._strip_search_data(llm_narrative),
            "search_data": search_data,
            "severity": severity,
            "is_emergency": severity == "RED",
        }

    def _parse_search_data(self, llm_text: str) -> Dict:
        match = re.search(r"<SEARCH_DATA>(.*?)</SEARCH_DATA>", llm_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        return {}

    def _strip_search_data(self, text: str) -> str:
        clean = re.sub(r"<SEARCH_DATA>.*?</SEARCH_DATA>", "", text, flags=re.DOTALL)
        clean = re.sub(r"<EMERGENCY>.*?</EMERGENCY>", "", clean, flags=re.DOTALL)
        return clean.strip()
```

---

## 8. Symptom Severity Classifier (Gap Resolver)

**File:** `agents/severity_classifier.py`

Classifies every user query as **RED** (Emergency), **YELLOW** (Urgent), or **GREEN** (Elective).
Uses the NVIDIA LLM with a strict prompt engineering approach and hard-coded keyword overrides.

```python
# agents/severity_classifier.py

import re
from core.nvidia_client import NvidiaClient

# Hard-coded emergency overrides — these always trigger RED regardless of LLM
EMERGENCY_KEYWORDS = {
    "chest pain", "heart attack", "stroke", "unconscious", "unresponsive",
    "heavy bleeding", "can't breathe", "cannot breathe", "shortness of breath sudden",
    "severe pain", "collapse", "collapsed", "paralysis", "sudden numbness",
    "vision loss", "loss of consciousness", "difficulty breathing",
    "radiating pain left arm", "jaw pain",
}

SEVERITY_SYSTEM_PROMPT = """
You are a medical triage classifier. Classify the patient's input into EXACTLY one of:
- RED: Life-threatening emergency requiring immediate care (call 112)
- YELLOW: Urgent, needs care within 24-48 hours
- GREEN: Elective, can be planned at convenience

Return ONLY the word RED, YELLOW, or GREEN. Nothing else.

Examples:
"chest pain radiating to left arm" -> RED
"severe headache and vomiting for 3 hours" -> YELLOW
"knee replacement cost in Nagpur" -> GREEN
"high fever for 2 days" -> YELLOW
"want to know about diabetes management" -> GREEN
"unconscious patient" -> RED
"""


class SeverityClassifier:
    """
    Two-stage symptom severity classifier:
    1. Hard-coded keyword check (instantaneous, overrides LLM)
    2. LLM-based classification for nuanced cases
    """

    def __init__(self):
        self.llm = NvidiaClient(temperature=0.0, max_tokens=10)

    def classify(self, user_text: str) -> str:
        """
        Returns "RED", "YELLOW", or "GREEN".
        RED always overrides all other logic.
        """
        text_lower = user_text.lower()

        # Stage 1: Keyword override
        for keyword in EMERGENCY_KEYWORDS:
            if keyword in text_lower:
                return "RED"

        # Stage 2: LLM classification
        try:
            response = self.llm.simple_prompt(
                prompt=f"Classify: {user_text}",
                system_prompt=SEVERITY_SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=10,
            )
            severity = response.strip().upper()
            if severity in {"RED", "YELLOW", "GREEN"}:
                return severity
        except Exception:
            pass

        return "GREEN"  # Safe default for elective queries
```

---

## 9. Treatment Pathway & Cost Engine (Gap 9)

**File:** `engines/pathway_engine.py` and `engines/cost_engine.py`

### 9.1 Pathway Engine

```python
# engines/pathway_engine.py

from core.nvidia_client import NvidiaClient
from typing import List, Dict
import json

PATHWAY_PROMPT = """
You are a clinical pathway expert for Indian hospitals.
Given a medical procedure name and ICD-10 code, output ONLY a valid JSON array
of pathway steps. No preamble, no markdown, just JSON.

Each step object:
{
  "step": 1,
  "name": "Pre-operative Assessment",
  "description": "Blood tests, ECG, imaging",
  "typical_duration": "1-2 days",
  "cost_range": {"min": 3000, "max": 10000},
  "responsible_party": "Diagnostics Lab / Hospital"
}

Follow this standard pathway structure:
1. Pre-procedure Diagnostics
2. Specialist Consultation
3. Core Procedure / Surgery
4. Hospital / ICU Stay
5. Post-procedure Monitoring
6. Discharge & Follow-up Care
"""


class PathwayEngine:
    """
    Generates clinical pathway steps for a given procedure.
    Costs are in INR (pre-geographic adjustment).
    """

    STATIC_PATHWAYS = {
        "angioplasty": [
            {"step": 1, "name": "Pre-Procedure Diagnostics",
             "description": "ECG, Stress Test, Echocardiogram, Diagnostic Angiography",
             "typical_duration": "1-2 days",
             "cost_range": {"min": 10000, "max": 30000}},
            {"step": 2, "name": "Surgical Procedure",
             "description": "Balloon Angioplasty / Stent Placement (Drug-Eluting Stent)",
             "typical_duration": "2-4 hours",
             "cost_range": {"min": 100000, "max": 250000}},
            {"step": 3, "name": "Hospital Stay (ICU + Ward)",
             "description": "ICU monitoring and General Ward recovery",
             "typical_duration": "3-5 days",
             "cost_range": {"min": 20000, "max": 60000}},
            {"step": 4, "name": "Post-Procedure Care",
             "description": "Anti-platelets, statins, follow-up consultations",
             "typical_duration": "6-8 weeks",
             "cost_range": {"min": 10000, "max": 30000}},
        ],
        "total knee arthroplasty": [
            {"step": 1, "name": "Pre-Surgical Evaluation",
             "description": "X-ray, MRI, blood panel, anesthesia review",
             "typical_duration": "2-3 days",
             "cost_range": {"min": 5000, "max": 15000}},
            {"step": 2, "name": "Surgery",
             "description": "Implant selection + surgery (conventional or robotic-assisted)",
             "typical_duration": "2-3 hours",
             "cost_range": {"min": 90000, "max": 200000}},
            {"step": 3, "name": "Hospital Stay",
             "description": "3-5 nights, physiotherapy begins Day 1",
             "typical_duration": "3-5 days",
             "cost_range": {"min": 25000, "max": 60000}},
            {"step": 4, "name": "Post-Operative Physiotherapy",
             "description": "6-12 weeks outpatient physiotherapy",
             "typical_duration": "6-12 weeks",
             "cost_range": {"min": 8000, "max": 20000}},
        ],
    }

    def __init__(self):
        self.llm = NvidiaClient(temperature=0.1, max_tokens=1024)

    def get_pathway(self, procedure: str, icd10_code: str = "") -> List[Dict]:
        """
        Return treatment pathway for a procedure.
        Uses static data for known procedures; falls back to LLM for others.
        """
        procedure_lower = procedure.lower().strip()

        # Check static pathways first (fastest + most reliable)
        for key, steps in self.STATIC_PATHWAYS.items():
            if key in procedure_lower or procedure_lower in key:
                return steps

        # LLM fallback for unknown procedures
        return self._generate_via_llm(procedure, icd10_code)

    def _generate_via_llm(self, procedure: str, icd10_code: str) -> List[Dict]:
        prompt = f"Generate pathway steps for: {procedure} (ICD-10: {icd10_code})"
        try:
            response = self.llm.simple_prompt(
                prompt=prompt,
                system_prompt=PATHWAY_PROMPT,
                temperature=0.1,
                max_tokens=1024,
            )
            # Strip markdown fences if present
            clean = response.strip().strip("```json").strip("```").strip()
            return json.loads(clean)
        except Exception:
            return []
```

### 9.2 Cost Engine

```python
# engines/cost_engine.py

import json
from typing import Dict

class CostEngine:
    """
    Generates component-level cost breakdowns for medical procedures.
    Costs are BASE rates (Tier 1 metro) before geographic adjustment.
    Structure mirrors the frontend CostBreakdown interface.
    """

    # Base benchmark data (INR, Tier 1 metro baseline)
    BASE_BENCHMARKS: Dict[str, Dict] = {
        "angioplasty": {
            "total": {"min": 120000, "max": 300000, "typical_min": 150000, "typical_max": 200000},
            "breakdown": {
                "procedure":     {"min": 100000, "max": 250000},
                "doctor_fees":   {"min": 15000,  "max": 30000},
                "hospital_stay": {"min": 20000,  "max": 60000,  "nights": "3-5"},
                "diagnostics":   {"min": 10000,  "max": 30000},
                "medicines":     {"min": 5000,   "max": 15000},
                "contingency":   {"min": 10000,  "max": 40000},
            },
        },
        "total knee arthroplasty": {
            "total": {"min": 150000, "max": 450000, "typical_min": 200000, "typical_max": 300000},
            "breakdown": {
                "procedure":     {"min": 90000,  "max": 200000},
                "doctor_fees":   {"min": 15000,  "max": 30000},
                "hospital_stay": {"min": 25000,  "max": 60000,  "nights": "4-6"},
                "diagnostics":   {"min": 8000,   "max": 15000},
                "medicines":     {"min": 5000,   "max": 12000},
                "contingency":   {"min": 10000,  "max": 30000},
            },
        },
        "cataract surgery": {
            "total": {"min": 15000, "max": 60000, "typical_min": 20000, "typical_max": 40000},
            "breakdown": {
                "procedure":     {"min": 10000, "max": 45000},
                "doctor_fees":   {"min": 2000,  "max": 8000},
                "hospital_stay": {"min": 0,     "max": 5000,  "nights": "0-1"},
                "diagnostics":   {"min": 1500,  "max": 5000},
                "medicines":     {"min": 1000,  "max": 3000},
                "contingency":   {"min": 500,   "max": 2000},
            },
        },
        "dialysis": {
            "total": {"min": 3000, "max": 8000, "typical_min": 4000, "typical_max": 6000},
            "breakdown": {
                "procedure":     {"min": 2000, "max": 5000},
                "doctor_fees":   {"min": 500,  "max": 1000},
                "hospital_stay": {"min": 0,    "max": 1000, "nights": "0"},
                "diagnostics":   {"min": 300,  "max": 800},
                "medicines":     {"min": 200,  "max": 500},
                "contingency":   {"min": 100,  "max": 500},
            },
        },
        "cabg": {
            "total": {"min": 150000, "max": 500000, "typical_min": 200000, "typical_max": 350000},
            "breakdown": {
                "procedure":     {"min": 100000, "max": 350000},
                "doctor_fees":   {"min": 25000,  "max": 60000},
                "hospital_stay": {"min": 40000,  "max": 100000, "nights": "7-10"},
                "diagnostics":   {"min": 15000,  "max": 40000},
                "medicines":     {"min": 10000,  "max": 25000},
                "contingency":   {"min": 20000,  "max": 80000},
            },
        },
    }

    def estimate(self, procedure: str, city_tier: str = "tier2") -> Dict:
        """
        Return the base cost estimate for a procedure.
        This is BEFORE geographic multiplier and comorbidity adjustments.
        """
        procedure_lower = procedure.lower().strip()

        # Find matching benchmark
        benchmark = None
        for key, data in self.BASE_BENCHMARKS.items():
            if key in procedure_lower or procedure_lower in key:
                benchmark = data
                break

        if not benchmark:
            # Generic estimate for unknown procedures
            benchmark = {
                "total": {"min": 20000, "max": 150000, "typical_min": 50000, "typical_max": 100000},
                "breakdown": {
                    "procedure":     {"min": 10000, "max": 80000},
                    "doctor_fees":   {"min": 3000,  "max": 15000},
                    "hospital_stay": {"min": 5000,  "max": 30000, "nights": "1-3"},
                    "diagnostics":   {"min": 1000,  "max": 10000},
                    "medicines":     {"min": 500,   "max": 5000},
                    "contingency":   {"min": 500,   "max": 10000},
                },
            }

        return {
            "procedure": procedure,
            "city_tier": city_tier,
            "confidence": 0.0,        # Filled by confidence engine later
            **benchmark,
        }
```

---

## 10. Geographic Pricing Adjustment (Gap 5)

**File:** `engines/geo_pricing.py`

```python
# engines/geo_pricing.py

from typing import Dict, Tuple

class GeoPricingEngine:
    """
    Applies geographic cost multipliers to base procedure estimates.
    Formula: Adjusted_Cost = Base_Cost × γ_geo
    Based on Kearney India Healthcare Index and multi-site cost studies.
    """

    # Tier classification: city_name_lower -> city_tier
    CITY_TIER_MAP = {
        # Metro (Tier 1) — multiplier 1.0 (baseline)
        "mumbai": "metro", "delhi": "metro", "bangalore": "metro",
        "bengaluru": "metro", "chennai": "metro", "kolkata": "metro",
        "hyderabad": "metro", "pune": "metro", "ahmedabad": "metro",

        # Tier 2 — multiplier 0.82
        "nagpur": "tier2", "raipur": "tier2", "bhopal": "tier2",
        "indore": "tier2", "nashik": "tier2", "aurangabad": "tier2",
        "surat": "tier2", "patna": "tier2", "lucknow": "tier2",
        "jaipur": "tier2", "bhubaneswar": "tier2", "coimbatore": "tier2",
        "vizag": "tier2", "visakhapatnam": "tier2",

        # Tier 3 — multiplier 0.65
        "bilaspur": "tier3", "korba": "tier3", "durg": "tier3",
        "bhilai": "tier3", "jabalpur": "tier3", "gwalior": "tier3",
        "ratlam": "tier3", "amravati": "tier3", "dhule": "tier3",
    }

    # Cost multipliers relative to metro baseline
    GEO_MULTIPLIERS = {
        "metro": 1.00,
        "tier2": 0.82,
        "tier3": 0.65,
    }

    # ICU bed-day cost benchmarks (INR/day) from multi-site study
    ICU_COST_PER_DAY = {
        "metro": 5534,
        "tier2": 5427,
        "tier3": 2638,
    }

    def get_city_tier(self, city: str) -> str:
        return self.CITY_TIER_MAP.get(city.lower().strip(), "tier2")

    def get_multiplier(self, city_tier: str) -> float:
        return self.GEO_MULTIPLIERS.get(city_tier, 0.82)

    def apply_multiplier(self, cost_estimate: Dict, city_tier: str) -> Dict:
        """
        Scale all cost components by the geographic multiplier.
        Returns a new cost estimate dict with adjusted values.
        """
        γ = self.get_multiplier(city_tier)
        adjusted = {"geo_multiplier": γ, "city_tier": city_tier}

        # Adjust total
        if "total" in cost_estimate:
            t = cost_estimate["total"]
            adjusted["total"] = {
                "min": round(t["min"] * γ),
                "max": round(t["max"] * γ),
                "typical_min": round(t.get("typical_min", t["min"]) * γ),
                "typical_max": round(t.get("typical_max", t["max"]) * γ),
            }

        # Adjust each breakdown component
        if "breakdown" in cost_estimate:
            adjusted["breakdown"] = {}
            for component, values in cost_estimate["breakdown"].items():
                adjusted["breakdown"][component] = {
                    "min": round(values["min"] * γ),
                    "max": round(values["max"] * γ),
                }
                if "nights" in values:
                    adjusted["breakdown"][component]["nights"] = values["nights"]

        adjusted["geo_adjustment"] = {
            "city_tier": city_tier,
            "multiplier": γ,
            "discount_vs_metro": round((1 - γ) * 100, 1),
        }

        return {**cost_estimate, **adjusted}
```

---

## 11. Age & Comorbidity Cost Adjustment (Gap 6)

**File:** `engines/comorbidity_engine.py`

```python
# engines/comorbidity_engine.py

from typing import Dict, List, Optional

class ComorbidityEngine:
    """
    Adjusts cost estimates for patient age and comorbidities.
    Formula: Final_Estimated_Cost = Adjusted_Cost × (1 + Σ ωᵢCᵢ)
    
    Comorbidity weights (ωᵢ) derived from epidemiological research:
    - ASCVD: 2.2x baseline cost uplift
    - Heart Failure: 3.3x
    - Kidney Disease: 2.7x
    - Diabetes Mellitus: elevates complication risk significantly
    """

    # Comorbidity weight: weight applied to contingency expansion
    COMORBIDITY_WEIGHTS = {
        "diabetes":             {"weight": 0.25, "icu_prob_uplift": 0.08},
        "hypertension":         {"weight": 0.10, "icu_prob_uplift": 0.03},
        "cardiac_history":      {"weight": 0.40, "icu_prob_uplift": 0.15},
        "heart_failure":        {"weight": 0.55, "icu_prob_uplift": 0.20},
        "kidney_disease":       {"weight": 0.40, "icu_prob_uplift": 0.12},
        "renal_disease":        {"weight": 0.40, "icu_prob_uplift": 0.12},
        "ascvd":                {"weight": 0.35, "icu_prob_uplift": 0.10},
        "obesity":              {"weight": 0.15, "icu_prob_uplift": 0.05},
        "copd":                 {"weight": 0.20, "icu_prob_uplift": 0.07},
    }

    # Age risk bands — add contingency uplift
    AGE_RISK = {
        (0,  40):  0.00,
        (40, 60):  0.05,
        (60, 70):  0.12,
        (70, 80):  0.20,
        (80, 120): 0.30,
    }

    def _age_weight(self, age: Optional[int]) -> float:
        if age is None:
            return 0.05  # Default moderate uplift when age unknown
        for (lo, hi), weight in self.AGE_RISK.items():
            if lo <= age < hi:
                return weight
        return 0.05

    def adjust(
        self,
        cost_estimate: Dict,
        comorbidities: List[str],
        age: Optional[int] = None,
    ) -> Dict:
        """
        Apply comorbidity and age adjustments to a geographically adjusted cost estimate.
        Returns the final estimate with risk_adjustments list for frontend display.
        """
        comorbidities_lower = [c.lower().strip().replace(" ", "_") for c in comorbidities]

        total_weight = self._age_weight(age)
        risk_adjustments = []

        for comorbidity in comorbidities_lower:
            if comorbidity in self.COMORBIDITY_WEIGHTS:
                w = self.COMORBIDITY_WEIGHTS[comorbidity]
                total_weight += w["weight"]
                risk_adjustments.append({
                    "factor": comorbidity,
                    "weight": w["weight"],
                    "icu_probability_uplift": w["icu_prob_uplift"],
                    "impact": self._impact_label(w["weight"]),
                })

        # Apply: Final = Adjusted_Cost × (1 + Σ ωᵢCᵢ)
        multiplier = 1 + total_weight
        adjusted = {}

        if "total" in cost_estimate:
            t = cost_estimate["total"]
            adjusted["total"] = {
                "min": round(t["min"] * multiplier),
                "max": round(t["max"] * multiplier),
                "typical_min": round(t.get("typical_min", t["min"]) * multiplier),
                "typical_max": round(t.get("typical_max", t["max"]) * multiplier),
            }

        if "breakdown" in cost_estimate:
            adjusted["breakdown"] = {}
            for component, values in cost_estimate["breakdown"].items():
                adjusted["breakdown"][component] = {
                    "min": round(values["min"] * multiplier),
                    "max": round(values["max"] * multiplier),
                }
                if "nights" in values:
                    adjusted["breakdown"][component]["nights"] = values["nights"]

        adjusted["comorbidity_multiplier"] = round(multiplier, 3)
        adjusted["risk_adjustments"] = risk_adjustments
        adjusted["comorbidity_warnings"] = [
            f"{ra['factor'].replace('_',' ').title()}: {ra['impact']}"
            for ra in risk_adjustments
        ]

        return {**cost_estimate, **adjusted}

    def _impact_label(self, weight: float) -> str:
        if weight >= 0.40:
            return "High cost impact — significantly increases complications risk"
        elif weight >= 0.20:
            return "Moderate cost impact — may require extended ICU stay"
        else:
            return "Low-moderate cost impact — increases monitoring requirements"
```

---

## 12. NBFC Loan Pre-Underwriting Engine (Gap 3)

**File:** `engines/loan_engine.py`

```python
# engines/loan_engine.py

from typing import Dict, List

INTEREST_RATES = {
    "low_risk":      {"range": (12.0, 13.0), "approval": "Very High"},
    "medium_risk":   {"range": (13.0, 15.0), "approval": "High (Conditional)"},
    "high_risk":     {"range": (15.0, 16.0), "approval": "Manual Review Required"},
    "critical_risk": {"range": (0, 0),        "approval": "Unlikely — Restructure First"},
}

class LoanEngine:
    """
    Automated NBFC healthcare loan pre-underwriting engine.
    Computes DTI ratio and assigns risk bands in milliseconds.
    Replaces the traditional 7-21 day manual TAT.

    DTI_Ratio = (Existing_EMIs + Proposed_Medical_EMI) / Gross_Monthly_Income × 100
    """

    LOAN_COVERAGE_RATIO = 0.80  # Loan covers 80% of total estimated cost
    TENURES_MONTHS = [12, 24, 36]

    def calculate_emi(self, principal: float, tenure_months: int, annual_rate: float) -> float:
        """Standard EMI formula: P × r × (1+r)^n / ((1+r)^n - 1)"""
        if annual_rate == 0:
            return principal / tenure_months
        monthly_rate = annual_rate / (12 * 100)
        n = tenure_months
        emi = principal * monthly_rate * ((1 + monthly_rate) ** n) / (((1 + monthly_rate) ** n) - 1)
        return round(emi)

    def evaluate(
        self,
        total_treatment_cost: float,
        gross_monthly_income: float,
        existing_emis: float,
    ) -> Dict:
        """
        Full pre-underwriting evaluation.
        Returns risk band, EMI options, and call-to-action for all tenures.
        """
        loan_amount = round(total_treatment_cost * self.LOAN_COVERAGE_RATIO)

        emi_options = []
        for tenure in self.TENURES_MONTHS:
            # Use median rate for initial display; actual rate depends on risk band
            median_rate = 14.0  # placeholder before risk classification
            emi = self.calculate_emi(loan_amount, tenure, median_rate)
            emi_options.append({
                "tenure_months": tenure,
                "emi_estimate": emi,
                "label": f"{tenure // 12} year{'s' if tenure > 12 else ''}",
            })

        # Evaluate for each tenure at different rates to find the best scenario
        results_by_tenure = {}
        for tenure in self.TENURES_MONTHS:
            for band_key, band_data in INTEREST_RATES.items():
                if band_data["range"][0] == 0:
                    continue
                rate = sum(band_data["range"]) / 2
                emi = self.calculate_emi(loan_amount, tenure, rate)
                dti = ((existing_emis + emi) / gross_monthly_income) * 100 if gross_monthly_income > 0 else 999
                results_by_tenure[f"{band_key}_{tenure}"] = {
                    "tenure_months": tenure,
                    "emi": emi,
                    "dti": round(dti, 1),
                    "rate": rate,
                }

        # Use standard 24-month tenure at median rate for primary DTI
        primary_emi = self.calculate_emi(loan_amount, 24, 14.0)
        primary_dti = ((existing_emis + primary_emi) / gross_monthly_income) * 100 if gross_monthly_income > 0 else 999

        risk_band = self._classify_dti(primary_dti)
        band_data = INTEREST_RATES[risk_band]

        # Recalculate EMI options with actual band interest rate
        actual_rate = sum(band_data["range"]) / 2 if band_data["range"][0] > 0 else 0
        final_emi_options = []
        for tenure in self.TENURES_MONTHS:
            if actual_rate > 0:
                emi = self.calculate_emi(loan_amount, tenure, actual_rate)
                dti_this = round(((existing_emis + emi) / gross_monthly_income) * 100, 1)
            else:
                emi = 0
                dti_this = primary_dti
            final_emi_options.append({
                "tenure_months": tenure,
                "emi": emi,
                "dti_at_this_tenure": dti_this,
            })

        return {
            "loan_amount": loan_amount,
            "treatment_cost": total_treatment_cost,
            "coverage_ratio": self.LOAN_COVERAGE_RATIO,
            "gross_monthly_income": gross_monthly_income,
            "existing_emis": existing_emis,
            "primary_dti": round(primary_dti, 1),
            "risk_band": risk_band,
            "risk_flag": self._risk_flag(primary_dti),
            "underwriting_assessment": band_data["approval"],
            "interest_rate_range": band_data["range"],
            "call_to_action": self._call_to_action(risk_band),
            "emi_options": final_emi_options,
        }

    def _classify_dti(self, dti: float) -> str:
        if dti < 30:
            return "low_risk"
        elif dti < 40:
            return "medium_risk"
        elif dti < 50:
            return "high_risk"
        return "critical_risk"

    def _risk_flag(self, dti: float) -> str:
        if dti < 30:   return "🟢 Low Risk"
        if dti < 40:   return "🟡 Medium Risk"
        if dti < 50:   return "🔴 High Risk"
        return "⛔ Critical Risk"

    def _call_to_action(self, risk_band: str) -> str:
        ctas = {
            "low_risk":      "Aap eligible hain — Apply Now",
            "medium_risk":   "Proceed with Standard Application",
            "high_risk":     "Flag for Manual Review",
            "critical_risk": "Recommend Alternate Financing",
        }
        return ctas[risk_band]
```

---

## 13. Insurance Cashless Integration (Gap 2)

**File:** `engines/insurance_engine.py`

```python
# engines/insurance_engine.py

from typing import Dict

class InsuranceEngine:
    """
    Objective arbitration layer for cashless insurance pre-authorization.
    Classifies hospitals into segments and predicts OOP expenses.
    Addresses the IRDAI 'cashless everywhere' initiative friction.
    """

    # Room rent capping thresholds by policy type (INR/day)
    ROOM_RENT_CAPS = {
        "basic":    1000,
        "standard": 3000,
        "premium":  6000,
        "no_cap":   999999,
    }

    # Hospital tier base room rates
    HOSPITAL_ROOM_RATES = {
        "budget":  {"general_ward": 800,  "semi_private": 1500, "private": 2500},
        "mid":     {"general_ward": 1500, "semi_private": 3000, "private": 5000},
        "premium": {"general_ward": 3000, "semi_private": 6000, "private": 10000},
    }

    def estimate_cashless_eligibility(
        self,
        hospital_tier: str,
        procedure_cost: Dict,
        policy_type: str,
        stay_nights: int,
        policy_sum_assured: float,
    ) -> Dict:
        """
        Estimate cashless pre-authorization likelihood and OOP exposure.
        """
        room_cap = self.ROOM_RENT_CAPS.get(policy_type, 3000)
        room_rates = self.HOSPITAL_ROOM_RATES.get(hospital_tier, self.HOSPITAL_ROOM_RATES["mid"])

        # Room rent OOP calculation
        actual_room_rate = room_rates["private"]
        room_oop = max(0, (actual_room_rate - room_cap) * stay_nights)

        # Total claim vs sum assured
        total_min = procedure_cost.get("total", {}).get("min", 0)
        total_max = procedure_cost.get("total", {}).get("max", 0)
        coverage_min = max(0, min(total_min - room_oop, policy_sum_assured))
        coverage_max = max(0, min(total_max - room_oop, policy_sum_assured))
        oop_min = total_min - coverage_min
        oop_max = total_max - coverage_max

        # Cashless approval likelihood
        if total_max <= policy_sum_assured * 0.7:
            cashless_likelihood = "High"
            approval_note = "Well within policy limits — pre-authorization likely within 4-6 hours."
        elif total_max <= policy_sum_assured:
            cashless_likelihood = "Moderate"
            approval_note = "Within limits but close to sum assured — attach all supporting documents."
        else:
            cashless_likelihood = "Low"
            approval_note = "Estimated cost exceeds sum assured — partial cashless + reimbursement likely."

        return {
            "hospital_tier": hospital_tier,
            "policy_type": policy_type,
            "room_rent_cap_per_day": room_cap,
            "actual_room_rate": actual_room_rate,
            "room_rent_oop_total": room_oop,
            "estimated_coverage_range": {"min": round(coverage_min), "max": round(coverage_max)},
            "estimated_oop_range": {"min": round(oop_min), "max": round(oop_max)},
            "cashless_likelihood": cashless_likelihood,
            "approval_note": approval_note,
            "documents_required": [
                "Policy document + health card",
                "Doctor's prescription / referral",
                "Hospital admission form",
                "Pre-authorization request form",
                "Photo ID (Aadhar)",
            ],
        }
```

---

## 14. Sentiment Analysis — ABSA Pipeline (Gap 1)

**File:** `nlp/sentiment_absa.py`

```python
# nlp/sentiment_absa.py

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Dict
import re

class ABSAPipeline:
    """
    Aspect-Based Sentiment Analysis on patient reviews.
    Uses VADER for compound sentiment scoring + keyword-based aspect extraction.
    Four aspects: Doctors' Services, Staff's Services, Hospital Facilities, Affordability.
    """

    ASPECT_KEYWORDS = {
        "doctors_services": [
            "doctor", "surgeon", "physician", "specialist", "consultation",
            "diagnosis", "treatment", "expertise", "bedside", "competent",
            "experience", "knowledgeable", "listened", "explained",
        ],
        "staff_services": [
            "nurse", "staff", "attendant", "reception", "admin", "responsive",
            "helpful", "rude", "slow", "efficient", "friendly", "care",
            "supportive", "attentive",
        ],
        "hospital_facilities": [
            "clean", "hygiene", "equipment", "room", "ward", "icu", "bed",
            "infrastructure", "modern", "outdated", "crowded", "spacious",
            "parking", "cafeteria", "ambience",
        ],
        "affordability": [
            "cost", "price", "bill", "expensive", "cheap", "affordable",
            "transparent", "hidden charges", "overcharged", "value",
            "insurance", "cashless", "payment",
        ],
    }

    # VADER thresholds
    POSITIVE_THRESHOLD = 0.05
    NEGATIVE_THRESHOLD = -0.05

    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()

    def analyze_review(self, review_text: str) -> Dict[str, Dict]:
        """
        Analyze a single review and return sentiment per aspect.
        """
        sentences = self._split_sentences(review_text)
        aspect_sentiments = {aspect: [] for aspect in self.ASPECT_KEYWORDS}

        for sentence in sentences:
            sentence_lower = sentence.lower()
            matched_aspect = None
            max_matches = 0

            # Assign sentence to the aspect with most keyword matches
            for aspect, keywords in self.ASPECT_KEYWORDS.items():
                matches = sum(1 for kw in keywords if kw in sentence_lower)
                if matches > max_matches:
                    max_matches = matches
                    matched_aspect = aspect

            if matched_aspect and max_matches > 0:
                scores = self.vader.polarity_scores(sentence)
                aspect_sentiments[matched_aspect].append(scores["compound"])

        # Aggregate per aspect
        result = {}
        for aspect, scores in aspect_sentiments.items():
            if scores:
                avg = sum(scores) / len(scores)
                result[aspect] = {
                    "score": round(avg, 3),
                    "label": self._label(avg),
                    "mention_count": len(scores),
                }
            else:
                result[aspect] = {"score": 0, "label": "neutral", "mention_count": 0}

        return result

    def analyze_batch(self, reviews: List[str]) -> Dict:
        """
        Analyze a batch of reviews and return aggregated hospital sentiment report.
        """
        all_aspect_scores = {aspect: [] for aspect in self.ASPECT_KEYWORDS}

        for review in reviews:
            result = self.analyze_review(review)
            for aspect, data in result.items():
                if data["mention_count"] > 0:
                    all_aspect_scores[aspect].append(data["score"])

        overall_scores = []
        aggregated = {}
        for aspect, scores in all_aspect_scores.items():
            if scores:
                avg = sum(scores) / len(scores)
                overall_scores.append(avg)
                aggregated[aspect] = {
                    "avg_score": round(avg, 3),
                    "label": self._label(avg),
                    "positive_pct": round(
                        sum(1 for s in scores if s >= self.POSITIVE_THRESHOLD) / len(scores) * 100
                    ),
                    "mention_count": len(scores),
                }
            else:
                aggregated[aspect] = {
                    "avg_score": 0, "label": "neutral",
                    "positive_pct": 50, "mention_count": 0
                }

        overall_avg = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        reputation_score = round((overall_avg + 1) / 2 * 100)  # Map [-1,1] to [0,100]

        return {
            "reputation_score": reputation_score,
            "overall_sentiment": self._label(overall_avg),
            "overall_positive_pct": round(
                sum(1 for s in overall_scores if s >= self.POSITIVE_THRESHOLD)
                / len(overall_scores) * 100 if overall_scores else 50
            ),
            "aspects": aggregated,
        }

    def _split_sentences(self, text: str) -> List[str]:
        return [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 10]

    def _label(self, score: float) -> str:
        if score >= self.POSITIVE_THRESHOLD:
            return "positive"
        elif score <= self.NEGATIVE_THRESHOLD:
            return "negative"
        return "neutral"
```

---

## 15. Appointment Availability Proxy (Gap 4)

**File:** `engines/availability_proxy.py`

```python
# engines/availability_proxy.py

from typing import Dict

class AvailabilityProxy:
    """
    Calculates appointment wait-time proxies using queuing theory principles.
    No real-time API needed — uses structural hospital data (beds, specialists, turnover).
    
    Outputs human-readable approximations, not abstract numbers.
    """

    def estimate(
        self,
        total_beds: int,
        specialists_in_department: int,
        has_emergency_unit: bool,
        bed_occupancy_rate: float = 0.75,
        hospital_tier: str = "mid",
    ) -> Dict:
        """
        Args:
            total_beds: Total hospital bed count
            specialists_in_department: Number of relevant specialists
            has_emergency_unit: Whether hospital has 24/7 emergency/trauma
            bed_occupancy_rate: Fraction of beds typically occupied (0-1)
            hospital_tier: "premium" | "mid" | "budget"

        Returns:
            Dict with wait_category, display_text, and supporting details
        """

        # Emergency override
        if has_emergency_unit:
            return {
                "wait_category": "emergency",
                "display_text": "24/7 emergency available ✅",
                "avg_wait_days": 0,
                "throughput": "immediate",
            }

        # Compute throughput score (higher = lower wait)
        capacity_score = (total_beds / 200) * 0.5 + (specialists_in_department / 5) * 0.5
        availability_factor = 1 - bed_occupancy_rate  # Free bed ratio

        throughput = capacity_score * availability_factor

        if throughput >= 0.4 and specialists_in_department >= 4:
            return {
                "wait_category": "low_wait",
                "display_text": "Appointments usually available within 2-3 days",
                "avg_wait_days": 2,
                "throughput": "High Throughput / Low Queue",
            }
        elif throughput >= 0.2 or specialists_in_department >= 2:
            return {
                "wait_category": "medium_wait",
                "display_text": "Estimated waiting time: 4-7 days",
                "avg_wait_days": 5,
                "throughput": "Medium Throughput / Moderate Queue",
            }
        else:
            return {
                "wait_category": "high_wait",
                "display_text": "Waiting time: 1-2 weeks",
                "avg_wait_days": 10,
                "throughput": "Low Throughput / High Queue",
            }
```

---

## 16. Multi-Source Data Fusion Score (Gap 7)

**File:** `engines/fusion_score.py`

```python
# engines/fusion_score.py

import math
from typing import List, Dict, Optional
from geo.distance_calc import haversine_km
from engines.availability_proxy import AvailabilityProxy

class FusionScoreEngine:
    """
    Aggregates Clinical, Reputation, Accessibility, and Affordability signals
    into a single normalized Multi-Source Data Fusion Score (0-1).

    Weights:
    Clinical:      40%
    Reputation:    25%
    Accessibility: 20%
    Affordability: 15%

    Uses min-max normalization and sigmoid mapping to prevent any single
    extreme metric from dominating.
    """

    WEIGHTS = {
        "clinical":      0.40,
        "reputation":    0.25,
        "accessibility": 0.20,
        "affordability": 0.15,
    }

    def __init__(self):
        self.availability_proxy = AvailabilityProxy()

    def _min_max_normalize(self, value: float, min_val: float, max_val: float) -> float:
        if max_val == min_val:
            return 0.5
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    def _sigmoid(self, x: float, k: float = 5.0) -> float:
        """Sigmoid mapping for smooth normalization."""
        return 1 / (1 + math.exp(-k * (x - 0.5)))

    def _clinical_score(self, hospital: Dict, procedure: str) -> float:
        """
        Assesses specialization relevance, NABH accreditation, and procedure volume proxy.
        """
        score = 0.0
        specializations = [s.lower() for s in hospital.get("specializations", [])]
        procedure_lower = procedure.lower()

        # Specialization match
        for spec in specializations:
            if any(word in spec for word in procedure_lower.split()):
                score += 0.5
                break

        # NABH accreditation bonus
        if hospital.get("nabh_accredited", False):
            score += 0.3

        # Bed count proxy for volume (large hospitals = higher procedure volume)
        beds = hospital.get("bed_count", 100)
        volume_score = self._min_max_normalize(beds, 50, 500)
        score += volume_score * 0.2

        return min(1.0, score)

    def _reputation_score(self, hospital: Dict) -> float:
        """
        Fuses public star ratings + ABSA sentiment score.
        """
        rating = hospital.get("rating", 3.0)
        rating_normalized = self._min_max_normalize(rating, 1.0, 5.0)

        sentiment = hospital.get("sentiment", {})
        absa_score = sentiment.get("reputation_score", 50) / 100.0

        return (rating_normalized * 0.55) + (absa_score * 0.45)

    def _accessibility_score(
        self,
        hospital: Dict,
        user_lat: Optional[float],
        user_lon: Optional[float],
    ) -> float:
        """
        Combines geographic distance with appointment availability proxy.
        """
        # Distance component
        if user_lat and user_lon and hospital.get("lat") and hospital.get("lon"):
            dist_km = haversine_km(user_lat, user_lon, hospital["lat"], hospital["lon"])
            dist_score = self._min_max_normalize(dist_km, 0, 50)
            dist_score = 1.0 - dist_score  # Invert: shorter = better
        else:
            dist_score = 0.5  # Neutral when no location

        # Availability proxy component
        avail = self.availability_proxy.estimate(
            total_beds=hospital.get("bed_count", 100),
            specialists_in_department=hospital.get("specialists_count", 2),
            has_emergency_unit=hospital.get("has_emergency", False),
            hospital_tier=hospital.get("tier", "mid"),
        )
        wait_score = {
            "emergency": 1.0,
            "low_wait": 0.85,
            "medium_wait": 0.55,
            "high_wait": 0.25,
        }.get(avail["wait_category"], 0.5)

        return (dist_score * 0.6) + (wait_score * 0.4)

    def _affordability_score(self, hospital: Dict, budget_max: Optional[float]) -> float:
        """
        Measures alignment with patient budget + pricing transparency.
        """
        cost_min = hospital.get("cost_range", {}).get("min", 0)
        cost_max = hospital.get("cost_range", {}).get("max", 999999)
        cost_typical = (cost_min + cost_max) / 2

        if budget_max and budget_max > 0:
            if cost_typical <= budget_max:
                within_budget_score = 1.0
            elif cost_min <= budget_max:
                within_budget_score = 0.6
            else:
                within_budget_score = max(0.1, 1 - (cost_typical - budget_max) / budget_max)
        else:
            # Tier-based affordability when no budget specified
            tier_scores = {"budget": 0.9, "mid": 0.7, "premium": 0.4}
            within_budget_score = tier_scores.get(hospital.get("tier", "mid"), 0.7)

        # NABH cashless insurance track record bonus
        cashless_bonus = 0.1 if hospital.get("nabh_accredited", False) else 0.0

        return min(1.0, within_budget_score + cashless_bonus)

    def compute_score(
        self,
        hospital: Dict,
        procedure: str,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        budget_max: Optional[float] = None,
    ) -> Dict:
        """Compute full fusion score for a single hospital."""
        clinical = self._clinical_score(hospital, procedure)
        reputation = self._reputation_score(hospital)
        accessibility = self._accessibility_score(hospital, user_lat, user_lon)
        affordability = self._affordability_score(hospital, budget_max)

        fusion = (
            clinical      * self.WEIGHTS["clinical"] +
            reputation    * self.WEIGHTS["reputation"] +
            accessibility * self.WEIGHTS["accessibility"] +
            affordability * self.WEIGHTS["affordability"]
        )

        return {
            **hospital,
            "rank_score": round(fusion, 3),
            "rank_signals": {
                "clinical_capability": round(clinical * 100),
                "reputation": round(reputation * 100),
                "accessibility": round(accessibility * 100),
                "affordability": round(affordability * 100),
            },
            "confidence": round(fusion, 2),
        }

    def score_and_rank(
        self,
        hospitals: List[Dict],
        procedure: str,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        budget_max: Optional[float] = None,
    ) -> List[Dict]:
        """Score and rank all hospitals. Returns list sorted by rank_score descending."""
        scored = [
            self.compute_score(h, procedure, user_lat, user_lon, budget_max)
            for h in hospitals
        ]
        return sorted(scored, key=lambda h: h["rank_score"], reverse=True)
```

---

## 17. Hospital Comparison Engine (Gap 8)

**File:** `engines/comparison_engine.py`

```python
# engines/comparison_engine.py

from typing import List, Dict

class ComparisonEngine:
    """
    Side-by-side hospital comparison logic.
    Computes 'Best Value' badge and highlights meaningful differences.
    """

    def compare(self, hospitals: List[Dict]) -> Dict:
        """
        Compare 2-3 hospitals and return a structured comparison matrix.
        """
        assert 2 <= len(hospitals) <= 3, "Compare requires 2-3 hospitals."

        comparison_rows = []
        attributes = [
            ("name", "Hospital Name"),
            ("rating", "Rating (out of 5)"),
            ("nabh_accredited", "NABH Accredited"),
            ("tier", "Hospital Tier"),
            ("distance_km", "Distance"),
            ("cost_range", "Estimated Cost Range"),
            ("confidence", "Recommendation Confidence"),
            ("rank_signals.clinical_capability", "Clinical Score"),
            ("rank_signals.reputation", "Reputation Score"),
            ("rank_signals.accessibility", "Accessibility Score"),
            ("rank_signals.affordability", "Affordability Score"),
            ("has_icu", "ICU Available"),
            ("has_emergency", "24/7 Emergency"),
        ]

        for attr_key, attr_label in attributes:
            row = {"attribute": attr_label, "values": [], "highlight": False}
            values = []
            for h in hospitals:
                # Handle nested keys like "rank_signals.clinical_capability"
                if "." in attr_key:
                    parts = attr_key.split(".")
                    val = h
                    for part in parts:
                        val = val.get(part, "N/A") if isinstance(val, dict) else "N/A"
                else:
                    val = h.get(attr_key, "N/A")

                # Format values for display
                if attr_key == "cost_range":
                    val = f"Rs {val.get('min', 0):,} – Rs {val.get('max', 0):,}"
                elif attr_key == "distance_km":
                    val = f"{val:.1f} km" if isinstance(val, (int, float)) else val
                elif attr_key == "nabh_accredited" or attr_key in ("has_icu", "has_emergency"):
                    val = "✅ Yes" if val else "❌ No"
                elif attr_key in ("confidence",):
                    val = f"{int(val * 100)}%"
                elif attr_key.startswith("rank_signals."):
                    val = f"{val}/100"

                values.append(val)

            row["values"] = values

            # Highlight rows where values differ significantly
            if len(set(str(v) for v in values)) > 1:
                row["highlight"] = True

            comparison_rows.append(row)

        # Best Value badge — composite formula
        best_value_idx = self._find_best_value(hospitals)

        return {
            "hospitals": [h.get("name", "Unknown") for h in hospitals],
            "comparison_rows": comparison_rows,
            "best_value_hospital": hospitals[best_value_idx].get("name"),
            "best_value_index": best_value_idx,
            "best_value_rationale": self._best_value_rationale(hospitals[best_value_idx]),
        }

    def _find_best_value(self, hospitals: List[Dict]) -> int:
        """
        Best Value = (Rating × 0.4) + (1/CostMidpoint_normalized × 0.3) + (Confidence × 0.3)
        """
        scores = []
        costs = [
            (h.get("cost_range", {}).get("min", 0) + h.get("cost_range", {}).get("max", 0)) / 2
            for h in hospitals
        ]
        max_cost = max(costs) if costs else 1

        for i, h in enumerate(hospitals):
            rating_score = h.get("rating", 0) / 5.0
            cost_score = 1 - (costs[i] / max_cost)  # Invert: lower cost = higher score
            confidence_score = h.get("confidence", 0)
            composite = (rating_score * 0.4) + (cost_score * 0.3) + (confidence_score * 0.3)
            scores.append(composite)

        return scores.index(max(scores))

    def _best_value_rationale(self, hospital: Dict) -> str:
        tier = hospital.get("tier", "mid")
        rating = hospital.get("rating", 0)
        nabh = hospital.get("nabh_accredited", False)
        parts = []
        if rating >= 4.0:
            parts.append(f"High patient rating ({rating}★)")
        if nabh:
            parts.append("NABH accredited")
        if tier == "budget":
            parts.append("Lowest cost tier")
        elif tier == "mid":
            parts.append("Best cost-quality balance")
        return " · ".join(parts) if parts else "Best composite score"
```

---

## 18. Geo-Spatial Intelligence

**File:** `geo/geocoder.py` and `geo/distance_calc.py`

```python
# geo/geocoder.py

import os
from geopy.geocoders import Nominatim, GoogleV3
from geopy.exc import GeocoderTimedOut
from typing import Optional, Dict

class Geocoder:
    """
    Resolves city names, neighborhoods, or pin codes to lat/lon coordinates.
    Primary: Nominatim (free, no API key needed)
    Fallback: GoogleV3 (requires GOOGLE_MAPS_KEY in env)
    """

    def __init__(self):
        self.nominatim = Nominatim(
            user_agent=os.getenv("NOMINATIM_USER_AGENT", "tenzorx_healthnav/1.0")
        )
        google_key = os.getenv("GOOGLE_MAPS_KEY")
        self.google = GoogleV3(api_key=google_key) if google_key else None

    def geocode(self, location_string: str) -> Optional[Dict]:
        """
        Returns {"lat": float, "lon": float, "display_name": str} or None.
        Adds ", India" suffix for better accuracy with Indian city names.
        """
        query = f"{location_string}, India"
        try:
            location = self.nominatim.geocode(query, timeout=10)
            if location:
                return {
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "display_name": location.address,
                }
        except GeocoderTimedOut:
            pass

        # Fallback to Google
        if self.google:
            try:
                location = self.google.geocode(query, timeout=10)
                if location:
                    return {
                        "lat": location.latitude,
                        "lon": location.longitude,
                        "display_name": location.address,
                    }
            except Exception:
                pass

        return None
```

```python
# geo/distance_calc.py

import math

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance (km) between two lat/lon coordinates.
    Uses the Haversine formula.
    """
    R = 6371.0  # Earth's radius in km
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)
```

---

## 19. Explainable AI — LIME & SHAP

**File:** `xai/shap_explainer.py` and `xai/lime_explainer.py`

### 19.1 SHAP — Fusion Score Attribution

```python
# xai/shap_explainer.py

import shap
import numpy as np
import pandas as pd
from typing import Dict, List

class FusionSHAPExplainer:
    """
    Explains the Multi-Source Data Fusion Score using SHAP.
    Generates waterfall plot data for the frontend to visualize.
    """

    FEATURE_NAMES = ["clinical_capability", "reputation", "accessibility", "affordability"]
    WEIGHTS = [0.40, 0.25, 0.20, 0.15]

    def explain(self, hospital: Dict) -> Dict:
        """
        Generate SHAP-style contribution explanation for a hospital's fusion score.
        Returns data suitable for rendering a waterfall chart.
        """
        signals = hospital.get("rank_signals", {})
        raw_scores = np.array([
            signals.get("clinical_capability", 50) / 100.0,
            signals.get("reputation", 50) / 100.0,
            signals.get("accessibility", 50) / 100.0,
            signals.get("affordability", 50) / 100.0,
        ])
        weights = np.array(self.WEIGHTS)
        contributions = raw_scores * weights

        base_value = 0.5  # Average expected score (baseline)
        final_score = float(np.sum(contributions))

        waterfall_data = []
        running_total = base_value
        for i, (feature, contribution) in enumerate(zip(self.FEATURE_NAMES, contributions)):
            delta = contribution - (weights[i] * 0.5)  # Relative to average contribution
            waterfall_data.append({
                "feature": feature.replace("_", " ").title(),
                "raw_score": round(float(raw_scores[i] * 100)),
                "weight": self.WEIGHTS[i],
                "contribution": round(float(contribution), 4),
                "delta_from_baseline": round(float(delta), 4),
                "direction": "positive" if delta >= 0 else "negative",
                "running_total": round(running_total + delta, 3),
            })
            running_total += delta

        return {
            "hospital_id": hospital.get("id"),
            "hospital_name": hospital.get("name"),
            "base_value": base_value,
            "final_score": round(final_score, 3),
            "waterfall": waterfall_data,
            "summary": self._generate_summary(hospital, waterfall_data),
        }

    def _generate_summary(self, hospital: Dict, waterfall: List[Dict]) -> str:
        positives = [w["feature"] for w in waterfall if w["direction"] == "positive"]
        negatives = [w["feature"] for w in waterfall if w["direction"] == "negative"]
        msg = f"{hospital.get('name')} ranks here because "
        if positives:
            msg += f"its {' and '.join(positives)} pushed the score up"
        if negatives:
            msg += f", while {' and '.join(negatives)} slightly reduced it"
        return msg + "."
```

### 19.2 LIME — Severity Classifier Explanation

```python
# xai/lime_explainer.py

from core.nvidia_client import NvidiaClient
from typing import Dict, List
import json

class SeverityLIMEExplainer:
    """
    Explains why a query was classified as RED/YELLOW/GREEN using LIME-style
    text perturbation. Identifies which tokens triggered the classification.
    """

    def __init__(self):
        self.llm = NvidiaClient(temperature=0.0, max_tokens=512)

    def explain(self, user_text: str, classification: str) -> Dict:
        """
        Perturb input text and identify which terms drove the severity classification.
        Returns a list of highlighted tokens with their influence direction.
        """
        system_prompt = """
You are an AI explainability engine. Given a medical query and its triage classification,
identify which specific words or phrases most strongly drove that classification.
Return ONLY valid JSON with this structure (no markdown, no preamble):
{
  "key_terms": [
    {"term": "chest pain", "influence": "high", "direction": "increases_severity"},
    {"term": "walking", "influence": "low", "direction": "neutral"}
  ],
  "explanation": "One sentence plain-language explanation."
}
Directions: "increases_severity" | "decreases_severity" | "neutral"
Influence: "high" | "medium" | "low"
"""
        prompt = f"""
Query: "{user_text}"
Classification: {classification}

Which terms drove this classification?
"""
        try:
            response = self.llm.simple_prompt(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.0,
                max_tokens=512,
            )
            clean = response.strip().strip("```json").strip("```").strip()
            return json.loads(clean)
        except Exception:
            return {
                "key_terms": [],
                "explanation": f"Query classified as {classification} based on clinical content.",
            }
```

---

## 20. RAG Confidence Scoring System

**File:** `confidence/rag_confidence.py`

```python
# confidence/rag_confidence.py

from core.nvidia_client import NvidiaClient
from typing import Dict
import json

class RAGConfidenceScorer:
    """
    Computes a composite confidence score for each LLM + RAG response.
    Formula: S = 0.4 × Faithfulness + 0.3 × Contextual_Relevancy + 0.3 × Answer_Relevancy
    
    Score < 0.40 triggers UI uncertainty indicator + mandatory disclaimer.
    """

    SAFETY_THRESHOLD = 0.40
    WEIGHTS = {"faithfulness": 0.40, "contextual_relevancy": 0.30, "answer_relevancy": 0.30}

    def __init__(self):
        self.llm = NvidiaClient(temperature=0.0, max_tokens=256)

    def score(
        self,
        user_query: str,
        retrieved_context: str,
        llm_response: str,
    ) -> Dict:
        """
        Evaluate RAG output quality on three dimensions.
        Returns composite score and per-dimension breakdown.
        """
        system_prompt = """
You are a RAG evaluation judge. Score the following on three dimensions from 0.0 to 1.0.
Return ONLY valid JSON (no markdown):
{
  "faithfulness": 0.0,        // Is the response grounded in retrieved context?
  "contextual_relevancy": 0.0, // Did retrieved context match the user's query?
  "answer_relevancy": 0.0,    // Does the answer directly address the query?
  "rationale": "One sentence."
}
"""
        prompt = f"""
User Query: {user_query}

Retrieved Context: {retrieved_context[:1000]}

LLM Response: {llm_response[:1000]}

Score these three dimensions:
"""
        try:
            response = self.llm.simple_prompt(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.0,
                max_tokens=256,
            )
            clean = response.strip().strip("```json").strip("```").strip()
            scores = json.loads(clean)

            faithfulness = float(scores.get("faithfulness", 0.5))
            contextual   = float(scores.get("contextual_relevancy", 0.5))
            answer       = float(scores.get("answer_relevancy", 0.5))

            composite = (
                faithfulness * self.WEIGHTS["faithfulness"] +
                contextual   * self.WEIGHTS["contextual_relevancy"] +
                answer       * self.WEIGHTS["answer_relevancy"]
            )

            return {
                "composite_score": round(composite, 3),
                "faithfulness": round(faithfulness, 3),
                "contextual_relevancy": round(contextual, 3),
                "answer_relevancy": round(answer, 3),
                "rationale": scores.get("rationale", ""),
                "below_threshold": composite < self.SAFETY_THRESHOLD,
                "show_uncertainty_indicator": composite < self.SAFETY_THRESHOLD,
                "label": self._label(composite),
            }

        except Exception:
            # Safe fallback — moderate confidence
            return {
                "composite_score": 0.60,
                "faithfulness": 0.60,
                "contextual_relevancy": 0.60,
                "answer_relevancy": 0.60,
                "rationale": "Score unavailable",
                "below_threshold": False,
                "show_uncertainty_indicator": False,
                "label": "Moderate",
            }

    def _label(self, score: float) -> str:
        if score >= 0.70: return "High"
        if score >= 0.40: return "Moderate"
        return "Low"
```

---

## 21. FastAPI Route Definitions

**File:** `main.py` and `api/routes/*.py`

### 21.1 Main App

```python
# main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chat, hospitals, cost, loan, compare, explain

app = FastAPI(
    title="TenzorX Healthcare API",
    description="AI-Powered Healthcare Navigator & Cost Estimator",
    version="1.0.0",
)

# CORS — allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router,      prefix="/api/chat",           tags=["Chat"])
app.include_router(hospitals.router, prefix="/api/hospitals",       tags=["Hospitals"])
app.include_router(cost.router,      prefix="/api/cost-estimate",   tags=["Cost"])
app.include_router(loan.router,      prefix="/api/loan-eligibility",tags=["Loan"])
app.include_router(compare.router,   prefix="/api/compare",         tags=["Compare"])
app.include_router(explain.router,   prefix="/api/explain",         tags=["XAI"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "TenzorX Healthcare API"}
```

### 21.2 Chat Route

```python
# api/routes/chat.py

from fastapi import APIRouter, HTTPException
from schemas.request_models import ChatRequest
from schemas.response_models import ChatResponse
from agents.healthcare_agent import HealthcareAgent
from confidence.rag_confidence import RAGConfidenceScorer

router = APIRouter()
agent = HealthcareAgent()
confidence_scorer = RAGConfidenceScorer()

@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Primary conversational endpoint.
    Accepts user message + session context, returns structured AI response.
    """
    try:
        result = agent.process(
            session_id=request.session_id,
            user_message=request.message,
            location=request.location or "",
            patient_profile=request.patient_profile or {},
        )

        # Score RAG confidence
        confidence = confidence_scorer.score(
            user_query=request.message,
            retrieved_context=str(result.get("search_data", {}))[:1000],
            llm_response=result.get("narrative", ""),
        )
        result["confidence"] = confidence

        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 21.3 Cost Estimate Route

```python
# api/routes/cost.py

from fastapi import APIRouter
from schemas.request_models import CostRequest
from engines.cost_engine import CostEngine
from engines.geo_pricing import GeoPricingEngine
from engines.comorbidity_engine import ComorbidityEngine
from engines.pathway_engine import PathwayEngine

router = APIRouter()
cost_engine = CostEngine()
geo_engine = GeoPricingEngine()
comorbidity_engine = ComorbidityEngine()
pathway_engine = PathwayEngine()

@router.post("")
async def estimate_cost(request: CostRequest):
    city_tier = geo_engine.get_city_tier(request.city)
    base = cost_engine.estimate(request.procedure, city_tier)
    geo_adjusted = geo_engine.apply_multiplier(base, city_tier)
    final = comorbidity_engine.adjust(
        geo_adjusted,
        comorbidities=request.comorbidities or [],
        age=request.age,
    )
    pathway = pathway_engine.get_pathway(request.procedure)
    return {"cost_estimate": final, "pathway": pathway}
```

### 21.4 Loan Eligibility Route

```python
# api/routes/loan.py

from fastapi import APIRouter
from schemas.request_models import LoanRequest
from engines.loan_engine import LoanEngine

router = APIRouter()
loan_engine = LoanEngine()

@router.post("")
async def loan_eligibility(request: LoanRequest):
    result = loan_engine.evaluate(
        total_treatment_cost=request.total_treatment_cost,
        gross_monthly_income=request.gross_monthly_income,
        existing_emis=request.existing_emis,
    )
    return result
```

---

## 22. Data Models (Pydantic)

**File:** `schemas/request_models.py`

```python
# schemas/request_models.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class PatientProfile(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    comorbidities: List[str] = []
    budget_max: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier per user")
    message: str = Field(..., min_length=1, max_length=2000)
    location: Optional[str] = None
    patient_profile: Optional[PatientProfile] = None
    lender_mode: bool = False

class CostRequest(BaseModel):
    procedure: str
    city: str
    comorbidities: Optional[List[str]] = []
    age: Optional[int] = None

class LoanRequest(BaseModel):
    total_treatment_cost: float = Field(..., gt=0)
    gross_monthly_income: float = Field(..., gt=0)
    existing_emis: float = Field(default=0, ge=0)

class CompareRequest(BaseModel):
    hospital_ids: List[str] = Field(..., min_length=2, max_length=3)
    procedure: str
    user_lat: Optional[float] = None
    user_lon: Optional[float] = None
    budget_max: Optional[float] = None
```

---

## 23. Mock Data & Seed Scripts

**File:** `data/hospitals_seed.json` (abbreviated schema — implement all 8 cities)

```json
[
  {
    "id": "hosp_nagpur_001",
    "name": "ABC Heart & Ortho Institute",
    "address": "Civil Lines, Nagpur, Maharashtra 440001",
    "city": "nagpur",
    "tier": "mid",
    "nabh_accredited": true,
    "rating": 4.5,
    "review_count": 312,
    "lat": 21.1458,
    "lon": 79.0882,
    "bed_count": 250,
    "specialists_count": 5,
    "has_emergency": true,
    "has_icu": true,
    "specializations": ["Cardiology", "Orthopedics", "General Surgery"],
    "cost_range": {"min": 140000, "max": 220000},
    "doctors": [
      {
        "id": "doc_001", "name": "Dr. Suresh Patel", 
        "specialization": "Orthopedic Surgeon",
        "qualification": "MS Ortho, DNB", "experience_years": 18,
        "rating": 4.7, "fee_min": 800, "fee_max": 1200
      }
    ],
    "reviews": [
      "Excellent surgery outcome. Dr. Patel was very experienced.",
      "Staff was helpful but waiting time was long.",
      "Cost was transparent, no hidden charges.",
      "Clean facility with modern equipment."
    ]
  }
]
```

**Required cities:** Nagpur, Raipur, Bhopal, Indore, Nashik, Aurangabad, Surat, Patna
**Required tiers per city:** 1 premium, 2 mid-tier, 1 budget

**File:** `data/procedure_benchmarks.json` (abbreviated)

```json
[
  {
    "procedure": "angioplasty",
    "icd10_code": "I25.10",
    "duration_hrs": 3,
    "stay_days": "3-5",
    "city_tier": {
      "metro": {"min": 120000, "max": 300000, "typical": 180000},
      "tier2": {"min": 100000, "max": 250000, "typical": 150000},
      "tier3": {"min": 80000,  "max": 200000, "typical": 120000}
    },
    "comorbidity_factors": {
      "diabetes":        {"multiplier": 1.25, "icu_prob": 0.18},
      "heart_failure":   {"multiplier": 1.55, "icu_prob": 0.35},
      "kidney_disease":  {"multiplier": 1.40, "icu_prob": 0.25}
    }
  },
  {
    "procedure": "total knee arthroplasty",
    "icd10_code": "M17.11",
    "duration_hrs": 2.5,
    "stay_days": "4-6",
    "city_tier": {
      "metro": {"min": 200000, "max": 450000, "typical": 300000},
      "tier2": {"min": 150000, "max": 350000, "typical": 230000},
      "tier3": {"min": 100000, "max": 250000, "typical": 160000}
    },
    "comorbidity_factors": {
      "diabetes":         {"multiplier": 1.20, "icu_prob": 0.10},
      "cardiac_history":  {"multiplier": 1.35, "icu_prob": 0.20},
      "obesity":          {"multiplier": 1.15, "icu_prob": 0.08}
    }
  }
]
```

---

## 24. Frontend API Contract

All responses from the backend must satisfy these contracts for the Next.js frontend.

### 24.1 `POST /api/chat` Response

```typescript
// Matches schemas/response_models.py ChatResponse
{
  session_id: string;
  narrative: string;           // Clean markdown text (no XML tags)
  search_data: {
    emergency: boolean;
    query_interpretation: string;
    procedure: string;
    icd10_code: string;
    icd10_label: string;
    snomed_code: string;
    medical_category: string;
    pathway: PathwayStep[];
    mapping_confidence: number;
    location: string;
    cost_estimate: CostEstimate;
    hospitals: Hospital[];
    comorbidity_warnings: string[];
    data_sources: string[];
  };
  severity: "RED" | "YELLOW" | "GREEN";
  is_emergency: boolean;
  confidence: {
    composite_score: number;
    faithfulness: number;
    contextual_relevancy: number;
    answer_relevancy: number;
    below_threshold: boolean;
    show_uncertainty_indicator: boolean;
    label: "High" | "Moderate" | "Low";
  };
}
```

### 24.2 `POST /api/loan-eligibility` Response

```typescript
{
  loan_amount: number;
  treatment_cost: number;
  primary_dti: number;
  risk_band: string;
  risk_flag: string;
  underwriting_assessment: string;
  interest_rate_range: [number, number];
  call_to_action: string;
  emi_options: Array<{
    tenure_months: number;
    emi: number;
    dti_at_this_tenure: number;
  }>;
}
```

### 24.3 `GET /api/explain/{hospital_id}` Response

```typescript
{
  shap_explanation: {
    hospital_name: string;
    base_value: number;
    final_score: number;
    waterfall: Array<{
      feature: string;
      raw_score: number;
      weight: number;
      contribution: number;
      delta_from_baseline: number;
      direction: "positive" | "negative";
    }>;
    summary: string;
  };
}
```

---

## 25. Deployment & Configuration

### 25.1 Running Locally

```bash
cd Backend

# Install dependencies
pip install -r requirements.txt

# Download spaCy models
python -m spacy download en_core_web_sm

# Copy and configure env
cp .env.example .env
# Edit .env with your NVIDIA_API_KEY and NEO4J credentials

# Seed Neo4j (run once)
python knowledge_graph/schema_setup.py

# Download ICD-10 JSON (run once)
python scripts/download_icd10.py

# Start the API server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 25.2 `scripts/download_icd10.py`

```python
# scripts/download_icd10.py
"""
Downloads the 2022 ICD-10 CM JSON dataset from GitHub.
Source: https://github.com/smog1210/2022-ICD-10-CM-JSON
"""
import requests, json, os

URL = "https://raw.githubusercontent.com/smog1210/2022-ICD-10-CM-JSON/master/icd10cm_codes_2022.json"
OUTPUT = "data/icd10_2022.json"

os.makedirs("data", exist_ok=True)
response = requests.get(URL, timeout=30)
response.raise_for_status()
with open(OUTPUT, "w") as f:
    json.dump(response.json(), f)
print(f"ICD-10 data saved to {OUTPUT}")
```

### 25.3 Environment Notes

| Variable | Required | Notes |
|---|---|---|
| `NVIDIA_API_KEY` | ✅ Yes | From NVIDIA NGC |
| `NEO4J_URI` | ✅ Yes | Use `bolt://localhost:7687` locally |
| `NEO4J_PASSWORD` | ✅ Yes | Set during Neo4j install |
| `NOMINATIM_USER_AGENT` | ✅ Yes | Must be unique app identifier |
| `GOOGLE_MAPS_KEY` | Optional | Fallback geocoder only |
| `CORS_ORIGINS` | ✅ Yes | Comma-separated list of frontend URLs |

### 25.4 Critical Implementation Notes

1. **All LLM calls → `NvidiaClient` only.** Never call the NVIDIA API directly from engines or routes.
2. **Session isolation is mandatory.** The `get_session_history(session_id)` function in `memory_manager.py` ensures no cross-user state leakage. Always pass a unique `session_id` per user from the frontend.
3. **Cost estimates are always ranges.** Never return a single INR value — always `{"min": X, "max": Y}`.
4. **Emergency detection runs first.** The `SeverityClassifier.classify()` call in `healthcare_agent.py` happens before any other processing. A RED result short-circuits the standard flow.
5. **Confidence threshold enforcement.** If `RAGConfidenceScorer` returns `below_threshold=True`, the frontend must display the uncertainty indicator and mandatory disclaimer.
6. **ICD-10 JSON download is a prerequisite.** Run `scripts/download_icd10.py` before starting the server. The `ICD10Mapper` will fail on import if the file is absent.
7. **Fusion score weights are locked.** Do not change the 40/25/20/15 weights — they are derived from the problem statement specification and directly impact hospital ranking.

---

*This document is the complete backend implementation specification for TenzorX.
The frontend (Next.js) specification lives in the root `instruction.md` file.
Together, these two documents define the full system architecture.*
