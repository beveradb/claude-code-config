# Session-Continuity System — Design

**Date:** 2026-09-09
**Status:** Approved (spec)
**Author:** Andrew + Claude (brainstormed)

## Problem

Andrew frequently tells Claude, near the end of a session: *"ensure everything done in
this session is thoroughly documented so I can close this session with confidence that
everything completed/learned here will be discoverable by future Claude sessions."*

This works but is repetitive to type, and the existing `/docs-review` command is a poor
fit for the long tail of use cases:

- `/docs-review` assumes a git repo with a `main` branch, and a mature structured-docs
  tree (README/ARCHITECTURE/DEVELOPMENT/API/LESSONS-LEARNED/CLAUDE.md). It's tuned for
  the "serious" projects (nomadkaraoke, aquarius, life360) inside the
  `/start → /shipit` workflow.
- Many other projects — standalone tools in `~/Projects/beveradb/`, one-off scripts,
  non-code folders — are too small/varied for it. Some aren't git repos at all.

There is no automatic mechanism to *read back* recent work when a new session opens in a
given project, so context from prior sessions is lost unless manually re-surfaced.

Separately: the existing flat `docs/archive/` convention has grown unwieldy in large
repos (aquarius has ~1200 files in `docs/archive/`), to the point that GitHub chokes on
rendering the folder.

## Goals

1. A single lightweight, **global** command to write a thorough session record — usable
   in any folder, git or not, code or not.
2. **Automatic** read-back of the most recent session records when a new session starts
   in a project, with zero per-project setup.
3. Fix the oversized-folder problem by splitting docs into typed, quarter-bucketed
   subfolders, and give `/docs-maintain` the ability to migrate existing archives into
   that layout.
4. Keep the proven serious-workflow commands coherent with the new layout.

## Non-Goals

- Auto-writing session records on session end (quality/noise risk; writing stays an
  explicit user-invoked action).
- Replacing `/docs-review`'s structured-doc review. `/wrap` is deliberately lighter.
- Editing project `CLAUDE.md` files to instruct read-back (the hook handles that).

## The Shared Convention

All doc-writing pieces agree on one layout:

```
docs/
├── sessions/2026-Q3/2026-09-09-<topic>.md   # session records — the hook reads these
├── designs/2026-Q3/<topic>-design.md
└── plans/2026-Q3/<topic>-plan.md
```

- **Quarter buckets** (`YYYY-Qn`, e.g. `2026-Q3`) keep any one folder small enough that
  GitHub renders it and context globs stay cheap.
- **Session records are their own type** (`docs/sessions/`), kept separate from plans and
  designs, so the read-back hook never accidentally injects a large plan/design doc.
- Quarter is derived from the doc's date: *today's date* when writing new, or the
  `YYYY-MM-DD` filename prefix when migrating (falling back to git first-commit date, then
  file mtime).
- Filenames keep the existing `YYYY-MM-DD-<topic>` prefix convention.

## Components

### 1. `SessionStart` hook — automatic read-back

**File:** `~/.claude/hooks/session-context.py` (Python 3; robust date/quarter parsing and
globbing).

**Registration:** one `SessionStart` entry in global `~/.claude/settings.json` (alongside
the existing `Stop`/`Notification` hooks), so it applies in every project.

**Behavior:**
1. Read `cwd` and `source` from the hook's stdin JSON.
2. Run only when `source` is `startup` or `clear`. Skip `resume` and `compact`, which
   already retain prior context (avoids redundant injection).
3. From `cwd`, walk up to the project root and locate the session-docs directory, in
   order of preference: `docs/sessions/` → `docs/archive/` (legacy fallback) →
   `./sessions/`. **Read-only: the hook never creates anything.**
4. Find the newest **3** session docs by date (across quarter subfolders). Print each,
   capped to ~200 lines / ~8 KB per doc with a total cap, to stdout → injected as session
   context.
5. If no sessions dir is found, print nothing. Must be fast (<1s) and silent when empty.

