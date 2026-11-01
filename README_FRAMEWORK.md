# QURAN AI — Multi-Agent Coding Framework v1.0

Thai-first Quran Reader and Tafsir AI platform.

## Agent topology

| Role | Tool | Ownership |
|---|---|---|
| Coordinator | Human / Orchestrator | Contracts, integration, QA |
| Backend | Claude Code | services/api/, services/ai-engine/ |
| Frontend | Kilo Code | apps/web/ |
| Data | Cline | database/, services/ingestion/ |

## Operating model

1. Inspect the repository before changing anything.
2. Read AGENT_MASTER_TASK.md.
3. Use separate Git worktrees for parallel agents.
4. Do not allow agents to edit the same files.
5. Freeze shared contracts before implementation.
6. Each agent reports files, tests, risks and blockers.
7. Coordinator reviews and integrates the work.
8. Run all quality gates before declaring MVP ready.

## Important

The framework does not automatically launch or control other coding agents.
Open each tool in its assigned worktree and provide its dispatch task.

## Language

- Product interface and AI explanations: Thai-first.
- Quran Arabic: preserve original Arabic and RTL layout.
- English: secondary language.
- Source titles and quotations: preserve original language.

## Non-negotiable Quran integrity

- Never fabricate Quran text, translations, hadith, tafsir quotations or citations.
- Never invent volume, page, edition, URL or source identifiers.
- Distinguish verified source material from AI-generated synthesis.
- If source evidence is unavailable, disclose the limitation and abstain.
- Agent profiles are research personas, not the actual scholars.

## Start

Read dispatch/START_HERE.md, then AGENT_MASTER_TASK.md.
