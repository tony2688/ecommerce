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