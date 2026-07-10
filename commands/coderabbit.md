---
description: Run CodeRabbit CLI review (with Superpowers review fallback) and fix issues before PR
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Skill, Task
---

# Code Review (CodeRabbit + Superpowers Fallback)

Run a local code review and fix any issues before creating a PR. Prefer the CodeRabbit CLI; fall back to the **Superpowers code review** (`superpowers:requesting-code-review`) whenever CodeRabbit is unavailable, rate-limited, errors out, or is explicitly skipped.

**Argument (optional):** $ARGUMENTS
- `uncommitted` - review working changes (default if nothing committed)
- `committed` - review committed changes vs main (default if commits exist)
- `superpowers` (alias: `agent`) - skip CodeRabbit entirely, use the Superpowers reviewer
- `--no-fallback` - do not fall back if CodeRabbit fails (report and stop)

Arguments can be combined, e.g. `committed superpowers` or `uncommitted --no-fallback`.

## Reviewer Selection

Two reviewers are available:

1. **CodeRabbit CLI** (primary) — thorough, but depends on an external service with rate limits and auth.
2. **Superpowers code review** (fallback) — invokes the `superpowers:requesting-code-review` skill, which dispatches a code-reviewer subagent locally with no external dependency.

Decision flow:
- If `$ARGUMENTS` contains `superpowers` or `agent` → go straight to the fallback path (Step 3b).
- Otherwise, try CodeRabbit (Step 3a). If it fails with any unavailability signal below, fall back to Superpowers review unless `--no-fallback` was passed.

**CodeRabbit unavailability signals** (treat any as "unavailable"):
- Binary missing on PATH
- Not authenticated (`coderabbit auth status` reports logged out / no token)
- Exit code non-zero AND stderr/stdout contains any of: `rate limit`, `rate-limit`, `429`, `quota`, `too many requests`, `unauthorized`, `authentication`, `auth required`, `login`, `network`, `timeout`, `ECONNREFUSED`, `ENOTFOUND`, `service unavailable`, `503`, `502`, `500`
- Command hangs past the timeout (see Step 3a)

## Instructions

### Step 1: Check Prerequisites

If `$ARGUMENTS` contains `superpowers` or `agent`, skip this step and go to Step 3b.

Verify the CodeRabbit CLI is installed and authenticated:
```bash
which coderabbit && coderabbit --version
coderabbit auth status 2>&1
```

- Binary missing:
  - `--no-fallback` set → tell the user to install with `npm install -g @coderabbitai/cli` (or `curl -fsSL https://cli.coderabbit.ai/install.sh | sh`) and stop.
  - Otherwise → note CodeRabbit is unavailable and proceed to Step 3b.
- Binary present but not authenticated:
  - `--no-fallback` set → tell the user to run `coderabbit auth login` and stop.
  - Otherwise → note CodeRabbit is unavailable (not authenticated) and proceed to Step 3b.

### Step 2: Determine What to Review

```bash
git status --porcelain
git log --oneline main..HEAD 2>/dev/null | head -5
```

If `$ARGUMENTS` specifies `committed` or `uncommitted`, use that. Otherwise:
- Commits ahead of main → `committed`
- Only uncommitted changes → `uncommitted`
- Nothing to review → tell user and stop

Record this as `$REVIEW_TYPE` for the remainder of the command.

### Step 3a: Run CodeRabbit Review (primary path)

The installed CLI uses the **`review` subcommand** (there is no `--prompt-only` flag). Use `--plain` for clean, token-efficient text output. CodeRabbit can take 7-30+ minutes, so cap it with `timeout` and run it in the background if the foreground Bash cap is shorter than the timeout.

```bash
# Correct invocation for CLI v0.6.x:
#   coderabbit review --plain --type <all|committed|uncommitted> [--base main]
# Use --agent instead of --plain if you want structured findings for programmatic parsing.
# Timeout at 35 minutes; capture both stdout and stderr.
timeout 2100 coderabbit review --plain --type "$REVIEW_TYPE" --base main 2>&1
CODERABBIT_EXIT=$?
```

