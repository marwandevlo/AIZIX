# Start AIZIX FastAPI with reload (run from apps/api after setup.ps1)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Missing .venv — run .\setup.ps1 first." -ForegroundColor Red
    exit 1
}

$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
Write-Host "Starting uvicorn on http://127.0.0.1:8000 ..."
& $py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
