# Tool Schemas — verified parameter signatures (UE 5.8 EN, 2026-08-28)

> Purpose: skip the `describe_toolset` discovery round-trips in fresh sessions. These signatures were
> battle-tested on 2026-08-28. After a UE upgrade run `scripts/refresh_schemas.ps1` and diff against
> this file (Freshness matrix: UE minor upgrade invalidates this page).
> Convention: refs are `{"refPath": "..."}` objects; transforms are `{location:{x,y,z}, rotation:{pitch,yaw,roll}, scale:{x,y,z}}`.

## BlueprintTools (`editor_toolset.toolsets.blueprint.BlueprintTools`)

| Tool | Params |
|---|---|
| `create` | `folder_path:str, asset_name:str, asset_type:ref` (parent class, e.g. `/Script/Engine.Actor`; SaveGame/DataAsset use their engine class) |
| `get_default_object` | `blueprint:ref` → CDO ref |
| `get_graph` | `blueprint:ref, graph_name:str` ("EventGraph") → graph ref |
| `add_variable` | `blueprint:ref, name:str, type_name:str ("float"/"bool"/...), container_type?` |
| `list_variables` | `blueprint:ref` |
| `write_graph_dsl` | `graph:ref, code:str` (writes AND compiles) |
| `read_graph_dsl` | `graph:ref` |
| `compile_blueprint` | `blueprint:ref, warnings_as_errors?:bool` |
| `find_node_types` | `graph:ref, type_id_filter:str, context_pins:[]` |
| `get_node_infos` | `nodes:[ref]` |
| `add_event` | `blueprint:ref, event_name:str, position?:{x,y}` |
| `connect_pins` | `output_pin:pinId, input_pin:pinId` (pinId = `{direction:"EGPD_Output", index_id:int, node:ref}`) |
| `set_pin_value` | `pin:pinId, value:str` |
| `find_nodes` | `graph:ref, title:str, entry_points_only?:bool` |

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
| `find_actors` | `name, tag, collision_channels` (all required; name=substring match) |
| `remove_from_scene` | `actor:ref` |
| `trace_world` | `start:{x,y,z}, end:{x,y,z}` → returns DISTANCE (ground_z = start.z − dist) |
| `get_current_level` | `{}` |
| `load_level` | `level_path:str` (fails if current level has unsaved changes) |

## AssetTools
| Tool | Params |
|---|---|
| `save_assets` | `asset_paths:[str]` (empty = all dirty) — **verify on disk after (SKILL#46)** |
| `find_assets` | `folder_path, name, recursive?=true, asset_type?` |
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
