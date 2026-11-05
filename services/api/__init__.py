"""
QURAN AI API Package

This package contains the complete backend infrastructure for the QURAN AI Super WebApp.
"""

from .models import *
from .routers import (
    quran_router,
    agents_router,
    tafsir_router,
)
from .services import QuranAPIService, AgentOrchestratorService, EvidenceValidationService
from .agents import (
    BaseTafsirAgent,
    IbnKathirAgent,
    AlTabariAgent,
    AlQurtubiAgent,
    IbnAshurAgent,
    AlSaadiAgent,
    AlZuhayliAgent,
)

__all__ = [
    # Models
    "SurahType",
    "Language",
    "EvidenceLevel",
    "AgentType",
    "Methodology",
    "HadithGrade",
    "UserRole",
    "BaseModel",
    "BaseEntity",
    "SurahModel",
    "AyahModel",
    "TranslationModel",
    "WordTranslationModel",
    "ScholarModel",
    "TafsirBookModel",
    "SourcePermissionModel",
    "SourceReferenceModel",
    "CitationModel",
    "AgentConfigModel",
    "RetrievedSourceModel",
    "AgentExecutionModel",
    "UserModel",
    "BookmarkModel",
    "ReadingProgressModel",
    "SearchRequestModel",
    "SearchResultModel",
    "SearchResponseModel",
    "CreateTafsirRequest",
    "CreateTafsirResponse",
    "ExecuteAgentRequest",
    "ExecuteAgentResponse",
    
    # Routers
    "quran_router",
    "agents_router",
    "tafsir_router",
    
    # Services
    "QuranAPIService",
    "AgentOrchestratorService",
    "EvidenceValidationService",
    
    # Agents
    "BaseTafsirAgent",
    "IbnKathirAgent",
    "AlTabariAgent",
    "AlQurtubiAgent",
    "IbnAshurAgent",
    "AlSaadiAgent",
    "AlZuhayliAgent",
]