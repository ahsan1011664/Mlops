# Dagshub Setup Guide - Central Hub for MLOps

## What is Dagshub?

Dagshub is a platform that integrates:
- **Git**: Code versioning (GitHub-like interface)
- **DVC**: Data versioning
- **MLflow**: Experiment tracking and model registry

All in one collaborative UI!

## Step-by-Step Setup

### Step 1: Create Dagshub Account

1. Go to: https://dagshub.com/
2. Sign up with GitHub account (recommended) or email
3. Verify your email

### Step 2: Create New Repository on Dagshub

1. Click "New Repository"
2. Repository name: `Mlops_Project` (match your GitHub repo)
3. Description: "Real-Time Weather Prediction MLOps Pipeline"
4. Visibility: Public or Private
5. Click "Create Repository"

### Step 3: Connect to Existing GitHub Repository

Since you already have a GitHub repo, you can:

**Option A: Import from GitHub**
1. On Dagshub, click "Import from GitHub"
2. Select: `asim548/Mlops_Project`
3. Dagshub will mirror your GitHub repo

**Option B: Push to Dagshub as Remote**
```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"

# Add Dagshub as additional remote
git remote add dagshub https://dagshub.com/asim548/Mlops_Project.git

# Push to Dagshub
git push dagshub main
```

### Step 4: Get Dagshub Credentials

1. On Dagshub repository page, click your profile icon
2. Go to "Settings" → "Access Tokens"
3. Click "Generate New Token"
4. Name: `mlflow-tracking`
5. Permissions: Select all
6. Copy the token (save it securely!)

### Step 5: Configure DVC Remote (Dagshub)

```powershell
# Add Dagshub as DVC remote
dvc remote add dagshub https://dagshub.com/asim548/Mlops_Project.dvc

# Set credentials
dvc remote modify dagshub --local auth basic
dvc remote modify dagshub --local user asim548
dvc remote modify dagshub --local password YOUR_DAGSHUB_TOKEN

# Set as default (optional)
dvc remote default dagshub
```

### Step 6: Configure MLflow Tracking URI

On Dagshub repository page, you'll see:

**MLflow Tracking URI**: `https://dagshub.com/asim548/Mlops_Project.mlflow`

Set this in your environment:

```powershell
# Set environment variable
$env:MLFLOW_TRACKING_URI = "https://dagshub.com/asim548/Mlops_Project.mlflow"
$env:MLFLOW_TRACKING_USERNAME = "asim548"
$env:MLFLOW_TRACKING_PASSWORD = "YOUR_DAGSHUB_TOKEN"
```

Or add to `.env` file:
```bash
MLFLOW_TRACKING_URI=https://dagshub.com/asim548/Mlops_Project.mlflow
MLFLOW_TRACKING_USERNAME=asim548
MLFLOW_TRACKING_PASSWORD=your_dagshub_token
```

### Step 7: Update Docker Compose with Dagshub Credentials

Add to `docker-compose.yml` in the `airflow-common` environment section:

```yaml
MLFLOW_TRACKING_URI: 'https://dagshub.com/asim548/Mlops_Project.mlflow'
MLFLOW_TRACKING_USERNAME: 'asim548'
MLFLOW_TRACKING_PASSWORD: 'your_dagshub_token'
```

## Dagshub UI Overview

After setup, your Dagshub repository shows:

### 1. **Code Tab**
- Git repository (mirrored from GitHub)
- Browse code, commits, branches

### 2. **Data Tab**
- DVC-tracked data files
- Data versioning history
- Download data versions

### 3. **Experiments Tab**
- MLflow experiments
- Metrics comparison
- Hyperparameter tracking
- Model artifacts

### 4. **Models Tab**
- MLflow Model Registry
- Model versions
- Production/staging models

## Using Dagshub in Your Pipeline

### In Your Training Script (train.py)

```python
import mlflow
import os

# Set Dagshub as tracking server
mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI'))

# Start experiment
with mlflow.start_run(run_name="temperature_prediction_v1"):
    # Log parameters
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_param("n_estimators", 100)
    
    # Train model
    model = train_model()
    
    # Log metrics
    mlflow.log_metric("rmse", 2.5)
    mlflow.log_metric("mae", 1.8)
    mlflow.log_metric("r2", 0.85)
    
    # Log model
    mlflow.sklearn.log_model(model, "model")
```

## Benefits of Dagshub

1. **Unified Interface**: Code, Data, and Models in one place
2. **Collaboration**: Share experiments with team
3. **Reproducibility**: Track everything needed to reproduce results
4. **Free Tier**: Generous free tier for students/small projects
5. **GitHub Integration**: Works alongside your existing GitHub workflow

## Verification Checklist

After setup, verify:

- [ ] Dagshub repository created
- [ ] GitHub repo connected/mirrored
- [ ] DVC remote configured for Dagshub
- [ ] MLflow tracking URI set
- [ ] Credentials configured
- [ ] Can access Dagshub UI

## Next Steps

Once Dagshub is configured:
1. ✅ Update training script to use Dagshub MLflow
2. ✅ Run training and log experiments
3. ✅ View experiments in Dagshub UI
4. ✅ Register models in MLflow Model Registry

## Troubleshooting

### Can't Access Dagshub
- Check internet connection
- Verify account is created and verified

### Authentication Errors
- Verify token is correct
- Check username matches Dagshub username
- Token must have correct permissions

### DVC Push to Dagshub Fails
- Verify DVC remote is configured correctly
- Check credentials are set with `--local` flag
- Try: `dvc push --remote dagshub`

### MLflow Tracking Fails
- Verify MLFLOW_TRACKING_URI is correct
- Check username and token are set
- Test connection: `mlflow experiments list`

## Alternative: Use Local MLflow (Without Dagshub)

If you prefer to start without Dagshub:

```python
# Use local MLflow tracking
mlflow.set_tracking_uri("file:./mlruns")
```

You can always migrate to Dagshub later!

