"""Reusable template for UE blueprint editing via ProgrammaticToolset. v2 (2026-08-28)

Battle-tested helpers from the 2026-08-28 sessions (flip-wall / orbit-puzzle tasks).
Copy this file, modify the run() function, then send via:
  powershell -File mcp_call.ps1 -ScriptPath "this_file.py" -ResultFile "result.json"

Key rules:
  - run() MUST return a dict (list return = "must return a dict[str, Any]" error)
  - One failing execute_tool call ABORTS the whole script (try/except does NOT catch) —
    keep scripts idempotent so re-running after a fix converges (SKILL#42)
  - Chinese type_id strings must use \\uXXXX escapes if locale reverts to Chinese
  - Sandbox allows: json, math, re, time, copy, datetime. Dict-like results support []
    but NOT .get() with default
"""
import json
import re

BT = "editor_toolset.toolsets.blueprint.BlueprintTools"
SC = "editor_toolset.toolsets.scene.SceneTools"
PT = "editor_toolset.toolsets.primitive.PrimitiveTools"
AKT = "editor_toolset.toolsets.actor.ActorTools"
AST = "editor_toolset.toolsets.asset.AssetTools"
OT = "editor_toolset.toolsets.object.ObjectTools"
EA = "EditorToolset.EditorAppToolset"


def call(tool_name, args, toolset=BT):
    """Call a toolset tool. toolset= is OPTIONAL (defaults to BlueprintTools)."""
    return execute_tool(toolset + "." + tool_name, json.dumps(args))


def rv(r):
    """Unwrap returnValue from a tool result dict."""
    try:
        return r["returnValue"]
    except Exception:
        return r


def as_ref(r):
    """Extract a {"refPath": ...} from any tool result shape."""
    r = rv(r)
    if isinstance(r, dict) and ("refPath" in r):
        return r
    if isinstance(r, str) and r.startswith("/"):
        return {"refPath": r}
    s = json.dumps(r)
    m = re.search(r'"refPath"\s*:\s*"([^"]+)"', s)
    if m:
        return {"refPath": m.group(1)}
    return None


def truthy(v):
    """Interpret tool truthiness across string/bool serialization variants."""
    if isinstance(v, bool):
        return v
    s = v if isinstance(v, str) else json.dumps(v)
    return "true" in s.lower()


def asset_exists(path):
    """In-memory asset existence (NOT a disk check — SKILL#46)."""
    try:
        return truthy(rv(call("exists", {"path": path}, AST)))
    except Exception:
        return False


def set_props(inst, values, results, label):
    """set_properties with nested->flat fallback. ALWAYS read back critical fields (SKILL#41)."""
    try:
        call("set_properties", {"instance": inst, "values": json.dumps(values)}, OT)
        results.append(label + ":props-ok")
        return
    except Exception:
        pass
    flat = {}
    for k in values:
        v = values[k]
        if isinstance(v, dict):
            for k2 in v:
                flat[k + "." + k2] = v[k2]
        else:
            flat[k] = v
    call("set_properties", {"instance": inst, "values": json.dumps(flat)}, OT)
    results.append(label + ":props-flat")


def find_component_ref(actor_or_cdo, cname):
    """Find a component ref by name on an actor/CDO (handles list of bare refs)."""
    try:
        comps = rv(call("get_components", {"actor": actor_or_cdo}, AKT))
        s = json.dumps(comps)
        m = re.search(r'"refPath"\s*:\s*"([^"]*:' + re.escape(cname) + r'(?:_GEN_VARIABLE)?)"', s)
        if m:
            return {"refPath": m.group(1)}
    except Exception:
        pass
    return None


def has_variable(bp, vname):
    try:
        vs = json.dumps(rv(call("list_variables", {"blueprint": bp})))
        return ('"' + vname + '"') in vs
    except Exception:
        return False


def remove_actors_named(name):
    """Remove all /Temp/ actors matching name (idempotent re-placement guard). Returns count."""
    removed = 0
    a = rv(call("find_actors", {"name": name, "tag": "", "collision_channels": []}, SC))
    for ref in re.findall(r'"refPath"\s*:\s*"(/Temp/[^"]+)"', json.dumps(a)):
        call("remove_from_scene", {"actor": {"refPath": ref}}, SC)
        removed += 1
    return removed


def save_all_and_report(results):
    """save_assets(all dirty) — disk verification must follow outside UE (SKILL#46)."""
    call("save_assets", {"asset_paths": []}, AST)
    results.append("saved-all-dirty (verify on disk!)")


# --- legacy pin-level helpers (node wiring) ---

def get_pin(pins, name):
    """Find a pin by name. Returns None if not found."""
    for p in pins:
        if p["name"] == name:
            return p
    return None


def find_type(graph_ref, search):
    """Find node type IDs matching a search string."""
    r = call("find_node_types", {"graph": graph_ref, "type_id_filter": search, "context_pins": []})
    return r["returnValue"]


def create_node(graph_ref, type_id, x=0, y=0):
    """Create a node and return its ref."""
    r = call("create_node", {"graph": graph_ref, "type_id": type_id, "pos": {"x": x, "y": y}})
    return r["returnValue"]


def connect(out_pin, in_pin):
    """Connect two pins (pin_id dicts)."""
    call("connect_pins", {"output_pin": out_pin, "input_pin": in_pin})


def connect_safe(ti, oi, src_name, dst_name, results, label=""):
    """Connect output pin src_name to input pin dst_name. Skips if already connected."""
    src = get_pin(ti["output_pins"], src_name)
    dst = get_pin(oi["input_pins"], dst_name)
    if src and dst and not dst["connected_pins"]:
        connect(src["pin_id"], dst["pin_id"])
        results.append(label or (src_name + "->" + dst_name))
    elif dst and dst["connected_pins"]:
        results.append((label or (src_name + "->" + dst_name)) + ":skip")
    return src, dst


def set_val(pin, value, results, label=""):
    """Set a pin value if not already set."""
    if pin and pin["value"] != str(value):
        call("set_pin_value", {"pin": pin["pin_id"], "value": str(value)})
        results.append(label or "set")


def run():
    # === EDIT BELOW ===
    results = []
    # ... your logic here ...
    return {"results": results, "status": "ok"}
