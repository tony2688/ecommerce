# ADR-004 — Observabilidad y Logging (Prometheus / Grafana / OpenTelemetry)

**Fecha:** 2025-11-03  
**Estado:** ✅ Aprobado  
**Autor:** Antonio Romero  
**Proyecto:** E-Commerce + Dashboard (AR / Mercado Pago)

---

## 1) Contexto

Con la arquitectura (ADR-001), la consistencia (ADR-002) y el modelo de datos (ADR-003) definidos, se establece el estándar de **observabilidad** del sistema.  
El objetivo es disponer de **visibilidad completa** sobre:

- Salud y rendimiento de la API y workers.  
- Monitoreo de base de datos, Redis y colas.  
- Métricas de negocio (órdenes, pagos, errores).  
- Logging estructurado y trazas distribuidas.  
- Alertas automatizadas y dashboards visuales.

---

## 2) Decisiones

| Componente | Decisión |
|-------------|-----------|
| **Logs** | Uso de `structlog` + formato JSON; nivel `INFO` en prod, `DEBUG` en dev. |
| **Métricas** | Exposición nativa `/metrics` con **Prometheus client Python**. |
| **Trazas distribuidas** | Integración **OpenTelemetry** (OTLP → Prometheus → Grafana Tempo). |
| **Dashboards** | Consolidados en **Grafana**: API, Worker, DB, Redis, Mercado Pago. |
| **Almacenamiento de logs** | `stdout` (Docker), capturado por Loki / Grafana. |
| **Alertas** | Grafana Alerting (emails/push) + reglas PromQL. |
| **Infraestructura** | Stack: **Prometheus + Node Exporter + Redis Exporter + MySQL Exporter + Grafana + Tempo + Loki**. |

---

## 3) Implementación

### 3.1 Estructura de carpetas

infra/monitoring/
├── prometheus/
│ ├── prometheus.yml
│ ├── alerts.yml
│ └── exporters/
│ ├── node_exporter.yml
│ ├── redis_exporter.yml
│ └── mysql_exporter.yml
├── grafana/
│ ├── dashboards/
│ │ ├── fastapi_overview.json
│ │ ├── celery_worker.json
│ │ └── business_kpis.json
│ ├── datasources.yml
│ └── alerts/
│ ├── latency_5xx.yml
│ └── redis_queue_lag.yml
└── loki/
└── loki.yml


### 3.2 Logs (FastAPI / Celery)

- Se usa **`structlog`** para logs estructurados:
  ```python
  logger.info("payment_approved", order_id=123, amount=25999, tenant="default")


En Docker Compose:
logging.driver: "json-file" → consumido por Grafana Loki.

3.3 Métricas Prometheus

Endpoint: /metrics → expone:

http_requests_total{path,method,status}

celery_tasks_total{status}

db_query_duration_seconds

inventory_stock_levels{warehouse}

Exporters:

node_exporter (sistema)

redis_exporter

mysqld_exporter

3.4 Trazas (OpenTelemetry)

FastAPI Instrumentor → OTEL_EXPORTER_OTLP_ENDPOINT=http://prometheus:4317

Celery Instrumentor → trazas de workers (task_id, retries, duration)

Grafana Tempo usado como backend para visualizar spans.