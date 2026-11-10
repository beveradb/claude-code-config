---
description: Run a local Superpowers code review and fix issues before PR
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Skill, Task
---

# Code Review (Superpowers)

Run a local code review and fix any issues before creating a PR, using the **Superpowers code review** (`superpowers:requesting-code-review`), which dispatches a code-reviewer subagent locally with no external dependency.

> The command keeps the name `/coderabbit` so `/pr`, `/shipit`, and other workflow commands that reference it keep working. The CodeRabbit CLI is no longer used.

**Argument (optional):** $ARGUMENTS
- `uncommitted` - review working changes (default if nothing committed)
- `committed` - review committed changes vs main (default if commits exist)

## Instructions

### Step 1: Determine What to Review

```bash
git status --porcelain
git log --oneline main..HEAD 2>/dev/null | head -5
```

If `$ARGUMENTS` specifies `committed` or `uncommitted`, use that. Otherwise:
- Commits ahead of main → `committed`
- Only uncommitted changes → `uncommitted`
- Nothing to review → tell user and stop

Record this as `$REVIEW_TYPE` for the remainder of the command.

### Step 2: Run Superpowers Review

Invoke the Superpowers code review skill:

```
Skill: superpowers:requesting-code-review
```

Give the skill the review scope so it crafts the right context for its reviewer subagent:
- Base: `main`. Diff command by scope:
  - `committed` → `git diff main..HEAD` (and `git log --oneline main..HEAD` for commit messages)
  - `uncommitted` → `git diff` and `git diff --staged`, plus new untracked files (`git ls-files --others --exclude-standard`) — read those in full, since they don't appear in either diff
- Ask for findings grouped as **Must fix / Should fix / Optional**, each with file:line, a one-sentence description, and a suggested fix.

If for any reason the `superpowers:requesting-code-review` skill is unavailable, fall back to the `feature-dev:code-reviewer` agent via the Task tool with the same scope and output format, reporting only findings at confidence ≥ 80.

Wait for the reviewer to return and use its output as the review results.

### Step 3: Parse Review Results

Categorize:
- **Must fix:** Security issues, bugs, clear errors
- **Should fix:** Style issues, convention violations, improvements
- **Optional:** Nitpicks, suggestions

### Step 4: Fix Issues (Max 3 Cycles)

For each cycle (limit to 3 total):

1. Address **must fix** items first
2. Then **should fix** items
3. Skip purely optional/nitpick items unless trivial

After fixes:
```bash
git add -A
git commit -m "fix: address code review feedback

- [list fixes]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Between cycles, re-invoke the reviewer on the updated changes.

If issues remain after 3 cycles, note them but don't chase perfection.

### Step 5: Final Verification

Re-invoke `superpowers:requesting-code-review` asking only for remaining high-confidence issues. Report final status.

## Output

```
## Code Review Summary

### Reviewer Used
- Superpowers code review (or feature-dev:code-reviewer fallback)

### Review Type
- Reviewed: committed/uncommitted changes
- Cycles completed: X/3

### Issues Found & Fixed
- [x] file.py:42 - Security: SQL injection risk → parameterized query
- [x] util.js:15 - Bug: null check missing → added guard

### Issues Noted (not fixed)
- [ ] style.css:100 - Nitpick: could use shorthand → skipped

### Status
✅ Ready for PR / ⚠️ Some issues remain
```

## Tips

- Run this BEFORE creating a PR, not after.
- Don't chase perfection — 2-3 cycles max. Focus on real issues, skip pure style nitpicks.

## Related Commands

| Command | Purpose |
|---------|---------|
| `/test` | Run tests before review |
| `/docs-review` | Check if docs need updates |
| `/pr` | Create PR after review |
| `/shipit` | Run all remaining steps and ship to prod |
