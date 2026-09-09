#!/bin/bash
# Fetch Claude subscription usage from the OAuth usage endpoint and cache a
# normalized, statusline-friendly JSON blob to $CACHE.
#
# Self-throttling: does nothing if the cache is younger than $TTL seconds, and
# uses an atomic mkdir lock so concurrent statusline renders never fan out into
# multiple network calls. Designed to be launched fire-and-forget in the
# background from the statusline; it exits fast on the common (cache-fresh) path.
#
# The endpoint is aggressively rate-limited, so keep $TTL >= 60.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE=/tmp/claude-usage.json
LOCK=/tmp/claude-usage.fetch.lock
TTL=60
NORMALIZE="$DIR/claude-usage-normalize.py"

mtime() { stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null || echo 0; }
now=$(date +%s)

# Fresh cache -> nothing to do.
if [ -f "$CACHE" ] && [ $((now - $(mtime "$CACHE"))) -lt "$TTL" ]; then
    exit 0
fi

# Atomic lock. If another fetch is in flight, back off (unless the lock is
# stale, in which case reclaim it).
if ! mkdir "$LOCK" 2>/dev/null; then
    if [ -d "$LOCK" ] && [ $((now - $(mtime "$LOCK"))) -gt 30 ]; then
        rmdir "$LOCK" 2>/dev/null
        mkdir "$LOCK" 2>/dev/null || exit 0
    else
        exit 0
    fi
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

# Read the OAuth access token from the macOS keychain (Claude Code refreshes it
# there during an active session, so it is normally valid).
TOKEN=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null \
    | jq -r '.claudeAiOauth.accessToken // .accessToken // empty' 2>/dev/null)
[ -z "$TOKEN" ] && exit 0

RAW=$(curl -s --max-time 10 https://api.anthropic.com/api/oauth/usage \
    -H "Authorization: Bearer $TOKEN" \
    -H "anthropic-beta: oauth-2025-04-20" \
    -H "User-Agent: claude-cli-statusline/1.0" 2>/dev/null)
[ -z "$RAW" ] && exit 0

# Normalize; only replace the cache if normalization succeeds (guards against
# overwriting good data with an auth-error/HTML/429 body).
if printf '%s' "$RAW" | python3 "$NORMALIZE" > "$CACHE.tmp" 2>/dev/null; then
    mv "$CACHE.tmp" "$CACHE"
else
    rm -f "$CACHE.tmp" 2>/dev/null
fi
