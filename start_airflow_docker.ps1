# PowerShell script to start Airflow with Docker
# Run this script to test Step 2.1 DAG

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Airflow with Docker" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "[OK] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Check if this is first run
if (-not (Test-Path "logs")) {
    Write-Host "First time setup detected..." -ForegroundColor Yellow
    Write-Host "Initializing Airflow..." -ForegroundColor Yellow
    docker-compose up airflow-init
    Write-Host ""
}

# Start services
Write-Host "Starting Airflow services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Airflow is starting up..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Wait 30-60 seconds for services to start, then:" -ForegroundColor Yellow
Write-Host "1. Open browser: http://localhost:8080" -ForegroundColor Cyan
Write-Host "2. Login: admin / admin" -ForegroundColor Cyan
Write-Host "3. Find DAG: lahore_temperature_prediction_pipeline" -ForegroundColor Cyan
Write-Host "4. Toggle it ON and click play button to run" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs: docker-compose logs -f" -ForegroundColor Gray
Write-Host "To stop: docker-compose down" -ForegroundColor Gray
Write-Host ""

