# Reader Demo UX/UI Design

## Goal and scope

Polish the three-panel Reader/Studio workspace so the local demo at
`http://localhost:3000/?view=reader` feels usable from first load. The landing
page is out of scope for this pass. Keep Quran text and Tafsir API-backed; do
not add synthetic verse content or a local Tafsir fallback.

## Design

Keep the current calm, green-and-neutral visual language and the responsive
Sources / Reader / Studio layout. Improve the Reader's first-load experience:
show clear loading feedback while Quran data is pending; show a useful,
retryable error state when a request fails; and distinguish a genuine empty
result from loading. The Reader loads ayahs from
`GET /api/quran/surahs/{surah}/ayahs/`; a successful response is currently a
top-level array of QPC ayah objects. The parser also supports existing
`data`, `surahs`, `ayahs`, and `translations` envelope keys when their value is
an array. “Empty” means that successful array has zero items. A missing, null,
or non-array collection, a malformed array item, a non-success HTTP response,
or an unavailable QPC dataset (currently a 404 `{ "detail": ... }` response)
must remain an error state, not an empty result. Once data arrives, retain the
current ayah navigation, Arabic size controls, translation, and audio
interactions, while tightening hierarchy and spacing so the selected ayah is
the visual focus.

Make the local demo open directly into the Reader, without changing the
homepage's existing default route. Ensure status messages are accessible and
mobile navigation remains usable. Keep provider generation manual and preserve
existing citation and source-permission rules.

## Implementation boundaries

- Use the existing Next.js API routes and Quran data loader; do not introduce a
  second data source or mock Quran content.
- Keep state local to the Reader unless an existing shared helper fits.
- Do not redesign marketing sections, authentication, or the database/API
  contracts.
- Do not read or expose `.env.local`.

## Validation

- Add focused tests for the Reader's loading, error/retry, successful empty,
  missing/null verse data, malformed-response, unavailable-QPC-dataset (404),
  and loaded states; the unavailable dataset test must assert the error state
  and that the empty-state message is absent.
- Run the web Jest suite and TypeScript typecheck.
- Verify the home page and `/?view=reader` in the browser at
  `http://localhost:3000`, including the responsive Reader layout.
- Confirm no API keys or generated local data were staged.
