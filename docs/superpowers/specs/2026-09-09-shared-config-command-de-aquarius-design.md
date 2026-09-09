# De-Aquarius the shared command layer — design

**Date:** 2026-09-09
**Repo:** `beveradb/claude-code-config` (checked out at `~/.claude` and cloned per-project at `~/.claude-aquarius`, `~/.claude-nomadkaraoke`, `~/.claude-life360`)
**Status:** approved, pending implementation plan

## Problem

Running `/shipit` (and `/start`, `/pr`) in a **non-Aquarius** project (e.g. `ynab-cli`)
produces **Aquarius-specific** instructions — dev-first release flow, `--base dev`,
`aquarius-base.sh`, `peopleaquarius.com`, `release.yml`. The ynab-cli session only
recovered because ynab-cli's `CLAUDE.md` narratively overrides `/shipit`.

### Root cause (verified, not assumed)

Per-project **session-state** isolation works and is not the problem:

- Each work project's `.envrc` exports `CLAUDE_CONFIG_DIR` (aquarius → `~/.claude-aquarius`,
  nomadkaraoke → `~/.claude-nomadkaraoke`, life360 → `~/.claude-life360`).
- `ynab-cli` (and other `beveradb` projects) set **no** `CLAUDE_CONFIG_DIR`, so they use the
  default `~/.claude`. That is correct and intended.

The leak is in **command content**, not config-dir routing:

- All four config dirs are **clones of the same repo** (`beveradb/claude-code-config`, all on
  `main`). They isolate *session state* (history, memory, `.claude.json`, MCP auth) — **not**
  the `commands/` set. Every clone therefore carries the *same* commands.
- That shared command set is Aquarius-flavoured. The canonical dev-first commands are authored
  in the **Aquarius workspace repo** (`Aquarius-Human-AI/workspace`) under `.claude/commands/`,
  and were being **hand-copied up** into `claude-code-config` (the current dirty working tree is
  exactly that copy-in-progress). No automation does this — it is a manual habit.
- So there is no neutral "general" `/shipit`: the one in `~/.claude` *is* the Aquarius one.

## Goal

The **shared layer stays generic**; project-specific behaviour lives in that project's own
repo. After this change, `/shipit`/`/start`/`/pr` read as generic everywhere by default, and
Aquarius's dev-first versions apply **only** inside Aquarius worktrees via its already-present
project-level overrides.

## Architecture — three command layers

| Layer | Location | Rule |
|---|---|---|
| **Generic shared** | `claude-code-config` (`~/.claude` + all clones) | Zero project-specific content. Cross-project workflow only. |
| **Project override** | each workspace repo's `.claude/commands/` (e.g. `Aquarius-Human-AI/workspace`) | Project's specific version; **overrides** the shared one when cwd is in that project. Already wired; already holds the dev-first versions (blob `7419397` == the working-tree copy in `~/.claude`). |
| **Project instructions** | project `CLAUDE.md` | Narrative overrides. |

Resolution precedence: **project-level command > user-level (config-dir) command**. Because
the Aquarius workspace repo already commits dev-first `shipit`/`start`/`pr`/`cleanup` (and the
full command set) under its own `.claude/commands/`, making the shared copies generic loses
nothing on the Aquarius side.

## Command buckets (from a full audit of `~/.claude/commands/*.md`)

Density = count of Aquarius-ism matches (`aquarius|peopleaquarius|aquabot|aquarius-base|
Aquarius-Human-AI|dev-first|deploy-dev|-main-readonly|-dev-readonly|ephemeral|release.yml|
workspace#|.aquarius-base|feature/<slug>`).

### A — Genericize (has a real generic form, currently contaminated)

`shipit` (51), `start` (48 working / **101 in committed HEAD**), `pr` (6), `cleanup` (5),
`tidy-all-worktrees` (1), `autonomous` (1), `gcp-billing` (1).

Strip all Aquarius specifics. Aquarius retains its dev-first versions via its project override
(all have an Aquarius override present). Notes:

- `shipit`, `pr`, `cleanup`: dev-first content is largely in the **uncommitted** working tree →
  revert to committed HEAD, then scrub any residual Aquarius-ism.
