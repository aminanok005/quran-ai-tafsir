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
  server-side local 9Router integration and render them in Studio. In local
  development, a provider request is allowed only after an explicit Generate
  click.
- Add local playback, immediate quiz feedback, JSON export, and explicit
  artifact-to-Note saving.
- Validate the flows locally with offline automated checks and mocked
  generation/source boundaries.

Out of scope:

- Strapi/CMS, course authoring, progress, streaks, gems, or user accounts.
- Report, Slides, Video, Flashcards, or Comparison enhancements; existing
  behavior for these kinds remains unchanged.
- External audio, image, or video generation, generated media files, and
  automatic artifact persistence.
- Calling external source APIs only to create a Studio artifact or calling a
  remote LLM provider.

## Architecture

Keep the existing Next.js workspace and FastAPI boundaries. The panel layout
continues to use `react-resizable-panels`, persists its sizes and visibility in
`localStorage`, supports `[` and `]` shortcuts outside editable controls, and
uses mobile tabs rather than forcing three narrow columns on small screens.

The browser sends an artifact request to the existing FastAPI workspace route.
FastAPI calls the configured local OpenAI-compatible 9Router endpoint using
server-only `LLM_API_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, and
`LLM_API_WIRE_API=responses` settings. A request is made only in direct response
to the user's Generate action; page load, selection changes, prefetching, and
automatic retries must not call the provider. Credentials must never reach
client code, logs, or error responses.

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

The workspace continues to map `[` to toggling the Sources panel and `]` to
toggling Studio; shortcuts are ignored while focus is in an editable control.
On mobile, Reader, Sources, Dialogue, and Studio remain selectable tabs.

## Artifact contracts and behavior

All three kinds use structured JSON validated by the API before returning it to
the browser. Shared fields are `title` (1–160 characters) and `summary` (0–500
characters). Invalid or incomplete model output is an explicit error; there is
no silent template fallback.

- **Audio:** Return `segments`, an array of 4–8 entries. Each entry has a
  `host` (`Host A` or `Host B`) and non-empty Thai `text` (maximum 1,200
  characters). Start with `Host A` and alternate hosts. Use browser Speech
  Synthesis for local playback, with play/stop controls and a clear status when
  the browser or a suitable voice is unavailable. Do not generate or upload an
  audio file.
- **Quiz:** Return `questions`, exactly five entries. Each has a non-empty
  `question` (maximum 500 characters), exactly three non-empty `options`
  (maximum 200 characters each), one `answer_index` from 0 to 2, and a
  non-empty `explanation` (maximum 1,000 characters). Selecting an option
  immediately shows correctness and the explanation. Progress and score are
  held only in the current page; they are not persisted.
- **Infographic:** Return a non-empty `key_takeaway` (maximum 500 characters)
  and 3–6 `cards`. Each card has a non-empty `heading` (maximum 100 characters)
  and 2–5 non-empty `points` (maximum 280 characters each). Optional
  `layout_hint` is one of `stacked`, `two-column`, or `sequence`. Render these
  as responsive local cards, without an image-generation service, and allow
  JSON export.

Keep source metadata separate from editable artifact content. Render clickable
citation pills below the artifact title: `[1] <surah name> <surah>:<ayah>` links
to the canonical Quran page, and `[2] <resource name>` links to the source URL
returned by the API only when that Tafsir is approved and was available in the
server cache. Do not construct or trust Tafsir citation URLs from browser input.
Mark generated output as `AI-SYNTHESIS`.

The JSON editor edits the artifact's `title`, `summary`, and kind-specific
content fields, but not server-returned citations or evidence status. Valid JSON
matching the active artifact schema updates the preview; invalid JSON leaves
the last valid preview intact, shows a validation error, and blocks Save and
Export until corrected. Export the validated artifact envelope, including
server-returned citations and evidence status, as JSON. **Save to Note** stores
that same validated envelope in the existing note `content` field, uses the
edited title, and records the selected ayah/source metadata through the existing
note API.

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
- Assert automated tests make zero network calls, including to 9Router and
  Quran Foundation. Manual
  Generate clicks in local development may call only the configured local
  9Router; no automated test may do so.
- Test Studio rendering, immediate Quiz feedback, local Audio controls, JSON
  export, editable JSON validation, citation links, Save to Note, and error
  states with the existing Jest setup.
- Test panel persistence, the `[`/`]` mapping outside editable controls, and
  mobile view-tab selection.
- Run the web typecheck and targeted API/web tests; do not make a 9Router
  request as part of automated verification.

Automated verification does not validate live provider operation. The latest
recorded 9Router attempt returned `401 invalid_api_key`; successful manual
generation requires the endpoint credential to be repaired.
