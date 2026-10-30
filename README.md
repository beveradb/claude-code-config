# Claude Code Workflow Configuration

A production-ready workflow system for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that enforces best practices through custom slash commands.

**What this does:** Provides 12 slash commands that structure your development workflow - from starting isolated work in git worktrees, through planning, implementing, testing, reviewing, and shipping to production with a single command.

## Why This Workflow?

### The Problem

Without structure, AI-assisted development can become chaotic:
- Working directly on `main` leads to messy commits and conflicts
- Skipping tests and reviews leads to bugs in production
- Forgetting documentation leads to knowledge silos
- Manual multi-step deployments are error-prone

### The Solution

This workflow enforces discipline through automation:

| Principle | Implementation |
|-----------|----------------|
| **Isolated work** | Every task starts in a new git worktree (`/start`) |
| **Plan before code** | Design implementation before writing (`/plan`) |
| **Tests are mandatory** | Must pass before PR (`/test`) |
| **Review locally** | CodeRabbit runs before PR, not after (`/coderabbit`) |
| **Docs stay current** | Checked before every merge (`/docs-review`) |
| **Ship with confidence** | One command does everything (`/shipit`) |

## Keep this repo generic (command layering)

This repo is the **generic, cross-project** command layer. It is cloned into every
per-project Claude Code config dir, so **anything project-specific added here leaks
into every project.** Commands resolve in this precedence:

1. **Project override** — a project's own repo at `.claude/commands/<cmd>.md`, used
   when the cwd is inside that project. Project-specific behaviour (a particular
   release flow, environment names, branch conventions) belongs **here**.
2. **Generic shared (this repo)** — the everywhere fallback. Keep it free of any
   project's names, URLs, or workflow specifics.
3. **Project `CLAUDE.md`** — narrative overrides.

**Never copy a project's command up into this repo.** To make `/shipit` (or any
command) behave differently for one project, add/edit it in that **project's** repo
under `.claude/commands/`. A `pre-commit` hook (`githooks/pre-commit`) enforces this
by rejecting staged `commands/*.md` that contain project-specific markers. Enable it
per clone with:

```bash
git config core.hooksPath githooks
```

## Quick Start

### Installation

1. **Clone this repo** into your Claude Code config directory:

```bash
# Back up existing config if you have one
[ -d ~/.claude ] && mv ~/.claude ~/.claude.backup

# Clone the config
git clone https://github.com/beveradb/claude-code-config.git ~/.claude
```

2. **Or merge with existing config:**

```bash
# Clone to a temp location
git clone https://github.com/beveradb/claude-code-config.git /tmp/claude-config

# Copy the commands (the key part)
cp -r /tmp/claude-config/commands ~/.claude/

# Copy CLAUDE.md (global instructions)
cp /tmp/claude-config/CLAUDE.md ~/.claude/

# Optionally merge settings.json manually if you have custom settings
```

3. **Verify installation:**

```bash
# Start Claude Code in any project
claude

# Test a command
/start test feature
```

You should see Claude create a new worktree and branch.

### Directory Structure

After installation, your `~/.claude` directory should contain:

```
~/.claude/
├── CLAUDE.md              # Global instructions Claude follows
├── commands/              # Slash command definitions
│   ├── start.md          # Create new worktree
│   ├── plan.md           # Design implementation
│   ├── implement.md      # Execute from plan
│   ├── test.md           # Run tests
│   ├── coderabbit.md     # Local code review
│   ├── docs-review.md    # Documentation check
│   ├── pr.md             # Create pull request
│   ├── shipit.md         # Ship to production
│   ├── cleanup.md        # Clean up worktree
│   ├── tidy-all-worktrees.md  # Clean all worktrees
│   ├── fix-main.md       # Fix main worktree
│   ├── docs-maintain.md  # Documentation maintenance
│   └── wrap.md           # Write a session record (any project)
├── hooks/                # SessionStart hook (session_context.py) — see Session Continuity
└── settings.json         # Optional: model and plugin settings (gitignored)
```

