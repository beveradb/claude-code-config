---
name: claude-codex-compat
description: "Convert a Claude Code project into a maintainable Claude Code + Codex setup, using shared skill sources and symlinks instead of duplicated files. Use when adapting a Claude project for Codex or reviewing its cross-agent setup."
---

# Claude Codex Compat

Adapt an existing Claude Code project so Claude Code and Codex can both use it without creating competing copies of shared knowledge or workflows. Preserve the project's existing behavior; add only the Codex-facing adapters that the user authorizes.

## Core model

Classify project material before changing it:

- **Shared knowledge:** project facts, architecture, runbooks, templates, and other ordinary documentation belong in normal tracked locations such as `docs/`, `references/`, and `templates/`. Both agents read these directly. Do not copy them into tool directories.
- **Shared skills:** a tool-agnostic skill has one canonical directory and is exposed to the other tool through a relative directory symlink. Never keep copied Claude and Codex versions merely for discovery.
- **Tool adapters:** instructions, settings, hooks, permissions, MCP configuration, and subagent definitions may have different formats and semantics. Keep those files separate and translate deliberately rather than symlinking or copying them wholesale.

Codex uses `AGENTS.md`, `.codex/`, and skills in `.agents/skills/`. Claude Code uses `CLAUDE.md`, `.claude/`, and skills in `.claude/skills/`. A shared `SKILL.md` format alone is not proof that every referenced tool, script, permission, or hook works in both hosts.

## Start with an audit

Before editing, inspect the repository root and the existing Claude setup: `CLAUDE.md`, `.claude/skills/`, `.claude/agents/`, `.claude/settings.json`, hooks, commands, `.gitignore`, current `AGENTS.md`, `.agents/skills/`, and `.codex/`. Check whether the working tree is already dirty and preserve unrelated work.

Report a short, concrete plan showing:

1. Files to create or edit.
2. Each skill's classification: shared, Claude-only, Codex-only, or needing adaptation.
3. The canonical directory and exact relative symlink to create, if shared skills are present.
4. Any incompatibilities that require a decision or make a symlink unsafe.

Do not create, replace, or remove a symlink or directory until the user has authorized the proposed changes, unless the user explicitly asked for immediate conversion. Never overwrite a nonempty skills directory to make a symlink.

## Build the adapter layer

### Project instructions

Create or revise root `AGENTS.md` as a concise Codex adapter to `CLAUDE.md`, not as a second complete handbook. It should identify `CLAUDE.md` and shared documentation as sources of project knowledge, give a useful project map, retain Codex-relevant operational instructions, and resolve contradictions explicitly. It must not tell Codex to ignore higher-priority instructions.

Keep `CLAUDE.md` as the existing Claude-facing document unless the user chooses another source of truth. When project-wide guidance changes, update the source and only the necessary adapter references; do not maintain duplicated long-form sections.

### Shared skills: symlink first

Prefer `.agents/skills/` as the canonical, tracked location for skills usable by both tools, then make Claude's expected directory a **relative directory symlink**:

```text
.claude/skills -> ../.agents/skills
```

From the repository root, after confirming there is no conflicting directory:

```sh
mkdir -p .agents
ln -s ../.agents/skills .claude/skills
```

Use a relative target so clones and Git worktrees remain portable. Commit both the canonical files and the symlink. Codex officially follows symlinked skill folders while scanning `.agents/skills`; its skill discovery therefore sees the canonical files directly.

Choose a different canonical location only when the repository's established convention gives a strong reason. In every case, create one physical source and one relative symlink. Verify the link with `test -L`, `readlink`, and a check that both expected paths resolve to the same `SKILL.md`.

If `.claude/skills/` already contains skills, first assess them:

- Move or reconcile compatible skills into the canonical directory only with authorization.
- Adapt skills before sharing if they name host-specific tools, commands, hooks, permissions, or inaccessible paths.
- Keep truly Claude-only or Codex-only skills in a separately named, clearly documented arrangement. A whole-directory symlink cannot coexist with physical per-tool-only children at the same `.claude/skills/` path. Explain this constraint and ask the user to choose an organization rather than silently duplicating files.

Never symlink settings, credentials, hooks, or agent-definition files just because skills are shared.

### Tool-specific configuration and agents

Create `.codex/config.toml` only when useful, starting minimal and omitting secrets. Do not translate `.claude/settings.json` mechanically: permission models, hook conventions, MCP configuration, and config formats differ. Preserve Claude settings.

Translate an important Claude subagent into a Codex agent only after checking that its responsibility and tools make sense in Codex. Convert its role and instructions into the appropriate Codex agent format; do not rename a Markdown file to `.toml`. Note behavioral differences rather than claiming equivalence.

Review `.gitignore` narrowly: ignore local overrides and secrets only where the project needs it, while leaving shared instructions, canonical skills, and the symlink tracked.

## Verify and hand off

After authorized edits:

1. Confirm every shared skill is present once physically and reachable through both expected paths.
2. Validate each `SKILL.md` has usable `name` and `description` metadata and retain its supporting files.
3. Confirm `AGENTS.md` points to the actual source-of-truth material and does not duplicate it unnecessarily.
4. Inspect Git status, including that Git records the relative symlink, and report intentional changes only.
5. State any remaining host-specific limitations and recommend restarting the relevant agent if discovery does not refresh.

If the request is only for review or a migration plan, do not edit. If a choice about the canonical source, relocation, or treatment of incompatible skills materially affects the repository, explain the options and request direction.
