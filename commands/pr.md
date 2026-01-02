---
description: Create a PR after running review (includes @coderabbitai ignore)
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, mcp__github__create_pull_request, mcp__github__get_me, mcp__github__list_pull_requests
---

# Create Pull Request

Create a PR after ensuring code quality with local review.

**Argument (optional):** PR title or description: $ARGUMENTS

## Prerequisites

- You should be on a feature branch (not main)
- Changes should be committed
- Review should be complete (run `/review` first if not done)

## Instructions

### Step 1: Verify Branch State

```bash
# Check current branch
git branch --show-current

# Ensure we're not on main
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "ERROR: Cannot create PR from main branch"
  exit 1
fi

# Check for commits ahead of main
git log --oneline main..HEAD
```

If no commits ahead of main, tell user there's nothing to PR.

### Step 2: Check if Review Was Done

Look for recent review-related commits:
```bash
git log --oneline -5 | grep -i "coderabbit\|review\|fix:"
```

If no evidence of review, suggest running `/review` first. Ask user if they want to:
1. Run `/review` now
2. Skip review and create PR anyway

### Step 3: Ensure Branch is Pushed

```bash
# Push branch to origin
git push -u origin $(git branch --show-current)
```

### Step 4: Generate PR Content

Analyze the changes:
```bash
# Get all commits for this branch
git log --oneline main..HEAD

# Get diff summary
git diff --stat main..HEAD
```

Create PR title and body:
- Title: Brief summary (or use $ARGUMENTS if provided)
- Body: Must include `@coderabbitai ignore` to prevent automatic review

### Step 5: Create the PR

Use the GitHub MCP tool or gh CLI:

```bash
gh pr create --title "TITLE" --body "$(cat <<'EOF'
## Summary
[2-3 bullet points describing the changes]

## Changes
- [List of specific changes]

## Testing
- [ ] Tests pass locally (`make test` or equivalent)
- [ ] Manual testing completed

## Review
- [x] CodeRabbit CLI review completed locally
- [x] Issues addressed

@coderabbitai ignore

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**CRITICAL:** The `@coderabbitai ignore` line prevents automatic CodeRabbit review since we already did it locally.

### Step 6: Report Success

Provide:
- PR URL
- PR number
- Summary of what's in the PR

## PR Description Template

```markdown
## Summary
[Brief description of what this PR does]

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Review
- [x] Local CodeRabbit review completed
- [x] Review feedback addressed

@coderabbitai ignore

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Why @coderabbitai ignore?

We use the CodeRabbit CLI locally before creating the PR because:
1. **Efficiency:** No waiting for GitHub webhook → review → fetch via API
2. **Cost:** Avoids hitting CodeRabbit free tier rate limits
3. **Context:** Review output goes directly to Claude, not through GitHub API
4. **Speed:** Issues fixed before PR, not after

## Related Commands

| Command | Purpose |
|---------|---------|
| `/review` | Run CodeRabbit CLI review locally |
| `/test` | Run tests before PR |
| `/docs-review` | Check if docs need updates |
