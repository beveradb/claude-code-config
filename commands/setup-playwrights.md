---
description: Set up multiple isolated Playwright MCP browser instances with separate profiles
allowed-tools: Read, Glob, Bash, Edit, Write, AskUserQuestion
---

# Setup Playwright Browser Instances

Set up, manage, or tear down multiple isolated Playwright MCP server instances, each with its own browser profile. Enables simultaneous control of independent browser windows from Claude Code sessions.

**Argument (optional):** $ARGUMENTS
- A number sets the instance count (e.g., `/setup-playwrights 5`)
- If omitted, defaults to 3 (or asks during guided flow)

## Instructions

### Step 0: Detect Current State

Run all detection in parallel:

```bash
# List all MCP servers, filter for playwright
claude mcp list 2>&1 | grep -i playwright
```

```bash
# Check for existing profile directories
ls -d ~/.playwright-profiles/*/ 2>/dev/null || ls -d "$USERPROFILE/.playwright-profiles"/*/ 2>/dev/null || echo "No profile directories found"
```

Read `~/.claude/settings.json` and check:
- `enabledPlugins` for any key containing `playwright` (marketplace plugin)
- `permissions.allow` for any `mcp__playwright-*` entries

Parse the `claude mcp list` output to categorize what exists:

**New-format instances:** Match `playwright-{browser}[-{flags}]-{number}` pattern (e.g., `playwright-chrome-1`, `playwright-firefox-headless-2`)

**Legacy-format instances:** Match `playwright-{number}` pattern (e.g., `playwright-1`, `playwright-2`) — these are from older manual setup

**Plain playwright:** A server named exactly `playwright` (no number/browser). Run `claude mcp get playwright 2>&1` and check the Scope field to confirm it's user-scope.

**Marketplace plugin:** An enabled plugin with `playwright` in its key in `settings.json` `enabledPlugins`.

**Branch based on state:**
- **Fresh** (no numbered instances, no legacy instances) → go to Step 1
- **Legacy setup** (legacy-format instances like `playwright-1`, marketplace plugin, or plain `playwright` MCP, but no new-format instances) → go to Legacy Migration
- **Existing setup** (new-format instances found) → go to Existing Setup Menu
- **Mixed** (both legacy and new-format) → show both, offer to migrate legacy ones via Legacy Migration, then go to Existing Setup Menu

---

### Legacy Migration

Display what was found:

```
Legacy Playwright MCP instances detected:
- playwright-1 (connected)
- playwright-2 (connected)
- playwright-3 (connected)
```

Use `AskUserQuestion` to ask:
> "These use the old naming format (playwright-{number}). I can migrate them to the new format (playwright-{browser}-{number}) which enables referring to instances by browser type (e.g., 'use an idle firefox playwright'). Would you like to:
> 1. Migrate existing instances to new naming
> 2. Remove all and start fresh
> 3. Keep as-is and skip setup"

**If migrating:**
For each legacy instance:
1. Run `claude mcp get playwright-{N} 2>&1` to read the current args and determine the browser (look for `--browser` flag; default to `chrome` if not specified)
2. Determine the new name: `playwright-{browser}-{N}`
3. Read the current `--user-data-dir` path to find the existing profile directory
4. Remove old: `claude mcp remove --scope user playwright-{N}`
5. Add new with same args but updated name:
   ```bash
   claude mcp add --scope user playwright-{browser}-{N} -- npx @playwright/mcp@latest \
     --user-data-dir ~/.playwright-profiles/{browser}-{N} \
     --caps vision,pdf,devtools \
     --browser {browser} \
     {any other existing flags}
   ```
