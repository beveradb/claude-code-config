"""Black-box tests for bin/pw-pool using a fake Playwright MCP child.

Run: python3 -m unittest discover -s tests/pw_pool -v
"""
import json
import os
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PW_POOL = REPO / "bin" / "pw-pool"
FAKE = Path(__file__).with_name("fake_mcp.py")


class SlotClient:
    """Speaks newline-delimited JSON-RPC to a `pw-pool slot` process."""

    def __init__(self, env, pool="testpool", browser="chrome", name="playwright-chrome-1"):
        self.p = subprocess.Popen([sys.executable, str(PW_POOL), "slot", "--pool", pool,
                                   "--browser", browser, "--name", name],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, env=env, text=True)
        self.q = queue.Queue()
        self.seq = 0
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.p.stdout:
            self.q.put(json.loads(line))

    def request(self, method, params=None, timeout=20):
        self.seq += 1
        mid = self.seq
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": mid, "method": method,
                                       "params": params or {}}) + "\n")
        self.p.stdin.flush()
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = self.q.get(timeout=max(0.1, deadline - time.time()))
            if msg.get("id") == mid:
                return msg
        raise TimeoutError(method)

    def init(self):
        r = self.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                        "clientInfo": {"name": "test", "version": "1"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.p.stdin.flush()
        return r

    def call(self, name, args=None):
        return self.request("tools/call", {"name": name, "arguments": args or {}})["result"]

    def close(self):
        if self.p.poll() is None:
            self.p.stdin.close()
            try:
                self.p.wait(15)
            except subprocess.TimeoutExpired:
                self.p.kill()
        self.p.stdout.close()


def text(result):
    return result["content"][0]["text"]


class PwPoolTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "pools.json").write_text(json.dumps({
            "chrome": 2, "firefox": 1,
            "mcp_command": [sys.executable, str(FAKE)], "mcp_args": [],
            "pools": {"testpool": {"account": "me@example.com"}, "other": {"chrome": 1}},
        }))
        self.env = dict(os.environ, PW_POOL_ROOT=str(self.root))
        self.clients = []

    def tearDown(self):
        for c in self.clients:
            c.close()
        self.tmp.cleanup()

    def slot(self, **kw):
        c = SlotClient(self.env, **kw)
        self.clients.append(c)
        c.init()
        return c

    def cli(self, *args, check=True):
        r = subprocess.run([sys.executable, str(PW_POOL), *args], env=self.env,
                           capture_output=True, text=True)
        if check and r.returncode:
            self.fail(f"pw-pool {args} failed: {r.stderr}")
        return r

    def status(self, pool="testpool"):
        data = json.loads(self.cli("status", "--pool", pool, "--json").stdout)
        return {p["profile"]: p for p in data[0]["profiles"]}

    def wait_for(self, cond, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if cond():
                return True
            time.sleep(0.2)
        return False

    def test_initialize_and_tools_list_without_profile(self):
        c = SlotClient(self.env)
        self.clients.append(c)
        init = c.init()["result"]
        self.assertIn("testpool", init["instructions"])
        self.assertIn("me@example.com", init["instructions"])
        names = [t["name"] for t in c.request("tools/list")["result"]["tools"]]
        self.assertEqual(names, ["browser_navigate", "browser_wait", "browser_close",
                                 "browser_pool_status", "browser_use_profile"])
        # Tool listing alone must not claim a profile.
        self.assertTrue(all(p["state"] == "free" for p in self.status().values()))
        self.assertTrue((self.root / ".cache" / "tools.json").exists())

    def test_first_call_claims_profile_and_close_releases(self):
        c = self.slot()
        r = c.call("browser_navigate", {"url": "https://example.com"})
        self.assertIn(f"udd={self.root}/testpool/chrome-1", text(r))
        st = self.status()["chrome-1"]
        self.assertEqual(st["state"], "held")
        self.assertEqual(st["meta"]["slot"], "playwright-chrome-1")
        c.call("browser_close")
        self.assertTrue(self.wait_for(lambda: self.status()["chrome-1"]["state"] == "free"))

    def test_concurrent_slots_get_different_profiles_then_report_none_free(self):
        a, b, c = self.slot(), self.slot(name="playwright-chrome-2"), self.slot(name="playwright-chrome-3")
        ra, rb = text(a.call("browser_navigate")), text(b.call("browser_navigate"))
        self.assertNotEqual(ra.split("udd=")[1], rb.split("udd=")[1])
        rc = c.call("browser_navigate")
        self.assertTrue(rc["isError"])
        self.assertIn("No free chrome profile in pool 'testpool'", text(rc))
        self.assertIn("held by playwright-chrome-1", text(rc))

    def test_slots_never_cross_pools(self):
        a = self.slot(pool="other")
        self.assertIn("/other/chrome-1", text(a.call("browser_navigate")))
        b = self.slot(pool="other", name="playwright-chrome-2")
        self.assertTrue(b.call("browser_navigate")["isError"])  # 'other' has only one chrome
        self.assertEqual(self.status()["chrome-1"]["state"], "free")

    def test_child_that_dies_during_startup_fails_fast(self):
        cfg = json.loads((self.root / "pools.json").read_text())
        cfg["mcp_command"] = [sys.executable, "-c", "import sys; sys.exit(1)"]
        (self.root / "pools.json").write_text(json.dumps(cfg))
        t = time.time()
        c = self.slot()  # initialize: tool-list fetch fails, falls back to own tools
        r = c.call("browser_navigate")
        self.assertTrue(r["isError"])
        self.assertIn("Could not start Playwright", text(r))
        self.assertLess(time.time() - t, 10)
        self.assertEqual(self.status()["chrome-1"]["state"], "free")

    def test_firefox_is_signed_out_by_design(self):
        f = SlotClient(self.env, browser="firefox", name="playwright-firefox-1")
        self.clients.append(f)
        ins = f.init()["result"]["instructions"]
        self.assertIn("DELIBERATELY SIGNED OUT", ins)
        self.assertNotIn("me@example.com", ins)
        chrome = self.slot()
        self.assertIn("me@example.com", chrome.request("initialize", {"protocolVersion": "2025-06-18"})["result"]["instructions"])
        st = text(chrome.call("browser_pool_status"))
        self.assertIn("firefox-1: free (signed out by design)", st)
        self.assertIn("chrome-1: free (new, not signed in yet)", st)
        self.assertIn("firefox signed out by design", self.cli("status", "--pool", "testpool").stdout)

    def test_warns_when_signed_out_profile_has_google_session(self):
        d = self.root / "testpool" / "firefox-1"
        d.mkdir(parents=True)
        con = sqlite3.connect(d / "cookies.sqlite")
        con.execute("create table moz_cookies (host text, name text)")
        con.execute("insert into moz_cookies values ('.google.com', 'SID')")
        con.commit()
        con.close()
        out = self.cli("status", "--pool", "testpool").stdout
        self.assertIn("WARNING: has a Google session but should be signed out", out)

    def test_signed_out_is_configurable_per_pool(self):
        cfg = json.loads((self.root / "pools.json").read_text())
        cfg["pools"]["testpool"]["signed_out"] = []
        (self.root / "pools.json").write_text(json.dumps(cfg))
        f = SlotClient(self.env, browser="firefox", name="playwright-firefox-1")
        self.clients.append(f)
        self.assertIn("signed in as me@example.com", f.init()["result"]["instructions"])

    def test_firefox_slot_uses_firefox_profiles(self):
        f = self.slot(browser="firefox", name="playwright-firefox-1")
        self.assertIn("/testpool/firefox-1", text(f.call("browser_navigate")))

    def test_dead_slot_releases_lock(self):
        c = self.slot()
        c.call("browser_navigate")
        self.assertEqual(self.status()["chrome-1"]["state"], "held")
        c.p.kill()
        c.p.wait()
        self.assertTrue(self.wait_for(lambda: self.status()["chrome-1"]["state"] == "free"))

    def test_idle_timeout_releases(self):
        self.env["PW_POOL_IDLE_MINUTES"] = str(1 / 60)  # one second
        c = self.slot()
        c.call("browser_navigate")
        self.assertTrue(self.wait_for(lambda: self.status()["chrome-1"]["state"] == "free"))
        # The next call transparently re-acquires.
        self.assertIn("chrome-1", text(c.call("browser_navigate")))

    def test_pinned_profile_without_browser_is_idled_out(self):
        self.env["PW_POOL_IDLE_MINUTES"] = str(1 / 60)
        c = self.slot()
        c.call("browser_use_profile", {"profile": "chrome-2"})
        self.assertTrue(self.wait_for(lambda: self.status()["chrome-2"]["state"] == "free"))

    def test_status_without_session_metadata(self):
        c = SlotClient(dict(self.env, CLAUDE_CONFIG_DIR=str(self.root / "nocfg")))
        self.clients.append(c)
        c.init()
        c.call("browser_navigate")
        self.assertIn("chrome-1: held by playwright-chrome-1", text(c.call("browser_pool_status")))

    def test_inflight_call_is_not_idled_out(self):
        self.env["PW_POOL_IDLE_MINUTES"] = str(1 / 60)  # one second, shorter than the call
        c = self.slot()
        self.assertIn("ok", text(c.call("browser_wait", {"s": 2.5})))
        self.assertEqual(self.status()["chrome-1"]["state"], "held")

    def test_use_profile_switches_and_validates(self):
        c = self.slot()
        c.call("browser_navigate")
        r = c.call("browser_use_profile", {"profile": "chrome-2"})
        self.assertFalse(r["isError"], text(r))
        self.assertIn("/testpool/chrome-2", text(c.call("browser_navigate")))
        self.assertEqual(self.status()["chrome-1"]["state"], "free")
        bad = c.call("browser_use_profile", {"profile": "firefox-1"})
        self.assertTrue(bad["isError"])

    def test_pool_status_tool(self):
        c = self.slot()
        c.call("browser_navigate")
        s = text(c.call("browser_pool_status"))
        self.assertIn("using testpool/chrome-1", s)
        self.assertIn("me@example.com", s)
        self.assertIn("(this server)", s)
        self.assertIn("chrome-2: free (new, not signed in yet)", s)

    def test_release_refuses_live_session_unless_forced(self):
        c = self.slot()
        c.call("browser_navigate")
        owner = self.status()["chrome-1"]["meta"].get("claude_pid")
        r = self.cli("release", "testpool/chrome-1", check=False)
        # Under Claude Code the owner is alive; outside it the owner is unknown. Both need --force.
        self.assertNotEqual(r.returncode, 0, owner)
        self.assertIn("--force", r.stderr)
        self.assertEqual(self.status()["chrome-1"]["state"], "held")
        self.cli("release", "testpool/chrome-1", "--force")
        self.assertEqual(self.status()["chrome-1"]["state"], "free")
        self.assertEqual(c.p.poll(), None)  # the slot itself keeps running
        self.assertIn("chrome-1", text(c.call("browser_navigate")))

    def test_clone_unused_skips_lock_files(self):
        c = self.slot()
        c.call("browser_navigate")
        r = self.cli("clone", "testpool/chrome-1", "--unused", check=False)
        self.assertNotEqual(r.returncode, 0)  # source still open
        c.call("browser_close")
        self.wait_for(lambda: self.status()["chrome-1"]["state"] == "free")
        self.cli("clone", "testpool/chrome-1", "--unused")
        dst = self.root / "testpool" / "chrome-2"
        self.assertTrue((dst / "Cookies").exists())
        self.assertFalse((dst / "SingletonLock").exists())
        r = self.cli("clone", "testpool/chrome-1", "--to", "chrome-2")
        self.assertIn("already has data", r.stdout)

    def test_unmanaged_browser_on_profile_is_skipped(self):
        d = self.root / "testpool" / "chrome-1"
        d.mkdir(parents=True)
        # A process whose argv looks like a browser on chrome-1 (e.g. a legacy MCP server's Chrome).
        fake = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", f"--user-data-dir={d}"])
        try:
            self.assertEqual(self.status()["chrome-1"]["state"], "open-unmanaged")
            c = self.slot()
            self.assertIn("/testpool/chrome-2", text(c.call("browser_navigate")))
        finally:
            fake.kill()
            fake.wait()

    def test_profile_10_does_not_shadow_profile_1(self):
        cfg = json.loads((self.root / "pools.json").read_text())
        cfg["chrome"] = 10
        (self.root / "pools.json").write_text(json.dumps(cfg))
        d = self.root / "testpool" / "chrome-10"
        d.mkdir(parents=True)
        (self.root / "testpool" / "chrome-1").mkdir()
        fake = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", f"--user-data-dir={d}"])
        try:
            st = self.status()
            self.assertEqual(st["chrome-10"]["state"], "open-unmanaged")
            self.assertEqual(st["chrome-1"]["state"], "free")
        finally:
            fake.kill()
            fake.wait()

    def test_install_dry_run(self):
        cd = self.root / "cfg"
        cd.mkdir()
        (cd / ".claude.json").write_text(json.dumps({"mcpServers": {"playwright-chrome-3": {}, "other": {}}}))
        (cd / "settings.json").write_text(json.dumps({"permissions": {"allow": ["mcp__playwright-chrome-3__*", "Bash"]}}))
        out = self.cli("install", "--config-dir", str(cd), "--pool", "testpool", "--dry-run").stdout
        self.assertIn("claude mcp remove --scope user playwright-chrome-3", out)
        self.assertIn("slot --pool testpool --browser firefox --name playwright-firefox-1", out)
        self.assertIn("mcp__playwright-chrome-3__*", out)
        self.assertIn("mcp__playwright-chrome-3__*", (cd / "settings.json").read_text())  # dry run
        bad = self.cli("install", "--config-dir", str(cd), "--pool", "nope", "--dry-run", check=False)
        self.assertNotEqual(bad.returncode, 0)


if __name__ == "__main__":
    unittest.main()
