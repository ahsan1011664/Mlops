# Git Workflow Steps for Phase 3 Testing

## Current Status Check
First, check what you have:
```powershell
git status
git branch -a
```

## Step-by-Step Git Workflow

### Step 1: Commit All Phase 3 Changes
```powershell
# Add all new files
git add .

# Commit with descriptive message
git commit -m "Complete Phase 3: CI/CD implementation with Docker containerization"

# Check what branch you're on
git branch
```

### Step 2: Push to Feature Branch (Test feature→dev workflow)
```powershell
# If you're on a feature branch, push it
git push origin feature/your-branch-name

# OR create a new feature branch
git checkout -b feature/phase3-complete
git push origin feature/phase3-complete
```

**Then on GitHub:**
1. Create Pull Request: `feature/phase3-complete` → `dev`
2. **Expected:** GitHub Actions will run `ci-feature-to-dev.yml`
   - Code quality checks (Black, Flake8)
   - Unit tests
3. Wait for workflow to complete (green checkmark)
4. Get PR approval (if required by branch protection)
5. Merge PR

### Step 3: Push to Dev Branch (Test dev→test workflow)
```powershell
# Switch to dev branch
git checkout dev
git pull origin dev

# Merge your feature branch (or it's already merged via PR)
# If not merged, merge it:
git merge feature/phase3-complete

# Push to dev
git push origin dev
```

**Then on GitHub:**
1. Create Pull Request: `dev` → `test`
2. **Expected:** GitHub Actions will run `ci-dev-to-test.yml`
   - Model retraining (runs `scripts/train.py`)
   - CML comparison report posted in PR comments
   - Blocks merge if model performance degrades
3. Review CML report in PR comments
4. If model improved, get PR approval
5. Merge PR

### Step 4: Push to Test Branch (Test test→master workflow)
```powershell
# Switch to test branch
git checkout test
git pull origin test

# Merge dev branch (or it's already merged via PR)
git merge dev

# Push to test
git push origin test
```

**Then on GitHub:**
1. Create Pull Request: `test` → `master`
2. **Expected:** GitHub Actions will run `cd-test-to-master.yml`
   - Fetches best model from MLflow Registry
   - Builds Docker image
   - Pushes to Docker Hub (requires secrets)
   - Runs deployment verification
3. Check workflow logs for:
   - Docker image build success
   - Docker Hub push success
   - Health check verification
4. Get PR approval
5. Merge PR

### Step 5: Push to Master (Final Deployment)
```powershell
# Switch to master branch
git checkout master
git pull origin master

# Merge test branch (or it's already merged via PR)
git merge test

# Push to master - THIS TRIGGERS PRODUCTION DEPLOYMENT
git push origin master
```

**Expected:**
- GitHub Actions `cd-test-to-master.yml` runs automatically
- Docker image built and pushed to Docker Hub
- Deployment verification runs
- Production deployment complete

## Quick Commands Summary

```powershell
# 1. Commit changes
git add .
git commit -m "Complete Phase 3: CI/CD implementation"

# 2. Push to feature branch
git push origin feature/phase3-complete

# 3. After PR merge, update dev
git checkout dev
git pull origin dev
git push origin dev

# 4. After PR merge, update test
git checkout test
git pull origin test
git push origin test

# 5. After PR merge, update master (PRODUCTION)
git checkout master
git pull origin master
git push origin master
```

## Important: GitHub Secrets Setup

Before `test→master` workflow works, set these secrets in GitHub:
1. Go to: **Repository → Settings → Secrets and variables → Actions**
2. Add:
   - `DOCKER_HUB_USERNAME` - Your Docker Hub username
   - `DOCKER_HUB_TOKEN` - Your Docker Hub access token
   - `MLFLOW_TRACKING_URI` (optional) - If using remote MLflow

## What to Check After Each Push

### After feature→dev PR:
- ✅ Check Actions tab: `CI - Feature to Dev` workflow
- ✅ Verify code quality checks pass
- ✅ Verify unit tests pass

### After dev→test PR:
- ✅ Check Actions tab: `CI - Dev to Test` workflow
- ✅ Check PR comments for CML report
- ✅ Verify model metrics comparison

### After test→master PR:
- ✅ Check Actions tab: `CD - Test to Master` workflow
- ✅ Verify Docker image built successfully
- ✅ Verify Docker Hub push (check Docker Hub website)
- ✅ Verify deployment verification passed

### After master push:
- ✅ Check Actions tab: `CD - Test to Master` workflow
- ✅ Verify production deployment
- ✅ Check Docker Hub for new image tags

