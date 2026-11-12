# Reader Audio Contract v1

Frontend is current producer and consumer. Future Go and Rust services may implement this contract behind adapters.

## AudioRequest

```json
{"version":1,"source":"recitation","reciter":"ar.alafasy","surah":1,"ayah":1,"format":"mp3","speed":1,"request_id":"reader-generation-id"}
```

`source` is `recitation` or `translation-ai`. `surah` and `ayah` are per-surah coordinates. `request_id` is opaque and must not contain credentials.

## Playback events

Events use `version: 1`, `request_id`, `surah`, `ayah`, and one of `loading`, `cache-hit`, `cache-miss`, `native-playback`, `buffer-decoded`, `preload-armed`, `playing`, `stopped`, `aborted`, or `failed`.

Failures use safe codes: `aborted`, `cors-unavailable`, `upstream`, `invalid-payload`, `quota`, or `unavailable`. Never include provider response bodies, credentials, or full translation text.

## Limits

- One current item and one next-item preload per sequence.
- Every request accepts cancellation.
- Every generated object URL has one owner and a defined revoke point.
- Cross-origin URLs without CORS use native audio and skip Blob loading.
