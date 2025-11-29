# Phase II: Experimentation and Model Management (Step 4)

## Overview

Phase II focuses on **model training** with robust **experiment tracking** using **MLflow** and **Dagshub**. This ensures all experiments, hyperparameters, metrics, and models are tracked and reproducible.

## What We're Building

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE II ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ Processed    │─────▶│  train.py    │                    │
│  │ Data         │      │  (Training   │                    │
│  │ (from ETL)   │      │   Script)    │                    │
│  └──────────────┘      └──────┬───────┘                    │
│                               │                             │
│                               │ Logs to                     │
│                               ▼                             │
│                        ┌──────────────┐                    │
│                        │   MLflow     │                    │
│                        │  Tracking    │                    │
│                        └──────┬───────┘                    │
│                               │                             │
│                               │ Syncs to                    │
│                               ▼                             │
│                        ┌──────────────┐                    │
│                        │   Dagshub    │                    │
│                        │  (Central    │                    │
│                        │   Hub)       │                    │
│                        └──────────────┘                    │
│                                                              │
│  Tracks:                                                    │
│  • Hyperparameters (n_estimators, max_depth, etc.)         │
│  • Metrics (RMSE, MAE, R²)                                  │
│  • Models (trained artifacts)                               │
│  • Feature importance                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components Created

### 1. Training Script (`scripts/train.py`)

**Purpose:** Train ML models with comprehensive MLflow tracking

**Key Functions:**

- `load_processed_data()`: Load processed data from ETL pipeline
- `prepare_features_and_target()`: Split data into features (X) and target (y)
- `split_data()`: Create train/test splits (time-series aware)
- `train_model()`: Train regression model (Random Forest, Gradient Boosting, etc.)
- `evaluate_model()`: Calculate RMSE, MAE, R² on train and test sets
- `train_and_log_experiment()`: Complete training workflow with MLflow tracking
- `run_multiple_experiments()`: Run multiple experiments for comparison

**MLflow Integration:**

```python
import mlflow

# Set tracking URI (local or Dagshub)
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("lahore_temperature_prediction")

# Start run
with mlflow.start_run(run_name="rf_100_trees"):
    # Log parameters
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 10)
    
    # Train model
    model = train_model(X_train, y_train)
    
    # Log metrics
    mlflow.log_metric("test_rmse", 2.5)
    mlflow.log_metric("test_mae", 1.8)
    mlflow.log_metric("test_r2", 0.85)
    
    # Log model
    mlflow.sklearn.log_model(model, "model")
```

### 2. Airflow DAG Integration

**New Task:** `train_model` (Task 7)

**Workflow:**

```
extract_weather_data 
  ↓
data_quality_check
  ↓
transform_data
  ↓
generate_profiling_report
  ↓
load_to_cloud_storage
  ↓
dvc_version_data
  ↓
train_model  ← NEW TASK (Phase II)
```

**What it does:**

1. Loads processed data from previous tasks
2. Trains Random Forest model
3. Logs to MLflow (hyperparameters, metrics, model)
4. Saves model locally as backup
5. Pushes results to XCom for downstream tasks

### 3. Dagshub Setup Guide

**File:** `DAGSHUB_SETUP_GUIDE.md`

**Purpose:** Step-by-step guide to configure Dagshub as central hub

**Key Steps:**

1. Create Dagshub account
2. Create/import repository
3. Get access token
4. Configure DVC remote (Dagshub)
5. Configure MLflow tracking URI (Dagshub)
6. Update Docker Compose with credentials

### 4. Standalone Test Script

**File:** `scripts/test_training_standalone.py`

**Purpose:** Test training without Airflow (for development)

**Usage:**

```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
python scripts/test_training_standalone.py
```

## Implementation Steps

### Step 1: Understand MLflow Concepts

**MLflow Components:**

1. **Tracking**: Log parameters, metrics, and models
2. **Projects**: Package code for reproducibility
3. **Models**: Standard format for packaging models
4. **Model Registry**: Manage model lifecycle (staging, production)

**Key Concepts:**

- **Experiment**: Collection of related runs (e.g., "lahore_temperature_prediction")
- **Run**: Single training execution with logged data
- **Parameters**: Inputs to model (hyperparameters)
- **Metrics**: Outputs from model (RMSE, MAE, R²)
- **Artifacts**: Files produced (model, plots, feature importance)

### Step 2: Choose MLflow Tracking Backend

**Option A: Local MLflow (Simplest)**

```python
mlflow.set_tracking_uri("file:./mlruns")
```

**Pros:**

- No setup required
- Works offline
- Fast

**Cons:**

- Not collaborative
- No web UI (need to run `mlflow ui` separately)
- Not accessible from Docker containers easily

**Option B: Dagshub (Recommended for Production)**

