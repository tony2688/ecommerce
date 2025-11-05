# ADR-001 — Arquitectura y Dominios (DDD)

**Fecha:** 2025-11-03  
**Estado:** ✅ Aprobado  
**Autores:** Antonio Romero  
**Proyecto:** E-Commerce + Dashboard (Argentina / Mercado Pago)

---

## 🧠 Contexto

El sistema debe ofrecer una plataforma de **e-commerce completa con dashboard administrativo multi-rol**, integrada con **Mercado Pago**, **inventario multi-sucursal** y **facturación futura AFIP**.

Los objetivos principales son:
- Escalabilidad modular y mantenible.  
- Integración ágil con APIs externas (Mercado Pago, servicios de envío).  
- Rendimiento estable con cargas concurrentes moderadas.  
- Código limpio, tipado estricto y CI/CD automatizado.  

El entorno técnico y operativo se basa en:
- **FastAPI 0.120.4** como framework backend.  
- **MySQL 8.4.7 LTS** como base de datos transaccional.  
- **Redis 7.4.6 + Celery 5.4.0** para colas de tareas y cache.  
- **Jinja2 + htmx + Alpine.js + SCSS** como frontend liviano sin SPA.  
- **Ubuntu Server 24.04 + Nginx + Docker Compose** en la capa de infraestructura.

---

## 🧩 Decisión

Se adopta una **arquitectura basada en dominios (Domain-Driven Design, DDD)**, organizada por contextos delimitados dentro de `backend/app/`.

**Bounded Contexts:**
1. **Auth & Accounts** → usuarios, roles, permisos, sesiones.  
2. **Catalog** → productos, variantes, categorías, media.  
3. **Pricing** → precios retail/mayorista, cupones, costos.  
4. **Inventory** → stock multi-sucursal, ledger, lotes/serie, reorden.  
5. **Cart & Checkout** → carritos, direcciones, proceso de pago.  
6. **Orders** → órdenes, estados, historial.  
7. **Payments** → integración Mercado Pago (checkout API/Bricks, webhooks).  
8. **Shipping** → envíos, carriers, tracking, etiquetas.  
9. **Reviews** → reseñas, calificaciones, moderación.  
10. **Notifications** → emails, web-push, OTP.  
11. **Reporting** → métricas, dashboards, exportaciones.

Cada dominio incluye su propio módulo con modelos, esquemas (Pydantic), rutas, servicios y pruebas unitarias.

---

## ⚙️ Justificación

**Motivos técnicos y estratégicos:**

- **DDD** permite aislar la lógica de negocio por contexto, facilitando la escalabilidad y testing.  
- **FastAPI** ofrece rendimiento asíncrono, tipado estricto y OpenAPI nativo.  
- **htmx + Alpine.js** eliminan la necesidad de una SPA compleja, manteniendo tiempos de carga bajos.  
- **SQLAlchemy 2.0 + Alembic** brindan ORM moderno y migraciones seguras.  
- **Celery + Redis** garantizan ejecución asíncrona confiable (pagos, emails, webhooks).  
- **Infraestructura Dockerizada** permite portabilidad y CI/CD continuo.  
- Cumple con el objetivo de **simplicidad + robustez + trazabilidad**.

---

## ⚖️ Alternativas consideradas

| Alternativa | Motivo de descarte |
|--------------|--------------------|
| **Django Monolítico** | Acoplamiento alto, poca flexibilidad por dominio. |
| **React/Next.js SPA** | Overhead de complejidad, ralentiza MVP y SEO server-side. |
| **Node/Express** | Rompe uniformidad del stack Python ya adoptado. |
| **Microservicios tempranos** | Prematuro para el volumen esperado; DDD modular permite futura separación sin sobrecoste. |

---

## 🔁 Consecuencias

**Positivas**
- Modularidad, claridad y testing granular.  
- Escalabilidad progresiva (posible transición a microservicios).  
- CI/CD más controlado por dominio.  
- Mantenibilidad y onboarding simple para nuevos desarrolladores.

**Negativas**
- Estructura inicial extensa (muchos directorios vacíos).  
- Requiere disciplina en convenciones y versionado de esquemas.  
- Mayor tiempo de documentación inicial (ADRs, RFCs).

---

## 🧱 Diagrama C4 (Nivel Sistema y Contenedor)

**Nivel Sistema (visión general):**

