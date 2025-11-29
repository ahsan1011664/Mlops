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

# Global model
model = None
feature_names = None


class PredictionRequest(BaseModel):
    features: Dict[str, float] = Field(..., description="Feature values")


class PredictionResponse(BaseModel):
    prediction: float
    timestamp: str
    model_version: Optional[str] = None


def load_model():
    """Load model from MLflow"""
    global model, feature_names, model_version
    
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
        
        print(f"✓ Model loaded successfully. Version: {model_version}. Features: {len(feature_names) if feature_names else 'unknown'}")
        
    except Exception as e:
        print(f"⚠ Warning: Could not load model: {e}")
        print("  The API will start but /predict and /health will return errors until a model is trained.")
        print("  To train a model, run: python scripts/train.py")
        model = None
        feature_names = None
        model_version = "N/A"


@app.on_event("startup")
async def startup():
    """Load model on startup"""
    try:
        load_model()
    except Exception as e:
        print(f"Warning: Could not load model: {e}")


@app.get("/")
async def root():
    return {"service": "Lahore Temperature Prediction API", "model_loaded": model is not None}


@app.get("/health")
async def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


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
        
        # Predict
        prediction = model.predict(features_df)[0]
        
        # Metrics
        latency = time.time() - start
        INFERENCE_LATENCY.observe(latency)
        REQUEST_COUNT.labels(status='success').inc()
        
        return PredictionResponse(
            prediction=float(prediction),
            timestamp=datetime.utcnow().isoformat()
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

