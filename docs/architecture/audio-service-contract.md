# Audio Service Contract v1

Go is future optional producer. FastAPI and browser-native playback remain valid implementations.

## Request

Production adapters use structured coordinates plus the global audio number from trusted Quran audio metadata, never an arbitrary user URL:

```text
GET /api/v1/quran/audio/{reciter}/{surah}/{ayah}.mp3?audio_number=<1-6236>
Range: bytes=<start>-<end>
```

`audio_number` is resolved from the selected upstream Quran audio record before proxying; the gateway never derives it with an unverified local table. Only allowlisted reciters and formats are accepted. Unknown hosts, paths, query forwarding, and redirects to unapproved hosts are rejected.

## Response

Successful responses preserve `Content-Type`, `Content-Length` when known, `Accept-Ranges`, `Content-Range` for `206`, `ETag`, and `Last-Modified` when supplied.

Errors use JSON `{ "version": 1, "code": "...", "message": "..." }` without upstream bodies or secrets.

## Security and performance

- Stream bytes; never buffer unbounded audio files.
- Enforce connect, read, total-duration, and response-size limits.
- Enforce bounded concurrent upstream requests.
- Propagate cancellation from client disconnect to upstream request.
- Cache only validated allowlisted audio responses.
