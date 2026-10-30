#!/usr/bin/env python3
"""Stand-in for @playwright/mcp: answers initialize/tools/list and echoes tool calls."""
import json
import sys

argv = sys.argv[1:]
udd = argv[argv.index("--user-data-dir") + 1] if "--user-data-dir" in argv else None
if udd:
    open(f"{udd}/SingletonLock", "w").close()  # something clone must not copy
    with open(f"{udd}/Cookies", "a") as f:
        f.write("cookie\n")

TOOLS = [{"name": n, "description": n, "inputSchema": {"type": "object"}}
         for n in ("browser_navigate", "browser_wait", "browser_close")]

for line in sys.stdin:
    msg = json.loads(line)
    mid, method = msg.get("id"), msg.get("method")
    if mid is None:
        continue
    if method == "initialize":
        res = {"protocolVersion": msg["params"]["protocolVersion"], "capabilities": {"tools": {}},
               "serverInfo": {"name": "Playwright", "version": "fake"}}
    elif method == "tools/list":
        res = {"tools": TOOLS}
    elif method == "tools/call":
        name = msg["params"]["name"]
        if name == "browser_wait":
            import time
            time.sleep(float(msg["params"].get("arguments", {}).get("s", 1)))
        res = {"content": [{"type": "text", "text": f"{name} ok udd={udd}"}]}
    else:
        print(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": method}}), flush=True)
        continue
    print(json.dumps({"jsonrpc": "2.0", "id": mid, "result": res}), flush=True)
