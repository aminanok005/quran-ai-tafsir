# Skill: Git Safety

Default is READ-ONLY / PLAN ONLY.

Inspect status, branch, remotes, log, staged diff, unstaged diff and untracked files.

Before commit:
- Inspect all files and complete diffs.
- Detect secrets and unrelated changes.
- Propose a Conventional Commit message.
- Wait for explicit approval.

Before push:
- Verify upstream and divergence.
- Inspect outgoing commits.
- Never force push without explicit approval.

Never run destructive recovery commands without explicit approval.
Never use `git add .` blindly.
Preserve all pre-existing user changes.
