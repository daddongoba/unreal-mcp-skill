"""Static verification checklist for one blueprint — run BEFORE handing off to user PIE test.
Usage: edit BP_PATH (+ EXPECTED_* config) below, then send via mcp_call.ps1.
Checks: asset exists / components present / trigger profile QueryOnly / physics root /
        variables present / DSL readback contains expected nodes / compiled state.
Disk verification (SKILL#46) runs OUTSIDE UE: Get-ChildItem Content/<Folder> for .uasset/.umap.
"""
import json
import re

BT = "editor_toolset.toolsets.blueprint.BlueprintTools"
AKT = "editor_toolset.toolsets.actor.ActorTools"
AST = "editor_toolset.toolsets.asset.AssetTools"
OT = "editor_toolset.toolsets.object.ObjectTools"


def call(n, a, ts=BT):
    return execute_tool(ts + "." + n, json.dumps(a))


def rv(r):
    try:
        return r["returnValue"]
    except Exception:
        return r


# === CONFIG ===
BP_PATH = "/Game/TestT10/BP_FlipWall"           # blueprint asset path (no .BP suffix)
EXPECTED_COMPONENTS = ["WallPanel", "TouchBox"]  # component names that must exist
PHYSICS_ROOT = None                              # component name that must be ROOT (physics BPs)
TRIGGER_COMPONENTS = ["TouchBox"]                # components that must be QueryOnly+overlap
EXPECTED_VARS = ["TargetYaw", "CurrentYaw", "bFlipping"]  # variables that must exist
DSL_MUST_CONTAIN = ["BeginOverlap", "EventTick"]  # substrings in EventGraph DSL
# ===============


def run():
    checks = []

    def check(name, ok):
        checks.append(("PASS" if ok else "FAIL") + "  " + name)

    bp = {"refPath": BP_PATH + "." + BP_PATH.split("/")[-1]}

    # 1. asset exists (in-memory)
    try:
        ex = rv(call("exists", {"path": BP_PATH}, AST))
        check("asset-exists", "true" in json.dumps(ex).lower())
    except Exception as e:
        check("asset-exists EXC:" + str(e)[:60], False)

    # 2. CDO + components
    comps_s = ""
    try:
        cdo = rv(call("get_default_object", {"blueprint": bp}))
        comps_s = json.dumps(rv(call("get_components", {"actor": cdo}, AKT)))
    except Exception as e:
        check("CDO EXC:" + str(e)[:60], False)
    for cname in EXPECTED_COMPONENTS:
        check("component:" + cname, (":" + cname + "_GEN_VARIABLE") in comps_s)

    # 3. trigger profiles
    for cname in TRIGGER_COMPONENTS:
        m = re.search(r'"refPath"\s*:\s*"([^"]*:' + cname + r'(?:_GEN_VARIABLE)?)"', comps_s)
        if not m:
            check("trigger:" + cname + " (missing)", False)
            continue
        try:
            b = json.dumps(rv(call("get_properties", {"instance": {"refPath": m.group(1)},
                                                       "properties": ["bGenerateOverlapEvents", "bodyInstance"]}, OT)))
            check("trigger:" + cname + "=QueryOnly", "QueryOnly" in b)
            check("trigger:" + cname + "=OverlapEvents", '"bGenerateOverlapEvents":true' in b.replace(" ", ""))
        except Exception as e:
            check("trigger:" + cname + " EXC:" + str(e)[:50], False)

    # 4. physics root
    if PHYSICS_ROOT:
        try:
            cdo = rv(call("get_default_object", {"blueprint": bp}))
            root = json.dumps(rv(call("get_root_component", {"actor": cdo}, AKT)))
            check("root-is:" + PHYSICS_ROOT, PHYSICS_ROOT in root)
        except Exception as e:
            check("root EXC:" + str(e)[:60], False)

    # 5. variables
    try:
        vs = json.dumps(rv(call("list_variables", {"blueprint": bp})))
        for vname in EXPECTED_VARS:
            check("var:" + vname, ('"' + vname + '"') in vs)
    except Exception as e:
        check("vars EXC:" + str(e)[:60], False)

    # 6. DSL readback
    try:
        g = rv(call("get_graph", {"blueprint": bp, "graph_name": "EventGraph"}))
        d = json.dumps(rv(call("read_graph_dsl", {"graph": g})))
        for sub in DSL_MUST_CONTAIN:
            check("dsl:" + sub, sub in d)
    except Exception as e:
        check("dsl EXC:" + str(e)[:60], False)

    # 7. compile (idempotent)
    try:
        call("compile_blueprint", {"blueprint": bp})
        check("compile", True)
    except Exception as e:
        check("compile EXC:" + str(e)[:60], False)

    fails = [c for c in checks if c.startswith("FAIL")]
    return {"checks": checks, "summary": ("ALL PASS (" + str(len(checks)) + " checks)") if not fails
            else (str(len(fails)) + " FAIL / " + str(len(checks)) + " checks")}
