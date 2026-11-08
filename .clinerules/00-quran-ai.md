# QURAN AI — Cline Rules

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
- database/**
- services/ingestion/**
- .agent-work/CLINE_REPORT.md

Follow database-management, quran-source-validation, citation-audit,
api-contract-audit, security-audit, test-and-build and git-safety.

Unknown source rights means ingestion is not approved.
Do not download copyrighted books or execute migrations against real data.
Do not edit frontend, backend or shared contracts without approval.
No installs, commits, pushes or destructive Git operations without approval.
