---
name: worktree-pr-workflow
description: "Run Andrew's standard worktree-to-PR development workflow: start isolated work, plan, implement, test, review, create or finish a PR, ship, clean up, or maintain worktrees. Use when Andrew names these workflow phases or asks to carry work through them."
---

# Worktree and PR Workflow

Use the existing Claude command documents as the single source of truth for this workflow. Do not reproduce their procedures in this skill. Select the requested action, read its complete command file from `~/.claude/commands/<action>.md`, translate Claude host syntax into available Codex capabilities, and carry out the workflow.

Supported actions are the Markdown filenames in `~/.claude/commands/`, including `start`, `plan`, `implement`, `test`, `test-review`, `docs-review`, `coderabbit`, `pr`, `shipit`, `cleanup`, `tidy-all-worktrees`, `fix-main`, `refresh`, `setup-workspace`, `setup-playwrights`, `docs-maintain`, `autonomous`, `export`, `seo-review`, `seo-content`, `gcp-billing`, and `edge`.

## Workspace routing

Before loading a generic command, resolve the current repository/worktree path. If it belongs to the Aquarius workspace or one of its child/sibling worktrees, route through `$aquarius-workflows`. If it belongs to Nomad Karaoke or one of its child worktrees, route through `$nomadkaraoke-workflows`. Workspace routing wins even when the same action exists globally. This ensures project-specific base branches, release gates, repository maps, and cleanup rules apply from nested Git repositories whose discovery would otherwise stop at their own root.

## Invocation

Interpret `$worktree-pr-workflow <action> [arguments]` as the Claude equivalent `/<action> [arguments]`. Preserve all arguments. Natural-language requests such as "start a worktree for…", "ship it", or "clean up this worktree" should select the matching action. If no action can be inferred, list the available command filenames and ask which one to run.

## Host translation

- Treat `$ARGUMENTS` in a command file as the arguments supplied with this invocation.
- Treat instructions such as "run `/test`" as recursive routing through this same skill: read `test.md` and execute it.
- Use Codex's available filesystem, shell, collaboration, and other tools for the intent of Claude-specific tool names such as `Read`, `Glob`, `Grep`, `Bash`, `Edit`, `Write`, or `Task`.
- A command's `allowed-tools` frontmatter documents expected capabilities; it does not grant permissions or override Codex approval and sandbox rules.
- Ignore Claude UI-only instructions that cannot apply, such as `/rename`, while preserving their useful outcome in the status report.
- Never claim that `cd` in one shell call changes Codex's persistent working directory. Pass the new worktree explicitly as the working directory for every later tool call.
- Honor project `AGENTS.md`, `CLAUDE.md`, and repository-specific workflow files. When a project-local workflow conflicts with the global command, the closer project instruction wins.

## Safety

Read the selected command before acting and inspect current repository/worktree state. Do not infer permission for merges, deployments, destructive cleanup, external messages, or production mutations beyond the user's request. A terminal request such as `shipit` authorizes its documented workflow, subject to Codex approval boundaries and repository-specific gates. Preserve unrelated dirty-tree changes and stop for a material ambiguity that could target the wrong repository or worktree.

Report which canonical command file governed the action and any Claude-only step that required adaptation or could not be performed.
