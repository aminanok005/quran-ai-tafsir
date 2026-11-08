# QURAN AI — Claude Code Project Rules

Read AGENT_MASTER_TASK.md and relevant .agents/skills before implementation.

## Superpowers Skills (installed at ~/.superpowers/)

Available skill commands:
- `superpowers:subagent-driven-development` — Execute plan with fresh implementer subagent per task + review after each
- `superpowers:executing-plans` — Execute plan inline in current session (no per-task subagents)
- `superpowers:writing-plans` — Create detailed implementation plans
- `superpowers:brainstorming` — Drawing out intent before building
- `superpowers:diagnosing-superpowers` — Work out what went wrong in a session
- `superpowers:dispatching-parallel-agents` — Concurrent subagent workflows
- `superpowers:requesting-code-review` — Pre-review checklist
- `superpowers:receiving-code-review` — Responding to feedback
- `superpowers:using-git-worktrees` — Parallel development branches
- `superpowers:finishing-a-development-branch` — Merge/PR decision workflow
- `superpowers:systematic-debugging` — Root cause tracing, defense-in-depth
- `superpowers:test-driven-development` — Write tests first, always
- `superpowers:verification-before-completion` — Ensure it's actually fixed
- `superpowers:using-superpowers` — Introduction to the skills system
- `superpowers:writing-skills` — Create new skills following best practices

You own only:
- services/api/**
- services/ai-engine/**
- .agent-work/CLAUDE_REPORT.md

Follow backend-development, quran-source-validation, citation-audit,
api-contract-audit, test-and-build, security-audit and git-safety.

Do not modify shared contracts, frontend or database-owned files without approval.
Do not fabricate Quran or tafsir evidence.
No installs, commits, pushes or destructive Git operations without approval.
