# Arranca lo necesario para estudiar y abre la web:
#   - la app UNED (http://localhost:8000): documentos, RAG, calendario…
#   - el motor de estudio (http://localhost:8011): documentos anotados, tarjetas y repaso.
# Ollama (RAG) debe estar abierto aparte. Si un servidor ya está en marcha, no se vuelve a lanzar.
#   ./scripts/iniciar-estudio.ps1            # arranca y abre el navegador
#   ./scripts/iniciar-estudio.ps1 -SinNavegador
param([switch]$SinNavegador)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$motor = Join-Path $repo 'estudio-profundo'
$logs = Join-Path $repo 'backend\data\logs'
New-Item -ItemType Directory -Force $logs | Out-Null

function Test-Puerto($puerto) {
    return [bool](Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue)
}

function Wait-Http($url, $segundos = 40) {
    for ($i = 0; $i -lt $segundos; $i++) {
        try { Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 2 | Out-Null; return $true } catch { Start-Sleep -Seconds 1 }
    }
    return $false
}

# --- App UNED (8000)
if (Test-Puerto 8000) {
    Write-Host 'App UNED: ya estaba en marcha (8000).'
} else {
    $py = Join-Path $repo '.venv\Scripts\python.exe'
    if (-not (Test-Path $py)) { throw "Falta el entorno virtual: ejecuta antes ./scripts/run.ps1 (crea .venv)." }
    Start-Process -WindowStyle Hidden -FilePath $py -WorkingDirectory $repo `
        -ArgumentList '-m', 'uvicorn', 'backend.app.main:app', '--port', '8000' `
        -RedirectStandardOutput (Join-Path $logs 'app.log') -RedirectStandardError (Join-Path $logs 'app.err.log')
    if (Wait-Http 'http://127.0.0.1:8000/api/rag/status') { Write-Host 'App UNED: arrancada (8000).' } else { Write-Warning "La app no responde; mira $logs\app.err.log" }
}

# --- Motor de estudio (8011)
if (Test-Puerto 8011) {
    Write-Host 'Motor de estudio: ya estaba en marcha (8011).'
} elseif (-not (Test-Path (Join-Path $repo '.venv\Scripts\python.exe'))) {
    Write-Warning "No encuentro el motor en $motor (¿has ejecutado antes ./scripts/run.ps1?)."
} else {
    Start-Process -WindowStyle Hidden -FilePath (Join-Path $repo '.venv\Scripts\python.exe') `
        -WorkingDirectory (Join-Path $motor 'backend') -ArgumentList '-m', 'uvicorn', 'app.main:app', '--port', '8011' `
        -RedirectStandardOutput (Join-Path $logs 'motor.log') -RedirectStandardError (Join-Path $logs 'motor.err.log')
    if (Wait-Http 'http://127.0.0.1:8011/api/sets') { Write-Host 'Motor de estudio: arrancado (8011).' } else { Write-Warning "El motor no responde; mira $logs\motor.err.log" }
}

# --- Aviso si falta Ollama (el RAG lo necesita para responder)
if (-not (Test-Puerto 11434)) { Write-Warning 'Ollama no está en marcha (11434): las preguntas al RAG no funcionarán hasta abrirlo.' }

if (-not $SinNavegador) { Start-Process 'http://localhost:8000/#/estudiar' }
