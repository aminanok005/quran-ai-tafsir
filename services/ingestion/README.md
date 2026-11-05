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
