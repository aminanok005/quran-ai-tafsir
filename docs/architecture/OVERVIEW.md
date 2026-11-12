# Architecture Overview

- apps/web: Thai-first Quran Reader and Tafsir Chat.
- apps/admin: source registry, ingestion review and operational administration.
- services/api: public application API and external API adapters.
- services/ai-engine: RAG, agent orchestration and evidence validation.
- services/ingestion: authorized book ingestion and metadata processing.
- packages: shared TypeScript types, UI and configuration.
- database: reviewed migrations and seed data.

## Reader Expert Lanes

- Frontend/Audio: `apps/web` owns Reader state, native audio, Web Audio, IndexedDB, cancellation, and accessibility.
- Backend/Go: future optional audio streaming gateway; must implement `docs/architecture/audio-service-contract.md`.
- Systems/Rust: future optional bounded async/codec worker; must consume versioned jobs and never own Quran or Tafsir authority.
- Cross-lane compatibility uses `docs/architecture/reader-audio-contract.md` and `docs/architecture/reader-event-contract.md`.
- Frontend remains functional when optional Go/Rust services are absent or unhealthy.
- Enablement gates and benchmark requirements live in `docs/architecture/reader-expert-lanes.md` and `docs/architecture/audio-cross-lane-benchmarks.md`.

Arabic Quran text and source quotations must preserve original text.
Thai is the default interface and explanation language.
