"""
Routing Logic for Provider Filters.

Handles severity-based filter overrides (TC-17).
"""

from typing import Dict, Any, Optional


def get_provider_filters(severity: str, budget: Optional[float] = None) -> Dict[str, Any]:
    """
    Get provider filters based on severity and budget.
    
    RED severity overrides budget filters - triggers emergency-only display.
    
    Args:
        severity: "RED", "YELLOW", or "GREEN"
        budget: Optional budget constraint
        
    Returns:
        Dict with filter parameters
    """
    filters: Dict[str, Any] = {}
    
    if severity == "RED":
        # RED overrides budget filters (TC-17)
        filters["emergency_only"] = True
        filters["budget"] = None  # Budget filter overridden
        filters["severity_override"] = True
    else:
        filters["emergency_only"] = False
        if budget is not None:
            filters["budget"] = budget
    
    return filters
