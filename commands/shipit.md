---
description: Ship it - run remaining workflow steps to ship code to prod
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Task, mcp__github__create_pull_request, mcp__github__get_me, mcp__github__list_pull_requests, mcp__github__merge_pull_request, mcp__github__pull_request_read
---

# Ship It

Assess what's already been done and complete the remaining workflow steps to ship code to production.

**Argument (optional):** $ARGUMENTS
- `--skip-prod-test` - Skip the production functionality test at the end
- `--dry-run` - Show what would be done without executing

## Overview

This command picks up where previous work left off and runs the remaining steps:
1. `/test` - Run tests (if not already passing)
2. `/test-review` - Assess test quality and coverage (if not done)
3. `/docs-review` - Update documentation (if not done)
4. `/coderabbit` - Run CodeRabbit review and fix issues (if not done)
5. **Bump version** - Increment version in project config (if applicable)
6. `/pr` - Create PR (if not created)
7. Merge PR once CI checks pass
8. Wait for production deployment workflow
9. Verify production health
10. Test new functionality in production (if safe)

## Instructions

### Step 1: Assess Current State

First, gather information about what's already been done:

```bash
# Check current branch
BRANCH=$(git branch --show-current)
echo "Current branch: $BRANCH"

# Check if we're on a feature branch
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "ERROR: On main branch - nothing to finish"
  exit 1
fi

# Check for uncommitted changes
git status --porcelain

# Check commits ahead of main
git log --oneline main..HEAD 2>/dev/null | head -10

# Check recent commit messages for evidence of completed steps
git log --oneline -20 | grep -iE "(test|coderabbit|review|fix:|docs)" || echo "No relevant commits found"
```

### Step 2: Check for Existing PR

```bash
# Get repo info
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')

# Check if PR already exists for this branch
gh pr list --head "$BRANCH" --json number,title,state,url
```

If PR exists:
- Note the PR number and URL
- Skip to Step 6 (merge/deployment) unless PR is still draft

### Step 3: Create Progress Checklist

Create a mental checklist based on evidence found:

```
## Workflow Progress Assessment

### Already Done
- [x/partial/?] Tests run - Evidence: [git log shows test fixes / no evidence]
- [x/partial/?] Test review - Evidence: [test files added/improved / coverage report / no evidence]
- [x/partial/?] Docs reviewed - Evidence: [docs files changed / no evidence]
- [x/partial/?] CodeRabbit review - Evidence: [commit mentioning coderabbit / no evidence]
- [?] PR created - Evidence: [PR exists / no PR found]

### Remaining Steps
1. [list steps still needed]
```

### Step 4: Execute Remaining Pre-PR Steps

For each step not yet completed, execute in order:

**If tests not verified:**
```
Run /test skill
```
- If tests fail, fix issues and re-run
- Continue only when tests pass

**If test review not done:**
```
Run /test-review skill
```
- Assess test quality and coverage (target 70%+)
- Add missing critical tests (P0/P1 items)
- Commit any new tests

**If docs not reviewed:**
```
Run /docs-review skill
```
- Make any needed documentation updates
- Commit changes

**If CodeRabbit not done:**
```
Run /coderabbit skill
```
- Fix issues found (max 3 cycles)
- Commit fixes

### Step 5: Bump Version (if applicable)

Before creating the PR, check if the project has a version to bump:

```bash
# Check for common version files
VERSION_FILE=""

if [ -f "pyproject.toml" ]; then
  VERSION_FILE="pyproject.toml"
  CURRENT_VERSION=$(grep -E '^version\s*=' pyproject.toml | head -1 | sed 's/.*=\s*"\(.*\)"/\1/')
  echo "Found pyproject.toml with version: $CURRENT_VERSION"
elif [ -f "package.json" ]; then
  VERSION_FILE="package.json"
  CURRENT_VERSION=$(grep '"version"' package.json | head -1 | sed 's/.*: "\(.*\)".*/\1/')
  echo "Found package.json with version: $CURRENT_VERSION"
elif [ -f "Cargo.toml" ]; then
  VERSION_FILE="Cargo.toml"
  CURRENT_VERSION=$(grep -E '^version\s*=' Cargo.toml | head -1 | sed 's/.*=\s*"\(.*\)"/\1/')
  echo "Found Cargo.toml with version: $CURRENT_VERSION"
fi

if [ -z "$VERSION_FILE" ]; then
  echo "No version file found - skipping version bump"
fi
```

