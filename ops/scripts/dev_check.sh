#!/usr/bin/env bash
set -e
echo "→ Ruff + mypy"
docker compose exec -T backend ruff check .
docker compose exec -T backend mypy app || true