6. Move profile directory if it exists: `mv ~/.playwright-profiles/profile-{N} ~/.playwright-profiles/{browser}-{N}` (skip if source doesn't exist)
7. Update permission rules in `settings.json`: remove `mcp__playwright-{N}__*`, add `mcp__playwright-{browser}-{N}__*`

After migration, go to Existing Setup Menu (so user can add more or make changes).

**If removing all:** Remove each legacy instance with `claude mcp remove --scope user playwright-{N}`, clean up permissions, then go to Step 1 (fresh wizard).

---

### Existing Setup Menu

Display current state as a table:

```
Current Playwright MCP Setup:
| Instance                    | Browser | Caps                 | Options   | Status    |
|-----------------------------|---------|----------------------|-----------|-----------|
| playwright-chrome-1         | Chrome  | vision,pdf,devtools  | -         | Connected |
| playwright-chrome-headless-1| Chrome  | vision,pdf,devtools  | headless  | Connected |
| playwright-firefox-1        | Firefox | vision,pdf,devtools  | -         | Connected |
```

Use `AskUserQuestion` to present options:
> "What would you like to do?
> 1. **Add more instances** — add new browser instances
> 2. **Remove specific instances** — remove selected instances
> 3. **Remove all** — tear down entire setup
> 4. **Reconfigure an instance** — change flags on an existing instance
> 5. **Done** — exit, no changes needed"

---

#### Option 1: Add More Instances

Use `AskUserQuestion` to ask how many new instances to add.

Use `AskUserQuestion` to ask which browser for each new instance:
- **Chrome** (default) — most compatible, best DevTools support
- **Firefox** — good for testing cross-browser compatibility
- **WebKit** — Safari engine, useful for testing Apple ecosystem
- **Edge** — Chromium-based, for testing Edge-specific behavior

Offer shortcuts like "all Chrome" or "2 Chrome and 1 Firefox".

Use `AskUserQuestion` to ask if any need special configuration (see Step 4 for the options).

Names continue from the highest existing number per browser+flags combo. For example, if `playwright-chrome-2` exists, the next Chrome instance is `playwright-chrome-3`.

Then go to Step 5 (profile directory), Step 6 (permissions), Step 7 (summary), Step 8 (execute), Step 9 (output) for the new instances only.

---

#### Option 2: Remove Specific Instances

Use `AskUserQuestion` to ask which instances to remove (show the numbered list).

For each selected instance:
1. Remove MCP server: `claude mcp remove --scope user <name>`
2. Use `Edit` to remove `mcp__<name>__*` from `permissions.allow` in `~/.claude/settings.json`
3. Use `AskUserQuestion` to ask whether to delete the profile directory:
   > "Delete the profile directory for {name} at {path}? This permanently removes cookies, local storage, and session data for this browser profile."

Report what was removed.

---

#### Option 3: Remove All

Use `AskUserQuestion` to confirm:
> "This will remove ALL Playwright MCP instances, their permission rules, and optionally their profile data. Are you sure?"

If confirmed:
1. For each `playwright-*` instance: `claude mcp remove --scope user <name>`
2. Use `Edit` to remove all `mcp__playwright-*` entries from `permissions.allow` in `~/.claude/settings.json`
3. Use `AskUserQuestion` to ask whether to delete `~/.playwright-profiles/` entirely:
   > "Delete all profile directories at ~/.playwright-profiles/? This permanently removes all browser data (cookies, local storage, sessions)."
4. Use `AskUserQuestion` to ask:
   > "Would you like to re-enable the default Playwright marketplace plugin for single-browser use? (You can do this via /plugin)"

Report what was removed.

---

#### Option 4: Reconfigure an Instance

Use `AskUserQuestion` to ask which instance to reconfigure (show the list).

Show its current configuration (browser, flags, profile dir).

Use `AskUserQuestion` to ask what to change:
- Add/remove `--headless`
- Add/remove `--ignore-https-errors`
- Add/remove `--proxy-server <url>` (ask for URL if adding)

Determine the new name based on updated flags:

**Naming rules:**
- Base: `playwright-{browser}-{number}`
- With flags (in this order): `playwright-{browser}-headless-insecure-proxy-{number}`
- `insecure` = `--ignore-https-errors`

**Before renaming, check for conflicts:** If the target name already exists, use the next available number for that browser+flags combo.

Execute the change:
1. Remove old: `claude mcp remove --scope user <old-name>`
2. Move profile directory: `mv <old-profile-dir> <new-profile-dir>`
   - If the target directory already exists, use `AskUserQuestion` to ask:
     > "Profile directory {new-path} already exists. Merge into it (keeping existing data), replace it, or cancel?"
3. Add new:
   ```bash
   claude mcp add --scope user <new-name> -- npx @playwright/mcp@latest \
     --user-data-dir <new-profile-dir> \
     --caps vision,pdf,devtools \
     --browser <browser> \
     [updated flags]
   ```
4. Use `Edit` to update `settings.json`: remove `mcp__<old-name>__*`, add `mcp__<new-name>__*`

Report the change.

---

### Step 1: Disable Conflicting Configs

**Only runs during fresh setup or after removing legacy instances.**

If a marketplace plugin with `playwright` in its key was detected in `enabledPlugins`:
- Explain: "The default Playwright marketplace plugin would create a separate unmanaged browser alongside your numbered instances, which can cause confusion."
- Use `AskUserQuestion`: "Please disable the Playwright marketplace plugin via /plugin. Let me know when done."
- Wait for confirmation before continuing.

If a plain `playwright` user-scope MCP server was detected:
- Explain: "A single 'playwright' MCP server exists at user scope. This would overlap with the numbered instances."
- Use `AskUserQuestion` to confirm removal.
- Remove: `claude mcp remove --scope user playwright`
- Use `Edit` to remove `mcp__playwright__*` from `permissions.allow` in `settings.json` if present.

### Step 2: Number of Instances

If `$ARGUMENTS` contains a number, use that as the instance count.

Otherwise, use `AskUserQuestion`:
> "How many browser instances would you like to set up? (Default: 3)
>
> More instances = more browsers you can control simultaneously, but each opens its own Chrome/Firefox/etc. window."

### Step 3: Browser Selection Per Instance

Use `AskUserQuestion`:
> "Which browser for each instance? Options:
> - **Chrome** (default) — most compatible, best DevTools support
> - **Firefox** — good for testing cross-browser compatibility
> - **WebKit** — Safari engine, useful for testing Apple ecosystem
> - **Edge** — Chromium-based, for Edge-specific behavior
>
> You can say things like:
> - 'All Chrome' — all instances use Chrome
> - '2 Chrome and 1 Firefox' — mix of browsers
> - 'Chrome, Firefox, Chrome' — specify each one"

Parse the response. Map browser names to Playwright values: chrome, firefox, webkit, msedge.

### Step 4: Niche Configuration Options

Use `AskUserQuestion`:
> "Do any instances need special configuration? These are optional — most users don't need them:
>
> - **Headless** — runs without a visible browser window. Good for background/CI tasks. Downside: you can't watch what's happening.
> - **Ignore HTTPS errors** — accepts self-signed SSL certificates. Good for staging/dev sites. Downside: real cert errors are silently ignored.
> - **Proxy** — routes traffic through a proxy server. Good for corporate networks or traffic inspection. Requires a running proxy.
>
> Say 'none' to skip, or describe what you need (e.g., 'make instance 2 headless' or 'all instances should ignore HTTPS errors')."

If user wants proxy on any instance, use `AskUserQuestion` to get the proxy URL.

**Build the instance list.** For each instance, determine:
- Browser (from Step 3)
- Flags (from Step 4)
- Instance name: `playwright-{browser}[-{flags}]-{number}`
  - Flag suffixes in order: `headless`, `insecure`, `proxy`
  - Numbers are per browser+flags combo (first Chrome = 1, second Chrome = 2, first headless Chrome = 1, etc.)

### Step 5: Profile Directory

Detect the platform:
```bash
uname -s 2>/dev/null || echo "$OSTYPE" || echo "$OS"
```

Set default base directory:
- macOS (Darwin) / Linux: `~/.playwright-profiles`
- Windows (MINGW/MSYS/CYGWIN or `windows_nt`): `$USERPROFILE/.playwright-profiles`

Use `AskUserQuestion`:
> "Browser profiles will be stored in: `{default_path}`
>
> Each instance gets its own subdirectory (e.g., `{default_path}/chrome-1/`).
> Profiles persist cookies, local storage, and session data between uses.
>
> Use this path, or specify a custom one?"

### Step 6: Permissions

Use `AskUserQuestion`:
> "Auto-allow permissions for all Playwright instances? (Recommended: yes)
>
> - **Yes (recommended):** Adds allow rules to settings.json so Claude can use browsers without prompting each time.
> - **No:** You'll be asked for permission on every browser action (navigate, click, screenshot, etc.)."

### Step 7: Summary & Confirmation

Display a summary table:

```
Playwright MCP Setup Summary:

| Instance                         | Browser | Caps                 | Options   | Profile Dir                              |
|----------------------------------|---------|----------------------|-----------|------------------------------------------|
| playwright-chrome-1              | Chrome  | vision,pdf,devtools  | -         | ~/.playwright-profiles/chrome-1          |
| playwright-chrome-2              | Chrome  | vision,pdf,devtools  | -         | ~/.playwright-profiles/chrome-2          |
| playwright-firefox-1             | Firefox | vision,pdf,devtools  | -         | ~/.playwright-profiles/firefox-1         |

Permissions: Auto-allow enabled
```

Also list any configs being disabled (marketplace plugin, plain playwright, legacy instances).

Use `AskUserQuestion`:
> "Does this look right? Confirm to proceed, or describe what to change."

If changes requested, go back to the relevant step.

### Step 8: Execute

For each instance:

1. **Create the profile directory:**
   ```bash
   mkdir -p {profile_dir}
   ```

2. **Register the MCP server:**
   ```bash
   claude mcp add --scope user {instance_name} -- npx @playwright/mcp@latest \
     --user-data-dir {profile_dir} \
     --caps vision,pdf,devtools \
     --browser {browser} \
     [--headless] [--ignore-https-errors] [--proxy-server {url}]
   ```

   If the command fails, report the error and continue with remaining instances.

3. **Update permissions** (if approved in Step 6):
   Use `Edit` on `~/.claude/settings.json` to add `mcp__{instance_name}__*` to the `permissions.allow` array.

4. **Verify all instances:**
   ```bash
   claude mcp list 2>&1 | grep -i playwright
   ```

### Step 9: Output

Display results:

```
## Setup Complete

| Instance                    | Status    |
|-----------------------------|-----------|
| playwright-chrome-1         | Connected |
| playwright-chrome-2         | Connected |
| playwright-firefox-1        | Connected |

### Usage Examples

Tell Claude which browser to use:
- "Use playwright-chrome-1 to navigate to example.com"
- "Use an idle firefox playwright to review the staging site"
- "Take a screenshot with playwright-chrome-2"
- "Use playwright-firefox-1 to fill out the login form"

All instances can be used simultaneously within a single session.

### Power-User Tips

- **Pre-load auth:** Add `--storage-state <path-to-json>` to an instance
  to start with saved cookies/sessions (works alongside the profile directory).
- **Reconfigure later:** Run `/setup-playwrights` again to add, remove, or
  change instances.
- **New sessions:** Restart Claude Code (or open a new terminal) for the
  new MCP servers to be available.
```

## Error Handling

- If `claude mcp add` fails for an instance, report the error and continue with remaining instances
- If `settings.json` can't be parsed or edited, warn and instruct the user to add permission rules manually:
  > "Could not update settings.json automatically. Add these to your permissions.allow array: [list rules]"
- If profile directory creation fails (permissions issue), report and suggest an alternative path
- If `npx @playwright/mcp@latest` is not available, suggest: `npm install -g @playwright/mcp`

## Safety Rules

- **Never modify project-scope .mcp.json files** — only user-scope config
- **Always confirm before deleting profile directories** — they contain user data
- **Always confirm before removing instances** — show what will be removed
- **Preserve profile data during reconfiguration** — move, don't delete

## Related Commands

| Command | Purpose |
|---------|---------|
| `/plugin` | Enable/disable marketplace plugins (needed to disable default Playwright) |
| `/setup-playwrights` | Run again to add, remove, or reconfigure instances |
