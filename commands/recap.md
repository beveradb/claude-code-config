---
description: Load the most recent session records in full (on-demand complement to the SessionStart hook)
allowed-tools: Read, Bash
argument-hint: "[count] (default 5)"
---

# Recap Recent Sessions

Read the newest few session records **in full** and print a short orientation.
This is the on-demand complement to `/wrap` (which *writes* records) and the
SessionStart hook (which auto-loads the newest 3, but **truncated** to 200
lines / 8KB each). Use `/recap` when you want the complete, untruncated context
of recent sessions pulled into the conversation.

## How many

Read `$ARGUMENTS` as the number of sessions to load. Default to **5** if empty
or not a positive integer.

## Steps

### 1. Locate the sessions dir and pick the newest N

Same discovery as the hook: project git root, then the first existing of
`docs/sessions/` or `docs/archive/`. Newest is by the `YYYY-MM-DD-` date prefix
in the filename (descending). Run:

```bash
N="${ARGUMENTS:-5}"; case "$N" in ''|*[!0-9]*) N=5 ;; esac; [ "$N" -lt 1 ] && N=5
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
DIR=""
for rel in docs/sessions docs/archive; do
  [ -d "$ROOT/$rel" ] && { DIR="$ROOT/$rel"; break; }
done
if [ -z "$DIR" ]; then
  echo "No sessions dir (docs/sessions or docs/archive) found under $ROOT"
else
  find "$DIR" -type f -name '*.md' | sort -r | head -n "$N"
fi
```

If no sessions dir is found, tell the user and stop.

### 2. Read each file IN FULL

`Read` every path the command printed — completely, no offset/limit. The entire
point of `/recap` is the untruncated content, so do not skim or clip.

### 3. Orient

After loading, print a short (few-line) recap:
- **Covered:** what the loaded sessions worked on (one line each, newest first).
- **Open threads:** any "next steps" / "pick up here" notes carried forward.
- **Loaded:** the list of file paths now in context, so the user can see exactly
  what was pulled in.

Keep the orientation tight — the value is the full docs now in context, not a
long summary of them.

## Related Commands
| Command | Purpose |
|---------|---------|
| `/wrap` | Write a record of the current session |
| SessionStart hook | Auto-loads the newest 3 records (truncated) at startup |
