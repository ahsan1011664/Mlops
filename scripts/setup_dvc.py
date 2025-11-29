"""
DVC Setup and Configuration Script
Sets up DVC with MinIO/S3 as remote storage
"""

import subprocess
import os
from pathlib import Path


def run_command(command, check=True):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"Warning: {result.stderr}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.output}")
        return False


def setup_dvc():
    """Initialize DVC and configure remote storage"""
    
    print("="*60)
    print("DVC SETUP - DATA VERSION CONTROL")
    print("="*60)
    
    # Step 1: Initialize DVC
    print("\n1. Initializing DVC...")
    if run_command("dvc init"):
        print("✓ DVC initialized successfully")
    else:
        print("✗ DVC initialization failed (might already be initialized)")
    
    # Step 2: Configure MinIO as remote storage
    print("\n2. Configuring MinIO as DVC remote storage...")
    
    # MinIO configuration
    endpoint_url = os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')
    bucket_name = os.getenv('S3_BUCKET_NAME', 'lahore-weather-data')
    access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    
    # Add remote storage
    remote_url = f"s3://{bucket_name}/dvc-storage"
    
    commands = [
        f'dvc remote add -d myremote {remote_url}',
        f'dvc remote modify myremote endpointurl {endpoint_url}',
        f'dvc remote modify myremote access_key_id {access_key}',
        f'dvc remote modify myremote secret_access_key {secret_key}',
    ]
    
    for cmd in commands:
        if run_command(cmd, check=False):
            print(f"✓ {cmd.split()[2]} configured")
    
    print("\n✓ DVC remote storage configured")
    
    # Step 3: Show configuration
    print("\n3. DVC Configuration:")
    run_command("dvc remote list")
    run_command("dvc config --list")
    
    print("\n" + "="*60)
    print("DVC SETUP COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Add data files: dvc add processed_data/")
    print("2. Commit .dvc files: git add processed_data.dvc .dvc/")
    print("3. Push data to remote: dvc push")
    print("="*60)


if __name__ == "__main__":
    setup_dvc()

