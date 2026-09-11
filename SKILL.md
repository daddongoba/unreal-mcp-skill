---
name: unreal-mcp
description: >-
  Unreal Engine MCP (Model Context Protocol) development skill for UE5.8+. Covers: editor control
  (spawn/remove actors, scene & level ops), blueprint authoring via DSL (components, variables,
  events, graphs), collision/trigger/physics interactions, materials, UMG, save systems,
  keyframed animation & ControlRig posing via Sequencer toolsets (~290 tools incl. FBX in/out),
  Niagara VFX, PCG graphs, physics assets, state trees & behavior trees. Also: programmatic
  batch orchestration, PIE control & log forensics, screen automation fallback, verified
  pitfalls/templates/design-conventions knowledge base. Use for ANY UE editor task driven over
  the MCP server (port 8000).
---

# Unreal MCP Development

skill_version: 3.12.0
designed-for: strong-model | weaker-model fallback: references/compatibility.md (baseline test + weak-mode rails)

## Capability Router (v3.0 — read this table FIRST for any task)

| Domain | Status | Read |
|---|---|---|
| physics-collision (triggers/touch/physics) | DEEP-VERIFIED | `references/capabilities/physics-collision.md` |
| anim-sequencer (sequences/keyframes/FBX) | DEEP-VERIFIED | `references/capabilities/anim-sequencer.md` |
| blueprint (DSL/components/variables) | DEEP-VERIFIED | `references/capabilities/blueprint.md` |
| scene-actors (placement/find/levels) | DEEP-VERIFIED | `references/capabilities/scene-actors.md` |
| anim-controlrig (rigs/posing) | DEEP-VERIFIED (visual) | `references/capabilities/anim-controlrig.md` |
| niagara-vfx | DEEP-VERIFIED | `references/capabilities/niagara-vfx.md` |
| pcg | VERIFIED | `references/capabilities/pcg.md` |
| materials-assets | VERIFIED | `references/capabilities/materials-assets.md` |
| skeletal-mesh | VERIFIED | `references/capabilities/skeletal-mesh.md` |
| env-session (startup/modals/rescue/logs) | DEEP-VERIFIED | `references/capabilities/env-session.md` |
| data-ui (save/UMG/tables) | VERIFIED | `references/capabilities/data-ui.md` |

Routing rule: match the task to a domain row → read that doc → design check → build. Ambiguous tasks (e.g. "interactive prop with VFX"): read ALL matched domains' Boundaries sections first. New lessons land in the matching capability-doc (§4 Laws) — SKILL.md only grows for cross-domain laws.

Cross-domain knowledge kept here (applies everywhere): DSL language reference (`references/dsl_syntax.md` R1-R23 + node_types.md), node dictionary (node_dictionary_merged.json), full API dictionary (ue_dict_full.json.gz — local path, -DictPath to override), few_shots.md behavioral cases, capability boundaries overview (`references/toolset_map.md`).

## Self-Maintenance Protocol

**Read this first — it defines how this skill grows.**

### Pitfall accumulation (mandatory, BATCHED) [revised v3.1]

When an MCP/DSL operation fails, gets diagnosed, fixed, and **verified working** (user confirms or PIE test passes):

1. During the session: accumulate the lesson as a DRAFT note (one line each) — do NOT write skill files mid-task.
2. At MILESTONES ONLY (session end, user-paused, or ≥5 lessons queued): batch-commit to `Common Pitfalls`/capability docs using the standard format, update cross-references + version + current-state, ONE backup + ONE repackage.
3. Tags are limited to: `[Collision]` `[Input]` `[Pin]` `[Node]` `[Flow]` `[Other]`
4. Only commit **after verification succeeds** — unverified guesses do not belong in Pitfalls.

### Knowledge confidence levels (mandatory tagging)

Every factual entry (pitfall/rule/template) carries one of:
- `[VERIFIED <date> UE<ver>-<lang>]` — PIE/user-confirmed. Highest trust.
- `[UNVERIFIED]` — theoretically sound, not yet tested. Expect failures; verify before relying.
- `[DOC]` — transcribed from docs/dictionary, not battle-tested.

Rules: pitfalls require the full diagnose→fix→verified loop before entry. Template library accepts `[UNVERIFIED]` only when the README index marks it as such. When practice contradicts a `[VERIFIED]` entry twice, mark it `[STALE]` and fix it.

### Size limits (byte-budgeted, NOT entry-counted)

