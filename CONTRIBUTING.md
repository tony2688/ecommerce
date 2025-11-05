(vacío)
# Guía de Contribución

- Rama por defecto: `main`.
- No se permiten commits directos a `main`; usar Pull Requests.
- Los PRs deben pasar CI (lint, build, tests) antes de merge.
- Nombrar ramas: `feature/<tema>` o `fix/<issue>`.
- Mantener documentación y changelog actualizados al cerrar PRs.

## Flujo recomendado

1) Crear rama desde `main`.
2) Implementar cambios y actualizar docs/tests.
3) Abrir PR hacia `main`.
4) Verificar que el workflow "UI Lint (SCSS)" y demás CI estén en verde.
5) Merge vía PR una vez aprobado.