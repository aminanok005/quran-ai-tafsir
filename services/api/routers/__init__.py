from .quran import router as quran_router
from .agents import router as agents_router
from .citations import router as citations_router
from .chat import router as chat_router
from .sources import router as sources_router

__all__ = [
    "quran_router",
    "agents_router", 
    "citations_router",
    "chat_router",
    "sources_router"
]