#!/usr/bin/env python3
"""Tests for the session-context hook.

Run: python3 ~/.claude/hooks/test_session_context.py
Exits non-zero on first failure.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import session_context as sc  # noqa: E402


def _mk(base, relname, content="x\n"):
    p = Path(base) / relname
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def test_skips_non_injecting_source():
    with tempfile.TemporaryDirectory() as d:
        _mk(d, "docs/sessions/2026-Q3/2026-09-09-a.md")
        assert sc.build_context(d, "resume") == ""
        assert sc.build_context(d, "compact") == ""


def test_empty_when_no_sessions_dir():
    with tempfile.TemporaryDirectory() as d:
        assert sc.build_context(d, "startup") == ""


def test_injects_newest_three_by_date():
    with tempfile.TemporaryDirectory() as d:
        for day in ("01", "02", "03", "04"):
            _mk(d, f"docs/sessions/2026-Q3/2026-09-{day}-x.md", f"day {day}\n")
        out = sc.build_context(d, "startup")
        assert "day 04" in out and "day 03" in out and "day 02" in out
        assert "day 01" not in out


def test_prefers_sessions_over_archive():
    with tempfile.TemporaryDirectory() as d:
        _mk(d, "docs/archive/2026-09-01-old.md", "ARCHIVE\n")
        _mk(d, "docs/sessions/2026-Q3/2026-09-09-new.md", "SESSION\n")
        out = sc.build_context(d, "startup")
        assert "SESSION" in out and "ARCHIVE" not in out


def test_archive_fallback_when_no_sessions():
    with tempfile.TemporaryDirectory() as d:
        _mk(d, "docs/archive/2026-09-01-old.md", "ARCHIVE\n")
        assert "ARCHIVE" in sc.build_context(d, "startup")


def test_clips_large_doc():
    with tempfile.TemporaryDirectory() as d:
        big = "\n".join(f"line{i}" for i in range(1000)) + "\n"
        _mk(d, "docs/sessions/2026-Q3/2026-09-09-big.md", big)
        assert "[truncated]" in sc.build_context(d, "startup")


def test_finds_dir_from_subdir_via_git_root():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".git").mkdir()
        _mk(d, "docs/sessions/2026-Q3/2026-09-09-a.md", "ROOT\n")
        sub = Path(d) / "src" / "deep"
        sub.mkdir(parents=True)
        assert "ROOT" in sc.build_context(str(sub), "startup")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\nAll {len(tests)} tests passed.")
