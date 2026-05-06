# AIZIX API — create venv and install dependencies (Windows PowerShell)
# Run from apps/api:  .\setup.ps1
# If scripts are blocked:  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

param(
    [switch]$InstallPython
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Find-PythonExe {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return (Resolve-Path $c).Path }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notmatch "WindowsApps") {
        return $cmd.Source
    }
    return $null
}

if ($InstallPython) {
    Write-Host "Installing Python 3.12 via winget (requires winget)..."
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
}

$py = Find-PythonExe
if (-not $py) {
    Write-Host "ERROR: Python not found. Install from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "Or run:  winget install Python.Python.3.12" -ForegroundColor Yellow
    Write-Host "Then re-run:  .\setup.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Using: $py"
& $py -m venv .venv
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "ERROR: venv creation failed." -ForegroundColor Red
    exit 1
}

$pip = ".\.venv\Scripts\python.exe"
& $pip -m pip install --upgrade pip
& $pip -m pip install fastapi uvicorn python-dotenv jinja2 pydantic-settings python-multipart

Write-Host "Done. Activate with:  .\.venv\Scripts\Activate.ps1" -ForegroundColor Green
Write-Host "Then run:  python -m uvicorn app.main:app --reload --port 8000" -ForegroundColor Green