If a version file is found:
1. Analyze the changes to determine bump type:
   - **Patch** (0.0.X): Bug fixes, minor changes, docs updates
   - **Minor** (0.X.0): New features, non-breaking changes
   - **Major** (X.0.0): Breaking changes (rare, usually explicit)

2. Increment the version appropriately (default to patch for most changes)

3. Update the version file:
```bash
# Example for pyproject.toml - adjust pattern for other files
# Increment patch version: 1.2.3 -> 1.2.4
NEW_VERSION=$(echo "$CURRENT_VERSION" | awk -F. '{print $1"."$2"."$3+1}')
sed -i '' "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" "$VERSION_FILE"
echo "Bumped version: $CURRENT_VERSION -> $NEW_VERSION"
```

4. Commit the version bump:
```bash
git add "$VERSION_FILE"
git commit -m "chore: bump version to $NEW_VERSION"
```

**Skip version bump if:**
- No version file exists
- Changes are docs-only (no code changes)
- Version was already bumped in this branch

### Step 6: Create PR (if not exists)

If no PR exists yet:
```
Run /pr skill
```

Get the PR number for next steps:
```bash
PR_NUMBER=$(gh pr list --head "$BRANCH" --json number -q '.[0].number')
echo "PR #$PR_NUMBER created"
```

### Step 7: Wait for CI and Merge

Monitor CI checks:
```bash
# Watch CI status (check every 30 seconds, timeout after 10 minutes)
PR_NUMBER=$(gh pr list --head "$BRANCH" --json number -q '.[0].number')

echo "Waiting for CI checks on PR #$PR_NUMBER..."
for i in {1..20}; do
  STATUS=$(gh pr checks "$PR_NUMBER" --json state -q '.[].state' | sort | uniq)
  echo "Check status: $STATUS"

  if echo "$STATUS" | grep -q "FAILURE"; then
    echo "CI checks failed!"
    gh pr checks "$PR_NUMBER"
    exit 1
  fi

  if [ "$STATUS" = "SUCCESS" ]; then
    echo "All CI checks passed!"
    break
  fi

  if [ $i -eq 20 ]; then
    echo "Timeout waiting for CI. Current status:"
    gh pr checks "$PR_NUMBER"
    exit 1
  fi

  sleep 30
done
```

Merge the PR:
```bash
# Merge with squash (adjust merge method if project prefers different)
gh pr merge "$PR_NUMBER" --squash --delete-branch

echo "PR #$PR_NUMBER merged successfully"
```

### Step 8: Wait for Production Deployment

Look for deployment workflow and wait for it:
```bash
# Get the merge commit SHA
MERGE_SHA=$(gh pr view "$PR_NUMBER" --json mergeCommit -q '.mergeCommit.oid')

# Find and wait for deployment workflow
echo "Waiting for production deployment..."

# Check for common deployment workflow names
for i in {1..30}; do
  # Look for workflow runs triggered by the merge
  DEPLOY_RUN=$(gh run list --branch main --limit 5 --json databaseId,status,conclusion,name,headSha \
    -q ".[] | select(.headSha == \"$MERGE_SHA\" or .name | test(\"deploy|prod|release\"; \"i\"))")

  if [ -n "$DEPLOY_RUN" ]; then
    RUN_ID=$(echo "$DEPLOY_RUN" | head -1 | jq -r '.databaseId')
    STATUS=$(gh run view "$RUN_ID" --json status,conclusion -q '.status')
    CONCLUSION=$(gh run view "$RUN_ID" --json status,conclusion -q '.conclusion')

    echo "Deployment workflow status: $STATUS ($CONCLUSION)"

    if [ "$STATUS" = "completed" ]; then
      if [ "$CONCLUSION" = "success" ]; then
        echo "Deployment completed successfully!"
        break
      else
        echo "Deployment failed with conclusion: $CONCLUSION"
        gh run view "$RUN_ID" --log-failed | tail -50
        exit 1
      fi
    fi
  fi

  if [ $i -eq 30 ]; then
    echo "Timeout waiting for deployment. Check GitHub Actions manually."
    gh run list --branch main --limit 5
    break
  fi

  sleep 20
done
```

### Step 9: Verify Production Health

