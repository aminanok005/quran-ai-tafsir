# Security Baseline

- Never commit .env files, tokens, API keys or private source credentials.
- Keep Quran Foundation OAuth client secrets on the backend.
- Restrict CORS to explicitly configured origins.
- Validate and authorize every user-controlled resource identifier.
- Apply rate limits to authentication, search and AI endpoints.
- Record source provenance and administrative changes.
- Do not expose unlicensed full-text book content.
- SETUP.sh does not install packages, start containers or run migrations.
