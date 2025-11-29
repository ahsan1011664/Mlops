# Lahore Temperature Prediction - Real-Time Predictive System (RPS)

## Project Overview

This MLOps pipeline predicts Lahore's temperature **4 hours into the future** using live data from the OpenWeather API. The system automatically retrains itself when new data arrives and includes comprehensive monitoring and CI/CD integration.

## Problem Statement

**"Build a Real-Time Predictive System that predicts the temperature of Lahore 4 hours into the future using live OpenWeather hourly data, and automatically retrains itself when new data arrives."**

## Project Structure

```
lahore_rps_pipeline/
├── dags/                    # Apache Airflow DAGs
│   └── lahore_temperature_prediction_dag.py
├── scripts/                 # Python scripts (training, ETL helpers)
├── raw_data/                # Raw API data (timestamped JSON files)
├── processed_data/          # Cleaned and feature-engineered datasets
├── models/                  # Trained model files
├── reports/                 # Data profiling reports, metrics
├── monitoring/              # Prometheus/Grafana configurations
├── tests/                   # Unit and integration tests
├── .github/                 # GitHub Actions workflows
└── requirements.txt         # Python dependencies
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Airflow

1. Initialize Airflow database:
```bash
airflow db init
```

2. Create an Airflow user:
```bash
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin
```

3. Set Airflow home (if needed):
```bash
export AIRFLOW_HOME=/path/to/your/project/lahore_rps_pipeline
```

4. Start Airflow webserver:
```bash
airflow webserver --port 8080
```

5. Start Airflow scheduler (in another terminal):
```bash
airflow scheduler
```

6. Access Airflow UI at: `http://localhost:8080`

### 3. API Configuration

The OpenWeather API key is already configured in the DAG file. If you need to change it, edit:
- `lahore_rps_pipeline/dags/lahore_temperature_prediction_dag.py`
- Update the `API_KEY` variable

## Current Implementation Status

### ✅ Phase I: Data Ingestion (Step 2.1) - COMPLETED

- **Extraction Task**: Fetches Lahore weather data from OpenWeather API
  - Saves raw data with timestamp to `raw_data/` directory
  - Uses OpenWeather Forecast API (3-hourly intervals)
  
- **Mandatory Quality Gate**: Strict data validation
  - Checks for >1% null values in temperature and other key columns
  - Schema validation
  - Data completeness checks
  - DAG fails immediately if quality check fails

### 🔄 Next Steps

- [ ] Transformation and Feature Engineering (Step 2.2)
- [ ] Data Profiling with Pandas Profiling (Step 2.2)
- [ ] Data Loading to Cloud Storage (Step 2.3)
- [ ] DVC Integration for Data Versioning (Step 3)
- [ ] MLflow Training Script (Step 4)
- [ ] Dagshub Integration (Step 4)
- [ ] CI/CD Pipeline with GitHub Actions (Step 5)
- [ ] Docker Containerization (Step 5.4)
- [ ] Prometheus & Grafana Monitoring (Step 6)

## Running the DAG

1. Ensure Airflow is running (webserver + scheduler)
2. Navigate to Airflow UI: `http://localhost:8080`
3. Find the DAG: `lahore_temperature_prediction_pipeline`
4. Toggle it ON (if not already)
5. Trigger manually or wait for scheduled run (daily at midnight)

## DAG Schedule

- **Current Schedule**: `@daily` (runs once per day)
- Can be changed to `@hourly` for more frequent updates
- Edit `schedule_interval` in the DAG definition

## Data Flow

1. **Extract** → Fetch weather data from OpenWeather API
2. **Quality Check** → Validate data quality (mandatory gate)
3. **Transform** → (Next step) Clean and engineer features
4. **Load** → (Next step) Save to cloud storage and version with DVC
5. **Train** → (Next step) Train model with MLflow tracking
6. **Deploy** → (Next step) Serve model via FastAPI
7. **Monitor** → (Next step) Track metrics with Prometheus/Grafana

## Notes

- Raw data files are saved with format: `lahore_weather_raw_YYYYMMDD_HHMMSS.json`
- Quality check ensures data integrity before proceeding
- All tasks use XCom to pass data between Airflow tasks

## License

This project is part of an MLOps case study assignment.

