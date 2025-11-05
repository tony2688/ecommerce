# ADR-006 — Backups & DRP (Disaster Recovery Plan)

**Fecha:** 2025-11-03  
**Estado:** ✅ Aprobado  
**Autor:** Antonio Romero  
**Proyecto:** E-Commerce + Dashboard (AR / Mercado Pago)

---

## 1) Contexto

El sistema maneja datos críticos (órdenes, pagos, inventario, clientes).  
Debemos garantizar **continuidad operativa** y **recuperación ante desastres** con objetivos acordados en NFRs (ADR-001):

- **RTO (Recovery Time Objective):** ≤ 1 hora  
- **RPO (Recovery Point Objective):** ≤ 15 minutos

Este ADR define **qué se respalda**, **cómo**, **dónde**, **por cuánto tiempo**, **quién** puede restaurar y **cómo se prueba**.

---

## 2) Alcance (qué se respalda)

1. **Base de datos MySQL 8.4.7**  
   - Backups **full** + **PITR** con **binlogs**.  
   - Esquema + datos + rutinas (si aplica).

2. **Redis 7.4.6** (colas/cache)  
   - No es fuente de verdad, pero se guardan **snapshots RDB** diarias (para diagnóstico/forense).  
   - No se exige restaurar Redis para volver a operar (se regenera).

3. **Artefactos de despliegue e Infra**  
   - `docker-compose.yml`, Dockerfiles, Nginx conf, Prometheus/Grafana configs.  
   - **ADRs/RFCs y documentación** (`/docs`).  
   - Scripts de **migraciones Alembic**.

4. **Secretos y configuración**  
   - `.env` y **secrets** (en bóveda separada, cifrada y versionada).  
   - Llaves de firma y certificados (rotación programada).

---

## 3) Estrategia de backup

| Ítem | Tipo | Frecuencia | Retención | Ubicación | Cifrado |
|------|------|------------|-----------|----------|---------|
| MySQL (full) | Logical dump | Diario (off-peak) | 7 días | Storage primario + offsite | AES-256 en reposo |
| MySQL (binlog) | Continuo | Cada ≤ 15 min | 7 días | Storage primario + offsite | AES-256 |
| MySQL (snapshot VM/volumen) | Snapshot | Semanal | 4 semanas | Offsite (región diferente) | Proveedor |
| Redis (RDB) | Snapshot | Diario | 3 días | Primario | AES-256 |
| Infra/Configs | Tarball | Semanal | 4 semanas | Repo privado + offsite | AES-256 |
| Docs/ADRs | Tarball | Diario | 14 días | Repo + offsite | AES-256 |
| Secrets | Export Vault | Al cambiar | 6 meses | Bóveda secundaria | AES-256 + KMS |

**Notas clave**
- **PITR**: MySQL se puede restaurar **hasta cualquier punto** usando full + binlogs (≤ 15 min).  
- Offsite: almacenamiento **en otra región**/proveedor para resiliencia.  
- Todo backup se firma con **hash** (integridad) y se almacena cifrado.

---

## 4) Procedimientos de restauración (runbooks)

### 4.1 Restauración MySQL — Escenario “borrado lógico”
1. **Aislar** el servicio API (modo mantenimiento).  
2. Crear **nuevo schema** `ecommerce_restore`.  
3. Restaurar **full dump** a `ecommerce_restore`.  
4. **Reproducir binlogs** hasta el timestamp deseado (PITR).  
5. Validar **conteo de tablas**, checksums y migraciones Alembic.  
6. Apuntar la aplicación a `ecommerce_restore` (swap) y **salir de mantenimiento**.

### 4.2 Restauración MySQL — Desastre total (nodo caído)
1. Provisionar **nuevo volumen**/nodo DB.  
2. Restaurar **full** + **binlogs** desde offsite.  
3. Validar consistencia y latencias.  
4. Levantar API/Workers contra el nuevo endpoint.

### 4.3 Restauración Redis
- **No bloquea** operación. Se puede **limpiar y reiniciar**.  
- Restaurar RDB solo para **análisis** si es necesario.

### 4.4 Restauración Infra/Configs
- Clonar repo infra.  
- Desplegar **Nginx/API/Workers** con imágenes versionadas.  
- Cargar **dashboards y datasources** de Grafana desde backup.

### 4.5 Secrets
- Rotar credenciales de acceso.  
- Reinyectar **secrets** desde bóveda; nunca desde archivos en texto plano.

---

## 5) Pruebas de restauración (DR Drills)

- **Mensual**: simulacro **PITR** (full + binlogs hasta T-X minutos).  
- **Trimestral**: simulacro **desastre total** (entorno de staging nuevo desde cero).  
- **Checklist**: tiempo real de recuperación (RTO), punto alcanzado (RPO), verificación de integridad (hash), prueba de login/checkout dummy, endpoints `/healthz`.

**Criterio de éxito**
- RTO ≤ 1h, RPO ≤ 15m, sin **errores de integridad** ni fallas de migración.

---

## 6) Seguridad y acceso

- Backups **cifrados** (AES-256).  
- Acceso **principio de mínimo privilegio** (solo DevOps senior / Owner).  
- Almacenamiento **offsite** con MFA obligatorio.  
- **Rotación programada** de llaves KMS y tokens.  
- **Inventario y etiquetas**: fecha, entorno, commit/tag asociado.

---

## 7) Observabilidad y alertas

- **Alertas** si algún job de backup falla o supera SLA.  
- **Prometheus**: métricas de tamaño de backup, duración de job, último éxito.  
- **Grafana**: tablero “Backups & DR” con estado y retenciones.  
- **Logs** firmados (Loki) de cada job.

---

## 8) Dependencias y costos

- Costos de **storage offsite** y **egress** al restaurar.  
- Tiempo de **replay** de binlogs (mayor actividad = mayor duración).  
- Mantenimiento de **scripts** y **políticas de retención**.

---

## 9) Riesgos y mitigaciones

| Riesgo | Mitigación |
|-------|------------|
| Backups corruptos | Verificación de **checksums** y **test restore** programados |
| Falla de acceso a bóveda | MFA + keys de emergencia + break-glass procedure |
| Expansión de binlogs | Rotación y compresión; limpieza automatizada |
| Error humano en restore | Runbooks paso a paso + revisión por pares |

---

## 10) Decisión final

Implementar un plan de **backups full + binlogs (PITR)** para MySQL, snapshots y tarballs para infra/configs, **cifrado** en reposo y tránsito, **offsite** en región distinta, y **simulacros regulares**. Redis se considera prescindible para operación y se respalda solo para fines forenses.

**Objetivos garantizados:** **RTO ≤ 1h** y **RPO ≤ 15m**.
