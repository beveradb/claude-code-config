---
description: Create a new git worktree for focused work on a task
allowed-tools: Read, Glob, Bash, Task
---

# New Worktree Session

Create a new git worktree from the latest main branch for focused, isolated work.

**Required argument:** A brief description of the work (e.g., "investigate prod auth flow")

Description provided: $ARGUMENTS

## Instructions

### Step 1: Validate Input

If no description was provided (empty or blank $ARGUMENTS), respond with:
```
Usage: /new-worktree <description of work>

Examples:
  /new-worktree fix authentication bug
  /new-worktree add export feature
  /new-worktree investigate slow queries
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

```bash
# Fetch latest from origin
git fetch origin main

# Create new worktree with branch based on origin/main
git worktree add -b {branch-name} {worktree-path} origin/main
```

Report success with:
- Branch name created
- Worktree path
- Command to cd into it

### Step 4: Provide Next Steps

Tell the user:
```
## Worktree Created

**Branch:** feat/sess-YYYYMMDD-HHMM-keywords
**Location:** /path/to/worktree

To start working:
  cd {worktree-path}

Or open in a new terminal/editor.

## Suggested Workflow

1. `/plan <feature>` - Create implementation plan
2. `/implement` - Implement from plan
3. `/shipit` - Ship it all (test → review → docs → PR → merge → deploy → verify)

Or run individual steps:
3. `/test` - Run tests
4. `/coderabbit` - Run CodeRabbit CLI locally, fix issues
5. `/docs-review` - Check docs before PR
6. `/pr` - Create PR (auto-ignores CodeRabbit bot)

After merge:
7. `/cleanup` - Clean up this worktree
```

### Step 5: Read Project Context

Read key documentation if it exists:
- `CLAUDE.md` (project instructions)
- `docs/README.md` (current status)
- `docs/CONTEXT.md` (background)
- `docs/LESSONS-LEARNED.md` (recent lessons)

If no docs exist, that's fine - just note it.

### Step 6: Summarize and Confirm Ready

Provide:
1. **Worktree created:** path and branch
2. **Project context:** Key points from docs (if available)
3. **Recent activity:** Notable recent changes (from docs or git log)

End with: **"Ready for your task. What would you like to work on?"**

Then output the rename command as the final line:
```
**Rename session:** /rename {keywords}
```

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
