"""Build normalized local RAG corpora and rights-gated fine-tuning datasets."""

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List

from .agents import DEFAULT_DATABASES, REPOSITORY_ROOT
from .rights import (
    load_rights_manifest,
    permission_allows,
    validate_rights_manifest_structure,
)
from .source_retrieval import (
    DATASET_METADATA,
    _json_record,
    _load_json_dataset,
    _visible_text,
    connect_readonly,
)

DEFAULT_SOURCE_FILES = tuple(dict.fromkeys(DEFAULT_DATABASES.values())) + (
    "id-tafsir-as-saadi.db",
)
DEFAULT_RAG_OUTPUT = REPOSITORY_ROOT / "data" / "processed" / "tafsir-rag.jsonl"


def _resolve_source_path(source_dir: Path, database_filename: str) -> Path:
    json_path = source_dir / Path(database_filename).with_suffix(".json").name
    database_path = source_dir / database_filename
    return json_path if json_path.is_file() else database_path


def _chunks(text: str, max_chars: int) -> Iterator[str]:
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    pending = ""
    for paragraph in text.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        while len(paragraph) > max_chars:
            boundary = paragraph.rfind(" ", 0, max_chars + 1)
            if boundary <= 0:
                boundary = max_chars
            piece, paragraph = paragraph[:boundary].strip(), paragraph[boundary:].strip()
            if pending:
                yield pending
                pending = ""
            if piece:
                yield piece
        if pending and len(pending) + len(paragraph) + 1 > max_chars:
            yield pending
            pending = paragraph
        else:
            pending = f"{pending}\n{paragraph}".strip()
    if pending:
        yield pending


def iter_rag_records(source_path: Path, max_chars: int = 2000) -> Iterator[Dict[str, Any]]:
    source_id = source_path.stem
    metadata = DATASET_METADATA.get(source_id)
    if metadata is None:
        raise ValueError(f"Unrecognized tafsir dataset: {source_path.name}")
    rights_sources = load_rights_manifest().get("sources", {})
    permission = rights_sources.get(f"qul:{source_id}", {})
    if not isinstance(permission, dict) or not permission_allows(
        permission, ["storage", "indexing"]
    ):
        raise PermissionError(
            f"Tafsir source {source_id} is not approved for storage and indexing"
        )
    rights_status = permission["status"]
    if source_path.suffix.lower() == ".json":
        stat = source_path.stat()
        records = _load_json_dataset(
            str(source_path.resolve()), stat.st_mtime_ns, stat.st_size
        )
        for ayah_key, value in records.items():
            if isinstance(value, str) and value in records:
                continue
            passage = _json_record(records, ayah_key)
            if passage is None:
                continue
            original_text = _visible_text(passage["raw_text"])
            mapped_ayah_keys = passage["ayah_keys"]
            group_key = passage["group_ayah_key"]
            start, end = mapped_ayah_keys[0], mapped_ayah_keys[-1]
            ayah_range = start if start == end else f"{start}-{end}"
            yield from _iter_source_chunks(
                source_id,
                metadata,
                permission,
                rights_status,
                ayah_key,
                group_key,
                mapped_ayah_keys,
                ayah_range,
                original_text,
                "qul_json",
                max_chars,
            )
        return

    if source_path.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}:
        raise ValueError(f"Unsupported tafsir source format: {source_path.suffix}")
    connection = connect_readonly(source_path.resolve())
    try:
        rows = connection.execute(
            """SELECT ayah_key, group_ayah_key, from_ayah, to_ayah, ayah_keys, text
               FROM tafsir WHERE COALESCE(text, '') <> '' ORDER BY ayah_key"""
        )
        for ayah_key, group_key, from_ayah, to_ayah, ayah_keys, raw_html in rows:
            original_text = _visible_text(raw_html or "")
            mapped_ayah_keys = [
                key.strip()
                for key in (ayah_keys or "").split(",")
                if key.strip()
            ] or [ayah_key]
            start = from_ayah or ayah_key
            end = to_ayah or start
            ayah_range = start if start == end else f"{start}-{end}"
            yield from _iter_source_chunks(
                source_id,
                metadata,
                permission,
                rights_status,
                ayah_key,
                group_key or ayah_key,
                mapped_ayah_keys,
                ayah_range,
                original_text,
                "qul_sqlite",
                max_chars,
            )
    finally:
        connection.close()


