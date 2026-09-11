# Capability: blueprint
> toolsets: BlueprintTools / ProgrammaticToolset / UMGToolSet (widgets) | status: DEEP-VERIFIED (5 PIE features + 2026-09-06 cross-BP battery) | 2026-09-06 UE5.8-EN
> Routing: any task about creating/editing blueprints, DSL graphs, variables, functions, events, components, cross-BP calls, widget BPs, compiling.

## 1. Boundaries
- CAN: create BP from any Actor-family parent, add components (mesh/box/camera...), member+local variables (incl object/struct types), event graphs via DSL, function graphs + signature params, cross-BP calls (create_node AND DSL), widget BPs (UMGToolSet), compile.
- CANNOT: AnimBlueprint creation (engine refusal — G13), state-machine graphs, input-key events via DSL (must create_node+Python), editing BPs while PIE runs.
- The DSL compiler is the bottleneck: pure nodes in for/if bodies get hoisted & mis-wired — see G6.

## 2. Design conventions
- Workflow order (mandatory): design check → create → CDO components → variables → **node lookup** (`scripts/search_node_dict.ps1` for any type_id/pin not template-verified) → DSL (write_graph_dsl MERGES — clean stale nodes) → compile → save → re-place instances.
- Step 0 design check: consult domain docs (this router) + ue_conventions.md §5 before choosing components/events.
- Logic actors (watchers/controllers): invisible, self-discovering targets via tagged overlap — see physics-collision.md §5 scene_watcher.
- Cross-BP calls: `Class|<NameNoUnderscores>|<Func>` (strip underscores from BP name — MANDATORY; underscore-kept / no-prefix / bare-name+declaring_class all fail).

### Idempotency guards (re-entrancy safety for retried/batched operations)

