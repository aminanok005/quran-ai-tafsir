"""
QURAN AI API Service

Thai-first Quran study and evidence-based Tafsir API.

Core responsibilities:
- Quran Foundation API proxy (server-side credentials only)
- Agent orchestration and execution
- Citation validation and verification
- Chat/session management
- Source registry and metadata management
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .models import *
from .routers import quran, agents, retrieval, tafsir, workspace
from .services import QuranAPIService, AgentOrchestratorService, EvidenceValidationService
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting QURAN AI API service")

    # Initialize services
    try:
        quran_api_service = QuranAPIService()
        agent_orchestrator = AgentOrchestratorService()
        citation_service = EvidenceValidationService()

        # Test database connections
        # Test external API connectivity
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down QURAN AI API service")

app = FastAPI(
    title="QURAN AI API",
    version="0.1.0",
    description="Thai-first Quran study and evidence-based Tafsir API.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(quran.router, prefix="/api/v1")
app.include_router(agents.router)
app.include_router(agents.router, prefix="/api/v1/tafsir/agents", include_in_schema=False)
app.include_router(tafsir.router, prefix="/api/v1")
app.include_router(retrieval.router, prefix="/api/v1")
app.include_router(workspace.router, prefix="/api/v1")

@app.get("/health", tags=["health"])
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "quran-ai-api"}

@app.get("/ready", tags=["health"])
async def readiness() -> Dict[str, Any]:
    """Readiness check for load balancers."""
    try:
        # Add service checks here
        services_status = {
            "database": "checking",
            "quran_api": "checking",
            "redis": "checking"
        }

        # If all services are ready
        return {
            "status": "ready",
            "services": services_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTPException handler."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    """Unhandled exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )