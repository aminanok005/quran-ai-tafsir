# QURAN AI API

The FastAPI bootstrap in `main.py` exposes an ayah-selected tafsir chat API:

- `GET /api/v1/tafsir/agents` lists the four source assistants and the Arabic
  and Indonesian As-Saadi source variants.
- `POST /api/v1/tafsir/chat` accepts `surah`, `ayah`, `scholar_id`, `message`,
  optional `history`, and optional As-Saadi `source_language`.

Run the API from the repository root with
`uvicorn services.api.main:app --reload --env-file .env`. The Next.js app uses
same-origin server routes to proxy requests, so browser CORS is not required for
this integration. Configure `CORS_ORIGINS` only for separately hosted browser
clients.

The response contains the original passage, its language and source citation,
separately from the AI-generated Thai explanation. The assistant does not
impersonate the named scholar and is instructed not to invent source details.

Provision the five `.db` files in `data-tafsir/` (or configure
`QURAN_TAFSIR_DB_DIR`). Source display and LLM processing are denied unless
`TAFSIR_RIGHTS_MANIFEST` names a reviewed source with an approved license,
review timestamp, evidence reference, decision note, and `display`,
`quotation`, and `ai_processing` permissions. Set `TAFSIR_LLM_API_KEY` (or
`LLM_API_KEY`/`OPENAI_API_KEY`) and optionally `TAFSIR_LLM_MODEL` and
`TAFSIR_LLM_BASE_URL` to enable generated responses. The OpenAI-compatible
adapter can also be pointed at another compatible provider, such as OpenRouter.

For the API schema and data governance rules, see
[`docs/sources/README.md`](../../docs/sources/README.md).
