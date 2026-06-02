# ============================================================
#  Material Learning Platform - One-Click Stop
#  Location: D:\Desktop\agent\Material\stop.ps1
#  Usage: Right-click -> Run with PowerShell
#         or: powershell -ExecutionPolicy Bypass -File .\stop.ps1
# ============================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$PROJECT_ROOT = $PSScriptRoot
Set-Location $PROJECT_ROOT

function Write-Step($msg) { Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow }

Clear-Host
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  Material Learning Platform - One-Click Stop" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta

# Step 1: Stop Backend and Frontend processes
Write-Step "[1/3] Stopping Backend (port 8000) and Frontend (port 5173) processes..."

$ports = @(8000, 5173)
$killedCount = 0

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        $procId = $conn.OwningProcess
        if ($procId) {
            try {
                $process = Get-Process -Id $procId -ErrorAction Stop
                Write-Host "  Stopping: $($process.ProcessName) (PID: $procId, Port: $port)" -ForegroundColor Yellow
                Stop-Process -Id $procId -Force
                $killedCount++
            } catch {
                Write-Warn "Cannot stop PID $procId : $($_.Exception.Message)"
            }
        }
    }
}

if ($killedCount -eq 0) {
    Write-OK "No backend/frontend processes to stop"
} else {
    Write-OK "Stopped $killedCount processes"
}

Start-Sleep -Seconds 2

# Step 2: Ask whether to stop Docker services
Write-Step "[2/3] Docker services..."

$dockerRunning = $false
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -eq 0) { $dockerRunning = $true }
} catch {}

if (-not $dockerRunning) {
    Write-OK "Docker is not running"
} else {
    $choice = Read-Host "  Stop all Docker services? (y/N) (Enter N to keep containers running)"
    if ($choice -eq "y" -or $choice -eq "Y") {
        Write-Host "  Stopping Docker services..." -ForegroundColor Yellow
        docker compose stop
        Write-OK "Docker services stopped"
    } else {
        Write-OK "Docker services kept running"
    }
}

# Step 3: Done
Write-Step "[3/3] Done"
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Stop completed" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Tips:" -ForegroundColor Yellow
Write-Host "     - Restart:  .\start.ps1" -ForegroundColor Gray
Write-Host "     - Clean Docker volumes: docker compose down -v" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to close"
