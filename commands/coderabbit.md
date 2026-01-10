---
description: Run CodeRabbit CLI review and fix issues before PR
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Code Review with CodeRabbit CLI

Run a local CodeRabbit review and fix any issues before creating a PR.

**Argument (optional):** Review type: $ARGUMENTS
- `uncommitted` - review working changes (default if nothing committed)
- `committed` - review committed changes vs main (default if commits exist)

## Instructions

### Step 1: Check Prerequisites

Verify coderabbit CLI is installed:
```bash
which coderabbit || echo "CodeRabbit CLI not installed. Install with: npm install -g coderabbit"
```

If not installed, tell the user how to install it and stop.

### Step 2: Determine What to Review

Check the state of the working directory:
```bash
# Check for uncommitted changes
git status --porcelain

# Check for commits ahead of main
git log --oneline main..HEAD 2>/dev/null | head -5
```

If $ARGUMENTS is provided, use that type. Otherwise:
- If there are commits ahead of main → use `--type committed`
- If only uncommitted changes → use `--type uncommitted`
- If nothing to review → tell user and stop

### Step 3: Run CodeRabbit Review

Run the review in the background since it takes 7-30+ minutes:

```bash
# For committed changes (comparing to main)
coderabbit --prompt-only --type committed 2>&1

# OR for uncommitted changes
coderabbit --prompt-only --type uncommitted 2>&1
```

**IMPORTANT:** Use `--prompt-only` for clean, token-efficient output.

Wait for it to complete and capture the output.

### Step 4: Parse Review Results

The review output will contain:
- Issues found (bugs, security, style)
- Suggestions for improvement
- File paths and line numbers

Parse through the output and categorize:
- **Must fix:** Security issues, bugs, clear errors
- **Should fix:** Style issues, improvements
- **Optional:** Nitpicks, suggestions

### Step 5: Fix Issues (Max 3 Cycles)

For each cycle (limit to 3 total):

1. Address **must fix** items first
2. Then **should fix** items
3. Skip purely optional/nitpick items unless trivial

After fixes:
```bash
git add -A
git commit -m "fix: address CodeRabbit review feedback

- [list fixes]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

If more issues remain after 3 cycles, note them but don't chase perfection.

### Step 6: Final Verification

Run one more quick check:
```bash
coderabbit --prompt-only --type committed 2>&1 | head -50
```

Report final status.

## Output

Provide a summary:

```
## CodeRabbit Review Summary

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

- Run this BEFORE creating a PR, not after
- The `--prompt-only` flag gives clean output for LLMs
- Don't chase perfection - 2-3 cycles max
- Focus on real issues, skip pure style nitpicks
- If review takes too long, you can check progress with the background task

## Related Commands

| Command | Purpose |
|---------|---------|
| `/test` | Run tests before review |
| `/docs-review` | Check if docs need updates |
| `/pr` | Create PR after review |
| `/shipit` | Run all remaining steps and ship to prod |
