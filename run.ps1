# ==============================================================================
# Script de Inicio Rápido - ToolMaker CAM Studio
# ==============================================================================

$ErrorActionPreference = "Stop"
$ProjectDir = Get-Location

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host " Iniciando ToolMaker CAM Studio..." -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Verificar o Crear Entorno Virtual
Write-Host "
[1/3] Verificando entorno virtual de Python..." -ForegroundColor Yellow

$VenvPath = ""
if (Test-Path "\.venv") {
    $VenvPath = "\.venv"
} elseif (Test-Path "\venv") {
    $VenvPath = "\venv"
} else {
    Write-Host "  -> Entorno virtual no encontrado. Creando '.venv'..." -ForegroundColor DarkGray
    python -m venv .venv
    $VenvPath = "\.venv"
}

# Activar entorno virtual
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    . $ActivateScript
    Write-Host "  -> Entorno virtual activado ($VenvPath)." -ForegroundColor DarkGray
} else {
    Write-Host "⚠️ No se pudo encontrar el script de activación. Usando Python del sistema." -ForegroundColor Red
}

# 2. Verificar e Instalar Dependencias
Write-Host "
[2/3] Verificando dependencias..." -ForegroundColor Yellow

if (Test-Path "\requirements.txt") {
    pip install -r requirements.txt --quiet
    Write-Host "  -> Dependencias al día." -ForegroundColor DarkGray
} else {
    Write-Host "  -> 'requirements.txt' no encontrado. Saltando instalación de paquetes." -ForegroundColor DarkGray
}

# 3. Iniciar Servidor Flask y Abrir Navegador
Write-Host "
[3/3] Lanzando aplicación..." -ForegroundColor Yellow
Write-Host " Servidor local: http://127.0.0.1:5001" -ForegroundColor Green
Write-Host " Presiona Ctrl + C en esta ventana para detener el servidor.
" -ForegroundColor DarkGray

# Abrir el navegador tras 2 segundos
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://127.0.0.1:5001"
} | Out-Null

# Ejecutar Flask
python app.py
