---
description: Create git worktree(s) in backend, frontend, or both repos
allowed-tools: Read, Glob, Bash, Task
---

# Multi-Repo Worktree Session

Create new git worktree(s) for focused, isolated work across the Aquarius project.

**Format:** `/start <repo> <description>`

- `repo`: `backend`, `frontend`, or `both`
- `description`: Brief name for the work (2-4 words)

Arguments provided: $ARGUMENTS

## Instructions

### Step 1: Parse Arguments

Parse $ARGUMENTS to extract repo selection and full task description.

The description serves **two purposes**:
- 2-4 keywords are extracted for the branch/folder name
- The **full text** (after the repo keyword) is preserved as the task to work on after setup (see final step)

Valid formats:
- `/start backend fix auth bug`
- `/start frontend add dark mode`
- `/start aquabot add vault`
- `/start protocol add contract spec`
- `/start e2e-sites add vocal coach directory`
- `/start intake add sms connector`
- `/start both add export feature`
- `/start backend I need to fix the auth token refresh and add better error messages for expired sessions`

If invalid or missing, respond with:
```
Usage: /start <repo> <description>

Where <repo> is one of:
  backend    - Changes to API, services, database, infra
  frontend   - Changes to UI, components, styling
  aquabot    - Autonomous web agent changes
  protocol   - AWP specs, decision records, protocol docs
  e2e-sites  - KAT E2E test sites (silverforkplumbing.com, etc.)
  intake     - Aquarius Intake attention engine (FastAPI/Firestore/Cloud Run)
  both       - Full-stack changes (creates worktrees in both repos)
  (workspace changes: edit directly on `main` in the root clone — no /start needed.)

Examples:
  /start backend fix authentication bug
  /start frontend add user settings page
  /start aquabot add credential vault
  /start protocol add contract spec
  /start e2e-sites add vocal coach directory
  /start intake add sms connector
  /start both add export feature
```
Then stop.

### Step 2: Define Paths

Set these paths based on working directory:

```
PARENT_DIR=$(pwd)
BACKEND_MAIN="$PARENT_DIR/backend-main-readonly"
FRONTEND_MAIN="$PARENT_DIR/frontend-main-readonly"
AQUABOT_MAIN="$PARENT_DIR/aquabot-main-readonly"
PROTOCOL_MAIN="$PARENT_DIR/protocol-main-readonly"
E2E_SITES_MAIN="$PARENT_DIR/aquabot-e2e-sites-main-readonly"
INTAKE_MAIN="$PARENT_DIR/aquarius-intake-mvp-main-readonly"
# --- WFM-worker path only. Humans edit the workspace directly on `main` in the
# root clone (see CLAUDE.md) — no /start, no PR. This block is kept because WFM
# kickoff templates run `/start workspace <desc>` for wfm:scope:wfm-self issues. ---
# Workspace itself IS the main clone — no -main-* suffix. Sibling
# worktrees go OUTSIDE $PARENT_DIR so they don't pollute the workspace's
# git status.
WORKSPACE_MAIN="$PARENT_DIR"
WORKSPACE_SIBLING_DIR="$(dirname "$PARENT_DIR")"
```

Verify the main worktree folders exist. If not, error with helpful message.

### Step 3: Generate Names

1. Get current datetime: `date +%Y%m%d-%H%M`
2. Extract 2-4 keywords from description, lowercase, hyphenated (e.g., "fix auth bug" → "fix-auth-bug")
3. Create branch name: `feat/sess-{YYYYMMDD-HHMM}-{keywords}`
4. Create worktree paths:
   - Backend: `$PARENT_DIR/backend-{keywords}`
   - Frontend: `$PARENT_DIR/frontend-{keywords}`

### Step 3b: Refresh Read-Only Mirrors

Before branching, hard-sync every read-only mirror to its origin tip so the new
worktree branches off a current base and the `*-{main,dev}-readonly` checkouts
aren't left showing stale HEADs. The workspace root clone is never touched.

```bash
ROOT="$(pwd)"
while [ "$ROOT" != "/" ] && [ -z "$(ls -d "$ROOT"/*-main-readonly 2>/dev/null)" ]; do
  ROOT="$(dirname "$ROOT")"
done
bash "$ROOT/docs/archive/scripts/refresh-mirrors.sh"
```

This subsumes the per-repo `git fetch` in Step 4 (harmless if repeated), and is
the same refresh that `/refresh`, `/tidy-all-worktrees`, `/cleanup`, and `/setup`
run.

### Step 4: Create Worktree(s)

