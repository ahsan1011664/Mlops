"""
Airflow DAG for Lahore Temperature Prediction Pipeline
This DAG handles the complete ETL and model retraining lifecycle for predicting
Lahore's temperature 4 hours into the future using OpenWeather API data.
"""

import os
import sys
import requests
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException

# Add project root to path for imports
# In Docker, DAGs are in /opt/airflow/dags, so parent is /opt/airflow
# In local, DAGs are in dags/, so parent is project root
if Path('/opt/airflow').exists():
    # Running in Docker
    PROJECT_ROOT = Path('/opt/airflow')
else:
    # Running locally
    PROJECT_ROOT = Path(__file__).parent.parent

sys.path.append(str(PROJECT_ROOT))

# Import transformation, profiling, and loading modules
sys.path.append(str(PROJECT_ROOT / 'scripts'))
try:
    from transform_data import transform_weather_data
    from generate_profiling_report import generate_and_log_profiling
    from load_to_cloud_storage import upload_processed_data
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    # Define stub functions to prevent DAG from failing on import
    def transform_weather_data(*args, **kwargs):
        raise ImportError("transform_data module not available")
    def generate_and_log_profiling(*args, **kwargs):
        raise ImportError("generate_profiling_report module not available")
    def upload_processed_data(*args, **kwargs):
        raise ImportError("load_to_cloud_storage module not available")
    
    def load_to_cloud_storage(*args, **kwargs):
        raise ImportError("load_to_cloud_storage module not available")

# Configuration
API_KEY = 'f1f8d5f1208905c5a795ba04a171acdf'
CITY = 'Lahore'
COUNTRY_CODE = 'PK'
RAW_DATA_DIR = PROJECT_ROOT / 'raw_data'
PROCESSED_DATA_DIR = PROJECT_ROOT / 'processed_data'
REPORTS_DIR = PROJECT_ROOT / 'reports'
OPENWEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5'

# MLflow/Dagshub Configuration
# TODO: Set your Dagshub MLflow tracking URI
# Format: https://dagshub.com/<username>/<repo-name>.mlflow
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', None)  # Set via environment variable
MLFLOW_EXPERIMENT_NAME = "lahore_temperature_prediction"

