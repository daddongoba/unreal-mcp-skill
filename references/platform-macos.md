# Platform: macOS (unreal-mcp skill)

> Companion for running this skill on macOS. Everything NOT listed here is identical
> to the Windows baseline (skill location `~/.codely-cli/skills/unreal-mcp`, MCP
> protocol, port 8000, UE-before-Codely startup order, DSL/palette laws, all
> references/*.md content).

## 0. Platform detection dispatch (how the agent picks the script family)

1. **Primary — zero cost, always available**: the Codely session context injected at
   conversation start states `My operating system is: win32` (Windows family) /
   `darwin` (macOS) / `linux`. Dispatch on it: `win32` → use the `.ps1` script twins;
   `darwin`/`linux` → use the `.py` twins + this file.
2. **Secondary — verify when context is stale/ambiguous**: run `uname` (returns
   `Darwin` on macOS; missing on Windows where `$env:OS` returns `Windows_NT`), or
   `python3 -c "import sys; print(sys.platform)"` → `win32` / `darwin`.
3. The UE/MCP layer is platform-INDEPENDENT (port 8000, refPaths, DSL) — only the
   helper scripts and the editor launch command differ by platform.

## 1. Environment differences

| Item | Windows baseline | macOS |
|---|---|---|
| Skill path | `C:\Users\<u>\.codely-cli\skills\unreal-mcp` | `~/.codely-cli/skills/unreal-mcp` (same layout) |
| Shell / script flavor | PowerShell 5.1 (`scripts/*.ps1`) | zsh/bash — use the Python twins (`scripts/*.py`) |
| Python | `python` (3.12) | `python3` (system or brew; no extra deps — stdlib only) |
| UE editor binary | `E:\UE_5.8\...\UnrealEditor.exe "<proj>.uproject" -ModelContextProtocolStartServer` | `/Users/Shared/Epic\ Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor "<proj>.uproject" -ModelContextProtocolStartServer` (launch with `open -a` is possible but args pass more reliably via the inner binary) |
| Text encoding | UTF-8 no-BOM pitfalls + GBK console risk (PS 5.1) | UTF-8 everywhere — no GBK layer; the PS BOM/encoding notes do NOT apply |
| Project paths | drive letters `F:\...` | POSIX `/Users/...`; write_file absolute paths are `/Users/...` |
| Node dictionary BOM | PS tolerates; Python scripts must use `utf-8-sig` (already handled in `search_node_dict.py`) | same — the py twins already handle it |

## 2. Cross-platform script twins (use these on macOS)

| Task | Windows (ps1) | macOS/Linux (py) |
|---|---|---|
| Node/pin lookup | `search_node_dict.ps1 -Query X [-Exact]` | `python3 scripts/search_node_dict.py -q X [--exact] [--max N]` |
| MCP call (root tool) | `mcp_call.ps1 -ToolName list_toolsets` | `python3 scripts/mcp_call.py --tool list_toolsets --out r.json` |
| MCP call (toolset tool) | `mcp_call.ps1 -ToolName X -Toolset Y -ArgumentsJson '{...}'` | `python3 scripts/mcp_call.py --tool X --toolset Y --args-file args.json --out r.json` (args-file avoids shell quoting) |
| Batch Python script | `mcp_call.ps1 -ScriptPath batch.py` | `python3 scripts/mcp_call.py --script batch.py --out r.json` |
| Schema drift guard (offline) | `refresh_schemas.ps1` | `python3 scripts/refresh_schemas.py` |
| Schema drift guard (live) | `refresh_schemas.ps1 -Live` | `python3 scripts/refresh_schemas.py --live` |
| One-click connectivity | (py script, cross-platform) | `python3 scripts/ue_connect.py check` / `launch` / `wait` (mac engine autodetect: /Users/Shared/Epic Games/UE_5.8; pgrep process check) |

Behavior parity verified on Windows (2026-09-11): search output format/rank order
identical, offline cross-check reports identical (0 DRIFT, 1 WARN baseline).
Live-path caveat (both platforms): `--live` is best-effort regex parsing — treat
LIVE-DRIFT as investigate, not gospel.

## 3. macOS workflow examples

```bash
SKILL=~/.codely-cli/skills/unreal-mcp

# node lookup before writing DSL
python3 "$SKILL/scripts/search_node_dict.py" -q SpawnActorfromClass --exact

# probe a palette id (no context needed - G16)
echo '{"graph":{"refPath":"/Game/BP.BP:EventGraph"},"type_id_filter":"GetTotalItems","context_pins":[]}' > /tmp/args.json
python3 "$SKILL/scripts/mcp_call.py" --tool find_node_types \
  --toolset editor_toolset.toolsets.blueprint.BlueprintTools \
  --args-file /tmp/args.json --out /tmp/r.json && cat /tmp/r.json

# batch blueprint edit (Pattern C)
python3 "$SKILL/scripts/mcp_call.py" --script my_batch.py --out /tmp/result.json

# schema drift guard after editing capability docs
python3 "$SKILL/scripts/refresh_schemas.py"
```

## 4. macOS-specific gotchas

- **UE Mac binary path**: the executable lives INSIDE the .app bundle
  (`UnrealEditor.app/Contents/MacOS/UnrealEditor`); passing the bundle to a shell
  does not forward args — call the inner binary directly.
- **Firewall prompt**: first MCP server start on macOS triggers the
  "accept incoming connections" dialog — it blocks headless operation until
  dismissed once (System Settings > Network > Firewall). Equivalent of the Windows
  firewall-modal trap (G10/#18).
- **Case-insensitive FS**: macOS (APFS default) is case-insensitive like Windows —
  readback casing law (G2) unchanged; on case-SENSITIVE volumes (rare), mind asset
  path casing exactly.
- **`python` vs `python3`**: macOS ships `python3`; do NOT assume `python` exists.
- **Chinese-locale editor**: the zh display-name laws (G17, conventions §10) apply
  identically — palette categories localize (工具|Casting|), function-node ids don't.
- **Codely CLI**: same `~/.codely-cli` home; MCP server registration identical;
  UE-before-Codely startup order unchanged (G10/#15).
