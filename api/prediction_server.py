"""
FastAPI Prediction Server for Lahore Temperature Prediction
"""

import os
import sys
import glob
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import time

import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Configuration
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'file:./mlruns')
MODEL_NAME = os.getenv('MODEL_NAME', 'lahore_temperature_predictor_random_forest')
MODEL_STAGE = os.getenv('MODEL_STAGE', 'Production')

# Initialize FastAPI
app = FastAPI(title="Lahore Temperature Prediction API", version="1.0.0")

# Prometheus Metrics
REQUEST_COUNT = Counter('prediction_requests_total', 'Total prediction requests', ['status'])
INFERENCE_LATENCY = Histogram('prediction_latency_seconds', 'Prediction latency')
DATA_DRIFT_DETECTIONS = Counter('data_drift_detections_total', 'Total data drift detections', ['feature'])
DRIFT_RATIO = Histogram('data_drift_ratio', 'Ratio of out-of-distribution features per request', buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

# Global model
model = None
feature_names = None
model_version = "N/A"
feature_statistics = None  # Store feature statistics for drift detection


class PredictionRequest(BaseModel):
    features: Dict[str, float] = Field(..., description="Feature values")


class PredictionResponse(BaseModel):
    prediction: float
    timestamp: str
    model_version: Optional[str] = None


def load_model():
    """Load model from MLflow"""
    global model, feature_names, model_version, feature_statistics
    
    print("Loading model from MLflow...")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    try:
        from mlflow.tracking import MlflowClient
        client = MlflowClient()
        
        # Try to get model from registry
        # First, search for registered models
        registered_models = client.search_registered_models(filter_string=f"name='{MODEL_NAME}'")
        
        if not registered_models:
            raise ValueError(f"Model {MODEL_NAME} not found in registry")
        
        # Get model versions - try Production first, then any stage
        model_versions = []
        if MODEL_STAGE and MODEL_STAGE != 'None':
            try:
                model_versions = client.get_latest_versions(MODEL_NAME, stages=[MODEL_STAGE])
            except:
                pass
        
        if not model_versions:
            try:
                model_versions = client.get_latest_versions(MODEL_NAME, stages=["None", "Staging", "Production"])
            except:
                model_versions = client.get_latest_versions(MODEL_NAME, stages=["None"])
        
        if not model_versions:
            raise ValueError(f"Model {MODEL_NAME} not found in registry")
        
        best_model = model_versions[0]
        
        # Try to load model - handle Windows path issues in containers
        # Get tracking URI base path
        tracking_uri = MLFLOW_TRACKING_URI.replace('file:', '').replace('file://', '')
        if not os.path.isabs(tracking_uri):
            tracking_uri = os.path.join(os.getcwd(), tracking_uri)
        
        # Find model artifact directory directly (avoids Windows path issues)
        # Model registry stores models in: mlruns/{experiment_id}/models/{model_id}/artifacts/
        model_pattern = os.path.join(tracking_uri, '*', 'models', '*', 'artifacts')
        model_dirs = glob.glob(model_pattern)
        
        if model_dirs:
            # Use the first found model directory (direct path works in containers)
            model_path = model_dirs[0]
            print(f"  Loading model from: {model_path}")
            model = mlflow.sklearn.load_model(model_path)
            model_version = f"{best_model.version} (Stage: {best_model.current_stage if hasattr(best_model, 'current_stage') else MODEL_STAGE})"
        else:
            # Fallback: try models:/ URI
            try:
                if MODEL_STAGE and MODEL_STAGE != 'None':
                    model_uri = f"models:/{MODEL_NAME}/{MODEL_STAGE}"
                else:
                    model_uri = f"models:/{MODEL_NAME}/{best_model.version}"
                model = mlflow.sklearn.load_model(model_uri)
                model_version = f"{best_model.version} (Stage: {best_model.current_stage if hasattr(best_model, 'current_stage') else MODEL_STAGE})"
            except Exception as e:
                raise ValueError(f"Could not load model: {e}")
        
        if hasattr(model, 'feature_names_in_'):
            feature_names = list(model.feature_names_in_)
        elif hasattr(model, 'n_features_in_'):
            feature_names = [f"feature_{i}" for i in range(model.n_features_in_)]
        
        # Load training data statistics for drift detection
        # Try to get statistics from MLflow run
        try:
            run_id = best_model.run_id
            run = client.get_run(run_id)
            # Try to load training data statistics if available
            # For now, initialize with None - will be set from training data if available
            feature_statistics = None
            print(f"  Note: Feature statistics for drift detection will be initialized from first predictions")
        except:
            feature_statistics = None
        
        print(f"✓ Model loaded successfully. Version: {model_version}. Features: {len(feature_names) if feature_names else 'unknown'}")
        
    except Exception as e:
        print(f"⚠ Warning: Could not load model: {e}")
        print("  The API will start but /predict and /health will return errors until a model is trained.")
        print("  To train a model, run: python scripts/train.py")
        model = None
        feature_names = None
        model_version = "N/A"
        feature_statistics = None


@app.on_event("startup")
async def startup():
    """Load model on startup"""
    try:
        load_model()
    except Exception as e:
        print(f"Warning: Could not load model: {e}")


@app.get("/")
async def root():
    return {
        "service": "Lahore Temperature Prediction API",
        "model_loaded": model is not None,
        "model_version": model_version
    }


@app.get("/health")
async def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model_version": model_version
    }


