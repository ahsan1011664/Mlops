# Complete Phase 3 Testing Script
# Tests all Phase 3 components with trained model

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Phase 3 Complete Testing" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify Model Exists
Write-Host "Step 1: Verifying model in MLflow..." -ForegroundColor Green
python -c "import mlflow; from mlflow.tracking import MlflowClient; mlflow.set_tracking_uri('file:./mlruns'); client = MlflowClient(); models = client.search_registered_models(); print(f'Found {len(models)} registered models')"
Write-Host ""

# Step 2: Test API Server
Write-Host "Step 2: Testing API Server..." -ForegroundColor Green
Write-Host "Starting API server in background..." -ForegroundColor Yellow
Start-Process python -ArgumentList "api/prediction_server.py" -WindowStyle Hidden
Start-Sleep -Seconds 8

Write-Host "Testing endpoints..." -ForegroundColor Yellow

# Test root
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing
    $json = $response.Content | ConvertFrom-Json
    Write-Host "✓ Root endpoint: Model loaded = $($json.model_loaded)" -ForegroundColor Green
} catch {
    Write-Host "✗ Root endpoint failed" -ForegroundColor Red
}

# Test health
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    Write-Host "✓ Health check: PASSED" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 503) {
        Write-Host "⚠ Health check: 503 (Model not loaded)" -ForegroundColor Yellow
    }
}

# Test metrics
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing
    Write-Host "✓ Metrics endpoint: Working" -ForegroundColor Green
} catch {
    Write-Host "✗ Metrics failed" -ForegroundColor Red
}

Write-Host ""

# Step 3: Test Docker Build
Write-Host "Step 3: Testing Docker Build..." -ForegroundColor Green
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -f Dockerfile.api -t lahore-temp-predictor:phase3-test . 2>&1 | Select-String -Pattern "Successfully|ERROR" | ForEach-Object { Write-Host $_ }

Write-Host ""

# Step 4: Test Docker Container
Write-Host "Step 4: Testing Docker Container..." -ForegroundColor Green
docker run -d --name phase3-test -p 8002:8000 -e MLFLOW_TRACKING_URI=file:./mlruns lahore-temp-predictor:phase3-test
Start-Sleep -Seconds 10

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8002/" -UseBasicParsing
    $json = $response.Content | ConvertFrom-Json
    Write-Host "✓ Container running: Model loaded = $($json.model_loaded)" -ForegroundColor Green
} catch {
    Write-Host "✗ Container test failed" -ForegroundColor Red
}

# Cleanup
docker stop phase3-test 2>$null
docker rm phase3-test 2>$null

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Phase 3 Testing Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Push code to GitHub"
Write-Host "2. Test GitHub Actions workflows"
Write-Host "3. Set Docker Hub secrets for deployment"

