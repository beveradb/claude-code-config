---
description: Tidy all worktrees - review and clean up across all worktrees (interactive)
allowed-tools: Read, Glob, Grep, Bash, mcp__github__list_pull_requests, mcp__github__pull_request_read, mcp__github__get_me, mcp__github__search_pull_requests, AskUserQuestion
---

# Tidy All Worktrees

Review all git worktrees, identify merged PRs for cleanup, and organize outstanding work.

**Note:** This is an interactive maintenance command for periodic use. For quick cleanup of the current worktree after merging, use `/cleanup` instead.

## When to Use

- Periodically to clean up multiple merged worktrees at once
- When disk space is getting low
- To get an overview of outstanding work across all worktrees
- When you want to rename or reorganize worktrees

## Instructions

### 1. Refresh All Read-Only Mirrors (run first)

Before auditing worktrees, ensure every read-only mirror is clean and current and the
dev mirrors exist. The workspace root clone is never touched.

```bash
ROOT="$(pwd)"
while [ "$ROOT" != "/" ] && [ -z "$(ls -d "$ROOT"/*-main-readonly 2>/dev/null)" ]; do
  ROOT="$(dirname "$ROOT")"
done
bash "$ROOT/docs/archive/scripts/refresh-mirrors.sh"
```

### 2. List All Worktrees

```bash
git worktree list
```

### 3. Get Repository Info

```bash
git remote get-url origin
```
Parse the owner/repo from the URL.

### 4. Get PR Status for Each Branch

For each worktree (excluding main):
- Use `gh pr list --state all --limit 50 --json number,title,headRefName,state,mergedAt` or GitHub MCP tools
- Match each worktree branch to its PR
- Categorize: MERGED (can cleanup), OPEN (keep), NO PR (investigate)

### 5. Categorize Worktrees

**Can be cleaned up (PRs merged):**
- Worktrees where the associated PR has been merged
- Safe to remove with `git worktree remove <path>`

**Outstanding/WIP (keep):**
- Worktrees with open PRs
- Check if worktree name is descriptive or generic
- Generic patterns: `sess-YYYYMMDD-*`, `work-*`, `session-*`
- For generic names, read PR title to suggest better name

**No PR found:**
- Flag for user attention
- May be abandoned or local-only work

### 6. Present Findings

Show a summary:
```
## Worktree Status Report

### Can be cleaned up (merged PRs):
| Worktree Path | Branch | PR # | Merged Date |
|---------------|--------|------|-------------|

### Outstanding PRs (keep):
| Worktree Path | Branch | PR # | PR Title | Rename Suggestion |
|---------------|--------|------|----------|-------------------|

### No PR found:
| Worktree Path | Branch | Last Commit | Notes |
|---------------|--------|-------------|-------|

### Main worktree:
[path] - never remove
```

### 7. Ask User for Action

Use AskUserQuestion to ask:
- Clean up all merged worktrees?
- Rename generic worktree names?
- Investigate worktrees with no PR?

### 8. Execute Cleanup

If user approves:

**Removing merged worktrees:**
```bash
# Check for uncommitted changes first
cd <worktree-path> && git status --porcelain
# If clean:
git worktree remove <path>
# If changes exist, warn user
```

**Renaming worktrees:**
```bash
# Move the directory
mv <old-path> <new-path>
# Repair worktree references
git worktree repair <new-path>
# Clean up stale entries
git worktree prune
```

**Pruning stale entries:**
```bash
git worktree prune
```

### 9. Final Verification

```bash
git worktree list
```

## Important Rules

- **Never remove the main worktree**
- Always check for uncommitted changes before removing
- If worktree has unmerged changes, offer to create a PR first
- Generic name patterns to watch for:
  - `sess-YYYYMMDD-*` (from /new-worktree)
  - `work-*`, `session-*`, `temp-*`
  - Names without descriptive keywords
- Good names reflect the work: `fix-auth-flow`, `add-export-feature`

## Integration with /new-worktree

Worktrees created with `/new-worktree` use the pattern:
- Branch: `feat/sess-YYYYMMDD-HHMM-description`
- Folder: `../<repo>-description`

When suggesting renames, keep the folder name short and descriptive.
