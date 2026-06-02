# ============================================================
#  Material Learning Platform - One-Click Startup
#  Location: D:\Desktop\agent\Material\start.ps1
#  Usage: Right-click -> Run with PowerShell
#         or: powershell -ExecutionPolicy Bypass -File .\start.ps1
# ============================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$PROJECT_ROOT = $PSScriptRoot
Set-Location $PROJECT_ROOT

function Write-Step($msg) { Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "  [X] $msg" -ForegroundColor Red }

Clear-Host
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  Material Learning Platform - One-Click Startup" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta

# Step 1: Check Docker Desktop
Write-Step "[1/5] Checking Docker Desktop..."

$dockerReady = $false
for ($i = 0; $i -lt 20; $i++) {
    try {
        $null = docker info 2>&1
        if ($LASTEXITCODE -eq 0) { $dockerReady = $true; break }
    } catch {}
    Write-Host "  Waiting for Docker Desktop to start (max 60s)..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 3
}

if (-not $dockerReady) {
    Write-Err "Docker Desktop not found or startup timed out."
    Write-Host "  Please make sure Docker Desktop is installed and running." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-OK "Docker Desktop is running"

# Step 2: Start Docker Compose services
Write-Step "[2/5] Starting Docker services (PostgreSQL/Redis/Milvus/MinIO/etcd)..."

$composeOk = $true
try {
    docker compose up -d 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $composeOk = $false }
} catch { $composeOk = $false }

if (-not $composeOk) {
    Write-Err "Failed to start Docker services. Check: docker compose logs"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "  Waiting for services to be healthy (this may take 30-60s)..." -ForegroundColor DarkGray
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    $status = docker compose ps --format json 2>$null
    $allHealthy = $true
    $hasService = $false
    if ($status) {
        $status | ForEach-Object {
            $hasService = $true
            $obj = $_ | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($obj.Health -ne "healthy" -and $obj.State -ne "running") {
                $allHealthy = $false
            }
        }
    }
    if ($hasService -and $allHealthy) { $healthy = $true; break }
    Start-Sleep -Seconds 3
}

if ($healthy) {
    Write-OK "All Docker services are running"
} else {
    Write-Warn "Some services may not be fully ready. Check: docker compose ps"
}

# Step 3: Check Python venv
Write-Step "[3/5] Checking Python venv..."

$venvPython = Join-Path $PROJECT_ROOT "backend\venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Warn "Backend venv not found, creating..."
    Push-Location (Join-Path $PROJECT_ROOT "backend")
    try {
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Failed to create venv"
            Pop-Location
            Read-Host "Press Enter to exit"
            exit 1
        }
        Write-OK "venv created"
    } catch {
        Write-Err "Failed to create venv: $($_.Exception.Message)"
        Pop-Location
        Read-Host "Press Enter to exit"
        exit 1
    }
    Pop-Location
}

$pipCheck = & $venvPython -m pip show fastapi 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Python dependencies not installed, installing (this may take 1-2 minutes)..."
    Push-Location (Join-Path $PROJECT_ROOT "backend")
    & $venvPython -m pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to install Python dependencies"
        Pop-Location
        Read-Host "Press Enter to exit"
        exit 1
    }
    Pop-Location
    Write-OK "Python dependencies installed"
} else {
    Write-OK "Python venv ready"
}

# Step 4: Start Backend
Write-Step "[4/5] Starting Backend (FastAPI on port 8000)..."

$port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($port8000) {
    Write-OK "Port 8000 already in use (Backend may be running)"
} else {
    $backendLog = Join-Path $PROJECT_ROOT "backend.log"
    $backendCmd = "cd /d `"$PROJECT_ROOT\backend`" && `"$PROJECT_ROOT\backend\venv\Scripts\python.exe`" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > `"$backendLog`" 2>&1"

    Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $backendCmd -WindowStyle Hidden

    $backendReady = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 2
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) { $backendReady = $true; break }
        } catch {}
        Write-Host "  Waiting... ($((($i+1)*2))s)" -ForegroundColor DarkGray
    }

    if ($backendReady) {
        Write-OK "Backend started (http://localhost:8000)"
    } else {
        Write-Warn "Backend may not be fully ready. Check: backend.log"
    }
}

# Step 5: Start Frontend
Write-Step "[5/5] Starting Frontend (Vite on port 5173)..."

$port5173 = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
if ($port5173) {
    Write-OK "Port 5173 already in use (Frontend may be running)"
} else {
    $frontendLog = Join-Path $PROJECT_ROOT "frontend.log"
    $frontendCmd = "cd /d `"$PROJECT_ROOT\frontend`" && npm run dev > `"$frontendLog`" 2>&1"

    Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $frontendCmd -WindowStyle Hidden

    $frontendReady = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 2
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) { $frontendReady = $true; break }
        } catch {}
        Write-Host "  Waiting... ($((($i+1)*2))s)" -ForegroundColor DarkGray
    }

    if ($frontendReady) {
        Write-OK "Frontend started (http://localhost:5173)"
    } else {
        Write-Warn "Frontend may not be fully ready. Check: frontend.log"
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  All services started successfully!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Access URLs:" -ForegroundColor Yellow
Write-Host "     Frontend:  http://localhost:5173" -ForegroundColor Cyan
Write-Host "     Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "     API Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Tips:" -ForegroundColor Yellow
Write-Host "     - Stop all:  .\stop.ps1" -ForegroundColor Gray
Write-Host "     - Backend log:  backend.log" -ForegroundColor Gray
Write-Host "     - Frontend log: frontend.log" -ForegroundColor Gray
Write-Host "     - Docker logs:  docker compose logs -f" -ForegroundColor Gray
Write-Host ""

$openBrowser = Read-Host "Open browser automatically? (Y/n)"
if ($openBrowser -ne "n" -and $openBrowser -ne "N") {
    Start-Process "http://localhost:5173"
}