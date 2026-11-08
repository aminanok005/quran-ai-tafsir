# Smart Translation Audio Design

## Goal

Let Reader users listen to the selected Quran translation in Thai, English, or
Indonesian using either an explicitly selected AI-generated voice or a matching
voice available on their device. Keep `Listen Audio` and `Auto`, while replacing
the always-visible settings card with a compact summary button that reveals
settings on demand and reports real playback work.

## Relationship to the existing Reader audio design

This design builds on
[`2026-11-08-reader-audio-autoplay-design.md`](./2026-11-08-reader-audio-autoplay-design.md).
The earlier design's browser-only speech boundary remains the default when AI
audio is not configured; this phase adds an optional AI translation-audio path.
Recitation remains the existing Alafasy audio and is never synthesized or
modified. Translation text remains the exact text returned by the selected
Quran edition; AI may vocalize it but must not translate, rewrite, summarize,
or add to it.

## User experience

- Keep `Listen Audio`, `Auto`, and the existing recitation, translation, and
  recitation-then-translation playback modes.
- Replace the always-visible options card with a compact, keyboard-operable
  summary button. Initially keep settings collapsed. The button summarizes
  playback mode, translation language when relevant, selected voice engine,
  and speed, and opens/closes the settings.
- In the expanded settings, allow users to choose:
  - Thai, English, or Indonesian translation.
  - AI voice or device voice for translation. AI voice is selectable only when
    the server advertises that it is configured and the current edition is
    allowed. Device voice uses Web Speech and requires a matching `th`, `en`,
    or `id` locale.
  - A supported playback speed from 0.85x, 1x, or 1.15x. Apply the rate to both
    the selected voice engine and every Alafasy recitation segment, including
    recitation-only and combined playback.
- Default to device voice when AI is unavailable. Show this choice and its
  reason in the collapsed summary; never switch engines silently after an AI
  request or playback error.
- Announce genuine statuses in a polite live region: fetching translation,
  generating/loading AI audio, playing recitation, speaking translation,
  using device voice, cache hit when known, completion, cancellation, and
  actionable errors. A failed AI request stops the current sequence and Auto;
  it does not fall back to device voice.
- The AI voice setting explicitly informs the user that translation text is
  sent to the configured audio provider to synthesize speech. The browser sends
  only surah, ayah, edition, and speed to the app backend, not arbitrary text.

## Backend and provider

- Add a dedicated, opt-in TTS configuration, separate from LLM credentials and
  model configuration. Default it off. Enable it only when the operator sets a
  TTS API key/base URL/model and explicitly lists editions approved for external
  processing. Do not infer TTS support from the LLM provider.
- Use an OpenAI-compatible speech endpoint via the existing `httpx` dependency.
  Keep the provider base URL configurable and keep credentials server-side.
  Require HTTPS except for explicitly recognized loopback hosts for local
  development. Configure a voice per supported language.
- Add a capabilities endpoint that reports availability, supported languages,
  and only the edition identifiers the server allows; never return secrets or
  internal provider error details.
- Add a generated-audio endpoint keyed by surah, ayah, allowed edition, and
  speed. Resolve the exact translation server-side from the same
  `https://api.alquran.cloud/v1/surah/{surah}/{edition}` source used by the
  Reader's existing Quran Cloud proxy; the edition segment must come only from
  the fixed `th.thai`, `en.sahih`, and `id.indonesian` mapping and then pass the
  configured allowlist. In this Quran Cloud surah response, validate that
  `data.number` matches the requested surah and `ayahs[].numberInSurah` matches
  the requested ayah, requiring actual JSON integer identifiers (not booleans
  or numeric strings); these are the response's surah and ayah identifiers, so
  do not rely on a separate nested `ayah.surah.number` field. Require
  non-empty text. Send that exact text to the provider only after all
  configuration and allowlist checks pass. Never accept arbitrary text or a
  source URL from the browser. Reject invalid ranges, unsupported editions,
  missing translations, oversized text, and invalid provider audio responses
  with safe client errors.
- Return MPEG audio bytes and a cache outcome header. Use a bounded,
  process-local TTL/LRU cache keyed by edition, verse, source-text hash, model,
  configured voice, and speed. Bound both entry count and aggregate cached
  bytes; remove expired entries during cache maintenance and do not cache an
  item that exceeds the aggregate cache budget. Cache only successful validated
  audio. Do not persist translation text or audio to a database or disk.