- `start`: dev-first content is **committed** (HEAD has 101 hits; commit `2870ade` "Make /start
  dev-first aware"). Genericizing means **authoring/recovering** the simple single-repo worktree
  `/start <description>` (mine the pre-`2870ade` generic form from git history as the base). The
  Aquarius workspace-aware `/start <repo> <description>` is created by `setup-workspace` as a
  project-level override, so it survives.
- `tidy-all-worktrees`, `autonomous`, `gcp-billing`: single incidental mention — scrub the line.

### B — Aquarius-exclusive concepts, no generic form → remove from shared

`createenv`, `destroyenv`, `extendenv`, `envs`, `addfeaturebranch`. All have an Aquarius
project-level override, so removal from shared is safe there. (`addfeaturebranch` is currently
**untracked** in the working tree — drop it rather than add it.)

### B′ — Genuinely cross-project workspace tooling → rewrite generic, keep in shared

`refresh`, `setup-workspace`, and any Bucket-A/B command that turns out to be used by ≥2
workspaces (Aquarius + Nomad + Life360). Rewrite to strip Aquarius names/URLs while keeping the
mechanism generic (e.g. `refresh` refreshes read-only mirror clones by convention, not by the
`*-main-readonly` Aquarius naming). **Verify during implementation** whether
`nomadkaraoke`/`life360` project repos rely on the shared copies (check their project
`.claude/commands/`); if a non-Aquarius workspace needs one and it can't be made cleanly
generic, that workspace gets its own project override rather than us keeping Aquarius content in
the generic layer.

### C — Leave (already free of Aquarius)

`coderabbit`, `plan`, `implement`, `test`, `test-review`, `docs-review`, `docs-maintain`,
`fix-main`, `export`, `wrap`, `setup-playwrights`, and the non-Aquarius project commands `edge`
(Life360), `seo-content`, `seo-review`. (Life360/Nomad specifics are a separate concern, out of
scope for this Aquarius de-leak.)

## Dirty working tree — preserve vs revert

The current `~/.claude` working tree is a **mix**; handle each item deliberately:

- **Preserve (legit general edits):** `CLAUDE.md` (coderabbit `review` rule rewrite + `md2pdf`
  Local Tools section — already matches the live global CLAUDE.md) and the untracked
  `claude-usage-fetch.sh` / `claude-usage-normalize.py` / `.last-update-result.json`.
- **Revert/scrub (the contamination):** Aquarius dev-first blocks in `shipit`/`start`/`pr`/
  `cleanup`; do **not** add untracked `commands/addfeaturebranch.md`.
- **Leave alone (unrelated, yours):** the `skills/find-docs/SKILL.md` deletion.

## Re-leak guardrail

1. **Policy doc:** document the three-layer model in `claude-code-config` (README + `CLAUDE.md`):
   the shared layer is generic; project-specific commands belong in that project's own
   `.claude/commands/`; never copy a project's command up into the shared repo.
2. **Pre-commit check:** a tracked script that greps **staged** `commands/*.md` for Aquarius-isms
   and blocks the commit with a hint ("put this in the project override instead"). Installed via a
   tracked hook (e.g. `core.hooksPath` or an installer), so it lives in the repo, not just local
   `.git/hooks`.

## Delivery & propagation

- Edit + **commit straight to `main`** on `claude-code-config` (personal config repo, not a
  product repo), after showing Andrew the diff. Push.
- `git pull` in the three sibling clones (`~/.claude-aquarius`, `~/.claude-nomadkaraoke`,
  `~/.claude-life360`), checking each for its own dirty state first (the Aquarius clone may hold
  the same uncommitted dev-first blocks; reconcile them to match `main`).

## Verification

- `/shipit`, `/start`, `/pr` resolved from `~/.claude` in `ynab-cli` read as **generic** (no
  dev-first / `--base dev` / `peopleaquarius`).
- The same commands inside an `~/Projects/aquarius/...` worktree still read as **dev-first**
  (proves the project override wins).
- `grep -rE '<aquarius-isms>' ~/.claude/commands/` returns only Bucket-C false-positives (none of
  A/B).
- The pre-commit hook rejects a test commit that adds `aquarius` to a `commands/*.md`.

## Out of scope

- Life360 (`edge`) and Nomad/SEO command specifics beyond confirming they don't depend on removed
  Bucket-B commands.
- Any change to `CLAUDE_CONFIG_DIR` routing (it works correctly).
- Building project-level overrides for Nomad/Life360 (only noted if a removal exposes a gap).
