# Reader Audio Playback UX Design

## Goal

Make Reader audio controls clear and non-duplicative while supporting optional
spoken translations and hands-free, verse-by-verse playback. Preserve the
existing `Listen Audio` action and the API-backed Quran content. This design
covers the Reader only; it does not add generated audio or change Tafsir and
Studio behavior.

## Current context

The selected ayah currently has a `Listen Audio` button that calls `play()` on
an audio element, plus a second visible native audio player labeled
“เสียงอ่าน · อัลอะฟาซี”. Both refer to the same Alafasy recitation. The Reader
already loads Alafasy audio and Thai translation from Quran Cloud through local
Next.js API routes. The translation route currently permits `th.thai` and
`ar.alafasy`; it will need to permit the established English and Indonesian
translation editions `en.sahih` and `id.indonesian`.

## Playback controls

- Keep one visible `Listen Audio` button for the selected ayah. It plays the
  selected playback mode for that ayah.
- Remove the duplicate visible native audio player and its repeated
  Alafasy-only label. Use one shared, non-visible audio element internally for
  recitation playback.
- Add a compact playback mode selector:
  - Alafasy recitation
  - Spoken translation
  - Alafasy followed by spoken translation
- When a translation mode is selected, provide a language selector for Thai,
  English, or Indonesian. Use the existing Thai edition by default.
- Add an `Auto` control. It starts continuous playback at the selected ayah
  using the selected mode and language. While active, it is labeled `Stop Auto`
  and stops the sequence when activated. For each ayah, finish the chosen audio
  sequence before advancing; in combined mode, recitation plays first and
  translation follows.

## Continuous playback behavior

After an ayah's selected audio sequence completes, select the next ayah,
update the Reader's existing location state, and scroll that ayah into view.
Stop automatically after the last ayah in the surah. Starting Auto clears an
active search so all subsequent ayahs remain visible. Manual ayah or surah
selection, a playback-mode/language change, or an explicit stop cancels the
current sequence and speech. Pressing `Listen Audio` plays only the selected
ayah and stops any active Auto run before starting.

Speech translation uses the browser's Web Speech API and the selected
translation text fetched from the existing Quran route. It is not presented as
a scholarly recitation or a prerecorded translation. When a matching language
voice or speech synthesis support is unavailable, show an actionable status
and do not silently substitute another voice or language.

## Data flow and failure behavior

The Reader requests only the selected translation edition, normalizes it
through the existing Quran response validation, and maps text by ayah number.
The API route explicitly allows `th.thai`, `en.sahih`, and `id.indonesian`,
while continuing to reject other editions. Alafasy continues to use the
existing `ar.alafasy` audio payload.

Use a monotonically increasing playback generation for each start/stop or
sequence interruption. Every asynchronous continuation and audio/speech event
captures its generation and must verify it is still current before speaking,
advancing, changing status, or scrolling. On cancellation, pause and reset the
shared audio element, detach/neutralize its completion callback, call
`speechSynthesis.cancel()`, and invalidate the generation. Translation
requests are keyed by surah and edition; abort an obsolete request when the
surah or selected edition changes or the Reader unmounts, and ignore any late
result whose key no longer matches. Auto must await the selected translation
request before speaking and must not advance after cancellation.

Select a browser voice only when its BCP-47 language tag has the requested
primary language (`th`, `en`, or `id`), case-insensitively; locale variants
such as `en-US` are acceptable. If `getVoices()` is initially empty, wait for
`voiceschanged` for up to three seconds, then report that no matching voice is
available. Do not select an unrelated default voice.

If translation data is missing, its request fails, audio fails, or speech
synthesis/voice support is unavailable, stop Auto and surface a clear status
near the playback controls. Do not advance to the next ayah after a failed
sequence. Cancel pending speech on stop, mode changes, manual navigation, and
Reader unmount so stale utterance callbacks cannot move the current ayah.

## Accessibility and responsive behavior

Keep controls keyboard-operable with visible focus. Expose selected mode and
language through labeled native controls, and announce playback progress,
errors, and completion in a live status region. Ensure the compact control row
wraps or stacks on narrow screens without obscuring ayah navigation.

## Boundaries

- Use the existing Quran API routes and Quran Cloud editions; do not add a
  second provider, synthetic content, or generated translation audio.
- Keep citations, source permissions, provider-generation behavior, and the
  landing page unchanged.
- Do not inspect or expose `.env.local`.

## Validation

- Test that only one visible recitation control remains and `Listen Audio` is
  retained.
- Test mode and language selection, correct translation loading, and
  single-ayah playback.
- Test Auto's per-ayah sequence, selected-ayah scrolling, stop at surah end,
  interruption by manual navigation or settings changes, stale-event/result
  suppression, and cleanup.
- Test missing/failed translations, audio failures, and unsupported speech
  synthesis, empty voice lists, language-voice timeouts, and non-matching
  voices; each must stop playback and expose an error.
- Run the focused web tests, full web Jest suite, and TypeScript typecheck.
- Verify desktop and mobile Reader controls in the local browser.
