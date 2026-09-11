# Pitfalls Archive

Overflow storage for SKILL.md pitfalls. SKILL.md v2.11 groups ACTIVE pitfalls into Law Groups (G1-G11);
this file keeps full per-incident detail for ARCHIVED entries (numbers stable, cross-referenced by
templates/history — do NOT renumber). Active incidents also cite their original numbers inside G-sections.

## Archived 2026-08-28 (v2.10.1 hygiene pass — 39→30 active, per Self-Maintenance size limits)

17. **[Flow] Output Log drawer auto-collapses; console input is inside it**: The bottom-bar "Output Log" button opens a drawer whose console textbox (`[focused]`, bottom ~y=978) only exists while open; delayed snapshots see nothing. — Fix: Click "Output Log" → Snapshot immediately → Type into `[focused]` textbox with `submit=true`; verify via `GetLogEntries` (needs `category:""` empty, NOT default "LogsToolset").

21. **[Node] Slate Snapshot default depth hides console**: Output Log drawer controls need maxDepth=45 (239 lines), not 30 (116). — Fix: use 45 when hunting textboxes/buttons in drawers.

23. **[Other] LiveCoding output goes to its own console window**: editor log stops at "Starting Live Coding compile"; results (patch_0.dll etc.) appear in `Binaries/Win64/UnrealEditor-<Mod>.patch_N.*` timestamps. Patch generated ≠ hot-applied — verify behavior, not just files.

31. **[Node] Sequencer track has no sections by default**: `add_track_to_sequence` returns a track with zero sections; `add_key_float` needs a section ref. — Fix: `add_section(track, section_class)` then `getsections` → key on section[0]. Full chain: track → section → `add_key_float(section, channel_name="Location.X", frame, value, interpolation="Auto")`.

32. **[Flow] Niagara stack refs need full 6-field objects**: SetEmitterData/AddModule take a `NiagaraExt_StackItemReference` with required fields (system, emitterName, scriptName, moduleName, rendererIndex, inputNameStack) — empty strings/-1/[] for unused. `emitterData.propertyValues` is a JSON **string** with PascalCase fields. — Fix: build the full struct in ProgrammaticToolset Python (PowerShell escaping mangles nested JSON-in-JSON).

34. **[Flow] WorldSettings GameMode override works via set_properties**: find WorldSettings actor → `DefaultGameMode:"/Game/.../BP_GM.BP_GM_C"` → PIE spawns the GM as `/Temp/UEDPIE_0_...BP_GM_C_0`. Verify in PIE via `find_actors(name="GameMode")`.

36. **[Other] SaveGame base class instantiate-but-fails (P47, 2026-08-24)**: `CreateSaveGameObject("/Script/Engine.SaveGame")` creates an object but `SaveGameToSlot` returns false, no .sav written — same family as DataAsset (P33): engine base classes aren't valid save subjects. — Fix: BP subclass first (`create` asset_type=/Script/Engine.SaveGame → compile → save), then `"/Game/.../BP_SaveData.BP_SaveData_C"`. Verified: SaveOK=true + TestSlot.sav 2014B. Full chain: templates/save_load.txt.

37. **[Node] SaveGame category is `SaveGame|` not `Game|` + inconsistent conversion pins**: CreateSaveGameObject/SaveGametoSlot/LoadGamefromSlot/DoesSaveGameExist live under `SaveGame|`. Conversion pins vary: ToString(Boolean)=`InBool`, ToString(Integer)=`InInt`, IsValid=`InputObject`. — Fix: find_node_types first; get_node_type_pins for any conversion node.

39. **[Other] LiveCoding: hotkey trigger works, native-class hot-apply does NOT (v2.5 final)**: `Ctrl+Alt+F11` via SendKeys after SetForegroundWindow reliably triggers LC → "Live coding succeeded" + patch_N. BUT changed native behavior (Tick 4x→8x) invisible to existing AND newly-spawned instances until editor restart — patch loads but UClass native rewiring needs restart. — Fix: LC only for iterating NEW code paths; verifying changed native behavior = close UE → full build → restart (cpp_workflow.txt).

