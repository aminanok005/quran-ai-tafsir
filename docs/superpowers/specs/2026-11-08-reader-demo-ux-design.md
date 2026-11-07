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
result from loading. “Empty” means a successful Quran ayah response whose body
is a top-level array or a supported existing envelope (`data`, `surahs`,
`ayahs`, or `translations`) containing a verse array with zero items. A missing,
null, or otherwise malformed verse collection, a failed request, or an
unavailable Quran dataset must remain an error state, not an empty result. Once
data arrives, retain the current ayah navigation,
Arabic size controls, translation, and audio interactions, while tightening
hierarchy and spacing so the selected ayah is the visual focus.

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
  missing/null verse data, malformed-response, and loaded states.
- Run the web Jest suite and TypeScript typecheck.
- Verify the home page and `/?view=reader` in the browser at
  `http://localhost:3000`, including the responsive Reader layout.
- Confirm no API keys or generated local data were staged.
