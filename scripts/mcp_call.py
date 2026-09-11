#!/usr/bin/env python3
"""Cross-platform MCP HTTP caller (macOS/Linux/Windows) - Python twin of mcp_call.ps1
plus the file-based-args design from the 2026-09-06 debug helper.

Usage:
    python3 mcp_call.py --tool list_toolsets --out result.json
    python3 mcp_call.py --tool describe_toolset --args-file args.json --out desc.json
    python3 mcp_call.py --tool create_node --toolset editor_toolset.toolsets.blueprint.BlueprintTools \
                        --args '{"graph":{"refPath":"..."},"type_id":"...","pos":{"x":1,"y":1}}' --out r.json
    python3 mcp_call.py --script batch.py --out result.json     # ProgrammaticToolset batch

Notes:
  - Reads tool arguments from --args-file (JSON file) to avoid shell quoting hell.
  - --args accepts inline JSON when convenient.
  - Session init mirrors mcp_call.ps1 (initialize -> notifications/initialized -> tools/call).
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

MCP_URL = "http://127.0.0.1:8000/mcp"
SESSION_ID = None


def post(url, body, headers=None, timeout=120):
    data = body.encode("utf-8")
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8"), dict(r.headers)


def mcp_post(url, sid, body, timeout=120):
    h = {"Mcp-Session-Id": sid} if sid else {}
    return post(url, body, h, timeout)


def main():
    ap = argparse.ArgumentParser(description="Cross-platform MCP call_tool wrapper")
    ap.add_argument("--tool", help="tool name (e.g. list_toolsets, create_node)")
    ap.add_argument("--toolset", help="toolset full name (e.g. editor_toolset.toolsets.blueprint.BlueprintTools)")
    ap.add_argument("--args", help='inline JSON args, e.g. \'{"graph":{...}}\'')
    ap.add_argument("--args-file", dest="args_file", help="JSON file with tool arguments (no shell quoting issues)")
    ap.add_argument("--script", dest="script_path", help="path to a .py batch script for execute_tool_script")
    ap.add_argument("--out", dest="out_file", help="write response text to this file")
    ap.add_argument("--url", default=MCP_URL, help="MCP server URL")
    args = ap.parse_args()

    if not args.tool and not args.script_path:
        ap.error("either --tool or --script is required")

    # session init (server 404s when the editor is closed / MCP endpoint absent)
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "codely", "version": "1.0"}}})
    try:
        _, h1 = post(args.url, init, timeout=10)
        sid = h1.get("Mcp-Session-Id") or h1.get("mcp-session-id")
    except urllib.error.HTTPError as e:
        print("HTTP-ERR at initialize: {} (is UE running with -ModelContextProtocolStartServer?)".format(e),
              file=sys.stderr)
        sys.exit(2)
    if sid:
        mcp_post(args.url, sid, json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}), timeout=5)

    # build inner call_tool arguments
    if args.script_path:
        with open(args.script_path, "r", encoding="utf-8") as f:
            content = f.read()
        inner = {"tool_name": "execute_tool_script",
                 "toolset_name": "editor_toolset.toolsets.programmatic.ProgrammaticToolset",
                 "arguments": {"script": content}}
    else:
        if args.args_file:
            with open(args.args_file, "r", encoding="utf-8") as f:
                arguments = json.load(f)
        elif args.args:
            arguments = json.loads(args.args)
        else:
            arguments = {}
        inner = {"tool_name": args.tool, "arguments": arguments}
        if args.toolset:
            inner["toolset_name"] = args.toolset

    body = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                       "params": {"name": "call_tool", "arguments": inner}})

    try:
        text, _ = mcp_post(args.url, sid, body)
        if args.out_file:
            with open(args.out_file, "w", encoding="utf-8") as f:
                f.write(text)
            print("OK -> {}".format(args.out_file))
        else:
            print(text)
    except Exception as e:
        print("HTTP-ERR: {}".format(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
