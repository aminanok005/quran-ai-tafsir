# Credit-Safe AI and Phase Continuation Design

## Goal

Continue the QURAN AI roadmap without spending external-model credits or letting
an unavailable AI provider break Reader, audio playback, or other non-AI work.
Keep a clear connection point for a locally hosted AI service that speaks an
OpenAI-compatible API.

## Decisions

- Provider choice is explicit and fail-closed. `LLM_PROVIDER` accepts only
  `disabled`, `openai`, or `openai_compatible`; an absent value means
  `disabled`. `openai` uses only `https://api.openai.com/v1` and
  `OPENAI_API_KEY`. `openai_compatible` requires `LLM_API_BASE_URL` and
  `LLM_MODEL`; it uses `LLM_API_KEY`, which may be omitted only for a loopback
  HTTP endpoint. Non-loopback endpoints require HTTPS and an explicit key.
  `LLM_API_WIRE_API` remains limited to the supported `responses` and
  `chat_completions` protocols. Explicitly configured non-loopback HTTPS
  endpoints may be used by routes that already support them, such as Tafsir
  translation and chat suggestions. Preserve Studio's existing loopback-only
  provider restriction; do not broaden it as part of this work. A disabled or
  incomplete configuration makes no LLM request.
- Embeddings have an independent provider selection using the same modes.
  Missing `EMBEDDING_PROVIDER` means disabled. The `openai` mode uses only the
  OpenAI HTTPS endpoint and the dedicated `EMBEDDING_API_KEY`; the compatible
  mode requires `EMBEDDING_API_BASE_URL` and `EMBEDDING_MODEL`, uses only the
  embedding credential, and allows an omitted key only for loopback HTTP.
  Non-loopback embedding endpoints require HTTPS and an explicit key.
  Embeddings never borrow the LLM/OpenAI key. Missing or disabled configuration
  raises the existing safe configuration error before any embedding request.
- A configured local OpenAI-compatible endpoint is an operator-owned inference
  service. Its base URL, model, wire protocol, and optional loopback credential
  remain server-side. This means connecting an inference endpoint, not uploading
  or importing model weights into the web application. There is no automatic
  switch to an external provider, or vice versa.
- External TTS is independently opt-in. It is unavailable and makes no
  synthesis request unless `TTS_ENABLED`, API key, model, base URL, an
  allowlisted supported edition (`th.thai`, `en.sahih`, or `id.indonesian`),
  and a voice for that edition's language are all configured. Retain the
  existing HTTPS-or-loopback-HTTP TTS endpoint validation. Device speech and
  existing recitation continue to work when TTS is unavailable.
- Suggestion generation and other optional AI work may return a retryable,
  generic unavailable result; it must not invalidate an already successful
  grounded answer or prevent non-AI controls from working.
- Tests and in-scope validation use deterministic fixtures, mocks, and local
  services only. No live external AI call, production database, real billing,
  or deployment operation is part of this change.

## Provider boundary

Reuse the existing LLM, embedding, and TTS configurations and HTTP clients
rather than adding a second client SDK. Normalize LLM provider behavior behind
a small server-side boundary that can:

1. determine whether an explicitly selected provider is usable;
2. build requests for the configured Responses or Chat Completions wire format;
3. attach credentials only on the server and only when configured;
4. translate provider failures into generic, non-secret errors; and
5. be replaced by a local OpenAI-compatible service without changing feature
   handlers.

Disabled mode must short-circuit before constructing or sending any AI-provider
request. Configuration errors must be visible to operators through safe
diagnostics, not hidden by fabricated content. Retries are user-triggered only;
there are no automatic or background retries of paid requests. Timeout, quota,
authentication, and malformed-response errors return a generic actionable
unavailable/error response to users. Operators may see the provider category
and numeric HTTP status in logs, but not response bodies, credentials, or
source text. This preserves actionable quota diagnostics without leaking them
through public responses.

This design covers provider availability and its integration with the work
already in progress. It does not authorize or specify the separate Phase 4-6
CMS, gamification, active-recall, billing, or deployment projects. Those remain
separately scoped roadmap tasks with their existing identity, copyright,
rights, and release gates.

## Failure behavior

- Core Reader navigation, selected-ayah context, notes, existing device speech,
  and recitation are independent of external LLM/TTS availability.
- Optional AI generation errors remain isolated from the primary answer or
  lesson view. UI may hide unavailable suggestions or show an actionable
  unavailable state; it must not show fabricated success.
- A local provider's network/auth/protocol error does not trigger an external
  request.
- Retries happen only after a user action; no automatic retry is made for quota,
  rate-limit, timeout, or provider errors.
- Logs, responses, and browser-visible configuration must not contain
  credentials, full provider response bodies, or sensitive source text.
- Existing source approval, browser ownership, score thresholds, rights, and
  migration safety checks remain unchanged.
- Provider selection never bypasses source approval, evidence/relevance
  thresholds, or source-use rights before Quran/Tafsir content is transmitted.

## Out of scope

- Finding, rotating, or adding any API key.
- Importing model weights, training models, or deploying a local inference
  server.
- Automatically retrying paid calls or changing provider account credit/quota.
- Implementing the separate Phase 4-6 CMS, gamification, active-recall, billing,
  or deployment features.
- Applying migrations to production, seeding production data, real billing, or
  production deployment.
- Replacing existing Quran/Tafsir sources or weakening approval requirements.

## Acceptance criteria

- With LLM disabled, Studio, AI translation, and chat-suggestion generation
  make zero LLM-provider calls; optional features return their safe unavailable
  states and successful answers remain successful. Approved Quran/Tafsir source
  retrieval remains a separate, user-requested source-provider operation.
- With embeddings disabled or unconfigured, retrieval scoring makes zero
  embedding-provider calls and reports unavailable scoring without fabricating
  relevance; answer generation remains unaffected where existing behavior
  permits it.
- With TTS disabled or incomplete, capabilities report unavailable and the TTS
  endpoint makes zero source/TTS calls; browser speech/recitation remains
  available.
- With mocked local OpenAI-compatible endpoints, both supported LLM wire
  formats and embedding requests are testable without external network access.
  Credentials remain server-side and never appear in logs, responses, or
  browser-visible configuration.
- Provider failures do not corrupt successful answer state or prevent unrelated
  non-AI work; retryable UI actions require explicit user input.
- Tests prove that a denied or unverified Quran/Tafsir source, including sources
  missing approval evidence or required license metadata, is never included in
  an AI-provider request.
- Tests prove Studio rejects non-loopback provider URLs, while eligible
  OpenAI-compatible routes retain their explicit HTTPS endpoint behavior.
- Tests prove non-loopback HTTP embedding URLs are rejected before any request.
- Tests assert zero provider calls for disabled/misconfigured LLM, embeddings,
  and TTS, and safe handling of timeout, quota/rate-limit, authentication, and
  malformed responses.
- Targeted tests, available offline suites, typecheck, and build run before
  claiming completion. No live AI-provider request is needed for these checks.
