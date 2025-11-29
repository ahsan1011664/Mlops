# Branch Protection Setup Guide

This guide walks you through setting up branch protection rules on GitHub to enforce PR approvals and CI/CD checks.

---

## Prerequisites

- Admin access to the GitHub repository
- Branches `dev`, `test`, and `master` must exist (see `scripts/setup_branches.sh` or `.ps1`)

---

## Step-by-Step Setup

### 1. Navigate to Branch Protection Settings

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. Click **Branches** (left sidebar)
4. You'll see "Branch protection rules" section

---

## 2. Set Up Protection for `test` Branch

### Create Rule

1. Click **Add rule** button
2. In "Branch name pattern", enter: `test`
3. Click **Create** (or configure settings first)

### Configure Settings

Enable the following options:

#### ✅ Require a pull request before merging
- **Require approvals:** Set to **1**
- ✅ **Dismiss stale pull request approvals when new commits are pushed**
- ✅ **Require review from Code Owners** (optional, if you have CODEOWNERS file)

#### ✅ Require status checks to pass before merging
- **Require branches to be up to date before merging:** ✅ Enabled
- In "Status checks that are required", add:
  - `CI - Dev to Test (Model Retraining + CML)` (once workflow is created)
  - Or any other required checks

#### ✅ Require conversation resolution before merging
- Ensures all PR comments are addressed

#### ✅ Do not allow bypassing the above settings
- Prevents admins from bypassing rules (recommended)

#### ⚠️ Restrict who can push to matching branches
- Leave unchecked (we want PRs, not direct pushes)

### Save Rule

Click **Create** or **Save changes**

---

## 3. Set Up Protection for `master` Branch

### Create Rule

1. Click **Add rule** button again
2. In "Branch name pattern", enter: `master`
3. Click **Create**

### Configure Settings

Enable the following options:

#### ✅ Require a pull request before merging
- **Require approvals:** Set to **1**
- ✅ **Dismiss stale pull request approvals when new commits are pushed**
- ✅ **Require review from Code Owners** (optional)

#### ✅ Require status checks to pass before merging
- **Require branches to be up to date before merging:** ✅ Enabled
- In "Status checks that are required", add:
  - `CD - Test to Master (Production Deployment)` (once workflow is created)
  - Or any other required checks

#### ✅ Require conversation resolution before merging

#### ✅ Include administrators
- **Important:** Even admins must follow these rules

#### ✅ Do not allow bypassing the above settings

### Save Rule

Click **Create** or **Save changes**

---

## 4. Optional: Set Up Protection for `dev` Branch

### Create Rule

1. Click **Add rule** button
2. In "Branch name pattern", enter: `dev`
3. Click **Create**

### Configure Settings

Enable the following (lighter restrictions):

#### ✅ Require status checks to pass before merging
- **Require branches to be up to date before merging:** ✅ Enabled
- In "Status checks that are required", add:
  - `CI - Feature to Dev` (once workflow is created)

#### ⚠️ Do NOT require approvals (dev is for integration)

#### ⚠️ Do NOT restrict pushes (allows faster iteration)

### Save Rule

Click **Create** or **Save changes**

---

## Verification

### Test Branch Protection

1. Create a test feature branch:
   ```bash
   git checkout -b test/branch-protection
   ```

2. Make a small change and push:
   ```bash
   echo "# Test" >> README.md
   git add README.md
   git commit -m "Test branch protection"
   git push -u origin test/branch-protection
   ```

3. Try to create PR to `test` or `master`:
   - You should see that approvals are required
   - Direct push to protected branch should be blocked

4. Clean up:
   ```bash
   git checkout dev
   git branch -D test/branch-protection
   git push origin --delete test/branch-protection
   ```

---

## Visual Guide

### Branch Protection Rule Configuration

```
Branch name pattern: test
                    ┌─────────────────────────────┐
                    │ Require a pull request      │ ✓
                    │   Require approvals: 1      │
                    │   Dismiss stale approvals   │ ✓
                    ├─────────────────────────────┤
                    │ Require status checks       │ ✓
                    │   Require up to date        │ ✓
                    │   Required checks:          │
                    │     - CI - Dev to Test      │
                    ├─────────────────────────────┤
                    │ Require conversation        │ ✓
                    │   resolution                │
                    ├─────────────────────────────┤
                    │ Do not allow bypassing      │ ✓
                    └─────────────────────────────┘
```

---

## Troubleshooting

### "No status checks found"

**Issue:** Status checks dropdown is empty

**Solution:**
- This is normal if GitHub Actions workflows haven't run yet
- Create a test PR to trigger workflows
- After workflows run, status checks will appear
- You can then add them to branch protection rules

### "Cannot push to protected branch"

**Issue:** Direct push is blocked

**Solution:**
- This is intentional! Use feature branches and PRs
- If you need to push (emergency), temporarily disable protection
- Re-enable immediately after

### "PR requires approval but no reviewers available"

**Issue:** No team members to approve

**Solution:**
- Add team members as collaborators
- Or temporarily reduce required approvals to 0 (not recommended)
- Or use CODEOWNERS file to auto-assign reviewers

---

## Advanced: CODEOWNERS File

Create `.github/CODEOWNERS` to auto-assign reviewers:

```
# Default reviewers for all files
* @username1 @username2

# Specific reviewers for critical paths
/dags/ @mlops-team
/api/ @mlops-team
/.github/workflows/ @mlops-team
```

This ensures PRs are automatically assigned to the right reviewers.

---

## Summary

✅ **test branch:** Requires 1 approval + CI checks  
✅ **master branch:** Requires 1 approval + deployment checks  
✅ **dev branch:** CI checks only (no approval required)  

**Remember:** These rules enforce code quality and prevent accidental deployments!

---

**Last Updated:** Phase III - Step 5.1 & 5.3 Setup

