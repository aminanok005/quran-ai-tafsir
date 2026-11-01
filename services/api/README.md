# Quran Reader API

The `main.py` entry point provides a small server-side proxy to the public
Quran.com API v4:

- `GET /health`
- `GET /api/v1/surahs`
- `GET /api/v1/surahs/{surah_id}/ayahs`

By default, the proxy uses `https://api.quran.com/api/v4`. Override
`QURAN_COM_API_BASE_URL` with the full API v4 base URL if needed. The proxy
returns the provider's source data and reports upstream failures as HTTP 502;
it does not cache, modify, or synthesize Quran text.

Run locally from the repository root:

```sh
python3 -m uvicorn services.api.main:app --reload --port 8000
```

Configure `CORS_ORIGINS` as a comma-separated list when the web app runs on a
different origin. The older `app.py` service is separate and is not used by
these Reader endpoints.

## Test

```sh
python3 -m pytest tests/test_quran_reader_api.py
```
