from .quran import router as quran_router
from .agents import router as agents_router
from .tafsir import router as tafsir_router
from .workspace import router as workspace_router

__all__ = [
    "quran_router",
    "agents_router", 
    "tafsir_router",
    "workspace_router",
]