```python
mlflow.set_tracking_uri("https://dagshub.com/asim548/Mlops_Project.mlflow")
```

**Pros:**

- Collaborative (team can see experiments)
- Integrated with Git and DVC
- Beautiful web UI
- Free tier available

**Cons:**

- Requires internet connection
- Need to set up account and credentials

### Step 3: Set Up Dagshub (Recommended)

Follow the detailed guide in `DAGSHUB_SETUP_GUIDE.md`:

1. **Create Dagshub Account:**
   - Go to https://dagshub.com/
   - Sign up with GitHub

2. **Create Repository:**
   - Name: `Mlops_Project`
   - Import from GitHub: `asim548/Mlops_Project`

3. **Get Access Token:**
   - Settings → Access Tokens
   - Generate new token
   - Save it securely

4. **Configure Environment Variables:**

```powershell
# Set in PowerShell
$env:MLFLOW_TRACKING_URI = "https://dagshub.com/asim548/Mlops_Project.mlflow"
$env:MLFLOW_TRACKING_USERNAME = "asim548"
$env:MLFLOW_TRACKING_PASSWORD = "your_dagshub_token"
```

5. **Update Docker Compose:**

Add to `docker-compose.yml` in `airflow-common` environment:

```yaml
MLFLOW_TRACKING_URI: 'https://dagshub.com/asim548/Mlops_Project.mlflow'
MLFLOW_TRACKING_USERNAME: 'asim548'
MLFLOW_TRACKING_PASSWORD: 'your_dagshub_token'
```

### Step 4: Test Training Locally (Without Airflow)

**Prerequisites:**

- Processed data from ETL pipeline (Steps 2.1-2.3)
- Python dependencies installed

**Run Standalone Test:**

```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"

# Install dependencies
pip install scikit-learn mlflow joblib

# Run test
python scripts/test_training_standalone.py
```

**Expected Output:**

```
====================================================================
STANDALONE TRAINING TEST SUITE (PHASE II - STEP 4)
====================================================================

[OK] Found processed data in: processed_data

Running: Single Model Training...

============================================================
MODEL TRAINING WITH MLFLOW TRACKING
============================================================

Step 1: Configuring MLflow...
  Tracking URI: file:./mlruns
  Experiment: lahore_temperature_prediction

Step 2: Loading processed data...
  Loaded 41 rows, 25 columns

...

Training Metrics:
  RMSE: 1.2345
  MAE:  0.9876
  R²:   0.8765

Test Metrics:
  RMSE: 2.3456
  MAE:  1.8765
  R²:   0.7654

[OK] Model training complete!
  MLflow Run ID: abc123...
  Test RMSE: 2.3456

====================================================================
ALL TESTS PASSED!
====================================================================
```

### Step 5: View MLflow Experiments

**Option A: Local MLflow UI**

```powershell
# Start MLflow UI
mlflow ui --backend-store-uri file:./mlruns

# Open browser: http://localhost:5000
```

**Option B: Dagshub UI**

1. Go to your Dagshub repository
2. Click "Experiments" tab
3. View all logged runs, metrics, and models

### Step 6: Run Training in Airflow

**Start Airflow:**

```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
.\start_airflow_docker.ps1
```

**Trigger DAG:**

1. Open Airflow UI: http://localhost:8080
2. Find DAG: `lahore_temperature_prediction_pipeline`
3. Click "Trigger DAG"
4. Wait for all tasks to complete (including new `train_model` task)

**Check Results:**

- **Airflow UI:** Task logs show training progress
- **MLflow UI:** Experiments logged with metrics
- **Local Files:** Models saved in `models/` directory

### Step 7: Run Multiple Experiments

**Purpose:** Compare different hyperparameters to find best model

**Run from Command Line:**

```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
python scripts/train.py --multiple
```

**What it does:**

Trains 5 different models:

1. Random Forest (50 trees, depth 5)
2. Random Forest (100 trees, depth 10)
3. Random Forest (200 trees, depth 15)
4. Gradient Boosting (100 estimators, lr=0.1)
5. Ridge Regression (alpha=1.0)

**Output:**

```
====================================================================
EXPERIMENTS SUMMARY
====================================================================

1. rf_50_trees_depth5
   Test RMSE: 2.5432
   Test MAE:  1.9876
   Test R²:   0.7234

2. rf_100_trees_depth10
   Test RMSE: 2.3456
   Test MAE:  1.8765
   Test R²:   0.7654

...

====================================================================
BEST MODEL: rf_100_trees_depth10
  Test RMSE: 2.3456
  Test MAE:  1.8765
  Test R²:   0.7654
====================================================================
```

## What Gets Logged to MLflow

### Parameters (Hyperparameters)

