---
description: Document this session's work to the project's sessions folder for future discoverability
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Wrap Up Session

Write a thorough, self-contained record of everything done and learned in this
session, so a future Claude session (or Andrew) can pick up with full context —
then leave the working tree clean by committing and pushing the loose changes
(the session record and other safe edits) so the local clone and `main` are up
to date. Works in ANY folder — git or not, code or not.

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

### 4. Leave the working tree clean and up to date

The point of wrapping is to end the session with **nothing dangling** — the
session record you just wrote (and any other loose changes) should be committed
and pushed, so the local clone and `main` are clean and current for next time.

Only do this in a git repo. If not a repo, skip to Report.

1. **Survey the working tree:**
   ```bash
   git branch --show-current
   git status --short
   git status --short --untracked-files=all   # include untracked
   ```
2. **Review every change** — read the diff of what's staged/unstaged and inspect
   untracked files so you know exactly what you'd be committing. Never blind-add:
   ```bash
   git diff
   git diff --cached
   # for each untracked file that matters, look at it before adding
   ```
3. **Decide what belongs on `main`.** Classify the changes:
   - **Session records / docs / notes** (this command's output and similar) →
     safe to commit + push to `main` directly.
   - **Substantive code changes on `main`** → these usually should have gone
     through a worktree + PR, not landed on `main`. Do **not** blindly commit
     them. Surface them to Andrew (this is `/fix-main` territory) and let him
     decide; only proceed if he confirms.
   - **Stray junk** (accidental files, scratch output) → point it out; don't
     commit it.
4. **Guard the branch.** Only commit-and-push-to-`main` when the current branch
   IS the repo's default branch (check with
   `git symbolic-ref --short refs/remotes/origin/HEAD` — usually `origin/main`). If you're on a feature branch
   or inside a worktree, do **not** push to `main` — just report that the record
   was written and leave committing to the branch's normal flow (`/pr`, `/shipit`).
5. **Commit + push** the safe changes:
   ```bash
   git pull --ff-only                    # sync FIRST; if this fails, stop and report — don't commit
   git add <the reviewed paths>          # explicit paths, not `git add -A` blindly
   git commit -m "<concise message, e.g. 'docs: session record — <topic>'>" -- <the reviewed paths>
   git push
   ```
   The path-limited `git commit -- <paths>` ensures anything else that was
   already staged is **not** swept into the commit. If the push is rejected
   because `main` moved, `git pull --rebase` and push again; if that conflicts,
   stop and report rather than forcing.
   End the commit message with the repo's usual trailer if it has one
   (e.g. a `Co-Authored-By: Claude …` line).
6. **Confirm clean:** run `git status` again and verify the tree is clean and the
   branch is not ahead of its upstream. Report the final state.

### 5. Report

Print the path written, the commit(s) pushed (or why nothing was committed), the
final `git status` state, and a one-line summary. Do NOT modify
README/ARCHITECTURE/etc. — that is `/docs-review`'s job.

## Guidelines
- Lightweight and universal: write the session record, then tidy the git tree.
- Concise and factual; write for a future session with zero context.
- The record is auto-loaded by the SessionStart hook next time — front-load
  what matters most.

## Related Commands
| Command | Purpose |
|---------|---------|
| `/docs-review` | Full structured-doc review (serious workflow) |
| `/docs-maintain` | Reorganize & enforce the docs layout |
