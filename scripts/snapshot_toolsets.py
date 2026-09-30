#!/usr/bin/env python3
"""Snapshot the live UE MCP toolset/tool inventory.

Cross-platform (macOS/Linux/Windows). Requires UE running with the MCP server
(see SKILL.md -> One-Click Connect).

Usage:
    python3 snapshot_toolsets.py                      # write references/ue<ver>_baseline.json
    python3 snapshot_toolsets.py --out my.json
    python3 snapshot_toolsets.py --diff references/ue583_baseline.json
    python3 snapshot_toolsets.py --url http://127.0.0.1:8000/mcp

What it fixes over naive counting (see references/ue583_baseline.json):
  * list_toolsets prints multi-line descriptions whose bullet lines also start
    with "- ", so a line count over-reports. A real entry is the token before
    ':' matching ^[A-Za-z_][A-Za-z0-9_.]*$ (bullets contain spaces).
  * describe_toolset repeats the toolset's own name once, so counting '"name"'
    over-reports each toolset by exactly 1. We count qualified names
    '"name":"<toolset>.<tool>"' instead.
"""
import argparse
import json
import os
import re
import sys
import urllib.request

DEFAULT_URL = "http://127.0.0.1:8000/mcp"
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


def post(url, body, sid=None, timeout=180):
    headers = {"Content-Type": "application/json"}
    if sid:
        headers["Mcp-Session-Id"] = sid
    req = urllib.request.Request(url, data=body.encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8"), dict(r.headers)


class Client:
    def __init__(self, url):
        self.url = url
        self.sid = None

    def connect(self):
        init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                      "clientInfo": {"name": "snapshot", "version": "1.0"}}})
        try:
            _, headers = post(self.url, init, timeout=15)
        except Exception as e:
            sys.exit("cannot reach MCP endpoint {}: {} (is UE running with "
                     "-ModelContextProtocolStartServer?)".format(self.url, e))
        self.sid = headers.get("Mcp-Session-Id") or headers.get("mcp-session-id")
        # NOTE: the notification returns an empty body. PowerShell 5.1's
        # Invoke-WebRequest throws NullReferenceException on that; urllib is fine.
        post(self.url, json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
             self.sid, timeout=10)

    def call(self, tool, args=None, toolset=None):
        inner = {"tool_name": tool, "arguments": args or {}}
        if toolset:
            inner["toolset_name"] = toolset
        body = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                           "params": {"name": "call_tool", "arguments": inner}})
        text, _ = post(self.url, body, self.sid)
        obj = json.loads(text)
        content = obj.get("result", {}).get("content", [])
        if not content:
            raise RuntimeError("no content for {}: {}".format(tool, text[:200]))
        return content[0].get("text", "")


def parse_toolsets(raw):
    """Return (real_toolsets, phantom_entries)."""
    toolsets, others = [], []
    for line in raw.split("\n"):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        name = stripped[2:].split(":", 1)[0].strip()
        if not NAME_RE.match(name):
            continue          # description bullet line, not an entry
        if "." in name:
            toolsets.append(name)
        else:
            others.append(name)
    return sorted(set(toolsets)), sorted(set(others))


def snapshot(url):
    c = Client(url)
    c.connect()
    toolsets, others = parse_toolsets(c.call("list_toolsets"))
    inventory = {}
    for ts in toolsets:
        blob = c.call("describe_toolset", {"toolset_name": ts})
        inventory[ts] = sorted(set(
            re.findall(re.escape('"name":"' + ts + ".") + r'([A-Za-z0-9_]+)"', blob)))
    unique = set()
    for names in inventory.values():
        unique.update(names)
    return {
        "verified": __import__("datetime").date.today().isoformat(),
        "toolset_count": len(inventory),
        "tool_count": sum(len(v) for v in inventory.values()),
        "unique_tool_name_count": len(unique),
        "phantom_list_toolsets_entries": others,
        "toolsets": inventory,
    }


def diff(old, new):
    ot, nt = old.get("toolsets", {}), new.get("toolsets", {})
    lines = []
    for ts in sorted(set(ot) | set(nt)):
        if ts not in ot:
            lines.append("+ TOOLSET  {}".format(ts))
        elif ts not in nt:
            lines.append("- TOOLSET  {}".format(ts))
        else:
            added = sorted(set(nt[ts]) - set(ot[ts]))
            removed = sorted(set(ot[ts]) - set(nt[ts]))
            for t in added:
                lines.append("  + {:28s} {}".format(t, ts))
            for t in removed:
                lines.append("  - {:28s} {}".format(t, ts))
    if not lines:
        lines.append("no differences")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Snapshot the live UE MCP tool inventory")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--out", help="output path (default references/ue<toolsets>_baseline.json)")
    ap.add_argument("--diff", help="compare against this baseline JSON and print the delta")
    args = ap.parse_args()

    snap = snapshot(args.url)

    if args.diff:
        with open(args.diff, encoding="utf-8") as f:
            old = json.load(f)
        print("=== drift vs {} ===".format(os.path.basename(args.diff)))
        print("old: {} toolsets / {} tools".format(old.get("toolset_count"), old.get("tool_count")))
        print("new: {} toolsets / {} tools".format(snap["toolset_count"], snap["tool_count"]))
        print()
        print(diff(old, snap))
        return 0

    out = args.out
    if not out:
        here = os.path.dirname(os.path.abspath(__file__))
        out = os.path.join(here, os.pardir, "references", "ue_baseline.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=1)
    print("toolsets: {}  tools: {}  unique: {}".format(
        snap["toolset_count"], snap["tool_count"], snap["unique_tool_name_count"]))
    if snap["phantom_list_toolsets_entries"]:
        print("phantom list_toolsets entries (not real toolsets): {}".format(
            ", ".join(snap["phantom_list_toolsets_entries"])))
    print("wrote {}".format(os.path.abspath(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
