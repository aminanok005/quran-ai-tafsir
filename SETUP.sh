#!/usr/bin/env bash
set -Eeuo pipefail

# QURAN AI monorepo scaffold
# Safe to rerun: existing files are preserved unless FORCE=1 is supplied.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

FORCE="${FORCE:-0}"

# Write a file from stdin without replacing existing work by default.
write_if_missing() {
  local path="$1"
  mkdir -p "$(dirname "$path")"
  if [[ -e "$path" && "$FORCE" != "1" ]]; then
    echo "SKIP existing: $path"
    cat >/dev/null
  else
    cat > "$path"
    echo "CREATE: $path"
  fi
}

echo "==> Creating QURAN AI monorepo directories"

dirs=(
  apps/web
  apps/admin
  services/api
  services/ai-engine
  services/ingestion
  packages/shared-types
  packages/ui
  packages/config
  database/migrations
  database/seeds
  docs/architecture
  docs/product
  docs/sources
  docs/security
  infra/containers
  infra/k8s
  infra/monitoring
  scripts
  tests/integration
  tests/fixtures
)

for dir in "${dirs[@]}"; do
  mkdir -p "$dir"
  if [[ ! -e "$dir/README.md" ]]; then
    printf '# %s\n\nQURAN AI workspace component.\n' "$dir" > "$dir/README.md"
  fi
done

echo "==> Creating root package.json"
write_if_missing package.json <<'EOF'
{
  "name": "quran-ai",
  "private": true,
  "version": "0.1.0",
  "packageManager": "bun@1.2.0",
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "scripts": {
    "dev:web": "bun --cwd apps/web dev",
    "build:web": "bun --cwd apps/web run build",
    "lint": "bun --workspaces --if-present run lint",
    "typecheck": "bun --workspaces --if-present run typecheck",
    "test": "bun --workspaces --if-present run test"
  }
}
EOF

echo "==> Creating .gitignore"
write_if_missing .gitignore <<'EOF'
# JavaScript / TypeScript
node_modules/
.next/
out/
dist/
coverage/
.turbo/
*.tsbuildinfo

# Python
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.venv/
venv/

# Environment and secrets
.env
.env.*
!.env.example
!.env.*.example
*.pem
*.key
secrets/
.credentials/

# Databases, indexes and generated data
*.sqlite
*.sqlite3
*.db
data/raw/
data/processed/
data/indexes/
uploads/
storage/

