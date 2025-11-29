# PowerShell script to stop Airflow Docker services

Write-Host "Stopping Airflow services..." -ForegroundColor Yellow
docker-compose down
Write-Host "[OK] Airflow stopped" -ForegroundColor Green

