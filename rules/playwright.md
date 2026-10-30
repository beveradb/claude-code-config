## Playwright browsers (pooled profiles)

The `playwright-chrome-1`, `playwright-chrome-2` and `playwright-firefox-1` MCP servers are
`pw-pool` slots. Each draws a persistent, already-signed-in profile from **this config dir's
pool**. Every config dir has its own pool, normally signed in to one Google account. The
server instructions name the pool and account.

- **Just use a server.** The first browser call claims a free profile in the pool. Don't try
  profiles one by one. If none is free, the error says which sessions hold them.
- **Check the account before acting as the user.** Pages can show the wrong Google identity.
  If a profile is signed out or on a different account, say so and ask the user to sign in
  in that window. Never type passwords yourself.
- **Close it when done.** Call `browser_close` as soon as the browser part of a task is
  finished, before long non-browser work or waiting on the user for something unrelated.
  This releases the profile for other sessions. Idle browsers auto-close after 30 min.
- **Who holds what:** `browser_pool_status` (MCP tool) or `pw-pool status` (shell, add
  `--all` for every pool).
- **Never kill another session's browser**, and never use `pw-pool release --force`, without
  the user's OK. A release without `--force` only clears claims whose session has exited.
- To use a specific profile (e.g. the one the user just signed in to), call
  `browser_use_profile {profile: "chrome-3"}`.
- After a profile is newly signed in and closed, `pw-pool clone <pool>/<profile> --unused`
  copies its logins into the pool's never-used profiles.
