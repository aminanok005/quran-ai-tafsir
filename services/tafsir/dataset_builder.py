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
from .source_retrieval import DATASET_METADATA, _visible_text, connect_readonly

DEFAULT_SOURCE_FILES = tuple(dict.fromkeys(DEFAULT_DATABASES.values())) + (
    "id-tafsir-as-saadi.db",
)
DEFAULT_RAG_OUTPUT = REPOSITORY_ROOT / "data" / "processed" / "tafsir-rag.jsonl"


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


def iter_rag_records(database_path: Path, max_chars: int = 2000) -> Iterator[Dict[str, Any]]:
    source_id = database_path.stem
    metadata = DATASET_METADATA.get(source_id)
    if metadata is None:
        raise ValueError(f"Unrecognized tafsir dataset: {database_path.name}")
    rights_sources = load_rights_manifest().get("sources", {})
    permission = rights_sources.get(f"qul:{source_id}", {})
    if not isinstance(permission, dict) or not permission_allows(
        permission, ["storage", "indexing"]
    ):
        raise PermissionError(
            f"Tafsir source {source_id} is not approved for storage and indexing"
        )
    rights_status = permission["status"]
    connection = connect_readonly(database_path.resolve())
    try:
        rows = connection.execute(
            """SELECT ayah_key, group_ayah_key, from_ayah, to_ayah, ayah_keys, text
               FROM tafsir WHERE COALESCE(text, '') <> '' ORDER BY ayah_key"""
        )
        for ayah_key, group_key, from_ayah, to_ayah, ayah_keys, raw_html in rows:
            original_text = _visible_text(raw_html or "")
            if not original_text:
                continue
            start = from_ayah or ayah_key
            end = to_ayah or start
            ayah_range = start if start == end else f"{start}-{end}"
            mapped_ayah_keys = [
                key.strip()
                for key in (ayah_keys or "").split(",")
                if key.strip()
            ] or [ayah_key]
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
                    "group_ayah_key": group_key or ayah_key,
                    "ayah_keys": mapped_ayah_keys,
                    "ayah_range": ayah_range,
                    "chunk_index": chunk_number,
                    "original_text": chunk,
                    "resource_url": metadata["resource_url"],
                    "rights_status": rights_status,
                    "license": (
                        permission.get("license")
                        if isinstance(permission, dict)
                        else None
                    ),
                    "allowed_uses": (
                        permission.get("allowed_uses", [])
                        if isinstance(permission, dict)
                        and isinstance(permission.get("allowed_uses"), list)
                        else []
                    ),
                    "verification_status": "not_reviewed",
                    "source_backend": "qul_sqlite",
                }
    finally:
        connection.close()


def write_rag_corpus(
    source_dir: Path = REPOSITORY_ROOT / "data-tafsir",
    output_path: Path = DEFAULT_RAG_OUTPUT,
    max_chars: int = 2000,
) -> int:
    missing = [
        filename for filename in DEFAULT_SOURCE_FILES if not (source_dir / filename).is_file()
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
            for filename in DEFAULT_SOURCE_FILES:
                database_path = source_dir / filename
                for record in iter_rag_records(database_path, max_chars):
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
