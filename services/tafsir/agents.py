"""Source-bound assistant configurations for the available tafsir books."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .source_retrieval import DATASET_METADATA, TafsirSourceRetrieval

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASES = {
    "ibn-kathir": "ar-tafsir-ibn-kathir.db",
    "al-tabari": "ar-tafsir-al-tabari.db",
    "al-qurtubi": "ar-tafseer-al-qurtubi.db",
    "al-saadi": "tafsir-as-saadi.db",
}
AGENT_FOCUS = {
    "ibn-kathir": "Explain only what the retrieved Ibn Kathir passage supports.",
    "al-tabari": "Explain only what the retrieved al-Tabari passage supports.",
    "al-qurtubi": (
        "Explain only what the retrieved al-Qurtubi passage supports; do not turn "
        "its legal discussion into a personal fatwa."
    ),
    "al-saadi": "Explain only what the retrieved al-Sa'di passage supports.",
}


@dataclass(frozen=True)
class ScholarAgentConfig:
    agent_id: str
    title: str
    author: str
    author_ar: str
    language: str
    focus: str
    database_path: Path
    dataset_id: str


def get_agent_config(
    agent_id: str,
    source_language: Optional[str] = None,
    database_dir: Optional[Path] = None,
) -> ScholarAgentConfig:
    if agent_id not in DEFAULT_DATABASES:
        raise ValueError(f"Unknown tafsir agent: {agent_id}")
    if source_language not in (None, "ar", "id"):
        raise ValueError("source_language must be 'ar' or 'id'")
    if agent_id != "al-saadi" and source_language not in (None, "ar"):
        raise ValueError("Only al-saadi supports a non-Arabic source")

    filename = DEFAULT_DATABASES[agent_id]
    if agent_id == "al-saadi" and source_language == "id":
        filename = "id-tafsir-as-saadi.db"
    dataset_id = Path(filename).stem
    metadata = DATASET_METADATA[dataset_id]
    env_key = f"QURAN_TAFSIR_DB_{agent_id.upper().replace('-', '_')}"
    if agent_id == "al-saadi" and source_language == "id":
        env_key += "_ID"
    configured_path = os.environ.get(f"{env_key}_PATH")
    root = database_dir or Path(
        os.environ.get("QURAN_TAFSIR_DB_DIR", REPOSITORY_ROOT / "data-tafsir")
    )
    path = Path(configured_path).expanduser() if configured_path else root / filename

    return ScholarAgentConfig(
        agent_id=agent_id,
        title=metadata["title"],
        author=metadata["author"],
        author_ar=metadata["author_ar"],
        language=metadata["language"],
        focus=AGENT_FOCUS[agent_id],
        database_path=path,
        dataset_id=dataset_id,
    )


def create_retrieval(config: ScholarAgentConfig) -> TafsirSourceRetrieval:
    return TafsirSourceRetrieval(str(config.database_path))
