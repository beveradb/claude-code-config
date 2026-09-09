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

2. **Review before PR, not after** - Run `/coderabbit` locally before `/pr`. This runs `coderabbit review` (plain text is the default output) for efficient LLM-friendly review.

3. **Review locally with `/coderabbit` BEFORE opening a PR, then add `@coderabbitai ignore`** - Always run `/coderabbit` and address feedback *before* `/pr`, never after. Only add `@coderabbitai ignore` to a PR description once a local CodeRabbit review has **successfully completed on that branch and its feedback has been addressed**. If no successful local review was done, open the PR **without** the ignore line so the GitHub bot reviews it — never leave a PR with neither a local review nor the bot review.

4. **Max 3 review cycles** - Fix real issues, don't chase perfection. Skip pure nitpicks.

5. **Tests are mandatory** - Run `/test` before PR. Don't skip.

6. **Test quality matters** - Run `/test-review` to assess coverage (70%+ target) and ensure appropriate test types (unit, integration, e2e, etc.) for the changes.

7. **Docs stay current** - Run `/docs-review` before PR to check if docs need updates.

8. **Use `gh` CLI for GitHub** - Always use the `gh` CLI for all GitHub operations (PRs, issues, repos, etc.). Do not use the GitHub MCP. The `GH_TOKEN` env var must be set (via direnv) to control which account is used per-directory.

## Command layering — this repo stays GENERIC

This repo (`claude-code-config`) is the **generic, cross-project** command layer.
It is cloned into every per-project config dir (`~/.claude`, `~/.claude-aquarius`,
`~/.claude-nomadkaraoke`, `~/.claude-life360`), so **anything project-specific here
leaks into every project.** Three layers, in precedence order:

1. **Project override** — a project's own repo, `.claude/commands/<cmd>.md`. Wins
   when the cwd is inside that project. This is where project-specific behaviour
   belongs (e.g. Aquarius's dev-first `/shipit`, `/start`, `/pr`).
2. **Generic shared (this repo)** — the fallback used everywhere. Keep it free of
   any project's names, URLs, branch conventions, or release flow.
3. **Project `CLAUDE.md`** — narrative overrides layered on top.

**Rule:** never copy a project's command *up* into this repo. If `/shipit` needs to
behave differently for a project, add/edit that command in the **project's** repo
under `.claude/commands/`, not here. A `pre-commit` hook (`githooks/pre-commit`,
enabled via `git config core.hooksPath githooks`) blocks staged `commands/*.md`
that contain project-specific (Aquarius) markers; bypass only with `--no-verify`.

## Local Tools

- **`md2pdf <input.md> [output.pdf]`** — render any Markdown file to a clean, watermark-free PDF
  (headless Chrome via `md-to-pdf`, styled like markdowntopdf.com). Use this whenever I ask for a
  PDF version of a Markdown doc. Writes `<input>.pdf` beside the source unless an output path is
  given. Theme lives at `~/Projects/md2pdf/style.css` (edit to restyle); override per-run with
  `md2pdf --css other.css in.md` or `MD2PDF_CSS=...`.

## Quick Reference

| Phase | Commands |
|-------|----------|
| Start | `/start <desc>` |
| Build | `/plan` → `/implement` → `/test` |
| Ship | `/test-review` → `/docs-review` → `/coderabbit` → `/pr` |
| Ship (one cmd) | `/shipit` (assesses + completes all remaining steps) |
| Clean up | `/cleanup` (current worktree) or `/tidy-all-worktrees` (all) |
| Troubleshoot | `/fix-main` (if main worktree has accidental changes) |