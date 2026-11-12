# Reader Event Contract v1

Reader events cross frontend, optional service adapters, and observability. They are diagnostic metadata, not source content.

```json
{"version":1,"event":"playing","request_id":"reader-generation-id","surah":1,"ayah":1,"engine":"native","cache_status":"bypass"}
```

Allowed engines: `native`, `web-audio`, `go-proxy`, `rust-worker`.

Allowed cache states: `hit`, `miss`, `bypass`, `unknown`.

Events must not include Quran passage text, translation text, Tafsir text, provider payloads, URLs containing credentials, or raw IP addresses.

Optional engines are capability-gated. Missing or unhealthy Go/Rust services must leave native/FastAPI behavior available.
