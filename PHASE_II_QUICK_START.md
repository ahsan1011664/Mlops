# Phase II Quick Start Guide

## 🎯 Goal

Train a machine learning model to predict Lahore temperature 4 hours ahead, with full MLflow experiment tracking.

## 📋 Prerequisites

✅ Phase I complete (Steps 2.1-2.3: ETL pipeline)
✅ Processed data available in `processed_data/`
✅ Docker and Docker Compose installed

## 🚀 Quick Start (3 Options)

### Option A: Test Locally (Fastest)

**Best for:** Quick testing without Docker

```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"

# Install dependencies
pip install scikit-learn mlflow joblib

# Run training test
python scripts/test_training_standalone.py
```

**Expected time:** 1-2 minutes

**What you'll see:**

- Model training progress
- Metrics (RMSE, MAE, R²)
- MLflow run ID
- Model saved locally

**View results:**

```powershell
# Start MLflow UI
mlflow ui --backend-store-uri file:./mlruns

# Open: http://localhost:5000
```

---

### Option B: Run in Airflow (Recommended)

**Best for:** Full pipeline integration

```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"

# Start Airflow
.\start_airflow_docker.ps1

# Wait for services to start (2-3 minutes)
```

**Trigger DAG:**

1. Open: http://localhost:8080
2. Login: `admin` / `admin`
3. Find: `lahore_temperature_prediction_pipeline`
4. Click: "Trigger DAG" ▶️
5. Wait for all tasks to complete (green)

**Check training task:**

1. Click on DAG run
2. Find task: `train_model`
3. Click "Logs" to see training progress
4. Check metrics in logs

**Expected time:** 5-10 minutes (full pipeline)

---

### Option C: Run Multiple Experiments (Advanced)

**Best for:** Hyperparameter tuning and model comparison

```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"

# Run 5 different experiments
python scripts/train.py --multiple
```

**What it does:**

Trains 5 models with different hyperparameters:

1. Random Forest (50 trees, depth 5)
2. Random Forest (100 trees, depth 10)
3. Random Forest (200 trees, depth 15)
4. Gradient Boosting (100 estimators)
5. Ridge Regression

**Expected time:** 5-8 minutes

**View comparison:**

```powershell
mlflow ui --backend-store-uri file:./mlruns
```

Then compare metrics across all runs.

---

## 📊 View Results

### Local MLflow UI

```powershell
mlflow ui --backend-store-uri file:./mlruns
```

Open: http://localhost:5000

**What you'll see:**

- All experiment runs
- Hyperparameters
- Metrics (RMSE, MAE, R²)
- Model artifacts
- Feature importance

### Dagshub (Optional - Cloud)

**Setup required** (see `DAGSHUB_SETUP_GUIDE.md`)

1. Create Dagshub account
2. Connect repository
3. Set credentials in environment
4. All experiments sync automatically

**Benefits:**

- Collaborative (team access)
- Integrated with Git and DVC
- No need to run local MLflow UI

---

## 🔍 Understanding the Output

### Training Metrics

**RMSE (Root Mean Squared Error):**

- Measures prediction error in same units as target (°C)
- Lower is better
- Example: RMSE of 2.5 means predictions are off by ~2.5°C on average

**MAE (Mean Absolute Error):**

- Average absolute difference between prediction and actual
- Lower is better
- Example: MAE of 1.8 means average error is 1.8°C

**R² (R-squared):**

- Proportion of variance explained by model
- Range: 0 to 1 (higher is better)
- Example: R² of 0.85 means model explains 85% of variance

### Example Output

```
Training Metrics:
  RMSE: 1.2345  ← Model fits training data well
  MAE:  0.9876
  R²:   0.8765

Test Metrics:
  RMSE: 2.3456  ← Real-world performance
  MAE:  1.8765
  R²:   0.7654  ← 76.5% of variance explained
```

**Interpretation:**

- Test RMSE of 2.3°C is reasonable for 4-hour ahead prediction
- Model is not overfitting (train vs test metrics are close)
- R² of 0.76 shows good predictive power

---

## 🐛 Troubleshooting

### "No processed data found"

**Problem:** Training script can't find data

**Solution:**

```powershell
# Run ETL pipeline first
python scripts/test_extraction_standalone.py

# Or trigger Airflow DAG to run Steps 2.1-2.3
```

---

### "Module 'sklearn' not found"

**Problem:** scikit-learn not installed

**Solution:**

```powershell
pip install scikit-learn joblib
```