## The Workflow

### Starting Work: Always Use Worktrees

**Never commit directly to main.** Always start with:

```
/start fix authentication bug
```

This creates:
- A new git worktree (sibling folder to your repo)
- A feature branch based on latest `main`
- Isolated environment for your work

**Why worktrees?**
- Work on multiple features in parallel
- Keep `main` always clean and deployable
- Easy cleanup when done
- No accidental commits to wrong branch

### Development Cycle

```
/plan add user export feature    # Design before coding
/implement                       # Execute the plan
/test                            # Verify everything works
```

### Before Creating a PR

Run these in order:

```
/docs-review     # Check if documentation needs updates
/coderabbit      # Run local CodeRabbit review, fix issues
/pr              # Create the PR (auto-adds @coderabbitai ignore)
```

**Why review locally?** Running CodeRabbit before the PR means:
- Issues fixed before reviewers see them
- No back-and-forth on the PR
- PRs are already clean when opened

### Ship Everything at Once

When you're ready to ship (or returning to a session where implementation is done):

```
/shipit
```

This intelligent command:
1. Assesses what's already done
2. Runs remaining steps: test → review → docs → version bump → PR → merge → deploy → verify
3. Skips completed steps automatically
4. Verifies production is healthy after deployment

Options:
- `--skip-prod-test` - Skip testing new functionality in production
- `--dry-run` - Preview what would happen without executing

### After Shipping

```
/cleanup              # Clean up current worktree
```

Or periodically:

```
/tidy-all-worktrees   # Review and clean ALL worktrees (interactive)
```

## Command Reference

### Starting & Planning

| Command | Description | When to Use |
|---------|-------------|-------------|
| `/start <desc>` | Create new worktree for focused work | Always - start every task this way |
| `/plan <feature>` | Design implementation before coding | For non-trivial features |
| `/implement` | Execute steps from existing plan | After `/plan` |

### Development

| Command | Description | When to Use |
|---------|-------------|-------------|
| `/test` | Run tests and report results | Before PR, after changes |

### Review & Ship

| Command | Description | When to Use |
|---------|-------------|-------------|
| `/coderabbit` | Run local CodeRabbit review, fix issues | Before PR (max 3 cycles) |
| `/docs-review` | Check and update documentation | Before PR |
| `/pr` | Create PR with `@coderabbitai ignore` | After review passes |
| `/shipit` | Run all remaining steps to ship | When ready to ship |

### Maintenance

| Command | Description | When to Use |
|---------|-------------|-------------|
| `/cleanup` | Clean up current worktree after PR merge | End of session |
| `/tidy-all-worktrees` | Review and clean ALL worktrees | Periodic maintenance |
| `/fix-main` | Fix accidental changes in main worktree | When main has uncommitted changes |
| `/docs-maintain` | Documentation health check | Periodic maintenance |
| `/wrap` | Write a session record for future sessions | End of any session (code or not) |

### Setup & Configuration

| Command | Description | When to Use |
|---------|-------------|-------------|
| `/setup-playwrights` | Set up pooled, per-config-dir Playwright browser profiles (`pw-pool`) | Browser automation setup |

## Typical Session

```bash
# Start Claude Code in your project
cd ~/projects/myapp
claude

# Start isolated work
> /start add export feature

# Claude creates worktree, you cd into it
cd ../myapp-add-export

# Plan the feature
> /plan add CSV and JSON export for user data

# Implement from the plan
> /implement

# Ship it all
> /shipit

# Clean up when done
> /cleanup
```

## Customization

### Modifying Commands

Each command is a Markdown file in `~/.claude/commands/`. The format:

```markdown
---
description: Short description for /help
allowed-tools: Read, Glob, Bash, Edit, Write, Task
---

# Command Title

Instructions Claude follows when you invoke the command...
```

