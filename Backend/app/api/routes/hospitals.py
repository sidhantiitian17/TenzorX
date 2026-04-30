"""
Hospital API router.

Provides endpoints for hospital search and discovery based on location,
specialization, and other criteria.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.services.hospital_search import search_hospitals, get_hospital_details, HospitalSearchRequest, Hospital

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.post(
    "/search",
    response_model=List[Hospital],
    status_code=status.HTTP_200_OK,
    summary="Search for hospitals based on location and criteria",
)
async def search_hospitals_endpoint(request: HospitalSearchRequest) -> List[Hospital]:
    """
    Search for hospitals near a location with optional filters.

    Returns hospitals sorted by ranking score, filtered by distance,
    specialization, cost, and rating criteria.
    """
    try:
        results = await search_hospitals(request)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hospital search failed: {str(e)}",
        )


@router.get(
    "/{hospital_id}",
    response_model=Hospital,
    status_code=status.HTTP_200_OK,
    summary="Get detailed information for a specific hospital",
)
async def get_hospital_details_endpoint(hospital_id: str) -> Hospital:
    """
    Get comprehensive details for a specific hospital by ID.

    Includes doctors, reviews, ranking signals, and operational details.
    """
    try:
        hospital = await get_hospital_details(hospital_id)
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hospital with ID '{hospital_id}' not found",
            )
        return hospital
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve hospital details: {str(e)}",
        )


@router.get(
    "/near/{location}",
    response_model=List[Hospital],
    status_code=status.HTTP_200_OK,
    summary="Find hospitals near a location",
)
async def get_hospitals_near_location(
    location: str,
    specialization: Optional[str] = Query(None, description="Filter by medical specialization"),
    max_distance: float = Query(50.0, ge=0.0, description="Maximum distance in kilometers"),
    max_cost: Optional[int] = Query(None, ge=0, description="Maximum cost filter"),
    min_rating: float = Query(3.0, ge=0.0, le=5.0, description="Minimum rating filter"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
) -> List[Hospital]:
    """
    Quick search for hospitals near a location with query parameters.

    Simplified endpoint for common hospital searches using URL parameters.
    """
    try:
        request = HospitalSearchRequest(
            location=location,
            specialization=specialization,
            max_distance_km=max_distance,
            max_cost=max_cost,
            min_rating=min_rating,
            limit=limit,
        )
        results = await search_hospitals(request)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hospital search failed: {str(e)}",
        )