# Cloud Storage Configuration (Step 2.3)
# For MinIO (local testing): Use endpoint_url='http://localhost:9000'
# For AWS S3: Leave endpoint_url as None
# For Azure Blob: Use appropriate endpoint
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'lahore-weather-data')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL', None)  # None for AWS S3, 'http://localhost:9000' for MinIO
S3_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
S3_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY') or os.getenv('MINIO_SECRET_KEY', 'minioadmin')
S3_PREFIX = 'processed_data'  # Prefix for uploaded files

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def fetch_weather_data(**context):
    """
    Extraction Task (2.1): Fetch latest weather data from OpenWeather API for Lahore.
    Saves raw data immediately with collection timestamp.
    """
    try:
        # Use forecast endpoint to get hourly data (5-day forecast with 3-hour intervals)
        # For more granular hourly data, we can use the One Call API 3.0 (requires subscription)
        # Using forecast endpoint which provides 3-hourly forecasts
        url = f'{OPENWEATHER_BASE_URL}/forecast'
        params = {
            'q': f'{CITY},{COUNTRY_CODE}',
            'appid': API_KEY,
            'units': 'metric'  # Temperature in Celsius
        }
        
        print(f"Fetching weather data for {CITY} from OpenWeather API...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Validate response structure
        if 'list' not in data or 'city' not in data:
            raise AirflowException(f"Invalid API response structure: {list(data.keys())}")
        
        # Create timestamp for this extraction
        collection_time = datetime.now(timezone.utc)
        timestamp_str = collection_time.strftime('%Y%m%d_%H%M%S')
        
        # Add metadata to the data
        data['_metadata'] = {
            'collection_time_utc': collection_time.isoformat(),
            'city': CITY,
            'country_code': COUNTRY_CODE,
            'api_endpoint': url,
            'total_forecasts': len(data.get('list', []))
        }
        
        # Save raw data with timestamp
        filename = f'lahore_weather_raw_{timestamp_str}.json'
        filepath = RAW_DATA_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Successfully fetched and saved raw data to: {filepath}")
        print(f"  Total forecast entries: {len(data.get('list', []))}")
        
        # Push filepath to XCom for next task
        context['ti'].xcom_push(key='raw_data_path', value=str(filepath))
        context['ti'].xcom_push(key='collection_time', value=timestamp_str)
        
        return str(filepath)
        
    except requests.exceptions.RequestException as e:
        raise AirflowException(f"Failed to fetch data from OpenWeather API: {str(e)}")
    except Exception as e:
        raise AirflowException(f"Unexpected error during data extraction: {str(e)}")


def data_quality_check(**context):
    """
    Mandatory Quality Gate: Strict data quality validation.
    Checks for:
    - >1% null values in key columns (temperature)
    - Schema validation
    - Data completeness
    Fails the DAG if quality check fails.
    """
    try:
        # Pull filepath from previous task
        raw_data_path = context['ti'].xcom_pull(task_ids='extract_weather_data', key='raw_data_path')
        
        if not raw_data_path or not os.path.exists(raw_data_path):
            raise AirflowException("Quality check failed: Raw data file not found or path is invalid")
        
        print(f"Running data quality check on: {raw_data_path}")
        
        # Load the raw JSON data
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate top-level structure
        required_keys = ['list', 'city']
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise AirflowException(f"Quality check failed: Missing required keys in response: {missing_keys}")
        
        # Convert to DataFrame for easier analysis
        forecast_list = data['list']
        if not forecast_list or len(forecast_list) == 0:
            raise AirflowException("Quality check failed: No forecast data in response")
        
        # Extract main weather data (temperature, pressure, humidity, etc.)
        df = pd.DataFrame(forecast_list)
        
        # Expand nested 'main' dictionary which contains temperature data
        if 'main' not in df.columns:
            raise AirflowException("Quality check failed: 'main' key missing from forecast data")
        
        df_main = pd.json_normalize(df['main'])
        
        # Key columns to check (temperature is primary)
        key_columns = {
            'temp': 'Temperature',
            'feels_like': 'Feels Like Temperature',
            'pressure': 'Pressure',
            'humidity': 'Humidity'
        }
        
        quality_report = []
        quality_passed = True
        
        print("\n" + "="*60)
        print("DATA QUALITY CHECK REPORT")
        print("="*60)
        
        for col, display_name in key_columns.items():
            if col not in df_main.columns:
                print(f"⚠ WARNING: Column '{col}' ({display_name}) not found in data")
                continue
            
            # Calculate null percentage
            null_count = df_main[col].isnull().sum()
            total_count = len(df_main[col])
            null_percentage = (null_count / total_count) * 100 if total_count > 0 else 100
            
            # Check if null percentage exceeds 1% threshold
            if null_percentage > 1.0:
                quality_passed = False
                error_msg = (
                    f"❌ QUALITY CHECK FAILED: {display_name} ({col}) has "
                    f"{null_percentage:.2f}% null values (threshold: 1.0%)\n"
                    f"   Null count: {null_count}/{total_count}"
                )
                print(error_msg)
                quality_report.append(error_msg)
            else:
                success_msg = (
                    f"✓ PASS: {display_name} ({col}) - "
                    f"{null_percentage:.2f}% null ({null_count}/{total_count} null)"
                )
                print(success_msg)
                quality_report.append(success_msg)
            
            # Additional validation: Check for reasonable value ranges
            if col == 'temp' and not df_main[col].isnull().all():
                min_temp = df_main[col].min()
                max_temp = df_main[col].max()
                # Lahore temperature range check (reasonable: -10°C to 50°C)
                if min_temp < -10 or max_temp > 50:
                    print(f"⚠ WARNING: Temperature values outside expected range: {min_temp:.1f}°C to {max_temp:.1f}°C")
        
        # Schema validation: Check for required fields
        required_fields = ['dt', 'main', 'weather']
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            quality_passed = False
            error_msg = f"❌ QUALITY CHECK FAILED: Missing required fields: {missing_fields}"
            print(error_msg)
            quality_report.append(error_msg)
        
        # Data completeness check: Ensure we have sufficient data points
        min_required_forecasts = 5  # At least 5 forecast points (15 hours of data)
        if len(forecast_list) < min_required_forecasts:
            quality_passed = False
            error_msg = (
                f"❌ QUALITY CHECK FAILED: Insufficient forecast data points. "
                f"Found: {len(forecast_list)}, Required: {min_required_forecasts}"
            )
            print(error_msg)
            quality_report.append(error_msg)
        
        print("="*60)
        
        # Final decision
        if not quality_passed:
            print("\n❌ DATA QUALITY CHECK FAILED - DAG WILL STOP")
            print("\nQuality Report Summary:")
            for report_line in quality_report:
                print(f"  {report_line}")
            raise AirflowException("Data quality check failed. See logs above for details.")
        else:
            print("\n✓ DATA QUALITY CHECK PASSED - Proceeding to next step")
            print(f"  Total forecast entries validated: {len(forecast_list)}")
            print(f"  Data collection time: {context['ti'].xcom_pull(task_ids='extract_weather_data', key='collection_time')}")
        
        # Push quality check results to XCom
        context['ti'].xcom_push(key='quality_check_passed', value=True)
        context['ti'].xcom_push(key='forecast_count', value=len(forecast_list))
        
        return True
        
    except AirflowException:
        raise  # Re-raise Airflow exceptions as-is
    except Exception as e:
        raise AirflowException(f"Unexpected error during quality check: {str(e)}")


def transform_and_feature_engineering(**context):
    """
    Transformation Task (2.2): Clean data and perform feature engineering.
    Creates time-series features for 4-hour ahead temperature prediction.
    """
    try:
        # Pull filepath from previous task
        raw_data_path = context['ti'].xcom_pull(task_ids='extract_weather_data', key='raw_data_path')
        
        if not raw_data_path or not os.path.exists(raw_data_path):
            raise AirflowException("Transformation failed: Raw data file not found")
        
        print(f"Starting transformation on: {raw_data_path}")
        
        # Perform transformation and feature engineering
        processed_data_path, df_processed = transform_weather_data(
            raw_data_path=raw_data_path,
            processed_data_dir=PROCESSED_DATA_DIR
        )
        
        # Push processed data path to XCom
        context['ti'].xcom_push(key='processed_data_path', value=processed_data_path)
        context['ti'].xcom_push(key='processed_data_shape', value=f"{df_processed.shape[0]}x{df_processed.shape[1]}")
        
        print(f"✓ Transformation complete. Processed data saved to: {processed_data_path}")
        
        return processed_data_path
        
    except Exception as e:
        raise AirflowException(f"Transformation failed: {str(e)}")


def generate_profiling_report_task(**context):
    """
    Documentation Artifact (2.2): Generate pandas profiling report and log to MLflow.
    Creates a detailed data quality and feature summary report.
    """
    try:
        # Pull processed data path from previous task
        processed_data_path = context['ti'].xcom_pull(task_ids='transform_data', key='processed_data_path')
        
        if not processed_data_path or not os.path.exists(processed_data_path):
            raise AirflowException("Profiling failed: Processed data file not found")
        
        print(f"Loading processed data from: {processed_data_path}")
        
        # Load processed data
        df = pd.read_parquet(processed_data_path)
        print(f"  Loaded DataFrame: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # Generate profiling report and log to MLflow
        report_path, run_id = generate_and_log_profiling(
            df=df,
            output_dir=REPORTS_DIR,
            mlflow_tracking_uri=MLFLOW_TRACKING_URI,
            experiment_name=MLFLOW_EXPERIMENT_NAME
        )
        
        # Push report path to XCom
        context['ti'].xcom_push(key='profiling_report_path', value=report_path)
        if run_id:
            context['ti'].xcom_push(key='mlflow_run_id', value=run_id)
        
        print(f"✓ Profiling report generated and logged to MLflow")
        print(f"  Report: {report_path}")
        if run_id:
            print(f"  MLflow Run ID: {run_id}")
        
        return report_path
        
    except ImportError as e:
        # If pandas profiling is not installed, log a warning but don't fail
        print(f"⚠ Warning: Pandas profiling not available: {e}")
        print("  Install with: pip install ydata-profiling")
        print("  Skipping profiling report generation...")
        return None
    except Exception as e:
        # Log error but don't fail the DAG (profiling is documentation, not critical)
        print(f"⚠ Warning: Profiling report generation failed: {e}")
        print("  Continuing pipeline execution...")
        return None


def load_to_cloud_storage(**context):
    """
    Data Loading Task (2.3): Upload processed dataset to cloud storage.
    Supports MinIO (local), AWS S3, or S3-compatible storage.
    """
    try:
        # Pull processed data path from previous task
        processed_data_path = context['ti'].xcom_pull(task_ids='transform_data', key='processed_data_path')
        
        if not processed_data_path or not os.path.exists(processed_data_path):
            raise AirflowException("Loading failed: Processed data file not found")
        
        print(f"Loading processed data to cloud storage: {processed_data_path}")
        
        # Upload to cloud storage
        upload_result = upload_processed_data(
            processed_data_path=processed_data_path,
            bucket_name=S3_BUCKET_NAME,
            s3_prefix=S3_PREFIX,
            endpoint_url=S3_ENDPOINT_URL,
            access_key=S3_ACCESS_KEY,
            secret_key=S3_SECRET_KEY
        )
        
        # Push upload information to XCom
        context['ti'].xcom_push(key='s3_url', value=upload_result['s3_url'])
        context['ti'].xcom_push(key='s3_bucket', value=upload_result['bucket'])
        context['ti'].xcom_push(key='s3_key', value=upload_result['s3_key'])
        context['ti'].xcom_push(key='file_size_mb', value=upload_result['file_size_mb'])
        
        print(f"✓ Data successfully loaded to cloud storage")
        print(f"  S3 URL: {upload_result['s3_url']}")
        
        return upload_result['s3_url']
        
    except Exception as e:
        raise AirflowException(f"Failed to load data to cloud storage: {str(e)}")


# Default arguments for the DAG
default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

# Define the DAG
dag = DAG(
    'lahore_temperature_prediction_pipeline',
    default_args=default_args,
    description=(
        'Real-Time Predictive System for Lahore Temperature: '
        'ETL pipeline that fetches weather data, validates quality, '
        'and prepares for model training (4-hour ahead prediction)'
    ),
    schedule_interval='@daily',  # Run daily (can be changed to hourly: '@hourly')
    catchup=False,  # Don't backfill past dates
    tags=['mlops', 'weather', 'lahore', 'temperature-prediction'],
    max_active_runs=1,  # Only one run at a time
)

# Task 1: Extract weather data
extract_task = PythonOperator(
    task_id='extract_weather_data',
    python_callable=fetch_weather_data,
    dag=dag,
    doc_md="""
    ### Extract Weather Data
    
    Fetches the latest weather forecast data for Lahore from OpenWeather API.
    
    **Outputs:**
    - Raw JSON file saved to `raw_data/` directory with timestamp
    - Filepath pushed to XCom for downstream tasks
    """,
)

# Task 2: Data Quality Check (Mandatory Gate)
quality_check_task = PythonOperator(
    task_id='data_quality_check',
    python_callable=data_quality_check,
    dag=dag,
    doc_md="""
    ### Mandatory Data Quality Gate
    
    Performs strict validation on the extracted data:
    - Checks for >1% null values in key columns (temperature, pressure, humidity)
    - Validates data schema and completeness
    - Ensures minimum required data points
    
    **Behavior:**
    - If quality check fails, the DAG stops immediately
    - No downstream tasks will execute if validation fails
    """,
)

# Task 3: Transformation and Feature Engineering (Step 2.2)
transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_and_feature_engineering,
    dag=dag,
    doc_md="""
    ### Transformation and Feature Engineering (Step 2.2)
    
    Cleans raw data and performs essential feature engineering:
    - Flattens nested JSON structure
    - Creates lag features (previous temperature values)
    - Creates rolling statistics (mean, std, min, max)
    - Creates time-based features (hour, day of week, cyclical encodings)
    - Creates interaction features
    - Prepares target variable for 4-hour ahead prediction
    
    **Outputs:**
    - Processed CSV and Parquet files saved to `processed_data/` directory
    """,
)

# Task 4: Generate Profiling Report (Step 2.2)
profiling_task = PythonOperator(
    task_id='generate_profiling_report',
    python_callable=generate_profiling_report_task,
    dag=dag,
    doc_md="""
    ### Pandas Profiling Report (Step 2.2)
    
    Generates a detailed data quality and feature summary report:
    - Creates comprehensive pandas profiling report (HTML)
    - Logs report as artifact to MLflow (Dagshub)
    - Logs dataset statistics and metrics
    
    **Outputs:**
    - HTML profiling report saved to `reports/` directory
    - Report logged to MLflow tracking server (Dagshub)
    
    **Note:**
    - This task will not fail the DAG if profiling is unavailable
    - Install ydata-profiling for full functionality
    """,
)

# Task 5: Load to Cloud Storage (Step 2.3)
load_to_storage_task = PythonOperator(
    task_id='load_to_cloud_storage',
    python_callable=load_to_cloud_storage,
    dag=dag,
    doc_md="""
    ### Data Loading to Cloud Storage (Step 2.3)
    
    Uploads processed dataset to cloud storage:
    - Supports MinIO (local testing), AWS S3, or S3-compatible storage
    - Creates bucket if it doesn't exist
    - Uploads processed data files (CSV/Parquet)
    - Stores metadata about the upload
    
    **Outputs:**
    - Processed data uploaded to cloud storage
    - S3 URL and metadata pushed to XCom
    
    **Configuration:**
    - Set S3_BUCKET_NAME, S3_ENDPOINT_URL via environment variables
    - For MinIO: S3_ENDPOINT_URL=http://localhost:9000
    - For AWS S3: Leave S3_ENDPOINT_URL as None
    """,
)

# Task 6: DVC Version Data (Step 3)
dvc_version_data_task = PythonOperator(
    task_id='dvc_version_data',
    python_callable=dvc_add_and_push_task,
    dag=dag,
    doc_md="""
    ### DVC Data Versioning (Step 3)
    
    Versions processed dataset using DVC:
    - Adds processed data to DVC tracking
    - Pushes data to remote storage (MinIO/S3)
    - Commits .dvc metadata file to Git
    
    **Outputs:**
    - Data versioned in DVC
    - .dvc metadata file created
    - Data pushed to remote storage
    """,
)

# Task 7: Model Training (Step 4 - Phase II)
def train_model_task(**context):
    """
    Wrapper function to call train.py script for model training.
    Integrates with MLflow for experiment tracking.
    """
    from scripts.train import train_and_log_experiment
    
    print("\n" + "="*60)
    print("TASK 7: MODEL TRAINING (PHASE II - STEP 4)")
    print("="*60 + "\n")
    
    # Get collection time from XCom
    ti = context['ti']
    collection_time = ti.xcom_pull(task_ids='extract_weather_data', key='collection_time')
    
    print(f"Training model with data from: {collection_time}")
    
    # Train model with MLflow tracking
    result = train_and_log_experiment(
        model_type='random_forest',
        hyperparams={
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 2,
            'random_state': 42
        },
        run_name=f"airflow_training_{collection_time}"
    )
    
    # Push results to XCom
    ti.xcom_push(key='model_path', value=result['model_path'])
    ti.xcom_push(key='mlflow_run_id', value=result['run_id'])
    ti.xcom_push(key='test_rmse', value=result['metrics']['test_rmse'])
    ti.xcom_push(key='test_mae', value=result['metrics']['test_mae'])
    ti.xcom_push(key='test_r2', value=result['metrics']['test_r2'])
    
    print(f"\n[OK] Model training complete!")
    print(f"  MLflow Run ID: {result['run_id']}")
    print(f"  Test RMSE: {result['metrics']['test_rmse']:.4f}")
    print(f"  Test MAE: {result['metrics']['test_mae']:.4f}")
    print(f"  Test R²: {result['metrics']['test_r2']:.4f}")
    
    return result['run_id']

train_model_task_op = PythonOperator(
    task_id='train_model',
    python_callable=train_model_task,
    dag=dag,
    doc_md="""
    ### Model Training with MLflow (Phase II - Step 4)
    
    Trains machine learning model for temperature prediction:
    - Loads processed data from previous task
    - Trains Random Forest Regressor (4-hour ahead prediction)
    - Logs all hyperparameters, metrics, and model to MLflow
    - Integrates with Dagshub as central MLflow tracking server
    
    **Model Details:**
    - Algorithm: Random Forest Regressor
    - Target: Temperature 4 hours ahead
    - Features: Lag features, rolling means, time encodings
    
    **MLflow Tracking:**
    - Hyperparameters: n_estimators, max_depth, etc.
    - Metrics: RMSE, MAE, R² (train & test)
    - Artifacts: Trained model, feature importance
    
    **Outputs:**
    - Model logged to MLflow Model Registry
    - Metrics pushed to XCom for downstream tasks
    - Local model backup saved
    
    **Configuration:**
    - MLFLOW_TRACKING_URI: Set to Dagshub URL or local
    - MLFLOW_EXPERIMENT_NAME: Experiment name for grouping runs
    """,
)

# Define task dependencies
extract_task >> quality_check_task >> transform_task >> profiling_task >> load_to_storage_task >> dvc_version_data_task >> train_model_task_op

