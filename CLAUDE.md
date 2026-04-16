# Global Claude Code Instructions

## Workflow Commands

Use these slash commands to maintain consistency across sessions and worktrees:

### Starting Work
```
/start <description>   # Always start new work in isolated worktree
```

### Development Cycle
```
/plan        # Design before coding (for non-trivial work)
/implement   # Execute from plan
/test        # Verify tests pass
```

### Before Creating PR (in order)
```
/test-review   # Assess test quality, coverage, and completeness
/docs-review   # Update docs if needed
/coderabbit    # Run CodeRabbit CLI locally, fix issues (max 3 cycles)
/pr            # Create PR (auto-adds @coderabbitai ignore)
```

### Ship It All (one command)
```
/shipit        # Assess progress, run remaining steps, merge, deploy, verify prod
```
Use `/shipit` when returning to a session where implementation is done. It intelligently skips completed steps and runs: test → test-review → docs-review → coderabbit → version bump → pr → merge → wait for deploy → verify prod health → test new functionality.

Options: `--skip-prod-test` (skip prod testing), `--dry-run` (preview only)

### After Shipping
```
/cleanup            # Clean up current worktree after PR merged (end of session)
```

### Periodic Maintenance
```
/tidy-all-worktrees # Review ALL worktrees, clean merged, organize (interactive)
/docs-maintain      # Documentation health check
/fix-main           # Fix accidental changes in main worktree
```

## Key Rules

1. **Always use worktrees** - Never commit directly to main. Start with `/start`.

2. **Review before PR, not after** - Run `/coderabbit` locally before `/pr`. This runs `coderabbit --prompt-only` for efficient LLM-friendly output.

3. **PRs must include `@coderabbitai ignore`** - The `/pr` command adds this automatically. We review locally, not via GitHub bot.

4. **Max 3 review cycles** - Fix real issues, don't chase perfection. Skip pure nitpicks.

5. **Tests are mandatory** - Run `/test` before PR. Don't skip.

6. **Test quality matters** - Run `/test-review` to assess coverage (70%+ target) and ensure appropriate test types (unit, integration, e2e, etc.) for the changes.

7. **Docs stay current** - Run `/docs-review` before PR to check if docs need updates.

8. **Use `gh` CLI for GitHub** - Always use the `gh` CLI for all GitHub operations (PRs, issues, repos, etc.). Do not use the GitHub MCP. The `GH_TOKEN` env var must be set (via direnv) to control which account is used per-directory.

## Quick Reference

| Phase | Commands |
|-------|----------|
| Start | `/start <desc>` |
| Build | `/plan` → `/implement` → `/test` |
| Ship | `/test-review` → `/docs-review` → `/coderabbit` → `/pr` |
| Ship (one cmd) | `/shipit` (assesses + completes all remaining steps) |
| Clean up | `/cleanup` (current worktree) or `/tidy-all-worktrees` (all) |
| Troubleshoot | `/fix-main` (if main worktree has accidental changes) |