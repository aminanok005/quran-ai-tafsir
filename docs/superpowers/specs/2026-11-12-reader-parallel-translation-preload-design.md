# Reader Parallel Translation Preload Design

## Intent

Reduce the pause between recitation ayahs and generated translation audio by preloading only the next ayah while current recitation plays.

## Goals

- Preload at most one next-ayah AI translation audio item per playback sequence.
- Keep current recitation uninterrupted if preload fails.
- Reuse existing generated-audio API and cache behavior; deduplicate requests.
- Abort stale work on stop, navigation, surah/language/speed/mode changes, and unmount.

## Non-goals and anti-goals

- No browser speech-synthesis preload.
- No multi-ayah queue, backend/Go/Rust changes, or new dependency.
- Never delay, replace, or silently alter Quran or translation text.
- Never let preload failure change current playback or Auto progression.

## Approaches

- Next translation only: smallest bandwidth/API cost; chosen for default implementation.
- Current plus next: faster transition in combined mode, but risks duplicate requests and extra bandwidth; deferred.
- Multiple-ayah window: smoother under slow networks but increases memory, API load, and stale-work complexity; rejected for this change.

## Design

When generated translation audio is enabled and current recitation starts, request generated audio for exactly the next ayah if combined recitation-then-translation mode, capabilities, and a next ayah are available. Reuse the existing loader/API cache. Key cached audio by surah, ayah, language, edition, and speed. Playing the target ayah consumes the preloaded result instead of issuing a duplicate request. Preload errors are swallowed as preload-only failures; normal on-demand loading remains available when the ayah becomes current.

Cancellation and generated object URL ownership follow the existing Reader playback generation/controller lifecycle. Stop, navigation, settings changes, and unmount invalidate pending preload results and release unused object URLs. No changes to external audio source, Quran content, Tafsir attribution, or API contract.

## Acceptance

Tests prove one-next-only behavior, request reuse/no duplicate, cache hit, preload failure isolation, cancellation/stale result suppression, and feature guard behavior. Existing sequential playback, cancellation, Reader text, and Tafsir behavior remain unchanged.