The Pitfalls section carries a **12KB budget** (≈25% of SKILL.md's activation cost). When exceeded:
1. FIRST compress losslessly: merge related pitfalls into Law Groups (G-sections) — one law, many incidents, original numbers cited inline.
2. If still over budget: archive the LOWEST value-density entries (frequency × severity) — NOT the oldest — to `references/pitfalls_archive.md`.
Entry count is a diagnostic, not a rule. SKILL.md keeps only laws and pointers.

**Current state**: v3.12.0 (2026-09-11) — Project-open intake law added to One-Click Connect: user gives project link/name → resolve path (name-only = scan+match, ambiguous → candidate list) → ONE confirmation round carrying the full pre-flight (path, autodetected engine, plugin audit, UE-already-running state; the message doubles as --fix-plugins consent when plugins are listed missing) → only then `ue_connect.py launch` + `wait` (never raw-shell spawn). Prior: v3.11.0 One-Click Connect (`scripts/ue_connect.py` check/launch/wait/all; E2E-verified: real ghost python process on 8000 caught → killed → launch → wait 289s → 67 toolsets → reconnect 1s → exit 0; all-mode timeout bug fixed in-run); v3.10.0 macOS twin (py script twins + platform-macos.md §0 platform-detection dispatch); v3.9.0 TestT1 forensics case + conventions §6-§10; v3.8.0 G17/R27; v3.7.0 G16/R24-26; v3.6 dict tooling + hard rail. Architecture: 11 capability docs + router (v3.0).

**Numbering note**: templates/archives may cite external IDs (P40-P49 = history/UE_Test_Achievements.md test-log IDs). Authoritative pitfall IDs are the ones in this file only; on conflict trust this file.

### Template library growth

When a DSL workflow is fully verified in PIE:
1. Save it to `references/templates/<name>.txt` using the standard template structure (see `templates/README.md`).
2. Update `templates/README.md` index.
3. Unverified DSL never enters the template library unmarked.

### Cross-references

- Pitfalls record the **trap** (what breaks); `references/dsl_syntax.md` records the **law** (what works). Update both when a new lesson lands.
- After UE version upgrades, review dated entries and prune stale ones.

### Freshness matrix — what an environment change invalidates

| Change | Re-review scope |
|--------|-----------------|
| UE minor upgrade (5.8→5.9) | node type_ids, DSL syntax rules, all templates |
| Editor language switch (EN↔CN) | node_types.md, all DSL templates, encoding rules |
| Toolsets plugins added/removed | Toolset Reference table, affected templates |
| Codely CLI upgrade | startup-order rule (Pitfall #15), Pattern 0 vs A/B priority |

### Backup before install [revised v3.1]

Before each re-package/install, copy the skill folder to `~/.codely-cli/skills/_backup/unreal-mcp_<date>/` (keep latest 2, delete older). Rollback = restore folder + `/skills reload`. Backups happen at BATCH-COMMIT milestones only (see Pitfall accumulation), not per-lesson.

## Environment Dependency (the one non-obvious invariant)

`[VERIFIED 2026-08-23 UE5.8-EN]` **Codely must start AFTER UE.** Codely discovers MCP tools only at its own startup — if port 8000 isn't up then, native tools (`list_toolsets`/`describe_toolset`/`call_tool`) never appear for the whole session even after UE comes online.

- Correct order: UE fully loaded → port 8000 answers 200 → then start Codely.
- If session already lacks native tools: fall back to PowerShell Patterns A/B (below) without ceremony, or ask user to restart Codely.
- If a request mentions UE-specific concepts but this skill isn't active, mention it to the user once.

## One-Click Connect (novice connectivity mode, v3.11)

Connectivity requests ("连不上/连UE/为什么工具不可用") or novice first-run → `python3 scripts/ue_connect.py check` FIRST (read-only diagnosis: UE process, port 8000 vs real /mcp endpoint, NON-UE port listeners, .uproject plugin audit; state cached at ~/.codely-cli/ue_connect_state.json so later runs need no args). Verdicts drive the fix:
- UE not running → `launch` (detached spawn with -ModelContextProtocolStartServer, engine autodetected, returns immediately) → `wait` (30s progress prints, ~4.5 min first load, full handshake + toolset count on success). Run launch and wait as SEPARATE shell calls (tree-kill lesson).
- Plugins missing → ask user (Danger Gate #3: .uproject edit) → `launch --fix-plugins` (writes .uproject.bak first).
- Port held by non-UE listener (initialize→404) → report PID-hunting commands; kill it, then launch. `[VERIFIED 2026-09-11: caught a real ghost python process squatting on 8000]`
- UE running but /mcp dead → console `ModelContextProtocol.StartServer` or relaunch.
- Session-side (agent checks own tool list): native call_tool missing = Codely started before UE → mcp_call.py fallback keeps everything working immediately; recommend Codely restart for native tools.
E2E-verified 2026-09-11 on Windows: ghost-port diagnosis → launch → wait 289s → 67 toolsets → all-mode reconnect (1s) → check exit 0.

**Project-open intake (both platforms, v3.12)**: when the user provides a project link/name to open (fresh install onboarding or any "帮我打开项目" request):
1. Resolve the .uproject path (user-given path; or if only a name is given, scan plausible roots — Desktop/Documents/common project dirs — and match `<Name>/<Name>.uproject`; ambiguous matches → list candidates and ask).
2. **Pre-flight + confirm in ONE round**: present the resolved details for explicit confirmation — full .uproject path, engine to be used (autodetected root), plugin audit result (5 required present / which missing → will need --fix-plugins consent), and whether UE is already running (already running + different project = close-first decision belongs to the user, Danger Gate #1). NEVER launch before this confirmation — wrong-project launches cost a 4.5-min load cycle.
3. Confirmed → run `ue_connect.py launch [--fix-plugins]` (detached, flag included) → `wait` (separate shell call) → report toolset count. Never spawn UE via raw shell (tree-kill lesson).
The confirmation message doubles as the plugin-fix consent when missing plugins are listed in it.

## Requirement De-Risking (v3.2)

遇到不明白或需要补充的，主动提问，构建前一轮问清（多问题打包、附默认值；反转成本<5调的歧义直接按最优猜测做并声明）。
## Teaching Mode (v3.5)

Trigger: user says "讲解模式/教学模式/新手模式" OR user profile is novice. Exit: "直接做/别解释".
When active, follow `references/teaching.md`: narrate each build step with its law (板块1 边建边讲), deliver risk-forecast with every feature (板块2), upgrade novice symptom-reports into diagnostic questions then execute (板块3 话术库), answer concept questions via 板块4 速查. Narration hangs on actions — never a separate lecture. Q-level tasks: only 板块2 risk forecast; D-level: all four.
Non-teaching sessions: adaptive interaction stays model-native (one-line anchor: match explanation density to user expertise; profile persists via global memory).
## Verification Tiering (v3.1) — protocol cost control

Task classes (judge at intake): **Q-level** (quick: expected <15 tool calls OR template direct-hit) vs **D-level** (deep: everything else).
- Q-level: router glance → template adapt → build → compile is the MINIMUM verification (compile-pass ≠ correct wiring). Extra readbacks only on first-of-kind writes.
- D-level: full protocol (design check → domain doc → first-write verify → milestone commit).
- Readback tiering (applies to both): collision profiles/struct writes — verify FIRST write of a kind per session (per component class), skip repeats of the same verified pattern; DSL readback — always verify after semantic rewrites (G2), skip after template-verbatim writes.
- **Hard rail (v3.6, 2026-08-30): "template-verbatim" means ZERO modification** — DSL identical AND same variables/components/params as the verified template. ANY deviation (renamed var, different pin value, extra node, different component) makes it a semantic rewrite → G2 readback is MANDATORY (find_nodes + readback verify presence AND absence). "ADAPT don't copy" implies adaptation is the norm — so in practice nearly every DSL write needs readback. Compile-pass alone never proves the graph.


## Visual-Capture Gate (v3.4) — screenshot BEFORE asking "what will this image change?"

One capture = 2-4MB base64 = 50-100x a normal tool call's token cost. Never screenshot as a thinking placeholder.

- **R1 Data first**: if a read tool answers the question, NO capture (actor positions=find_actors, property state=get_properties, what happened=GetLogEntries).
- **R2 Visual-exclusive domain**: capture ONLY for facts only eyes can decide — render results, pose deformation, modal dialogs, UI layout.
- **R3 No re-capture of known state**: if this session already imaged the same state, reuse it (f0 shot exists -> only capture f60 for the comparison).
- **R4 Diagnosis order**: capture is the LAST diagnostic step, not the first — log forensics (G5) first; capture only what logs cannot answer.
- Budget intuition: 1-3 captures per task is normal; >5 means the approach (not the picture) is wrong.
## Danger Gates

Three irreversible actions are RED — require the user to explicitly request them **in the current message** (earlier authorization doesn't carry over):

1. Closing/killing the UE editor process (loses unsaved work).
2. Deleting pre-existing assets/actors the user placed (SceneTools.remove_from_scene, AssetTools.delete on non-session-created objects).
3. Modifying project files (.uproject, Build.cs, source files).

GREEN (no gate): objects/assets created earlier in the same session by the agent, all queries, screenshots, DSL writes, node creation, PIE start/stop, blueprint compile.

**Data boundary:** never send project source/assets to external services; TJGenerators uploads only user-provided/generated content.

## Resource Lifecycle

| Artifact | Location | Cleanup |
|----------|----------|---------|
| Downloaded source files (`C:\UE_Import\*`) | system temp | delete right after import step-5 verification (keep on failure for diagnosis) |
| `Saved/import_*.py` | project | keep latest 3, delete older on next import |
| `Saved/pytest*.py`, snapshot dumps | session dirs | delete when user says "clean up" |
| `verify_*.png` thumbnails | UE_Import | delete after viewing |

Natural cleanup points: immediately after successful import verification; on explicit "清理/clean up" request. No session-end hooks exist — never promise one.

## Prerequisites

- UE5.8+ running with "Unreal MCP" (ModelContextProtocol) plugin enabled in .uproject
- MCP Server listening on port 8000 (see "Launching UE" below)
- Codely CLI settings.json configured with `unreal-mcp` MCP server entry

### Required Plugins in .uproject

5-plugin JSON block + core/minimal variants: see 
eferences/capabilities/env-session.md §1 and 
eferences/toolset_map.md. All engine built-ins.

### Launching UE

**CRITICAL ORDER: UE must be fully running BEFORE Codely CLI starts.** Codely discovers MCP tools at startup only — if port 8000 isn't ready, tools never register (verified 2026-08-23: UE online first → all toolsets become native tools; Codely first without UE → tools never appear).

Correct sequence:
1. Start UE (command below), wait for full load
2. Verify port 8000 responds (see "Verifying Connection" below)
3. THEN start Codely CLI → `list_toolsets` / `describe_toolset` / `call_tool` become native tools

If Codely is already running but UE was not up at its startup: restart Codely after UE is ready.

Always launch UE Editor with `-ModelContextProtocolStartServer` so the MCP HTTP server auto-starts on port 8000 regardless of project config:

```
E:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe "<ProjectPath>\Project.uproject" -ModelContextProtocolStartServer
```

This bypasses the plugin's default `bAutoStartServer = false`.

If UE is already running without the flag, start the server from the Output Log console:
```
ModelContextProtocol.StartServer
```
Or enable `Edit > Editor Preferences > Model Context Protocol > Auto Start Server` (per-project setting).

### Verifying Connection

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/mcp" -Method POST -Body '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' -ContentType "application/json" -UseBasicParsing -TimeoutSec 5
```
Returns HTTP 200 with `"protocolVersion": "2024-11-05"` if connected.

### Verifying Toolsets

After connecting, call `list_toolsets` to verify available toolsets. With AllToolsets enabled, expect 30+ toolsets. With minimal setup (no AllToolsets), expect 18+.

If toolsets are missing, check that `.uproject` has `ToolsetRegistry`, `EditorToolset`, and `PythonScriptPlugin` enabled. After adding plugins, restart UE editor.

## MCP Server API

The UE MCP server (Epic's built-in `ModelContextProtocol` plugin) exposes 3 top-level tools:
- `list_toolsets` — list all available toolsets (18+)
- `describe_toolset` — get detailed tool list with input schemas
- `call_tool` — call a tool by name, optionally within a toolset

## Calling Patterns

### Pattern 0: Native tool call (PREFERRED — use when tools are registered)

When Codely was started after UE (correct order), `call_tool` is a native tool. Use it directly — no PowerShell, no HTTP, no session management:

```
Tool: call_tool
Arguments: {
  "tool_name": "find_node_types",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {"graph": {"refPath": "/Game/BP.BP:EventGraph"}, "type_id_filter": "MakeVector", "context_pins": []}
}
```

Also native: `list_toolsets` and `describe_toolset`.

If these tools are NOT in the tool list, Codely started before UE — either restart Codely, or fall back to Patterns A/B below.

### Pattern A/B (fallback PowerShell)"
Both fallback scripts live in scripts/mcp_call.ps1 (encoding-safe caller). Use Pattern 0 when native tools registered; A/B only when session started before UE.

### Pattern C: Python script via ProgrammaticToolset (for multi-step blueprint editing)

Write a `.py` file, send via `scripts/mcp_call.ps1 -ScriptPath "script.py"`. Or use `scripts/bp_template.py` as starting point.

**For Chinese-locale UE**: Must write .py to file and use `mcp_call.ps1` to avoid encoding corruption. See "Encoding Notes" below.

**For English-locale UE**: Can inline Python directly in PowerShell — no encoding issues.

## ProgrammaticToolset Python Template

Copy scripts/bp_template.py (v2: rv/as_ref/set_props fallback/find_component/... helpers), modify run(), send via mcp_call.ps1. Sandbox: json/math/re/time/copy/datetime only; aborts on first tool error; run() must return dict.

## Blueprint Editing Workflow

0. Design check (router/domain docs). 1. create →2. CDO components →3. variables →3b. **node lookup**: any type_id/pin not template-verified → `scripts/search_node_dict.ps1 -Query <name>` (offline, covers Actor/Component members + special K2Nodes in extras) →4. DSL (MERGES —clean stale nodes, G2) →5. compile →6. **verify_bp.py** (scripts/, edit BP_PATH+expected config, run via mcp_call.ps1, all-PASS checklist) →7. save →8. re-place instances.
Idempotency guards table + full step details: `references/capabilities/blueprint.md` §2/§3.

## Scene Operations

spawn/find/remove/trace/get_current_level params: 
eferences/capabilities/scene-actors.md 搂3.

## Common Pitfalls (Law Groups)

Format: `G. [Tag] Law`: symptom → fix. Grouped by semantic law (v2.11 refactor) — original pitfall numbers cited in parens for cross-reference with templates/archive/history; do NOT renumber. Incidents #1-#4 predate this format (encoded as dsl_syntax rules R3/R4/R6 + Idempotency table — see `references/pitfalls_archive.md` v2.3.1 section). Full per-incident detail: `references/history/UE_Test_Achievements.md`.

**Domain laws G1/G4 (physics-collision) and sequencer specifics now live in `references/capabilities/*.md` §4 — the entries below are kept as cross-reference stubs during the v2.14 pilot.**

### G1 [Collision] Overlap & trigger semantics (#10 #41 #45 #48 #51) → MOVED to capabilities/physics-collision.md §4

### G4 [Collision] Physics activation chain (#7 #8 #35 #38 #40) → MOVED to capabilities/physics-collision.md §4

### G2 [Node] Graph rewrite & id round-trip asymmetries (#49 #50 #33)
`write_graph_dsl` MERGES, never replaces — after any semantic rewrite, `find_nodes(title=...)` + `delete_node` stale entry points/orphans, then readback-verify absence AND presence (#49). Bool variable nodes: INPUT uses display name (`GetArmed`), READBACK prints internal (`GetbArmed`) — never feed readback ids back verbatim (#50). Duplicate nodes accumulate across failed retries — audit + dedupe before wiring (#33). READBACK CASING (2026-09-06, TestT1 case): readback prints display-styled casing (`AddToViewport`) while the registered id is `AddtoViewport` — readback comparisons must be case-insensitive; stored node type_id may also drop the `Class|` prefix entirely (`|UpdateCount`) — match by trailing function name, not full id.

### G3 [Flow] Save/persist is UNTRUSTWORTHY — verify on disk, TIERED (#19 #43 #46) [revised v3.1]
`save_assets`/`duplicate` return values LIE — but only for WorldPartition/level saves (2 incidents, both .umap). TIERING: `.umap`/WP-level saves and `duplicate` → ALWAYS disk-verify; regular asset saves (.uasset BPs/materials/sequences) → spot-check first save of a session, then trust `returnValue:true`. WorldPartition `/Temp` levels: `load_level` blocked; `duplicate` unreliable as a save (HLOD private refs); real persistence = manual Save Level As or autosaves (#43). New assets are NOT auto-saved — `save_assets` after every batch (#19).

### G5 [Input] Player interaction reality (#9 #52)
Flying DefaultPawn CANNOT push physics bodies — displacement triggers are unreachable; trigger on PROXIMITY: `Game|GetPlayerPawn` + `Transformation|GetDistanceTo(:OtherActor tgt)` < ~250 (#52). Non-Pawn actors ignore keyboard until `Input|EnableInput` + GetPlayerController in BeginPlay (#9, archived). Log forensics: `GetLogEntries(category:"", pattern:...)` — prints carry per-UAID identity + timestamps + build fingerprints (#52).

### G6 [Node] DSL structure laws (#12 #14 #30 #48b)
Top level = event/fn only; everything else nests inside (#30). Arithmetic binary-only, nest or bind (#14, R3). Input-key events must be `create_node`+Python wired, not DSL events (#12, R2). For/if bodies: keep to SetVar/PrintString only — pure nodes get hoisted & mis-wired (see G1 #48).

### G7 [Pin] Name & path formats (#5 #13 #27 #28 #29)
Path types differ: asset `BP.BP` / graph `BP.BP:EventGraph` / CDO `Default__BP_C` / component `BP_C:Comp_GEN_VARIABLE` — match to the tool (#5). SpawnActor Class pin wants `_C` (#13). Bool var nodes drop the b-prefix in input ids (#27, G2). Cast outputs have spaces (`AsBP Grid Game Mode`); wildcard Object needs typed source (#28). Cross-BP member id: `Class|<NameNoUnderscores>|<Func>` (#29).

### G8 [Node] Discovery-before-use, TIERED (#11 #26 R8) [revised v3.1]
Template-verified type_ids (those already cited in templates/dsl_syntax/node_types) are SAFE to use directly — no probe needed. Only genuinely unknown nodes require `find_node_types` / `get_node_type_pins` first. Per-toolset schemas: if calling ≥3 different tools of one toolset, ONE `describe_toolset` beats error-iterating each; for single calls the error-iterate loop (G12) is faster. Baked shortcuts: `references/tool_schemas.md` + `scripts/search_node_dict.ps1` (offline node/pin lookup: merged dict + verified extras; the raw `node_dictionary_merged.json` is a 734KB single-line JSON — unreadable via read_file, ONLY searchable via the script).

### G9 [Flow] Instance/template split (#25 #34 #47 #53)
Placed instances do NOT pick up template edits — re-place after compile+save (stale PIE bindings) (#25). WorldSettings GameMode override via set_properties (#34, archived). Level blueprints are lazily created (open once in editor before tools can see them); `LS_*.uasset` = LevelSequence, NOT a level; prefer cross-BP calls / GameMode BP over level blueprints (#47). Instance component struct props apply FIRST SCALAR ONLY — set single-leaf structs per call, or re-place from template (#53). Object-reference setting: CDO TEMPLATE component refs ARE settable (SkeletalMesh→component worked); RUNTIME-INSTANCE object vars and ASSET-level refs (SkeletalMesh→Skeleton) are NOT (2026-08-29) — fix at the right layer or re-import.

### G10 [Other] Environment & session traps (#4 #6 #15 #16 #18 #22)
Scripts abort on first tool error (try/except does NOT catch) — keep idempotent, results[] lists, risky calls last (#4-family, active #42). UE must be up before Codely starts or MCP tools never register (#15). write_file needs absolute paths into Content/Saved (#16). Native dialogs (firewall/Restore Packages) block headlessly — see screen_control.md (#18). SlateInspector recovers via Observe cycle + 5s wait (#22). Console/OutputLog drawer + LiveCoding specifics: archived #17 #21 #23 #39; Sequencer/Niagara/SaveGame specifics: archived #31 #32 #36 #37 — `references/pitfalls_archive.md`.

### G11 [Flow] Scene placement reality (#20 #24 #44)
OpenWorld terrain buries actors — `trace_world` BEFORE placing, keep above ground (#24). PIE instances live at `/Memory/UEDPIE_N_` paths — use those for live reads (#20). Read PlayerStart transform first; place demos 800-1200 units along its facing; FocusOnActors after (#44).

### G12 [Other] Cross-toolset survey laws (2026-08-29 capability survey)
**Param-name anarchy is the norm**: every toolset uses different conventions (`folder_path+asset_name` vs `package_path+asset_name` vs `path` vs `assetPath+assetName` camelCase vs `mesh` ref) — and **error messages self-document**: missing-param errors name the exact required param, type errors name the expected class. Iterate: send minimal args → read error → add the named param → repeat. 3-4 rounds reaches a working call; do NOT describe_toolset-guess first for simple calls. Class-typed params (track_type/section_type/templateSystem/component_type) want OBJECT paths with dot suffix (`/X/Y.Z`), not asset paths. World-typed params want the World object (`/Game/L.L`), NOT `:PersistentLevel`. Actor-typed params want LIVE actor refs (find_actors fresh — stale UAIDs fail "not valid Actor for TransientPythonProperty"). `[VERIFIED 2026-08-29 UE5.8-EN — 17-round systematic survey]`

### G13 [Other] UE modals dismiss via PostMessage, NOT synthetic clicks; AnimBP create refused at tool layer (2026-08-29)
UE native modal Message boxes ignore simulated cursor events (SetCursorPos+mouse_event failed twice with verified coords); **PostMessage WM_CLOSE(0x0010) to `FindWindow(NULL,"Message")` works instantly**; MCP resumes in ~5-10s — poll initialize, then save_assets([])+disk-verify mid-flight assets (all survived). Full procedure: `references/screen_control.md`. AnimBP create confirmed dead: engine REFUSES outright ("Cannot create a blueprint based on the class 'AnimBlueprint'") — tool-layer rejection, not just a modal. `[VERIFIED 2026-08-29 UE5.8-EN — remote rescue performed for user]`

### G14 [Flow] Level Instance coordinate-system separation (2026-08-29, user-reported incident)

A level instance = a SHELL actor in the parent level + its content living in a sub-world. Coordinate tools (set_actor_transform/trace_world/find_actors) do NOT distinguish the two worlds. Moving an instance's PLACEMENT must target the SHELL; find_actors can return refs INSIDE the instance world instead — then set_actor_transform silently rearranges the instance's INTERNAL actors while the placement never changes (tool returns success; error is invisible without visual check).

- Fix (placement tasks): list ALL refs matching the instance name FIRST; pick the one whose refPath does NOT contain the instance-world prefix (the shell). Danger signal: refPath containing a LevelInstanceActor/world-inner fragment in a placement task = wrong target.
- Fix (content tasks): explicitly edit_level_instance into the sub-world, operate on internal refs, exit.
- After placement: R2 visual capture (only eyes confirm placement changed) — per Visual-Capture Gate, this IS the visual-exclusive domain.
- User wording tip: requests saying "实例在主关卡中的位置" mean the SHELL; ask/confirm if ambiguous which world is meant.
### G15 [Node] Graph hygiene: incremental edit tiers + orphan sweep (2026-08-29, dup-incident)

Repeated DSL writes accumulate duplicate event entries + orphan chains (observed: 7 dead K2Node_Event entries, counter at _281 for 87 live nodes). write_graph_dsl MERGES (G2) and failed-retry halves also leave bodies (#33) — AND entry-deletion alone does not remove their call-chain bodies.

- Edit tiers: <3 node changes → node surgery (find_nodes + set_pin_value/connect_pins/delete_node, zero residue); logic-branch changes → read_graph_dsl, edit text, write back, then IMMEDIATELY sweep; architecture changes → full rebuild (delete entries, fresh write).
- Orphan sweep (verified method): find entry nodes → BFS get_connected_subgraph to collect live set → delete(all_nodes − live_set) → verify live==total. Zero-orphan result achievable (87/87 verified).
- NEW TRAP: read_graph_dsl/find_nodes can return EMPTY after compile+save sequences (editor graph cache). Recover: reopen via OpenEditorForAsset, or re-compile; get_node_infos/get_connected_subgraph keep working as fallback read channels.
- Duplicate diagnosis signature: multiple K2Node_Event_* with wired-pins=0 in get_node_infos.

### G16 [Node] Cross-BP node creation & the dictionary-namespace trap (2026-09-06, user-reported mystery resolved)
User report "create_node cannot create cross-BP nodes (declaring_class either), Utilities|ToString(Integer) does not exist, write_graph_dsl is the only path" — LIVE-TESTED, all three FALSE on UE5.8: (a) create_node DOES create cross-BP nodes with `Class\|<NameNoUnderscores>\|<Func>` — works in Actor BP AND WBP graphs, against UNCOMPILED targets, no declaring_class needed (and declaring_class cannot rescue bare function names); (b) ToString works at FULL path `Utilities\|String\|ToString(Integer)` — the reported form was missing the String segment; (c) BOTH create_node and write_graph_dsl construct cross-BP nodes (DSL preferred: wires in one shot). REAL ROOT CAUSE = THE NAMESPACE TRAP: node_dictionary display_name/category are PALETTE names, NOT tool type_ids (`float * float`→`Utilities\|Operators\|Multiply`; `Flow Control\|Branch`→`Utilities\|FlowControl\|Branch`; `To String (Integer)`→`Utilities\|String\|ToString(Integer)`); display forms FAIL in create_node — verify dictionary-sourced ids with find_node_types first. Same battery also verified: function return type needs add_function_param(input_param=false) (DSL (return x) does NOT infer it — call nodes show no ReturnValue pin otherwise); multi-param events = ONE parenthesized list `(MyGeometry InDeltaTime)`; widget events need `AddEvent\|UserInterface\|` prefix (bare EventTick FAILS in WBP graphs); cross-BP :self target must be wired unless caller IS the target class (unwired → compile error naming the target class). `[VERIFIED 2026-09-06 UE5.8-EN — PIE end-to-end: spawned→called→printed "42"]`

### G17 [Node] Cast-family trap: inverted underscore rule + locale + the GAOC bypass (2026-09-06, user finding validated+extended)
User reported: DSL failed on `Utilities|Casting|...` because their (Chinese-locale) palette shows `工具|Casting|...`, and discovered GAOC's ActorClass pin TYPES its output so no Cast is needed. LIVE-TESTED (EN locale) REFINED THE ROOT CAUSE: the id form was ALSO wrong — Cast node ids KEEP underscores (`Utilities\|Casting\|CastToBP_Inventory` works; stripped `CastToBPInventory` fails "does not exist" even in English, live-verified), the OPPOSITE of cross-BP call rule R12. Project-BP casts are NOT in the palette list (engine-class casts only, 5964 nodes) — only find_node_types with the underscore-kept name finds them. Cast category likely localizes in zh editors while function-node categories (Actor\|, Game\|...) keep untranslated metadata — EITHER error kills Cast, and the two rules (R12 strip vs R15 keep) being opposite makes Cast the #1 footgun. **PATTERN: prefer typed-source over Cast** (R27): generic nodes with Class pins output the specialized type — `(Actor\|GetAllActorsOfClass :ActorClass "BP_Inventory_C")` → foreach elem feeds `Class\|BPInventory\|GetTotalItems :self elem` directly. PIE-verified: printed 42 per found instance, zero Cast nodes. Use Cast only when no typed source exists (GameMode→Door chains), and remember its underscore-kept id. `[VERIFIED 2026-09-06 UE5.8-EN — CastToBP_Inventory create + GAOC no-cast chain both compiled & PIE'd]`

## Encoding Notes

Current environment is **English locale** (fixed 2026-08-22) — no encoding constraints; `ConvertTo-Json`, inline Python, and DSL all safe.

If locale ever reverts to Chinese: see `scripts/mcp_call.ps1` (UTF-8-safe HTTP), use `\uXXXX` escapes in .py, never `ConvertTo-Json`/inline Chinese — full rules in `references/node_types.md` mapping table.

## Reference Index

| Need | Read |
|---|---|
| Node type_ids quick map / DSL grammar R1-R23 / error-fix table | `references/node_types.md` + `references/dsl_syntax.md` |
| Node/pin lookup BEFORE writing DSL | `scripts/search_node_dict.ps1 -Query <name>` [-Exact] — searches merged dict (1665 library nodes) + `references/node_dict_extras.json` (PIE-verified Actor/Component members, special K2Nodes); offline, cheaper than find_node_types |
| Full UE API dict (346K entries) | `ue_dict_full.json.gz` via `scripts/search_ue_dict.ps1` (-DictPath overrides local path) |
| Tool param signatures | capability docs §3 + `references/tool_schemas.md` (cache; drift-guard via `scripts/refresh_schemas.ps1` — offline cross-check runs WITHOUT UE; `-Live` diffs live server) |
| Design conventions (component/event selection) | `references/ue_conventions.md` + capability docs §2 |
| Behavioral cases (ask/decline/gates/template-hit) | `references/few_shots.md` |
| Real-world failure case (scene-scan → cross-BP → widget chain; TestT1 inventory forensics 2026-09-06: dead-cast residue, GAOC class=0, same-name call drift, CreateWidget Class=0, Tick-refresh antipattern, readback casing) | `references/history/case_testT1_inventory.md` |
| Native-window rescue procedures | `references/screen_control.md` |
| macOS platform twin (env diffs, .app inner-binary launch, py script twins, firewall gotcha) | `references/platform-macos.md` |
| One-click UE connectivity (check/launch/wait/all; novice mode) | `scripts/ue_connect.py` (cross-platform, state-cached; see One-Click Connect section) |
| Verified workflow templates | `references/templates/README.md` (17, ADAPT don't copy) |
## Toolset Reference

Full 67-toolset landscape incl. core/extended tables, Niagara/animation families, and third-party extensions (VibeUE): 
eferences/toolset_map.md (2026-08-29 survey-verified). Per-domain tool params: capability docs §3.

**Capability boundaries (verified 2026-08-28, 67 toolsets live)**: Landscape sculpt/paint = NO toolset (VibeUE adds it); vertex-level mesh Modeling Mode = NO; IK Retargeter (skeleton retarget) = NO (component-level SkeletalMeshAsset/AnimClass swap auto-rebinds compatible skeletons); AnimBP state-machine graphs = no dedicated toolset (AnimBP EventGraph via BlueprintTools `[UNVERIFIED]`; state/blend params settable via ObjectTools). Everything else above is directly callable.

## When to Use What

| Task | Approach | Why |
|------|----------|-----|
| Any tool call (native `call_tool` in tool list) | **Pattern 0 first** | 1 call, no HTTP/PowerShell overhead |
| Native tools absent (Codely started before UE) | Pattern A/B fallback | session didn't register MCP tools |
| Create blueprint with logic | Pattern C (.py file) | Batch in single round-trip |
| Complex blueprint (10+ nodes) | .py via ProgrammaticToolset | Batch, avoids multiple round-trips |
| Discover unknown node types | `find_node_types` at runtime | Dynamic, no hardcoded type_ids |
| Check pin names / type_id BEFORE DSL write | `scripts/search_node_dict.ps1 -Query <name>` | Offline dict lookup, avoids blind retry loops |
