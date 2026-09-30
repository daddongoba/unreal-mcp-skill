# Tool Schemas — verified parameter signatures (UE 5.8.3 EN, re-verified 2026-09-24)

> Purpose: skip the `describe_toolset` discovery round-trips in fresh sessions. Battle-tested on
> 2026-08-28 (UE 5.8.0); the live diff was re-run against UE 5.8.3 on 2026-09-24 and reported
> **0 DRIFT** (every recorded param still exists) plus a handful of tools with new OPTIONAL params,
> listed below.
> After a UE upgrade run `powershell -File scripts/refresh_schemas.ps1 -Live` (UE must be running)
> and diff against this file. The live diff is toolset-aware, so colliding tool names
> (`create`, `add_variable`, `connect_pins`, `get_graph`, `list_variables`) no longer false-alarm.
> Convention: refs are `{"refPath": "..."}` objects; transforms are `{location:{x,y,z}, rotation:{pitch,yaw,roll}, scale:{x,y,z}}`.

## New optional params in 5.8.3 (additive, non-breaking) `[VERIFIED 2026-09-24 UE5.8.3-EN]`

(Toolset column first so `refresh_schemas.ps1`'s row parser does not read these as signatures.)

| Toolset | Tool | New optional params |
|---|---|---|
| BlueprintTools | `add_variable` | `graph` |
| BlueprintTools | `list_variables` | `graph` |
| BlueprintTools | `find_nodes` | `node_class` |
| BlueprintTools | `set_pin_value` | `control_rig`, `graph` |
| SceneTools | `find_actors` | `actor_type`, `bounds`, `root` |
| AssetTools | `find_assets` | `tags` |

## BlueprintTools tools added/available in 5.8.3 `[VERIFIED 2026-09-24 UE5.8.3-EN]`

BlueprintTools now exposes 53 tools (was 48 in 5.8.0). Previously undocumented but present —
params live-verified:

| Tool | Params |
|---|---|
| `get_graph_dsl_docs` | `{}` |
| `find_node_categories` | `graph, category_filter, context_pins` |
| `retarget_node_class` | `node, old_class, new_class` |
| `list_compatible_event_functions` | `node` |
| `get_create_event_function` | `node` |
| `add_component_bound_event` | `graph, component, event_name` |
| `set_variable_instance_editable` | `blueprint, variable_name, instance_editable` |

- `get_graph_dsl_docs` returns the **authoritative in-engine DSL grammar** (~8.7KB) — cross-check
  `dsl_syntax.md` against it, but note its Switch id error (see node_types.md).
- `find_node_categories` lists node categories, filterable by compatible input/output pin types.
- `retarget_node_class` swaps a node's baked-in class reference in place.
- `add_component_bound_event` creates a component-bound event node in the event graph.
- `set_variable_instance_editable` sets per-instance editability on a member variable.
- Also present (params not yet verified — probe before use): `add_object_variable`,
  `add_struct_variable`, `get_pin_value`, `break_pins`, `add_node_pin`, `remove_node_pin`,
  `arrange_nodes`, `set_variable_category`, `get_variable_category`, `set_variable_replication`,
  `get_variable_replication`, `add_event_dispatcher`, `list_event_dispatchers`, `get_parent`,
  `set_parent`.


## BlueprintTools (`editor_toolset.toolsets.blueprint.BlueprintTools`)

| Tool | Params |
|---|---|
| `create` | `folder_path:str, asset_name:str, asset_type:ref` (parent class, e.g. `/Script/Engine.Actor`; SaveGame/DataAsset use their engine class) |
| `get_default_object` | `blueprint:ref` → CDO ref |
| `get_graph` | `blueprint:ref, graph_name:str` ("EventGraph") → graph ref |
| `add_variable` | `blueprint:ref, name:str, type_name:str ("float"/"bool"/...), container_type?, graph?` |
| `list_variables` | `blueprint:ref, graph?` |
| `write_graph_dsl` | `graph:ref, code:str` (writes AND compiles) |
| `read_graph_dsl` | `graph:ref` |
| `compile_blueprint` | `blueprint:ref, warnings_as_errors?:bool` |
| `find_node_types` | `graph:ref, type_id_filter:str, context_pins:[]` |
| `get_node_infos` | `nodes:[ref]` |
| `add_event` | `blueprint:ref, event_name:str, position?:{x,y}` |
| `connect_pins` | `output_pin:pinId, input_pin:pinId` (pinId = `{direction:"EGPD_Output", index_id:int, node:ref}`) |
| `set_pin_value` | `pin:pinId, value:str` |
| `find_nodes` | `graph:ref, title:str, entry_points_only?:bool, node_class?` |

## ActorTools
| Tool | Params |
|---|---|
| `add_component` | `owner:ref, component_type:ref, name:str` → new component ref (**use for BoxComponent triggers** `/Script/Engine.BoxComponent`) |
| `remove_component` | `component:ref` |
| `set_parent_component` | `component:ref, parent:ref` — to promote mesh to ROOT pass `component=<DefaultSceneRoot>, parent=<Mesh>`; **parent omitted = "attach to world" → error on BP templates** |
| `get_root_component` | `actor:ref` |
| `get_components` | `actor:ref, component_type?:ref` |
| `get/set_actor_transform` | `actor:ref [, xform, worldspace=true]` |

## PrimitiveTools
| Tool | Params |
|---|---|
| `add_cube` | `actor:ref, name:str, dimensions?{x,y,z}=100, local_transform?:transform` (creates StaticMeshComponent under root — needs ROOT promotion for physics) |
| `add_cylinder` | `actor:ref, name:str, radius?=50, height?=100, local_transform?` |

## ObjectTools
| Tool | Params |
|---|---|
| `get_properties` | `instance:ref, properties:[str]` (unknown props → hard error; query one-by-one to isolate) |
| `set_properties` | `instance:ref, values:str(JSON)` — nested `{"bodyInstance":{...}}` works but **profiles silently fail on StaticMeshComponent** (SKILL#41); flat dotted keys = error; ALWAYS read back |

## SceneTools
| Tool | Params |
|---|---|
| `add_to_scene_from_asset` | `asset_path:str, name:str, xform, parent?:ref, snap_to_ground?:bool` |
| `find_actors` | `name, tag, collision_channels, actor_type, bounds, root` (first three required in 5.8.0; name=substring match; 5.8.3 adds the optional `actor_type`/`bounds`/`root`) |
| `remove_from_scene` | `actor:ref` |
| `trace_world` | `start:{x,y,z}, end:{x,y,z}` → returns DISTANCE (ground_z = start.z − dist) |

**⚠ `find_actors.collision_channels` IS AN ENUM ARRAY — the schema lies** `[VERIFIED 2026-09-25 UE5.8.3-EN]`.
The schema declares `{"type":"array","items":{"type":"string"}}`, but strings do NOT convert:
`[]` (all channels) and `[0]` (numeric enum index) work; `["WorldStatic"]` and `["ECC_WorldStatic"]`
**fail** with a generic `could not convert incoming function input params Json to a UStruct` that does
NOT name the offending param. Use `[]` unless you specifically need channel filtering.

| `get_current_level` | `{}` |
| `load_level` | `level_path:str` (fails if current level has unsaved changes) |

## AssetTools
| Tool | Params |
|---|---|
| `save_assets` | `asset_paths:[str]` (empty = all dirty) — **verify on disk after (SKILL#46)** |
| `find_assets` | `folder_path, name, recursive?=true, asset_type?, tags?` |
| `create_folder` | `path:str` |
| `exists` | `path:str` (in-memory check — NOT a disk check!) |
| `duplicate` / `move` / `delete` | `path:str, new_path?` — **return values lie for WorldPartition temp levels** (SKILL#43/#46) |
| `load_asset` | `asset_path:str` |

## EditorAppToolset
| Tool | Params |
|---|---|
| `StartPIE` | `options:{bSimulate:bool, playMode:str("PlayMode_InViewPort"), warmupSeconds:num}` |
| `StopPIE` / `IsPIERunning` | `{}` |
| `FocusOnActors` | `actors:[ref]` |
| `CaptureViewport` | `captureTransform?, annotations?, bShowUI?` |

## LogsToolset
| Tool | Params |
|---|---|
| `GetLogEntries` | `category:""(empty=all), pattern:str(regex), maxEntries:int` |
