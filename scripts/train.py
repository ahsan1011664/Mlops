"""
Model Training Script for Lahore Temperature Prediction (Step 4)
Trains a machine learning model to predict temperature 4 hours ahead.
Integrates with MLflow for experiment tracking and model logging.
"""

import os
import sys
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from pathlib import Path
from datetime import datetime, timezone
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Configuration
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'file:./mlruns')
MLFLOW_EXPERIMENT_NAME = os.getenv('MLFLOW_EXPERIMENT_NAME', 'lahore_temperature_prediction')
PROCESSED_DATA_DIR = PROJECT_ROOT / 'processed_data'
MODELS_DIR = PROJECT_ROOT / 'models'

# Ensure models directory exists
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def load_processed_data(data_path=None):
    """
    Load processed data for training.
    
    Args:
        data_path: Path to specific processed data file. If None, loads latest.
    
    Returns:
        DataFrame with processed data
    """
    if data_path is None:
        # Find latest processed data file
        parquet_files = list(PROCESSED_DATA_DIR.glob('*.parquet'))
        if not parquet_files:
            raise FileNotFoundError("No processed data files found")
        
        # Sort by modification time, get latest
        data_path = max(parquet_files, key=lambda p: p.stat().st_mtime)
    
    print(f"Loading data from: {data_path}")
    df = pd.read_parquet(data_path)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
    
    return df


def prepare_features_and_target(df, target_col='target_temp_4h'):
    """
    Prepare features (X) and target (y) for training.
    
    Args:
        df: Processed DataFrame
        target_col: Name of target column
    
    Returns:
        X, y, feature_names
    """
    print(f"\nPreparing features and target...")
    
    # Remove rows with NaN in target (due to shifting)
    df_clean = df.dropna(subset=[target_col]).copy()
    print(f"  Rows after removing NaN targets: {len(df_clean)}")
    
    # Define features to exclude (non-predictive or target-related)
    exclude_cols = [
        'timestamp', 'dt_unix', 'dt_txt',  # Time identifiers
        target_col, 'target_temp_3h',  # Target variables
        'weather_main', 'weather_description', 'pod',  # Categorical (need encoding)
    ]
    
    # Select numeric features
    feature_cols = [col for col in df_clean.columns if col not in exclude_cols]
    
    # Handle any remaining NaN in features (fill with forward fill then backward fill)
    X = df_clean[feature_cols].fillna(method='ffill').fillna(method='bfill')
    y = df_clean[target_col]
    
    print(f"  Features: {len(feature_cols)}")
    print(f"  Samples: {len(X)}")
    print(f"  Target: {target_col}")
    
    return X, y, feature_cols


def split_data(X, y, test_size=0.2, random_state=42):
    """
    Split data into train and test sets.
    
    Args:
        X: Features
        y: Target
        test_size: Proportion of test set
        random_state: Random seed
    
    Returns:
        X_train, X_test, y_train, y_test
    """
    print(f"\nSplitting data...")
    print(f"  Test size: {test_size*100}%")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, shuffle=False  # Don't shuffle time-series
    )
    
    print(f"  Train samples: {len(X_train)}")
    print(f"  Test samples: {len(X_test)}")
    
    return X_train, X_test, y_train, y_test