| Operation | Re-run safe? | Guard to apply |
|---|---|---|
| `write_graph_dsl` | NO — MERGES | Same-name event rewrite REPLACED the body in clean tests (2026-09-06) — but failed/partial writes leave residue: find_nodes + delete_node stale entries, verify absence AND presence (G2/#33/#49). Failed compile inside write (it writes AND compiles) leaves the written graph uncompiled — clean + retry. |
| `connect_pins` | NO — duplicate-connection error | Check `pin.connected_pins` is empty before connecting (#3). |
| `compile_blueprint` | YES | Safe to repeat. In Python scripts put compile LAST — an error aborts the whole script (G10). |
| `save_assets` | YES | Repeat freely; disk-verify .umap/WP-level ALWAYS, .uasset first save of session (G3). New assets NOT auto-saved (#19). |
| `set_properties` (component profiles) | silent-fail risk | ALWAYS read back — profiles silently fail on StaticMeshComponent (SKILL#41). Instance struct props: first-scalar-only (#53). |
| `add_variable` / `add_object_variable` / `add_struct_variable` | UNKNOWN | Guard: `list_variables` first, skip if name exists. |
| `add_component` (ActorTools) | UNKNOWN | Guard: `get_components` check name before adding. |
| `add_function_graph` | NO (function exists → error) | Guard: `list_functions` first; on rerun use `get_graph` (2026-09-06). |
| `add_function_param` | UNKNOWN (existing name) | Signature-only op; verify via `get_node_type_pins` after recompile. |
| `BlueprintTools.create` | UNKNOWN | Guard: `AssetTools.exists` before create. |
| `set_pin_value` | UNKNOWN (last-wins assumed) | Prefer full-graph DSL rewrites over repeated pin surgery when >3 pins change. |

## 3. Tool params (verified signatures)
| Tool | Params |
|---|---|
| `BlueprintTools.create` | folder_path, asset_name, asset_type:ref(parent class) |
| `get_default_object` | blueprint:ref → CDO ref |
| `get_graph` | blueprint:ref, graph_name:"EventGraph" |
| `list_graphs` / `list_functions` | blueprint:ref — graph/function discovery + existence guards |
| `add_variable` | blueprint, name, type_name ("bool"/"int"/"float"/"string"/"Vector"/...) |
| `add_object_variable` / `add_struct_variable` | blueprint, name, object_class:ref / struct_type:ref |
| `write_graph_dsl` | graph:ref, code:str — writes AND compiles (compile failure leaves written graph) |
| `read_graph_dsl` | graph:ref — readback prints INTERNAL bool ids (b-prefixed); unwired/unused binds pruned; auto-stub events (Tick/Overlap skeletons) may appear in fresh BPs |
| `compile_blueprint` | blueprint:ref [, warnings_as_errors] |
| `find_node_types` / `get_node_type_pins` | graph, type_id_filter / type_id — cross-BP ids appear WITHOUT context (context_pins=[] works, 2026-09-06) |
| `find_nodes` / `delete_node` | graph, title[, entry_points_only] / node:ref — NOTE: event entry titles don't match "EventBeginPlay" string (found 0 in test); delete by exact refPath instead |
| `add_event` | blueprint, event_name, position? |
| `add_function_graph` / `remove_function_graph` | blueprint, graph_name |
| `add_function_param` / `remove_function_param` | graph, param_name, param_type, input_param:bool — input_param=false declares the RETURN value (param_name="ReturnValue"); REQUIRED for ReturnValue pin on call nodes (R24) |
| `create_node` | graph, type_id, pos{x,y} [, declaring_class] — cross-BP `Class|X|Y` ids WORK (declaring_class unnecessary); types with `Class|` namespace resolve against project BP classes even uncompiled |
| UMGToolSet: `CreateWidgetBlueprint` | folderPath, assetName, parentClass:ref(/Script/UMG.UserWidget) |
| UMGToolSet: `CompileWidgetBlueprint` | widgetBlueprint:ref |
| ProgrammaticToolset: `execute_tool_script` | script:str — sandbox: json/math/re/time/copy/datetime only (NO unreal import); aborts on first tool error; run() MUST return dict |

## 4. Laws (domain)
- **G6 DSL structure (#12 #14 #30 #48b)**: top level = event/fn only; arithmetic binary; input-key events via create_node; for/if bodies = SetVar/PrintString only.
- **G2 Graph rewrite (#49 #50 #33)**: write_graph_dsl MERGES — find_nodes+delete_node stale entries, verify absence AND presence; bool ids input(display)/readback(internal) asymmetric — never round-trip verbatim; dedupe after failed retries. Refinement (2026-09-06): clean same-name event rewrites REPLACE the body; residue comes from failed/partial writes.
- **G7 Names & paths (#5 #13 #27 #28 #29)**: asset `BP.BP`/graph `BP.BP:EventGraph`/CDO `Default__BP_C`/component `BP_C:Comp_GEN_VARIABLE`; SpawnActor `_C`; cast outputs have spaces; cross-BP `Class|NameNoUnderscores|Func`.
- **G9 (blueprint facet) (#25 #47 #53)**: instances don't pick up template edits — re-place; instance struct props first-scalar-only; CDO component refs settable, instance object vars NOT.
- **Namespace law (2026-09-06)**: node_dictionary display_name/category = PALETTE names, NOT tool type_ids (e.g. display "float * float"/"Flow Control"/"To String (Integer)" vs tool `Utilities|Operators|Multiply`/`Utilities|FlowControl|Branch`/`Utilities|String|ToString(Integer)`). Tool ids are compact; verify dictionary-sourced ids with find_node_types before create_node. Encoded at node_types.md top.
- **Cross-BP authoring (R24-R26, 2026-09-06)**: function return types need add_function_param(input_param=false) + recompile; multi-param events = ONE parenthesized list; cross-BP call :self target MUST be wired (caller-is-target exception); widget events need `AddEvent|UserInterface|` prefix.
- Pre-G-format incidents #2 (IsInputKeyDown needs PlayerController — encoded R6) and #3 (duplicate-connection guard — encoded Idempotency table) live in `references/pitfalls_archive.md`.
- Cross-domain: G3 save-disk-verify, G12 param anarchy.

## 5. Recipes
| Task | Template |
|---|---|
| WASD movement | `templates/movement_wasd.txt` [PIE] |
| Projectile | `templates/projectile_basic.txt` [PIE] |
| Spawn/despawn lifecycle | `templates/spawn_despawn.txt` [PIE] |
| Interactive door (trigger+lerp+cross-BP) | `templates/interactive_door.txt` [PIE] — ADAPT, don't copy |
| C++ class + BP inheritance | `templates/cpp_workflow.txt` [VERIFIED] |
| DSL language reference | `references/dsl_syntax.md` (R1-R26) + node_types.md |

## 6. Evidence
- flip-wall / orbit-puzzle / sink-watcher / WASD / projectile all PIE-confirmed.
- b-prefix asymmetry (#27/#50), merge semantics (#49), loop hoisting (#48) all discovered via these builds.
- 2026-09-06 cross-BP battery (CCC test bed): create_node cross-BP in Actor BP + WBP + uncompiled target; DSL cross-BP chain SpawnActor→GetTotalItems→ToString(Integer)→Print compiled and **PIE-returned 42** (LogBlueprintUserMessages `[BP_Caller_C_UAID_...] 42`); WBP Tick via `AddEvent|UserInterface|EventTick (MyGeometry InDeltaTime)`; failure forms catalogued (underscore-kept, no-prefix, bare+declaring_class, short ToString path).