**Base branch by repo (workspace#946 dev-first release flow):**
- `backend`, `frontend`, `aquabot`, `intake` → branch from `origin/dev` (product repos under dev-first flow).
- `protocol`, `e2e-sites`, `workspace` → branch from `origin/main` (no prod environment / not under dev-first).

**For `backend` or `both`:**
```bash
cd "$BACKEND_MAIN"
git fetch origin dev
git worktree add -b {branch-name} "$PARENT_DIR/backend-{keywords}" origin/dev
```

**For `frontend` or `both`:**
```bash
cd "$FRONTEND_MAIN"
git fetch origin dev
git worktree add -b {branch-name} "$PARENT_DIR/frontend-{keywords}" origin/dev
```

**For `aquabot`:**
```bash
cd "$AQUABOT_MAIN"
git fetch origin dev
git worktree add -b {branch-name} "$PARENT_DIR/aquabot-{keywords}" origin/dev
```

**For `protocol`:**
```bash
cd "$PROTOCOL_MAIN"
git fetch origin main
git worktree add -b {branch-name} "$PARENT_DIR/protocol-{keywords}" origin/main
```

**For `e2e-sites`:**
```bash
cd "$E2E_SITES_MAIN"
git fetch origin main
git worktree add -b {branch-name} "$PARENT_DIR/aquabot-e2e-sites-{keywords}" origin/main
```

**For `intake`:**
```bash
cd "$INTAKE_MAIN"
git fetch origin dev
git worktree add -b {branch-name} "$PARENT_DIR/aquarius-intake-mvp-{keywords}" origin/dev
```

**For `workspace`:**
```bash
# Workspace repo IS the parent dir — branch off the main clone in place.
# Sibling worktree lives one level up so it doesn't pollute git status.
# The PreToolUse hook .claude/hooks/guard-worktree-location.py permits
# this exact shape (siblings whose name starts with <workspace_basename>-);
# any other destination is blocked. See workspace#743.
cd "$WORKSPACE_MAIN"
git fetch origin main
git worktree add -b {branch-name} "$WORKSPACE_SIBLING_DIR/aquarius-workspace-{keywords}" origin/main
```

### Step 4b: Copy Environment Files

Copy appropriate environment files based on the development scenario.

**For `backend` only:**
```bash
# Backend local dev config
if [ -f "$PARENT_DIR/.env.backend.local" ]; then
  cp "$PARENT_DIR/.env.backend.local" "$PARENT_DIR/backend-{keywords}/.env"
  echo "Copied .env.backend.local → backend-{keywords}/.env"
else
  echo "WARNING: No .env.backend.local found in workspace"
fi
```

**For `frontend` only:**
```bash
# Frontend-only work → use PROD backend (no need to run backend locally)
if [ -f "$PARENT_DIR/.env.frontend.prod" ]; then
  cp "$PARENT_DIR/.env.frontend.prod" "$PARENT_DIR/frontend-{keywords}/.env.local"
  echo "Copied .env.frontend.prod → frontend-{keywords}/.env.local"
  echo "  (Frontend will talk to PROD backend)"
else
  echo "WARNING: No .env.frontend.prod found in workspace"
fi
```

**For `both` (full-stack):**
```bash
# Backend local dev config
if [ -f "$PARENT_DIR/.env.backend.local" ]; then
  cp "$PARENT_DIR/.env.backend.local" "$PARENT_DIR/backend-{keywords}/.env"
  echo "Copied .env.backend.local → backend-{keywords}/.env"
else
  echo "WARNING: No .env.backend.local found in workspace"
fi

# Frontend LOCAL config → talks to LOCAL backend (localhost:3080)
if [ -f "$PARENT_DIR/.env.frontend.local" ]; then
  cp "$PARENT_DIR/.env.frontend.local" "$PARENT_DIR/frontend-{keywords}/.env.local"
  echo "Copied .env.frontend.local → frontend-{keywords}/.env.local"
  echo "  (Frontend will talk to LOCAL backend at localhost:3080)"
else
  echo "WARNING: No .env.frontend.local found in workspace"
fi
```

**For `intake`:**
```bash
# Intake local dev config. Prefer a workspace-level override if present,
# otherwise seed from the repo's own .env.example so the worktree is runnable.
if [ -f "$PARENT_DIR/.env.intake.local" ]; then
  cp "$PARENT_DIR/.env.intake.local" "$PARENT_DIR/aquarius-intake-mvp-{keywords}/.env"
  echo "Copied .env.intake.local → aquarius-intake-mvp-{keywords}/.env"
elif [ -f "$PARENT_DIR/aquarius-intake-mvp-{keywords}/.env.example" ]; then
  cp "$PARENT_DIR/aquarius-intake-mvp-{keywords}/.env.example" "$PARENT_DIR/aquarius-intake-mvp-{keywords}/.env"
  echo "Seeded .env from .env.example — fill in real values before running"
else
  echo "WARNING: No .env.intake.local or .env.example found for intake"
fi
```

### Step 5: Change to Primary Worktree

**CRITICAL: Change the working directory to the new worktree immediately.** This is mandatory — without it, all subsequent file operations will target the wrong directory.

```bash
cd {primary-worktree-path}
```

- For `backend`: `cd "$PARENT_DIR/backend-{keywords}"`
- For `frontend`: `cd "$PARENT_DIR/frontend-{keywords}"`
- For `aquabot`: `cd "$PARENT_DIR/aquabot-{keywords}"`
- For `protocol`: `cd "$PARENT_DIR/protocol-{keywords}"`
- For `e2e-sites`: `cd "$PARENT_DIR/aquabot-e2e-sites-{keywords}"`
- For `intake`: `cd "$PARENT_DIR/aquarius-intake-mvp-{keywords}"`
- For `workspace`: `cd "$WORKSPACE_SIBLING_DIR/aquarius-workspace-{keywords}"`
- For `both`: `cd "$PARENT_DIR/backend-{keywords}"` (primary for full-stack)

**All file operations after this point must use paths under the worktree directory. Never use paths under the main clone directories.** A PreToolUse hook will block any attempts to edit files in main clone directories.

### Step 6: Report Success

**For `backend` only:**
```
## Worktree Created

**Backend:** /path/to/backend-{keywords} (branch: feat/sess-...)
  - .env: copied from .env.backend.local

**Working directory:** /path/to/backend-{keywords}
All file operations must use paths under this directory. Never use paths under the main clone.
```

**For `frontend` only:**
```
## Worktree Created

**Frontend:** /path/to/frontend-{keywords} (branch: feat/sess-...)
  - .env.local: copied from .env.frontend.prod
  - API: PROD backend (https://aquarius-orchestrator-prod-...)

**Working directory:** /path/to/frontend-{keywords}
All file operations must use paths under this directory. Never use paths under the main clone.
```

**For `aquabot` only:**
```
## Worktree Created

**AquaBot:** /path/to/aquabot-{keywords} (branch: feat/sess-...)

**Working directory:** /path/to/aquabot-{keywords}
All file operations must use paths under this directory. Never use paths under the main clone.
```

**For `protocol` only:**
```
## Worktree Created

**Protocol:** /path/to/protocol-{keywords} (branch: feat/sess-...)

**Working directory:** /path/to/protocol-{keywords}
All file operations must use paths under this directory. Never use paths under the main clone.
```

**For `intake` only:**
```
## Worktree Created

**Intake:** /path/to/aquarius-intake-mvp-{keywords} (branch: feat/sess-... off origin/dev)
  - .env: seeded from .env.example (fill in real values before running)

**Working directory:** /path/to/aquarius-intake-mvp-{keywords}
All file operations must use paths under this directory. Never use paths under the main clone.
```

**For `workspace` only:**
```
## Worktree Created

**Workspace:** /path/to/aquarius-workspace-{keywords} (branch: feat/sess-...)
  - The main workspace clone (/Users/andrew/Projects/aquarius/) is reserved
    for the manager pane and must stay on `main`. The pre-commit hook in
    that clone hard-rejects commits on any other branch — see issue #40.

**Working directory:** /path/to/aquarius-workspace-{keywords}
All file operations must use paths under this directory. Never use paths under the main clone.
```

**For `both`:**
```
## Worktrees Created

**Backend:** /path/to/backend-{keywords} (branch: feat/sess-...)
  - .env: copied from .env.backend.local

**Frontend:** /path/to/frontend-{keywords} (branch: feat/sess-...)
  - .env.local: copied from .env.frontend.local
  - API: LOCAL backend (http://localhost:3080)

**Full-stack development:** Start backend with `docker-compose up` or `make run-all`

**Working directory:** /path/to/backend-{keywords}
All file operations must use paths under the worktree directories. Never use paths under the main clones.
```

If any .env file is missing, remind the user:
```
**Setup required:** Run /setup or create env files manually:
  - .env.backend.local - Backend local dev config
  - .env.frontend.prod - Frontend → PROD backend
  - .env.frontend.local - Frontend → LOCAL backend
```

### Step 7: Read Project Context

Read key documentation from the PRIMARY worktree:
- `CLAUDE.md` (project instructions)
- `docs/README.md` (current status)
- `docs/LESSONS-LEARNED.md` (recent lessons)

### Step 8: Summarize and Proceed

Output a brief summary:

```
## Worktree Created

**Branch:** feat/sess-YYYYMMDD-HHMM-keywords
**Working directory:** /path/to/worktree

**Rename session:** /rename {keywords}
```

Then **immediately proceed to work on the full task description** from Step 1.

- If the description is short (a few words like "fix auth bug"), treat it as a task and begin investigating/working on it directly. Use `/plan` if non-trivial.
- If the description is detailed (a sentence or more), treat it as if the user had typed it as their first message after worktree setup. Follow the task fully — plan, implement, whatever is appropriate.

**Do NOT** ask "What would you like to work on?" — the user already told you in the arguments.

## Notes

- This command is for the aquarius parent folder only
- From inside a repo, use the standard `/start <description>`
- For `both`, you'll need separate PRs for each repo
- Worktrees appear as sibling folders in the parent directory