Feel free to modify commands to match your workflow.

### Settings

The optional `settings.json` configures:

```json
{
  "model": "opus",
  "enabledPlugins": {
    "frontend-design@claude-plugins-official": true,
    "context7@claude-plugins-official": true
  },
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "afplay /System/Library/Sounds/Blow.aiff"
          }
        ]
      }
    ]
  }
}
```

- `model`: Which Claude model to use
- `enabledPlugins`: Official plugins to enable
- `hooks`: Commands to run on events (e.g., play sound when Claude stops)

### Global Instructions

`CLAUDE.md` contains instructions Claude follows for all sessions. This is where workflow rules are defined. Modify to match your preferences.

## Session Continuity (automatic session records)

Every session can leave a durable, discoverable record of what was done and
learned, and every new session automatically picks up recent records for the
project it starts in — so context survives across sessions (and machines).

**Components:**

| Piece | What it does |
|-------|--------------|
| `/wrap` (`commands/wrap.md`) | Writes a session record to `docs/sessions/<YYYY-Qn>/YYYY-MM-DD-<topic>.md`. Works in ANY folder — git or not, code or not (e.g. a budget-reconciliation session, not just code changes). |
| `SessionStart` hook (`hooks/session_context.py`) | On session start, reads the newest 3 session records for the current project and injects them into context automatically. Read-only; silent when there are none. |
| `/docs-review`, `/docs-maintain` | Adopt/enforce the docs layout below. `/docs-maintain` can migrate a legacy flat `docs/archive/` into it (report-first). |

**Docs layout convention (shared by all of the above):**

```
docs/
├── sessions/<YYYY-Qn>/YYYY-MM-DD-<topic>.md   # session records (the hook reads these)
├── designs/<YYYY-Qn>/                          # design & spec docs
└── plans/<YYYY-Qn>/                            # implementation plans
```

Quarter is `YYYY-Qn` where `n = ((month - 1) // 3) + 1` (e.g. September → `2026-Q3`).
The hook looks for `docs/sessions/` first, falling back to a legacy `docs/archive/`
for repos not yet migrated.

### Reproducing on a new machine

`commands/wrap.md` and `hooks/session_context.py` are committed, so cloning this
repo brings them along. **But the hook only fires once it is registered in
`settings.json`, which is gitignored (it holds secrets).** After cloning on a
new machine, add this entry under the `"hooks"` object in `~/.claude/settings.json`:

```json
"SessionStart": [
  {
    "hooks": [
      { "type": "command", "command": "python3 \"$HOME/.claude/hooks/session_context.py\"" }
    ]
  }
]
```

Then verify:

```bash
# Run the hook's own tests
python3 ~/.claude/hooks/test_session_context.py   # expect: "All N tests passed."

# Simulate a session start in a project that has session records
mkdir -p /tmp/sc-check/docs/sessions/2026-Q3
echo '# demo record' > /tmp/sc-check/docs/sessions/2026-Q3/2026-01-01-demo.md
echo '{"cwd":"/tmp/sc-check","source":"startup"}' | python3 ~/.claude/hooks/session_context.py
rm -rf /tmp/sc-check
```

Requires Python 3 (stdlib only). Design and full implementation plan:
`docs/superpowers/specs/2026-09-09-session-continuity-design.md`.

## Pooled Playwright Browser Profiles (`pw-pool`)

Persistent, signed-in Playwright browser profiles, grouped into **pools** (one per identity,
e.g. one Google account each) and shared safely across many parallel Claude sessions.

### How it works

- Profiles live in `~/.playwright-profiles/<pool>/chrome-1..N` and `firefox-1..N`. Pool names,
  account labels and counts (default 5 Chrome + 2 Firefox) come from the machine-local
  `~/.playwright-profiles/pools.json`, which is not in this repo.
