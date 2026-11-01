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
