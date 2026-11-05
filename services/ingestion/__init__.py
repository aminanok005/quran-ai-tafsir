"""Source-aware ingestion helpers."""

from .parser import (
    DEVELOPMENT_COLLECTION,
    DevelopmentProvenance,
    ParsedTafsirRecord,
    ParseIssue,
    ParseResult,
    embedding_collection,
    parse_ayah_key,
    parse_json_file,
    parse_json_payload,
    parse_sqlite_file,
)
from .embedding import EmbeddingDocument, build_development_embedding_document
from .policy import IngestionDecision, SourcePermission, evaluate_source
from .search import SearchHit, search_development

__all__ = [
    "DEVELOPMENT_COLLECTION",
    "DevelopmentProvenance",
    "EmbeddingDocument",
    "IngestionDecision",
    "ParseIssue",
    "ParseResult",
    "ParsedTafsirRecord",
    "SourcePermission",
    "SearchHit",
    "build_development_embedding_document",
    "embedding_collection",
    "evaluate_source",
    "parse_ayah_key",
    "parse_json_file",
    "parse_json_payload",
    "parse_sqlite_file",
    "search_development",
]
