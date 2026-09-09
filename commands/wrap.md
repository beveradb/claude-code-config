---
description: Document this session's work to the project's sessions folder for future discoverability
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Wrap Up Session

Write a thorough, self-contained record of everything done and learned in this
session, so a future Claude session (or Andrew) can pick up with full context.
Works in ANY folder — git or not, code or not.

## Core principle: activities are not always code

A session may have reconciled a budget, cleaned data, done research, run ops
tasks, or edited code. Capture **what was actually done and learned**, not just
code changes. `git diff`/`git log` are OPTIONAL supplementary inputs used only
when code actually changed — never treat an empty or irrelevant diff as
"nothing happened." The primary source is THIS conversation: the actions taken,
commands/tools run, external systems changed, and outcomes.

## Instructions

### 1. Reconstruct the session

Review the conversation and determine what was actually accomplished:
- What was the goal / task?
- What concrete actions were taken? (commands run, tools used, external state
  changed — e.g. "reconciled budget, updated 4 YNAB accounts to live balances")
- What was decided, and why?
- What was learned (non-obvious gotchas, findings)?
- What is unfinished, or where should the next session pick up?

If in a git repo AND code changed, gather supplementary detail only:
```bash
git branch --show-current 2>/dev/null
git log --oneline -10 2>/dev/null
git diff --stat 2>/dev/null
```
Do NOT rely on git as the source of truth.

### 2. Locate / establish the sessions folder

Find the project root (the dir the session started from; its git root if any):
```bash
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
```
Choose the sessions dir, in preference order: use existing `docs/sessions/`; else
if `docs/` exists create `docs/sessions/`; else create `docs/sessions/` at the
root anyway (fine for non-code folders). Compute the quarter and make the folder:
```bash
M=$(( 10#$(date +%m) )); Q=$(( (M - 1) / 3 + 1 ))
QUARTER="$(date +%Y)-Q${Q}"
mkdir -p "${ROOT}/docs/sessions/${QUARTER}"
echo "${ROOT}/docs/sessions/${QUARTER}"
```

### 3. Write the session record

Path: `docs/sessions/<quarter>/YYYY-MM-DD-<topic>.md` — `<topic>` is a short
kebab-case slug of the session's focus; date from `date +%Y-%m-%d`.

Same-day handling: different topic today → new file; re-running for the same
topic today → update the existing file in place.

Template (omit sections that genuinely don't apply, but always keep
"Open threads & next steps"):
```markdown
# <Topic> — YYYY-MM-DD

**Project:** <name>   **Branch/commit:** <if a repo, else n/a>   **Status:** <done / in-progress>

## Summary
What was done and why.

## What changed
Concrete actions and their effects — code changes OR external state changed
(accounts updated, data reconciled, resources created), commands run, config touched.

## Decisions & rationale
- Decision — why.

## Learnings / gotchas
- Non-obvious things worth keeping.

## Open threads & next steps
- What's unfinished / where a future session should pick up.

## Related docs
- Links to relevant plans/designs/other session records.
```

### 4. Report

Print the path written and a one-line summary. Do NOT modify
README/ARCHITECTURE/etc. — that is `/docs-review`'s job.

## Guidelines
- Lightweight and universal: this command only writes the session record.
- Concise and factual; write for a future session with zero context.
- The record is auto-loaded by the SessionStart hook next time — front-load
  what matters most.

## Related Commands
| Command | Purpose |
|---------|---------|
| `/docs-review` | Full structured-doc review (serious workflow) |
| `/docs-maintain` | Reorganize & enforce the docs layout |
