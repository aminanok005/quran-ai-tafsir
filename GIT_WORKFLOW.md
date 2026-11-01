# QURAN AI — GIT SAFETY WORKFLOW

## Default mode
PLAN ONLY. Inspection is allowed; mutations require explicit approval.

## Pre-check
Inspect:
- git status --short --branch
- git branch --show-current
- git log -5 --oneline
- git remote -v
- git diff
- git diff --cached
- untracked files

## Smart commit
Before proposing a commit:
1. Inspect every changed file.
2. Classify source, config, schema, docs, tests, generated files and unknown files.
3. Inspect full staged and unstaged diffs.
4. Check for secrets, credentials, private keys and local data.
5. Check for unrelated changes.
6. Propose Conventional Commit message.
7. Wait for approval before staging or committing.

Never use `git add .` blindly.

## Smart push
Before proposing a push:
1. Inspect branch and upstream.
2. Fetch only with approval if required by the user's policy.
3. Check ahead/behind and divergence.
4. Check commits and secrets.
5. Never force push unless explicitly approved.

## Recovery
Read-only diagnosis first:
- git status
- git reflog
- git log --all --graph --oneline
- git diff

Do not reset, clean, checkout over changes, rebase, amend or force-push without explicit approval.

## Multi-agent
- One worktree per agent.
- Do not share a working directory between coding agents.
- Do not merge another agent's branch without Coordinator review.
- Preserve all uncommitted work.
