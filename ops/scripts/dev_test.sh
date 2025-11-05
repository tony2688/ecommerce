#!/usr/bin/env bash
set -e
echo "→ Ejecutando tests pytest"
docker compose exec -T backend pytest -q