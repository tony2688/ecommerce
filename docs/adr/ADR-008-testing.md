# # ADR-008 — Testing y Validación

**Fecha:** 2025-11-03  
**Estado:** ✅ Aprobado  
**Autor:** Antonio Romero  
**Proyecto:** E-Commerce + Dashboard (AR / Mercado Pago)

---

## 1) Contexto

El sistema abarca múltiples dominios (auth, catálogo, pagos, inventario, etc.) y una integración compleja con **Mercado Pago, Redis, Celery y MySQL**.  
Para mantener fiabilidad y velocidad de entrega, se requiere una estrategia de **testing automatizado multi-nivel**, abarcando:

- Validación funcional (unitaria e integración).  
- Validación de interfaces (API contract, frontend).  
- Validación no funcional (performance, seguridad).  
- Integración continua (ADR-005) con Quality Gates automáticos.

---

## 2) Objetivos

1. Prevenir regresiones funcionales y de seguridad.  
2. Garantizar consistencia de flujos críticos (checkout, pagos, stock).  
3. Validar contratos de APIs externas (Mercado Pago / Envíos).  
4. Asegurar 90%+ de cobertura de código en módulos críticos.  
5. Permitir despliegues seguros y confiables en entornos CI/CD.

---

## 3) Pirámide de Testing

### `docs/diagrams/testing_pyramid.puml`

```plantuml
@startuml
title Pirámide de Testing — E-Commerce + Dashboard

skinparam rectangle {
  BackgroundColor<<Unit>> #22C55E
  BackgroundColor<<Integration>> #6C63FF
  BackgroundColor<<E2E>> #007AFF
  BackgroundColor<<Contract>> #FACC15
  BackgroundColor<<NonFunctional>> #EF4444
}

rectangle "Unit Tests (pytest)" <<Unit>> {
  note right: Modelos, servicios,\nutils, validaciones
}

rectangle "Integration Tests" <<Integration>> {
  note right: API interna, ORM, Redis, Celery
}

rectangle "Contract Tests" <<Contract>> {
  note right: Webhooks y SDK Mercado Pago,\nendpoints REST externos
}

rectangle "E2E / UI Tests" <<E2E>> {
  note right: Flujos completos (login→checkout→pago)
}

rectangle "Non-Functional Tests" <<NonFunctional>> {
  note right: Performance, estrés, seguridad (bandit)
}

Unit Tests -down-> Integration Tests
Integration Tests -down-> Contract Tests
Contract Tests -down-> E2E / UI Tests
E2E / UI Tests -down-> Non-Functional Tests

@enduml

4) Tipos de pruebas y herramientas
Nivel	Objetivo	Herramienta	Alcance
Unit	Validar funciones y lógica aislada	pytest	Models, utils, services
Integration	Validar módulos combinados	pytest + TestClient FastAPI	DB, Redis, Celery
Contract	Verificar contratos externos	pytest, schemathesis, mocks httpx	Webhooks MP / Envia
E2E/UI	Validar flujo completo	Playwright (headless)	Login, carrito, checkout
Performance	Cargar endpoints críticos	k6 o locust	Checkout, catálogo
Security	Analizar vulnerabilidades	bandit, safety	Código y dependencias
5) Estructura del proyecto de tests
tests/
├── unit/
│   ├── test_models.py
│   ├── test_utils.py
│   └── test_services.py
├── integration/
│   ├── test_auth_api.py
│   ├── test_orders_flow.py
│   ├── test_inventory_sync.py
│   └── test_celery_tasks.py
├── contract/
│   ├── test_mp_webhook_contract.py
│   ├── test_envia_api_contract.py
│   └── schemas/
│       ├── mercado_pago.json
│       └── envia.json
├── e2e/
│   ├── test_checkout_flow.spec.js
│   ├── test_login.spec.js
│   └── fixtures/
│       ├── users.json
│       └── products.json
└── performance/
    ├── load_checkout.js
    └── load_catalogo.js
