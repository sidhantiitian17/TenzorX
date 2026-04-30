"""
Knowledge Graph module for Neo4j integration.

Provides graph database connectivity, schema management, and GraphRAG capabilities.
"""

from app.knowledge_graph.neo4j_client import Neo4jClient
from app.knowledge_graph.graph_rag import GraphRAGEngine

__all__ = ["Neo4jClient", "GraphRAGEngine"]
