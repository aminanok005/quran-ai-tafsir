# Audio Gateway Spike

Optional, disabled streaming proxy. Accepts structured `reciter`, `surah`, `ayah`, and trusted `audio_number` query parameters; never accepts arbitrary URLs. Uses bounded concurrency, request cancellation, upstream timeout, and preserves `Content-Type`, `Content-Length`, `Accept-Ranges`, and `Content-Range`.

`AUDIO_UPSTREAM_BASE_URL` is restricted at startup to `https://cdn.islamic.network/quran/audio/128`. `GET /health` reports service capabilities for an explicit adapter gate. Not production-integrated. Enable only after security, benchmark, license, and deployment-owner review.
