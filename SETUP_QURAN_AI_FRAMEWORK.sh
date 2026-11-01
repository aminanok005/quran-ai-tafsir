#!/usr/bin/env bash
set -Eeuo pipefail

# QURAN AI MULTI-AGENT CODING FRAMEWORK v1.0
# Creates framework files only. Does not modify application code or Git state.

ROOT="$(pwd)"

if [[ ! -d "$ROOT/.git" ]]; then
  echo "ERROR: Run this script from the root of the QURAN AI Git repository."
  exit 1
fi

echo "Installing QURAN AI Multi-Agent Coding Framework..."
echo "Repository: $ROOT"

FILES=(
  "README_FRAMEWORK.md"
  "AGENT_MASTER_TASK.md"
  "GIT_WORKFLOW.md"
  "dispatch/CLAUDE_TASK.md"
  "dispatch/KILO_TASK.md"
  "dispatch/CLINE_TASK.md"
  "dispatch/INTEGRATION_TASK.md"
  "dispatch/START_HERE.md"
  ".agent-work/TASK_BOARD.md"
  ".agent-work/REPORT_TEMPLATE.md"
  ".agent-work/CLAUDE_REPORT.md"
  ".agent-work/KILO_REPORT.md"
  ".agent-work/CLINE_REPORT.md"
  ".agent-work/INTEGRATION_REPORT.md"
  ".agent-work/FINAL_QA_REPORT.md"
  ".agents/skills/quran-ai-architecture/SKILL.md"
  ".agents/skills/parallel-task-manager/SKILL.md"
  ".agents/skills/backend-development/SKILL.md"
  ".agents/skills/frontend-development/SKILL.md"
  ".agents/skills/database-management/SKILL.md"
  ".agents/skills/quran-source-validation/SKILL.md"
  ".agents/skills/citation-audit/SKILL.md"
  ".agents/skills/api-contract-audit/SKILL.md"
  ".agents/skills/code-review/SKILL.md"
  ".agents/skills/test-and-build/SKILL.md"
  ".agents/skills/security-audit/SKILL.md"
  ".agents/skills/git-safety/SKILL.md"
  ".claude/CLAUDE.md"
  ".kilocode/rules/00-quran-ai.md"
  ".clinerules/00-quran-ai.md"
)

for file in "${FILES[@]}"; do
  if [[ -e "$ROOT/$file" ]]; then
    echo "ERROR: Target already exists: $file"
    echo "No files have been overwritten. Resolve existing files, then rerun."
    exit 1
  fi
done

mkdir -p \
  dispatch \
  .agent-work \
  .agents/skills/quran-ai-architecture \
  .agents/skills/parallel-task-manager \
  .agents/skills/backend-development \
  .agents/skills/frontend-development \
  .agents/skills/database-management \
  .agents/skills/quran-source-validation \
  .agents/skills/citation-audit \
  .agents/skills/api-contract-audit \
  .agents/skills/code-review \
  .agents/skills/test-and-build \
  .agents/skills/security-audit \
  .agents/skills/git-safety \
  .claude \
  .kilocode/rules \
  .clinerules

write_file() {
  local file="$1"
  shift
  cat > "$ROOT/$file" <<'QURAN_AI_FILE_EOF'
$CONTENT_PLACEHOLDER
QURAN_AI_FILE_EOF
}

cat > README_FRAMEWORK.md <<'EOF'
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
EOF

cat > AGENT_MASTER_TASK.md <<'EOF'
# QURAN AI — MASTER ORCHESTRATOR TASK v1.0

## 1. Mission

Build a working QURAN AI MVP, not merely a scaffold.

The MVP must provide:
- Quran Reader with Surah/Ayah navigation.
- Arabic Quran text with correct RTL rendering.
- Thai-first interface.
- Thai translation only when an actual supported translation source is verified.
- Ayah selection.
- Tafsir chat for a selected Ayah.
- At least one functioning agent profile.
- Verifiable citations when licensed and indexed source material exists.
- Honest unavailable/insufficient-evidence behavior.

## 2. First action: repository discovery

Before editing, every agent MUST inspect:

