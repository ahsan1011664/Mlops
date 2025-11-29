# Phase III Testing Guide

## Step-by-Step Testing Instructions

### Prerequisites
- Python 3.10+ installed
- Docker installed and running
- Git repository set up with branches (dev, test, master)
- GitHub repository connected

---

## Test 1: FastAPI Server (Local)

### Step 1.1: Test API Server Locally

```powershell
# 1. Start the API server
python api/prediction_server.py

# 2. In another terminal, test endpoints:
# Root endpoint
curl http://localhost:8000/

# Health check (will fail if no model - that's OK)
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics
```

**Expected Results:**
- ✅ Server starts without errors
- ✅ Root endpoint returns JSON with `model_loaded: false`
- ⚠️ Health check returns 503 (expected if no model)
- ✅ Metrics endpoint returns Prometheus format

---

## Test 2: Docker Build and Run (Local)

### Step 2.1: Build Docker Image

```powershell
# Build the image
docker build -f Dockerfile.api -t lahore-temp-predictor:test .

# Check if image was created
docker images | Select-String "lahore-temp-predictor"
```

**Expected Results:**
- ✅ Image builds successfully
- ✅ Image appears in `docker images`

### Step 2.2: Run Container

```powershell
# Run container
docker run -d --name test-api -p 8001:8000 lahore-temp-predictor:test

# Wait a few seconds
Start-Sleep -Seconds 5

# Test endpoints
curl http://localhost:8001/
curl http://localhost:8001/health
curl http://localhost:8001/metrics

# Stop and remove
docker stop test-api
docker rm test-api
```

**Expected Results:**
- ✅ Container starts successfully
- ✅ Endpoints respond (health may fail if no model - that's OK)

---

## Test 3: Unit Tests

### Step 3.1: Run Unit Tests

```powershell
# Install test dependencies
pip install pytest pytest-cov httpx

# Run tests
pytest tests/ -v
```

**Expected Results:**
- ✅ All tests pass
- ✅ Test coverage reported

---

## Test 4: GitHub Actions Workflows

### Step 4.1: Test Feature → Dev Workflow

```powershell
# 1. Create a feature branch
git checkout dev
git pull origin dev
git checkout -b feature/test-ci

# 2. Make a small change
echo "# Test" >> test_file.txt
git add test_file.txt
git commit -m "Test CI workflow"

# 3. Push and create PR
git push -u origin feature/test-ci

# 4. Go to GitHub and create PR: feature/test-ci → dev
# 5. Check Actions tab - workflow should run
```

**Expected Results:**
- ✅ Workflow triggers on PR creation
- ✅ Code quality checks run
- ✅ Unit tests run
- ✅ PR shows check status

### Step 4.2: Test Dev → Test Workflow

```powershell
# 1. Merge feature branch to dev (or create PR from dev to test)
git checkout dev
git checkout -b test/test-model-comparison

# 2. Push and create PR: dev → test
git push -u origin test/test-model-comparison

# 3. Create PR on GitHub: test/test-model-comparison → test
# 4. Check Actions tab
```

**Expected Results:**
- ✅ Workflow triggers on PR creation
- ✅ Model training runs (or simulates)
- ✅ CML comparison comment posted in PR
- ✅ Merge blocked if model degraded

### Step 4.3: Test Test → Master Deployment

**Before testing, set GitHub Secrets:**
1. Go to GitHub → Settings → Secrets and variables → Actions
2. Add:
   - `DOCKER_HUB_USERNAME` - Your Docker Hub username
   - `DOCKER_HUB_TOKEN` - Your Docker Hub access token

```powershell
# 1. Merge test to master (or create PR)
git checkout test
git checkout -b master/deployment-test

# 2. Push to master
git push origin master/deployment-test:master

# 3. Check Actions tab - deployment workflow should run
```

**Expected Results:**
- ✅ Workflow triggers on push to master
- ✅ Fetches model from MLflow
- ✅ Builds Docker image
- ✅ Pushes to Docker Hub
- ✅ Verifies deployment with health check

---

## Test 5: Complete End-to-End Flow

### Step 5.1: Full Pipeline Test

1. **Create feature branch:**
   ```powershell
   git checkout dev
   git checkout -b feature/new-feature
   # Make changes
   git commit -m "Add new feature"
   git push -u origin feature/new-feature
   ```

2. **Create PR to dev:**
   - PR triggers: Code quality + Unit tests
   - ✅ Verify checks pass

3. **Merge to dev:**
   - After PR approved/merged

4. **Create PR from dev to test:**
   - PR triggers: Model retraining + CML comparison
   - ✅ Verify CML comment posted
   - ✅ Verify merge blocked if model degraded

5. **Merge to test:**
   - After PR approved

6. **Push to master:**
   - Triggers: Deployment workflow
   - ✅ Verify Docker image built
   - ✅ Verify pushed to Docker Hub
   - ✅ Verify health check passes

---

## Quick Verification Checklist

### Local Testing
- [ ] API server starts: `python api/prediction_server.py`
- [ ] Docker image builds: `docker build -f Dockerfile.api -t test .`
- [ ] Container runs: `docker run -d -p 8001:8000 test`
- [ ] Unit tests pass: `pytest tests/ -v`

### GitHub Actions
- [ ] Feature → Dev workflow runs on PR
- [ ] Dev → Test workflow runs on PR (with CML)
- [ ] Test → Master workflow runs on push (deployment)

### Deployment
- [ ] Docker image pushed to Docker Hub
- [ ] Health check passes in deployment verification
- [ ] Container runs successfully

---

## Troubleshooting

### API Server Issues
- **Model not loaded:** Expected if no model trained. API still works for testing structure.
- **Port already in use:** Change port: `uvicorn.run(app, host="0.0.0.0", port=8001)`

### Docker Issues
- **Build fails:** Check Dockerfile syntax and dependencies
- **Container won't start:** Check logs: `docker logs <container-name>`

### GitHub Actions Issues
- **Workflow not triggering:** Check branch names match workflow triggers
- **Secrets not found:** Verify secrets are set in GitHub Settings
- **Docker Hub push fails:** Check credentials in secrets

---

## Success Criteria

✅ **All local tests pass**  
✅ **All GitHub Actions workflows run successfully**  
✅ **Docker image builds and runs**  
✅ **Deployment verification passes**  
✅ **CML comparison works in PRs**  
✅ **Model deployment to Docker Hub succeeds**

---

**Last Updated:** Phase III Testing Guide

