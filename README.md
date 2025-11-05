# E‑Commerce — v0.6

> Rama por defecto: `main`. Todas las contribuciones deben entrar vía Pull Request a `main` con CI verde.

Este repositorio contiene el backend FastAPI y utilitarios para correr validaciones locales. Cambios clave desde v0.4 a v0.6:

- Canonicalizamos slashes en la API para evitar redirecciones 307 que pueden perder el header `Authorization`.
- Agregamos un script de humo (PowerShell) para validar el flujo E2E de checkout en un comando.
- Incorporamos Dashboard Admin v0.6 con endpoints de métricas y vistas parciales HTMX.

## Ajuste de slashes

Para evitar 307 automáticos que rompen `Authorization`, la app FastAPI está configurada con:

- `app.router.redirect_slashes = False` al crear la app.

Recomendación: mantener consistencia de rutas; si una ruta se define con `/path/`, usar siempre el trailing slash al consumirla.

## Smoke Checkout (PowerShell)

Script: `ops/scripts/smoke_checkout.ps1`

Valida el flujo completo: login → catálogo → carrito → lock → checkout → direcciones (listar/seleccionar) → confirmación. Devuelve el `orderNumber` y si se puede proceder a pago.

### Uso rápido

- `pwsh ops/scripts/smoke_checkout.ps1`

### Parámetros

- `Base`: URL base de API (default `http://localhost:8000/api/v1`).
- `Email`: usuario (default `admin@example.com`).
- `Password`: password (default `admin123`).
- `SessionId`: cookie de sesión para enlazar carrito/checkout (default `smoke5`).

Ejemplo:

- `pwsh ops/scripts/smoke_checkout.ps1 -Base "http://localhost:8000/api/v1" -Email "admin@example.com" -Password "admin123" -SessionId "smoke_local"`

Salida esperada:

```
{
  "orderNumber": "ORD-XXXX",
  "canProceedToPayment": true
}
```

### Requisitos

- Backend corriendo en `http://localhost:8000` (por Docker Compose):
  - `docker compose up -d`
- Catálogo con al menos 1 producto.
- Direcciones existentes para el usuario (el script toma la primera shipping/billing). Si no existen, crear vía API o UI.

## Dashboard Admin v0.6

Endpoints nuevos bajo `GET /api/v1/admin/metrics/*` (requieren autenticación y rol admin):

- `GET /api/v1/admin/metrics/daily?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /api/v1/admin/metrics/categories?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /api/v1/admin/metrics/stock`

UI (vistas HTMX parciales) disponibles en:

- `http://localhost:8000/admin/dashboard` — página principal (requiere login)
- Parciales:
  - `/admin/partials/kpis`
  - `/admin/partials/daily`
  - `/admin/partials/categories`
  - `/admin/partials/stock`

Acceso rápido (seed admin):

- Crear/validar usuario admin: `docker compose exec backend python -m app.seed_admin admin@example.com admin123`
- Login por API: `POST /api/v1/auth/login` con `{"email":"admin@example.com","password":"admin123"}`

### Tests de integración

Se añadieron pruebas para asegurar disponibilidad y contrato básico de estos endpoints:

- `backend/tests/integration/test_admin_metrics_daily.py`
- `backend/tests/integration/test_admin_metrics_categories.py`
- `backend/tests/integration/test_admin_metrics_stock.py`

Ejecutar:

- `docker compose exec backend pytest -q /app/tests/integration/test_admin_metrics_daily.py /app/tests/integration/test_admin_metrics_categories.py /app/tests/integration/test_admin_metrics_stock.py`

### Script de humo (métricas)

Para validar rápidamente autenticación y respuestas básicas de métricas admin:

- `ops/scripts/smoke_admin_metrics.ps1`

Uso:

- `pwsh ops/scripts/smoke_admin_metrics.ps1 -Base "http://localhost:8000/api/v1" -Email "admin@example.com" -Password "admin123" -From (Get-Date).AddDays(-7).ToString('yyyy-MM-dd') -To (Get-Date).ToString('yyyy-MM-dd')`

Salida esperada (resumen): códigos HTTP y extractos de payload.

## v0.7 — Go-Live Ready (MP Prod + Snapshots + Alertas)

Objetivos:
- Mercado Pago PROD paralelo a sandbox via `MP_ENV`.
- Snapshots diarios para acelerar dashboard (`SNAPSHOTS_ENABLED`).
- Alertas operativas (stock bajo, pagos pendientes, reservas vencidas) (`ALERTS_ENABLED`).
- Exportables CSV desde panel admin.
- Hardening: flags, Nginx proxy `/webhooks/mp`, gzip en snapshots.

Configuración de entornos (`.env`, `.env.test`, `.env.prod`):
- `ENV=dev|test|prod`
- `MP_ENV=sandbox|prod`
- `MP_ACCESS_TOKEN_SANDBOX`, `MP_PUBLIC_KEY_SANDBOX`
- `MP_ACCESS_TOKEN_PROD`, `MP_PUBLIC_KEY_PROD`
- `MP_WEBHOOK_SECRET`
- `BASE_URL=https://<dominio>`
- `MP_WEBHOOK_URL=${BASE_URL}/webhooks/mp` (opcional; por defecto se construye)
- `ADMIN_EMAIL_ALERTS` o `SLACK_WEBHOOK_URL`
- `ALERTS_ENABLED=true|false`
- `SNAPSHOTS_ENABLED=true|false`
- `MP_WEBHOOK_TEST_ENABLED=true|false` (false en prod)
- Thresholds: `LOW_STOCK_THRESHOLD`, `PENDING_PAYMENT_MAX_HOURS`, `STALE_RESERVATION_MAX_MINUTES`

Mercado Pago:
- Verificación de credenciales: `GET /api/v1/payments/mp/credentials/check` → métrica `mp.credentials.ok` si válido.
- Webhook firmado en `/webhooks/mp` (Nginx proxy directo).

Snapshots:
- Tablas: `daily_sales`, `daily_category_sales` (Alembic v0.7).
- Tareas Celery beat: `snapshot_daily_sales` (01:00 AR) y `snapshot_daily_categories` (01:10 AR).
- Endpoints: `GET /api/v1/admin/snapshots/daily`, `GET /api/v1/admin/snapshots/categories`.
- Dashboard consume snapshots por defecto; fallback a consulta si no hay datos del día.

Alertas:
- Servicio: `app/services/alerts.py`.
- Regla stock bajo, pagos pendientes viejos, reservas vencidas.
- Canales: Slack webhook o email (placeholder log).
- Métricas: `alerts.sent.count.{type}`.

Exportables CSV:
- `GET /api/v1/admin/exports/daily.csv?from=...&to=...`
- `GET /api/v1/admin/exports/categories.csv?from=...&to=...`
- Botones agregados en parciales del dashboard admin.

Hardening / Infra:
- Nginx: proxy directo `/webhooks/mp` y gzip para `/api/v1/admin/snapshots/*`.
- Flags: `MP_WEBHOOK_TEST_ENABLED` desactivado en prod.

Tests (mínimo):
- `pytest` integración para snapshots/exports/alerts.
- Playwright E2E básico (login, carga HTMX, export CSV).

Orden sugerido de commits:
- config → db → jobs → alerts → api → ui → tests → docs.

## Cerrar v0.6

- Ajuste de slashes vigente (`redirect_slashes = False`).
- Dashboard Admin disponible y probado (UI y API).
- Scripts de humo: checkout y métricas.
- Ejecutar tests de integración de métricas.
- Crear tag y empujar:
  - `git tag v0.6 && git push --tags`