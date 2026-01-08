# Global Claude Code Instructions

## Workflow Commands

Use these slash commands to maintain consistency across sessions and worktrees:

### Starting Work
```
/new-worktree <description>   # Always start new work in isolated worktree
```

### Development Cycle
```
/plan        # Design before coding (for non-trivial work)
/implement   # Execute from plan
/test        # Verify tests pass
```

### Before Creating PR (in order)
```
/docs-review   # Update docs if needed
/coderabbit    # Run CodeRabbit CLI locally, fix issues (max 3 cycles)
/pr            # Create PR (auto-adds @coderabbitai ignore)
```

### Maintenance
```
/worktree-cleanup   # Clean up merged worktrees periodically
/docs-maintain      # Periodic documentation health check
```

## Key Rules

1. **Always use worktrees** - Never commit directly to main. Start with `/new-worktree`.

2. **Review before PR, not after** - Run `/coderabbit` locally before `/pr`. This runs `coderabbit --prompt-only` for efficient LLM-friendly output.

3. **PRs must include `@coderabbitai ignore`** - The `/pr` command adds this automatically. We review locally, not via GitHub bot.

4. **Max 3 review cycles** - Fix real issues, don't chase perfection. Skip pure nitpicks.

5. **Tests are mandatory** - Run `/test` before PR. Don't skip.

6. **Docs stay current** - Run `/docs-review` before PR to check if docs need updates.

7. **GitHub CLI auth** - When using the `gh` CLI instead of the GitHub MCP, run `gh auth switch` first to ensure you're using the correct account.

## Quick Reference

| Phase | Commands |
|-------|----------|
| Start | `/new-worktree <desc>` |
| Build | `/plan` → `/implement` → `/test` |
| Ship | `/docs-review` → `/coderabbit` → `/pr` |
| Clean | `/worktree-cleanup` |
