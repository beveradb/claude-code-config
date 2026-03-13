# /setup-playwrights — Design Spec

## Purpose

A slash command that provides a guided setup flow for configuring multiple isolated Playwright MCP server instances in Claude Code. Each instance gets its own browser profile, enabling simultaneous control of independent browser windows from Claude Code sessions.

## Scope

- Handles fresh setup, adding/removing instances, reconfiguration, and full teardown
- Cross-platform: macOS, Linux, Windows
- Operates on user-scope MCP config (`~/.claude.json`) and user settings (`~/.claude/settings.json`)
- Does NOT touch project-scope `.mcp.json` files

## Naming Convention

Instance names are built from components:

```
playwright-{browser}[-{flags}]-{number}
```

**Browser values:** `chrome`, `firefox`, `webkit`, `msedge`

**Flag suffixes (optional, in this order if multiple):** `headless`, `insecure`, `proxy`

**Examples:**
- `playwright-chrome-1`
- `playwright-firefox-2`
- `playwright-chrome-headless-1`
- `playwright-firefox-proxy-1`
- `playwright-chrome-headless-proxy-1`
- `playwright-chrome-insecure-1` (for `--ignore-https-errors`)

**Numbers** are scoped per browser+flags combo. Two headless Chrome instances: `playwright-chrome-headless-1`, `playwright-chrome-headless-2`.

**Legacy naming:** Instances named `playwright-{number}` (without browser, e.g., `playwright-1`) are recognized as a legacy format from earlier manual setup. The command detects these and offers migration to the new naming scheme.