## Archived 2026-08-24 (v2.3.1 hygiene pass — superseded by dsl_syntax rules / Prerequisites section / templates)

1. **[Pin] Bool→Float rejected**: Operator nodes (Add/Subtract/Multiply) have wildcard pins that reject bool. — Fix: insert `SelectFloat` (condition=bool, A=1.0, B=0.0) between bool output and operator input. *(→ encoded as R4)*

2. **[Input] IsInputKeyDown needs PlayerController**: Its `self` pin expects a PlayerController, not an Actor. — Fix: create `GetPlayerController` node, connect output to each IsInputKeyDown's `self` pin. *(→ encoded as R6)*

3. **[Pin] Duplicate connection errors**: Connecting an already-connected pin fails. — Fix: always check `not pin["connected_pins"]` before `connect_pins`. *(→ encoded in Idempotency rules table)*

4. **[Flow] Compile errors abort scripts**: `compile_blueprint` raises on errors, killing the whole Python script. — Fix: put compilation last; wrap in try/except when experimenting. *(→ encoded in Idempotency conventions)*

6. **[Other] MCP Server not listening**: `ModelContextProtocol` plugin defaults `bAutoStartServer=false`; port 8000 unreachable. — Fix: launch UE with `-ModelContextProtocolStartServer`, or run `ModelContextProtocol.StartServer` in Output Log. *(→ encoded in Prerequisites/Launching UE section)*

11. **[Node] MakeTransform type_id**: It's `Math|Transform|MakeTransform` (not `Math|Transformation|...`). — Fix: run `find_node_types` before hardcoding any type_id. *(→ encoded as R8)*

14. **[Pin] DSL arithmetic takes exactly 2 args**: `(* a b c)` fails. — Fix: nest `(* a (* b c))` or `(bind mid (* a b))` then reuse. *(→ encoded as R3)*

## Archived 2026-08-28 (v2.6 hygiene pass — keep SKILL.md ≤30 entries; superseded by #40 / basic patterns)

5. **[Node] Graph/CDO/Component path formats differ**: asset `/Game/Folder/BP.BP`; graph `/Game/Folder/BP.BP:EventGraph`; CDO `/Game/Folder/BP.Default__BP_C`; component `/Game/Folder/BP.BP_C:ComponentName_GEN_VARIABLE`. — Fix: match the path type to the tool's expected parameter.

7. **[Collision] Root Component determines Sweep**: `AddActorWorldOffset` with `bSweep=true` only collides via the **Root Component**. `DefaultSceneRoot` has no collision body → bullets pass through walls. — Fix: `ActorTools.set_parent_component` to promote the mesh to root (make DefaultSceneRoot its child).

8. **[Collision] EventHit needs sweep or physics**: `EventHit` only fires when the root actually blocks during movement. — Fix: `bSweep=true` on movement nodes, or physics sim with `bNotifyRigidBodyCollision=true`.

9. **[Input] Non-Pawn actors ignore keyboard**: Keyboard events (SpaceBar, WASD) never fire on plain Actors. — Fix: in BeginPlay, `(Input|EnableInput :self self :PlayerController pc)` after binding `(Game|GetPlayerController :PlayerIndex 0)`.

10. **[Collision] Collision profile needs a collision shape**: `bodyInstance.collisionProfileName="BlockAll"` alone does nothing if the component has no shape. — Fix: components from PrimitiveTools (add_sphere/cube) have shapes; verify with `get_properties`.

12. **[Node] Keyboard events break DSL (event ...) syntax**: `Input|KeyboardEvents|SpaceBar` is K2Node_InputKey; DSL auto-prepends `AddEvent|` which doesn't exist for it. — Fix: create via `create_node` tool, then connect pins via ProgrammaticToolset script.

13. **[Node] SpawnActor needs _C class path**: Use `/Game/BP_X.BP_X_C` (generated class), not `/Game/BP_X.BP_X` (asset). — Fix: append `_C` for the `Class` pin.

---

*Full historical index P1-P49 with all details: `references/history/UE_Test_Achievements.md`*
