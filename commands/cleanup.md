---
description: Clean up current worktree after PR is merged
allowed-tools: Read, Glob, Bash, AskUserQuestion
---

# Cleanup Current Worktree

Clean up the current worktree after its PR has been merged. This is the quick end-of-session cleanup.

**Note:** For reviewing and cleaning up multiple worktrees at once, use `/tidy-all-worktrees` instead.

## When to Use

- At the end of a session after `/shipit` has merged your PR
- When you're done with a feature branch and want to clean up

## Instructions

### Step 1: Verify Current State

```bash
# Get current branch and worktree info
BRANCH=$(git branch --show-current)
WORKTREE_PATH=$(pwd)

echo "Current branch: $BRANCH"
echo "Worktree path: $WORKTREE_PATH"

# Check if we're in a worktree (not the main repo)
git worktree list
```

**Safety check:** If on `main` or `master` branch, STOP and warn the user - this command is for cleaning up feature worktrees, not the main repo.

### Step 2: Check if PR is Merged

```bash
# Check if there's a merged PR for this branch
gh pr list --head "$BRANCH" --state merged --json number,title,mergedAt
```

If no merged PR found:
- Check if PR exists but is still open: `gh pr list --head "$BRANCH" --state open`
- If PR is open, warn user and ask if they want to proceed anyway
- If no PR at all, warn user this branch may have unmerged work

### Step 3: Check for Uncommitted Changes (CRITICAL)

**This step is essential - do not skip it.**

```bash
# Check for any uncommitted changes
git status --porcelain
```

**If there are uncommitted changes:**

1. **List what's there:**
   ```bash
   git status
   ```

2. **Categorize the files:**
   - **Generated/build artifacts** (node_modules, __pycache__, .pyc, dist/, build/, etc.) - safe to discard
   - **IDE/editor files** (.idea/, .vscode/settings.json, *.swp) - usually safe to discard
   - **Log files** (*.log) - usually safe to discard
   - **Actual code changes** (.py, .ts, .js, etc.) - REVIEW CAREFULLY
   - **Config changes** - may be important, review

3. **For actual code or config changes:**
   - Show the diff: `git diff <file>`
   - Assess if this looks like:
     - Leftover debug code (safe to discard)
     - Incomplete work that should be preserved
     - Important changes that were missed in the PR

4. **Ask the user** if unsure about any files using AskUserQuestion:
   - "I found uncommitted changes in [files]. These appear to be [assessment]. Should I discard them, or would you like to review?"

5. **Only proceed with cleanup after resolving uncommitted files**

### Step 4: Switch to a safe dir and refresh all mirrors

Leave the worktree being removed, then refresh every read-only mirror (main + dev
for product repos) so local `dev`/`main` are clean and current. The workspace root
clone is never touched.

```bash
# Move out of the worktree we're about to remove
MAIN_WORKTREE=$(git worktree list | grep -E '\[main\]|\[master\]' | awk '{print $1}')
cd "$MAIN_WORKTREE"

# Workspace root = parent of any *-main-readonly clone
ROOT="$(pwd)"
while [ "$ROOT" != "/" ] && [ -z "$(ls -d "$ROOT"/*-main-readonly 2>/dev/null)" ]; do
  ROOT="$(dirname "$ROOT")"
done
bash "$ROOT/docs/archive/scripts/refresh-mirrors.sh"
```

### Step 5: Remove the Worktree

```bash
# Remove the worktree
git worktree remove "$WORKTREE_PATH"

# Prune any stale worktree references
git worktree prune

# Delete the remote branch if it still exists
git push origin --delete "$BRANCH" 2>/dev/null || echo "Remote branch already deleted"

# Delete local branch reference
git branch -d "$BRANCH" 2>/dev/null || echo "Local branch already deleted"
```

### Step 6: Confirm Cleanup

```bash
# Show remaining worktrees
git worktree list
```

Report:
```
## Cleanup Complete

- Removed worktree: [path]
- Deleted branch: [branch name]
- PR #[number] was merged on [date]

Remaining worktrees:
[list]
```

## Handling Edge Cases

### Uncommitted changes that look important
If you find code changes that seem significant:
1. Do NOT proceed with cleanup
2. Show the user what you found
3. Ask if they want to:
   - Commit these changes to a new branch
   - Discard them
   - Abort cleanup entirely

### PR not merged
If the PR isn't merged:
1. Warn the user clearly
2. Ask if they want to:
   - Wait and merge the PR first
   - Force cleanup anyway (with confirmation)
   - Abort

### Worktree removal fails
If `git worktree remove` fails:
```bash
# Try with force if appropriate (only after user confirms)
git worktree remove --force "$WORKTREE_PATH"
```

## Safety Rules

- **Never clean up the main worktree**
- **Always check for uncommitted changes first**
- **Review code changes, don't blindly discard**
- **Confirm PR is merged before cleanup**
- **When in doubt, ask the user**

## Related Commands

| Command | Purpose |
|---------|---------|
| `/shipit` | Complete the shipping workflow (ends with merge) |
| `/tidy-all-worktrees` | Review and clean up all worktrees at once |
| `/new-worktree` | Create a new worktree for fresh work |