- pwd
- git status --short --branch
- git branch --show-current
- git log -5 --oneline
- git remote -v
- top-level files and directories
- existing README, PRD, package manifests, API definitions and database configuration

Do not assume the repository is empty or that the proposed architecture already exists.

Record existing architecture and blockers in the agent report.

Do not overwrite existing implementation merely to match this framework.

## 3. Architecture discovery and decision

Inspect the actual repository and identify:
- Existing frontend framework and scripts.
- Existing backend framework and routes.
- Existing database and migration system.
- Existing Quran Foundation integration.
- Existing AI/LLM provider integration.
- Existing tests and CI.

Use existing working technology where practical.
Do not introduce duplicate applications, routers, models or configuration systems.

If an architectural change is required, document the reason and request Coordinator approval.

## 4. File ownership

### Claude Code — Backend
Allowed:
- services/api/**
- services/ai-engine/**
- .agent-work/CLAUDE_REPORT.md

Responsible for:
- FastAPI application and routes, if FastAPI is consistent with repository architecture.
- Quran Foundation API adapter.
- Surah and Ayah endpoints.
- Agent listing and Tafsir request/response.
- Input validation and error handling.
- Backend tests.

### Kilo Code — Frontend
Allowed:
- apps/web/**
- .agent-work/KILO_REPORT.md

Responsible for:
- Quran Reader.
- Thai-first UI.
- Arabic RTL rendering.
- Surah navigation and Ayah selection.
- Tafsir chat.
- Agent selection.
- Citation and evidence-status presentation.
- Loading, empty, error and unavailable states.
- Frontend tests/build.

### Cline — Data and ingestion
Allowed:
- database/**
- services/ingestion/**
- .agent-work/CLINE_REPORT.md

Responsible for:
- Database schema and models.
- Migration files.
- Source registry and provenance.
- Tafsir work metadata.
- Citation structures.
- Ingestion interfaces and tests.

Do not download or ingest copyrighted books without documented permission.

### Coordinator
Responsible for:
- Shared contracts.
- Integration planning.
- Cross-agent review.
- Conflict resolution.
- End-to-end tests.
- Integration and final QA reports.

No agent may edit another agent's owned files without explicit coordination.

## 5. Shared API contract proposal

Treat these endpoints as a proposed baseline, not permission to break existing APIs.

GET /health
GET /api/v1/surahs
GET /api/v1/surahs/{surah_id}/ayahs
GET /api/v1/ayahs/{surah_id}/{ayah_number}
GET /api/v1/agents
POST /api/v1/tafsir/explain

Before implementation, compare with existing routes and publish the agreed contract.

### Tafsir request proposal

{
  "surah_id": 1,
  "ayah_number": 1,
  "agent_id": "saadi",
  "question": "ช่วยอธิบายอายะฮ์นี้"
}

### Tafsir response proposal

{
  "answer": "...",
  "language": "th",
  "agent_id": "saadi",
  "evidence_status": "AI-SYNTHESIS",
  "citations": [],
  "limitations": []
}

Do not return invented citations to make the response appear complete.

## 6. Agent profiles

Proposed research profiles:
- Ibn Kathir
- Al-Tabari
- Al-Qurtubi
- Ibn Ashur
- Al-Sa'di
- Wahbah Al-Zuhayli

These are AI research profiles inspired by the methodologies and works of the named scholars. They are not the scholars themselves and must never be presented as direct quotations or personal opinions of those scholars.

For MVP, implement only profiles supported by available verified source material.

## 7. Evidence status

Use these statuses consistently:

- VERIFIED: Exact source passage checked against an identifiable source.
- SOURCE-ATTRIBUTED: Source attribution exists but exact passage has not been independently verified.
- SCHOLARLY-DIFFERENCE: Recognized disagreement between scholarly interpretations.
- UNVERIFIED: Evidence is insufficient or not checked.
- AI-SYNTHESIS: AI-generated explanation, not a direct source quotation.

Never label AI-SYNTHESIS as VERIFIED.

## 8. Parallel execution rules

- Use separate Git worktrees or independent working copies.
- Do not let two agents edit the same file.
- Do not modify shared API contracts without Coordinator approval.
- Do not change root dependency manifests unless assigned and approved.
- Report blockers immediately.
- Do not merge or cherry-pick another agent's work without Coordinator approval.

## 9. Safety and change control

Unless explicitly approved:
- No dependency installation or upgrade.
- No system configuration changes.
- No secret or credential changes.
- No database migration execution against real data.
- No downloading or ingesting source books.
- No destructive Git commands.
- No commit, push, deployment or force push.
- No schema/API breaking changes.

Do not discard, reset, stash or overwrite pre-existing user changes.

## 10. Testing requirements

Each agent must:
- Identify existing test commands before running them.
- Run focused tests for changed components.
- Report exact commands and results.
- Report tests not run and why.
- Avoid claiming success without execution evidence.

Coordinator must plan:
- Backend tests.
- Frontend build and tests.
- Database/migration validation.
- API contract compatibility.
- End-to-end Reader-to-Tafsir flow.
- Security and citation audits.

## 11. Definition of Done

MVP is complete only when:
1. Reader loads real Quran data from a verified source.
2. Arabic text is rendered correctly.
3. Thai UI works.
4. Ayah selection works.
5. Tafsir chat receives a selected Ayah.
6. Backend request/response works.
7. At least one agent profile works.
8. Citations are genuine and traceable when evidence exists.
9. No-source behavior is honest and safe.
10. Relevant tests and builds pass.
11. Final QA report documents remaining limitations.

A scaffold, mock response or placeholder is not a completed feature.

## 12. Required agent reports

Each agent updates its report with:
- Initial repository findings.
- Assigned scope.
- Files created/modified.
- Implementation summary.
- Tests and exact results.
- Contract assumptions.
- Risks and blockers.
- Remaining work.
- Explicit statement whether any unapproved action occurred.

## 13. Execution order

Phase A — Discovery and contract agreement.
Phase B — Parallel implementation in owned directories.
Phase C — Individual tests and reports.
Phase D — Coordinator integration.
Phase E — Cross-system QA and security/citation audits.
Phase F — Final report and approval request for Git operations.

Start with discovery. Do not silently skip blocked tasks.
EOF

cat > dispatch/CLAUDE_TASK.md <<'EOF'
# CLAUDE CODE — TASK A: BACKEND ENGINEER

Read AGENT_MASTER_TASK.md and the relevant Skills before starting.

OWNERSHIP:
- services/api/**
- services/ai-engine/**
- .agent-work/CLAUDE_REPORT.md

MISSION:
Implement the backend portion of the QURAN AI MVP using the existing repository architecture.

TASKS:
1. Inspect repository and existing backend before editing.
2. Implement or extend health endpoint.
3. Implement Quran Foundation adapter if compatible with existing design.
4. Implement Surah and Ayah endpoints.
5. Implement agent registry endpoint.
6. Implement Tafsir explain endpoint and validated request/response.
7. Add honest unavailable-source and insufficient-evidence handling.
8. Add focused backend tests.

CONSTRAINTS:
- Never expose OAuth client secrets to frontend.
- Never invent translation IDs or API credentials.
- Never fabricate tafsir citations.
- Never duplicate existing routes or application instances.
- Do not edit frontend, database or shared contracts.
- No installs, commits, pushes or migrations without approval.

REPORT:
Update .agent-work/CLAUDE_REPORT.md.

STOP if API access, credentials, architecture or contract changes require approval.
EOF

cat > dispatch/KILO_TASK.md <<'EOF'
# KILO CODE — TASK B: FRONTEND ENGINEER

Read AGENT_MASTER_TASK.md and relevant Skills first.

OWNERSHIP:
- apps/web/**
- .agent-work/KILO_REPORT.md

MISSION:
Build a usable Thai-first Quran Reader and Tafsir Chat MVP.

TASKS:
1. Inspect existing frontend and preserve its architecture.
2. Build or extend Surah navigation.
3. Display Arabic Quran text with RTL support.
4. Show Thai translation only when a verified translation is available.
5. Support Ayah selection.
6. Open Tafsir Chat with selected Surah/Ayah context.
7. Add agent selection.
8. Display citations and evidence status transparently.
9. Implement loading, empty, error and unavailable states.
10. Run existing frontend tests and build.

CONSTRAINTS:
- Do not fabricate Quran text or translations.
- Do not invent citation details.
- Do not edit backend, database or shared API contract files.
- Do not modify root dependency manifests without approval.
- No installs, commits or pushes without approval.

Use the agreed API contract. If it is not available, document the dependency and use a clearly marked temporary interface only if necessary.

REPORT:
Update .agent-work/KILO_REPORT.md.
EOF

cat > dispatch/CLINE_TASK.md <<'EOF'
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
EOF

cat > dispatch/INTEGRATION_TASK.md <<'EOF'
# COORDINATOR — INTEGRATION TASK

Do not start by editing agent-owned files.

1. Read all three agent reports.
2. Inspect each worktree and Git diff.
3. Verify file ownership and identify overlaps.
4. Compare backend routes with frontend API usage.
5. Compare database models with backend expectations.
6. Check error schemas, field names and evidence statuses.
7. Plan integration order.
8. Request approval before resolving ownership conflicts.
9. Run focused tests, then end-to-end tests.
10. Run security and citation audits.
11. Record actual results in INTEGRATION_REPORT.md and FINAL_QA_REPORT.md.

Do not merge, cherry-pick, commit, push or deploy without explicit approval.
EOF

cat > dispatch/START_HERE.md <<'EOF'
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
EOF

cat > .agent-work/TASK_BOARD.md <<'EOF'
# QURAN AI — TASK BOARD

Status values: NOT_STARTED | IN_PROGRESS | BLOCKED | REVIEW | DONE

| Task | Owner | Scope | Status | Blocker |
|---|---|---|---|---|
| Repository discovery | All | Existing repository | NOT_STARTED | |
| Shared API contract | Coordinator | Shared | NOT_STARTED | |
| Backend API | Claude | services/api | NOT_STARTED | |
| AI engine | Claude | services/ai-engine | NOT_STARTED | |
| Quran Reader | Kilo | apps/web | NOT_STARTED | |
| Tafsir Chat UI | Kilo | apps/web | NOT_STARTED | |
| Database models | Cline | database | NOT_STARTED | |
| Source registry | Cline | database | NOT_STARTED | |
| Ingestion interface | Cline | services/ingestion | NOT_STARTED | |
| Integration | Coordinator | Cross-system | NOT_STARTED | |
| Final QA | Coordinator | Cross-system | NOT_STARTED | |

Update only your assigned rows. Do not mark DONE without evidence.
EOF

cat > .agent-work/REPORT_TEMPLATE.md <<'EOF'
# Agent Execution Report

## 1. Agent and task
- Agent:
- Task ID:
- Worktree:
- Branch:

## 2. Initial repository findings
- Existing architecture:
- Existing user changes:
- Relevant existing components:

## 3. Implementation
- Summary:
- Files created:
- Files modified:
- Files deliberately not changed:

## 4. Contract compatibility
- API assumptions:
- Schema assumptions:
- Dependencies:

## 5. Tests
| Command | Result | Notes |
|---|---|---|
| | | |

## 6. Risks and blockers
-

## 7. Remaining work
-

## 8. Change-control confirmation
- Any dependency installation?:
- Any migration execution?:
- Any secrets/configuration changes?:
- Any commit/push?:
- Any files outside ownership modified?:

## 9. Final status
NOT_STARTED | IN_PROGRESS | BLOCKED | REVIEW | DONE
Evidence supporting status:
EOF

for agent in CLAUDE KILO CLINE INTEGRATION FINAL_QA; do
  cp .agent-work/REPORT_TEMPLATE.md ".agent-work/${agent}_REPORT.md"
done

cat > GIT_WORKFLOW.md <<'EOF'
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
EOF

cat > .agents/skills/quran-ai-architecture/SKILL.md <<'EOF'
# Skill: QURAN AI Architecture

## Purpose
Keep the product architecture coherent and protect the MVP scope.

## Procedure
1. Inspect existing implementation before proposing architecture.
2. Reuse working frameworks, conventions and services.
3. Identify ownership boundaries.
4. Document API and database dependencies.
5. Separate MVP requirements from later roadmap items.
6. Request approval for breaking changes.

## Product principles
- Thai-first experience.
- Arabic Quran text remains unchanged and RTL.
- Clear separation of Quran text, translation, tafsir and AI synthesis.
- Source provenance is first-class data.
- Agents are research personas, not the actual scholars.

## Output
Architecture findings, decisions, dependencies, risks and unresolved questions.
EOF

cat > .agents/skills/parallel-task-manager/SKILL.md <<'EOF'
# Skill: Parallel Task Manager

## Purpose
Coordinate multiple coding agents without overlapping edits.

## Procedure
1. Discover repository state.
2. Break work into independently testable tasks.
3. Assign exactly one owner to each file path.
4. Identify shared contracts and freeze them.
5. Give each agent a separate worktree.
6. Record dependencies and acceptance criteria.
7. Require reports before integration.
8. Detect overlapping file changes.
9. Escalate conflicts to Coordinator.

## Required task contract
TASK ID, AGENT, OBJECTIVE, ALLOWED FILES, FORBIDDEN FILES,
DEPENDENCIES, INPUT CONTRACT, OUTPUT CONTRACT, TESTS,
ACCEPTANCE CRITERIA, REPORT LOCATION.

Never assume agents can automatically communicate or launch one another.
EOF

cat > .agents/skills/backend-development/SKILL.md <<'EOF'
# Skill: Backend Development

## Procedure
1. Inspect existing backend structure and conventions.
2. Reuse existing application and router setup.
3. Validate all incoming data.
4. Keep secrets server-side.
5. Use explicit response schemas and consistent errors.
6. Add timeouts and safe handling for external API failures.
7. Add focused tests.
8. Document configuration requirements.

Do not invent Quran data, translation IDs, citations or source metadata.
Do not break existing endpoints without approval.
EOF

cat > .agents/skills/frontend-development/SKILL.md <<'EOF'
# Skill: Frontend Development

## Procedure
1. Inspect existing framework, routes and design system.
2. Preserve existing conventions.
3. Implement Thai-first interface.
4. Render Arabic with RTL and appropriate text direction.
5. Separate Arabic, translation, tafsir quotation and AI explanation.
6. Provide loading, empty, error and unavailable states.
7. Display evidence status and citations clearly.
8. Test responsive layout and core interactions.

Do not hardcode invented Quran passages or translations.
Do not silently replace API behavior with mock data.
EOF

cat > .agents/skills/database-management/SKILL.md <<'EOF'
# Skill: Database Management

## Procedure
1. Inspect current database engine, ORM and migration framework.
2. Reuse established conventions.
3. Model source, work, author, edition, passage and citation provenance.
4. Track rights status and ingestion permission.
5. Use stable identifiers and appropriate constraints.
6. Make migrations reversible where practical.
7. Validate migrations in an isolated test environment.
8. Never apply migrations to production or user data without approval.

Unknown rights status must block ingestion.
Do not create duplicate models or competing migration systems.
EOF

cat > .agents/skills/quran-source-validation/SKILL.md <<'EOF'
# Skill: Quran Source Validation

## Purpose
Protect the integrity of Quran text, translations and tafsir evidence.

## Validation
- Identify the exact source and edition.
- Preserve Arabic text exactly.
- Record translation author and source where available.
- Distinguish Quran text from translation and commentary.
- Track retrieval origin and verification status.
- Check passage boundaries and Surah/Ayah identifiers.
- Record uncertainty instead of silently correcting source data.

Never fabricate or paraphrase Quran text as though it were the original.
Never infer a missing translation or verse identifier.
If uncertain, mark UNVERIFIED and abstain from presenting it as fact.
EOF

cat > .agents/skills/citation-audit/SKILL.md <<'EOF'
# Skill: Citation Audit

## Required citation metadata
- source_id
- work_title
- author
- edition
- volume (nullable)
- page (nullable)
- passage or original quotation
- URL (nullable)
- verification_status

## Audit
1. Verify the work exists.
2. Verify author and edition.
3. Verify the quoted passage against available source evidence.
4. Verify volume/page only when directly supported.
5. Verify URL points to the actual source.
6. Distinguish direct quotation from paraphrase.
7. Flag missing or contradictory metadata.

Never invent page numbers, volume numbers, URLs or quotations.
No supporting passage means no fabricated citation.
EOF

cat > .agents/skills/api-contract-audit/SKILL.md <<'EOF'
# Skill: API Contract Audit

## Audit procedure
1. Inspect backend route definitions.
2. Inspect request and response schemas.
3. Inspect frontend API calls and types.
4. Compare path, method, fields, types and nullability.
5. Check error response behavior.
6. Check pagination and loading semantics.
7. Check evidence-status and citation structures.
8. Report mismatches with file and line references.

Do not change a shared contract unilaterally.
Propose a backward-compatible fix and obtain Coordinator approval.
EOF

cat > .agents/skills/code-review/SKILL.md <<'EOF'
# Skill: Code Review

Review in this order:
1. Correctness and runtime failures.
2. Security and privacy.
3. Data integrity and Quran/source correctness.
4. API and schema compatibility.
5. Error handling and edge cases.
6. Performance and maintainability.
7. Test coverage.

Report findings by severity:
CRITICAL, HIGH, MEDIUM, LOW.

Every finding must include location, impact and a suggested remediation.
Do not silently modify another agent's files.
EOF

cat > .agents/skills/test-and-build/SKILL.md <<'EOF'
# Skill: Test and Build

## Procedure
1. Discover existing test/build commands.
2. Read relevant project instructions.
3. Run focused tests first.
4. Run type checks and lint where configured.
5. Run full tests and production build when feasible.
6. Capture exact command, exit code and result.
7. Separate failures introduced by changes from pre-existing failures.
8. Report tests not run.

Never claim a test passed unless it was actually executed.
Do not install or upgrade dependencies without approval.
EOF

cat > .agents/skills/security-audit/SKILL.md <<'EOF'
# Skill: Security Audit

Check:
- Secrets and credentials in source, logs and frontend bundles.
- Authentication and authorization boundaries.
- Input validation and injection risks.
- CORS and exposed debug endpoints.
- Unsafe file uploads and path handling.
- SQL/query safety.
- Rate limiting and abuse controls.
- Dependency and configuration risks.
- Sensitive data in logs and error responses.

Do not print secret values in reports.
Do not change production configuration or rotate credentials without approval.
Report severity, evidence and remediation.
EOF

cat > .agents/skills/git-safety/SKILL.md <<'EOF'
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
EOF

cat > .claude/CLAUDE.md <<'EOF'
# QURAN AI — Claude Code Project Rules

Read AGENT_MASTER_TASK.md and relevant .agents/skills before implementation.

You own only:
- services/api/**
- services/ai-engine/**
- .agent-work/CLAUDE_REPORT.md

Follow backend-development, quran-source-validation, citation-audit,
api-contract-audit, test-and-build, security-audit and git-safety.

Do not modify shared contracts, frontend or database-owned files without approval.
Do not fabricate Quran or tafsir evidence.
No installs, commits, pushes or destructive Git operations without approval.
EOF

cat > .kilocode/rules/00-quran-ai.md <<'EOF'
# QURAN AI — Kilo Code Rules

Read AGENT_MASTER_TASK.md and relevant .agents/skills before implementation.

You own only:
- apps/web/**
- .agent-work/KILO_REPORT.md

Follow frontend-development, quran-source-validation, citation-audit,
api-contract-audit, code-review and test-and-build.

Thai-first UI. Preserve Arabic text and RTL.
Never fabricate Quran text, translations or citations.
Do not edit backend, database or shared contracts without approval.
No dependency installation, commit or push without approval.
EOF

cat > .clinerules/00-quran-ai.md <<'EOF'
# QURAN AI — Cline Rules

Read AGENT_MASTER_TASK.md and relevant .agents/skills before implementation.

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
EOF

echo
echo "Framework files created successfully."
echo "No application code, dependencies or Git state were intentionally changed."
echo
echo "Next:"
echo "1. Review README_FRAMEWORK.md"
echo "2. Read AGENT_MASTER_TASK.md"
echo "3. Read dispatch/START_HERE.md"
echo "4. Inspect git status --short"

echo "Framework setup script generated."