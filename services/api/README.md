# QURAN AI API

The FastAPI bootstrap in `main.py` exposes an ayah-selected tafsir chat API:

- `GET /api/v1/tafsir/agents` lists the four source assistants and the Arabic
  and Indonesian As-Saadi source variants.
- `POST /api/v1/tafsir/chat` accepts `surah`, `ayah`, `scholar_id`, `message`,
  optional `history`, and optional As-Saadi `source_language`.
- `GET /api/v1/quran/surahs/{number}/info` returns Indonesian background
  reading from `surah-info-id.json`, after checking `display` permission for
  `qul:surah-info-id`. It is not sent to an LLM.
- `GET /api/v1/quran/mushaf/15-line/pages/{page_number}` returns page/line
  positions and ayah references from the local KFGQPC V4 layout database.
  Glyph text is not rendered because its V4 Tajweed font is unpublished and
  being proofread; the endpoint requires `display` permission for
  `qul:qpc-v4-tajweed-15-lines`.

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
The Quran endpoints also use `QURAN_QPC_V4_PATH` and
`QURAN_SURAH_INFO_ID_PATH` to locate optional local QUL JSON files, plus
`QURAN_QPC_15_LINE_LAYOUT_PATH` for the Mushaf page map.

For the API schema and data governance rules, see
[`docs/sources/README.md`](../../docs/sources/README.md).
