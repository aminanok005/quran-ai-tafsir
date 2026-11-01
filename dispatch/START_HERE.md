# START HERE

## Before launching agents

1. Open the QURAN AI repository root.
2. Run `git status --short --branch`.
3. Confirm existing user changes are understood and preserved.
4. Read AGENT_MASTER_TASK.md.
5. Prepare separate worktrees or independent working copies.
6. Freeze shared API contracts before implementation.
7. Open three coding-agent sessions.

## Suggested worktree layout

Use the actual repository path and confirm the branch names do not already exist.

Example only:

    git worktree add ../quran-ai-claude -b agent/claude-backend main
    git worktree add ../quran-ai-kilo -b agent/kilo-frontend main
    git worktree add ../quran-ai-cline -b agent/cline-database main

Do not execute these example commands blindly.

## Dispatch

- Claude Code: dispatch/CLAUDE_TASK.md
- Kilo Code: dispatch/KILO_TASK.md
- Cline: dispatch/CLINE_TASK.md

Give each agent its own worktree and task file.

## After agents finish

Coordinator reads all reports and follows dispatch/INTEGRATION_TASK.md.

No automatic orchestration is implied by these files. They provide a consistent human-dispatched workflow.
