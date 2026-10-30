## Playwright browsers (pooled profiles)

The `playwright-chrome-1`, `playwright-chrome-2` and `playwright-firefox-1` MCP servers are
`pw-pool` slots. Each draws a persistent profile from **this config dir's pool**. Every config
dir has its own pool. The server instructions name the pool and account.

**Which browser:**
- **Chrome (`playwright-chrome-*`) is signed in** to the pool's account, both in Chrome itself
  and in the Google session. Use it to act as the user, or for anything behind their login.
- **Firefox (`playwright-firefox-1`) is deliberately signed out of everything.** Use it when you
  need a clean, logged-out browser, such as testing as an anonymous visitor, checking what a
  public page shows, or a sign-up flow. Never sign in to Firefox profiles, and never ask the
  user to. If a Firefox task turns out to need a login, switch to a Chrome server.

- **Just use a server.** The first browser call claims a free profile in the pool. Don't try
  profiles one by one. If none is free, the error says which sessions hold them.
- **Check the account before acting as the user in Chrome.** Pages can show the wrong Google identity.
  If a Chrome profile is signed out or on a different account, say so and ask the user to
  sign in in that window. Never type passwords yourself.
- **Close it when done.** Call `browser_close` as soon as the browser part of a task is
  finished, before long non-browser work or waiting on the user for something unrelated.
  This releases the profile for other sessions. Idle browsers auto-close after 30 min.
- **Who holds what:** `browser_pool_status` (MCP tool) or `pw-pool status` (shell, add
  `--all` for every pool).
- **Never kill another session's browser**, and never use `pw-pool release --force`, without
  the user's OK. A release without `--force` only clears claims whose session has exited.
- To use a specific profile (e.g. the one the user just signed in to), call
  `browser_use_profile {profile: "chrome-3"}`.
- After a Chrome profile is newly signed in and closed, `pw-pool clone <pool>/chrome-1 --unused`
  copies its logins into the pool's never-used Chrome profiles.
- If `pw-pool status` warns that a signed-out profile has a Google session, tell the user. Don't
  use that profile as a clean browser until it's signed out again.
