# ADR-009 — Autenticación, Autorización y RBAC (JWT + OAuth2 + Refresh)

**Fecha:** 2025-11-04  
**Estado:** ✅ Aprobado  
**Autor:** Antonio Romero  
**Proyecto:** E-Commerce + Dashboard (AR / Mercado Pago)

---

## 1) Contexto

El sistema requiere identidad **segura y granular** para tres perfiles principales: `admin`, `manager/seller`, `buyer`.  
Debemos cubrir:
- **Login** por email/contraseña (bcrypt).  
- **Tokens** de acceso con **expiración corta** y **refresh rotation**.  
- **RBAC** por rol y permisos finos.  
- **OAuth (Google)** preparado.  
- **Protecciones web**: CSRF, CORS, rate limit.  
- **Auditoría** y revocación de sesiones.

Alineado con ADR-007 (Seguridad) y ADR-005 (CI/CD).

---

## 2) Decisiones

| Área | Decisión |
|------|----------|
| **Protocolo** | OAuth2 Password + Bearer tokens (FastAPI Security). |
| **Token Access** | **JWT HS256** (exp. 15 min). Requiere `jti`, `sub`, `role`, `scope`, `iat`, `exp`. |
| **Token Refresh** | **JWT** (exp. 7 días) con **rotación** (one-time use) y **lista de revocados** (Redis). |
| **Almacenamiento** | API: Header `Authorization: Bearer <access>`; Front web (Jinja+htmx): **cookie HttpOnly** + **CSRF** doble. |
| **RBAC** | Roles base (`admin`, `manager`, `seller`, `buyer`) + **permisos** por dominio (catálogo, inventario, pedidos, pagos, reportes). |
| **Password** | `bcrypt` cost=12, política OWASP (longitud ≥ 10, complejidad). |
| **2FA/OTP** | Opcional: TOTP o SMS/Email OTP para acciones sensibles (retiros, cambios críticos). |
| **OAuth** | Proveedor Google (OIDC); mapea email verificado → `buyer` por defecto (elevación manual). |
| **Auditoría** | `system_audit` registra in/out, refresh, revocación, intentos fallidos. |
| **Rate limit** | 100 req/min por IP (nginx/Redis), 5 intentos de login/10 min por usuario (lockout temporal). |

---

## 3) Modelo de datos (resumen)

Tablas (complemento ADR-003):

- `auth_user(id, email, password_hash, is_active, email_verified_at, created_at, updated_at)`  
- `auth_role(id, name, description)`  
- `auth_permission(id, code, description)`  
- `auth_user_role(user_id, role_id)` (UK compuesta)  
- `auth_role_permission(role_id, permission_id)`  
- `auth_session(id, user_id, user_agent, ip, created_at, revoked_at)`  
- `auth_refresh_token(id, user_id, jti, session_id, issued_at, expires_at, rotated_at, revoked_at, reason)` (UK jti)  
- `auth_oauth_account(id, user_id, provider, provider_user_id, email, meta, linked_at)`  
- `otp_attempt(id, user_id/email, purpose, code_hash, expires_at, attempts, consumed_at)`  
- `system_audit(id, when, actor_id, action, resource, ip, ua, meta)`

**Índices clave**:  
- `auth_user.email` (UNIQUE)  
- `auth_refresh_token.jti` (UNIQUE)  
- `auth_oauth_account.provider + provider_user_id` (UNIQUE)  
- `system_audit.when` (reportes)  

---

## 4) Flujos

### 4.1 Login (password)
1. Usuario envía credenciales.  
2. Validación y **password hashing** (`bcrypt`).  
3. Se emite **Access JWT (15m)** + **Refresh JWT (7d)**; se crea `auth_session`.  
4. Front web: `access` en **cookie HttpOnly** + **CSRF cookie**; API pura: header `Authorization`.  
5. Auditoría `login_success`.