**Profile directories** mirror the instance name (without the `playwright-` prefix):
- macOS/Linux: `~/.playwright-profiles/chrome-1/`, `~/.playwright-profiles/firefox-proxy-1/`
- Windows: `%USERPROFILE%\.playwright-profiles\chrome-1\`

**Permission rules** follow the full instance name: `mcp__playwright-chrome-1__*`, `mcp__playwright-firefox-proxy-1__*`, etc.

## Default Capabilities

All instances get `--caps vision,pdf,devtools` by default. These flags unlock additional tools with no performance cost — they only register more tools:
- **vision** — coordinate-based mouse interactions (click, drag, scroll by x/y position)
- **pdf** — save pages as PDF files
- **devtools** — access browser DevTools (console, network, performance)

## Detection & State Assessment (Step 0)

On invocation, inventory the current state:

1. Run `claude mcp list` — parse output for servers matching both patterns:
   - New format: `playwright-{browser}[-{flags}]-{number}` (e.g., `playwright-chrome-1`)
   - Legacy format: `playwright-{number}` (e.g., `playwright-1`, `playwright-2`)
2. Check `settings.json` `enabledPlugins` for any key containing `playwright` (the marketplace plugin key format may vary, so match broadly)
3. Run `claude mcp get playwright` — check output for a plain `playwright` MCP server. Parse the output's "Scope" field to confirm it's user-scope (not project-scope)
4. Check for `~/.playwright-profiles/` directory and contents (use `$HOME` on macOS/Linux, `$USERPROFILE` or `$HOME` on Windows)
5. Read `settings.json` `permissions.allow` for existing `mcp__playwright-*` rules

**Branch based on state:**
- **Fresh** (no numbered instances, no legacy instances) → Full Wizard Flow
- **Existing setup** (new-format instances found) → Existing Setup Menu
- **Legacy setup** (legacy-format instances like `playwright-1`, or marketplace plugin, or plain `playwright` MCP, but no new-format instances) → offer to migrate, then Full Wizard Flow. Migration means: detect browser from existing args if possible, rename to new format, move profile directories
- **Mixed** (both legacy and new-format) → show both, offer to migrate legacy ones, then Existing Setup Menu

## Full Wizard Flow (Fresh Setup)

### Step 1: Disable Conflicting Configs

If the marketplace plugin or a plain `playwright` user-scope MCP was detected:
- Explain the conflict (having an unmanaged default playwright alongside numbered instances causes confusion)
- Use `AskUserQuestion` to ask user to confirm disabling
- For user-scope MCP: `claude mcp remove --scope user playwright`
- For marketplace plugin: instruct user to disable via `/plugin` (cannot be done programmatically), wait for confirmation before continuing

### Step 2: Number of Instances

Use `AskUserQuestion` to ask how many browser instances the user wants. Default: 3.

If `$ARGUMENTS` contains a number, use that and skip this question.

### Step 3: Browser Selection Per Instance

Use `AskUserQuestion` to ask which browser for each instance:
- **Chrome** (default) — most compatible, best DevTools support
- **Firefox** — good for testing cross-browser compatibility
- **WebKit** — Safari engine, useful for testing Apple ecosystem
- **Edge** — Chromium-based, for testing Edge-specific behavior

Offer shortcuts:
- "All Chrome" / "All Firefox" etc. for uniform setup
- Or specify per-instance for a mix (e.g., "2 Chrome and 1 Firefox")

### Step 4: Niche Configuration Options

Use `AskUserQuestion` to ask: "Do any of your instances need special configuration?"

Explain each option with a clear description of what it does and when you'd want it:
- **`--headless`** — runs the browser without a visible window. Useful for background tasks or CI environments where you don't need to see the browser. Downside: you can't visually watch what Claude is doing.
- **`--ignore-https-errors`** — accepts self-signed or invalid SSL certificates. Useful for staging/dev environments with self-signed certs. Downside: reduces security — a real cert error would be silently ignored. (Named `insecure` in instance name for brevity.)
- **`--proxy-server <url>`** — routes all browser traffic through a proxy server. Useful for corporate networks, VPNs, or traffic inspection. Requires a running proxy.

If user wants any:
- Use `AskUserQuestion` to ask which instances get which flags
- Flags affect the instance name (e.g., `playwright-chrome-headless-1`)
- If proxy, use `AskUserQuestion` to ask for the proxy URL

### Step 5: Profile Directory

Show the default path for the detected platform:
- macOS/Linux: `~/.playwright-profiles/`
- Windows: `%USERPROFILE%\.playwright-profiles\`

Use `AskUserQuestion` to ask if user wants to customize. Most users accept the default.

### Step 6: Permissions

Explain the choice using `AskUserQuestion`:
- **Auto-allow (recommended):** Adds `mcp__playwright-{name}__*` to the allow list in `settings.json`. Claude can use these browsers without prompting each time.
- **Manual approval:** No permission rules added. Claude will ask permission for every browser tool call.

Recommend auto-allow. Ask user to confirm.

### Step 7: Summary & Confirmation

Display a table of everything that will be created:

```
Playwright MCP Setup Summary:
| Instance                    | Browser | Caps                 | Options   | Profile Dir                          |
|-----------------------------|---------|----------------------|-----------|--------------------------------------|
| playwright-chrome-1         | Chrome  | vision,pdf,devtools  | -         | ~/.playwright-profiles/chrome-1      |
| playwright-chrome-2         | Chrome  | vision,pdf,devtools  | headless  | ~/.playwright-profiles/chrome-2      |
| playwright-firefox-1        | Firefox | vision,pdf,devtools  | -         | ~/.playwright-profiles/firefox-1     |
```

Use `AskUserQuestion` to ask user to confirm before executing.

### Step 8: Execute

For each instance:
1. Create the profile directory: `mkdir -p <profile_dir>`
2. Register the MCP server:
   ```bash
   claude mcp add --scope user <name> -- npx @playwright/mcp@latest \
     --user-data-dir <profile_dir> \
     --caps vision,pdf,devtools \
     --browser <browser> \
     [--headless] [--ignore-https-errors] [--proxy-server <url>]
   ```
   Note: `--transport stdio` is omitted as it's the default.
3. If permissions approved, use `Edit` to update `settings.json` and add `mcp__<name>__*` to `permissions.allow`
4. Verify all instances with `claude mcp list` at the end

### Step 9: Output

Show:
- Success confirmation with status of each instance (Connected / Failed)
- Example usage phrases:
  - "Use playwright-chrome-1 to navigate to example.com"
  - "Use an idle firefox playwright to review the staging site"
  - "Take a screenshot with playwright-chrome-2"
- Mention `--storage-state <path>` as a power-user option for pre-loading auth/cookies into isolated sessions (note: this loads initial state into an otherwise clean profile — it works alongside `--user-data-dir`, not in conflict with it)
- Mention the command can be re-run to add/remove/reconfigure instances

## Existing Setup Menu

When new-format numbered instances are detected, display current state:

```
Current Playwright MCP Setup:
| Instance                    | Browser | Caps                 | Options   | Status    |
|-----------------------------|---------|----------------------|-----------|-----------|
| playwright-chrome-1         | Chrome  | vision,pdf,devtools  | -         | Connected |
| playwright-chrome-2         | Chrome  | vision,pdf,devtools  | headless  | Connected |
| playwright-firefox-1        | Firefox | vision,pdf,devtools  | -         | Connected |
```

Then use `AskUserQuestion` to present options:

### Option 1: Add More Instances

Mini-flow: how many, which browsers, any niche flags. Names continue from the highest existing number per browser+flags combo (e.g., if `playwright-chrome-2` exists, next Chrome is `playwright-chrome-3`).

Then runs Steps 5-9 of the wizard for the new instances only.

### Option 2: Remove Specific Instances

List existing instances, let user pick which to remove via `AskUserQuestion`. For each:
- Remove MCP server: `claude mcp remove --scope user <name>`
- Use `Edit` to remove the permission rule from `settings.json`
- Use `AskUserQuestion` to ask whether to delete the profile directory (warn: this deletes cookies, local storage, session data)

### Option 3: Remove All

Full teardown with confirmation via `AskUserQuestion`:
- Remove all `playwright-*` MCP servers with `claude mcp remove --scope user <name>` for each
- Use `Edit` to remove all `mcp__playwright-*` permission rules from `settings.json`
- Ask whether to delete `~/.playwright-profiles/` entirely (data loss warning)
- Offer to re-enable the marketplace `playwright` plugin if user wants a single default back

### Option 4: Reconfigure an Instance

List instances, let user pick one via `AskUserQuestion`. Show current config. Allow changing:
- Add/remove niche flags (headless, proxy, ignore-https-errors)
- This requires removing and re-adding the MCP server with updated args
- If flags changed, the name changes too (e.g., `playwright-chrome-1` → `playwright-chrome-headless-1`)
- Before renaming, check if the target name already exists. If it does, use the next available number (e.g., `playwright-chrome-headless-2` if `-1` is taken)
- Profile directory is preserved: use `mv <old_dir> <new_dir>` to rename. If the target directory already exists, warn the user and ask how to proceed via `AskUserQuestion`
- Permission rules updated accordingly (remove old, add new)

## Command File Structure

**File:** `~/.claude/commands/setup-playwrights.md`

**Frontmatter:**
```yaml
---
description: Set up multiple isolated Playwright MCP browser instances with separate profiles
allowed-tools: Read, Glob, Bash, Edit, Write, AskUserQuestion
---
```

**Arguments:** Optional. A number sets the instance count and skips that question (e.g., `/setup-playwrights 5`).

**Structure:** Follow existing command conventions — use `## Instructions` section heading to wrap the step-by-step flow.

## Error Handling

- If `claude mcp add` fails for an instance, report the error and continue with remaining instances
- If `settings.json` can't be parsed, warn and skip permission auto-configuration (instruct user to add manually)
- If profile directory creation fails (permissions issue), report and suggest alternative path
- If `npx @playwright/mcp@latest` isn't available, suggest `npm install -g @playwright/mcp`

## Platform Notes

- Detect platform via `uname -s` (Darwin = macOS, Linux = Linux, MINGW/MSYS/CYGWIN = Windows). If `uname` is unavailable, fall back to checking `$OSTYPE` or `$OS` environment variables
- Windows: use `$USERPROFILE` (or `$HOME`) for home directory
- All platforms: `claude mcp add --scope user` writes to `~/.claude.json` which is cross-platform
