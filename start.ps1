# Expenso launcher (PowerShell)
# Idempotent: creates venv, installs deps, opens browser, starts uvicorn.

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path 'venv\Scripts\python.exe')) {
    Write-Host '[expenso] creating venv with python 3.9...'
    $hasPy = $false
    try { & py -3.9 --version *> $null; $hasPy = ($LASTEXITCODE -eq 0) } catch { $hasPy = $false }
    if ($hasPy) {
        & py -3.9 -m venv venv
    } else {
        & python -m venv venv
    }
}

if (-not (Test-Path 'venv\Scripts\python.exe')) {
    Write-Error '[expenso] failed to create venv -- is python 3.9 installed?'
    exit 1
}

Write-Host '[expenso] installing dependencies...'
& venv\Scripts\python.exe -m pip install --upgrade pip | Out-Null
& venv\Scripts\python.exe -m pip install -r requirements.txt

$ExpensoHost = '127.0.0.1'
$Port = 8000
$Url  = "http://${ExpensoHost}:${Port}/"

Write-Host "[expenso] opening $Url"
Start-Process $Url | Out-Null

Write-Host '[expenso] starting uvicorn -- Ctrl+C to stop'
& venv\Scripts\python.exe -m uvicorn app.main:app --host $ExpensoHost --port $Port
