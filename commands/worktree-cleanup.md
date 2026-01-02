---
description: Maintain git worktrees - identify merged PRs for cleanup
allowed-tools: Read, Glob, Grep, Bash, mcp__github__list_pull_requests, mcp__github__pull_request_read, mcp__github__get_me, mcp__github__search_pull_requests, AskUserQuestion
---

# Git Worktree Maintenance

Clean up git worktrees for merged PRs and organize outstanding work.

## When to Use

- Periodically to clean up merged work
- When disk space is getting low
- To get an overview of outstanding work across worktrees

## Instructions

### 1. List All Worktrees

```bash
git worktree list
```

### 2. Get Repository Info

```bash
git remote get-url origin
```
Parse the owner/repo from the URL.

### 3. Get PR Status for Each Branch

For each worktree (excluding main):
- Use `gh pr list --state all --limit 50 --json number,title,headRefName,state,mergedAt` or GitHub MCP tools
- Match each worktree branch to its PR
- Categorize: MERGED (can cleanup), OPEN (keep), NO PR (investigate)

### 4. Categorize Worktrees

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

### 5. Present Findings

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

### 6. Ask User for Action

Use AskUserQuestion to ask:
- Clean up all merged worktrees?
- Rename generic worktree names?
- Investigate worktrees with no PR?

### 7. Execute Cleanup

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

### 8. Final Verification

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
