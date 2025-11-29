"""
Generate Pandas Profiling Report and Log to MLflow (Dagshub)
This module creates a detailed data quality and feature summary report.
"""

import pandas as pd
import numpy as np
import mlflow
from pathlib import Path
from datetime import datetime, timezone
import os


def generate_profiling_report(df, output_dir, report_name=None):
    """
    Generate a pandas profiling report for the processed dataset.
    
    Args:
        df: Processed DataFrame
        output_dir: Directory to save the report
        report_name: Optional custom name for the report
    
    Returns:
        Path to the generated HTML report
    """
    try:
        # Try to import ydata_profiling (newer version)
        from ydata_profiling import ProfileReport
        print("Using ydata_profiling (pandas-profiling v4+)")
    except ImportError:
        try:
            # Fallback to pandas_profiling (older version)
            from pandas_profiling import ProfileReport
            print("Using pandas_profiling (legacy)")
        except ImportError:
            raise ImportError(
                "Neither ydata_profiling nor pandas_profiling is installed. "
                "Install with: pip install ydata-profiling"
            )
    
    print(f"\nGenerating profiling report for {len(df)} rows and {len(df.columns)} columns...")
    
    # Create profile report with minimal mode for faster generation
    # For production, you might want to use full mode
    profile = ProfileReport(
        df,
        title=f"Lahore Weather Data Profile - {report_name or 'Report'}",
        minimal=False,  # Set to True for faster generation
        explorative=True,
        html={
            'style': {
                'full_width': True
            }
        }
    )
    
    # Save report
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if report_name:
        report_filename = f"{report_name}.html"
    else:
        timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        report_filename = f"lahore_weather_profile_{timestamp_str}.html"
    
    report_path = output_dir / report_filename
    profile.to_file(report_path)
    
    print(f"  Profiling report saved to: {report_path}")
    
    return str(report_path), profile


def log_to_mlflow(report_path, df, mlflow_tracking_uri=None, experiment_name="lahore_temperature_prediction"):
    """
    Log the profiling report and dataset metadata to MLflow.
    
    Args:
        report_path: Path to the HTML profiling report
        df: Processed DataFrame
        mlflow_tracking_uri: MLflow tracking URI (Dagshub or local)
        experiment_name: Name of the MLflow experiment
    
    Returns:
        Run ID from MLflow
    """
    # Set MLflow tracking URI (Dagshub or local)
    if mlflow_tracking_uri:
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        print(f"MLflow tracking URI set to: {mlflow_tracking_uri}")
    else:
        # Default to local file store
        mlflow.set_tracking_uri("file:./mlruns")
        print("Using local MLflow tracking (file:./mlruns)")
    
    # Set or create experiment
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(experiment_name)
            print(f"Created new experiment: {experiment_name}")
        else:
            experiment_id = experiment.experiment_id
            print(f"Using existing experiment: {experiment_name}")
    except Exception as e:
        print(f"Warning: Could not set experiment: {e}")
        experiment_id = "0"
    
    mlflow.set_experiment(experiment_name)
    
    # Start MLflow run
    with mlflow.start_run(run_name=f"data_profiling_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}") as run:
        run_id = run.info.run_id
        
        print(f"\nMLflow Run ID: {run_id}")
        
        # Log parameters
        mlflow.log_param("data_rows", len(df))
        mlflow.log_param("data_columns", len(df.columns))
        mlflow.log_param("profiling_timestamp", datetime.now(timezone.utc).isoformat())
        
        # Log dataset statistics as metrics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if 'target_temp_4h' in df.columns:
            target_col = 'target_temp_4h'
            if df[target_col].notna().sum() > 0:
                mlflow.log_metric("target_temp_mean", df[target_col].mean())
                mlflow.log_metric("target_temp_std", df[target_col].std())
                mlflow.log_metric("target_temp_min", df[target_col].min())
                mlflow.log_metric("target_temp_max", df[target_col].max())
        
        if 'temp' in df.columns:
            mlflow.log_metric("current_temp_mean", df['temp'].mean())
            mlflow.log_metric("current_temp_std", df['temp'].std())
        
        # Log the profiling report as an artifact
        if os.path.exists(report_path):
            mlflow.log_artifact(report_path, "profiling_reports")
            print(f"  Logged profiling report as artifact")
        else:
            print(f"  Warning: Report file not found at {report_path}")
        
        # Log dataset summary statistics
        summary_stats = df.describe().to_dict()
        import json
        stats_path = Path(report_path).parent / "dataset_summary.json"
        with open(stats_path, 'w') as f:
            json.dump(summary_stats, f, indent=2, default=str)
        mlflow.log_artifact(str(stats_path), "dataset_summary")
        
        print(f"\n✓ Successfully logged to MLflow")
        print(f"  Experiment: {experiment_name}")
        print(f"  Run ID: {run_id}")
        
        return run_id


def generate_and_log_profiling(df, output_dir, mlflow_tracking_uri=None, experiment_name="lahore_temperature_prediction"):
    """
    Complete workflow: Generate profiling report and log to MLflow.
    
    Args:
        df: Processed DataFrame
        output_dir: Directory to save reports
        mlflow_tracking_uri: MLflow tracking URI (for Dagshub)
        experiment_name: MLflow experiment name
    
    Returns:
        Tuple of (report_path, run_id)
    """
    print(f"\n{'='*60}")
    print("GENERATING PANDAS PROFILING REPORT")
    print(f"{'='*60}\n")
    
    # Generate profiling report
    timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    report_name = f"lahore_weather_profile_{timestamp_str}"
    
    report_path, profile = generate_profiling_report(df, output_dir, report_name)
    
    # Log to MLflow
    print(f"\n{'='*60}")
    print("LOGGING TO MLFLOW")
    print(f"{'='*60}\n")
    
    try:
        run_id = log_to_mlflow(report_path, df, mlflow_tracking_uri, experiment_name)
        print(f"\n{'='*60}")
        print("PROFILING AND MLFLOW LOGGING COMPLETE")
        print(f"{'='*60}\n")
        return report_path, run_id
    except Exception as e:
        print(f"\n⚠ Warning: Could not log to MLflow: {e}")
        print("  Report generated successfully, but MLflow logging failed.")
        print("  This might be due to:")
        print("    - MLflow not installed")
        print("    - Dagshub credentials not configured")
        print("    - Network connectivity issues")
        return report_path, None

