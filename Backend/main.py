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
from app.api.routes.chat import router as chat_router
from app.api.routes.cost import router as cost_router
from app.api.routes.loan import router as loan_router
from app.api.routes.compare import router as compare_router
from app.api.routes.explain import router as explain_router
# New routes per instructionagent.md Section 6
from app.api.routes.emi import router as emi_router
from app.api.routes.session import router as session_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.save_result import router as save_result_router
from app.api.routes.form_template import router as form_template_router
from app.api.routes.lender import router as lender_router
from app.api.routes.websocket import router as websocket_router
from app.api.routes.procedure_detection import router as procedure_detection_router
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
    
    # Initialize ICD-10 Medical Ontology (TC-23)
    logger.info("Initializing ICD-10 Medical Ontology...")
    try:
        from app.nlp.icd10_mapper import load_icd10
        icd10_index = load_icd10()
        logger.info(f"✅ ICD-10 Ontology loaded ({len(icd10_index):,} clinical keywords)")
        app.state.icd10_loaded = True
        app.state.icd10_size = len(icd10_index)
    except RuntimeError as e:
        logger.error(f"⚠️ ICD-10 Medical Ontology could not be loaded: {e}")
        logger.error("Run `python setup_data.py` to download ICD-10 data")
        app.state.icd10_loaded = False
        app.state.icd10_error = str(e)
    
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
# Add wildcard for local development to handle proxy URLs
origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
# Add regex pattern for 127.0.0.1 with any port
origins.append("http://127.0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)

logger.info(f"CORS middleware configured for: {origins}")


# ============================================================================
# Global OPTIONS Handler for CORS Preflight
# ============================================================================
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle OPTIONS preflight requests for all routes."""
    return JSONResponse(
        content={"message": "OK"},
        status_code=200,
    )


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
    # Check ICD-10 status
    icd10_status = "ok" if getattr(app.state, 'icd10_loaded', False) else "error"
    icd10_size = getattr(app.state, 'icd10_size', 0)
    
    # Get list of registered routes
    routes_info = {
        "agents": ["ner_triage", "clinical_pathway", "hospital_discovery",
                   "financial_engine", "geo_spatial", "xai_explainer", "appointment_paperwork"],
        "endpoints": [
            f"{settings.API_V1_STR}/chat",
            f"{settings.API_V1_STR}/triage",
            f"{settings.API_V1_STR}/hospitals",
            f"{settings.API_V1_STR}/cost-estimate",
            f"{settings.API_V1_STR}/loan-eligibility",
            f"{settings.API_V1_STR}/emi-calculate",
            f"{settings.API_V1_STR}/session",
            f"{settings.API_V1_STR}/feedback",
            f"{settings.API_V1_STR}/save-result",
            f"{settings.API_V1_STR}/form-template",
            f"{settings.API_V1_STR}/lender",
            "/ws/chat/{{session_id}}",
        ],
    }
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": "development" if settings.DEBUG else "production",
            "icd10": {
                "status": icd10_status,
                "keywords_loaded": icd10_size,
            },
            "agents_implemented": routes_info["agents"],
            "endpoints": routes_info["endpoints"],
            "specification": "instructionagent.md",
        },
    )


# ============================================================================
# API Router Registration
# ============================================================================
# Per instructionagent.md Section 6 - All API endpoints

# Existing routes
app.include_router(triage_router, prefix=settings.API_V1_STR)
app.include_router(hospitals_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chat")
app.include_router(cost_router, prefix=f"{settings.API_V1_STR}/cost-estimate")
app.include_router(loan_router, prefix=f"{settings.API_V1_STR}/loan-eligibility")
app.include_router(compare_router, prefix=f"{settings.API_V1_STR}/compare")
app.include_router(explain_router, prefix=f"{settings.API_V1_STR}/explain")

# New routes per instructionagent.md
# POST /api/emi-calculate - Real-time EMI calculation
app.include_router(emi_router, prefix=settings.API_V1_STR)
# GET/PATCH /api/session/{session_id} - Session management
app.include_router(session_router, prefix=settings.API_V1_STR)
# POST /api/feedback - Feedback submission
app.include_router(feedback_router, prefix=settings.API_V1_STR)
# POST /api/save-result - Save results to session
app.include_router(save_result_router, prefix=settings.API_V1_STR)
# GET /api/form-template/{form_name} - Form templates
app.include_router(form_template_router, prefix=settings.API_V1_STR)
# POST /api/lender/underwrite - Lender/insurer B2B mode
app.include_router(lender_router, prefix=settings.API_V1_STR)
# WebSocket /ws/chat/{session_id} - Streaming responses
app.include_router(websocket_router)
# POST /api/detect-procedure - Real-time procedure detection
app.include_router(procedure_detection_router, prefix=settings.API_V1_STR)

logger.info(f"✅ API routes registered under {settings.API_V1_STR}")
logger.info("Routes: triage, hospitals, chat, cost-estimate, loan-eligibility,")
logger.info("        compare, explain, emi-calculate, session, feedback,")
logger.info("        save-result, form-template, lender, websocket, detect-procedure")


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
