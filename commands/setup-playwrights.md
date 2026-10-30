---
description: Set up or change pooled Playwright browser profiles (pw-pool) for Claude config dirs
allowed-tools: Read, Glob, Bash, Edit, Write, AskUserQuestion
---

# Setup Playwright Profile Pools

Configure `pw-pool`: pools of persistent Playwright browser profiles, one pool per Claude
config dir, shared safely between parallel sessions. See README → "Pooled Playwright Browser
Profiles" for how it works.

**Argument (optional):** $ARGUMENTS (e.g. a config dir and pool name)

## Step 0: Detect current state (run in parallel)

```bash
ls ~/.claude/bin/pw-pool 2>&1; ls -la ~/.local/bin/pw-pool 2>&1
cat ~/.playwright-profiles/pools.json 2>&1
ls -la ~/.playwright-profiles/
ls -d ~/.claude ~/.claude-* 2>/dev/null
pw-pool status --all 2>&1
```

For each config dir, read its MCP servers (`~/.claude.json` for `~/.claude`, otherwise
`<dir>/.claude.json`, key `mcpServers`) and list the `playwright*` entries. Classify each one:
- **pool slot**: args contain `slot --pool <name>`.
- **legacy**: `@playwright/mcp` with a fixed `--user-data-dir`.

## Step 1: Pools

If `pools.json` is missing or the user wants changes, use `AskUserQuestion` to confirm:
- **Pools:** one per identity/config dir, and the account each is signed in to.
- **Which config dir uses which pool.** Exactly one pool per config dir.
- **Counts:** default 5 Chrome (signed in) + 2 Firefox (kept signed out, for clean logged-out
  browsing) per pool.
- **Idle timeout:** default 30 min.

Write `~/.playwright-profiles/pools.json`:

```json
{
  "chrome": 5, "firefox": 2, "idle_minutes": 30, "signed_out": ["firefox"],
  "pools": {
    "personal": {"account": "me@example.com"},
    "work": {"account": "me@work.example", "chrome": 3}
  }
}
```

It is machine-local and holds account names: never commit it.

## Step 2: Migrate legacy profiles (if any)

Legacy profiles are top-level dirs such as `~/.playwright-profiles/chrome-1`.

1. Work out which account each one is signed in to:
   - Chrome: `Default/Preferences` → `account_info[].email`, and history titles in
     `Default/History` (`sqlite3 "file:...?immutable=1"`).
   - Firefox: titles in `places.sqlite`.
2. Propose a mapping to `<pool>/<browser>-N` and confirm it with `AskUserQuestion`.
3. For each profile, make sure no browser has it open (`pw-pool status --all` shows
   `open by a browser outside the pool`). Then:
   `mkdir -p ~/.playwright-profiles/personal && mv ~/.playwright-profiles/chrome-3 ~/.playwright-profiles/personal/chrome-1 && ln -s personal/chrome-1 ~/.playwright-profiles/chrome-3`.
   The symlink keeps still-running sessions on the legacy servers pointed at the same
   profile, and pw-pool treats a browser using it as "in use".
4. Profiles that aren't needed go to `~/.playwright-profiles/.trash/`. Never delete profile
   data without asking.

## Step 3: Register slots per config dir

```bash
mkdir -p ~/.local/bin && ln -sf ~/.claude/bin/pw-pool ~/.local/bin/pw-pool   # CLI on PATH
pw-pool install --config-dir <dir> --pool <pool> --exe ~/.claude/bin/pw-pool --dry-run
```

Show the dry run, then run it without `--dry-run`. It:
- removes the dir's old `playwright*` servers,
- adds `playwright-chrome-1`, `playwright-chrome-2` and `playwright-firefox-1` (override with
  `--slots chrome,chrome,chrome,firefox`),
- updates the `mcp__playwright-*__*` allow rules in `<dir>/settings.json`.

Always register the canonical `~/.claude/bin/pw-pool`, so every config dir runs the same code.

## Step 4: Seed logins (Chrome only)

Firefox profiles stay **signed out** on purpose. Never seed or sign in to them.

For each pool, one pool at a time:
1. Open `<pool>/chrome-1` headed through a pw-pool slot, never in plain Chrome. Playwright's
   mock keychain means cookies saved by normal Chrome come back logged out.
2. Show a labelled `data:` page naming the pool and the account, so the user can tell which
   window is which.
3. Ask the user to sign in to Google **and** to Chrome itself (profile avatar, top right) as
   that account.
4. Call `browser_close`, then check `Default/Preferences` → `account_info[].email`.
5. Run `pw-pool clone <pool>/chrome-1 --unused`.

## Step 5: Verify

```bash
(cd ~/.claude && python3 -m unittest discover -s tests/pw_pool)
pw-pool status --all
```

Tell the user that **new** Claude sessions pick up the slots. Running sessions keep their old
servers until restarted.

## Safety rules

- Never delete profile directories without confirmation. They hold logins.
- Never move a profile a browser currently has open.
- Never close another session's browser (`pw-pool release --force`) without the user's OK.
