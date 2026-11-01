"""Backward-compatible Ibn Kathir retrieval import."""

from services.tafsir.source_retrieval import DATASET_METADATA, TafsirSourceRetrieval

IbnKathirSourceRetrieval = TafsirSourceRetrieval

__all__ = ["DATASET_METADATA", "IbnKathirSourceRetrieval"]
