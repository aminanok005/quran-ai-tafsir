# database/migrations

QURAN AI workspace component.

## Migration ownership and boundaries

- Cline owns `database/**` (this directory). Canonical Alembic migration files live under `services/api/migrations/` (per `pyproject.toml` `script_location = "services/api/migrations"`) and are maintained by the backend owner.
- `database/migrations/` holds reference SQL, setup guidance, and ownership documentation — not canonical Alembic revision files.
- No schema changes may be applied to production. Run migrations only against disposable development data with explicit authorization.

## Existing canonical migration

`services/api/migrations/versions/0001_initial_setup.py` already:
- Enables the `pgvector` extension
- Creates the `vector(1536)` column and HNSW index on `tafsir_passages`
- Establishes the base schema for scholars, tafsir_books, source_permissions, and tafsir_passages

## Development-only source permissions

The `source_permissions` table tracks source rights and verification state:
- `permission_status`: `pending`, `approved`, `rejected`, `suspended`, `development_only`
- `verification_status`: `unverified`, `verified`
- Default for development ingestion: `development_only` / `unverified`, `production_eligible = false`
- Ingestion writes are hard-coded to development-only status; this path cannot promote sources to production.

## Safe migration workflow

1. Never run `alembic upgrade head` against production.
2. Use a disposable development database for validation.
3. Verify schema state and all 6,236 Quran ayahs after seeding.
4. Review `EXECUTE_NOW.sh` before execution (needs review per PHASE_CHECKLIST.md).

## Related references

- `PHASE_CHECKLIST.md` — Phase 2 database/source gates and ordered next steps
- `services/ingestion/README.md` — Development Tafsir parsing and ingestion guards
- `services/ingestion/policy.py` — Pure source-rights policy (no network or database access)
- `.agent-work/CLINE_REPORT.md` — Cline ownership and blocker record

## Validation

- `cd services/ingestion && python3 -m unittest -v` — ingestion policy and parser tests (30 tests passing)
- `python3 -m py_compile services/ingestion/*.py` — syntax check for ingestion modules
- PostgreSQL migration and seeding validation requires explicit authorization and a disposable database
