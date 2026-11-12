# Reader Expert Lanes

## Current path

Next.js owns Reader state, native cross-origin audio, same-origin Web Audio, IndexedDB, cancellation, and accessibility. FastAPI remains control plane for Tafsir and source permissions.

## Optional lanes

- Go gateway: structured audio requests, allowlisted upstreams, streaming, Range, timeout, and bounded concurrency.
- Rust worker: bounded async jobs and codec experiments only; no Quran/Tafsir text, citations, or source authority.

Go and Rust stay disabled until contract tests, security review, license review, benchmark evidence, and deployment ownership are recorded. Native CDN playback remains default for cross-origin sources without CORS.

## Evidence and fallback

Tafsir failures remain explicit and fail closed. No provider substitution or fabricated text. Audio preload is current item plus one next item; stale work is cancelled on navigation, stop, settings changes, and unmount.
