#!/usr/bin/env python3
"""ue_connect.py - one-click UE5.8 MCP connectivity pipeline (novice mode).

Subcommands:
    check   Diagnose (read-only): UE process, port 8000 vs real /mcp endpoint,
            non-UE port listeners, .uproject plugin audit. Exit 0 = connected.
    launch  Ensure plugins (only with --fix-plugins; auto-backup .uproject.bak),
            spawn UE DETACHED with -ModelContextProtocolStartServer, return
            immediately (run `wait` next, in a SEPARATE shell call).
    wait    Poll /mcp until online (progress print every 30s; first AllToolsets
            load takes ~4.5 min). On success: full handshake + toolset count.
    all     check -> (fix/launch) -> wait -> report. Convenient for interactive
            single-shot use; agents should prefer separate launch/wait calls
            (long-running shell calls that get cancelled can kill child trees).

State (engine + project paths) is cached at ~/.codely-cli/ue_connect_state.json,
so after the first successful launch later runs need no arguments.

Exit codes: 0 connected/ok | 1 action needed (see report) | 2 hard error |
3 launched, awaiting `wait`.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

MCP_URL = "http://127.0.0.1:8000/mcp"
REQUIRED_PLUGINS = ["ModelContextProtocol", "ToolsetRegistry", "EditorToolset",
                    "PythonScriptPlugin", "AllToolsets"]
STATE_PATH = os.path.join(os.path.expanduser("~"), ".codely-cli", "ue_connect_state.json")
IS_WIN = sys.platform == "win32"


# ---------- state ----------
def load_state():
    try:
        with open(STATE_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(engine=None, project=None, pid=None):
    st = load_state()
    if engine:
        st["engine"] = engine
    if project:
        st["project"] = project
    if pid:
        st["last_pid"] = pid
    st["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2)


# ---------- probes ----------
def ue_process_alive():
    try:
        if IS_WIN:
            out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq UnrealEditor.exe", "/FO", "CSV"],
                                 capture_output=True, text=True, timeout=15).stdout
            return "UnrealEditor.exe" in out
        out = subprocess.run(["pgrep", "-x", "UnrealEditor"],
                             capture_output=True, text=True, timeout=15)
        return out.returncode == 0
    except Exception:
        return False


def http_post(url, body, timeout=4):
    data = body.encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace"), dict(r.headers)


def probe_mcp():
    """Returns (state, detail): 'mcp-ok' | 'http-not-mcp' | 'closed'."""
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "ue_connect", "version": "1.0"}}})
    try:
        text, headers = http_post(MCP_URL, init)
        if "protocolVersion" in text:
            return "mcp-ok", headers.get("Mcp-Session-Id") or headers.get("mcp-session-id")
        return "http-not-mcp", "initialize returned 200 but no protocolVersion"
    except urllib.error.HTTPError as e:
        return "http-not-mcp", "HTTP {} at initialize".format(e.code)
    except Exception:
        return "closed", "no listener / connection refused"


def full_handshake_and_count():
    """Assumes /mcp is alive: completes the session and counts toolsets."""
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "ue_connect", "version": "1.0"}}})
    try:
        _, h1 = http_post(MCP_URL, init, timeout=6)
        sid = h1.get("Mcp-Session-Id") or h1.get("mcp-session-id")
        if sid:
            body = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
            req = urllib.request.Request(MCP_URL, data=body.encode(),
                                         headers={"Content-Type": "application/json",
                                                  "Mcp-Session-Id": sid}, method="POST")
            urllib.request.urlopen(req, timeout=5).read()
        inner = {"tool_name": "list_toolsets", "arguments": {}}
        body = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                           "params": {"name": "call_tool", "arguments": inner}})
        headers = {"Content-Type": "application/json"}
        if sid:
            headers["Mcp-Session-Id"] = sid
        req = urllib.request.Request(MCP_URL, data=body.encode(), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            j = json.loads(r.read().decode("utf-8", "replace"))
        txt = j["result"]["content"][0]["text"]
        n = txt.count("\n- ") + (1 if txt.strip().startswith("- ") else 0)
        return n if n > 0 else "?"
    except Exception as e:
        return "count-failed ({})".format(str(e)[:60])


# ---------- .uproject plugin audit / fix ----------
def audit_plugins(project_path):
    """Returns (missing, data). project_path = path to .uproject."""
    with open(project_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    enabled = {p.get("Name") for p in data.get("Plugins", []) if p.get("Enabled")}
    missing = [p for p in REQUIRED_PLUGINS if p not in enabled]
    return missing, data


def fix_plugins(project_path):
    missing, data = audit_plugins(project_path)
    if not missing:
        return []
    backup = project_path + ".bak"
    with open(project_path, "r", encoding="utf-8-sig") as f:
        raw = f.read()
    with open(backup, "w", encoding="utf-8") as f:
        f.write(raw)
    plugins = data.setdefault("Plugins", [])
    for name in missing:
        plugins.append({"Name": name, "Enabled": True})
    with open(project_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent="\t")
    return missing


# ---------- engine discovery ----------
def editor_binary(engine_root):
    if IS_WIN:
        p = os.path.join(engine_root, "Engine", "Binaries", "Win64", "UnrealEditor.exe")
    else:
        p = os.path.join(engine_root, "Engine", "Binaries", "Mac",
                         "UnrealEditor.app", "Contents", "MacOS", "UnrealEditor")
    return p if os.path.exists(p) else None


def autodetect_engine():
    st = load_state()
    candidates = [st.get("engine"), "E:\\UE_5.8", "C:\\Program Files\\Epic Games\\UE_5.8",
                  "D:\\UE_5.8", "/Users/Shared/Epic Games/UE_5.8"]
    for c in candidates:
        if c:
            b = editor_binary(c)
            if b:
                return c, b
    return None, None


# ---------- subcommands ----------
def cmd_check(args):
    state = load_state()
    alive = ue_process_alive()
    mcp, detail = probe_mcp()
    print("== ue_connect check ==")
    print("UE process: {}".format("RUNNING" if alive else "not running"))
    print("MCP endpoint ({}): {}".format(MCP_URL, mcp if mcp != "closed" else "closed ({})".format(detail)))

    project = args.project or state.get("project")
    missing = None
    if project and os.path.exists(project):
        try:
            missing, _ = audit_plugins(project)
            print(".uproject plugin audit ({}): {}".format(
                os.path.basename(project),
                "all {} required present".format(len(REQUIRED_PLUGINS)) if not missing
                else "MISSING {}".format(", ".join(missing))))
        except Exception as e:
            print(".uproject audit failed: {}".format(str(e)[:80]))

    if mcp == "mcp-ok":
        n = full_handshake_and_count()
        print("\nVERDICT: CONNECTED - UE MCP alive, {} toolsets ready.".format(n))
        save_state()
        return 0
    if alive:
        print("\nVERDICT: UE is running but the MCP endpoint is not answering ({}).".format(detail))
        print("If it has been loading for >6 min: open the UE Output Log console and run")
        print("`ModelContextProtocol.StartServer`, or close UE and run: ue_connect.py launch")
        return 1
    if mcp == "http-not-mcp":
        print("\nVERDICT: port 8000 is held by a NON-UE listener (initialize -> 404).")
        print("Locate it:  Windows: netstat -ano | findstr :8000   macOS: lsof -i :8000")
        print("Kill that process (UE's MCP server needs port 8000), then run: ue_connect.py launch")
        return 1
    if missing:
        print("\nVERDICT: UE not running AND plugins missing from .uproject.")
        print("Fix with: ue_connect.py launch --project <path> --fix-plugins  (backs up .uproject.bak)")
        return 1
    print("\nVERDICT: UE not running.")
    print("Action: ue_connect.py launch --project <path/to/XX.uproject>   (first time)")
    print("        ue_connect.py launch                                  (uses saved state)")
    return 1


def cmd_launch(args):
    state = load_state()
    project = args.project or state.get("project")
    if not project:
        print("No project known. Pass --project <path/to/XX.uproject> (saved for next time).")
        return 2
    if not os.path.exists(project):
        print("Project not found: {}".format(project))
        return 2

    if ue_process_alive():
        print("UE is ALREADY RUNNING - refusing to double-launch. Run `check` to see its state.")
        return 1

    missing, _ = audit_plugins(project)
    if missing:
        if not args.fix_plugins:
            print(".uproject is MISSING plugins: {}".format(", ".join(missing)))
            print("Project-file edits need your consent (Danger Gate): re-run with --fix-plugins")
            print("(a .uproject.bak backup is written before any change).")
            return 1
        fixed = fix_plugins(project)
        print("plugins added (backup at .uproject.bak): {}".format(", ".join(fixed)))

    engine_root, binary = (None, None)
    if args.engine:
        engine_root, binary = args.engine, editor_binary(args.engine)
    if not binary:
        engine_root, binary = autodetect_engine()
    if not binary:
        print("UE 5.8 editor binary not found. Pass --engine <UE root> (folder containing Engine/).")
        return 2

    popen_kwargs = {}
    if IS_WIN:
        popen_kwargs["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    try:
        p = subprocess.Popen([binary, os.path.abspath(project), "-ModelContextProtocolStartServer"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             stdin=subprocess.DEVNULL, **popen_kwargs)
    except Exception as e:
        print("launch failed: {}".format(e))
        return 2
    save_state(engine=engine_root, project=os.path.abspath(project), pid=p.pid)
    print("UE launched (pid {}, engine {}, project {}).".format(p.pid, engine_root, project))
    print("Now run `wait` in a SEPARATE shell call - first AllToolsets load takes ~4.5 min.")
    return 3


def cmd_wait(args):
    timeout = getattr(args, "timeout", 420)  # `all` namespace lacks --timeout
    t0 = time.time()
    deadline = t0 + timeout
    print("waiting for MCP endpoint (timeout {}s; progress every 30s)...".format(timeout))
    last_report = t0
    while time.time() < deadline:
        mcp, _ = probe_mcp()
        if mcp == "mcp-ok":
            n = full_handshake_and_count()
            print("CONNECTED after {:.0f}s - UE MCP alive, {} toolsets ready.".format(time.time() - t0, n))
            save_state()
            return 0
        if time.time() - last_report >= 30:
            print("  still loading... {:.0f}s elapsed (first AllToolsets load ~= 4.5 min)".format(time.time() - t0))
            last_report = time.time()
        time.sleep(5)
    print("TIMEOUT after {}s. Run `check` for a diagnosis (UE may be showing a firewall dialog".format(timeout))
    print("or a modal - see the check verdict).")
    return 2


def cmd_all(args):
    rc = cmd_check(args)
    if rc == 0:
        return 0
    if rc == 1:
        rc2 = cmd_launch(args)
        if rc2 != 3:
            return rc2
        return cmd_wait(args)
    return rc


def main():
    ap = argparse.ArgumentParser(description="one-click UE5.8 MCP connectivity pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("check", "launch", "all"):
        p = sub.add_parser(name)
        p.add_argument("--project", help="path to .uproject (cached after first success)")
        p.add_argument("--engine", help="UE root folder containing Engine/ (autodetected if omitted)")

    w = sub.add_parser("wait")
    w.add_argument("--timeout", type=int, default=420)

    sub.choices["launch"].add_argument("--fix-plugins", action="store_true",
                                       help="consent to .uproject edit (writes .uproject.bak first)")

    args = ap.parse_args()
    fn = {"check": cmd_check, "launch": cmd_launch, "wait": cmd_wait, "all": cmd_all}[args.cmd]
    return fn(args)


if __name__ == "__main__":
    sys.exit(main())
