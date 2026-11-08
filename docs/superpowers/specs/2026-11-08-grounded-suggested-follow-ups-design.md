# Grounded Suggested Follow-Ups Design

## Goal and scope

Add API-backed follow-up suggestions to the Reader's Grounded dialogue. Users
can select one or several suggestions below an answer and ask them together.
Suggestion content must come from the API, and the server must prove eligibility
from the exact approved source set associated with that answer. Suggestion
failures must never invalidate the answer.

The current Reader keeps only one submitted question/answer at a time, and the
API has no chat session, message, or retrieval-snapshot store. The current agent
route fetches API passages by ayah but does not calculate relevance scores or
return message IDs. The retired local Tafsir search must remain retired; it is
not an acceptable fallback.

## Recommended approach

Use the existing Postgres database and browser identity to own chat-message
retrieval snapshots. Extend the existing grounded-answer flow to accept a
browser-generated session ID and persist a server-generated assistant message
ID together with the original question, selected agent/source IDs, and
retrieval records. Return the session and assistant message IDs in the answer
response so the client can request suggestions for that answer. A retrieval
record contains a source identity, a relevance score calculated from the exact
question and source passage using the configured embedding service, and a hash
of the passage text. Do not persist source text: when suggestions are requested,
re-fetch only those exact source identities, re-check current source
permission/readiness, and compare the content hash. Changed or unavailable
sources are excluded. If snapshot persistence fails, log the failure and return
the answer with follow-up availability marked false; do not fail the answer.

If the retrieval set is empty, the embedding provider is unavailable, the
highest valid similarity is below `0.72`, or no source remains enabled and
approved, return an empty suggestions array. Never invent or default a score.
The existing answer is returned independently of retrieval scoring and
suggestion generation.

Add `POST /api/v1/chat/suggestions` with the specified `{session_id,
message_id}` request and `{suggestions: [...]}` response. It loads the
browser-owned message snapshot, generates candidate questions from only the
revalidated source content, validates them with strict Pydantic v2 models, then
applies category filters before returning at most four:

- `compare`: at least two distinct scholars represented in the user's selected
  and currently enabled sources.
- `deepen`: at least one source has both volume and page.
- `context`: at least one selected, enabled neighboring-ayah or asbab
  al-nuzul source.
- `review`: may be generated for any qualifying retrieval set and is labeled
  `AI_SYNTHESIS`.

The generation contract includes internal supporting source IDs for every
candidate; these IDs are not part of the public `Suggestion` response. Reject
candidates with missing, duplicate, or unapproved supporting IDs, or IDs not
present in that message's revalidated retrieval set. Apply category rules to
the candidate's supporting sources, not merely to all available chunks.
Calculate `basisCount` from the distinct currently valid supporting sources and
set `evidence` server-side (`AI_SYNTHESIS` for `review`, otherwise
`SOURCE_ATTRIBUTED`). Invalid candidate categories are discarded without
replacement requirements.

Treat generated text as untrusted: reject candidates that quote or reproduce a
source passage, that request a fatwa/religious ruling in supported languages,
or that fail a question/instruction shape check. Instruct the generator not to
quote source content or solicit rulings; validate these requirements before
returning a candidate. If no candidate survives, return an empty array.

Keep a local Reader conversation history so each assistant answer retains its
own suggestions. One selected prompt is sent as ordinary user text. Multiple
prompts are sent as a single numbered user message, with an explicit instruction
to answer in separate headings and retain citations for each section. On
successful submission, clear that answer's selection and fetch suggestions for
the new assistant message. Loading uses four skeleton cards; empty and error
responses hide the section without changing the answer.

## Alternatives considered

1. **Process-local cache:** simpler, but loses snapshots on restart and cannot
   reliably serve multiple workers. Rejected.
2. **Re-enable local vector Tafsir search:** it provides stored passage scores,
   but the endpoint is intentionally retired in favor of API-sourced content.
   Rejected.
3. **Postgres message snapshots with live source revalidation (recommended):**
   preserves message-specific provenance, honors current source permissions,
   and fails closed when scoring or source metadata is missing.

## Boundaries and behavior

- Add a canonical Alembic migration for browser-scoped sessions and
  message-to-source retrieval metadata; do not apply it to production.
- The existing approved Quran Foundation source path remains authoritative.
  Categories requiring metadata it does not currently return (volume/page,
  neighboring ayahs, or asbab al-nuzul) remain absent until such approved
  records are actually retrieved; do not synthesize eligibility.
- Keep suggestion generation and retrieval errors separate from the primary
  answer path. Surface operational errors through existing API logging, and
  return no suggestions to the UI for suggestion-only failures.
- Scope session and message lookup by the existing browser identity. IDs alone
  must not expose another browser's conversation.
- UI strings are localized consistently with the Reader; suggestion titles,
  prompts, and counts are always API response data, never hard-coded content.
- Preserve existing answer citations, source-rights checks, and audio/note
  behavior.

## Validation

- Backend: pytest for empty retrieval, scores below, at, and above `0.72`,
  compare with one versus two scholars, deepen without volume/page, context
  without a neighboring-ayah/asbab source, review evidence, disabled/unavailable
  sources reducing `basisCount`, browser ownership, changed passage hashes,
  malformed or untrusted candidate source IDs, quoted-text/fatwa rejection,
  embedding failure preserving the answer, and suggestion-generation failure
  isolation. Run `python -m compileall`.
- Frontend: component/integration tests for loading, empty, hidden error,
  category/evidence labels, toggles, clearing, one/multiple prompt submission,
  per-answer suggestion state, and response refresh after sending.
- Run the existing web typecheck and build, plus focused web tests.
- Validate the toolbar review follow-up: clicking “ถาม AI” must open the
  explanation form with the selected ayah context.
- Do not apply database migrations to production or introduce local Tafsir
  fallbacks.
