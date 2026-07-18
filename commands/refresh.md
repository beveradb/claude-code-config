---
description: Refresh all read-only mirrors (*-main-readonly / *-dev-readonly) to their origin tips
allowed-tools: Bash
---

# Refresh Read-Only Mirrors

Pull every read-only clone up to its remote tip in one shot. Each
`<repo>-{main,dev}-readonly` dir is a pure reflection of its remote branch —
always clean, always == origin — so this fetches, hard-resets to origin, and
wipes any uncommitted drift (`-fd`, keeping `.env`/`node_modules`/`venv`). The
workspace root clone is **never** touched.

This is the same refresh that `/tidy-all-worktrees`, `/cleanup`, `/start`, and
`/setup` run automatically; use `/refresh` to do it on demand (e.g. before
grepping a `*-dev-readonly` mirror for freshly-merged work).

## Run it

```bash
# Workspace root = parent of any *-main-readonly clone (works from any worktree)
ROOT="$(pwd)"
while [ "$ROOT" != "/" ] && [ -z "$(ls -d "$ROOT"/*-main-readonly 2>/dev/null)" ]; do
  ROOT="$(dirname "$ROOT")"
done
bash "$ROOT/docs/archive/scripts/refresh-mirrors.sh"
```

The script prints one line per mirror: `✓ <dir> (<branch>) <old> → <new>` when it
advances, or `✓ <dir> (<branch>) @ <sha>` when already current. Report the
summary back to the user.
