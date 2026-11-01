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
DEFAULT_JSON_SOURCES = {
    agent_id: Path(filename).with_suffix(".json").name
    for agent_id, filename in DEFAULT_DATABASES.items()
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
        source_filename = "id-tafsir-as-saadi.json"
    else:
        source_filename = DEFAULT_JSON_SOURCES[agent_id]
    dataset_id = Path(filename).stem
    metadata = DATASET_METADATA[dataset_id]
    env_key = f"QURAN_TAFSIR_DB_{agent_id.upper().replace('-', '_')}"
    source_env_key = f"QURAN_TAFSIR_SOURCE_{agent_id.upper().replace('-', '_')}_PATH"
    if agent_id == "al-saadi" and source_language == "id":
        env_key += "_ID"
        source_env_key = "QURAN_TAFSIR_SOURCE_AL_SAADI_ID_PATH"
    configured_path = os.environ.get(f"{env_key}_PATH")
    configured_source_path = os.environ.get(source_env_key)
    root = database_dir or Path(
        os.environ.get("QURAN_TAFSIR_DB_DIR", REPOSITORY_ROOT / "data-tafsir")
    )
    if configured_source_path:
        path = Path(configured_source_path).expanduser()
    elif configured_path:
        path = Path(configured_path).expanduser()
    elif (root / source_filename).is_file():
        path = root / source_filename
    else:
        path = root / filename

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
