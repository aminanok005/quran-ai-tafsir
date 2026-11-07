# services/api

QURAN AI workspace component.

## Quran Foundation Tafsir runtime

Run the API from the repository root with `uvicorn services.api.main:app --reload`.
The API loads repository-root `.env` and `.env.local` files regardless of the
current working directory. `.env.local` overrides `.env`, while exported shell
variables take precedence over both. Set `DATABASE_URL` and `CORS_ORIGINS` in
one of these sources before starting the API. The API reads `LLM_PROVIDER`,
`LLM_API_BASE_URL`, `LLM_MODEL`, and the API key from the same configuration.
Use `LLM_API_KEY` for OpenAI-compatible custom endpoints (including local
routers). `OPENAI_API_KEY` is used only with `https://api.openai.com`; it is not
sent to custom endpoints. Set `LLM_API_WIRE_API=responses` when the endpoint
uses the Responses API; otherwise it defaults to `chat_completions`.

The Reader uses `GET /api/v1/tafsir/passages/{surah}/{ayah}?agent_type=...` to
fetch each original passage from the authenticated Quran Foundation Content API
v4. Raw Tafsir is cached in API process memory for
`QURAN_API_TAFSIR_CACHE_TTL_SECONDS` (default 300 seconds), never written to
`tafsir_passages` or another database table. The Reader loads saved Thai AI
translations only when the corresponding source-permission record is approved,
verified, licensed, and has verification evidence and a source URL.

The LLM key is used only by the API and is never sent to the browser. Translation
is limited to five requests per minute per API worker and is blocked unless the
source-permission record is approved, verified, and has a license, source URL,
and verification evidence. Unapproved source text can still be viewed, but its
cached Thai translation is not returned. Very long passages (>30,000 characters)
require editorial segmentation before translation.

For local Studio generation, configure `ENVIRONMENT=development`,
`LLM_API_BASE_URL` to a loopback provider endpoint, `LLM_MODEL`, and
`LLM_API_WIRE_API=responses` when the endpoint uses the Responses API.
`LLM_API_KEY` is server-only and must never be included in client code, logs, or
error responses. The workspace generation route rejects production mode and
non-loopback provider hosts.

The JSON importer remains separately rights-gated. Do not mark a source as
approved or import it into a production database until its rights and
verification evidence have been reviewed. Imported/local Tafsir is not a Reader
fallback.

Configure the Quran Foundation credentials on the API server only:

```text
QURAN_API_BASE_URL=https://apis-prelive.quran.foundation
QURAN_API_CLIENT_ID=<pre-live client ID>
QURAN_API_CLIENT_SECRET=<pre-live client secret>
QURAN_API_TAFSIR_SCOPE=content.tafsirs.read
QURAN_API_TAFSIR_CACHE_TTL_SECONDS=300
QURAN_TAFSIR_RESOURCE_MAP={"ibn_kathir":168}
```

Use the production API host with production credentials, or the pre-live host
with pre-live credentials; OAuth is selected to match the API host. The default
resource mapping is Ibn Kathir English (resource 168). Override it with a JSON
object mapping scholar IDs to resources enabled for your Quran Foundation
account, and verify resource IDs/languages against that account. Keep credentials
server-side. The Quran seeding CLI is a separate development-only tool; it does
not run automatically when the API starts.

`POST /api/v1/tafsir/passages/api/{surah}/{ayah}/translate?agent_type=...`
translates a live API passage and saves only the generated Thai text, its source
hash/reference, resource/ayah identifiers, model, and timestamps in
`tafsir_api_translations`. It never persists the raw source passage.
`POST /api/v1/tafsir/passages/{passage_id}/translate` returns HTTP 410; clients
must use the API-passage route. Apply migrations before using saved translations:

```bash
DATABASE_URL=<development-database-url> \
  python3 -m alembic -c services/api/alembic.ini upgrade head
```

The local JSON importer and vector search remain development/research tooling,
not a source fallback for the Reader. Do not use their imported Tafsir as
current source text.

### Grounded agent explanations

The versioned `POST /api/v1/tafsir/agents/explain` endpoint accepts `ayah_id`
as a query parameter and `agent_types` plus optional `context` in the JSON body.
The API fetches each configured scholar passage directly from Quran Foundation,
and only supplies it to agents when its source-permission record is approved,
verified, and licensed. It returns only outputs whose citations resolve to those
live passages. Citation records include canonical references and passage-level
`VERIFIED` status; generated explanations are labeled `SOURCE-ATTRIBUTED`, never
`VERIFIED`. The workspace's “Ask AI” view displays these labels and citations.
`POST /api/v1/tafsir/agents/compare` remains unavailable until claim-level
scholarly positions can be tied to reviewable evidence; it returns an explicit
unavailable response rather than inferring disagreement.

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
is fetched from Quran Foundation server-side and included only when its source
permission record is approved and verified; client-supplied approval flags or
Tafsir text are never trusted. Quran citations are included with the generated
content, which is labeled `AI-SYNTHESIS`. Audio uses the browser's speech
synthesis; Video is an editable/exportable storyboard, not a rendered video
file. Studio generation is limited to five requests per minute per browser.

Audio, Quiz, and Infographic generation calls the configured provider only after
the user clicks **Generate**; mounting the workspace, changing a source, or
choosing an artifact kind does not call it. If Tafsir is selected, its passage
must already be approved and present in the short-lived API cache. A cache miss
or permission failure is returned to the user without fetching a replacement or
falling back to database/JSON Tafsir. Generated artifacts are not persisted
automatically; **Save to Note** stores the complete artifact envelope in the
browser-identity-scoped Notes service. Automated tests mock provider and Quran
transports and make no external requests.

If translation returns HTTP 429 with an exhausted-credit/quota message, the
configured provider account must have available API billing/usage quota before
translation can succeed. This is separate from the ChatGPT subscription. A
temporary request-rate limit will instead ask the user to wait and retry.

## Retired database-backed Tafsir retrieval

`POST /api/v1/tafsir/search` returns HTTP 410. The previous endpoint searched
`tafsir_passages` and could serve imported source text, so it is retired rather
than used as a fallback for current Tafsir. Any future search feature must ground
results in Quran Foundation API content and must not read raw Tafsir from the
legacy corpus.

The embedding and local-vector ingestion utilities remain only for isolated
development/research work and tests; they are not part of Reader, Ask AI, or
Studio runtime paths.

### Development-only vector ingestion (offline research)

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
