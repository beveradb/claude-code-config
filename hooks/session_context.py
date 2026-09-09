#!/usr/bin/env python3
"""SessionStart hook: inject the newest session records for the current project.

Reads the hook payload (JSON) from stdin, locates the project's session-docs
directory, and prints the newest few session records so they are added to the
new session's context. Read-only: never creates anything. Silent when there is
nothing to show.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

INJECT_ON = {"startup", "clear"}          # skip resume/compact: context retained
NUM_DOCS = 3
MAX_LINES_PER_DOC = 200
MAX_BYTES_PER_DOC = 8_000
MAX_TOTAL_BYTES = 30_000
SESSION_DIR_CANDIDATES = ("docs/sessions", "docs/archive", "sessions")

DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def project_root(start: Path) -> Path:
    """Nearest ancestor containing a .git entry, else `start` itself."""
    start = start.resolve()
    for base in (start, *start.parents):
        if (base / ".git").exists():
            return base
    return start


def find_sessions_dir(cwd: Path) -> Path | None:
    """Return the project's session-docs dir, honoring preference order."""
    root = project_root(cwd)
    for rel in SESSION_DIR_CANDIDATES:
        candidate = root / rel
        if candidate.is_dir():
            return candidate
    return None


def _sort_key(path: Path):
    m = DATE_RE.match(path.name)
    date_part = (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    return (date_part, mtime)


def newest_session_docs(sessions_dir: Path, n: int = NUM_DOCS) -> list[Path]:
    """Newest `n` markdown files under `sessions_dir` (recurses quarter dirs)."""
    docs = [p for p in sessions_dir.rglob("*.md") if p.is_file()]
    docs.sort(key=_sort_key, reverse=True)
    return docs[:n]


def _clip(text: str) -> str:
    lines = text.splitlines()
    truncated = False
    if len(lines) > MAX_LINES_PER_DOC:
        lines = lines[:MAX_LINES_PER_DOC]
        truncated = True
    clipped = "\n".join(lines)
    encoded = clipped.encode("utf-8")
    if len(encoded) > MAX_BYTES_PER_DOC:
        clipped = encoded[:MAX_BYTES_PER_DOC].decode("utf-8", "ignore")
        truncated = True
    if truncated:
        clipped += "\n... [truncated]"
    return clipped


def render(docs: list[Path], root: Path) -> str:
    if not docs:
        return ""
    out = [f"Recent session records for {root.name} "
           "(auto-loaded, read-only context):", ""]
    total = 0
    for i, doc in enumerate(docs):
        try:
            body = _clip(doc.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        try:
            label = doc.relative_to(root)
        except ValueError:
            label = doc
        block = f"----- {label} -----\n{body}\n"
        out.append(block)
        total += len(block.encode("utf-8"))
        if total > MAX_TOTAL_BYTES and i < len(docs) - 1:
            out.append("... [remaining records omitted to stay within budget]")
            break
    return "\n".join(out).rstrip() + "\n"


def build_context(cwd: str, source: str) -> str:
    """Pure entry point: return the context string to inject (may be empty)."""
    if source not in INJECT_ON:
        return ""
    cwd_path = Path(cwd) if cwd else Path.cwd()
    sessions_dir = find_sessions_dir(cwd_path)
    if sessions_dir is None:
        return ""
    docs = newest_session_docs(sessions_dir)
    return render(docs, project_root(cwd_path))


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    cwd = payload.get("cwd") or os.getcwd()
    source = payload.get("source", "startup")
    context = build_context(cwd, source)
    if context:
        print(context)


if __name__ == "__main__":
    main()
