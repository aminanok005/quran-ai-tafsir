---
name: github-rulesets
description: Inspect, plan, and validate GitHub repository rulesets, branch protection, pull request requirements, CI checks, and Git safety for the QURAN AI repository. Use before committing a baseline, integrating code, merging changes, or changing repository protection settings.
---

# QURAN AI — GitHub Rulesets Security Skill

## 1. Purpose

Safely inspect and manage GitHub repository rulesets for:

- Repository: `aminanok005/quran-ai-tafsir`
- Primary branch: `main`
- Local repository: `/home/nisreen/Videos/yt-project/quran-intelligent-tafsir`

The objective is to protect important Git history, prevent accidental deletion or force-pushes, and establish appropriate review requirements without disrupting the existing development workflow.

Creating or using this Skill does not automatically configure GitHub rulesets.

## 2. Mandatory Safety Rules

1. Default to read-only inspection.
2. Never stage, commit, push, merge, rebase, reset, or clean files unless explicitly authorized for that specific operation.
3. Never delete files, branches, worktrees, or backups without explicit approval.
4. Never modify GitHub rulesets, branch protection settings, repository permissions, or bypass permissions without explicit approval.
5. Never disable security protections merely to make a workflow pass.
6. Never expose access tokens, credentials, private keys, `.env` values, or other secrets in reports.
7. Never overwrite or discard existing user changes.
8. Do not assume the working tree is safe merely because tracked files are clean; inspect untracked files separately.
9. Do not assume CI checks exist or are passing. Verify their actual configuration and status.
10. If an operation is ambiguous, destructive, blocked, or outside the approved scope, stop and report the issue.

## 3. Read-Only Repository Inspection

Run the following commands from the repository root:

```bash
pwd
git rev-parse --show-toplevel
git branch --show-current
git status --short --branch
git log -5 --oneline --decorate
git remote -v
git diff --stat
git diff --cached --stat
git ls-files --others --exclude-standard
```

Check the current branch and remote tracking status:

```bash
git status -sb
git branch -vv
git rev-parse --verify HEAD
```

### Inspection requirements

- Confirm that the repository path is correct.
- Identify the current branch and commit.
- Report tracked modifications, staged changes, and untracked files separately.
- Do not treat untracked files as committed or backed up.
- Do not assume that the local branch and GitHub branch are synchronized.
- Redact credentials if remote output contains embedded secrets.

Do not proceed with a commit or integration operation until the user has reviewed the findings and authorized the next step.

## 4. GitHub Ruleset Inspection

Inspect the repository's current rulesets using the GitHub UI or an authorized GitHub API integration.

For each ruleset, report:

| Field | What to verify |
|---|---|
| Name | Ruleset name |
| Enforcement | Active, Evaluate, or Disabled, as supported |
| Target | Which branches or tags are covered |
| Restrictions | Which operations are restricted |
| Pull requests | Whether PRs are required |
| Approvals | Required review approvals |
| Status checks | Required checks and whether they actually exist |
| Bypass | Which users, teams, or applications can bypass the rules |
| Conflicts | Whether other rulesets or branch protection rules overlap |

If access is unavailable, report `NOT VERIFIED`. Do not claim that a ruleset exists or is active without evidence.

## 5. Recommended Protection for `main`

Propose the following rules for review. Do not apply them automatically.

### Required protections

- Target the `main` branch.
- Require pull requests before merging, if compatible with the approved workflow.
- Require approval from at least one independent reviewer when review is available and appropriate.
- Dismiss stale approvals when new commits are pushed, where supported and appropriate.
- Require approval of the most recent reviewable push when supported and appropriate.
- Require conversations to be resolved before merging.
- Block force pushes.
- Restrict branch deletion.

### Optional protections

- Require linear history if the repository's merge workflow supports it.
- Require signed commits if signing is configured and the team is ready to enforce it.
- Require status checks only when the corresponding checks exist, are reliable, and have been verified.
- Restrict bypass permissions to the minimum necessary.

### Configuration safeguards

Before recommending any rule:

1. Verify the current repository configuration.
2. Identify whether the rule could block the existing workflow.
3. Identify any required CI checks that do not exist yet.
4. Explain the expected impact.
5. Request explicit approval before applying the configuration.

Never invent CI check names or assume that a proposed rule is already active.

## 6. Baseline Commit Safety Gate

Before recommending a baseline commit:

1. Inspect the current branch and commit history.
2. Review tracked changes, staged changes, and untracked files.
3. Identify generated files, caches, build artifacts, and local-only configuration.
4. Check for likely credentials or secrets without printing their values.
5. Review relevant `.gitignore` rules.
6. Verify that intended source files are present.
7. Confirm that no unrelated user changes would be included.
8. Report the proposed scope of the commit.

Do not stage or commit anything unless the user explicitly authorizes the operation.

A clean working tree alone does not prove that the repository is complete or ready for release.

## 7. Pull Request and Integration Safety Gate

Before approving or recommending a merge:

- Confirm the source and target branches.
- Review the complete change summary.
- Check for unrelated files or unexpected deletions.
- Review test results and CI status where available.
- Check whether database migrations or API changes require additional review.
- Verify that secrets and local configuration are not included.
- Identify unresolved conflicts and review comments.
- Confirm that the required GitHub protections are active.

If required checks are missing or their status cannot be verified, report `BLOCKED` or `NOT VERIFIED` as appropriate.

Do not merge or push without explicit authorization.

## 8. GitHub Configuration Procedure

When the user explicitly authorizes configuration:

1. Inspect the existing rulesets and branch protection rules.
2. Record the current configuration before making changes.
3. Present the exact proposed changes and their impact.
4. Obtain confirmation of the specific configuration to apply.
5. Apply only the approved changes through an authorized interface.
6. Re-read the configuration after the operation.
7. Verify that the intended rules are active and that unrelated settings remain unchanged.
8. Report the results and any remaining limitations.

If the required permissions or tools are unavailable, provide the steps for the user to perform manually. Do not claim success without verification.

## 9. Reporting Format

Use this report structure:

### Repository
- Path:
- Current branch:
- Current commit:
- Working tree:

### Git Safety
- Tracked changes:
- Staged changes:
- Untracked files:
- Potential secret exposure:
- Backup or recovery concerns:

### GitHub Protection
- Rulesets discovered:
- Ruleset enforcement:
- `main` protection:
- Required reviews:
- Required status checks:
- Bypass permissions:

### Findings
- PASS:
- WARNING:
- BLOCKED:
- NOT VERIFIED:

### Recommended Next Step
- Exact action:
- Expected impact:
- Approval required:

## 10. Prohibited Actions

Without explicit authorization, never:

- Stage or commit files.
- Push to GitHub.
- Merge or rebase branches.
- Run destructive Git commands.
- Delete or overwrite user files.
- Create or delete branches or worktrees.
- Modify GitHub rulesets or branch protection.
- Change repository permissions or bypass rules.
- Run database migrations.
- Print secrets or credential values.
- Claim that tests, CI checks, or GitHub protections passed without evidence.

## 11. Definition of Done

The task is complete only when:

- Repository state has been inspected.
- Existing changes and untracked files have been accounted for.
- Current GitHub protection has been verified where access permits.
- Recommendations distinguish verified facts from assumptions.
- No unapproved changes have been made.
- The final report identifies the next action and any approval required.
