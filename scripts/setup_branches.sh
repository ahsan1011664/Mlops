#!/bin/bash
# Script to set up Git branches for MLOps project
# Run this once to initialize the branching structure

set -e

echo "=========================================="
echo "Git Branch Setup Script"
echo "=========================================="
echo ""

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"
echo ""

# Check if we're on main or master
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    echo "⚠️  Warning: You're not on main/master branch."
    echo "   Please switch to main or master first:"
    echo "   git checkout main  # or git checkout master"
    exit 1
fi

# Ensure we're up to date
echo "1. Pulling latest changes..."
git pull origin $CURRENT_BRANCH
echo "✓ Up to date"
echo ""

# Check if branches already exist
check_branch() {
    if git show-ref --verify --quiet refs/heads/$1; then
        echo "   Branch '$1' already exists locally"
        return 1
    else
        return 0
    fi
}

check_remote_branch() {
    if git show-ref --verify --quiet refs/remotes/origin/$1; then
        echo "   Branch '$1' already exists on remote"
        return 1
    else
        return 0
    fi
}

# Create dev branch
echo "2. Setting up 'dev' branch..."
if check_branch "dev"; then
    git checkout -b dev
    git push -u origin dev
    echo "✓ Created and pushed 'dev' branch"
else
    echo "   Branch 'dev' exists, skipping..."
    if check_remote_branch "dev"; then
        echo "   Pushing existing branch to remote..."
        git push -u origin dev
    fi
fi
echo ""

# Create test branch
echo "3. Setting up 'test' branch..."
if check_branch "test"; then
    git checkout -b test
    git push -u origin test
    echo "✓ Created and pushed 'test' branch"
else
    echo "   Branch 'test' exists, skipping..."
    if check_remote_branch "test"; then
        echo "   Pushing existing branch to remote..."
        git push -u origin test
    fi
fi
echo ""

# Return to original branch
echo "4. Returning to original branch..."
git checkout $CURRENT_BRANCH
echo "✓ Back on $CURRENT_BRANCH"
echo ""

echo "=========================================="
echo "Branch Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Go to GitHub → Settings → Branches"
echo "2. Set up branch protection rules for 'test' and 'master'"
echo "3. See GIT_WORKFLOW_GUIDE.md for details"
echo ""
echo "Available branches:"
git branch -a | grep -E "(dev|test|master|main)" || echo "  (check with: git branch -a)"
echo ""

