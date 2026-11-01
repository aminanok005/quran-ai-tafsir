# Architecture Overview

- apps/web: Thai-first Quran Reader and Tafsir Chat.
- apps/admin: source registry, ingestion review and operational administration.
- services/api: public application API and external API adapters.
- services/ai-engine: RAG, agent orchestration and evidence validation.
- services/ingestion: authorized book ingestion and metadata processing.
- packages: shared TypeScript types, UI and configuration.
- database: reviewed migrations and seed data.

Arabic Quran text and source quotations must preserve original text.
Thai is the default interface and explanation language.
