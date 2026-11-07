# services/ingestion

Pure Python source-policy and development parser helpers. No parser performs writes or network access.

## Development Tafsir parsing

Use `DevelopmentProvenance` with an explicit `source_id` and dataset path/name. Parsed records are always marked:

```text
permission_status=development_only
verification_status=unverified
ingestion_mode=development
production_eligible=false
```

`parse_json_file` handles objects keyed by `surah:ayah`. `parse_sqlite_file` opens SQLite files in read-only mode and defaults to the `tafsir` table. Invalid keys, duplicate keys, missing text, and empty text are reported as `ParseIssue` entries. Raw source text remains unchanged; `normalized_text` is separate derived search text.

Missing license, source URL, volume, and page remain `None`. The parser does not infer them from dataset names, URLs, repository presence, or content. Development embedding collection helper returns only `tafsir_development`; no production collection is selectable through this parser.

`build_development_embedding_document` creates provider-neutral text and metadata only. It does not call an embedding provider, create vectors, or write an index. Metadata keeps source, dataset, work, scholar, edition, license, evidence, passage boundaries, permission state, verification state, ingestion mode, and production eligibility.

Run focused tests:

```bash
cd services/ingestion
python3 -m unittest -v
```

This parser is for research and engineering only. It does not establish legal authorization or production approval.

## Development-only PostgreSQL/pgvector ingestion

`postgres.py` maps parsed records into the existing canonical schema:
`scholars`, `tafsir_books`, `source_permissions`, and `tafsir_passages`.
Stable UUIDs and `ON CONFLICT` updates make passage re-ingestion repeatable.
Every write is hard-coded to `development_only` permission and `unverified`
status; this parser cannot ingest into the approved production corpus.

The repository-root script `scripts/ingest_tafsir_vectors.py` defaults to a
no-network, no-database dry run. Writes require `--apply-development-only`,
`ENVIRONMENT=development`, a 1536-dimensional embedding provider, and an
explicit development database URL. Raw Arabic text is stored unchanged; only
normalized search text is sent to the embedding endpoint. API keys and source
text are not printed.

No schema change is required: `services/api/migrations/versions/0001_initial_setup.py`
already enables pgvector and creates the `vector(1536)` column and HNSW index.
