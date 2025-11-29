# DVC (Data Version Control) Setup Guide

## What is DVC?

DVC (Data Version Control) is a version control system for data and ML models. It works alongside Git:
- **Git**: Tracks code and small metadata files (.dvc files)
- **DVC**: Tracks large data files and models, stores them in cloud storage

## Why Use DVC?

1. **Version large datasets** without bloating Git repository
2. **Track data lineage** and reproducibility
3. **Share data** efficiently with team members
4. **Cloud storage integration** (S3, MinIO, Azure, GCS)

## Step-by-Step Setup

### Step 1: Install DVC

```powershell
pip install dvc[s3]
```

### Step 2: Initialize DVC

```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
dvc init
```

This creates `.dvc/` directory with DVC configuration.

### Step 3: Configure Remote Storage (MinIO)

```powershell
# Add MinIO as remote storage
dvc remote add -d myremote s3://lahore-weather-data/dvc-storage

# Configure MinIO endpoint
dvc remote modify myremote endpointurl http://localhost:9000

# Set credentials
dvc remote modify myremote access_key_id minioadmin
dvc remote modify myremote secret_access_key minioadmin
```

### Step 4: Track Processed Data

```powershell
# Add processed_data directory to DVC
dvc add processed_data

# This creates: processed_data.dvc
```

### Step 5: Commit .dvc File to Git

```powershell
# Add DVC files to Git
git add processed_data.dvc .gitignore .dvc/

# Commit
git commit -m "Add DVC tracking for processed data"

# Push to GitHub
git push origin main
```

### Step 6: Push Data to Remote Storage

```powershell
# Push actual data files to MinIO
dvc push
```

## Quick Setup Script

Use the automated setup script:

```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
python scripts/setup_dvc.py
```

## Complete Workflow

### For Data Producer (You)

```powershell
# 1. Setup DVC (one time)
python scripts/setup_dvc.py

# 2. Add new processed data
dvc add processed_data

# 3. Commit .dvc file to Git
git add processed_data.dvc .gitignore
git commit -m "Update processed data"
git push origin main

# 4. Push data to remote storage
dvc push
```

### For Data Consumer (Team Member)

```powershell
# 1. Clone repository
git clone https://github.com/asim548/Mlops_Project.git
cd Mlops_Project

# 2. Pull data from remote storage
dvc pull
```

## DVC File Structure

### What Gets Tracked Where

**Git (Small files):**
- `processed_data.dvc` - Metadata file (hash, size, path)
- `.dvc/config` - DVC configuration
- `.dvc/.gitignore` - DVC internal files to ignore
- `.gitignore` - Updated to ignore actual data files

**DVC Remote (Large files):**
- Actual data files (CSV, Parquet, etc.)
- Stored in MinIO/S3 with content-addressable storage

### Example .dvc File

```yaml
outs:
- md5: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
  size: 1048576
  path: processed_data
```

## Useful DVC Commands

```powershell
# Check DVC status
dvc status

# Check remote status
dvc status --remote

# List DVC-tracked files
dvc list . --dvc-only

# Pull specific file
dvc pull processed_data.dvc

# Push specific file
dvc push processed_data.dvc

# Show data statistics
dvc dag

# Remove DVC tracking
dvc remove processed_data.dvc
```

## Integration with Airflow

Add DVC operations to your Airflow DAG:

```python
def dvc_version_data(**context):
    """Add DVC versioning after data processing"""
    import subprocess
    
    # Add to DVC
    subprocess.run(['dvc', 'add', 'processed_data'], check=True)
    
    # Push to remote
    subprocess.run(['dvc', 'push'], check=True)
    
    print("✓ Data versioned with DVC")
```

## Troubleshooting

### Issue 1: DVC Remote Connection Failed

**Solution**: Check MinIO is running
```powershell
docker-compose ps minio
```

### Issue 2: Authentication Error

**Solution**: Verify credentials
```powershell
dvc remote modify myremote access_key_id minioadmin
dvc remote modify myremote secret_access_key minioadmin
```

### Issue 3: Large Files in Git

**Solution**: Ensure .gitignore is updated
```powershell
# .gitignore should contain:
/processed_data
```

### Issue 4: DVC Push Fails

**Solution**: Check MinIO bucket exists
- Access MinIO console: http://localhost:9001
- Verify `lahore-weather-data` bucket exists
- Check `dvc-storage` prefix

## Benefits for Your Project

1. **Reproducibility**: Anyone can reproduce your results by pulling exact data version
2. **Collaboration**: Team members can access large datasets without Git bloat
3. **Versioning**: Track data changes over time
4. **Storage Efficiency**: Deduplication and compression
5. **Cloud-Native**: Works with S3, Azure, GCS, MinIO

## Next Steps

After setting up DVC:
1. ✅ Data versioned with DVC
2. ✅ .dvc files committed to Git
3. ✅ Large files stored in MinIO
4. ⏭️ Continue to Phase II: Model Training with MLflow

