$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$modelPath = Join-Path $projectRoot "models\best.pt"
$frontendPath = Join-Path $projectRoot "frontend"

if (-not (Test-Path -LiteralPath $pythonPath)) { throw "Python environment missing. Run: uv venv --python 3.11 .venv; uv pip install --python .venv\Scripts\python.exe -e '.\backend[test]'" }
if (-not (Test-Path -LiteralPath $modelPath)) { throw "Model missing: models\best.pt" }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "Node.js/npm is required." }
if (-not (Test-Path -LiteralPath (Join-Path $frontendPath "node_modules"))) { throw "Frontend packages missing. Run: npm --prefix frontend install" }

$backend = Start-Process -FilePath $pythonPath -ArgumentList "-m", "uvicorn", "backend.app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8010" -WorkingDirectory $projectRoot -PassThru -WindowStyle Hidden
$frontend = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev", "--", "--host", "127.0.0.1" -WorkingDirectory $frontendPath -PassThru -WindowStyle Hidden
Write-Host "RoadSight is starting..."
Write-Host "Website: http://127.0.0.1:5173"
Write-Host "API docs: http://127.0.0.1:8010/docs"
Write-Host "Press Ctrl+C to stop both services."
try { Wait-Process -Id $backend.Id } finally {
    foreach ($process in @($backend, $frontend)) { if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force } }
}
