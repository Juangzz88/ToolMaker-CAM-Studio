# ==============================================================================
# Script de Empaquetado y Despliegue Local - ToolMaker CAM Studio
# ==============================================================================

Param(
    [string]$Version = "1.0.0",
    [switch]$CleanOnly
)

$ErrorActionPreference = "Stop"
$ProjectDir = Get-Location
$ReleaseDir = Join-Path $ProjectDir "dist"
$ZipName = "ToolMaker-CAM-Studio-v$Version.zip"
$ZipPath = Join-Path $ReleaseDir $ZipName

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host " ToolMaker CAM Studio - Script de Empaquetado v$Version" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Limpieza de Archivos Temporales y Caché
Write-Host "
[1/4] Limpiando archivos temporales y caché..." -ForegroundColor Yellow

Get-ChildItem -Path $ProjectDir -Include "__pycache__", "*.pyc", "*.pyo" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
if (Test-Path $ReleaseDir) {
    Remove-Item -Path $ReleaseDir -Recurse -Force
}

if ($CleanOnly) {
    Write-Host "✅ Limpieza completada exitosamente." -ForegroundColor Green
    exit 0
}

# 2. Verificación de Integridad de Código
Write-Host "
[2/4] Verificando sintaxis de código Python..." -ForegroundColor Yellow
try {
    python -m compileall app.py engineering/ routes/ core/ -q
    Write-Host "  -> Sintaxis Python verificada correctamente." -ForegroundColor DarkGray
} catch {
    Write-Host "❌ Error en la compilación de scripts Python. Abortando." -ForegroundColor Red
    exit 1
}

# 3. Preparación del Directorio de Distribución
Write-Host "
[3/4] Preparando estructura de archivos limpios..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $ReleaseDir | Out-Null
$TempBuildDir = Join-Path $ReleaseDir "app_build"
New-Item -ItemType Directory -Path $TempBuildDir | Out-Null

# Lista de carpetas y archivos a incluir en la versión de producción
$ItemsToInclude = @(
    "app.py",
    "engineering",
    "routes",
    "templates",
    "static",
    "core",
    "requirements.txt",
    ".env.example",
    "README.md"
)

foreach ($item in $ItemsToInclude) {
    $source = Join-Path $ProjectDir $item
    if (Test-Path $source) {
        Copy-Item -Path $source -Destination $TempBuildDir -Recurse -Force
    }
}

# 4. Generación del Archivo Comprimido (.ZIP)
Write-Host "
[4/4] Comprimiendo paquete de despliegue..." -ForegroundColor Yellow
Compress-Archive -Path "$TempBuildDir\*" -DestinationPath $ZipPath -Force
Remove-Item -Path $TempBuildDir -Recurse -Force

Write-Host "
====================================================" -ForegroundColor Green
Write-Host " ✅ Empaquetado finalizado con éxito!" -ForegroundColor Green
Write-Host " Paquete listo en: $ZipPath" -ForegroundColor White
Write-Host "====================================================" -ForegroundColor Green