For long runs, prefer launching in the background and monitoring rather than blocking:
```bash
LOG="$SCRATCH/coderabbit.log"   # use the session scratchpad dir
nohup coderabbit review --plain --type "$REVIEW_TYPE" --base main > "$LOG" 2>&1 &
CR_PID=$!
# Monitor with: while kill -0 $CR_PID 2>/dev/null; do sleep 10; done; cat "$LOG"
```

Inspect the exit code and output:

- **Exit 0** → review succeeded, proceed to Step 4.
- **Exit 124** (timeout) → treat as unavailable.
- **Non-zero exit** → scan output for unavailability signals (listed above). If matched, treat as unavailable.
- **Any other non-zero exit** → surface the error; if `--no-fallback`, stop. Otherwise treat as unavailable.

If unavailable:
- Tell the user: "CodeRabbit unavailable (reason: <brief>). Falling back to Superpowers code review."
- Proceed to Step 3b.

### Step 3b: Run Superpowers Review (fallback path)

Invoke the Superpowers code review skill:

```
Skill: superpowers:requesting-code-review
```

Give the skill the review scope so it crafts the right context for its reviewer subagent:
- Base: `main`. Diff command by scope:
  - `committed` → `git diff main..HEAD` (and `git log --oneline main..HEAD` for commit messages)
  - `uncommitted` → `git diff` and `git diff --staged`
- Ask for findings grouped as **Must fix / Should fix / Optional**, each with file:line, a one-sentence description, and a suggested fix, so Step 4 parsing is uniform with CodeRabbit's shape.

If for any reason the `superpowers:requesting-code-review` skill is unavailable, fall back one more level to the `feature-dev:code-reviewer` agent via the Task tool with the same scope and output format, reporting only findings at confidence ≥ 80.

Wait for the reviewer to return and use its output as the review results.

### Step 4: Parse Review Results

Whichever reviewer ran, categorize:
- **Must fix:** Security issues, bugs, clear errors
- **Should fix:** Style issues, convention violations, improvements
- **Optional:** Nitpicks, suggestions

### Step 5: Fix Issues (Max 3 Cycles)

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

Between cycles, re-run the same reviewer that produced the findings. If CodeRabbit becomes unavailable mid-cycle, fall back to Superpowers review for the remaining cycles.

If issues remain after 3 cycles, note them but don't chase perfection.

### Step 6: Final Verification

Run one more quick check with whichever reviewer is currently healthy:

- CodeRabbit: `timeout 2100 coderabbit review --plain --type "$REVIEW_TYPE" --base main 2>&1 | head -50`
- Superpowers: re-invoke `superpowers:requesting-code-review` asking only for remaining high-confidence issues.

Report final status.

## Output

```
## Code Review Summary

### Reviewer Used
- Primary: CodeRabbit ✅ / ⚠️ unavailable (<reason>)
- Fallback: Superpowers code review (used / not needed)

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
- Correct CLI invocation is `coderabbit review --plain --type <type>` — the old `--prompt-only` flag no longer exists.
- Use `--agent` instead of `--plain` when you want structured findings to parse programmatically.
- CodeRabbit runs can take 30+ min — run in the background and monitor rather than blocking.
- Don't chase perfection — 2-3 cycles max. Focus on real issues, skip pure style nitpicks.
- Pass `superpowers` as an argument to skip CodeRabbit entirely (faster, no external dependency).
- Pass `--no-fallback` if you specifically need CodeRabbit's output (e.g., for parity with CI).

## Related Commands

| Command | Purpose |
|---------|---------|
| `/test` | Run tests before review |
| `/docs-review` | Check if docs need updates |
| `/pr` | Create PR after review |
| `/shipit` | Run all remaining steps and ship to prod |