---

### "Not enough data for training"

**Problem:** Need more samples (minimum ~10)

**Solution:**

Run extraction multiple times to collect more data:

```powershell
python scripts/test_extraction_standalone.py
# Wait 1 hour, run again
python scripts/test_extraction_standalone.py
```

Or adjust test_size in `train.py`:

```python
X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.1)  # Use 10% for test
```

---

### Airflow task fails with "ImportError"

**Problem:** Docker container missing dependencies

**Solution:**

Rebuild containers:

```powershell
.\stop_airflow_docker.ps1
docker-compose build --no-cache
.\start_airflow_docker.ps1
```

Dependencies are in `docker-compose.yml`:

```yaml
_PIP_ADDITIONAL_REQUIREMENTS: 'requests pandas numpy pyarrow mlflow-skinny boto3 scikit-learn joblib dvc[s3]'
```

---

## ✅ Verification Checklist

After running Phase II:

- [ ] Training script runs without errors
- [ ] Metrics logged (RMSE, MAE, R²)
- [ ] Model saved locally in `models/`
- [ ] Can view experiments in MLflow UI
- [ ] Feature importance logged
- [ ] Airflow `train_model` task succeeds (if using Airflow)

---

## 📁 Files Created

After training, you'll see:

```
lahore_rps_pipeline/
├── models/
│   ├── random_forest_model_20251127_123456.joblib  ← Trained model
│   └── random_forest_model_20251127_123456_features.json  ← Feature names
├── mlruns/
│   └── 0/  ← MLflow experiment data
│       ├── meta.yaml
│       └── abc123.../  ← Run ID
│           ├── artifacts/
│           │   ├── model/  ← MLflow model format
│           │   └── feature_importance/
│           ├── params/  ← Hyperparameters
│           ├── metrics/  ← RMSE, MAE, R²
│           └── meta.yaml
```

---

## 🎓 Key Concepts

### MLflow Tracking

**Experiment:** Collection of related runs (e.g., "lahore_temperature_prediction")

**Run:** Single training execution

**Parameters:** Model inputs (hyperparameters)

**Metrics:** Model outputs (RMSE, MAE, R²)

**Artifacts:** Files (model, plots, feature importance)

### Model Registry

After training, models can be:

1. **Staged:** Ready for testing
2. **Production:** Deployed and serving predictions
3. **Archived:** Old versions kept for reference

---

## 🎯 Next Steps

### Immediate

1. ✅ Run training locally (Option A)
2. ✅ View results in MLflow UI
3. ✅ Run in Airflow (Option B)
4. ✅ Compare multiple experiments (Option C)

### Optional (Dagshub)

5. Set up Dagshub account
6. Configure credentials
7. Push experiments to Dagshub
8. Share with team

### Phase III (CI/CD)

9. Set up GitHub Actions
10. Implement CML for model comparison
11. Containerize model serving
12. Deploy to production

---

## 📚 Additional Resources

- **Detailed Guide:** `PHASE_II_STEP_4_GUIDE.md`
- **Dagshub Setup:** `DAGSHUB_SETUP_GUIDE.md`
- **Training Script:** `scripts/train.py`
- **Test Script:** `scripts/test_training_standalone.py`
- **MLflow Docs:** https://mlflow.org/docs/latest/index.html
- **Dagshub Docs:** https://dagshub.com/docs/

---

## 💡 Tips

**Tip 1: Compare Experiments**

Use MLflow UI to compare runs side-by-side:

1. Select multiple runs (checkbox)
2. Click "Compare"
3. View metrics and parameters in table/chart

**Tip 2: Feature Importance**

Check which features matter most:

1. Open run in MLflow UI
2. Go to "Artifacts" → "feature_importance"
3. Download CSV to see top features

**Tip 3: Model Versioning**

Each run gets a unique ID. To load a specific model:

```python
import mlflow

# Load model by run ID
model = mlflow.sklearn.load_model("runs:/abc123.../model")

# Or load latest production model
model = mlflow.pyfunc.load_model("models:/lahore_temperature_predictor_random_forest/Production")
```

---

## 🎉 Success Criteria

You've completed Phase II when:

✅ Model trains successfully
✅ Metrics are reasonable (RMSE < 5°C for 4-hour prediction)
✅ Experiments logged to MLflow
✅ Can reproduce training from logged data
✅ Airflow pipeline includes training task

**Congratulations!** You now have a complete MLOps pipeline from data ingestion to model training with full experiment tracking! 🚀