- Each Claude config dir is bound to **exactly one pool**. It registers three small "slot" MCP
  servers (`playwright-chrome-1`, `playwright-chrome-2`, `playwright-firefox-1`), each running
  `bin/pw-pool slot --pool <pool> --browser <b>`.
- A slot is a stdio proxy. It answers `initialize`/`tools/list` from a cache, so idle sessions
  cost one small Python process per slot and no node or browser. On the first browser tool call
  it claims a free profile in its pool with `flock`, which is released automatically if the
  process dies, and starts the real `@playwright/mcp` on that profile.
- The claim is released on `browser_close`, after `idle_minutes` (default 30) with no tool
  calls, or when the session exits.
- Slots add two tools: `browser_pool_status` (who holds what) and `browser_use_profile` (pin a
  specific profile).
- **Chrome profiles are signed in** to the pool's account, in Chrome itself and on the web.
  **Firefox profiles are deliberately kept signed out**, so every session also has a clean,
  logged-out browser (`signed_out` in `pools.json`, default `["firefox"]`, overridable per pool).
  The Firefox slots say so in their MCP instructions. `pw-pool status` warns if one picks up a
  Google session.
- Guidance for Claude is in `rules/playwright.md`.

### Commands

```bash
pw-pool status [--all]                         # profiles in this config dir's pool: free / held by session X / idle time
pw-pool clone personal/chrome-1 --unused       # seed never-used profiles from a signed-in one (source must be closed)
pw-pool release personal/chrome-2 [--force]    # free a stale claim; --force closes a live session's browser
pw-pool install --config-dir ~/.claude --pool personal   # (re)register slots + permissions for a config dir
```

### Setup

See `/setup-playwrights`. In short:

1. Write `~/.playwright-profiles/pools.json`:
   `{"pools": {"personal": {"account": "me@example.com"}, "work": {"account": "me@work.com"}}}`.
   Optional keys: `chrome`, `firefox` (counts, also per pool), `signed_out` (browsers kept
   logged out, default `["firefox"]`, also per pool), `idle_minutes`, `mcp_command`, `mcp_args`.
2. Run `pw-pool install --config-dir <dir> --pool <pool>` for each config dir.
3. Sign in once in `<pool>/chrome-1`, to the Google account and to Chrome itself. Close it, then
   run `pw-pool clone <pool>/chrome-1 --unused`. Leave the Firefox profiles signed out.

Tests: `python3 -m unittest discover -s tests/pw_pool` (uses a fake Playwright MCP, no browser).

## Requirements

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed
- Git (with worktree support - any modern version)
- [GitHub CLI](https://cli.github.com/) (`gh`) for PR commands
- [CodeRabbit CLI](https://www.npmjs.com/package/coderabbit) for review commands (`npm install -g coderabbit`)

## FAQ

**Q: Can I use just some commands?**
A: Yes! Each command is independent. Copy only the ones you want to `~/.claude/commands/`.

**Q: What if I don't use worktrees?**
A: You can modify `/start` or skip it. The other commands work on any branch.

**Q: What if I don't have CodeRabbit?**
A: Skip `/coderabbit` or remove it from `/shipit`. The workflow still works.

**Q: How do I update?**
A: `cd ~/.claude && git pull` - or manually copy updated files.

**Q: Will this overwrite my settings?**
A: `settings.json` is in `.gitignore` specifically to avoid this. Your settings are safe after initial setup.

## Philosophy

This workflow is opinionated. The core beliefs:

1. **Structure enables speed** - Consistent workflows mean less decision fatigue
2. **Review before submit** - Fix issues before others see them
3. **Isolation prevents accidents** - Worktrees keep work separated
4. **One command to ship** - Reduce manual steps, reduce errors
5. **Tests aren't optional** - They catch bugs before users do
6. **Documentation is code** - It should be updated with the code

If these don't match your style, fork and customize!

## Contributing

Issues and PRs welcome at [github.com/beveradb/claude-code-config](https://github.com/beveradb/claude-code-config).

## License

MIT - Use however you like.
