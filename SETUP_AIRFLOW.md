# How to Test the Airflow DAG

## Quick Setup Guide

### Step 1: Install Airflow
```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
pip install apache-airflow
```

**Note:** On Windows, Airflow has limitations. You may need to use WSL2 or Docker. But we can try this first.

### Step 2: Set Airflow Home Directory
```powershell
$env:AIRFLOW_HOME = "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
```

### Step 3: Initialize Airflow Database
```powershell
airflow db init
```

### Step 4: Create Admin User
```powershell
airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin
```

### Step 5: Start Airflow Webserver (Terminal 1)
```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
$env:AIRFLOW_HOME = "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
airflow webserver --port 8080
```
**Keep this terminal open!**

### Step 6: Start Airflow Scheduler (Terminal 2 - New Window)
```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
$env:AIRFLOW_HOME = "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
airflow scheduler
```
**Keep this terminal open too!**

### Step 7: Access Airflow UI
1. Open browser: **http://localhost:8080**
2. Login: 
   - Username: `admin`
   - Password: `admin`

### Step 8: Find and Run Your DAG
1. Look for DAG: **`lahore_temperature_prediction_pipeline`**
2. Toggle it **ON** (switch on the left side)
3. Click the **play button (▶)** to trigger manually
4. Click on the DAG name to see task details
5. Watch tasks execute:
   - `extract_weather_data` → should turn green (success)
   - `data_quality_check` → should turn green (success)

### Step 9: Check Results
```powershell
# View raw data files created by DAG
dir raw_data

# View latest file
Get-ChildItem raw_data | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```

## Troubleshooting

### If Airflow doesn't work on Windows:
- **Option A:** Use WSL2 (Windows Subsystem for Linux)
- **Option B:** Use Docker (recommended for production)
- **Option C:** Continue building pipeline and test later

### If DAG doesn't appear:
1. Check DAG file location: `lahore_rps_pipeline/dags/lahore_temperature_prediction_dag.py`
2. Check for syntax errors: `python -m py_compile dags/lahore_temperature_prediction_dag.py`
3. Restart Airflow scheduler

### If tasks fail:
- Check logs in Airflow UI (click on failed task → View Log)
- Verify API key is correct
- Check that `raw_data/` folder exists

