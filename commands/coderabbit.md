---
description: Run CodeRabbit CLI review (with agent fallback) and fix issues before PR
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Task
---

# Code Review (CodeRabbit + Agent Fallback)

Run a local code review and fix any issues before creating a PR. Prefer the CodeRabbit CLI; fall back to the `feature-dev:code-reviewer` agent when CodeRabbit is unavailable, rate-limited, or explicitly skipped.

**Argument (optional):** $ARGUMENTS
- `uncommitted` - review working changes (default if nothing committed)
- `committed` - review committed changes vs main (default if commits exist)
- `agent` - skip CodeRabbit entirely, use the agent reviewer
- `--no-fallback` - do not fall back to agent if CodeRabbit fails (report and stop)

Arguments can be combined, e.g. `committed agent` or `uncommitted --no-fallback`.

## Reviewer Selection

There are two reviewers available:

1. **CodeRabbit CLI** (primary) — thorough, but depends on an external service with rate limits.
2. **`feature-dev:code-reviewer` agent** (fallback) — runs locally via the Task tool, no external dependencies. Focuses on high-confidence issues (≥80) and project-convention violations.

Decision flow:
- If `$ARGUMENTS` contains `agent` → go straight to the agent path (Step 3b).
- Otherwise, try CodeRabbit (Step 3a). If it fails with any of the unavailability signals below, fall back to the agent path unless `--no-fallback` was passed.

**CodeRabbit unavailability signals** (treat any of these as "unavailable"):
- Binary missing on PATH
- Exit code non-zero AND stderr/stdout contains any of: `rate limit`, `rate-limit`, `429`, `quota`, `too many requests`, `unauthorized`, `authentication`, `auth required`, `login`, `network`, `timeout`, `ECONNREFUSED`, `ENOTFOUND`, `service unavailable`, `503`, `502`, `500`
- Command hangs past a reasonable timeout (see Step 3a)

## Instructions

### Step 1: Check Prerequisites

If `$ARGUMENTS` contains `agent`, skip this step and go to Step 3b.

Verify the CodeRabbit CLI is installed:
```bash
which coderabbit
```

If not installed:
- If `--no-fallback` is set → tell the user to install with `npm install -g coderabbit` and stop.
- Otherwise → note that CodeRabbit is unavailable and proceed to Step 3b (agent fallback).

### Step 2: Determine What to Review

Check the state of the working directory:
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

Run the review with a reasonable timeout. CodeRabbit can take 7-30+ minutes; use `timeout` to cap it.

```bash
# Use --prompt-only for clean, token-efficient output.
# Timeout at 35 minutes; capture both stdout and stderr.
timeout 2100 coderabbit --prompt-only --type "$REVIEW_TYPE" 2>&1
CODERABBIT_EXIT=$?
```

Inspect the exit code and output:

- **Exit 0** → review succeeded, proceed to Step 4.
- **Exit 124** (timeout) → treat as unavailable.
- **Non-zero exit** → scan output for unavailability signals (listed above). If matched, treat as unavailable.
- **Any other non-zero exit** → surface the error to the user; if `--no-fallback`, stop. Otherwise treat as unavailable.

If unavailable:
- Tell the user: "CodeRabbit unavailable (reason: <brief>). Falling back to `feature-dev:code-reviewer` agent."
- Proceed to Step 3b.

### Step 3b: Run Agent Review (fallback path)

Dispatch the `feature-dev:code-reviewer` agent via the Task tool. Give it:
- The review scope (`$REVIEW_TYPE`).
- The exact git command it should use to see the diff (so it doesn't guess):
  - `committed` → `git diff main..HEAD` and `git log --oneline main..HEAD`
  - `uncommitted` → `git diff` and `git diff --staged`
- Instructions to follow its own confidence-scoring rules (report only confidence ≥ 80) and to categorize findings as **Must fix / Should fix / Optional**.
- A request for output in the same shape as CodeRabbit's (file:line, issue, suggested fix) so Step 4 parsing is uniform.

Example Task prompt skeleton (adapt to the actual scope):

> Review the **$REVIEW_TYPE** changes on this branch. Base: `main`. Use `<git command>` to see the diff. Focus on bugs, security issues, logic errors, and violations of project conventions documented in CLAUDE.md. Apply your confidence-scoring policy: report only issues with confidence ≥ 80. Group findings as **Must fix / Should fix / Optional**. For each finding: file path, line number, one-sentence description, and suggested fix. Keep output concise.

Wait for the agent to return and use its output as the review results.

### Step 4: Parse Review Results

Whichever reviewer ran, parse the output and categorize:
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

Between cycles, re-run the same reviewer that produced the findings (CodeRabbit or agent). If CodeRabbit becomes unavailable mid-cycle, fall back to the agent for the remaining cycles.

If more issues remain after 3 cycles, note them but don't chase perfection.

### Step 6: Final Verification

Run one more quick check with whichever reviewer is currently healthy:

- CodeRabbit: `timeout 2100 coderabbit --prompt-only --type "$REVIEW_TYPE" 2>&1 | head -50`
- Agent: re-dispatch `feature-dev:code-reviewer` with a short prompt asking only for remaining high-confidence issues.

Report final status.

## Output

Provide a summary:

```
## Code Review Summary

### Reviewer Used
- Primary: CodeRabbit ✅ / ⚠️ unavailable (<reason>)
- Fallback: feature-dev:code-reviewer agent (used / not needed)

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
- `--prompt-only` gives clean output for LLMs.
- Don't chase perfection — 2-3 cycles max.
- Focus on real issues, skip pure style nitpicks.
- Pass `agent` as an argument to skip CodeRabbit entirely (faster, no external dependency).
- Pass `--no-fallback` if you specifically need CodeRabbit's output (e.g., for parity with CI).

## Related Commands

| Command | Purpose |
|---------|---------|
| `/test` | Run tests before review |
| `/docs-review` | Check if docs need updates |
| `/pr` | Create PR after review |
| `/shipit` | Run all remaining steps and ship to prod |
