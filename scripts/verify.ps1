param([switch]$E2E)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) { throw "Create .venv with Python 3.11 first." }
Push-Location $projectRoot
try {
    & $pythonPath -m pytest backend/tests -m "not model"
    if ($LASTEXITCODE -ne 0) { throw "Backend tests failed." }
    & npm.cmd --prefix frontend test -- --run --pool=threads --maxWorkers=1
    if ($LASTEXITCODE -ne 0) { throw "Frontend tests failed." }
    & npm.cmd --prefix frontend run typecheck
    if ($LASTEXITCODE -ne 0) { throw "TypeScript validation failed." }
    & npm.cmd --prefix frontend run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
    if ($E2E) {
        Push-Location frontend
        try {
            & npx.cmd playwright test
            if ($LASTEXITCODE -ne 0) { throw "Browser end-to-end tests failed." }
        } finally { Pop-Location }
    }
    Write-Host "All verification checks passed."
} finally { Pop-Location }
