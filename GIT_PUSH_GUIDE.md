# Git Push Guide - Push Project to GitHub

## Your GitHub Repository
**URL**: https://github.com/asim548/Mlops_Project.git

## Step-by-Step Commands

### Step 1: Navigate to Project Directory
```powershell
cd "C:\Users\Aaim Shehzad\OneDrive\Desktop\New folder\lahore_rps_pipeline"
```

### Step 2: Initialize Git (if not already done)
```powershell
git init
```

### Step 3: Configure Git (if first time)
```powershell
git config --global user.name "asim548"
git config --global user.email "your-email@example.com"  # Replace with your email
```

### Step 4: Add Remote Repository
```powershell
git remote add origin https://github.com/asim548/Mlops_Project.git
```

### Step 5: Create .gitignore (Important!)
This file tells Git which files to ignore (large data files, logs, etc.)

Already created in your project. Verify it exists:
```powershell
Get-Content .gitignore
```

### Step 6: Add All Files
```powershell
git add .
```

### Step 7: Commit Changes
```powershell
git commit -m "Initial commit: Phase I complete (Steps 2.1-2.3) - Data Ingestion Pipeline"
```

### Step 8: Push to GitHub
```powershell
# For first push (creates main branch)
git branch -M main
git push -u origin main
```

## Alternative: If You Need to Force Push (Use Carefully!)
```powershell
git push -u origin main --force
```

## Verify Push
After pushing, visit: https://github.com/asim548/Mlops_Project

You should see:
- All your project files
- README.md displayed on the main page
- Folder structure visible

## Common Issues & Solutions

### Issue 1: Authentication Required
**Solution**: Use Personal Access Token (PAT)
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` permissions
3. Use token as password when prompted

### Issue 2: Remote Already Exists
```powershell
git remote remove origin
git remote add origin https://github.com/asim548/Mlops_Project.git
```

### Issue 3: Files Too Large
If you get errors about large files:
```powershell
# Remove large files from staging
git rm --cached raw_data/*.json
git rm --cached processed_data/*.csv

# Commit and push
git commit -m "Remove large data files"
git push -u origin main
```

### Issue 4: Merge Conflicts
If repository already has files:
```powershell
git pull origin main --allow-unrelated-histories
# Resolve conflicts if any
git push -u origin main
```

## What Gets Pushed

### ✅ Included (Code & Config)
- All Python scripts
- Airflow DAG files
- Docker configuration
- Documentation (MD files)
- Requirements.txt
- .gitignore

### ❌ Excluded (via .gitignore)
- Large data files (raw_data/*.json, processed_data/*.csv)
- Log files
- Python cache (__pycache__)
- Virtual environments
- Airflow database
- Docker volumes

## After Pushing

### Update README
Add project details to README.md on GitHub:
- Project description
- Setup instructions
- How to run
- Dependencies

### Add Topics/Tags
On GitHub repository page:
- Click "Add topics"
- Add: `mlops`, `airflow`, `machine-learning`, `weather-prediction`, `docker`

### Enable GitHub Actions (Phase III)
Will be set up in Phase III for CI/CD

## Quick Reference

```powershell
# Check status
git status

# View remote
git remote -v

# View commit history
git log --oneline

# Create new branch
git checkout -b feature/new-feature

# Push branch
git push origin feature/new-feature
```

