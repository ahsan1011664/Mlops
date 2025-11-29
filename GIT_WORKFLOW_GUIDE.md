# Git Workflow and Branching Strategy Guide

## Overview

This project follows a strict branching model to ensure code quality and controlled deployments. All work flows through feature branches before reaching production.

---

## Branching Model

### Branch Hierarchy

```
feature → dev → test → master
```

### Branch Descriptions

| Branch | Purpose | Protection Level |
|--------|---------|------------------|
| **master** | Production-ready code | Highest - Requires PR approval + CI/CD checks |
| **test** | Pre-production testing | High - Requires PR approval + model validation |
| **dev** | Development integration | Medium - Requires CI checks |
| **feature/*** | New features/fixes | Low - No restrictions |

---

## Workflow Rules

### 1. Feature Branches → Dev

**When:** Starting new work (features, bug fixes, improvements)

**Process:**
1. Create feature branch from `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

3. Push feature branch:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. Create Pull Request to `dev`:
   - Go to GitHub → Create Pull Request
   - Base: `dev`, Compare: `feature/your-feature-name`
   - CI checks will run automatically (code quality, tests)
   - Once CI passes, merge (no approval required for dev)

5. After merge, delete feature branch:
   ```bash
   git checkout dev
   git pull origin dev
   git branch -d feature/your-feature-name
   ```

### 2. Dev → Test

**When:** Ready to test model retraining and validation

**Process:**
1. Create PR from `dev` to `test`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b test-integration
   # Make any test-specific changes if needed
   git push -u origin test-integration
   ```

2. Create Pull Request:
   - Base: `test`, Compare: `dev` (or your test branch)
   - **Requires:** At least 1 peer approval (mandatory)
   - CI will trigger full pipeline + model retraining
   - CML will compare model performance
   - **Blocked if:** Model performance degrades

3. After approval and CI passes, merge to `test`

### 3. Test → Master

**When:** Ready for production deployment

**Process:**
1. Create PR from `test` to `master`:
   ```bash
   git checkout test
   git pull origin test
   git checkout -b production-release
   # Make any production-specific changes if needed
   git push -u origin production-release
   ```

2. Create Pull Request:
   - Base: `master`, Compare: `test` (or your release branch)
   - **Requires:** At least 1 peer approval (mandatory)
   - CI will trigger deployment pipeline
   - Docker image will be built and pushed
   - **Blocked if:** Deployment checks fail

3. After approval and CI passes, merge to `master`
4. Deployment to production happens automatically

---

## Branch Naming Conventions

### Feature Branches
- Format: `feature/description`
- Examples:
  - `feature/add-data-validation`
  - `feature/improve-model-accuracy`
  - `feature/fix-api-endpoint`

### Bug Fix Branches
- Format: `fix/description`
- Examples:
  - `fix/handle-null-values`
  - `fix/dag-scheduler-error`

### Hotfix Branches (for master)
- Format: `hotfix/description`
- Examples:
  - `hotfix/critical-api-bug`
  - `hotfix/security-patch`

---

## Initial Setup

### Step 1: Create Required Branches

If branches don't exist yet, create them:

```bash
# Ensure you're on main/master
git checkout main  # or master, depending on your default branch

# Create dev branch
git checkout -b dev
git push -u origin dev

# Create test branch
git checkout -b test
git push -u origin test

# Return to main/master
git checkout main  # or master
```

### Step 2: Configure Branch Protection (GitHub)

1. Go to your GitHub repository
2. Navigate to: **Settings → Branches**
3. Add branch protection rules:

#### For `test` branch:
- Click "Add rule"
- Branch name pattern: `test`
- Enable:
  - ✅ Require a pull request before merging
    - Require approvals: **1**
    - Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require status checks to pass before merging
    - Select: `CI - Dev to Test (Model Retraining + CML)`
  - ✅ Require conversation resolution before merging
  - ✅ Do not allow bypassing the above settings

#### For `master` branch:
- Click "Add rule"
- Branch name pattern: `master`
- Enable:
  - ✅ Require a pull request before merging
    - Require approvals: **1**
    - Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require status checks to pass before merging
    - Select: `CD - Test to Master (Production Deployment)`
  - ✅ Require conversation resolution before merging
  - ✅ Include administrators
  - ✅ Do not allow bypassing the above settings

#### For `dev` branch (optional, recommended):
- Click "Add rule"
- Branch name pattern: `dev`
- Enable:
  - ✅ Require status checks to pass before merging
    - Select: `CI - Feature to Dev`
  - ⚠️ Do NOT require approvals (dev is for integration)

---

## Daily Workflow

### Starting New Work

```bash
# 1. Update dev branch
git checkout dev
git pull origin dev

# 2. Create feature branch
git checkout -b feature/my-new-feature

# 3. Make changes, commit, push
git add .
git commit -m "Add new feature"
git push -u origin feature/my-new-feature

# 4. Create PR on GitHub (dev ← feature)
```

### After Feature Complete

```bash
# 1. Ensure feature is merged to dev
git checkout dev
git pull origin dev

# 2. Verify changes are there
git log --oneline -5
```

---

## PR Approval Process

### Who Can Approve?

- Any team member with write access to the repository
- At least **1 approval** required for `test` and `master` merges
- Self-approvals are allowed (but discouraged for critical changes)

### Approval Checklist

Before approving a PR to `test` or `master`, reviewers should check:

- [ ] Code changes are clear and well-documented
- [ ] Tests pass (if applicable)
- [ ] CI/CD checks pass
- [ ] For `test` PRs: Model performance is maintained or improved
- [ ] For `master` PRs: Deployment configuration is correct
- [ ] No breaking changes (or properly documented)
- [ ] Documentation updated if needed

---

## Common Scenarios

### Scenario 1: Hotfix to Production

If you need to fix a critical bug in production:

```bash
# 1. Create hotfix from master
git checkout master
git pull origin master
git checkout -b hotfix/critical-fix

# 2. Make fix, commit, push
git add .
git commit -m "Fix critical bug"
git push -u origin hotfix/critical-fix

# 3. Create PR directly to master (bypasses test)
#    - Still requires approval
#    - CI will run deployment checks
```

### Scenario 2: Sync Branches

If branches get out of sync:

```bash
# Sync dev with master
git checkout dev
git pull origin master
git push origin dev

# Sync test with dev
git checkout test
git pull origin dev
git push origin test
```

### Scenario 3: Revert a Merge

If you need to revert a merge:

```bash
# Find the merge commit
git log --oneline --merges

# Revert it
git revert -m 1 <merge-commit-hash>
git push origin <branch-name>
```

---

## Best Practices

1. **Always start from the correct branch:**
   - Features: Start from `dev`
   - Hotfixes: Start from `master`

2. **Keep branches up to date:**
   - Regularly pull latest changes
   - Rebase feature branches before creating PR

3. **Write clear commit messages:**
   - Use present tense: "Add feature" not "Added feature"
   - Be descriptive but concise

4. **Keep PRs small:**
   - One feature/fix per PR
   - Easier to review and test

5. **Delete merged branches:**
   - Clean up after merge
   - Keeps repository organized

---

## Troubleshooting

### PR is blocked by branch protection

**Issue:** Cannot merge because branch protection rules block it

**Solution:**
- Ensure all required status checks pass
- Get required number of approvals
- Resolve any conversations/threads

### Cannot push to protected branch

**Issue:** Direct push to `test` or `master` is blocked

**Solution:**
- This is intentional! Use PRs instead
- Create a feature branch and PR

### CI checks are failing

**Issue:** PR cannot merge because CI fails

**Solution:**
- Check CI logs for errors
- Fix issues in your branch
- Push new commits (CI will re-run)

---

## Summary

✅ **Feature → Dev:** No approval needed, CI checks required  
✅ **Dev → Test:** 1 approval required, model validation  
✅ **Test → Master:** 1 approval required, deployment checks  

**Remember:** All work starts on feature branches, never commit directly to `dev`, `test`, or `master`!

---

**Last Updated:** Phase III - Step 5.1 & 5.3 Setup

