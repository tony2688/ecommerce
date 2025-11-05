# Frontend — Base SCSS v0.9

## Build SCSS (Dart Sass 1.93.3)

Instalar dependencia de desarrollo:

- `npm install --save-dev sass@1.93.3`

Compilar `base.scss` → `base.css` (ruta servida por templates):

- `npx sass --style=expanded frontend/assets/scss/base.scss frontend/static/scss/base.css --no-source-map`

Opcional: modo watch durante desarrollo:

- `npx sass --watch frontend/assets/scss/base.scss:frontend/static/scss/base.css`

Notas:
- Usar únicamente tokens/mixins definidos; evitar colores hardcodeados fuera de `_tokens.scss`.
- Fase E v0.9: se agregan páginas públicas mínimas y pulido de navbar/footer.

## QA Visual (SCSS Lint)

Regla principal: no usar colores hex fuera de `frontend/assets/scss/_tokens.scss`.

Opción rápida (sin dependencias):

- `rg -n --glob '!frontend/assets/scss/_tokens.scss' -e '#[0-9A-Fa-f]{3,6}\b' frontend/assets/scss`
- Si no hay coincidencias, el lint básico pasa.

Opción Stylelint (recomendado, en `frontend/`):

1. Instalar dependencias:
   - `npm install --save-dev stylelint stylelint-scss stylelint-config-standard-scss stylelint-order`
2. Configuración ya incluida:
   - `frontend/.stylelintrc.json` (reglas estándar, orden alfabético, `color-no-hex: true`).
   - `frontend/.stylelintignore` con `static/**` y `assets/scss/_tokens.scss`.
3. Ejecutar scripts:
   - Lint: `npm run lint:scss`
   - Autofix: `npm run lint:scss:fix`
   - Combo QA: `npm run qa:ui`

CI: el workflow `UI Lint (SCSS)` corre en Push/PR a `main`, ejecuta `npm run lint:scss` y `npm run scss:build` desde `frontend/`.

## Fase E (v0.9) — Páginas públicas y pulido base

Entregables:
- Plantillas públicas: `frontend/templates/public/{home,about,contact}.html` extendiendo `layout/base.html`.
- SCSS: `frontend/assets/scss/components/{_hero,_footer}.scss` y `frontend/assets/scss/pages/_public.scss` importados en `base.scss`.
- Navbar accesible (`aria-label="primary"`), estados `hover/focus` con `$color-primary-hover` y activo `.is-active`.
- Footer con fondo `$color-bg-muted` y borde superior `$color-border`.

QA y pruebas manuales:
- `npm run lint:scss`
- `npm run scss:build`
- `npm run qa:ui`
- Navegar:
  - `/` → `public/home.html`
  - `/about` → `public/about.html`
  - `/contact` → `public/contact.html`
- Verificar:
  - Tipografías (Poppins/Inter/Roboto Mono) desde `layout/base.html`.
  - Hover primario coincide con `$color-primary-hover`.
  - Formulario de Contacto accesible: foco visible, labels asociadas, placeholder regional `+54 381 123-4567`.
  - Contraste AA en links/texto.

No-Go’s:
- No agregar endpoints ni lógica nueva de backend.
- No usar hex ni `!important` en nuevos SCSS; solo tokens/mixins.

## Fase F (v1.0) — Build automático SCSS + Deploy seguro

Durante el build de Docker del frontend se compila automáticamente el SCSS y se aseguran los tipos MIME correctos en Nginx.

### Build de imagen (multi-stage)

- Se usa `node:20` para compilar SCSS y luego `nginx:1.28.0` para servir.
- Comandos ejecutados en la etapa de build:
  - `npm ci && npm run scss:build`
- La imagen final copia `static/` y `index.html` a `/usr/share/nginx/html/`.
- `nginx.conf` incluye `mime.types` para servir `text/css`.

### Verificación rápida

1. `docker compose build frontend nginx`
2. `docker compose up -d`
3. `curl -I http://localhost:8080/static/scss/base.css` → `Content-Type: text/css`
4. `curl -I http://localhost:8080/` → `200 OK`

### CI/CD

- Workflow `Frontend Build SCSS` compila (`npm ci`, `npm run qa:ui`, `npm run scss:build`).
- Levanta temporalmente `nginx:1.28.0` para validar el MIME del CSS con `curl -I`.

### Definition of Done

- Dockerfile compila SCSS automáticamente.
- CI ejecuta lint + build.
- Nginx sirve `.css` como `text/css`.
- `/`, `/about`, `/contact` con estilos aplicados.

## Fase G (v1.1) — Públicas vía backend + Cache busting + Headers

Objetivo: Servir Home/About/Contact desde FastAPI + Jinja, mantener estáticos en `/static/` por Nginx, sumar cache busting y headers de seguridad.

### Rutas públicas (FastAPI + Jinja)

- Nuevas rutas en backend: `GET /`, `GET /about`, `GET /contact` → `TemplateResponse("public/<page>.html", {...})`.
- Se monta `/static` en FastAPI sólo si el directorio existe (dev/Docker), pero en producción los estáticos se sirven por Nginx.

### Cache busting CSS

- En `frontend/templates/layout/base.html` el `<link>` usa `{{ css_href }}`.
- El backend pasa `{"css_href": "/static/scss/base.css?v=<BUILD_HASH>"}` con `BUILD_HASH` desde env o timestamp.

### Headers de seguridad y caché en Nginx

- Seguridad:
  - `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`.
  - `Permissions-Policy: geolocation=(), microphone=(), camera=()`.
  - CSP mínima: `default-src 'self'; img-src 'self' data:; style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; font-src https://fonts.gstatic.com; script-src 'self'`.
- Caché estáticos:
  - `location /static/ { alias /usr/share/nginx/html/static/; expires 30d; add_header Cache-Control "public, max-age=2592000, immutable"; }`.
- Públicas vía backend:
  - `location = /`, `location = /about`, `location = /contact` → `proxy_pass` al backend.

### CI — UI Smoke

- Workflow `UI Smoke` compila SCSS y levanta:
  - Backend con `uvicorn` en `:8000`.
  - Nginx en `:8080` apuntando al backend (Actions usa `host.docker.internal`).
- Checks:
  - Home `curl -sSf http://localhost:8080/` → 200.
  - CSS `curl -I http://localhost:8080/static/scss/base.css` contiene `Content-Type: text/css`.

### Definition of Done

- `/`, `/about`, `/contact` servidos por backend (TemplateResponse).
- CSS con cache busting `?v=`.
- Nginx con MIME + headers de seguridad + caché en `/static/`.
- CI UI Smoke en verde: Home 200 + CSS `text/css`.
- README actualizado.