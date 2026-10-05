$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path "$root\.venv")) {
    Write-Host "Creando entorno virtual..."
    python -m venv .venv
}

$venvPython = "$root\.venv\Scripts\python.exe"

Write-Host "Instalando dependencias..."
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r backend\requirements.txt

Write-Host "Arrancando servidor en http://localhost:8000 ..."
& $venvPython -m uvicorn backend.app.main:app --reload --port 8000
