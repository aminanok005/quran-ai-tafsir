# services/api

QURAN AI workspace component.

## Database-backed tafsir translations

Run the API from the repository root with `uvicorn services.api.main:app --reload`.
Set `DATABASE_URL` and `CORS_ORIGINS` in the API server's environment before
starting it. The API reads `LLM_PROVIDER`, `LLM_API_BASE_URL`, `LLM_MODEL`, and
the API key from the shell environment at runtime. Use `LLM_API_KEY` for
OpenAI-compatible custom endpoints (including local routers). `OPENAI_API_KEY`
is used only with `https://api.openai.com`; it is not sent to custom endpoints.
Set `LLM_API_WIRE_API=responses` when the endpoint uses the Responses API;
otherwise it defaults to `chat_completions`. Exported shell values take
precedence over `.env` values.

The Reader uses `GET /api/v1/tafsir/passages/{surah}/{ayah}?agent_type=...` to
load an imported source passage. Selecting “แสดงตัฟซีรและแปลเป็นไทย” uses the
stored Thai translation when available; otherwise the API translates the Arabic
passage with OpenAI and caches the result in `tafsir_passages.thai_translation`.

The LLM key is used only by the API and is never sent to the browser. Translation
is limited to five requests per minute per API worker and is blocked unless the
book and its source-permission record are approved, verified, and have a license,
source URL, and verification evidence. Unapproved source text can still be viewed
in Arabic, but its cached Thai translation is not returned. Very long passages
(>30,000 characters) require editorial segmentation before translation.

The JSON importer remains separately rights-gated. Do not mark a source as
approved or import it into a production database until its rights and
verification evidence have been reviewed.

### Local development using the JSON corpus

When `ENVIRONMENT=development` (the default), the Reader loads the selected
passage directly from the matching `data-tafsir/*.json` file and translates
only that passage on demand. This path does not connect to PostgreSQL or write
translations to the database; translated passages are cached in API process
memory. Production continues to use the database-backed, rights-gated routes.
Long passages are split into word-boundary chunks and translated in order.
The LLM key remains server-side and must be provided through the existing
runtime environment variables.

If translation returns HTTP 429 with an exhausted-credit/quota message, the
configured provider account must have available API billing/usage quota before
translation can succeed. This is separate from the ChatGPT subscription. A
temporary request-rate limit will instead ask the user to wait and retry.

## Tafsir vector retrieval

The canonical initial migration already enables pgvector and creates
`tafsir_passages.embedding vector(1536)` with a cosine HNSW index. No new table
or migration is needed for semantic lookup. The `POST /api/v1/tafsir/search`
endpoint accepts a query, optional paired surah/ayah filters, optional scholar
filter, and a bounded `top_k`; it returns source references, similarity, and
the stored evidence status. Production searches include only explicitly
approved and verified source/book records. Development data is isolated behind
`include_development=true`, is available only when `ENVIRONMENT=development`,
and is never eligible for production results. Thai text remains hidden unless
the existing source-rights checks allow its disclosure. Search is limited to 30
requests per minute per API worker to bound embedding usage.

Configure embeddings independently from the translation model:

```text
EMBEDDING_PROVIDER=openai
EMBEDDING_API_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=<server-side embedding key>
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_DIMENSIONS=1536
```

An OpenAI-compatible provider can be used by setting
`EMBEDDING_PROVIDER=openai_compatible` and its HTTPS base URL. Plain HTTP is
restricted to loopback addresses. The API does not reuse an LLM/OpenAI
translation key as an embedding credential, and request text or credentials are
not logged.

### Development-only vector ingestion

The existing local JSON corpus can be checked without external calls or database
writes:

```bash
python3 scripts/ingest_tafsir_vectors.py \
  --file data-tafsir/ar-tafsir-ibn-kathir.json \
  --source-id dev-tafsir-ibn-kathir \
  --dataset ar-tafsir-ibn-kathir.json \
  --scholar-id ibn_kathir \
  --scholar-name "Ibn Kathir" \
  --book-title "Tafsir al-Qur'an al-Azim"
```

This is a dry run. Embedding and PostgreSQL writes require the explicit
`--apply-development-only` flag, `ENVIRONMENT=development`, a separate
embedding-provider key, and the configured development `DATABASE_URL`.
Imported records are always marked `development_only`/`unverified`, retain the
raw Arabic source, and use stable IDs for repeatable ingestion. Do not run
against production. Existing source-rights records are not overwritten or
promoted. Database migrations and ingestion have not been run as part of this
change.
