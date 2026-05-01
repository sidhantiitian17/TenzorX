"""
Knowledge Graph module for Neo4j integration.

Provides graph database connectivity, schema management, and GraphRAG capabilities.
Implements the full Knowledge Graph architecture per instruction_KG.md.
"""

from app.knowledge_graph.neo4j_client import Neo4jClient
from app.knowledge_graph.graph_rag import GraphRAGEngine
from app.knowledge_graph.schema_setup import (
    setup_schema,
    create_constraints,
    create_indexes,
    seed_geography,
    seed_comorbidities,
    seed_cost_components,
    seed_specialists,
    seed_insurance_tiers,
    seed_review_aspects,
    seed_symptoms_and_diseases,
    seed_disease_procedure_relationships,
    seed_comorbidity_procedure_links,
    compute_fusion_scores,
)
from app.knowledge_graph.fusion_scorer import FusionScorer
from app.knowledge_graph.availability_proxy import (
    AvailabilityProxy,
    AvailabilityResult,
    SeverityClassifier,
)

__all__ = [
    "Neo4jClient",
    "GraphRAGEngine",
    "FusionScorer",
    "AvailabilityProxy",
    "AvailabilityResult",
    "SeverityClassifier",
    "setup_schema",
    "create_constraints",
    "create_indexes",
    "compute_fusion_scores",
]
