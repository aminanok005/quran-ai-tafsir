# Workspace Studio and Local 9Router Design

## Goal

Finalize the existing three-panel study workspace and the Audio, Quiz, and
Infographic Studio flows. Use the user's local 9Router endpoint only after an
explicit Generate action. Keep Notes in PostgreSQL and save artifacts there only
when the user chooses **Save to Note**.

## Scope and non-goals

In scope:

- Preserve and complete the resizable Sources, Reader/Dialogue, and Studio
  panels, including saved layout, collapse shortcuts, and mobile view tabs.
- Keep personal Notes scoped to the existing signed browser identity and stored
  in PostgreSQL.
- Generate an Audio script, a three-choice Quiz, and an Infographic through the
  server-side 9Router integration and render them in Studio.
- Add local playback, immediate quiz feedback, JSON export, and explicit
  artifact-to-Note saving.
- Validate the flows locally without live model or Quran Foundation requests.

Out of scope:

- Strapi/CMS, course authoring, progress, streaks, gems, or user accounts.
- Report, Slides, Video, Flashcards, or Comparison enhancements; existing
  behavior for these kinds remains unchanged.
- External audio, image, or video generation, generated media files, and
  automatic artifact persistence.
- Calling external source APIs only to create a Studio artifact.

## Architecture

Keep the existing Next.js workspace and FastAPI boundaries. The panel layout
continues to use `react-resizable-panels`, persists its sizes and visibility in
`localStorage`, supports `[` and `]` shortcuts outside editable controls, and
uses mobile tabs rather than forcing three narrow columns on small screens.

The browser sends an artifact request to the existing FastAPI workspace route.
FastAPI calls the configured OpenAI-compatible 9Router endpoint using
server-only `LLM_API_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, and
`LLM_API_WIRE_API=responses` settings. Credentials must never reach client code,
logs, or error responses.

Artifact grounding is limited to the currently selected Quran ayah and an
already-loaded, approved Tafsir passage. The API may use only its existing
short-lived in-memory Tafsir cache; it must not fetch a source passage on an
artifact request. Cache misses or expired entries fail closed with an
actionable response asking the user to load the Tafsir passage first. The API
continues to check source permissions server-side and does not trust a
client-supplied approval flag or Tafsir text.

Generated artifacts stay in Studio's current page state. The existing browser
identity and `user_notes` API remain the persistence path: **Save to Note**
creates a Note; generation, editing, export, and quiz progress do not create a
separate database record.

## Artifact contracts and behavior

All three kinds use structured JSON validated by the API before returning it to
the browser. Invalid or incomplete model output is an explicit error; there is
no silent template fallback.

- **Audio:** Return a Thai, two-host script with labeled turns. Use browser
  Speech Synthesis for local playback, with play/stop controls and a clear
  status when the browser or a suitable voice is unavailable. Do not generate
  or upload an audio file.
- **Quiz:** Each question has exactly three options and exactly one valid answer.
  Selecting an option immediately shows correctness and the explanation.
  Progress and score are held only in the current page; they are not persisted.
- **Infographic:** Return structured headings, key points, and layout hints.
  Render these as responsive local cards, without an image-generation service,
  and allow JSON export.

Show Quran citation metadata and include Tafsir citation metadata only when the
source is approved and was available in the server cache. Mark generated output
as `AI-SYNTHESIS`.

## Errors and privacy

Surface actionable errors for missing server configuration, an unreachable or
unauthorized 9Router, invalid structured output, missing approved source
permission, and a Tafsir cache miss. Do not log request credentials or source
text, silently fall back to another provider, or retry generation automatically.
Keep the existing per-browser Studio rate limit.

## Verification

Use the repository's existing pytest, Jest, and TypeScript tooling:

- Unit-test strict output validation for Audio, Quiz, and Infographic.
- Test the API route with a mocked generator and mocked/cache-only Tafsir
  boundary, including the no-cache and unapproved-source failures.
- Assert tests make no outbound model or Quran Foundation calls.
- Test Studio rendering, immediate Quiz feedback, local Audio controls, JSON
  export, Save to Note, and error states with the existing Jest setup.
- Run the web typecheck and targeted API/web tests; do not make a live 9Router
  request as part of implementation or verification.

Live provider operation is not part of local verification. The latest recorded
9Router attempt returned `401 invalid_api_key`; successful live generation must
wait until the endpoint credential is repaired.
