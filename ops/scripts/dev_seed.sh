#!/usr/bin/env bash
set -e
echo "→ Creando admin por defecto (admin@local / admin123)"
docker compose exec -T backend python -m app.seed_admin
echo "→ Seed de catálogo demo"
docker compose exec -T backend python -m app.seed_catalog
echo "→ Seed de inventario demo"
docker compose exec -T backend python -m app.seed_inventory
echo "→ Seed de direcciones demo"
docker compose exec -T backend python -m app.seed_addresses