# OS / editor
.DS_Store
.idea/
.vscode/*
!.vscode/extensions.json

# Build artifacts
/target/
.pybuild/
EOF

echo "==> Creating environment template (placeholders only)"
write_if_missing .env.example <<'EOF'
# QURAN AI - local development defaults; replace placeholders locally.
APP_ENV=development
APP_NAME=QURAN AI
APP_DEFAULT_LOCALE=th
APP_SUPPORTED_LOCALES=th,ar,en
APP_BASE_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000

# PostgreSQL + pgvector
DATABASE_URL=postgresql+psycopg://quran_ai:CHANGE_ME@localhost:5432/quran_ai

# Redis (optional in early development)
REDIS_URL=redis://localhost:6379/0

# Quran Foundation API - keep credentials on the server only.
QURAN_API_BASE_URL=https://apis.quran.foundation
QURAN_API_CLIENT_ID=REPLACE_WITH_APPROVED_CLIENT_ID
QURAN_API_CLIENT_SECRET=REPLACE_WITH_SECRET
QURAN_API_TOKEN_CACHE_TTL_SECONDS=3300

# AI provider adapter; do not commit real API keys.
LLM_PROVIDER=REPLACE_ME
LLM_API_BASE_URL=
LLM_API_KEY=REPLACE_ME
LLM_MODEL=REPLACE_ME

# Retrieval
EMBEDDING_PROVIDER=REPLACE_ME
EMBEDDING_MODEL=REPLACE_ME
VECTOR_DIMENSIONS=REVIEW_BEFORE_MIGRATION

# Security
SECRET_KEY=GENERATE_A_LONG_RANDOM_SECRET
CORS_ORIGINS=http://localhost:3000
EOF

echo "==> Creating TypeScript configuration"
write_if_missing tsconfig.base.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true
  }
}
EOF

echo "==> Creating Python project metadata"
write_if_missing pyproject.toml <<'EOF'
[project]
name = "quran-ai-services"
version = "0.1.0"
description = "Backend, AI orchestration and source-ingestion services for QURAN AI"
requires-python = ">=3.12"
dependencies = []

[project.optional-dependencies]
dev = [
  "pytest>=8",
  "pytest-cov>=5",
  "ruff>=0.6",
  "mypy>=1.11"
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
testpaths = ["services", "tests"]
python_files = ["test_*.py"]
EOF

echo "==> Creating API service skeleton"
write_if_missing services/api/README.md <<'EOF'
# API Service

FastAPI application entry point will live here.

Initial boundaries:
- REST API and request validation
- Quran Foundation API proxy (server-side credentials only)
- Authentication and authorization
- Chat/session endpoints
- Source and citation endpoints

Do not place LLM orchestration or book-ingestion logic in this service.
EOF

write_if_missing services/api/main.py <<'EOF'
"""QURAN AI API service bootstrap."""

from fastapi import FastAPI

app = FastAPI(
    title="QURAN AI API",
    version="0.1.0",
    description="Thai-first Quran study and evidence-based Tafsir API.",
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
EOF

echo "==> Creating AI engine and ingestion boundaries"
write_if_missing services/ai-engine/README.md <<'EOF'
# AI Engine

Owns agent orchestration, retrieval, evidence validation and response formatting.

Required safeguards:
- Retrieve source passages before generating source-attributed claims.
- Keep verbatim Arabic quotations separate from Thai explanations.
- Never fabricate author, title, volume, page or hadith grading.
- Label AI synthesis and scholarly disagreement explicitly.
- Abstain when reliable evidence is unavailable.
EOF

write_if_missing services/ingestion/README.md <<'EOF'
# Source Ingestion

Owns authorized acquisition, extraction, normalization, segmentation,
metadata enrichment, Ayah mapping and source-quality validation.

Do not ingest or redistribute a book until its license and permitted uses
(including indexing and AI processing) have been reviewed and recorded.
EOF

echo "==> Creating database governance notes"
write_if_missing database/README.md <<'EOF'
# Database

PostgreSQL is the system of record. pgvector is an optional retrieval extension.

Important: do not create production migrations from placeholder assumptions.
Confirm the embedding model and vector dimensions, source licensing metadata,
Arabic text normalization strategy and citation model before the first schema
migration.
EOF

write_if_missing database/migrations/README.md <<'EOF'
# Migrations

Add reviewed, versioned database migrations here.
Never apply migrations automatically as part of SETUP.sh.
EOF

echo "==> Creating source registry template"
write_if_missing docs/sources/SOURCE_REGISTRY_TEMPLATE.md <<'EOF'
# Source Registry Record

- Source ID:
- Work title (original language):
- Author:
- Author death year (if verified):
- Edition:
- Publisher:
- Publication year:
- Volume/page scheme:
- Source URL or acquisition record:
- License / rights holder:
- Permitted use: display / quotation / indexing / embedding / AI processing
- Verification status:
- Reviewer:
- Notes:

Do not mark a source as approved until rights and bibliographic details are verified.
EOF

echo "==> Creating architecture and security notes"
write_if_missing docs/architecture/OVERVIEW.md <<'EOF'
# Architecture Overview

- apps/web: Thai-first Quran Reader and Tafsir Chat.
- apps/admin: source registry, ingestion review and operational administration.
- services/api: public application API and external API adapters.
- services/ai-engine: RAG, agent orchestration and evidence validation.
- services/ingestion: authorized book ingestion and metadata processing.
- packages: shared TypeScript types, UI and configuration.
- database: reviewed migrations and seed data.

Arabic Quran text and source quotations must preserve original text.
Thai is the default interface and explanation language.
EOF

write_if_missing docs/security/BASELINE.md <<'EOF'
# Security Baseline

- Never commit .env files, tokens, API keys or private source credentials.
- Keep Quran Foundation OAuth client secrets on the backend.
- Restrict CORS to explicitly configured origins.
- Validate and authorize every user-controlled resource identifier.
- Apply rate limits to authentication, search and AI endpoints.
- Record source provenance and administrative changes.
- Do not expose unlicensed full-text book content.
- SETUP.sh does not install packages, start containers or run migrations.
EOF

echo "==> Creating scripts"
write_if_missing scripts/check-env.sh <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.example to .env and fill in approved credentials."
  exit 1
fi

echo ".env exists. This check does not validate credentials or external API access."
EOF
chmod +x scripts/check-env.sh

write_if_missing README.md <<'EOF'
# QURAN AI

Thai-first Quran study and evidence-based Tafsir platform.

## Repository structure

- `apps/web` — Quran Reader and Tafsir Chat
- `apps/admin` — content and source administration
- `services/api` — FastAPI application API
- `services/ai-engine` — RAG and Tafsir agent orchestration
- `services/ingestion` — authorized source ingestion
- `packages` — shared frontend packages
- `database` — reviewed migrations and seeds
- `docs` — product, architecture, source and security documentation

## Initial setup

```bash
cp .env.example .env
```

Edit `.env` locally. Do not commit it.

This scaffold intentionally does not install dependencies, create database
schemas, download books, start containers or call external APIs.

## Principles

1. Thai is the default UI and AI response language.
2. Quran Arabic and Arabic source quotations must preserve the original text.
3. Every source-attributed claim must be traceable to a retrieved source.
4. Never fabricate citations, page numbers, hadith gradings or scholarly views.
5. Confirm source rights before ingestion, indexing, quotation or AI processing.
EOF

echo
echo "Scaffold complete."
echo "No dependencies installed; no containers started; no database migrations run."
echo "Next: review the generated structure, then configure .env locally."
if [[ "$FORCE" == "1" ]]; then
  echo "NOTE: FORCE=1 was used; existing generated files may have been replaced."
fi
