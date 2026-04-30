"""
Route collection for the API surface.
"""

from .triage import router as triage_router

__all__ = ["triage_router"]
