
# ADR-010 — Gobernanza, Convenciones y Control del Repositorio

**Fecha:** 2025-11-04  
**Estado:** ✅ Aprobado  
**Autor:** Antonio Romero  
**Proyecto:** E-Commerce + Dashboard (AR / Mercado Pago)

---

## 1) Contexto

Con arquitectura, seguridad, CI/CD y testing consolidados, es necesario establecer **normas de colaboración y versionado** que aseguren consistencia, trazabilidad y calidad del repositorio.  
Este ADR define:

- Estructura de ramas (GitFlow híbrido).  
- Convenciones de commits y PRs.  
- Versionado SemVer.  
- Codeowners y revisiones obligatorias.  
- Reglas de documentación, licencias y releases.

---

## 2) Estrategia de ramas

El proyecto adopta una variante liviana de **GitFlow**, adaptada a CI/CD automático.

| Rama | Propósito | Restricciones |
|------|------------|----------------|
| `main` | Producción estable | Solo merge desde `release/*` con PR aprobado |
| `develop` | Integración principal | PR desde `feature/*` o `fix/*` |
| `feature/*` | Nuevas funciones | Prefijo `feature/<dominio>` |
| `fix/*` | Corrección de errores | Prefijo `fix/<issue>` |
| `hotfix/*` | Urgentes en producción | Merge directo a `main` + `develop` |
| `release/*` | Preparar versión estable | Tests y documentación antes del merge |

**Protecciones:**  
- `main` y `develop` son *branch-protected*.  
- Requieren CI/CD ✅ y **dos revisores** (uno senior).  
- Sin commits directos: solo merge por PR.

---

## 3) Convención de commits (Conventional Commits)

<tipo>(<área>): <mensaje breve>

tipos permitidos:
feat → nueva funcionalidad
fix → corrección
docs → documentación
style → formato/código sin lógica
refactor → reestructuración interna
perf → mejora de rendimiento
test → nuevos tests o fixtures
chore → mantenimiento interno

Ejemplos:
feat(auth): implement JWT refresh rotation
fix(orders): corregir cálculo de stock reservado
docs(adr): agregar ADR-009 sobre autenticación

Esto permite generar **CHANGELOG** y **versiones automáticas**.

---

## 4) Versionado Semántico (SemVer)
- **MAJOR:** cambios incompatibles (breaking changes).  
- **MINOR:** nuevas funciones compatibles.  
- **PATCH:** correcciones o mejoras menores.

Reglas CI/CD:
- Merge a `main` desde `release/*` → crea **tag `vX.Y.Z`** automático.  
- CHANGELOG generado por `semantic-release` (basado en commits).

---

## 5) Pull Requests (PRs)

| Requisito | Detalle |
|------------|----------|
| Plantilla obligatoria | `.github/pull_request_template.md` con: descripción, issue, checklist |
| Revisores requeridos | 2 (mínimo 1 senior) |
| Checks automáticos | CI/CD, coverage ≥ 90 %, lint/mypy OK |
| Resolución de conflictos | Rebase preferido sobre merge manual |
| Etiquetas | `feature`, `fix`, `security`, `docs`, `infra`, `refactor` |
| Issue link | `Closes #<número>` en descripción |

---

## 6) Code Review & CODEOWNERS

Archivo `CODEOWNERS`:

/backend/ @antonioromero
/frontend/ @antonioromero
/docker/ @antonioromero
/docs/ @antonioromero
/tests/ @antonioromero

**Reglas:**
- Ningún PR a `main` sin aprobación del owner.  
- Revisores deben validar **seguridad, rendimiento y estilo**.  
- Uso obligatorio de **GitHub Review Checklist**:  
  - ✅ Código limpio y documentado  
  - ✅ Tests actualizados  
  - ✅ Sin secretos ni datos reales  
  - ✅ Desempeño sin regresión

---

## 7) Documentación y Licencia

- Cada módulo tiene README local (`/backend/auth/README.md`, etc.).  
- Documentación técnica en `/docs/adr/` y `/docs/diagrams/`.  
- Licencia MIT (archivo `LICENSE`).  
- Archivo `CONTRIBUTING.md` con guías de estilo y flujo de PRs.  
- `SECURITY.md` para vulnerabilidades (report vía email privado).  
- `CODE_OF_CONDUCT.md` basado en Contributor Covenant.

---

## 8) Automatización y Hooks

### Pre-commit
Ejecuta: `black`, `ruff`, `isort`, `mypy`, `pytest -q`.

### GitHub Actions
- Workflow `ci.yml` ejecuta test + coverage + build.  
- Workflow `release.yml` crea tag y changelog.  
- Workflow `security.yml` ejecuta `bandit` + `trivy`.

---

## 9) Diagrama — GitFlow Simplificado

### `docs/diagrams/git_flow.puml`

```plantuml
@startuml
title GitFlow Simplificado — E-Commerce + Dashboard

actor Dev
participant "feature/*" as FE
participant "develop" as DEV
participant "release/*" as REL
participant "main" as MAIN

Dev -> FE : crea rama feature
FE -> DEV : PR → merge (CI/CD)
DEV -> REL : cuando estable → crear release/x.y.z
REL -> REL : tests + docs
REL -> MAIN : merge → tag vX.Y.Z
MAIN -> DEV : back-merge cambios
@enduml