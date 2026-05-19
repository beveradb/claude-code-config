---
description: Create a new git worktree for focused work on a task
allowed-tools: Read, Glob, Bash, Task
---

# New Worktree Session

Create a new git worktree from the latest main branch for focused, isolated work.

**Required argument:** A description of the work

Description provided: $ARGUMENTS

## Instructions

### Step 1: Parse Arguments

Parse $ARGUMENTS to extract:
1. **Full task description** — the entire text, preserved verbatim

The description serves **two purposes**:
- 2-4 keywords are extracted for the branch/folder name
- The **full text** is preserved as the task to work on after setup (see Step 6)

If no description was provided (empty or blank $ARGUMENTS), respond with:
```
Usage: /start <description of work>

Examples:
  /start fix authentication bug
  /start add export feature
  /start investigate slow queries
  /start I need to add a new API endpoint for user preferences that validates input and stores in the database
```
Then stop.

### Step 2: Generate Names

1. Get current datetime: `date +%Y%m%d-%H%M`
2. Extract 2-4 keywords from description, lowercase, hyphenated
3. Get repo name: `basename $(git rev-parse --show-toplevel)`
4. Create:
   - Branch: `feat/sess-{YYYYMMDD-HHMM}-{keywords}` (e.g., `feat/sess-20260102-1152-fix-auth-bug`)
   - Worktree folder: `../{repo}-{keywords}` (e.g., `../myproject-fix-auth-bug`)

### Step 3: Create the Worktree

Pick the base branch: prefer `origin/dev` (dev-first release flow), fall back to `origin/main` if the remote has no `dev` branch.

```bash
# Detect base branch
if git ls-remote --exit-code --heads origin dev >/dev/null 2>&1; then
  BASE=dev
else
  BASE=main
fi

# Fetch latest from origin
git fetch origin "$BASE"

# Create new worktree with branch based on origin/$BASE
git worktree add -b {branch-name} {worktree-path} "origin/$BASE"
```

Report success with:
- Branch name created
- Worktree path

**CRITICAL: Change the working directory to the new worktree immediately:**
```bash
cd {worktree-path}
```

This ensures ALL subsequent file operations (Read, Edit, Write, Glob, Grep, Bash) happen in the worktree, not the main clone.

### Step 4: Read Project Context

Read key documentation if it exists:
- `CLAUDE.md` (project instructions)
- `docs/README.md` (current status)
- `docs/CONTEXT.md` (background)
- `docs/LESSONS-LEARNED.md` (recent lessons)

If no docs exist, that's fine - just note it.

### Step 5: Summarize and Proceed

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

## Related Commands

| Command | When to Use |
|---------|-------------|
| `/plan` | Create a detailed implementation plan |
| `/implement` | Execute a plan step by step |
| `/shipit` | Ship it all - test, review, docs, PR, merge, deploy, verify |
| `/test` | Run tests and check coverage |
| `/docs-review` | Update docs before merging |
| `/docs-maintain` | Periodic documentation cleanup |
| `/coderabbit` | Run CodeRabbit CLI locally before PR |
| `/pr` | Create PR with @coderabbitai ignore |
| `/cleanup` | Clean up current worktree after PR merged |
| `/tidy-all-worktrees` | Review and clean up ALL worktrees (periodic) |

## Notes

- Each worktree is isolated - work on multiple features in parallel
- Always commit your work in the worktree before switching
- Use `/cleanup` at end of session to clean up the current worktree
- Use `/tidy-all-worktrees` periodically to review all worktrees
- The worktree folder is a sibling to the main repo folder
