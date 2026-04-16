---
description: Set up a multi-repo workspace with worktree workflow, guard hooks, and /start command
allowed-tools: Read, Glob, Bash, Write, Edit, AskUserQuestion
---

# Set Up Multi-Repo Workspace

Set up a parent directory containing multiple git repos as a proper Claude Code workspace with worktree-based development workflow.

**Usage:** `/setup-workspace` (run from the parent directory containing your repos)

Optional arguments: $ARGUMENTS

## What This Creates

1. **Parent git repo** (if not already one) with `.gitignore`
2. **`CLAUDE.md`** — workspace map with repo table, worktree safety rules, workflow reference
3. **`.claude/settings.local.json`** — permissions and PreToolUse guard hook
4. **`.claude/hooks/guard-main-worktree.sh`** — blocks edits to main clone directories
5. **`.claude/commands/start.md`** — workspace-specific `/start <repo> <description>` command
6. **`.envrc`** — direnv config for GitHub token and project-specific env vars

## Instructions

### Step 1: Discover Repos

Scan the current directory for git repositories:

```bash
WORKSPACE=$(pwd)
for d in */; do
  if [ -d "$d/.git" ] || git -C "$d" rev-parse --git-dir &>/dev/null 2>&1; then
    REMOTE=$(git -C "$d" remote get-url origin 2>/dev/null || echo "no remote")
    BRANCH=$(git -C "$d" symbolic-ref --short HEAD 2>/dev/null || echo "unknown")
    echo "$d | $REMOTE | $BRANCH"
  fi
done
```

Also note any non-repo directories (these go in .gitignore, not the repo table).

### Step 2: Build Repo Table

For each discovered repo, determine:
- **Directory name** (as-is on disk)
- **Short alias** (1-2 word shorthand for `/start`, e.g., `frontend`, `backend`, `config`)
- **Purpose** (one-line description, inferred from README.md, package.json, or repo name)
- **Default branch** (usually `main` or `master`)

Present the table to the user:

```
## Discovered Repos

| Alias | Directory | Remote | Purpose |
|-------|-----------|--------|---------|
| frontend | kiosk-frontend | github.com/org/kiosk-frontend | React frontend app |
| backend | kiosk-backend | github.com/org/kiosk-backend | Node.js API server |

Non-repo directories (will be gitignored): old-stuff/

Does this look right? Any aliases or descriptions to change?
```

Wait for user confirmation before proceeding. Adjust if they request changes.

### Step 3: Check Existing State

Before creating anything, check what already exists:

```bash
# Check for existing setup
[ -d .git ] && echo "Already a git repo"
[ -f CLAUDE.md ] && echo "CLAUDE.md exists"
[ -f .claude/settings.local.json ] && echo "settings.local.json exists"
[ -f .claude/hooks/guard-main-worktree.sh ] && echo "guard hook exists"
[ -f .claude/commands/start.md ] && echo "start command exists"
[ -f .envrc ] && echo ".envrc exists"
```

If any files exist, warn the user and ask whether to overwrite or skip each one.

### Step 4: Initialize Parent Git Repo

If not already a git repo:

```bash
git init
```

Create `.gitignore`:

```
# Repo clones are submodules/independent repos - don't track their contents
{list each repo directory}/

# Non-repo directories
{list each non-repo directory}/

# Environment
.env
.envrc

# Node
node_modules/

# OS
.DS_Store

# Claude Code
.claude/
```

**Important:** Each repo directory goes in .gitignore since the parent repo only tracks workspace-level files (CLAUDE.md, docs/, etc.), not the repo contents.

### Step 5: Create CLAUDE.md

Generate a CLAUDE.md following this template. Adapt the content based on the discovered repos:

```markdown
# {Project Name} - Multi-Repo Workspace

This is the parent folder containing all {Project Name} repositories:

| Repo | Directory | Purpose |
|------|-----------|---------|
{for each repo: | {Name} | `{directory}/` | {purpose} | }

## Starting Work

From this parent folder, use:

\`\`\`
/start <repo> <description>
\`\`\`

Where `<repo>` is one of:
{for each repo: - `{alias}` - {purpose} }

### Examples

\`\`\`
{2-3 realistic examples like: /start frontend fix button alignment}
\`\`\`

## Worktree Safety Rules

**NEVER edit files in main clone directories.** A PreToolUse hook enforces this.

Main clones (read-only):
{for each repo: - `{directory}/` }

Worktrees (where you work):
{for each repo: - `{directory}-fix-something/`, `{directory}-add-feature/`, etc. }

Always use `/start` to create an isolated worktree before any work. After creating a worktree, you MUST `cd` into it before doing any work. All file paths must point to the worktree, not the main clone.

## Plan Files

**Always write plan files to `docs/`** (e.g., `docs/my-feature-plan.md`). Never use `.claude/plans/` — that path requires permission prompts.

## Workflow

1. **`/start <repo> <description>`** - Create worktree, get oriented
2. **`/plan`** - For non-trivial work, plan first
3. **`/implement`** - Execute the plan
4. **`/shipit`** - Test, review, PR, merge, deploy, verify

## Existing Worktrees

Active worktrees appear as sibling folders (e.g., `{first-repo}-fix-something/`).

To see all:
\`\`\`bash
{for each repo: cd {directory} && git worktree list && cd ..}
\`\`\`
```

If any repo has a CLAUDE.md with important project-specific info, mention it in a "Repo-Specific Instructions" section.

### Step 6: Create Guard Hook

Create `.claude/hooks/guard-main-worktree.sh`:

