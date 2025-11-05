# ADR-007 — Seguridad y Control de Acceso

**Fecha:** 2025-11-03  
**Estado:** ✅ Aprobado  
**Autor:** Antonio Romero  
**Proyecto:** E-Commerce + Dashboard (AR / Mercado Pago)

---

## 1) Contexto

El sistema maneja datos financieros, personales y operativos de usuarios, administradores y vendedores.  
Se requiere garantizar **confidencialidad, integridad, disponibilidad y trazabilidad** (modelo CIA+T).

Este ADR establece las políticas y controles mínimos para:

- Autenticación y autorización (RBAC).  
- Protección de API (CSRF, CORS, rate-limit, headers).  
- Seguridad en transporte y almacenamiento.  
- Gestión de secretos y rotación.  
- Endurecimiento (hardening) de Nginx, Docker y Ubuntu Server.  
- Auditoría y detección de incidentes.

---

## 2) Decisiones de diseño

| Componente | Decisión |
|-------------|-----------|
| **Autenticación** | OAuth2 Password + Bearer Tokens (FastAPI Security). |
| **Autorización** | RBAC granular basado en roles (`admin`, `manager`, `seller`, `buyer`). |
| **Sesiones** | Tokens firmados con JWT (HS256) + expiración 24 h; refresh configurable. |
| **CSRF** | Token doble (cookie + header) en formularios POST. |
| **CORS** | Orígenes explícitos: `https://{tenant}.webinizadev.com`. |
| **Rate limit** | 100 req/min por IP (nginx + Redis limiter). |
| **Headers** | Strict CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy. |
| **Secretos** | `.env` cifrado con Vault (AES-256, rotación 90 días). |
| **Contraseñas** | `bcrypt` (cost = 12) + validación OWASP. |
| **Logs sensibles** | Nunca registrar tokens ni contraseñas; ofuscación por patrón RegEx. |
| **Auditoría** | Tabla `system_audit` + envío opcional a Loki/Grafana. |
| **Infra** | Nginx + Ubuntu reforzados (hardening base CIS). |
| **Red** | Puertos mínimos abiertos (80→443 redirigido, 443, 22 restrictivo). |
| **Docker** | Usuarios no-root, imágenes firmadas, escaneo `trivy`. |

---

## 3) Arquitectura de capas de seguridad

### `docs/diagrams/security_layers.puml`

```plantuml
@startuml
title Capas de Seguridad — E-Commerce + Dashboard

rectangle "Capa Cliente" {
  [Browser / App] --> [HTTPS TLS1.3]
}

rectangle "Capa Web" {
  [Nginx Reverse Proxy]
}

rectangle "Capa Aplicación" {
  [FastAPI Backend]
  [Celery Workers]
}

rectangle "Capa Datos" {
  [MySQL 8.4.7]
  [Redis 7.4.6]
}

rectangle "Capa Monitoreo" {
  [Prometheus]
  [Grafana]
  [Loki]
}

[Browser / App] -down-> [Nginx Reverse Proxy] : HTTPS (TLS1.3)
[Nginx Reverse Proxy] -down-> [FastAPI Backend] : internal HTTPS
[FastAPI Backend] -down-> [MySQL 8.4.7]
[FastAPI Backend] -right-> [Redis 7.4.6]
[Celery Workers] -right-> [Redis 7.4.6]
[Prometheus] -up-> [FastAPI Backend] : /metrics
[Grafana] -up-> [Prometheus]
[Loki] -up-> [Grafana] : Logs
@enduml
