# services/api

QURAN AI workspace component.

## Database-backed tafsir translations

Run the API from the repository root with `uvicorn services.api.main:app --reload`.
Set `DATABASE_URL` and `CORS_ORIGINS` in the API server's environment before
starting it. The API reads `LLM_PROVIDER`, `LLM_API_BASE_URL`, `LLM_MODEL`, and
the API key from the shell environment at runtime. `OPENAI_API_KEY` takes
precedence over the legacy `LLM_API_KEY` alias; exported shell values take
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
