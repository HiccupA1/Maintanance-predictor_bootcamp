<#
.SYNOPSIS
  Start the local client demo: API, frontend, sign-in stand-in and demo data.

.DESCRIPTION
  Runs everything locally against a disposable Postgres database. The demo
  database is dropped and recreated each time. See Docs/runbooks/demo.md.

.EXAMPLE
  ./tools/demo/start.ps1 -DatabaseUrl "postgresql+psycopg2://postgres:postgres@localhost:5432/demo"
#>
param(
  [Parameter(Mandatory = $true)] [string] $DatabaseUrl,
  [string] $Python = ".venv\Scripts\python.exe",
  [int] $ApiPort = 8000,
  [int] $WebPort = 4173,
  [int] $AuthPort = 54321
)
# Native tools (alembic, node) log to stderr; judge them by exit code only.
$ErrorActionPreference = "Continue"
function Invoke-Step([string] $what, [scriptblock] $cmd, [switch] $AllowFailure) {
  $out = & $cmd 2>&1 | ForEach-Object { "$_" }
  if ($LASTEXITCODE -and -not $AllowFailure) { $out | Select-Object -Last 15; throw "$what failed (exit $LASTEXITCODE)" }
  return $out
}
$root = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $root
$py = (Resolve-Path $Python).Path
$demo = Join-Path $root "reports\demo-env"
New-Item -ItemType Directory -Force $demo | Out-Null

$env:APP_ENV = "dev"
$env:DATABASE_URL = $DatabaseUrl
$env:MODEL_STORE_DIR = Join-Path $demo "models"
$env:OMP_NUM_THREADS = "1"

Write-Host "1/5 Resetting the demo schema"
Invoke-Step "downgrade" { & $py -m alembic downgrade base } -AllowFailure | Out-Null
Invoke-Step "migration" { & $py -m alembic upgrade head } | Out-Null

Write-Host "2/5 Model, users and sign-in keys"
if (-not (Test-Path "ml\artifacts\ai4i-v1\model.joblib")) {
  Invoke-Step "training" { & $py -m ml.pipelines.train_ai4i --version ai4i-v1 } | Select-Object -Last 3
}
Invoke-Step "seed" { & $py -m tools.testenv.seed $demo } | Out-Null

Write-Host "3/5 Starting the sign-in stand-in, API and frontend"
$jwks = ([System.Uri](Join-Path $demo "jwks.json")).AbsoluteUri
$env:SUPABASE_JWKS_URL = $jwks
$env:CORS_ORIGINS = "http://127.0.0.1:$WebPort,http://localhost:$WebPort"
Start-Process -FilePath $py -ArgumentList "-m tools.demo.auth_stub `"$demo`" --port $AuthPort" `
  -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput "$demo\auth.log" -RedirectStandardError "$demo\auth.err"
Start-Process -FilePath $py -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port $ApiPort --log-level warning" `
  -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput "$demo\api.log" -RedirectStandardError "$demo\api.err"

$env:VITE_API_BASE_URL = "http://127.0.0.1:$ApiPort"
$env:VITE_SUPABASE_URL = "http://localhost:$AuthPort"
$env:VITE_SUPABASE_PUBLISHABLE_KEY = "sb_publishable_demo"
Push-Location frontend
Invoke-Step "frontend build" { node ./node_modules/vite/bin/vite.js build } | Select-Object -Last 1
Start-Process -FilePath "node" -ArgumentList "./node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port $WebPort --strictPort" `
  -WorkingDirectory (Get-Location) -WindowStyle Hidden -RedirectStandardOutput "$demo\web.log" -RedirectStandardError "$demo\web.err"
Pop-Location

Write-Host "4/5 Waiting for the API"
for ($i = 0; $i -lt 30; $i++) {
  try { Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$ApiPort/v1/health" -TimeoutSec 2 | Out-Null; break } catch { Start-Sleep 1 }
}

Write-Host "5/5 Loading the demo plant"
Invoke-Step "demo data" { & $py -m tools.demo.seed_data $demo --api "http://127.0.0.1:$ApiPort" }

Write-Host ""
Write-Host "Demo running: http://127.0.0.1:$WebPort   (password demo1234)"
Write-Host "  admin@testenv.invalid | plantmanager@testenv.invalid | operator@testenv.invalid | maintenanceengineer@testenv.invalid"
Write-Host "Stop with: ./tools/demo/stop.ps1"
