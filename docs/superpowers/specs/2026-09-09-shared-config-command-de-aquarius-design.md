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
- `claude-code-config` was **always intended to be fully generic** and was, until it got
  contaminated by accident. The canonical dev-first commands live in the **Aquarius workspace
  repo** (`Aquarius-Human-AI/workspace`) under `.claude/commands/`; a session **pushed Aquarius
  content up** into the shared repo, misunderstanding the separation. No automation does this —
  it was a one-off human/agent mistake.

### Contamination origin (traced in git history)

- The single contaminating commit is **`d9b9af9`** (June 2026,
  *"feat(commands): add /refresh + wire mirror-refresh into start/cleanup/tidy"*). At its parent
  `d9b9af9^` the shared commands were clean: `shipit`=0, `pr`=0, `cleanup`=0, `tidy`=0, `start`=1
  incidental Aquarius hit; and `refresh`/`createenv`/`addfeaturebranch` **did not exist**.
- `d9b9af9` heavily rewrote `start` (+379 lines) and wired Aquarius mirror-refresh into
  `start`/`cleanup`/`tidy`, and added the Aquarius-only `refresh`.
- None of the 4 commits after `d9b9af9` touched `shipit`/`start`/`pr`/`cleanup`/`tidy` (they are
  `docs-review`/`docs-maintain`/`wrap`/session-record changes), so **`d9b9af9^` is the last-clean
  version with no legit later work to preserve** in those files.
- The recent **uncommitted working-tree** edits are a second wave of the same mistake (they add
  the dev-first blocks to `shipit`/`pr` and more to `start`/`cleanup`, and drop untracked
  Aquarius commands on disk).

**This work is therefore a restoration to the repo's original generic intent, not a new policy.**

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

Because the contamination is a known, bounded set of git changes, genericizing is mostly
**recovery from history**, not hand-authoring.

### A — Restore to the last-clean version

| Command | HEAD | Working tree | Restore action |
|---|---|---|---|
| `shipit` | generic (0) | contaminated (46) | `git checkout HEAD -- commands/shipit.md` |
| `pr` | generic (0) | contaminated (5) | `git checkout HEAD -- commands/pr.md` |
| `start` | contaminated (40) | contaminated (47) | `git checkout d9b9af9^ -- commands/start.md` |
| `cleanup` | contaminated (2) | contaminated (4) | `git checkout d9b9af9^ -- commands/cleanup.md` |
| `tidy-all-worktrees` | contaminated (1) | (1) | `git checkout d9b9af9^ -- commands/tidy-all-worktrees.md` |
| `autonomous` | (1 incidental) | (1) | manual scrub of the single line |
| `gcp-billing` | (1 incidental) | (1) | manual scrub of the single line |

`d9b9af9^` is the last-clean commit for `start`/`cleanup`/`tidy` (nothing after it touched them).
Aquarius keeps its dev-first `start`/`cleanup`/etc. via its project override, so restoring the
generic shared copies loses nothing there. After restoring, re-scan each file for residual
Aquarius-isms and scrub any stragglers.

### B — Remove from shared (Aquarius-only, never generic)

- `refresh` — **tracked**, born in the contaminating commit `d9b9af9` (mirror-refresh of
  `*-main-readonly`/`*-dev-readonly`); it was never part of the generic repo → `git rm
  commands/refresh.md`.
- `createenv`, `destroyenv`, `extendenv`, `envs`, `addfeaturebranch` — **untracked** on disk
  (never committed to the shared repo) → delete the files. Each already has an Aquarius
  project-level override.

### B′ — Verify-then-decide (possibly cross-project)

`setup-workspace` (tracked; 0 Aquarius-ism hits by regex but it scaffolds the multi-repo
worktree workflow). During implementation, read it and check whether `nomadkaraoke`/`life360`
rely on it (or on any removed command). If it's genuinely generic, keep it as-is; if it embeds
Aquarius specifics, either genericize or relocate to the Aquarius repo. A non-Aquarius workspace
that needs a removed command gets its own project override — we do not keep Aquarius content in
the generic layer.

### C — Leave (already free of Aquarius)

`coderabbit`, `plan`, `implement`, `test`, `test-review`, `docs-review`, `docs-maintain`,
`fix-main`, `export`, `wrap`, `setup-playwrights`, and the non-Aquarius project commands `edge`
(Life360, untracked), `seo-content`, `seo-review`. (Life360/Nomad specifics are a separate
concern, out of scope for this Aquarius de-leak.)

## Dirty working tree — preserve vs revert

The current `~/.claude` working tree is a **mix**; handle each item deliberately:

- **Preserve (legit general edits):** `CLAUDE.md` (coderabbit `review` rule rewrite + `md2pdf`
  Local Tools section — already matches the live global CLAUDE.md) and the untracked
  `claude-usage-fetch.sh` / `claude-usage-normalize.py` / `.last-update-result.json`.
- **Revert/scrub (the contamination):** per the Bucket A restore table for
  `shipit`/`start`/`pr`/`cleanup`/`tidy`; `git rm` the tracked `refresh`; delete the untracked
  Aquarius commands (`addfeaturebranch`, `createenv`, `destroyenv`, `envs`, `extendenv`).
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
