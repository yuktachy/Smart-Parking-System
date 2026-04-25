$pythonPath = Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"

if (Test-Path $pythonPath) {
    & $pythonPath -m uvicorn server:app --host 0.0.0.0 --port 8001
    exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.11 -m uvicorn server:app --host 0.0.0.0 --port 8001
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python -m uvicorn server:app --host 0.0.0.0 --port 8001
    exit $LASTEXITCODE
}

Write-Error "Python 3.11 was not found. Install Python 3.11 and backend dependencies first, then rerun .\start_backend.ps1."
exit 1
