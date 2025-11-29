# Commands to Test Step 2.1 (Extraction & Quality Gate)

## Option 1: Quick Test WITHOUT Airflow (Recommended for First Test)

This tests the extraction and quality check functions directly without needing Airflow running.

### Step 1: Navigate to Project Directory
```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
```

### Step 2: Install Required Packages (if not already installed)
```powershell
pip install requests pandas
```

### Step 3: Run the Test Script
```powershell
python scripts/test_extraction.py
```

**Expected Output:**
- ✓ Weather data fetched successfully
- ✓ Raw data file saved to `raw_data/` folder
- ✓ Quality check passed
- ✓ All tests passed

**Check Results:**
```powershell
# List the raw data files created
dir raw_data
```

---

## Option 2: Full Test with Airflow (Complete Pipeline)

### Step 1: Install Airflow
```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
pip install apache-airflow
```

### Step 2: Set Airflow Home Environment Variable
```powershell
$env:AIRFLOW_HOME = "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
```

### Step 3: Initialize Airflow Database
```powershell
airflow db init
```

### Step 4: Create Airflow Admin User
```powershell
airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin
```

### Step 5: Start Airflow Webserver (Terminal 1)
```powershell
airflow webserver --port 8080
```
**Keep this terminal open!** Access UI at: http://localhost:8080

### Step 6: Start Airflow Scheduler (Terminal 2 - New Window)
```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
$env:AIRFLOW_HOME = "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
airflow scheduler
```
**Keep this terminal open too!**

### Step 7: Access Airflow UI and Run DAG
1. Open browser: http://localhost:8080
2. Login: username=`admin`, password=`admin`
3. Find DAG: `lahore_temperature_prediction_pipeline`
4. Toggle it ON (switch on the left)
5. Click the play button (▶) to trigger manually
6. Click on the DAG name to see task details
7. Watch the tasks execute:
   - `extract_weather_data` (green = success)
   - `data_quality_check` (green = success)

### Step 8: Check Results
```powershell
# View raw data files
dir raw_data

# View a sample raw data file
Get-Content raw_data\lahore_weather_raw_*.json | Select-Object -First 50
```

---

## Option 3: Test Individual Functions (Python REPL)

### Start Python Interactive Session
```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
python
```

### In Python REPL:
```python
# Import functions
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
from dags.lahore_temperature_prediction_dag import fetch_weather_data, data_quality_check

# Create mock context
class MockTI:
    def __init__(self):
        self.xcom_data = {}
    def xcom_push(self, key, value):
        self.xcom_data[key] = value
        print(f"Saved: {key}")
    def xcom_pull(self, task_ids, key):
        return self.xcom_data.get(key)

class MockContext:
    def __init__(self):
        self.ti = MockTI()

context = MockContext()

# Test extraction
result = fetch_weather_data(**{'ti': context.ti})
print(f"File saved: {result}")

# Test quality check
quality_result = data_quality_check(**{'ti': context.ti})
print(f"Quality check: {quality_result}")
```

---

## Troubleshooting

### If API Key Error:
- Check that API key is correct in `dags/lahore_temperature_prediction_dag.py`
- Verify OpenWeather API key is active

### If Import Errors:
```powershell
pip install -r requirements.txt
```

### If Airflow DAG Not Showing:
1. Check DAG file is in correct location: `lahore_rps_pipeline/dags/`
2. Check for syntax errors: `python -m py_compile dags/lahore_temperature_prediction_dag.py`
3. Restart Airflow scheduler

### If Quality Check Fails:
- Check the logs in Airflow UI for specific error
- Verify API returned valid data
- Check `raw_data/` folder for the saved JSON file

---

## Quick Verification Commands

```powershell
# Check if raw data was created
dir raw_data

# Count files
(dir raw_data).Count

# View latest file
Get-ChildItem raw_data | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```