def detect_data_drift(features_dict: Dict[str, float]) -> tuple:
    """
    Detect data drift by checking if feature values are out-of-distribution.
    Uses simple statistical method: values outside 3 standard deviations are considered drift.
    
    Returns:
        tuple: (drift_detected: bool, drift_features: list, drift_ratio: float)
    """
    global feature_statistics
    
    if not feature_names or not feature_statistics:
        # Initialize statistics from first few predictions (simple approach)
        # In production, this should be loaded from training data
        return False, [], 0.0
    
    drift_features = []
    total_features = len(feature_names)
    
    for feature_name in feature_names:
        if feature_name not in features_dict:
            continue
            
        value = features_dict[feature_name]
        
        if feature_name in feature_statistics:
            mean = feature_statistics[feature_name].get('mean', 0)
            std = feature_statistics[feature_name].get('std', 1)
            
            # Check if value is outside 3 standard deviations
            if std > 0 and abs(value - mean) > 3 * std:
                drift_features.append(feature_name)
                DATA_DRIFT_DETECTIONS.labels(feature=feature_name).inc()
    
    drift_ratio = len(drift_features) / total_features if total_features > 0 else 0.0
    return len(drift_features) > 0, drift_features, drift_ratio


def update_feature_statistics(features_dict: Dict[str, float]):
    """Update running statistics for features (simple moving average approach)"""
    global feature_statistics
    
    if not feature_names:
        return
    
    if feature_statistics is None:
        feature_statistics = {}
        for feat in feature_names:
            feature_statistics[feat] = {'mean': 0.0, 'std': 1.0, 'count': 0, 'sum': 0.0, 'sum_sq': 0.0}
    
    # Update statistics using Welford's online algorithm
    for feat in feature_names:
        if feat not in features_dict:
            continue
            
        value = features_dict[feat]
        stats = feature_statistics[feat]
        stats['count'] += 1
        n = stats['count']
        
        # Update mean
        delta = value - stats['mean']
        stats['mean'] += delta / n
        
        # Update variance
        delta2 = value - stats['mean']
        stats['sum_sq'] += delta * delta2
        
        if n > 1:
            stats['std'] = np.sqrt(stats['sum_sq'] / (n - 1))
        else:
            stats['std'] = 1.0


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make temperature prediction"""
    start = time.time()
    
    if model is None:
        REQUEST_COUNT.labels(status='error').inc()
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Convert to DataFrame
        features_df = pd.DataFrame([request.features])
        
        # Check features
        if feature_names:
            missing = set(feature_names) - set(features_df.columns)
            if missing:
                raise HTTPException(status_code=400, detail=f"Missing features: {list(missing)}")
            features_df = features_df[feature_names]
        
        # Update feature statistics for drift detection
        update_feature_statistics(request.features)
        
        # Detect data drift
        drift_detected, drift_features, drift_ratio = detect_data_drift(request.features)
        DRIFT_RATIO.observe(drift_ratio)
        
        # Predict
        prediction = model.predict(features_df)[0]
        
        # Metrics
        latency = time.time() - start
        INFERENCE_LATENCY.observe(latency)
        REQUEST_COUNT.labels(status='success').inc()
        
        return PredictionResponse(
            prediction=float(prediction),
            timestamp=datetime.utcnow().isoformat(),
            model_version=model_version
        )
    except HTTPException:
        raise
    except Exception as e:
        REQUEST_COUNT.labels(status='error').inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics():
    """Prometheus metrics"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

