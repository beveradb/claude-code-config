---
description: Fix accidental changes in main worktree (should always be clean)
allowed-tools: Bash, Read, Glob, AskUserQuestion
---

# Fix Main Worktree

The main worktree should always be clean - all work happens in feature worktrees created with `/start`. This command helps identify and fix accidental changes in main.

## Instructions

### Step 1: Check for Changes in Main

First, verify we're in the main worktree and check for uncommitted changes:

```bash
# Verify we're in main worktree (not a feature worktree)
git rev-parse --abbrev-ref HEAD

# Check for any changes
git status --porcelain
```

If there are no changes, respond:
```
Main worktree is clean. Nothing to fix.
```
Then stop.

### Step 2: Show the Changes

Display what files are modified:

```bash
git status
git diff HEAD --stat
```

For each modified file, show a brief summary of the changes.

### Step 3: List All Worktrees

Get all worktrees for this repo:

```bash
git worktree list
```

Identify all feature worktrees (exclude main).

### Step 4: Check Each Modified File Against Other Worktrees

For each modified file in main, check if the same changes exist in other worktrees:

```bash
# For each modified file, check each worktree:
# 1. Check if file has been modified there (git diff)
# 2. Check if file has commits involving it (git log --oneline -5 -- <file>)
# 3. Compare the actual content to see if changes are identical
```

Categorize each file as:
- **Duplicate**: Changes already committed in another worktree (can be safely discarded)
- **Orphaned**: Changes not found elsewhere (need to be moved to the right place)
- **Conflicting**: Different changes in another worktree (needs manual resolution)

### Step 5: Report Findings

Present a summary:

```
## Main Worktree Analysis

### Modified Files

| File | Status | Found In |
|------|--------|----------|
| path/to/file.tsx | Duplicate | worktree-name (commit abc123) |
| path/to/other.ts | Orphaned | Not found |

### Recommended Actions

**Duplicates (safe to discard):**
- file.tsx - already in worktree-name

**Orphaned (need attention):**
- other.ts - likely belongs in worktree-xyz based on [reason]
```

### Step 6: Handle Based on Status

**For Duplicates:**
Ask user to confirm, then discard:
```bash
git checkout -- <file1> <file2> ...
```

**For Orphaned Changes:**
1. Try to identify which worktree likely made this change based on:
   - Worktree names matching the file's purpose
   - Recent commits in worktrees touching similar files
   - Worktree creation dates

2. Prepare a message for the user to paste into the relevant agent session:

```
## Message for Agent Session

Paste this into the agent working on [worktree-name]:

---
Some changes were accidentally made in the main worktree instead of this one:

Files:
- path/to/file.ts

These changes need to be moved here. Please:
1. Check if you already have these changes locally (committed or uncommitted)
2. If not, I'll provide the diff for you to apply here
3. Confirm when done so I can clean up main

Here's the diff:
[include git diff output]
---
```

**For Conflicting Changes:**
Present both versions and ask the user which to keep.

### Step 7: Verify Clean

After all actions, verify main is clean:

```bash
git status
```

Report final status.

## Examples

### Example 1: Duplicate Changes (Common Case)
```
The file frontend/components/JobCard.tsx was modified in main, but the exact
same changes are already committed in karaoke-gen-consolidate-frontends
(commit 8d537826).

This is safe to discard. Run:
  git checkout -- frontend/components/JobCard.tsx
```

### Example 2: Orphaned Changes
```
The file backend/api/routes.py was modified in main but not found in any
worktree. Based on the changes (adding a new /export endpoint), this likely
belongs in karaoke-gen-export-feature.

I've prepared a message for you to paste into that session.
```

## Notes

- This situation usually happens when an agent working in a feature worktree accidentally edits files in main (often due to path confusion)
- Most often, the changes are duplicates that can be discarded
- If changes are orphaned, they need to be manually moved to the right worktree
- Always verify main is clean at the end
