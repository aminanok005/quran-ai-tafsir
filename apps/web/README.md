# Quran Reader web app

The Thai-first Reader loads chapter metadata and Arabic Uthmani Ayah text from
the FastAPI service. It does not embed Quran text or invent translations.

## Run locally

From the repository root:

```sh
bun install
bun run dev:web
```

In another terminal, start the API:

```sh
python3 -m uvicorn services.api.main:app --reload --port 8000
```

Set `NEXT_PUBLIC_API_BASE_URL` when the API is not at `http://localhost:8000`.
Set `CORS_ORIGINS` for the web app origin when it is not
`http://localhost:3000`.

The Thai translation and Ibn Kathir explanation remain unavailable until an
actual translation and a licensed, verified Tafsir source are integrated.
