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

**Flag suffixes (optional, in this order if multiple):** `headless`, `proxy`, `nohttperr`

**Examples:**
- `playwright-chrome-1`
- `playwright-firefox-2`
- `playwright-chrome-headless-1`
- `playwright-firefox-proxy-1`
- `playwright-chrome-headless-proxy-1`

**Numbers** are scoped per browser+flags combo. Two headless Chrome instances: `playwright-chrome-headless-1`, `playwright-chrome-headless-2`.

**Profile directories** mirror the name:
- macOS/Linux: `~/.playwright-profiles/chrome-1/`, `~/.playwright-profiles/firefox-proxy-1/`
- Windows: `%USERPROFILE%\.playwright-profiles\chrome-1\`

**Permission rules** follow: `mcp__playwright-chrome-1__*`, `mcp__playwright-firefox-proxy-1__*`, etc.

## Default Capabilities

All instances get `--caps vision,pdf,devtools` by default. These flags unlock additional tools (coordinate-based mouse interactions, PDF saving, DevTools access) with no performance cost — they only register more tools.

## Detection & State Assessment (Step 0)

On invocation, inventory the current state:

1. Run `claude mcp list` — parse for servers matching `playwright-*-*` pattern (numbered instances)
2. Check `settings.json` `enabledPlugins` for `playwright@claude-plugins-official` (marketplace plugin)
3. Run `claude mcp get playwright` — check for a plain user-scope `playwright` MCP server
4. Check for `~/.playwright-profiles/` directory and contents
5. Read `settings.json` `permissions.allow` for existing `mcp__playwright-*` rules

**Branch based on state:**
- **Fresh** (no numbered instances) → Full Wizard Flow
- **Existing setup** (numbered instances found) → Existing Setup Menu
- **Legacy setup** (marketplace plugin or plain `playwright` MCP, but no numbered instances) → offer to migrate, then Full Wizard Flow

## Full Wizard Flow (Fresh Setup)

### Step 1: Disable Conflicting Configs

If the marketplace plugin or a plain `playwright` user-scope MCP was detected:
- Explain the conflict (having an unmanaged default playwright alongside numbered instances causes confusion)
- Ask user to confirm disabling
- For user-scope MCP: `claude mcp remove playwright`
- For marketplace plugin: instruct user to disable via `/plugin` (cannot be done programmatically)

### Step 2: Number of Instances

Ask how many browser instances the user wants. Default: 3.

If `$ARGUMENTS` contains a number, use that and skip this question.

### Step 3: Browser Selection Per Instance

For each instance, ask which browser:
- **Chrome** (default) — most compatible, best DevTools support
- **Firefox** — good for testing cross-browser compatibility
- **WebKit** — Safari engine, useful for testing Apple ecosystem
- **Edge** — Chromium-based, for testing Edge-specific behavior

Offer shortcuts:
- "All Chrome" / "All Firefox" etc. for uniform setup
- Or specify per-instance for a mix (e.g., "2 Chrome and 1 Firefox")

### Step 4: Niche Configuration Options

Ask: "Do any of your instances need special configuration?"

Explain each option with a clear description of what it does and when you'd want it:
- **`--headless`** — runs the browser without a visible window. Useful for background tasks or CI environments where you don't need to see the browser. Downside: you can't visually watch what Claude is doing.
- **`--ignore-https-errors`** — accepts self-signed or invalid SSL certificates. Useful for staging/dev environments with self-signed certs. Downside: reduces security — a real cert error would be silently ignored.
- **`--proxy-server <url>`** — routes all browser traffic through a proxy server. Useful for corporate networks, VPNs, or traffic inspection. Requires a running proxy.

If user wants any:
- Ask which instances get which flags
- Flags affect the instance name (e.g., `playwright-chrome-headless-1`)
- If proxy, ask for the proxy URL

### Step 5: Profile Directory

Show the default path for the detected platform:
- macOS/Linux: `~/.playwright-profiles/`
- Windows: `%USERPROFILE%\.playwright-profiles\`

Ask if user wants to customize. Most users accept the default.

### Step 6: Permissions

Explain the choice:
- **Auto-allow (recommended):** Adds `mcp__playwright-{name}__*` to the allow list in `settings.json`. Claude can use these browsers without prompting each time.
- **Manual approval:** No permission rules added. Claude will ask permission for every browser tool call.

Recommend auto-allow. Ask user to confirm.

### Step 7: Summary & Confirmation

Display a table of everything that will be created:

```
Playwright MCP Setup Summary:
| Instance                    | Browser | Flags                | Profile Dir                          |
|-----------------------------|---------|----------------------|--------------------------------------|
| playwright-chrome-1         | Chrome  | vision,pdf,devtools  | ~/.playwright-profiles/chrome-1      |
| playwright-chrome-2         | Chrome  | vision,pdf,devtools  | ~/.playwright-profiles/chrome-2      |
| playwright-firefox-1        | Firefox | vision,pdf,devtools  | ~/.playwright-profiles/firefox-1     |
```

Ask user to confirm before executing.

### Step 8: Execute

For each instance:
1. Create the profile directory: `mkdir -p <profile_dir>`
2. Register the MCP server:
   ```bash
   claude mcp add --transport stdio <name> --scope user -- npx @playwright/mcp@latest \
     --user-data-dir <profile_dir> \
     --caps vision,pdf,devtools \
     --browser <browser> \
     [--headless] [--ignore-https-errors] [--proxy-server <url>]
   ```
3. If permissions approved, update `settings.json` to add `mcp__<name>__*` to `permissions.allow`
4. Verify each with `claude mcp list` at the end

### Step 9: Output

Show:
- Success confirmation with status of each instance (Connected / Failed)
- Example usage phrases:
  - "Use playwright-chrome-1 to navigate to example.com"
  - "Use an idle firefox playwright to review the staging site"
  - "Take a screenshot with playwright-chrome-2"
- Mention `--storage-state <path>` as a power-user option for pre-loading auth/cookies into isolated sessions
- Mention the command can be re-run to add/remove/reconfigure instances

## Existing Setup Menu

When numbered instances are detected, display current state:

```
Current Playwright MCP Setup:
| Instance              | Browser | Flags               | Status    |
|-----------------------|---------|---------------------|-----------|
| playwright-chrome-1   | Chrome  | vision,pdf,devtools | Connected |
| playwright-chrome-2   | Chrome  | vision,pdf,devtools | Connected |
| playwright-firefox-1  | Firefox | vision,pdf,devtools | Connected |
```

Then present options:

### Option 1: Add More Instances

Mini-flow: how many, which browsers, any niche flags. Names continue from the highest existing number per browser+flags combo (e.g., if `playwright-chrome-2` exists, next Chrome is `playwright-chrome-3`).

Then runs Steps 5-9 of the wizard for the new instances only.

### Option 2: Remove Specific Instances

List existing instances, let user pick which to remove. For each:
- Remove MCP server: `claude mcp remove <name>`
- Remove permission rule from `settings.json`
- Ask whether to delete the profile directory (warn: this deletes cookies, local storage, session data)

### Option 3: Remove All

Full teardown with confirmation:
- Remove all `playwright-*` MCP servers
- Remove all `mcp__playwright-*` permission rules
- Ask whether to delete `~/.playwright-profiles/` entirely (data loss warning)
- Offer to re-enable the marketplace `playwright` plugin if user wants a single default back

### Option 4: Reconfigure an Instance

List instances, let user pick one. Show current config. Allow changing:
- Add/remove niche flags (headless, proxy, ignore-https-errors)
- This requires removing and re-adding the MCP server with updated args
- If flags changed, the name changes too (e.g., `playwright-chrome-1` → `playwright-chrome-headless-1`)
- Profile directory is preserved (moved/renamed to match new name)
- Permission rules updated accordingly

## Command File Structure

**File:** `~/.claude/commands/setup-playwrights.md`

**Frontmatter:**
```yaml
---
description: Set up multiple isolated Playwright MCP browser instances with separate profiles
allowed-tools: Read, Glob, Bash, Edit, Write, AskUserQuestion, Task
---
```

**Arguments:** Optional. A number sets the instance count and skips that question (e.g., `/setup-playwrights 5`).

## Error Handling

- If `claude mcp add` fails for an instance, report the error and continue with remaining instances
- If `settings.json` can't be parsed, warn and skip permission auto-configuration (instruct user to add manually)
- If profile directory creation fails (permissions issue), report and suggest alternative path
- If `npx @playwright/mcp@latest` isn't available, suggest `npm install -g @playwright/mcp`

## Platform Notes

- Detect platform via `uname -s` (Darwin = macOS, Linux = Linux, MINGW/MSYS/CYGWIN = Windows)
- Windows: use `%USERPROFILE%` for home directory, backslash paths in display but forward slashes work in `claude mcp add`
- All platforms: `claude mcp add --scope user` writes to `~/.claude.json` which is cross-platform
