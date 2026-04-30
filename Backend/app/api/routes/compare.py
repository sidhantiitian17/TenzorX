"""
Hospital Comparison API route.

Provides side-by-side hospital comparison.
"""

from fastapi import APIRouter, HTTPException
from app.schemas.request_models import CompareRequest
from app.engines.comparison_engine import ComparisonEngine
from app.knowledge_graph.neo4j_client import Neo4jClient

router = APIRouter()
comparison_engine = ComparisonEngine()
neo4j = Neo4jClient()


@router.post("")
async def compare_hospitals(request: CompareRequest):
    """
    Compare 2-3 hospitals side-by-side.
    """
    try:
        # Fetch hospital details from Neo4j
        hospitals = []
        for hid in request.hospital_ids:
            hosp = neo4j.get_hospital_by_id(hid)
            if hosp:
                hospitals.append(hosp)
        
        if len(hospitals) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 valid hospital IDs")
        
        result = comparison_engine.compare(hospitals)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
