# Quran and Tafsir Data Integration

## Recommendation

Use the **Quranic Universal Library (QUL) resource downloads as the first
ingestion source**. QUL groups Quran scripts, translations, tafsir, recitations,
morphology, topics, surah information, and structural metadata in one resource
catalog. Its downloads are available as JSON and SQLite, so the MVP does not
need to depend on a new API or keep a third-party service available at query
time.

QUL is a resource catalog, not a single authoritative edition. Each downloaded
resource must be registered and reviewed independently. Confirm that the
specific book, translation, edition, format, and intended use are available
before importing it.

> QUL's public API documentation currently says the REST API is still in
> design. Use resource downloads until that status changes; do not build a
> production integration against the proposed `/api/v1` URL.

## Source choices

| Need | First choice | Integration mode | Important limitation |
|---|---|---|---|
| Quran text and related Quran data | QUL | Download a selected resource; JSON for initial inspection, SQLite for larger/query-heavy resources | Record the exact script and resource version; validate text and all 6,236 ayahs |
| Tafsir corpus | QUL tafsir resources, one book/edition at a time | Import only after source, edition, and rights review | Resource availability and ayah/page mapping vary by book; do not assume all six PRD scholars are covered |
| Live Quran API | Quran Foundation API, only if runtime freshness is required | Backend adapter with server-side credentials | Separate product/API from QUL; verify access, permitted use, Thai translation IDs, and API terms |
| Additional tafsir books | Shamela or another licensed provider, as an optional adapter | Controlled ingestion into the same local schema | Credentials, book coverage, edition metadata, and permissions must be verified before use |
| Hadith and grading | A separately reviewed hadith source | Later, dedicated collection/adapter | QUL's documented categories do not establish a complete hadith corpus or grading service |

For the simplest MVP, start with **one QUL Quran text resource, one verified
Thai translation if available, and one available/licensed tafsir edition**.
Keep Quran Foundation API and Shamela out of the critical path until a concrete
need, access, and usage rights are confirmed. If the required Thai translation
is unavailable or unsuitable, select and review a separate translation source;
never silently substitute an English translation and label it Thai.

## Identified QUL tafsir resources

These are resource records supplied for this project. The corresponding SQLite
datasets are now present locally in `data-tafsir/` and are available to the
retrieval adapter. They are registered as **source-attributed, not
scholarly-verified corpora**. The download links below are preserved verbatim.
The paired IDs were supplied in JSON-then-SQLite order; confirm the returned
file name, format, schema, and checksum after any refresh rather than relying
on that order alone.