**Implementation-time verification:** confirm the current Claude Code `SessionStart`
stdout→context contract — plain stdout added to context vs. structured
`{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}`
JSON. Use whichever is current; prefer the structured form if both are supported.

### 2. `/wrap` — new global command (lightweight universal writer)

**File:** `~/.claude/commands/wrap.md`. (Name: `/wrap`; `/handoff` considered as an
alternative but `/wrap` chosen.)

The everyday "document everything before I close this" command. Works in any folder.

**Behavior:**
1. Reconstruct what the session did: `git log`/`git diff` if in a repo; otherwise reflect
   on the conversation's actual work.
2. Detect/establish the sessions dir: use existing `docs/sessions/` if present; else
   create `docs/sessions/<quarter>/` at the project root (works for non-code folders too).
3. Write `docs/sessions/<quarter>/YYYY-MM-DD-<topic>.md` with sections:
   - **Summary** — what was done and why.
   - **Key changes** — concrete changes (files, commands, config).
   - **Decisions & rationale** — choices made and why.
   - **Learnings / gotchas** — non-obvious discoveries worth keeping.
   - **Open threads & next steps** — what's unfinished / where a future session should
     pick up. (This is the section that makes future sessions land softly.)
   - **Related docs** — links to relevant plans/designs.
4. Same-day handling: multiple distinct topics in a day → multiple files (distinct topic
   slugs). Re-running for the same topic on the same day → update the existing file in
   place.
5. Report the path written.

**Deliberately lightweight:** `/wrap` does not touch README/ARCHITECTURE/etc. and does not
edit `CLAUDE.md`. Heavy structured-doc maintenance stays with `/docs-review`.

### 3. `/docs-review` update — keep serious workflow coherent

Change only its "Create Archive Entry" step: session/handoff-style entries now write to
`docs/sessions/<quarter>/` instead of flat `docs/archive/`. Everything else (structured
doc review across README/ARCHITECTURE/DEVELOPMENT/API/LESSONS-LEARNED/CLAUDE.md, its role
within `/shipit`) is unchanged.

### 4. `/docs-maintain` update — migration + enforcement

Add a **reorg mode** (to be run by Andrew, later, against large repos):

- **Classify** existing `docs/archive/*.md` by filename heuristics:
  - `*plan*` → `docs/plans/`
  - `*design*`, `*spec*` → `docs/designs/`
  - `*handoff*`, `*session*`, `*report*`, `*findings*`, `*investigation*` →
    `docs/sessions/`
  - otherwise → flag for manual classification (default to `docs/sessions/` only if
    confident).
- **Bucket** each file into a `<quarter>/` subfolder derived from its `YYYY-MM-DD` filename
  prefix (fall back to git first-commit date, then mtime).
- **Move** with `git mv` to preserve history.
- **Leave undated reference docs** (e.g. `capital-tier-strategy.md`) in place and flag
  them rather than guessing.
- **Report-first**: print the full proposed move plan and require confirmation before
  executing, so it is safe to run unattended against big repos.
- Also enforce the layout going forward and flag any single folder that has grown too
  large.

## Consistency Notes

Slash commands are markdown prompts, not shared code, so the layout convention is
documented in each command rather than factored into a shared library. The only executable
artifact is the `SessionStart` hook script. Quarter computation, sessions-dir detection
order, and filename format are specified here as the single source of truth and referenced
by each command.

## Rollout

1. Write the `SessionStart` hook script and register it in global `settings.json`.
2. Add the `/wrap` command.
3. Update `/docs-review` (one step) and `/docs-maintain` (reorg mode).
4. Andrew runs `/docs-maintain` reorg against large repos (nomadkaraoke, aquarius, …) at
   his own pace.

## Risks / Open Questions

- **Hook contract** — verify `SessionStart` stdout→context behavior at implementation time
  (see component 1).
- **Legacy fallback noise** — reading `docs/archive/` as a fallback could inject a large
  non-session doc in un-migrated repos. Mitigated by the per-doc size cap; fully resolved
  once a repo is migrated to `docs/sessions/`.
- **Hook latency** — must stay <1s since it runs on every qualifying session start; keep
  the script to a bounded glob + head.
