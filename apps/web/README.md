# Quran AI web app

## Local setup

Install the workspace dependencies from the repository root with `bun install`.
Copy `apps/web/.env.example` to `apps/web/.env.local`; set `TAFSIR_API_URL` if
the FastAPI server is not running on `127.0.0.1:8000`.

1. Configure the backend environment and rights manifest as described in
   [`services/api/README.md`](../../services/api/README.md).
2. Start the backend from the repository root:
   `uvicorn services.api.main:app --reload --env-file .env`.
3. Start the web app with `bun run dev:web`, then open `http://localhost:3000`.

The Quran reader fetches Uthmani text, the Thai King Fahad Quran Complex
translation (`th.thai`), and Alafasy recitation (`ar.alafasy`) from
AlQuran.cloud. The Thai translation and Arabic source are displayed separately,
with edition attribution. Audio playback uses the provider's verse audio URLs.
QPC V4 script and Indonesian surah background reading can be served from local
QUL files configured with `QURAN_QPC_V4_PATH` and
`QURAN_SURAH_INFO_ID_PATH`. Background reading is only displayed when the
rights manifest explicitly allows `display` for `qul:surah-info-id`.
The 604-page KFGQPC V4 15-line map is configured with
`QURAN_QPC_15_LINE_LAYOUT_PATH`; the reader shows its verse-location map but
keeps glyph rendering disabled while the source font is unpublished.
Surah navigation, ayah study, local bookmarks, recent reading history, and
resume-reading are available without an account; bookmark/history data stays
in the browser's local storage.

Tafsir requests are proxied server-to-server to FastAPI; LLM secrets are never
sent to the browser. The study panel can compare independently enabled source
agents while keeping each answer and citation separate. Tafsir chat remains
disabled until source rights permit display, quotation, and AI processing. A
local database alone does not grant those rights.

Production deployment needs the same backend URL, tafsir databases, reviewed
rights manifest, and server-side LLM settings. The Quran text provider must be
reachable from the Next.js server. If browser local storage is unavailable or
full, reading and study remain usable in-session and the app explains that
bookmarks/history could not be saved.
