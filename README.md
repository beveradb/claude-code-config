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
│   └── docs-maintain.md  # Documentation maintenance
└── settings.json         # Optional: model and plugin settings
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

### Setup & Configuration

| Command | Description | When to Use |
|---------|-------------|-------------|
| `/setup-playwrights` | Set up multiple isolated Playwright browser instances | Browser automation setup |

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

## Multi-Browser Playwright MCP Setup

This config includes three separate Playwright MCP server instances, each with its own persistent browser profile. This enables controlling multiple independent browser windows simultaneously from Claude Code sessions.

### How It Works

Three MCP servers are registered at user scope (in `~/.claude.json`):

| Server | Profile Directory | Tools Prefix |
|--------|------------------|--------------|
| `playwright-1` | `~/.playwright-profiles/profile-1` | `mcp__playwright-1__*` |
| `playwright-2` | `~/.playwright-profiles/profile-2` | `mcp__playwright-2__*` |
| `playwright-3` | `~/.playwright-profiles/profile-3` | `mcp__playwright-3__*` |

Each instance:
- Opens its own Chrome window
- Has isolated cookies, local storage, and session data (via `--user-data-dir`)
- Can be controlled independently and simultaneously

### Setup

The servers were added with:

```bash
# Create profile directories
mkdir -p ~/.playwright-profiles/profile-{1,2,3}

# Register each instance at user scope
claude mcp add --transport stdio playwright-1 --scope user -- npx @playwright/mcp@latest --user-data-dir ~/.playwright-profiles/profile-1
claude mcp add --transport stdio playwright-2 --scope user -- npx @playwright/mcp@latest --user-data-dir ~/.playwright-profiles/profile-2
claude mcp add --transport stdio playwright-3 --scope user -- npx @playwright/mcp@latest --user-data-dir ~/.playwright-profiles/profile-3
```

Then add permissions to `settings.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__playwright-1__*",
      "mcp__playwright-2__*",
      "mcp__playwright-3__*"
    ]
  }
}
```

### Usage

In any Claude Code session, specify which browser to use:

```
Use playwright-1 to navigate to example.com
Use playwright-2 to review the staging site
Use playwright-3 to check the production dashboard
```

All three can be used in parallel within a single session, or across separate terminal sessions.

### Customization

You can pass additional flags per-instance. For example, to add vision capabilities or use a specific browser:

```bash
claude mcp add --transport stdio playwright-1 --scope user -- npx @playwright/mcp@latest --user-data-dir ~/.playwright-profiles/profile-1 --caps vision --browser chrome
```

Run `npx @playwright/mcp@latest --help` for all available options.

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
