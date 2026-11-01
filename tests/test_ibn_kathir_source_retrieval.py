import asyncio
import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "services"
    / "ai-engine"
    / "agents"
    / "ibn-kathir"
    / "source_retrieval.py"
)
SPEC = importlib.util.spec_from_file_location("ibn_kathir_source_retrieval", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
IbnKathirSourceRetrieval = MODULE.IbnKathirSourceRetrieval


def test_empty_store_does_not_invent_sources():
    retrieval = IbnKathirSourceRetrieval()

    sources = asyncio.run(retrieval.retrieve("1:1", {}, "ma'thur"))

    assert sources == []


def test_loading_without_a_configured_source_store_fails_explicitly():
    retrieval = IbnKathirSourceRetrieval()

    with pytest.raises(RuntimeError, match="No licensed Tafsir source store"):
        asyncio.run(retrieval.load_sources())
