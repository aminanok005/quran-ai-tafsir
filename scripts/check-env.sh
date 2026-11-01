#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.example to .env and fill in approved credentials."
  exit 1
fi

echo ".env exists. This check does not validate credentials or external API access."
