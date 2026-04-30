"""
FastAPI application initialization and configuration.

Configures the FastAPI app with CORS middleware, health check endpoint,
and API routers. This is the entry point for the TenzorX backend.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.triage import router as triage_router
from app.api.routes.hospitals import router as hospitals_router
from app.core.config import settings

# ============================================================================
# Logging Configuration
# ============================================================================
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# ============================================================================
# Application Lifespan Events
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    
    This context manager handles:
    - Startup: Initialize connections, resources
    - Shutdown: Cleanup connections, resources
    """
    # ========================================================================
    # STARTUP
    # ========================================================================
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} API...")
    logger.info(f"Version: {settings.VERSION}")
    logger.info(f"API Base Path: {settings.API_V1_STR}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    # Initialize Neo4j driver (placeholder - implement in services)
    logger.info(f"Connecting to Neo4j at {settings.NEO4J_URI}...")
    # driver = GraphDatabase.driver(
    #     settings.NEO4J_URI,
    #     auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    # )
    
    yield
    
    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("🛑 Shutting down application...")
    # Close Neo4j driver connection
    # driver.close()
    logger.info("Shutdown complete")


# ============================================================================
# FastAPI Application Initialization
# ============================================================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.ENABLE_SWAGGER_UI else None,
    redoc_url="/redoc" if settings.ENABLE_REDOC else None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

logger.info("FastAPI application created")


# ============================================================================
# CORS Middleware Configuration
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

logger.info(f"CORS middleware configured for: {settings.BACKEND_CORS_ORIGINS}")


# ============================================================================
# Health Check Endpoint
# ============================================================================
@app.get(
    "/",
    summary="Health Check",
    description="Returns API status and basic information",
    tags=["Health"],
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and deployment verification.
    
    Returns:
        Dict containing API status, version, and environment info
        
    Example response:
        {
            "status": "healthy",
            "service": "TenzorX Healthcare Navigator",
            "version": "1.0.0",
            "environment": "development"
        }
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": "development" if settings.DEBUG else "production",
        },
    )


# ============================================================================
# API Router Placeholder
# ============================================================================
app.include_router(triage_router, prefix=settings.API_V1_STR)
app.include_router(hospitals_router, prefix=settings.API_V1_STR)
logger.info(f"API routes registered under {settings.API_V1_STR}")


# ============================================================================
# Error Handlers
# ============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    
    Logs the error and returns a consistent error response format.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "service": settings.PROJECT_NAME,
        },
    )


# ============================================================================
# Application Metadata
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Uvicorn server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