def _iter_source_chunks(
    source_id: str,
    metadata: Dict[str, Any],
    permission: Dict[str, Any],
    rights_status: str,
    ayah_key: str,
    group_key: str,
    mapped_ayah_keys: List[str],
    ayah_range: str,
    original_text: str,
    source_backend: str,
    max_chars: int,
) -> Iterator[Dict[str, Any]]:
    if not original_text:
        return
    for chunk_number, chunk in enumerate(_chunks(original_text, max_chars)):
        yield {
            "schema_version": 1,
            "chunk_id": f"qul:{source_id}:{ayah_key}:{chunk_number}",
            "source_id": f"qul:{source_id}",
            "dataset_id": source_id,
            "author": metadata["author"],
            "author_ar": metadata["author_ar"],
            "book": metadata["title"],
            "book_ar": metadata["title_ar"],
            "language": metadata["language"],
            "ayah_key": ayah_key,
            "group_ayah_key": group_key,
            "ayah_keys": mapped_ayah_keys,
            "ayah_range": ayah_range,
            "chunk_index": chunk_number,
            "original_text": chunk,
            "resource_url": metadata["resource_url"],
            "rights_status": rights_status,
            "license": permission.get("license"),
            "allowed_uses": permission.get("allowed_uses", []),
            "verification_status": "not_reviewed",
            "source_backend": source_backend,
        }


def write_rag_corpus(
    source_dir: Path = REPOSITORY_ROOT / "data-tafsir",
    output_path: Path = DEFAULT_RAG_OUTPUT,
    max_chars: int = 2000,
) -> int:
    source_paths = [
        _resolve_source_path(source_dir, filename) for filename in DEFAULT_SOURCE_FILES
    ]
    missing = [
        filename
        for filename, source_path in zip(DEFAULT_SOURCE_FILES, source_paths)
        if not source_path.is_file()
    ]
    if missing:
        raise FileNotFoundError(
            f"Missing required tafsir databases in {source_dir}: {', '.join(missing)}"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    record_count = 0
    with tempfile.TemporaryDirectory(dir=output_path.parent) as temporary_dir:
        temporary_path = Path(temporary_dir) / output_path.name
        with temporary_path.open("w", encoding="utf-8") as output:
            for source_path in source_paths:
                for record in iter_rag_records(source_path, max_chars):
                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                    record_count += 1
        os.replace(temporary_path, output_path)
    return record_count


def approved_finetuning_records(
    annotations: Iterable[Dict[str, Any]],
    rights_manifest: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Only pass through human-reviewed examples with explicit training permission."""
    approved: List[Dict[str, Any]] = []
    structure_issues = validate_rights_manifest_structure(rights_manifest)
    if structure_issues:
        raise ValueError(f"Invalid rights manifest: {'; '.join(structure_issues)}")
    sources = rights_manifest.get("sources", {})
    for annotation in annotations:
        if not isinstance(annotation, dict):
            continue
        source_id = annotation.get("source_id")
        if not isinstance(source_id, str):
            continue
        permission = sources.get(source_id, {})
        if (
            not isinstance(permission, dict)
            or not permission_allows(permission, ["model_training"])
        ):
            continue
        if annotation.get("human_reviewed") is not True:
            continue
        if not isinstance(annotation.get("reviewed_by"), str) or not annotation[
            "reviewed_by"
        ].strip():
            continue
        messages = annotation.get("messages")
        if (
            not isinstance(messages, list)
            or len(messages) != 2
            or any(not isinstance(message, dict) for message in messages)
            or [message.get("role") for message in messages]
            != ["user", "assistant"]
            or any(not isinstance(message.get("content"), str) for message in messages)
            or any(not message["content"].strip() for message in messages)
        ):
            continue
        approved.append(
            {
                "source_id": source_id,
                "ayah_key": annotation.get("ayah_key"),
                "reviewed_by": annotation["reviewed_by"],
                "messages": messages,
            }
        )
    return approved


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=REPOSITORY_ROOT / "data-tafsir")
    parser.add_argument("--rag-output", type=Path, default=DEFAULT_RAG_OUTPUT)
    parser.add_argument("--max-chars", type=int, default=2000)
    parser.add_argument("--annotations", type=Path)
    parser.add_argument("--rights-manifest", type=Path)
    parser.add_argument("--fine-tune-output", type=Path)
    args = parser.parse_args()

    count = write_rag_corpus(args.source_dir, args.rag_output, args.max_chars)
    print(f"Wrote {count} RAG chunks to {args.rag_output}")
    if args.fine_tune_output:
        if not args.annotations or not args.rights_manifest:
            parser.error(
                "--fine-tune-output requires --annotations and --rights-manifest"
            )
        annotations = _read_jsonl(args.annotations)
        with args.rights_manifest.open(encoding="utf-8") as manifest_file:
            rights_manifest = json.load(manifest_file)
        examples = approved_finetuning_records(annotations, rights_manifest)
        args.fine_tune_output.parent.mkdir(parents=True, exist_ok=True)
        with args.fine_tune_output.open("w", encoding="utf-8") as output:
            for example in examples:
                output.write(json.dumps(example, ensure_ascii=False) + "\n")
        print(f"Wrote {len(examples)} approved fine-tuning examples")


if __name__ == "__main__":
    main()
