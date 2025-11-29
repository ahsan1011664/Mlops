# Quick Start: Test Step 2.1 DAG with Docker

## Prerequisites
✅ **Docker Desktop must be installed and running**
- Download: https://www.docker.com/products/docker-desktop
- Make sure Docker Desktop is running (check system tray)

## Step-by-Step Commands

### Option 1: Use PowerShell Scripts (Easiest)

```powershell
# Navigate to project
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"

# Start Airflow
.\start_airflow_docker.ps1

# Wait 30-60 seconds, then open: http://localhost:8080
# Login: admin / admin
# Find DAG: lahore_temperature_prediction_pipeline
# Toggle ON and click play button

# When done, stop Airflow
.\stop_airflow_docker.ps1
```

---

### Option 2: Manual Commands

#### Step 1: Navigate to Project
```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
```

#### Step 2: Initialize Airflow (First Time Only)
```powershell
docker-compose up airflow-init
```
**Wait for:** "User 'admin' created with role 'Admin'"

#### Step 3: Start Airflow
```powershell
docker-compose up -d
```

#### Step 4: Access Airflow UI
1. Open browser: **http://localhost:8080**
2. Login:
   - Username: `admin`
   - Password: `admin`

#### Step 5: Run Your DAG
1. Find DAG: **`lahore_temperature_prediction_pipeline`**
2. Toggle it **ON** (switch on left)
3. Click **play button (▶)** to trigger
4. Watch tasks:
   - `extract_weather_data` → should turn green ✅
   - `data_quality_check` → should turn green ✅

#### Step 6: Verify Results
```powershell
# Check raw data files
dir raw_data

# View latest file
Get-ChildItem raw_data | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

#### Step 7: Stop Airflow
```powershell
docker-compose down
```

---

## Useful Commands

### View Logs
```powershell
# All logs
docker-compose logs

# Specific service
docker-compose logs airflow-scheduler

# Follow logs (real-time)
docker-compose logs -f airflow-scheduler
```

### Check Status
```powershell
docker-compose ps
```

### Restart Services
```powershell
docker-compose restart
```

### Complete Reset (if something breaks)
```powershell
docker-compose down -v
docker-compose up airflow-init
docker-compose up -d
```

---

## Expected Results

After running the DAG, you should see:

✅ **In Airflow UI:**
- Both tasks show green checkmarks
- No errors in task logs

✅ **In File System:**
- New JSON file in `raw_data/` folder
- File name: `lahore_weather_raw_YYYYMMDD_HHMMSS.json`

✅ **In Task Logs:**
- "Successfully fetched and saved raw data"
- "DATA QUALITY CHECK PASSED"

---

## Troubleshooting

### Docker not running?
- Start Docker Desktop application
- Wait for it to fully start

### Port 8080 already in use?
- Edit `docker-compose.yml`
- Change `"8080:8080"` to `"8081:8080"` (or another port)
- Access UI at: http://localhost:8081

### DAG not appearing?
```powershell
# Check DAG syntax
docker-compose exec airflow-webserver python -m py_compile /opt/airflow/dags/lahore_temperature_prediction_dag.py

# Check logs
docker-compose logs airflow-scheduler | Select-String "lahore"
```

### Tasks failing?
1. Click on failed task in Airflow UI
2. Click "Log" button
3. Check error message
4. Common issues:
   - API key incorrect
   - Network connectivity
   - File permissions

---

## Next Steps

Once Step 2.1 is verified working:
✅ Proceed to **Step 2.2** (Transformation and Feature Engineering)
✅ Same Docker setup will work for all future steps

