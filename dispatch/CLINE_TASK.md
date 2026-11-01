# CLINE — TASK C: DATA ENGINEER

Read AGENT_MASTER_TASK.md and relevant Skills first.

OWNERSHIP:
- database/**
- services/ingestion/**
- .agent-work/CLINE_REPORT.md

MISSION:
Implement the data foundation for source-aware Quran and Tafsir retrieval.

TASKS:
1. Inspect current database technology and existing migrations.
2. Design or extend source registry.
3. Define Tafsir work, edition and author metadata.
4. Define passage/chunk provenance.
5. Define citation structures with nullable volume/page fields.
6. Track source rights and ingestion permission.
7. Create migrations and models consistent with the existing stack.
8. Add validation tests.
9. Build ingestion interfaces without downloading or ingesting copyrighted books.

CONSTRAINTS:
- Do not execute migrations against real databases without approval.
- Do not download books or scrape websites.
- Unknown rights status means ingestion is not approved.
- Do not edit backend/frontend/shared contracts.
- Do not invent page numbers, editions or source URLs.
- No installs, commits or pushes without approval.

REPORT:
Update .agent-work/CLINE_REPORT.md.