```bash
#!/bin/bash
# Guard against editing files in main clone directories.
# Runs as a PreToolUse hook for Edit/Write tools.
# Exit 0 = allow, Exit 2 = block (stderr shown as feedback).

FILE_PATH="${TOOL_INPUT_file_path:-}"

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

WORKSPACE="{absolute path to workspace}"

# Main clone directory names
MAIN_DIRS="{space-separated list of repo directories}"

for dir in $MAIN_DIRS; do
  if [[ "$FILE_PATH" == "$WORKSPACE/$dir/"* ]]; then
    echo "" >&2
    echo "BLOCKED: Editing files in main clone '$dir/' is not allowed." >&2
    echo "Main clones must stay clean — all work happens in worktrees." >&2
    echo "" >&2
    echo "You're editing:  $FILE_PATH" >&2
    echo "You probably want: $WORKSPACE/$dir-<your-feature>/..." >&2
    echo "" >&2
    echo "Use /start to create a worktree first." >&2
    exit 2
  fi
done

exit 0
```

Make it executable: `chmod +x .claude/hooks/guard-main-worktree.sh`

### Step 7: Create settings.local.json

Create `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "Skill(test-review)",
      "Skill(docs-review)",
      "Skill(shipit)",
      "Skill(implement)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "{absolute path to workspace}/.claude/hooks/guard-main-worktree.sh"
          }
        ]
      }
    ]
  }
}
```

### Step 8: Create Workspace /start Command

Create `.claude/commands/start.md` — this is the workspace-specific `/start` that overrides the global single-repo `/start`.

The generated command should follow this structure:

````markdown
---
description: Create git worktree(s) for focused work in this workspace
allowed-tools: Read, Glob, Bash, Task
---

# Multi-Repo Worktree Session

Create a new git worktree for focused, isolated work on a {Project Name} project.

**Usage:** `/start <repo> <description>`

Arguments: $ARGUMENTS

## Available Repos

| Alias | Directory | Purpose |
|-------|-----------|---------|
{for each repo: | `{alias}` | {directory} | {purpose} | }

## Instructions

### Step 1: Parse Arguments

Parse $ARGUMENTS to extract:
1. **Repo alias** — the first word
2. **Full task description** — everything after the repo alias, preserved verbatim

The description serves two purposes:
- 2-4 keywords extracted for branch/folder name
- Full text preserved as the task to work on after setup

If invalid or missing, show usage with the repo table and examples, then stop.

### Step 2: Map Alias to Directory

```
WORKSPACE="{absolute path to workspace}"

Alias mappings:
{for each repo:   {alias} → {directory} }
```

Verify the directory exists. If not, error with helpful message.

### Step 3: Generate Names

1. Get datetime: `date +%Y%m%d-%H%M`
2. Extract 2-4 keywords, lowercase, hyphenated
3. Branch: `feat/sess-{YYYYMMDD-HHMM}-{keywords}`
4. Worktree: `$WORKSPACE/{directory}-{keywords}`

### Step 4: Create the Worktree

```bash
cd "$WORKSPACE/{directory}"
git fetch origin {default-branch}
git worktree add -b {branch} "$WORKSPACE/{directory}-{keywords}" origin/{default-branch}
```

### Step 5: Change to Worktree

**CRITICAL:** Change working directory immediately:
```bash
cd "$WORKSPACE/{directory}-{keywords}"
```

All file operations after this point must use paths under the worktree.

### Step 6: Read Project Context

Read from the NEW worktree if they exist:
- `CLAUDE.md`
- `README.md`
- `docs/README.md`

### Step 7: Summarize and Proceed

```
## Worktree Created

**Project:** {repo name}
**Branch:** feat/sess-YYYYMMDD-HHMM-keywords
**Working directory:** /path/to/worktree

**Rename session:** /rename {keywords}
```

Then **immediately proceed to work on the full task description**.
Do NOT ask "What would you like to work on?" — the user already said in the arguments.

## Notes

- Worktrees are flat siblings to main clones
- **NEVER edit files in main clone directories** — a PreToolUse hook blocks this
- Use `/cleanup` to remove worktree after PR merged
- Use `/tidy-all-worktrees` to review all worktrees
````

### Step 9: Create .envrc

Create a `.envrc` file. At minimum it needs `GH_TOKEN` for `gh` CLI operations.

Check the user's other workspaces for their GH_TOKEN pattern:
```bash
grep "GH_TOKEN" ~/.claude/../../../Projects/*/.envrc 2>/dev/null | head -5
```

Generate the `.envrc`:

```bash
# {Project Name} workspace environment

# GitHub: account token for gh CLI and GitHub operations
export GH_TOKEN={token from other projects, or placeholder}
```

Ask the user if they need additional env vars (GCP project, conda env, API keys, etc.).

After creating, remind the user to run `direnv allow` if they use direnv.

### Step 10: Create docs/ Directory

```bash
mkdir -p docs
```

This is where plan files go (avoids `.claude/plans/` permission prompts).

### Step 11: Initial Commit

Stage and commit the workspace-level files:

```bash
git add CLAUDE.md .gitignore .claude/
# Note: .envrc is gitignored (contains secrets)
git commit -m "Set up multi-repo workspace with worktree workflow"
```

### Step 12: Report

Summarize everything that was created:

```
## Workspace Setup Complete

**Created:**
- `.git/` — parent git repo initialized
- `CLAUDE.md` — workspace map and instructions
- `.gitignore` — ignores repo dirs, .env, node_modules
- `.claude/settings.local.json` — permissions and guard hook config
- `.claude/hooks/guard-main-worktree.sh` — blocks edits to main clones
- `.claude/commands/start.md` — workspace-specific /start command
- `.envrc` — direnv environment config
- `docs/` — for plan files

**Ready to use:**
- `/start {first-alias} <description>` — start working
- `direnv allow` — activate .envrc (run this in your terminal)

**Repos configured:**
{repo table}
```
