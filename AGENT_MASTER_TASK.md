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