| Corpus | Local SQLite file | QUL resource record | Language and review status |
|---|---|---|---|
| Tafsir As-Saadi (Arabic) | `data-tafsir/tafsir-as-saadi.db` | Arabic Resource page not yet identified | Arabic text, rights/edition review pending |
| Tafsir As-Saadi (Indonesian) | `data-tafsir/id-tafsir-as-saadi.db` | [Resource 503](https://qul.tarteel.ai/resources/tafsir/503) | Indonesian; not a Thai tafsir. QUL page screenshot says copyright information is unavailable; rights review pending |
| Tafsir al-Tabari | `data-tafsir/ar-tafsir-al-tabari.db` | [Resource 37](https://qul.tarteel.ai/resources/tafsir/37) | Arabic; edition and rights review pending |
| Tafsir Ibn Kathir | `data-tafsir/ar-tafsir-ibn-kathir.db` | [Resource 22](https://qul.tarteel.ai/resources/tafsir/22) | Arabic; edition and rights review pending |
| Tafsir al-Qurtubi | `data-tafsir/ar-tafseer-al-qurtubi.db` | Resource record not yet identified | Arabic; resolve resource record, edition, and rights |

The files use a `tafsir` table keyed by `ayah_key`, with `group_ayah_key`,
`from_ayah`, `to_ayah`, `ayah_keys`, and HTML `text`. Some records intentionally
have empty text because a passage is attached to a grouped ayah; retrieval falls
back to that group record and cites the range stored in the database. Page and
volume are not present in this schema and are therefore never displayed.

The `.db` files are ignored by Git (`*.db`): provision them in the runtime
workspace rather than expecting them in a clone or deployment artifact. By
default each source assistant reads its matching file under `data-tafsir/`.
Use `QURAN_TAFSIR_DB_DIR` to change the database directory or the per-agent
`QURAN_TAFSIR_DB_*_PATH` environment variables to select a specific file. The
Indonesian As-Saadi corpus is selectable separately and is never labeled Arabic
or Thai.

All local files are usable for retrieval, but their passages carry
`verified=false` and `rights_status=unknown` until the underlying edition,
accuracy, and intended usage rights have been reviewed. Do not treat successful
SQLite retrieval as scholarly verification or permission for public display.

## Local RAG export and rights-gated training

Build a normalized JSONL corpus for local RAG indexing:

```sh
python3 -m services.tafsir.dataset_builder
```

The default output is `data/processed/tafsir-rag.jsonl` (ignored by Git). Each
chunk retains its book, author, source language, source ID, ayah/group mapping,
QUL URL, and review/rights statuses. The builder requires all five local
databases and fails rather than silently exporting a partial corpus. Each
source must separately permit `storage` and `indexing` before its text can be
written into the normalized RAG corpus. The ayah chat endpoint currently
retrieves an exact ayah/group passage from the source SQLite database; the
JSONL corpus is the normalized input for later full-text or embedding indexing,
not a semantic index by itself.

Public/API display and LLM processing are disabled unless a source has status
`approved`, a license, reviewer, timezone-aware review timestamp, evidence
reference, decision note, and the specific uses `display`, `quotation`, and
`ai_processing` in `allowed_uses`. Fine-tuning requires a separate
`model_training` grant. Start the local review workflow (the manifest defaults
to `data-tafsir/rights-manifest.json`):

A QUL account welcome/confirmation email or access to a download is not, by
itself, evidence of permission for a particular resource or for display,
storage, indexing, quotation, or AI processing. The public
[dataset guide](https://qul.tarteel.ai/docs/datasets) identifies dataset
categories, and the [download guide](https://qul.tarteel.ai/docs/downloading-data)
describes technical ingestion; neither substitutes for the license or
resource-specific permission terms. Record only the uses actually granted for
each exact resource.

```sh
python3 -m services.tafsir.rights_review status
python3 -m services.tafsir.rights_review record qul:ar-tafsir-ibn-kathir \
  --status approved \
  --reviewed-by "reviewer identifier" \
  --decision-note "Reason for the source-specific decision" \
  --evidence-ref "path/to/license-or-permission-evidence.pdf" \
  --license "Exact license or permission identifier" \
  --allow display --allow quotation --allow ai_processing
python3 -m services.tafsir.rights_review validate
```

Add `--allow storage --allow indexing` only when evidence also grants local
RAG corpus creation/indexing; add `--allow model_training` only when training
is explicitly covered. `record` appends an audit history and validates the
required approval fields, but only records the reviewer's attestation: it does
not verify evidence or make a legal determination. Never approve a source based
only on the presence of a local file. Sources not reviewed with actual evidence
must remain `pending` and stay disabled.

Fine-tuning examples must be manually authored or reviewed and separately
approved for `model_training`. The CLI only exports two-message
user/assistant examples with a human reviewer and an approved source permission:

Each annotation JSONL record has this shape; replace the placeholder content
with an expert-reviewed prompt/answer and source-specific ayah reference:

```json
{
  "source_id": "qul:ar-tafsir-ibn-kathir",
  "ayah_key": "1:1",
  "human_reviewed": true,
  "reviewed_by": "reviewer identifier",
  "messages": [
    {"role": "user", "content": "Reviewed question"},
    {"role": "assistant", "content": "Reviewed answer"}
  ]
}
```

```sh
python3 -m services.tafsir.dataset_builder \
  --annotations data/curation/tafsir-annotations.jsonl \
  --rights-manifest data-tafsir/rights-manifest.json \
  --fine-tune-output data/processed/tafsir-finetune.jsonl
```

With the current rights state (`unknown`/`pending`), no source is eligible for
training. Raw tafsir passages are not automatically turned into synthetic
supervised answers.

## Ayah chat API

The API exposes `GET /api/v1/tafsir/agents` and
`POST /api/v1/tafsir/chat`. The chat request contains `surah`, `ayah`,
`scholar_id` (`ibn-kathir`, `al-tabari`, `al-qurtubi`, or `al-saadi`),
`message`, optional `history`, and optional As-Saadi `source_language` (`ar`
or `id`). Responses keep the exact source excerpt and source language separate
from the AI-generated Thai explanation. Configure `TAFSIR_LLM_API_KEY` (or
`LLM_API_KEY`/`OPENAI_API_KEY`), `TAFSIR_LLM_MODEL`, and optionally
`TAFSIR_LLM_BASE_URL` before asking for generated responses. For web clients,
configure `CORS_ORIGINS` as a comma-separated allowlist (defaults to
`http://localhost:3000`). The Next.js frontend uses a same-origin server-side
proxy for tafsir and keeps the backend URL and model credentials off the
browser. Quran text uses a same-origin proxy with a direct AlQuran.cloud browser
fallback if server-to-server access is unavailable; in that fallback, the
browser contacts that public text provider. Set
`TAFSIR_API_URL` in `apps/web/.env.local` when the backend is not at
`http://127.0.0.1:8000`.

## Official references

- [QUL datasets](https://qul.tarteel.ai/docs/datasets)
- [QUL API status](https://qul.tarteel.ai/docs/api)
- [QUL data model](https://qul.tarteel.ai/docs/data-model)
- [QUL downloading data](https://qul.tarteel.ai/docs/downloading-data)
- [QUL resources](https://qul.tarteel.ai/resources)
- [Quranic Universal Library repository](https://github.com/TarteelAI/quranic-universal-library)
- [Quran Foundation API documentation](https://api-docs.quran.com/docs/api-reference/)

QUL's resource page warns that material from external sources may be incomplete
or contain errors, and that translations are references rather than definitive
interpretations. Importing a resource must therefore not automatically mark
its content `VERIFIED`.

## Ingestion flow

1. Select the exact resource from the QUL resources catalog and record its URL,
   resource identifier, format, retrieval date, and checksum.
2. Review the underlying source, author/translator, edition, license, and
   permissions for display, quotation, storage, indexing, and AI processing.
   Record unknown rights as blocked; do not ingest or expose the content until
   reviewed.
3. Download and inspect the file. Use JSON for a small first sample and
   SQLite for larger resources or repeated local queries. Keep raw downloads
   immutable and separate from normalized records.
4. Map fields with a resource-specific adapter. Common joins are
   `surah_id + ayah_number` for ayah-level content and
   `surah_id + ayah_number + word_position` for word-level content. Preserve
   the original identifiers and raw metadata; do not infer missing page or
   volume values.
5. Normalize into PostgreSQL and validate UTF-8, required fields, unique keys,
   expected record counts, ayah references, Arabic text preservation, and
   resource-specific metadata. Import into staging first.
6. Require a human source review for each book/edition before publication.
   Build exact-text and full-text indexes after validation. Add embeddings only
   as a discovery aid, never as proof that a quote or citation is authentic.
7. Publish the approved dataset version atomically and retain an audit record
   of the import, validation, reviewer, and rights decision.

## Citation and agent rules

- Keep each book/edition as a distinct source collection. The agent ID may
  describe the corpus and methodology (for example, Ibn Kathir's tafsir); it
  must not imply that the AI is the scholar.
- Retrieve exact source passages before generation. Semantic search may find
  candidates, but claims and quotations must be tied to the stored passage.
- Cite only metadata present in the imported edition: book, author, edition,
  volume, page, chapter, ayah mapping, source URL, and resource version as
  available. Never invent page numbers, edition details, hadith grades, or
  chains of transmission.
- Label generated commentary as AI synthesis and keep it visibly separate
  from Arabic source quotations and human-reviewed translations.
- If a relevant passage, reliable mapping, or permission is missing, abstain
  and show that the source could not be verified.
- Preserve disagreements between books. Do not combine independent
  interpretations into a single attributed position.

## MVP acceptance checks

- The selected dataset's rights and bibliographic record are approved before
  public display or production use.
- Quran text imports preserve the selected Arabic script exactly and all
  expected ayah keys map to `1..114` and each surah's expected ayah count.
- Translation records retain translator, language, resource, and version.
- Tafsir passages can be traced to an imported source record and only expose
  volume/page when those values exist in the source.
- Retrieval returns no results when the approved corpus is empty; it never
  substitutes demonstration or fabricated source passages.
- Every generated quotation resolves to an exact stored excerpt and citation.
- A data refresh can be repeated without duplicate records and can be audited
  or rolled back by dataset version.

## Scope boundary

This guide defines source selection and integration. QUL does not replace
scholarly review, does not guarantee that each desired tafsir is available,
and does not provide a documented complete hadith verification pipeline.
Enable agents incrementally only after their actual source collections pass
the acceptance checks above.
