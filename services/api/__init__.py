"""
QURAN AI API Service Package

Core API service for the QURAN AI platform.

This package contains:
- FastAPI application with all necessary middleware
- Quran Foundation API integration service
- Agent orchestration service
- Citation validation service
- All API routers (quran, agents, citations, chat, sources)
- Database models and configurations
"""

from .app import app
from .config import settings
from .models import *
from .routers import quran, agents, citations, chat, sources
from .services.quran_api_service import QuranAPIService, QuranAPIError
from .middleware import RateLimitMiddleware, CacheMiddleware, SecurityMiddleware, ValidationMiddleware

__all__ = [
    # FastAPI app
    "app",

    # Configuration
    "settings",

    # Models
    "BaseModel", "BaseEntity",
    "SurahModel", "AyahModel", "TranslationModel", "WordTranslationModel",
    "ScholarModel", "TafsirBookModel",
    "SourcePermissionModel", "SourceReferenceModel", "CitationModel",
    "AgentConfigModel", "RetrievedSourceModel", "AgentExecutionModel",
    "UserModel", "BookmarkModel", "ReadingProgressModel",
    "SearchRequestModel", "SearchResultModel", "SearchResponseModel",
    "CreateTafsirRequest", "CreateTafsirResponse",
    "ExecuteAgentRequest", "ExecuteAgentResponse",

    # Enums
    "SurahType", "Language", "EvidenceLevel", "AgentType", "Methodology",
    "HadithGrade", "UserRole",

    # Routers
    "quran", "agents", "citations", "chat", "sources",

    # Services
    "QuranAPIService", "QuranAPIError",

    # Middleware
    "RateLimitMiddleware", "CacheMiddleware", "SecurityMiddleware", "ValidationMiddleware",
]