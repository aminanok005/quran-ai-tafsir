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

### Tafsir source in development

When `ENVIRONMENT=development` (the default), the Reader looks for a cached
passage in PostgreSQL first. On a cache miss, the API requests that single ayah
from the authenticated Quran Foundation Content API v4 Tafsir endpoint and
caches the response in PostgreSQL. Cached API passages are always marked
`development_only`/`unverified`; production never fetches or returns these
records. The development cache does not assert that the source is licensed for
reuse. Review rights, attribution, and verification evidence before promoting
any source to production or enabling translation.

Configure the Quran Foundation credentials on the API server only:

```text
QURAN_API_BASE_URL=https://apis-prelive.quran.foundation
QURAN_API_CLIENT_ID=<pre-live client ID>
QURAN_API_CLIENT_SECRET=<pre-live client secret>
QURAN_API_TAFSIR_SCOPE=content.tafsirs.read
QURAN_TAFSIR_RESOURCE_MAP={"ibn_kathir":169}
```

Use the production API host with production credentials, or the pre-live host
with pre-live credentials; OAuth is selected to match the API host. The default
resource mapping is Ibn Kathir English (resource 169). Override it with a JSON
object mapping the application's scholar IDs to resource IDs available to your
Quran Foundation account. Confirm IDs and languages against the API's current
resource list rather than assuming IDs from third-party examples. Keep all
credentials server-side.

Translation of a development-only API passage remains blocked until its source
book and permission record are explicitly approved, verified, and licensed.
The existing JSON importer and local JSON corpus remain separate tools for
development-only vector ingestion; they are not used as the Reader's Tafsir
runtime fallback. Long approved passages are split into word-boundary chunks
and translated in order.

## Study workspace: Notes and Studio

Apply the current database migrations before using saved notes:

```bash
DATABASE_URL=<development-database-url> \
  python3 -m alembic -c services/api/alembic.ini upgrade head
```

`GET/POST /api/v1/workspace/notes` and `PATCH/DELETE
/api/v1/workspace/notes/{id}` store personal notes in PostgreSQL. The API issues
a random browser identity in a signed, HttpOnly cookie and scopes every query by
that identity; notes are not shared across browsers or devices, and clearing the
cookie loses access to that browser's notes. Configure a strong `SECRET_KEY`
outside development. This anonymous browser identity is not a substitute for a
user account or account recovery.

`POST /api/v1/workspace/artifacts` creates a source-grounded Report, Slides,
Video storyboard, Audio script, Flashcards, three-choice Quiz, Infographic, or
Comparison table using the server-side LLM configuration above. Tafsir context
is loaded server-side and included only when both the book and its source
permission record are approved and verified; client-supplied approval flags or
Tafsir text are never trusted. Quran citations are included with the generated
content, which is labeled `AI-SYNTHESIS`. Audio uses the browser's speech
synthesis; Video is an editable/exportable storyboard, not a rendered video
file. Studio generation is limited to five requests per minute per browser.

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
