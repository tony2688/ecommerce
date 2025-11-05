# # ADR-005 — CI/CD y Control de Calidad

**Fecha:** 2025-11-03  
**Estado:** ✅ Aprobado  
**Autor:** Antonio Romero  
**Proyecto:** E-Commerce + Dashboard (AR / Mercado Pago)

---

## 1) Contexto

Con la arquitectura, consistencia, modelo de datos y observabilidad definidos, el siguiente paso es garantizar **entregas controladas, reproducibles y verificadas automáticamente**.

El objetivo es establecer una **canalización CI/CD estándar**, con:

- Validación automática de estilo, tipado y seguridad.  
- Ejecución de tests unitarios e integración.  
- Construcción y despliegue dockerizado sin intervención manual.  
- Control de calidad (Quality Gates) en cada commit o PR.  
- Versionado semántico y despliegues consistentes en entornos *dev/staging/prod*.

---

## 2) Decisiones

| Área | Decisión |
|------|-----------|
| **Repositorio** | GitHub (workflow `.github/workflows/ci.yml`). |
| **CI Runner** | GitHub Actions Ubuntu LTS. |
| **Linter/Formatter** | `black`, `ruff`, `isort`. |
| **Type Checking** | `mypy` (modo estricto). |
| **Tests** | `pytest` con `coverage>=90%`. |
| **Security** | `bandit` + `safety check` en requirements. |
| **Build** | Docker multi-stage (`api`, `worker`, `nginx`). |
| **Deploy** | GitHub Actions → VPS (Ubuntu 24.04) vía SSH o Docker Registry. |
| **Versioning** | SemVer + etiquetas `vMAJOR.MINOR.PATCH`. |
| **Quality Gate** | CI falla si hay errores o cobertura < 90 %. |

---

## 3) Estructura del flujo CI/CD

infra/ci/
├── github-actions.yml
├── pre-commit-config.yaml
└── quality/
├── linting.yml
├── testing.yml
├── build.yml
└── deploy.yml

markdown
Copiar código

- **pre-commit**: ejecuta linters y formato local.  
- **ci.yml**: pipeline principal de Actions (build/test/deploy).  
- **quality/**: plantillas internas de jobs para reutilización.

---

## 4) Etapas del pipeline

| Fase | Descripción | Tools |
|------|--------------|-------|
| **1. Lint & Typecheck** | Revisa estilo, imports, tipado. | `black`, `ruff`, `isort`, `mypy` |
| **2. Tests** | Ejecuta `pytest`, genera coverage y reportes. | `pytest`, `coverage` |
| **3. Security Scan** | Evalúa vulnerabilidades en dependencias. | `bandit`, `safety` |
| **4. Build Docker** | Construye imágenes versionadas (`api`, `worker`, `nginx`). | `docker buildx` |
| **5. Deploy** | Push a registry + `ssh` deploy staging/prod. | `actions/ssh-deploy` |
| **6. Post-Deploy Check** | Healthcheck `/healthz` + Prometheus scrape. | `curl`, `promtool` |

---

## 5) Diagrama — Flujo CI/CD

### `docs/diagrams/cicd_pipeline.puml`

```plantuml
@startuml
title CI/CD Pipeline — E-Commerce + Dashboard

actor Developer
participant "GitHub Actions" as GH
participant "Docker Builder" as DB
participant "Staging Server" as STG
participant "Production Server" as PROD
participant "Grafana/Prometheus" as MON

Developer -> GH : push / pull_request
GH -> GH : Run pre-commit (black, ruff, isort)
GH -> GH : Run mypy + pytest + coverage
GH -> GH : Run bandit + safety
GH -> DB : Build Docker images (api, worker, nginx)
DB -> GH : Push to GHCR / Registry
GH -> STG : Deploy via SSH (staging)
STG -> GH : Run healthcheck
alt passed tests & metrics OK
  GH -> PROD : Deploy production
  PROD -> MON : Expose metrics / logs
else failure
  GH -> Developer : Fail + logs + PR blocked
end
@enduml
