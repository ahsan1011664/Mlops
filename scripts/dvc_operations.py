"""
DVC Operations for Data Versioning
Tracks processed datasets and pushes to remote storage
"""

import subprocess
import os
from pathlib import Path
from datetime import datetime, timezone


def run_command(command, check=True, capture=True):
    """Run a shell command"""
    try:
        if capture:
            result = subprocess.run(
                command,
                shell=True,
                check=check,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print(f"stderr: {result.stderr}")
            return result.returncode == 0, result.stdout
        else:
            result = subprocess.run(command, shell=True, check=check)
            return result.returncode == 0, ""
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return False, str(e)


def add_data_to_dvc(data_path):
    """
    Add data file/directory to DVC tracking
    
    Args:
        data_path: Path to file or directory to track
    
    Returns:
        Path to generated .dvc file
    """
    print(f"\n{'='*60}")
    print(f"ADDING DATA TO DVC: {data_path}")
    print(f"{'='*60}\n")
    
    data_path = Path(data_path)
    
    if not data_path.exists():
        print(f"✗ Error: {data_path} does not exist")
        return None
    
    # Add to DVC
    print(f"1. Adding {data_path} to DVC tracking...")
    success, output = run_command(f'dvc add "{data_path}"')
    
    if success:
        print(f"✓ Successfully added to DVC")
        
        # Determine .dvc file path
        if data_path.is_dir():
            dvc_file = Path(f"{data_path}.dvc")
        else:
            dvc_file = data_path.with_suffix(data_path.suffix + '.dvc')
        
        print(f"\n2. Generated DVC metadata file: {dvc_file}")
        
        if dvc_file.exists():
            print(f"✓ DVC file created successfully")
            
            # Show .dvc file contents
            print(f"\n3. DVC file contents:")
            with open(dvc_file, 'r') as f:
                print(f.read())
            
            return str(dvc_file)
        else:
            print(f"✗ DVC file not found at expected location")
            return None
    else:
        print(f"✗ Failed to add to DVC")
        return None


def push_data_to_remote():
    """Push DVC-tracked data to remote storage"""
    print(f"\n{'='*60}")
    print("PUSHING DATA TO REMOTE STORAGE")
    print(f"{'='*60}\n")
    
    print("Pushing data to DVC remote...")
    success, output = run_command('dvc push')
    
    if success:
        print("✓ Data successfully pushed to remote storage")
        return True
    else:
        print("✗ Failed to push data to remote")
        return False


def pull_data_from_remote():
    """Pull DVC-tracked data from remote storage"""
    print(f"\n{'='*60}")
    print("PULLING DATA FROM REMOTE STORAGE")
    print(f"{'='*60}\n")
    
    print("Pulling data from DVC remote...")
    success, output = run_command('dvc pull')
    
    if success:
        print("✓ Data successfully pulled from remote storage")
        return True
    else:
        print("✗ Failed to pull data from remote")
        return False


def check_dvc_status():
    """Check DVC status"""
    print(f"\n{'='*60}")
    print("DVC STATUS")
    print(f"{'='*60}\n")
    
    run_command('dvc status')
    
    print("\nDVC Remote Status:")
    run_command('dvc status --remote')


def list_dvc_tracked_files():
    """List all DVC-tracked files"""
    print(f"\n{'='*60}")
    print("DVC TRACKED FILES")
    print(f"{'='*60}\n")
    
    run_command('dvc list . --dvc-only')


def version_processed_data(processed_data_dir='processed_data'):
    """
    Complete workflow to version processed data with DVC
    
    Args:
        processed_data_dir: Directory containing processed data
    """
    print(f"\n{'='*60}")
    print("DVC DATA VERSIONING WORKFLOW")
    print(f"{'='*60}\n")
    
    # Step 1: Add data to DVC
    dvc_file = add_data_to_dvc(processed_data_dir)
    
    if not dvc_file:
        print("✗ Failed to add data to DVC")
        return False
    
    # Step 2: Check status
    check_dvc_status()
    
    # Step 3: Push to remote
    push_success = push_data_to_remote()
    
    if not push_success:
        print("✗ Failed to push data to remote")
        return False
    
    # Step 4: Instructions for Git
    print(f"\n{'='*60}")
    print("NEXT STEPS: COMMIT TO GIT")
    print(f"{'='*60}\n")
    print("The .dvc metadata file should be committed to Git:")
    print(f"\n  git add {dvc_file} .gitignore")
    print(f"  git commit -m 'Add DVC tracking for {processed_data_dir}'")
    print(f"  git push origin main")
    print(f"\n{'='*60}")
    
    return True


if __name__ == "__main__":
    # Example usage
    version_processed_data('processed_data')

