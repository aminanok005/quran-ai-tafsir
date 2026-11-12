# Implementation Plan

## Overview

Complete the remaining gap in the Smart Translation Audio feature (docs/superpowers/plans/2026-11-08-smart-translation-audio.md) by extracting the TTS edition-mapping and AI-availability decision logic currently inline in `apps/web/app/page.tsx` into a dedicated, testable module `apps/web/src/lib/quran/reader-audio-settings.ts`, covering it with focused unit tests, and refactoring `page.tsx` to consume it. All backend (FastAPI TTS config, service, router, lifespan), frontend client, playback coordinator, controls, and tests from the plan are already implemented.

## Types

### TypeScript (new module)
- `EditionConfig` — `{ edition: string; language: ReaderAudioLanguage; label: string }`
- `EditionMap` — `Record<ReaderAudioLanguage, EditionConfig>` — fixed mapping: `th`→`th.thai`, `en`→`en.sahih`, `id`→`id.indonesian`
- `TtsAvailability` — `{ available: boolean; reason?: string }` — result of AI availability check
- `ReaderAudioSettings` (exported functions):
  - `mapLanguageToEdition(language): EditionConfig | null`
  - `mapEditionToLanguage(edition): ReaderAudioLanguage | null`
  - `isAiAvailable(enabledEditions: string[], selectedEdition: string, supportedLanguages: ReaderAudioLanguage[]): boolean`
  - `aiUnavailableReason(enabledEditions: string[], selectedEdition: string, supportedLanguages: ReaderAudioLanguage[]): string`
  - `buildTtsSettings(capabilities, selectedEdition, playbackLanguage): { edition: EditionConfig | null; aiVoiceAvailable: boolean; aiVoiceUnavailableReason: string }`

## Files

### New files
1. `apps/web/src/lib/quran/reader-audio-settings.ts` — Typed edition mapping (`th.thai`→`th`, `en.sahih`→`en`, `id.indonesian`→`id`), AI availability gating against allowlisted editions, and TTS settings assembly for Reader consumption.
2. `apps/web/src/lib/quran/reader-audio-settings.test.ts` — Unit tests: all three language mappings, allowed/disabled edition gates, unavailable capabilities, unknown edition handling, and settings assembly.

### Existing files to modify
1. `apps/web/app/page.tsx` — Remove inline `aiVoiceAvailable`/`aiVoiceUnavailableReason` computation; import and call `buildTtsSettings` from the new module. Pass results to `ReaderAudioControls` as before.
2. `implementation_plan.md` — This document (being created).

### Files to delete or move
- None.

## Functions

### New functions
1. `mapLanguageToEdition(language: ReaderAudioLanguage): EditionConfig | null` — `reader-audio-settings.ts` — Returns the fixed edition config for a language.
2. `mapEditionToLanguage(edition: string): ReaderAudioLanguage | null` — `reader-audio-settings.ts` — Reverse lookup; returns null for unknown editions.
3. `isAiAvailable(enabledEditions: string[], selectedEdition: string, supportedLanguages: ReaderAudioLanguage[]): boolean` — `reader-audio-settings.ts` — True only when TTS is enabled, the selected edition is allowlisted, and its language is supported.
4. `aiUnavailableReason(enabledEditions: string[], selectedEdition: string, supportedLanguages: ReaderAudioLanguage[]): string` — `reader-audio-settings.ts` — Human-readable reason when AI is unavailable.
5. `buildTtsSettings(capabilities: TranslationAudioCapabilities, selectedEdition: string, playbackLanguage: ReaderAudioLanguage): { edition: EditionConfig | null; aiVoiceAvailable: boolean; aiVoiceUnavailableReason: string }` — `reader-audio-settings.ts` — Composes edition config and AI availability for the Reader.

### Modified functions
1. Page-level TTS settings computation in `apps/web/app/page.tsx` — Replace inline `aiVoiceAvailable`/`aiVoiceUnavailableReason` logic (currently around line 864) with a call to `buildTtsSettings`.

### Removed functions
- None.

## Classes
- None (module is function-based).

## Dependencies
- No new dependencies. Reuses existing `TranslationAudioCapabilities` type from `apps/web/src/lib/api/client.ts` and `ReaderAudioLanguage` type from `apps/web/src/lib/quran/reader-audio-playback.ts`.

## Testing
- New test file: `apps/web/src/lib/quran/reader-audio-settings.test.ts` covering:
  - `th` maps to `th.thai`, `en` to `en.sahih`, `id` to `id.indonesian`
  - Reverse lookup for all three editions; null for unknown edition
  - `isAiAvailable` true when edition is allowlisted and language supported
  - `isAiAvailable` false when TTS disabled, edition not allowlisted, or language unsupported
  - `aiUnavailableReason` returns appropriate messages for each gate failure
  - `buildTtsSettings` assembles edition config + availability correctly
- Existing tests remain unchanged: `client.test.ts`, `reader-audio-playback.test.ts`, `ReaderAudioControls.test.tsx`, `page.test.tsx`, `test_config.py`, `test_translation_audio.py`
- Validation: `npm test -- --runInBand` from `apps/web`, `pytest -q services/api/tests/test_config.py services/api/tests/test_translation_audio.py`, `npm run typecheck`, `npm run build`

## Implementation Order
1. Create `apps/web/src/lib/quran/reader-audio-settings.ts` with edition map, availability gates, and `buildTtsSettings`.
2. Create `apps/web/src/lib/quran/reader-audio-settings.test.ts` with unit tests.
3. Refactor `apps/web/app/page.tsx` to import `buildTtsSettings` and replace inline AI-availability computation.
4. Run `npm test -- --runInBand` from `apps/web` — all web tests pass.
5. Run `npm run typecheck` and `npm run build` from `apps/web` — typecheck and production build pass.
6. Run `pytest -q services/api/tests/test_config.py services/api/tests/test_translation_audio.py` — backend TTS tests pass (confirm no regression).

---

The plan is saved at `implementation_plan.md`. The remaining work is small and contained: create the settings module, its test, and refactor `page.tsx`. Shall I proceed with implementation?