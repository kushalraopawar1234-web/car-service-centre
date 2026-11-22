# One-command local start for Windows PowerShell.
#
#   .\run.ps1            -> install deps if needed, start the app on :5000
#   .\run.ps1 -Init      -> also (re)load sql/database.sql first  [DESTRUCTIVE]
#
# If PowerShell blocks scripts, run once in this window:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

param(
    [switch]$Init
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment ..." -ForegroundColor Cyan
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
}

Write-Host "Checking dependencies ..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt

if (-not $env:DB_HOST) { $env:DB_HOST = "localhost" }
if (-not $env:DB_PORT) { $env:DB_PORT = "3306" }
if (-not $env:DB_USER) { $env:DB_USER = "root" }
if (-not $env:DB_NAME) { $env:DB_NAME = "car_service_db" }

if ($Init) {
    Write-Host "Loading sql/database.sql (this DROPS and recreates $($env:DB_NAME)) ..." -ForegroundColor Yellow
    .\.venv\Scripts\python.exe init_db.py
}

Write-Host ""
Write-Host "Starting http://127.0.0.1:5000  (Ctrl+C to stop)" -ForegroundColor Green
.\.venv\Scripts\python.exe app.py
