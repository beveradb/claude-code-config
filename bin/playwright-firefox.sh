#!/bin/bash
# Launches Playwright MCP with a lightweight copy of the user's Firefox profile.
# Only copies cookies/certs/logins — enough for authenticated sessions.

FIREFOX_PROFILE="$HOME/Library/Application Support/Firefox/Profiles/yilusvw2.default-release"
TEMP_PROFILE=$(mktemp -d)/firefox-profile
mkdir -p "$TEMP_PROFILE"

for f in cookies.sqlite cert9.db key4.db logins.json logins.db \
         permissions.sqlite prefs.js containers.json handlers.json \
         pkcs11.txt SiteSecurityServiceState.bin; do
  [ -f "$FIREFOX_PROFILE/$f" ] && cp "$FIREFOX_PROFILE/$f" "$TEMP_PROFILE/"
done

exec npx @playwright/mcp@latest --browser firefox --user-data-dir "$TEMP_PROFILE" "$@"
