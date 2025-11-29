# Phase 3 Implementation Guide

## ✅ Current Status
- ✅ Model trained and registered in MLflow
- ✅ API server working with model loaded
- ✅ All Phase 3 files created

## Phase 3 Components Overview

### 1. **FastAPI Prediction Server** ✅
- Location: `api/prediction_server.py`
- Status: Working (model loaded)
- Endpoints:
  - `GET /` - Service info
  - `GET /health` - Health check
  - `POST /predict` - Make predictions
  - `GET /metrics` - Prometheus metrics

### 2. **Docker Containerization** ✅
- Dockerfile: `Dockerfile.api`
- Ready to build and deploy

### 3. **GitHub Actions CI/CD** ✅
- `feature → dev`: Code quality + unit tests
- `dev → test`: Model retraining + CML comparison
- `test → master`: Docker build + deployment

## Implementation Steps

### Step 1: Test API Locally (DONE ✅)
```powershell
# Start API
uvicorn api.prediction_server:app --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
```

### Step 2: Test Docker Build
```powershell
# Build Docker image
docker build -f Dockerfile.api -t lahore-temp-predictor:test .

# Run container
docker run -d --name test-api -p 8001:8000 \
  -e MLFLOW_TRACKING_URI=file:./mlruns \
  lahore-temp-predictor:test

# Test
curl http://localhost:8001/health

# Cleanup
docker stop test-api
docker rm test-api
```

### Step 3: Set Up GitHub Secrets
Go to: `Settings → Secrets and variables → Actions`

Add these secrets:
- `DOCKER_HUB_USERNAME` - Your Docker Hub username
- `DOCKER_HUB_TOKEN` - Your Docker Hub access token
- `MLFLOW_TRACKING_URI` (optional) - If using remote MLflow

### Step 4: Test GitHub Actions Workflows

#### 4.1 Test `feature → dev` Workflow
```powershell
# Create feature branch
git checkout -b feature/test-ci
git add .
git commit -m "Test CI workflow"
git push origin feature/test-ci

# Create PR to dev branch on GitHub
# Workflow will run automatically
```

#### 4.2 Test `dev → test` Workflow
```powershell
# Merge feature to dev (after PR approval)
git checkout dev
git merge feature/test-ci
git push origin dev

# Create PR from dev to test
# Workflow will:
# - Retrain model
# - Compare with production model
# - Post CML report in PR comments
```

#### 4.3 Test `test → master` Workflow
```powershell
# Merge test to master (after PR approval)
git checkout master
git merge test
git push origin master

# Workflow will:
# - Fetch best model from MLflow
# - Build Docker image
# - Push to Docker Hub
# - Verify deployment
```

### Step 5: Transition Model to Production Stage
```powershell
# Register model as Production
python -c "
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri('file:./mlruns')
client = MlflowClient()

model_name = 'lahore_temperature_predictor_random_forest'
versions = client.get_latest_versions(model_name, stages=['None'])

if versions:
    version = versions[0].version
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage='Production'
    )
    print(f'Model version {version} transitioned to Production')
"
```

### Step 6: Verify Complete Pipeline

1. **Local Testing** ✅
   - API works
   - Model loads
   - Health check passes

2. **Docker Testing**
   - Build image
   - Run container
   - Test endpoints

3. **CI/CD Testing**
   - Push to GitHub
   - Watch workflows run
   - Verify deployments

## Quick Test Commands

```powershell
# 1. Check model in MLflow
python -c "import mlflow; from mlflow.tracking import MlflowClient; mlflow.set_tracking_uri('file:./mlruns'); client = MlflowClient(); models = client.search_registered_models(); print(f'Models: {len(models)}')"

# 2. Test API
uvicorn api.prediction_server:app --port 8000

# 3. Test Docker
docker build -f Dockerfile.api -t test-api .
docker run -p 8001:8000 test-api

# 4. Run unit tests
pytest tests/ -v
```

## Next: Phase 4 (Monitoring)
After Phase 3 is complete, implement:
- Prometheus metrics collection
- Grafana dashboards
- Alerting rules

