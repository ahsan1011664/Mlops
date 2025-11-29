# Docker Setup for Airflow - Testing Step 2.1

## Prerequisites

1. **Docker Desktop** must be installed and running
   - Download from: https://www.docker.com/products/docker-desktop
   - Make sure Docker Desktop is running (you'll see the Docker icon in system tray)

2. **Docker Compose** (usually comes with Docker Desktop)

## Quick Start Commands

### Step 1: Navigate to Project Directory
```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
```

### Step 2: Create Required Directories (if they don't exist)
```powershell
mkdir logs, plugins -ErrorAction SilentlyContinue
```

### Step 3: Initialize Airflow (First Time Only)
```powershell
docker-compose up airflow-init
```

This will:
- Initialize the Airflow database
- Create admin user (username: `admin`, password: `admin`)
- Set up all required configurations

**Expected output:** You should see "User 'admin' created with role 'Admin'" at the end.

### Step 4: Start Airflow Services
```powershell
docker-compose up -d
```

This starts:
- PostgreSQL database
- Airflow webserver (UI)
- Airflow scheduler

**Wait 30-60 seconds** for services to start up.

### Step 5: Access Airflow UI

1. Open browser: **http://localhost:8080**
2. Login:
   - Username: `admin`
   - Password: `admin`

### Step 6: Find and Run Your DAG

1. Look for DAG: **`lahore_temperature_prediction_pipeline`**
2. Toggle it **ON** (switch on the left side)
3. Click the **play button (▶)** to trigger manually
4. Click on the DAG name to see task details
5. Watch tasks execute:
   - `extract_weather_data` → should turn green (success)
   - `data_quality_check` → should turn green (success)

### Step 7: Check Results

```powershell
# View raw data files created by DAG
dir raw_data

# View latest file
Get-ChildItem raw_data | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```

## Useful Commands

### View Logs
```powershell
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs airflow-scheduler
docker-compose logs airflow-webserver

# Follow logs in real-time
docker-compose logs -f airflow-scheduler
```

### Stop Airflow
```powershell
docker-compose down
```

### Stop and Remove Volumes (Clean Start)
```powershell
docker-compose down -v
```

### Restart Services
```powershell
docker-compose restart
```

### Check Service Status
```powershell
docker-compose ps
```

## Troubleshooting

### If DAG doesn't appear:
1. Check DAG file is in correct location: `lahore_rps_pipeline/dags/lahore_temperature_prediction_dag.py`
2. Check for syntax errors:
   ```powershell
   docker-compose exec airflow-webserver python -m py_compile /opt/airflow/dags/lahore_temperature_prediction_dag.py
   ```
3. Check DAG logs:
   ```powershell
   docker-compose logs airflow-scheduler | Select-String "lahore"
   ```

### If tasks fail:
1. Click on the failed task in Airflow UI
2. Click "Log" button to see detailed error
3. Common issues:
   - API key incorrect → Check DAG file
   - Network issues → Check internet connection
   - Permission issues → Check file permissions

### If port 8080 is already in use:
Edit `docker-compose.yml` and change:
```yaml
ports:
  - "8080:8080"  # Change 8080 to another port like 8081
```

### If Docker Desktop is not running:
- Start Docker Desktop application
- Wait for it to fully start (whale icon in system tray should be steady)

### Reset Everything (Nuclear Option):
```powershell
# Stop and remove everything
docker-compose down -v

# Remove all containers and images
docker system prune -a

# Start fresh
docker-compose up airflow-init
docker-compose up -d
```

## Verify DAG is Working

After running the DAG, you should see:
1. ✅ Green checkmarks on both tasks in Airflow UI
2. ✅ New JSON file in `raw_data/` folder
3. ✅ No errors in task logs

## Next Steps

Once Step 2.1 is verified working in Docker:
- ✅ Proceed to Step 2.2 (Transformation and Feature Engineering)
- The same Docker setup will work for all future steps

