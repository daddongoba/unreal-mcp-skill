# Toolset Map — full UE 5.8 MCP capability landscape (verified live 2026-08-29)

> 67 toolsets registered with AllToolsets enabled. Use this to answer "can I do X via MCP?"
> before promising anything. Re-verify after plugin/UE changes (`list_toolsets`).
> Verified statuses below are from the 2026-08-29 systematic capability survey (per-toolset probes).

## Capability boundaries at a glance

| UE feature | MCP coverage |
|---|---|
| Landscape sculpt/paint | ❌ none — VibeUE (free, Epic Dev Community) adds it; PCG (31 tools) covers procedural scattering |
| Modeling Mode (vertex-level mesh editing) | ❌ none — pipeline-level only (import/LOD/collision/Nanite via StaticMeshTools) |
| IK Retargeter (cross-skeleton retarget) | ❌ none (re-confirmed 2026-08-29, 67 toolsets scanned) |
| AnimBP state-machine graph editing | ⚠️ BLOCKED-BY-MODAL: `BlueprintTools.create(asset_type=/Script/Engine.AnimBlueprint)` hangs the MCP server (skeleton-picker modal) — MCP stays down until user dismisses; AnimBP authoring NOT viable headless `[VERIFIED 2026-08-29 — crashed the server]` |
| **AnimBP state-machine** | ⚠️ BLOCKED-BY-MODAL: BlueprintTools.create with asset_type=/Script/Engine.AnimBlueprint **hangs the MCP server** (skeleton-picker modal, likely) — UE process alive but MCP dead until user dismisses dialog `[VERIFIED 2026-08-29]`. Do NOT create AnimBPs via MCP. |
| Level Blueprint editing | ⚠️ needs manual open-once first (G9/#47); UNVERIFIED after that |
| Keyframed animation | ✅ **FULL CHAIN VERIFIED 2026-08-29** (template sequencer_keyframe_chain.txt): create→bind→track→section→channels→keys→**FBX export (disk-verified)** |
| Niagara VFX | ✅ **deep-edit VERIFIED 2026-08-29** (template `niagara_authoring.txt`): CreateNiagaraSystem from template + AddEmitter (engine template, complete emitter lands) + AddModule (real NiagaraScript path) + topology readback — full authoring loop; template-copied emitters can be hollow (writes fail "emitter data is invalid") |
| PCG | ✅ verified: CreateGraph (lands in /Game/PCG/ by default!), AddNode(nativeNodeType="Surface Sampler" display-name + nodeName/nodeTitle/nodeComment/jsonParams all required), SpawnGraphInstance in level (graph+name+transform+jsonParams) |
| Skeletal mesh inspection | ✅ verified on /Engine/EngineMeshes/SkeletalCube (bones/sockets/morphs/LODs; mesh param = ref object) |
| Material editing | ✅ MaterialTools (23) + template verified earlier |
| Sequencer rebinding | ✅ rebind_component etc. (schema live, list-verified) |
| Dataflow | ✅ ListDataflowCompatibleAssetTypes verified (many templates incl skeletal attach); graph editing tools live |
| GAS | ✅ FindAttributeSetClasses/ListAttributes verified (real data) |
| Plugins | ✅ ListEnabledPlugins etc. (18 tools, incl CreatePlugin — untested write) |
| GameFeatures / DataRegistry | ✅ list tools live (empty project lists) |
| Automation tests | ✅ DiscoverTests → ready |
| AgentSkills (UE-side) | ✅ ListSkills shows embedded skills (PCG/Dataflow graph-generation skills) |
| SemanticSearch | ⚠️ live but Search struct params failed conversion (query+classFilter+pathRegexes[]+…) — needs exact struct shape, unresolved |
| BehaviorTree / StateTree / Conversation / WorldConditions | ⚠️ inspection tools live (schema-validated); no target assets in project to test against |
| ConfigSettings | ✅ live (containerName param) |
| PhysicsAsset | ⚠️ tools live; no PhysicsAsset found in engine content to test (create via CreateFromMesh untested) |

## animation_toolset family (the biggest hidden capability — ~290 tools)

| Toolset | Tools | Highlights |
|---|---|---|
| `toolsets.controlrig.ControlRigTools` | 45 | rig graph editing: bones/controls/nulls CRUD, variables, pins, event/backward/interaction/forward-solve graphs, import bones from mesh |
| `toolsets.sequencer.SequencerTools` | 141 | full sequence editing: tracks/sections/bindings/folders, camera, marked frames, spawnables, playback, **rebind_component / replace_binding_with_actors / fix_actor_references**, bake_transform |
| `toolsets.keyframing.SequencerKeyframingTools` | 23 | key CRUD (float/int/bool/string), channels, curve editor |
| `toolsets.controlrig_sequencer.SequencerControlRigTools` | 73 | posing & keying: get/set transforms on controls, key_controls(_at_frames), **anim layers (add/duplicate/merge/reorder)**, mirror/zero/snap, **import_fbx_to_rig / export_fbx_from_rig**, load_anim_into_rig, bake_to_control_rig |
| `toolsets.import_export.SequencerImportExportTools` | 7 | **import_fbx / export_fbx**, export/link anim sequences |
| `toolsets.outliner / conditions / custom_bindings` | — | sequencer folder/track organization, conditions, custom binding management |

Proven pipeline (VERIFIED 2026-08-29 end-to-end, template `sequencer_keyframe_chain.txt`):
create_level_sequence → add_actors(live ref) → add_track_to_binding(class ref) → add_section →
get_channel_names → add_key_float(interpolation REQUIRED) → export_fbx(world=World obj, disk-verified).
ControlRig authoring (CALL-VERIFIED 2026-08-29, template `controlrig_chain.txt`):
create rig → import_bones_from_asset(skeletal_mesh=ref, NOT skeleton) → add_control(bone=) →
find_or_create_track(sequence, binding, control_rig_asset_path) → set_rotator(sequence+frame+value) →
key_controls(section+control_names+frame) — every call succeeds, but pose readback stays 0.0:
evaluation linkage unresolved `[OPEN ITEM — verify visually before promising animation]`.
Cross-project copied skelmeshes have broken skeleton refs; set_properties CANNOT fix asset-level
Skeleton (CDO component refs settable, asset refs NOT) — import bones only from intact meshes.

## Core editor toolsets

| Toolset | Tools | Note |
|---|---|---|
| BlueprintTools | 49 | create/DSL/vars/pins/compile — see tool_schemas.md |
| SceneTools / ActorTools / AssetTools / ObjectTools / PrimitiveTools | 20/20/24/6/4 | see tool_schemas.md |
| StaticMeshTools | 17 | import, LODs, collisions, Nanite, material slots |
| SkeletalMeshTools | 23 | bones, sockets, morphs, physics asset, import |
| MaterialTools / MaterialInstanceTools | 23/? | expressions, params, functions |
| TextureTools / DataTable / CurveTable / StringTable / DataAsset | — | asset-type CRUD |
| ProgrammaticToolset | 1+ | execute_tool_script (batch Python — preferred for 10+ ops) |
| EditorAppToolset | 25 | PIE, viewport, selection, capture, camera |
| LogsToolset | 4 | GetLogEntries(category:"" for all) |
| AgentSkillToolset | — | list/read/create agent skills from inside UE |

## Extended toolsets (AllToolsets plugin)

AutomationTest, ConfigSettings, DataflowAgent, DataRegistry, GameFeatures, GameplayTags,
PluginToolset, SemanticSearch, SlateInspector, WorldConditions, UMG, StateTree, MVVM,
ConversationToolset, PCGToolset + PCGSpatialToolset, PhysicsAssetToolset,
NiagaraToolsets (Info/Component/Blueprint/System/Assets),
GASToolsets (GameplayCue/AttributeSet/AbilitySystemInspector),
BehaviorTreeTools, aimodule extras.

## Known-absent (verify again after UE/plugin upgrades)

Landscape sculpt/paint tools, Modeling Mode vertex tools, IK Retargeter tools,
AnimBP state-machine graph tools, Audio tools, UV editor, Profiler/Insights.
