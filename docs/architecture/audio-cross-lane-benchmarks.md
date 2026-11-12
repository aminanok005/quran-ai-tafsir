# Audio Cross-Lane Benchmark Record

No production benchmark has been recorded. Go and Rust services are isolated spikes, not enabled adapters.

## Local transport baseline

Run on November 12, 2026 using a 64 KiB local `httptest` response and Go 1.25.1. This measures process overhead only, not browser playback, CDN latency, cache behavior, TLS, or production concurrency.

| Path | Latency/op | Throughput | Allocations/op |
| --- | ---: | ---: | ---: |
| Direct upstream (native baseline) | 95.5 us | 686.5 MB/s | 5,799 B / 69 allocs |
| Go gateway | 151.8 us | 431.7 MB/s | 145,736 B / 116 allocs |

Decision: do not enable gateway. It adds local latency and allocations without a proven product benefit. If later enabled, an adapter must forward the global audio number from trusted Quran audio metadata rather than derive it from a local numbering table.

Rerun after gateway hardening: native `83.2 us/op`, `787.7 MB/s`, `5,802 B/op`, versus gateway `150.6 us/op`, `435.1 MB/s`, `146,312 B/op`. Result remains transport-only and supports keeping native playback as default.

## CDN capability check

The tested Alafasy URL responded on November 12, 2026 with `200`, `Content-Type: audio/mpeg`, `Accept-Ranges: bytes`, and `206 Partial Content` for `Range: bytes=0-1023`. The response did not include `Access-Control-Allow-Origin`, so browser `fetch()`/Blob loading remains invalid while native `<audio>` playback remains the correct path. This check does not prove every reciter behaves identically.

Additional spot checks on the same CDN returned `200 audio/mpeg` with ranges for `ar.minshawi` and `ar.husary`, `403 application/xml` for the tested `ar.abdulbasitmurattal` path, and no CORS header in any response. The application currently exposes only `ar.alafasy`, so unsupported reciter paths must not be inferred as CORS failures.

## Required before enablement

- Compare native HTMLAudioElement against Go proxy using startup latency, throughput, memory, cache hit rate, and concurrent playback.
- Run Go unit, race, Range, timeout, cancellation, and SSRF tests.
- Run Rust format, test, clippy, queue-bound, cancellation, output-limit, and shutdown tests.
- Record source license/permission review and deployment owner.

## Current gate

Native cross-origin playback is default because it avoids Blob-fetch CORS failures and requires no extra service. Enable proxy/worker only when measured product requirements justify operational complexity.