### 4.2 Refresh Rotation
1. Cliente envía **Refresh** (cookie o header).  
2. Verificar **revocado** por `jti` (Redis/DB).  
3. Emitir nuevo par (**Access + Refresh**) y **revocar** el viejo (set `rotated_at`).  
4. Si reuso de refresh antiguo → **revocar** toda la sesión (compromiso).  

### 4.3 Logout / Revocación
- Invalidar **refresh actual** y marcar `auth_session.revoked_at`.  
- Opcional: revocar **todas** las sesiones del usuario (compromiso).

### 4.4 OAuth (Google)
- OIDC code → token → email verificado.  
- Usuario nuevo: crear `auth_user` con `buyer`.  
- Usuario existente: vincular a `auth_oauth_account`.

### 4.5 Acciones sensibles (retiros, permisos)
- Requieren **2FA** (OTP TOTP/Email) + **confirmación**.  
- Expiración corta (≤ 10 min) y **idempotencia** (ADR-002).

---

## 5) RBAC — Roles y permisos

Permisos mínimos por dominio (ejemplos):

- `catalog:read|write|approve`  
- `inventory:read|adjust|transfer|approve`  
- `orders:read|manage|refund`  
- `payments:read|reconcile|withdraw_approve`  
- `reviews:moderate`  
- `reporting:view_finance|view_ops`  
- `users:manage_roles`

Roles por defecto:

- **admin**: todos los permisos.  
- **manager**: catálogo, inventario, pedidos, reportes.  
- **seller**: sus productos/pedidos, POS, solicitudes de retiro.  
- **buyer**: compra, reseñas, perfil.

---

## 6) Seguridad Web

- **Cookies**: `HttpOnly`, `Secure`, `SameSite=Lax` (o `Strict` en dashboard).  
- **CSRF**: token doble (cookie + header `X-CSRF-Token`) en POST/PUT/PATCH/DELETE.  
- **CORS**: orígenes explícitos por entorno (tenant subdomains).  
- **Headers**: CSP estricta, HSTS, X-Frame-Options DENY, X-Content-Type-Options nosniff.  
- **Rate limit**: login y endpoints sensibles.  
- **Logs**: nunca guardar contraseñas o tokens; ofuscar patrones.

---

## 7) Errores y auditoría

- `login_failed`, `login_locked`, `token_reuse_detected`, `refresh_rotated`, `logout`, `role_changed`.  
- Guardar IP/UA y `session_id`.  
- Alertar si hay **reutilización de refresh** (posible robo).

---

## 8) Alternativas consideradas

| Alternativa | Motivo de descarte |
|-------------|--------------------|
| **Solo sesiones server-side** | Simplicidad, pero limita integraciones API y apps móviles. |
| **Opaque tokens + store central** | Más IO/latencia y dependencia del store; JWT con jti cubre necesidades. |
| **Proveedor externo (Auth0, Cognito)** | Coste y vendor lock-in; se prioriza control local. |

---

## 9) Consecuencias

**Positivas**: tokens cortos + refresh rotado → menor superficie de ataque; RBAC flexible; auditable; escalable.  
**Negativas**: mayor complejidad (rotación, blacklist, 2FA); housekeeping de sesiones/revocados.

---

## 10) Variables de entorno (mínimas)

- `JWT_SECRET` (HS256, ≥ 256 bits)  
- `JWT_ACCESS_TTL=900` (seg)  
- `JWT_REFRESH_TTL=604800` (seg)  
- `JWT_ISSUER=ecommerce.api`  
- `SECURE_COOKIES=true`  
- `CSRF_ENABLED=true`  
- `OAUTH_GOOGLE_CLIENT_ID/SECRET`  
- `RATE_LIMIT_PER_MIN=100`

---

## 11) Decisión final

Se implementa **OAuth2 + JWT (access 15m / refresh 7d, rotación y revocación con jti)**,  
**RBAC** con permisos por dominio, **2FA opcional** para acciones críticas,  
y protecciones web (CSRF, CORS, headers, rate limit), con **auditoría completa**.

---