- `model_type`: 'random_forest', 'gradient_boosting', etc.
- `n_estimators`: Number of trees/estimators
- `max_depth`: Maximum tree depth
- `learning_rate`: Learning rate (for Gradient Boosting)
- `n_features`: Number of input features
- `n_train_samples`: Training set size
- `n_test_samples`: Test set size

### Metrics (Performance)

- `train_rmse`: Root Mean Squared Error (training)
- `train_mae`: Mean Absolute Error (training)
- `train_r2`: R² Score (training)
- `test_rmse`: Root Mean Squared Error (test)
- `test_mae`: Mean Absolute Error (test)
- `test_r2`: R² Score (test)

### Artifacts (Files)

- `model/`: Trained model (MLflow format)
- `feature_importance/`: CSV with feature importance scores
- `local_model/`: Joblib backup of model

## Model Details

### Target Variable

**Prediction Goal:** Temperature 4 hours into the future

**Target Column:** `target_temp_4h`

**Created in:** `scripts/transform_data.py` (Step 2.2)

### Features Used

**Lag Features:**

- `temp_lag_1h`: Temperature 1 hour ago
- `temp_lag_2h`: Temperature 2 hours ago
- `temp_lag_3h`: Temperature 3 hours ago

**Rolling Statistics:**

- `temp_rolling_mean_3h`: 3-hour rolling mean
- `temp_rolling_std_3h`: 3-hour rolling std
- `feels_like_rolling_mean_3h`: 3-hour rolling mean of feels_like

**Time Features:**

- `hour`: Hour of day (0-23)
- `day_of_week`: Day of week (0-6)
- `hour_sin`, `hour_cos`: Cyclical encoding of hour
- `day_of_week_sin`, `day_of_week_cos`: Cyclical encoding of day

**Weather Features:**

- `temp`: Current temperature
- `feels_like`: Feels like temperature
- `pressure`: Atmospheric pressure
- `humidity`: Humidity percentage
- `wind_speed`: Wind speed
- `clouds`: Cloud coverage percentage

### Model Algorithm

**Default:** Random Forest Regressor

**Why Random Forest?**

- Handles non-linear relationships
- Robust to outliers
- Provides feature importance
- Good baseline performance

**Alternatives Supported:**

- Gradient Boosting Regressor
- Ridge Regression
- Lasso Regression

## Troubleshooting

### Issue: "No processed data found"

**Solution:**

Run ETL pipeline first:

```powershell
python scripts/test_extraction_standalone.py
```

Or trigger Airflow DAG to run Steps 2.1-2.3.

### Issue: "MLflow authentication failed"

**Solution:**

Check environment variables:

```powershell
echo $env:MLFLOW_TRACKING_URI
echo $env:MLFLOW_TRACKING_USERNAME
echo $env:MLFLOW_TRACKING_PASSWORD
```

Verify Dagshub token is correct.

### Issue: "Module 'sklearn' not found"

**Solution:**

Install scikit-learn:

```powershell
pip install scikit-learn
```

For Docker, it's already in `docker-compose.yml` `_PIP_ADDITIONAL_REQUIREMENTS`.

### Issue: "Not enough data for training"

**Solution:**

The model needs at least ~10 samples. If you have less:

1. Run extraction multiple times to collect more data
2. Or use a smaller `test_size` in `split_data()`

### Issue: "Docker containers can't access MLflow"

**Solution:**

If using local MLflow (`file:./mlruns`), Docker containers can't access host filesystem easily.

**Fix:** Use Dagshub instead, or mount `mlruns` directory in Docker Compose.

## Verification Checklist

After completing Phase II Step 4:

- [ ] `scripts/train.py` created and tested
- [ ] Standalone test script runs successfully
- [ ] MLflow tracking configured (local or Dagshub)
- [ ] Training task added to Airflow DAG
- [ ] Docker Compose updated with ML dependencies
- [ ] Can view experiments in MLflow UI or Dagshub
- [ ] Models logged with hyperparameters and metrics
- [ ] Feature importance logged
- [ ] Local model backup saved

## Next Steps

**Phase III: CI/CD (Step 5)**

1. Set up GitHub Actions
2. Implement CML for model comparison
3. Containerize model serving (Docker)
4. Deploy to production

**Phase IV: Monitoring (Step 6)**

1. Set up Prometheus metrics
2. Create Grafana dashboards
3. Monitor model drift
4. Set up alerts

## Summary

Phase II establishes **robust experiment tracking** with MLflow and Dagshub:

✅ **Automated Training:** Integrated into Airflow DAG
✅ **Experiment Tracking:** All hyperparameters, metrics, models logged
✅ **Reproducibility:** Can reproduce any experiment from logged data
✅ **Collaboration:** Team can view experiments in Dagshub
✅ **Model Registry:** Models ready for deployment

**Key Achievement:** Complete MLOps pipeline from data ingestion → training → tracking!