- Expose the cache outcome response header through CORS so the Reader can
  distinguish cache hits from newly synthesized audio when the API is
  cross-origin.
- Apply an atomic, bounded per-client request rate limit using the existing
  Redis dependency so counts are shared by API workers. Use an atomic
  increment-and-expire operation and hashed client-address keys with a bounded
  TTL so limiter keys are cleaned up and raw IPs are not stored. Use only the
  direct request client address unless a deployment has explicitly configured
  trusted proxy handling; do not trust arbitrary `X-Forwarded-For` input. A
  Redis error fails closed for TTS requests instead of permitting unmetered
  provider calls. Apply provider timeout, source-response-size, and
  provider-output-size limits before buffering or parsing. Enforce an absolute
  deadline over each complete source and provider response stream, not only an
  inactivity timeout between network reads. Keep API keys, raw provider errors,
  and full translation text out of logs and responses. External HTTP and Redis
  dependencies must be injectable in tests.
- Create the translation-audio service once during FastAPI lifespan startup,
  store it on app state, and close its HTTP/Redis clients during shutdown. The
  request dependency must reuse this instance rather than lazily constructing
clients concurrently on first requests. Shutdown must attempt both client
closes even if one close operation fails, then propagate the cleanup error;
if both closes fail, preserve both errors. Preserve cancellation as the
propagated outcome if a client close is cancelled, while recording any
secondary cleanup failure.
- Document that operators are responsible for confirming the source edition's
  permission for external TTS processing before allowlisting it.

## Reader integration

- Fetch TTS capabilities from the API and treat errors as "AI unavailable"
  with an explicit device-voice explanation; do not make Reader loading fail.
- Add API client methods for capabilities and audio bytes.
- Extend the existing playback coordinator so translation playback selects the
  requested engine, waits for audio completion before Auto advances, and aborts
  pending fetch/speech on stop, setting changes, navigation, and unmount.
- Create and revoke browser object URLs for generated audio on replacement,
  completion, cancellation, and unmount. Preserve the existing generation guard
  so late network/audio callbacks cannot advance or mutate a newer sequence.
- Track only active/in-flight object URLs; do not retain every revoked URL for
  the lifetime of the Reader.
- Keep current edition mapping (`th.thai`, `en.sahih`, `id.indonesian`) and
  exact source text. Preserve existing Alafasy recitation playback and
  translation readiness/error behavior.

## Accessibility and failure behavior

- All settings remain native labeled controls and work with keyboard/focus.
- The summary button exposes its expanded state and current selection to assistive
  technology. Keep the live status region visible whether settings are
  collapsed or expanded.
- If capabilities, translation fetch, TTS generation, audio playback, or device
  voice selection fails, expose an actionable status and stop without advancing
  Auto. Do not log or display provider response bodies or credentials.
- Manual navigation, changing mode/language/engine/speed, or pressing Stop
  cancels outstanding requests and playback. AI cache hits are still reported
  as AI audio playback, not as newly generated work.

## Out of scope

- Generating, changing, or translating Quran translation text.
- Generating Quran recitation, replacing the existing recitation source, or
  combining audio engines without a user-selected playback mode.
- Persistent/shared audio storage, accounts, subscriptions, provider fallback,
  background prefetch, or server-side voice cloning.
- Enabling any edition for external processing by default.

## Validation

- Backend unit/API tests cover disabled-by-default configuration, allowlist and
  edition checks before network calls, supported language-to-edition mapping,
  exact source text forwarding, safe errors, request and response bounds,
  provider failures, rate limits, cache miss/hit/expiry/eviction, and capabilities
  without secrets.
- Web tests cover collapsed defaults and expanded settings, summaries for all
  three languages and both voice engines, AI unavailability messaging, speed
  and engine selection, exact selected edition use, blob URL cleanup, cache
  status, errors without fallback, cancellation/stale callbacks, and Auto
  progression for each language and playback mode.
- Run focused backend/web tests, the existing web test suite, type checking,
  and production build. Verify the Reader on desktop and narrow viewport.
