# PowerShell script to set up Git branches for MLOps project
# Run this once to initialize the branching structure

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Git Branch Setup Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get current branch
$currentBranch = git branch --show-current
Write-Host "Current branch: $currentBranch" -ForegroundColor Yellow
Write-Host ""

# Check if we're on main or master
if ($currentBranch -ne "main" -and $currentBranch -ne "master") {
    Write-Host "⚠️  Warning: You're not on main/master branch." -ForegroundColor Red
    Write-Host "   Please switch to main or master first:"
    Write-Host "   git checkout main  # or git checkout master"
    exit 1
}

# Ensure we're up to date
Write-Host "1. Pulling latest changes..." -ForegroundColor Green
git pull origin $currentBranch
Write-Host "✓ Up to date" -ForegroundColor Green
Write-Host ""

# Function to check if branch exists locally
function Test-LocalBranch {
    param([string]$BranchName)
    $branches = git branch --list $BranchName
    return $branches.Count -gt 0
}

# Function to check if branch exists on remote
function Test-RemoteBranch {
    param([string]$BranchName)
    $branches = git branch -r --list "origin/$BranchName"
    return $branches.Count -gt 0
}

# Create dev branch
Write-Host "2. Setting up 'dev' branch..." -ForegroundColor Green
if (-not (Test-LocalBranch "dev")) {
    git checkout -b dev
    git push -u origin dev
    Write-Host "✓ Created and pushed 'dev' branch" -ForegroundColor Green
} else {
    Write-Host "   Branch 'dev' exists locally, checking remote..." -ForegroundColor Yellow
    if (-not (Test-RemoteBranch "dev")) {
        Write-Host "   Pushing existing branch to remote..." -ForegroundColor Yellow
        git push -u origin dev
    } else {
        Write-Host "   Branch 'dev' exists on both local and remote" -ForegroundColor Yellow
    }
}
Write-Host ""

# Create test branch
Write-Host "3. Setting up 'test' branch..." -ForegroundColor Green
if (-not (Test-LocalBranch "test")) {
    git checkout -b test
    git push -u origin test
    Write-Host "✓ Created and pushed 'test' branch" -ForegroundColor Green
} else {
    Write-Host "   Branch 'test' exists locally, checking remote..." -ForegroundColor Yellow
    if (-not (Test-RemoteBranch "test")) {
        Write-Host "   Pushing existing branch to remote..." -ForegroundColor Yellow
        git push -u origin test
    } else {
        Write-Host "   Branch 'test' exists on both local and remote" -ForegroundColor Yellow
    }
}
Write-Host ""

# Return to original branch
Write-Host "4. Returning to original branch..." -ForegroundColor Green
git checkout $currentBranch
Write-Host "✓ Back on $currentBranch" -ForegroundColor Green
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Branch Setup Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Go to GitHub → Settings → Branches"
Write-Host "2. Set up branch protection rules for 'test' and 'master'"
Write-Host "3. See GIT_WORKFLOW_GUIDE.md for details"
Write-Host ""
Write-Host "Available branches:" -ForegroundColor Yellow
git branch -a | Select-String -Pattern "(dev|test|master|main)"
Write-Host ""

