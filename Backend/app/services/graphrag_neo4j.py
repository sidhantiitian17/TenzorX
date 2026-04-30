"""
Production GraphRAG Service for Healthcare Navigator.

This module implements a robust GraphRAG system using Neo4j for clinical pathway
traversal. It provides deterministic clinical pathway discovery from symptoms
to interventions through graph traversal.

Production Standards:
- Comprehensive logging with structured log levels
- Async/await patterns for non-blocking operations
- Connection pooling and proper resource management
- Strict type hints throughout
- Pydantic models for data validation
- Robust error handling with custom exceptions
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from neo4j import AsyncGraphDatabase, AsyncDriver
from pydantic import BaseModel, Field, validator

from app.core.config import settings

# Configure module logger
logger = logging.getLogger(__name__)


class ClinicalPathwayNode(BaseModel):
    """Represents a node in the clinical pathway graph."""

    node_type: str = Field(..., description="Type of clinical node (Symptom, Diagnosis, Procedure, etc.)")
    code: str = Field(..., description="Clinical code (ICD-10, CPT, etc.)")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Detailed description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional node metadata")

    @validator('node_type')
    def validate_node_type(cls, v):
        """Validate that node_type is one of the expected clinical pathway types."""
        valid_types = {'Symptom', 'Diagnosis', 'Procedure', 'Hospitalization', 'Outcome'}
        if v not in valid_types:
            raise ValueError(f"node_type must be one of {valid_types}")
        return v


class ClinicalPathway(BaseModel):
    """Complete clinical pathway from symptom to outcome."""

    icd_code: str = Field(..., description="Starting ICD-10 code")
    pathway: List[ClinicalPathwayNode] = Field(..., description="Ordered list of pathway nodes")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Pathway confidence score")
    estimated_duration_days: Optional[int] = Field(None, description="Estimated treatment duration")
    success_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Historical success rate")


class GraphRAGError(Exception):
    """Base exception for GraphRAG operations."""
    pass


class ConnectionError(GraphRAGError):
    """Raised when Neo4j connection fails."""
    pass


class QueryError(GraphRAGError):
    """Raised when Cypher query execution fails."""
    pass


class MedicalGraphRAG:
    """
    Production GraphRAG service for clinical pathway discovery.

    Uses Neo4j with connection pooling for robust graph traversal operations.
    Implements deterministic clinical pathways from symptoms to interventions.
    """

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize GraphRAG with connection pooling.

        Args:
            uri: Neo4j connection URI (defaults to settings)
            user: Neo4j username (defaults to settings)
            password: Neo4j password (defaults to settings)
        """
        self.uri = uri or settings.NEO4J_URI
        self.user = user or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD
        self._driver: Optional[AsyncDriver] = None
        self._connection_pool_size = 10  # Connection pool size
        self._connection_timeout = 30.0  # Connection timeout in seconds

        logger.info(f"Initializing MedicalGraphRAG with URI: {self.uri}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """
        Establish connection to Neo4j with pooling.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            logger.info("Establishing Neo4j connection with pooling...")

            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=self._connection_pool_size,
                connection_timeout=self._connection_timeout
            )

            # Test connection
            await self._driver.verify_connectivity()
            logger.info("✅ Neo4j connection established successfully")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise ConnectionError(f"Neo4j connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Close Neo4j connection gracefully."""
        if self._driver:
            try:
                await self._driver.close()
                logger.info("✅ Neo4j connection closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing Neo4j connection: {e}")
            finally:
                self._driver = None

    async def get_clinical_pathway(self, icd_code: str) -> ClinicalPathway:
        """
        Retrieve complete clinical pathway for an ICD-10 code.

        Executes a precise Cypher query to traverse from Symptom -> Diagnosis ->
        Procedure -> Hospitalization phases deterministically.

        Args:
            icd_code: ICD-10 code to start pathway from

        Returns:
            ClinicalPathway: Complete pathway with all nodes and metadata

        Raises:
            QueryError: If query execution fails
            ConnectionError: If database connection is lost
        """
        if not self._driver:
            raise ConnectionError("Not connected to Neo4j")

        try:
            logger.info(f"🔍 Retrieving clinical pathway for ICD-10: {icd_code}")

            # Precise Cypher query for deterministic pathway traversal
            query = """
            MATCH (symptom:Symptom {icd_code: $icd_code})
            OPTIONAL MATCH (symptom)-[:INDICATES]->(diagnosis:Diagnosis)
            OPTIONAL MATCH (diagnosis)-[:REQUIRES]->(procedure:Procedure)
            OPTIONAL MATCH (procedure)-[:LEADS_TO]->(hospitalization:Hospitalization)
            OPTIONAL MATCH (hospitalization)-[:RESULTS_IN]->(outcome:Outcome)

            RETURN
                symptom,
                diagnosis,
                procedure,
                hospitalization,
                outcome,
                size((symptom)-[:INDICATES]->()) as symptom_connections,
                size((diagnosis)-[:REQUIRES]->()) as diagnosis_connections
            LIMIT 1
            """

            async with self._driver.session() as session:
                result = await session.run(query, icd_code=icd_code)
                record = await result.single()

                if not record:
                    logger.warning(f"⚠️ No pathway found for ICD-10: {icd_code}")
                    return ClinicalPathway(
                        icd_code=icd_code,
                        pathway=[],
                        confidence_score=0.0
                    )

                # Build pathway nodes
                pathway_nodes = []

                # Add symptom node
                if record["symptom"]:
                    symptom_data = dict(record["symptom"])
                    pathway_nodes.append(ClinicalPathwayNode(
                        node_type="Symptom",
                        code=symptom_data.get("icd_code", icd_code),
                        name=symptom_data.get("name", "Unknown Symptom"),
                        description=symptom_data.get("description"),
                        metadata={
                            "connections": record["symptom_connections"],
                            "severity": symptom_data.get("severity", "Unknown")
                        }
                    ))

                # Add diagnosis node
                if record["diagnosis"]:
                    diagnosis_data = dict(record["diagnosis"])
                    pathway_nodes.append(ClinicalPathwayNode(
                        node_type="Diagnosis",
                        code=diagnosis_data.get("icd_code", ""),
                        name=diagnosis_data.get("name", "Unknown Diagnosis"),
                        description=diagnosis_data.get("description"),
                        metadata={
                            "connections": record["diagnosis_connections"],
                            "confidence": diagnosis_data.get("confidence", 0.0)
                        }
                    ))

                # Add procedure node
                if record["procedure"]:
                    procedure_data = dict(record["procedure"])
                    pathway_nodes.append(ClinicalPathwayNode(
                        node_type="Procedure",
                        code=procedure_data.get("cpt_code", ""),
                        name=procedure_data.get("name", "Unknown Procedure"),
                        description=procedure_data.get("description"),
                        metadata={
                            "duration_hours": procedure_data.get("duration_hours"),
                            "risk_level": procedure_data.get("risk_level", "Unknown"),
                            "cost_category": procedure_data.get("cost_category", "Unknown")
                        }
                    ))

                # Add hospitalization node
                if record["hospitalization"]:
                    hosp_data = dict(record["hospitalization"])
                    pathway_nodes.append(ClinicalPathwayNode(
                        node_type="Hospitalization",
                        code=hosp_data.get("drg_code", ""),
                        name=hosp_data.get("name", "Unknown Hospitalization"),
                        description=hosp_data.get("description"),
                        metadata={
                            "avg_length_stay": hosp_data.get("avg_length_stay_days"),
                            "complication_rate": hosp_data.get("complication_rate", 0.0)
                        }
                    ))

                # Add outcome node
                if record["outcome"]:
                    outcome_data = dict(record["outcome"])
                    pathway_nodes.append(ClinicalPathwayNode(
                        node_type="Outcome",
                        code=outcome_data.get("code", ""),
                        name=outcome_data.get("name", "Unknown Outcome"),
                        description=outcome_data.get("description"),
                        metadata={
                            "success_rate": outcome_data.get("success_rate", 0.0),
                            "recovery_time_days": outcome_data.get("recovery_time_days")
                        }
                    ))

                # Calculate confidence score based on pathway completeness
                pathway_completeness = len(pathway_nodes) / 5.0  # 5 potential nodes
                connection_strength = min(record["symptom_connections"] or 0,
                                        record["diagnosis_connections"] or 0) / 10.0
                confidence_score = min(pathway_completeness * 0.7 + connection_strength * 0.3, 1.0)

                # Extract duration and success rate from metadata
                estimated_duration = None
                success_rate = None

                for node in pathway_nodes:
                    if node.node_type == "Hospitalization" and node.metadata.get("avg_length_stay"):
                        estimated_duration = int(node.metadata["avg_length_stay"])
                    if node.node_type == "Outcome" and node.metadata.get("success_rate"):
                        success_rate = float(node.metadata["success_rate"])

                pathway = ClinicalPathway(
                    icd_code=icd_code,
                    pathway=pathway_nodes,
                    confidence_score=round(confidence_score, 3),
                    estimated_duration_days=estimated_duration,
                    success_rate=success_rate
                )

                logger.info(f"✅ Retrieved pathway with {len(pathway_nodes)} nodes, confidence: {confidence_score:.3f}")
                return pathway

        except Exception as e:
            logger.error(f"❌ Query execution failed for ICD-10 {icd_code}: {e}")
            raise QueryError(f"Clinical pathway query failed: {e}") from e

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Neo4j connection.

        Returns:
            Dict with health status and metadata
        """
        try:
            if not self._driver:
                return {"status": "disconnected", "error": "No active connection"}

            await self._driver.verify_connectivity()

            # Get basic database info
            async with self._driver.session() as session:
                result = await session.run("MATCH (n) RETURN count(n) as node_count")
                record = await result.single()
                node_count = record["node_count"] if record else 0

            return {
                "status": "healthy",
                "node_count": node_count,
                "connection_pool_size": self._connection_pool_size
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}


# Utility functions for async context management
@asynccontextmanager
async def get_graph_rag() -> MedicalGraphRAG:
    """
    Context manager for GraphRAG operations.

    Usage:
        async with get_graph_rag() as rag:
            pathway = await rag.get_clinical_pathway("I25.1")
    """
    rag = MedicalGraphRAG()
    try:
        await rag.connect()
        yield rag
    finally:
        await rag.disconnect()