# GPU Monitor Dashboard Native Deployment Script (Windows)
# This script deploys the application without Docker, running directly on the host system

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "GPU Monitor Dashboard Native Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python is installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed. Please install Python 3.8 or higher." -ForegroundColor Red
    Write-Host "Visit: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check if pip is installed
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✅ pip is installed: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip is not installed. Please install pip." -ForegroundColor Red
    Write-Host "Python installer usually includes pip. Reinstall Python with pip included." -ForegroundColor Yellow
    exit 1
}

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "📁 Installation directory: $ScriptDir" -ForegroundColor Yellow

# Create virtual environment
Write-Host "🔧 Creating Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create data directory
if (-not (Test-Path "data")) {
    Write-Host "📁 Creating data directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "data" -Force | Out-Null
    Write-Host "✅ Data directory created" -ForegroundColor Green
}

# Copy .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env file created" -ForegroundColor Green
}

# Create startup script
$startupScript = @"
@echo off
cd /d "$ScriptDir"
call venv\Scripts\activate.bat
streamlit run app.py --server.port 8000
"@

$startupScript | Out-File -FilePath "start-dashboard.bat" -Encoding ASCII
Write-Host "✅ Startup script created: start-dashboard.bat" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Native Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the dashboard:" -ForegroundColor White
Write-Host "   .\start-dashboard.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or manually:" -ForegroundColor White
Write-Host "   .\venv\Scripts\activate" -ForegroundColor Gray
Write-Host "   streamlit run app.py --server.port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "The dashboard will be available at:" -ForegroundColor White
Write-Host "🌐 http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run as a Windows service, you can use NSSM (Non-Sucking Service Manager):" -ForegroundColor White
Write-Host "   1. Download NSSM from https://nssm.cc/download" -ForegroundColor Gray
Write-Host "   2. Install: nssm install GPUMonitorDashboard" -ForegroundColor Gray
Write-Host "   3. Set path to: $ScriptDir\start-dashboard.bat" -ForegroundColor Gray
Write-Host "   4. Start: nssm start GPUMonitorDashboard" -ForegroundColor Gray
Write-Host ""
