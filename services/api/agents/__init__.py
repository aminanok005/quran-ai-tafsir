"""
QURAN AI Agent Package

This package contains all Tafsir agents for the QURAN AI Super WebApp.
"""

from .base_agent import BaseTafsirAgent
from .ibn_kathir_agent import IbnKathirAgent
from .al_tabari_agent import AlTabariAgent
from .al_qurtubi_agent import AlQurtubiAgent
from .ibn_ashur_agent import IbnAshurAgent
from .al_saadi_agent import AlSaadiAgent
from .al_zuhayli_agent import AlZuhayliAgent

__all__ = [
    "BaseTafsirAgent",
    "IbnKathirAgent",
    "(default_agent)",
    "AlTabariAgent",
    "AlQurtubiAgent",
    "IbnAshurAgent",
    "AlSaadiAgent",
    "AlZuhayliAgent",
]