def train_model(X_train, y_train, model_type='random_forest', **hyperparams):
    """
    Train a regression model.
    
    Args:
        X_train: Training features
        y_train: Training target
        model_type: Type of model ('random_forest', 'gradient_boosting', 'ridge', 'lasso')
        **hyperparams: Model hyperparameters
    
    Returns:
        Trained model
    """
    print(f"\nTraining {model_type} model...")
    
    if model_type == 'random_forest':
        model = RandomForestRegressor(
            n_estimators=hyperparams.get('n_estimators', 100),
            max_depth=hyperparams.get('max_depth', 10),
            min_samples_split=hyperparams.get('min_samples_split', 2),
            random_state=hyperparams.get('random_state', 42),
            n_jobs=-1
        )
    elif model_type == 'gradient_boosting':
        model = GradientBoostingRegressor(
            n_estimators=hyperparams.get('n_estimators', 100),
            learning_rate=hyperparams.get('learning_rate', 0.1),
            max_depth=hyperparams.get('max_depth', 5),
            random_state=hyperparams.get('random_state', 42)
        )
    elif model_type == 'ridge':
        model = Ridge(
            alpha=hyperparams.get('alpha', 1.0),
            random_state=hyperparams.get('random_state', 42)
        )
    elif model_type == 'lasso':
        model = Lasso(
            alpha=hyperparams.get('alpha', 1.0),
            random_state=hyperparams.get('random_state', 42)
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Train model
    model.fit(X_train, y_train)
    print(f"  Model trained successfully")
    
    return model


def evaluate_model(model, X_train, y_train, X_test, y_test):
    """
    Evaluate model performance on train and test sets.
    
    Args:
        model: Trained model
        X_train, y_train: Training data
        X_test, y_test: Test data
    
    Returns:
        Dictionary of metrics
    """
    print(f"\nEvaluating model...")
    
    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Calculate metrics
    metrics = {
        # Training metrics
        'train_rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
        'train_mae': mean_absolute_error(y_train, y_train_pred),
        'train_r2': r2_score(y_train, y_train_pred),
        
        # Test metrics
        'test_rmse': np.sqrt(mean_squared_error(y_test, y_test_pred)),
        'test_mae': mean_absolute_error(y_test, y_test_pred),
        'test_r2': r2_score(y_test, y_test_pred),
    }
    
    # Print metrics
    print(f"\n  Training Metrics:")
    print(f"    RMSE: {metrics['train_rmse']:.4f}")
    print(f"    MAE:  {metrics['train_mae']:.4f}")
    print(f"    R²:   {metrics['train_r2']:.4f}")
    
    print(f"\n  Test Metrics:")
    print(f"    RMSE: {metrics['test_rmse']:.4f}")
    print(f"    MAE:  {metrics['test_mae']:.4f}")
    print(f"    R²:   {metrics['test_r2']:.4f}")
    
    return metrics


def save_model_locally(model, model_name, feature_names):
    """
    Save model locally for backup.
    
    Args:
        model: Trained model
        model_name: Name for saved model
        feature_names: List of feature names
    
    Returns:
        Path to saved model
    """
    timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    model_filename = f"{model_name}_{timestamp_str}.joblib"
    model_path = MODELS_DIR / model_filename
    
    # Save model
    joblib.dump(model, model_path)
    print(f"\n  Model saved locally: {model_path}")
    
    # Save feature names
    feature_file = MODELS_DIR / f"{model_name}_{timestamp_str}_features.json"
    with open(feature_file, 'w') as f:
        json.dump(feature_names, f, indent=2)
    print(f"  Feature names saved: {feature_file}")
    
    return str(model_path)


def train_and_log_experiment(
    data_path=None,
    model_type='random_forest',
    hyperparams=None,
    experiment_name=None,
    run_name=None
):
    """
    Complete training workflow with MLflow tracking.
    
    Args:
        data_path: Path to processed data
        model_type: Type of model to train
        hyperparams: Model hyperparameters
        experiment_name: MLflow experiment name
        run_name: MLflow run name
    
    Returns:
        Dictionary with model, metrics, and MLflow run info
    """
    if hyperparams is None:
        hyperparams = {}
    
    print(f"\n{'='*60}")
    print("MODEL TRAINING WITH MLFLOW TRACKING")
    print(f"{'='*60}\n")
    
    # Step 1: Configure MLflow
    print("Step 1: Configuring MLflow...")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    print(f"  Tracking URI: {MLFLOW_TRACKING_URI}")
    
    if experiment_name:
        mlflow.set_experiment(experiment_name)
    else:
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    print(f"  Experiment: {mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME) or MLFLOW_EXPERIMENT_NAME}")
    
    # Step 2: Load data
    print("\nStep 2: Loading processed data...")
    df = load_processed_data(data_path)
    
    # Step 3: Prepare features and target
    print("\nStep 3: Preparing features and target...")
    X, y, feature_names = prepare_features_and_target(df)
    
    # Step 4: Split data
    print("\nStep 4: Splitting data...")
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    # Step 5: Start MLflow run
    if run_name is None:
        run_name = f"{model_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    
    print(f"\nStep 5: Starting MLflow run: {run_name}")
    
    with mlflow.start_run(run_name=run_name) as run:
        run_id = run.info.run_id
        print(f"  Run ID: {run_id}")
        
        # Log parameters
        print("\nStep 6: Logging parameters...")
        mlflow.log_param("model_type", model_type)
        mlflow.log_param("n_features", len(feature_names))
        mlflow.log_param("n_train_samples", len(X_train))
        mlflow.log_param("n_test_samples", len(X_test))
        mlflow.log_param("test_size", 0.2)
        
        # Log hyperparameters
        for param_name, param_value in hyperparams.items():
            mlflow.log_param(param_name, param_value)
        
        # Step 6: Train model
        print("\nStep 7: Training model...")
        model = train_model(X_train, y_train, model_type, **hyperparams)
        
        # Step 7: Evaluate model
        print("\nStep 8: Evaluating model...")
        metrics = evaluate_model(model, X_train, y_train, X_test, y_test)
        
        # Log metrics to MLflow
        print("\nStep 9: Logging metrics to MLflow...")
        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, metric_value)
        
        # Step 8: Log model to MLflow
        print("\nStep 10: Logging model to MLflow...")
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name=f"lahore_temperature_predictor_{model_type}"
        )
        print("  Model logged to MLflow")
        
        # Step 9: Log feature importance (if available)
        if hasattr(model, 'feature_importances_'):
            print("\nStep 11: Logging feature importance...")
            feature_importance = pd.DataFrame({
                'feature': feature_names,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            # Save and log as artifact
            importance_file = MODELS_DIR / f"feature_importance_{run_id}.csv"
            feature_importance.to_csv(importance_file, index=False)
            mlflow.log_artifact(str(importance_file), "feature_importance")
            
            print(f"  Top 10 features:")
            for idx, row in feature_importance.head(10).iterrows():
                print(f"    {row['feature']}: {row['importance']:.4f}")
        
        # Step 10: Save model locally
        print("\nStep 12: Saving model locally...")
        model_path = save_model_locally(model, f"{model_type}_model", feature_names)
        
        # Log additional artifacts
        mlflow.log_artifact(str(model_path), "local_model")
        
        print(f"\n{'='*60}")
        print("TRAINING COMPLETE")
        print(f"{'='*60}")
        print(f"  Model Type: {model_type}")
        print(f"  Test RMSE: {metrics['test_rmse']:.4f}")
        print(f"  Test MAE: {metrics['test_mae']:.4f}")
        print(f"  Test R²: {metrics['test_r2']:.4f}")
        print(f"  MLflow Run ID: {run_id}")
        print(f"  Local Model: {model_path}")
        print(f"{'='*60}\n")
        
        return {
            'model': model,
            'metrics': metrics,
            'run_id': run_id,
            'model_path': model_path,
            'feature_names': feature_names
        }


def run_multiple_experiments():
    """
    Run multiple experiments with different models and hyperparameters.
    This demonstrates MLflow's experiment tracking capabilities.
    """
    print(f"\n{'='*60}")
    print("RUNNING MULTIPLE EXPERIMENTS")
    print(f"{'='*60}\n")
    
    # Define experiments to run
    experiments = [
        {
            'model_type': 'random_forest',
            'hyperparams': {'n_estimators': 50, 'max_depth': 5},
            'run_name': 'rf_50_trees_depth5'
        },
        {
            'model_type': 'random_forest',
            'hyperparams': {'n_estimators': 100, 'max_depth': 10},
            'run_name': 'rf_100_trees_depth10'
        },
        {
            'model_type': 'random_forest',
            'hyperparams': {'n_estimators': 200, 'max_depth': 15},
            'run_name': 'rf_200_trees_depth15'
        },
        {
            'model_type': 'gradient_boosting',
            'hyperparams': {'n_estimators': 100, 'learning_rate': 0.1, 'max_depth': 5},
            'run_name': 'gb_lr0.1_depth5'
        },
        {
            'model_type': 'ridge',
            'hyperparams': {'alpha': 1.0},
            'run_name': 'ridge_alpha1.0'
        },
    ]
    
    results = []
    
    for i, exp in enumerate(experiments, 1):
        print(f"\n{'='*60}")
        print(f"Experiment {i}/{len(experiments)}: {exp['run_name']}")
        print(f"{'='*60}")
        
        try:
            result = train_and_log_experiment(
                model_type=exp['model_type'],
                hyperparams=exp['hyperparams'],
                run_name=exp['run_name']
            )
            results.append(result)
        except Exception as e:
            print(f"✗ Experiment failed: {e}")
            continue
    
    # Print summary
    print(f"\n{'='*60}")
    print("EXPERIMENTS SUMMARY")
    print(f"{'='*60}\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {experiments[i-1]['run_name']}")
        print(f"   Test RMSE: {result['metrics']['test_rmse']:.4f}")
        print(f"   Test MAE:  {result['metrics']['test_mae']:.4f}")
        print(f"   Test R²:   {result['metrics']['test_r2']:.4f}")
        print(f"   Run ID:    {result['run_id']}")
        print()
    
    # Find best model
    best_result = min(results, key=lambda r: r['metrics']['test_rmse'])
    best_exp_idx = results.index(best_result)
    
    print(f"{'='*60}")
    print(f"BEST MODEL: {experiments[best_exp_idx]['run_name']}")
    print(f"  Test RMSE: {best_result['metrics']['test_rmse']:.4f}")
    print(f"  Test MAE:  {best_result['metrics']['test_mae']:.4f}")
    print(f"  Test R²:   {best_result['metrics']['test_r2']:.4f}")
    print(f"{'='*60}\n")
    
    return results, best_result


if __name__ == "__main__":
    # Run single experiment (default)
    if len(sys.argv) > 1 and sys.argv[1] == '--multiple':
        # Run multiple experiments
        results, best_result = run_multiple_experiments()
    else:
        # Run single experiment with default hyperparameters
        result = train_and_log_experiment(
            model_type='random_forest',
            hyperparams={
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 2,
                'random_state': 42
            },
            run_name=f"rf_default_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        
        print("\nTo run multiple experiments, use: python train.py --multiple")