Check production is healthy:
```bash
# Look for production URL in docs or common locations
PROD_URL=""

# Try to find production URL from project docs
if [ -f "docs/README.md" ]; then
  PROD_URL=$(grep -oE 'https://[a-zA-Z0-9.-]+\.(com|app|dev|io)[^)]*' docs/README.md | head -1)
fi

if [ -z "$PROD_URL" ] && [ -f "CLAUDE.md" ]; then
  PROD_URL=$(grep -oE 'https://[a-zA-Z0-9.-]+\.(com|app|dev|io)[^)]*' CLAUDE.md | head -1)
fi

if [ -n "$PROD_URL" ]; then
  echo "Checking production health: $PROD_URL"

  # Basic health check
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$PROD_URL" --max-time 10)

  if [ "$HTTP_STATUS" = "200" ]; then
    echo "Production is healthy (HTTP $HTTP_STATUS)"
  else
    echo "WARNING: Production returned HTTP $HTTP_STATUS"
  fi

  # Check for health endpoint
  HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${PROD_URL}/health" --max-time 5 2>/dev/null || echo "N/A")
  if [ "$HEALTH_STATUS" = "200" ]; then
    echo "Health endpoint OK"
  fi
else
  echo "Could not determine production URL - skipping health check"
  echo "Please verify production manually"
fi
```

### Step 10: Test New Functionality in Production

**IMPORTANT:** Only test if it's safe to do so (read-only operations, test data, etc.)

If $ARGUMENTS contains `--skip-prod-test`, skip this step.

Otherwise, analyze the changes made and determine if production testing is safe:

1. Review what was changed:
```bash
git log --oneline main~5..main~1 | head -5
git diff --stat main~2..main~1
```

2. Categorize the change:
   - **Safe to test:** New read-only endpoints, UI changes, display fixes
   - **Test with caution:** New features that create data (use test data)
   - **Do not auto-test:** Destructive operations, payment flows, auth changes

3. If safe, perform basic verification:
   - Hit new endpoints with curl
   - Describe manual verification steps for UI changes
   - Note what the user should manually verify

### Step 11: Final Report

Provide a comprehensive summary:

```
## Finish Summary

### Workflow Steps Completed
- [x] Tests: Passed (X tests, Y% coverage)
- [x] Test review: Coverage at X%, N tests added
- [x] Docs: Updated docs/README.md
- [x] CodeRabbit: Reviewed, N issues fixed
- [x] Version: Bumped X.Y.Z -> X.Y.Z+1 (or "skipped - docs only" / "N/A - no version file")
- [x] PR: #123 created and merged
- [x] Deployment: Workflow completed successfully
- [x] Health check: Production responding (HTTP 200)
- [x] Prod test: [description or "skipped"]

### PR Details
- **URL:** https://github.com/org/repo/pull/123
- **Merged at:** [timestamp]
- **Deployment:** https://github.com/org/repo/actions/runs/XXX

### Production Status
- **URL:** https://your-app.com
- **Health:** Healthy
- **New functionality:** [verified/needs manual verification]

### Manual Verification Needed
- [List any items that need manual verification]

### Notes
- [Any observations or warnings]
```

## Error Handling

If any step fails:
1. Stop execution
2. Report what failed and why
3. Suggest remediation steps
4. Ask if user wants to retry or skip

Common issues:
- **CI fails:** Show failed checks, offer to investigate
- **Merge conflicts:** Show conflicts, ask user to resolve
- **Deployment fails:** Show logs, suggest rollback if needed
- **Health check fails:** Alert user, suggest investigation

## Safety Guards

- Never force-push or use destructive git operations
- Never merge if CI checks are failing
- Never auto-test destructive operations in prod
- Always wait for deployment to complete before health check
- Timeout all long-running operations

## Dry Run Mode

If `--dry-run` is in $ARGUMENTS:
1. Assess current state
2. List all steps that would be executed
3. Do not execute any commands that modify state
4. Report what would happen

## Related Commands

| Command | Purpose |
|---------|---------|
| `/test` | Run tests independently |
| `/test-review` | Assess test quality and coverage |
| `/docs-review` | Review docs independently |
| `/coderabbit` | Run CodeRabbit review independently |
| `/pr` | Create PR independently |
| `/cleanup` | Clean up current worktree after merge |
