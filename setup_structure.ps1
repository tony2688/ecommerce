# Script para corregir la estructura del proyecto

# 1. Crear carpetas faltantes
mkdir -Force ops\monitoring
mkdir -Force infra\nginx
mkdir -Force backend\tests\unit
mkdir -Force backend\tests\integration
mkdir -Force backend\tests\e2e
mkdir -Force docs

# 2. Crear archivos faltantes
echo "# placeholder" > infra\docker\docker-compose.yml
echo "# placeholder" > infra\docker\nginx.Dockerfile
echo "# placeholder" > infra\nginx\nginx.conf
echo "(vacío)" > ops\monitoring\README.md
echo "(vacío)" > ops\backups\README.md
echo "(vacío)" > ops\scripts\README.md
echo "# placeholder" > Makefile
echo "(vacío)" > CONTRIBUTING.md
echo "# placeholder" > backend\app\__init__.py
echo "(vacío)" > backend\alembic\README.migrations.md

# 3. Mover estructura_proyecto.txt a docs
if (Test-Path estructura_proyecto.txt) {
    Move-Item -Path estructura_proyecto.txt -Destination docs\estructura_proyecto.txt -Force
}

# 4. Crear __init__.py en todas las subcarpetas de backend/app
$appDirs = Get-ChildItem -Path backend\app -Directory
foreach ($dir in $appDirs) {
    echo "# placeholder" > "backend\app\$($dir.Name)\__init__.py"
}

# 5. Crear __init__.py en carpetas de tests
echo "# placeholder" > backend\tests\__init__.py
echo "# placeholder" > backend\tests\unit\__init__.py
echo "# placeholder" > backend\tests\integration\__init__.py
echo "# placeholder" > backend\tests\e2e\__init__.py

# 6. Crear ADRs faltantes
echo "# placeholder" > docs\adr\ADR-004-observabilidad.md
echo "# placeholder" > docs\adr\ADR-005-ci-cd.md
echo "# placeholder" > docs\adr\ADR-006-drp-backups.md
echo "# placeholder" > docs\adr\ADR-007-seguridad.md
echo "# placeholder" > docs\adr\ADR-008-testing.md
echo "# placeholder" > docs\adr\ADR-009-escalabilidad.md
echo "# placeholder" > docs\adr\ADR-010-governance.md

# 7. Crear RFCs faltantes
echo "# placeholder" > docs\rfc\RFC-shipping.md
echo "# placeholder" > docs\rfc\RFC-notifications.md
echo "# placeholder" > docs\rfc\RFC-reporting.md

# 8. Crear README.md en backend si no existe
if (-not (Test-Path backend\README.md)) {
    echo "# placeholder" > backend\README.md
}

# 9. Crear README.md en infra si no existe
if (-not (Test-Path infra\README.md)) {
    echo "# placeholder" > infra\README.md
}

Write-Host "Estructura del proyecto corregida exitosamente."