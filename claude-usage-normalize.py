#!/usr/bin/env python3
"""Normalize the Claude OAuth usage response into a compact statusline shape.

Reads the raw JSON from `GET https://api.anthropic.com/api/oauth/usage` on
stdin and emits:

    {"items": [{"label": "5h", "percent": 3, "reset": 1786990199, "active": false}, ...],
     "credits": {"percent": 1, "used": 2.06, "limit": 200.0} | null}

Ordering: session (5h) -> weekly_all (7d) -> per-model scoped buckets (e.g. Fable).
Unknown/future `limits[].kind` values are passed through generically so new
buckets (e.g. a future Opus-scoped limit) render automatically.
"""
import json
import sys
from datetime import datetime


def to_epoch(iso):
    if not iso:
        return None
    try:
        return int(datetime.fromisoformat(iso).timestamp())
    except (ValueError, TypeError):
        return None


def label_for(entry):
    kind = entry.get("kind")
    if kind == "session":
        return "5h"
    if kind == "weekly_all":
        return "7d"
    if kind == "weekly_scoped":
        scope = entry.get("scope") or {}
        model = (scope.get("model") or {}).get("display_name")
        surface = scope.get("surface")
        return model or surface or "scoped"
    # Unknown kind: fall back to a readable slug of the kind.
    return (kind or "?").replace("_", " ")


def sort_key(entry):
    order = {"session": 0, "weekly_all": 1, "weekly_scoped": 2}
    return order.get(entry.get("kind"), 3)


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(1)
    if not isinstance(data, dict) or "limits" not in data:
        # Not a valid usage payload (e.g. an auth error body) -> refuse to
        # overwrite a good cache with garbage.
        sys.exit(1)

    items = []
    for entry in sorted(data.get("limits") or [], key=sort_key):
        pct = entry.get("percent")
        if pct is None:
            continue
        items.append(
            {
                "label": label_for(entry),
                "percent": pct,
                "reset": to_epoch(entry.get("resets_at")),
                "active": bool(entry.get("is_active")),
                "severity": entry.get("severity") or "normal",
            }
        )

    credits = None
    spend = data.get("spend")
    if isinstance(spend, dict) and spend.get("enabled"):
        used = spend.get("used") or {}
        limit = spend.get("limit") or {}

        def money(m):
            amt = m.get("amount_minor")
            exp = m.get("exponent", 2)
            return None if amt is None else amt / (10 ** exp)

        credits = {
            "percent": spend.get("percent", 0),
            "used": money(used),
            "limit": money(limit),
        }

    json.dump({"items": items, "credits": credits}, sys.stdout)


if __name__ == "__main__":
    main()
