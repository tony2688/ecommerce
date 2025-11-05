# skeleton# ADR-003 — Modelo de Datos v1 (ERD Detallado)

**Fecha:** 2025-11-03  
**Estado:** ✅ Aprobado  
**Autor:** Antonio Romero  
**Proyecto:** E-Commerce + Dashboard (AR / Mercado Pago)

---

## 1) Contexto

Luego de definir la arquitectura (ADR-001) y los mecanismos de consistencia (ADR-002), se requiere formalizar el **modelo relacional inicial** del sistema.

El objetivo es establecer una base de datos **normalizada, auditable y escalable**, con soporte para:
- Catálogo de productos jerárquico.  
- Inventario multi-sucursal.  
- Órdenes y pagos integrados con Mercado Pago.  
- Usuarios y roles (multi-rol).  
- Reseñas, notificaciones y cupones.  
- Persistencia para idempotencia, outbox y webhooks.

La base seleccionada es **MySQL 8.4.7 LTS**, motor **InnoDB** (ACID, FK, transacciones).

---

## 2) Decisiones de diseño

| Tema | Decisión |
|------|-----------|
| **Modelo** | Relacional normalizado con claves foráneas y soft-delete lógico. |
| **Integridad** | Constraints FK + índices compuestos (para reporting e idempotencia). |
| **Escalabilidad** | Campos `created_at`, `updated_at`, `version` en todas las tablas críticas. |
| **Auditoría** | Tablas `*_history` o triggers para operaciones clave (orders, payments). |
| **Claves** | Uso de `BIGINT UNSIGNED AUTO_INCREMENT` o `UUID` según dominio. |
| **Prefijos** | Tablas agrupadas por dominio (`auth_user`, `catalog_product`, etc.). |
| **ORM** | SQLAlchemy 2.0 con migraciones Alembic. |

---

## 3) Entidades principales

### 🔹 Auth & Accounts
| Tabla | Propósito | Campos clave |
|--------|------------|--------------|
| `auth_user` | Usuarios del sistema (buyer/admin/seller) | id, email, password_hash, role_id |
| `auth_role` | Roles y permisos básicos | id, name, description |
| `auth_session` | Sesiones activas / tokens | id, user_id, session_token, expires_at |

---

### 🔹 Catálogo
| Tabla | Propósito |
|--------|------------|
| `catalog_category` | Jerarquía ilimitada (self FK → `parent_id`) |
| `catalog_product` | Datos principales del producto |
| `catalog_variant` | Variaciones (color, tamaño, SKU) |
| `catalog_media` | Imágenes asociadas |
| `catalog_review` | Reseñas + calificaciones (1–5 estrellas) |

---

### 🔹 Pricing & Cupones
| Tabla | Propósito |
|--------|------------|
| `pricing_price` | Precio minorista/mayorista por producto/variant |
| `pricing_coupon` | Cupones configurables (tipo, valor, expiración, usos) |
| `pricing_cost` | Costos de proveedor y margen de ganancia |

---

### 🔹 Inventario
| Tabla | Propósito |
|--------|------------|
| `inventory_warehouse` | Sucursales/depósitos |
| `inventory_stock` | Existencias por variante/sucursal (`qty`, `reserved_qty`, `version`) |
| `inventory_ledger` | Movimientos de stock (FEFO/FIFO, ajuste, traspaso) |
| `inventory_transfer` | Traspasos entre sucursales (estado → borrador/aprobado/recibido) |

---

### 🔹 Carrito y Checkout
| Tabla | Propósito |
|--------|------------|
| `cart_cart` | Carrito por usuario o sesión anónima |
| `cart_item` | Items del carrito (variant_id, qty, price_snapshot) |
| `checkout_address` | Direcciones de envío/facturación |
| `checkout_order` | Pedido generado (status, total, user_id) |
| `checkout_order_item` | Productos incluidos (variant_id, qty, subtotal) |

---

### 🔹 Pagos
| Tabla | Propósito |
|--------|------------|
| `payment_payment` | Pagos Mercado Pago (idempotente por `mp_payment_id`) |
| `payment_webhook_event` | Registro de webhooks recibidos |
| `payment_withdrawal` | Solicitudes de retiro (para sellers) |

---

### 🔹 Notificaciones
| Tabla | Propósito |
|--------|------------|
| `notification_log` | Email/push enviados (`notification_key`, status) |
| `otp_attempt` | Intentos OTP (registro, recuperación) |

---

### 🔹 Infra / Soporte
| Tabla | Propósito |
|--------|------------|
| `idempotency_key` | Control de re-ejecución de requests |
| `outbox_event` | Eventos pendientes de publicación |
| `system_audit` | Auditoría genérica |
| `system_config` | Parámetros globales (modo mantenimiento, API keys, etc.) |

---

## 4) Relaciones principales
auth_user 1───∞ checkout_order 1───∞ checkout_order_item
catalog_product 1───∞ catalog_variant 1───∞ inventory_stock
inventory_stock 1───∞ inventory_ledger
checkout_order 1───1 payment_payment
payment_payment 1───∞ payment_webhook_event
catalog_variant 1───∞ cart_item
cart_cart 1───∞ cart_item
auth_user 1───∞ cart_cart
inventory_warehouse 1───∞ inventory_stock


---

## 5) Índices y optimización

| Tipo | Ejemplo |
|------|----------|
| PK | `PRIMARY KEY (id)` |
| UK | `UNIQUE (email)` en `auth_user`, `UNIQUE (mp_payment_id)` en `payment_payment` |
| IDX | `(status, created_at)` en `checkout_order` |
| FK | `FOREIGN KEY (user_id) REFERENCES auth_user(id)` |
| CHECK | `rating BETWEEN 1 AND 5` en `catalog_review` |

---

## 6) Estrategias de escalabilidad

- **Partitioning** por `tenant_id` o `warehouse_id` en futuras versiones.  
- **Read replicas** para métricas/reportes.  
- **Caching selectivo** en `pricing_price` y `catalog_product` con Redis.  
- **Soft deletes** con campo `deleted_at`.  
- **Optimistic locking** (`version`) en tablas críticas (`inventory_stock`, `checkout_order`).  

---

## 7) ERD Diagramas

### A) `docs/diagrams/erd_global.puml`

```plantuml
@startuml
!define Table(name,desc) class name as "name\n<desc>" << (T,#ffebcd) >>
!theme plain

title ERD Global — E-Commerce + Dashboard

Table(auth_user, "Usuarios")
Table(auth_role, "Roles")
Table(catalog_category, "Categorías")
Table(catalog_product, "Productos")
Table(catalog_variant, "Variantes")
Table(inventory_stock, "Stock por sucursal")
Table(checkout_order, "Pedidos")
Table(payment_payment, "Pagos MP")
Table(payment_webhook_event, "Webhooks MP")
Table(outbox_event, "Outbox")
Table(idempotency_key, "Idempotencia")

auth_role "1" -- "∞" auth_user : role_id
catalog_category "1" -- "∞" catalog_product : category_id
catalog_product "1" -- "∞" catalog_variant : product_id
catalog_variant "1" -- "∞" inventory_stock : variant_id
auth_user "1" -- "∞" checkout_order : user_id
checkout_order "1" -- "1" payment_payment : order_id
payment_payment "1" -- "∞" payment_webhook_event : payment_id
@enduml


