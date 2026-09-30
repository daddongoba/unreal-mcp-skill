# Capability: scene-actors
> toolsets: SceneTools / ActorTools | status: DEEP-VERIFIED | 2026-08-29 UE5.8-EN
> Routing: any task about placing/moving/finding actors, level loading, folders, tags, transforms, demo layout.

## 1. Boundaries
- CAN: spawn from asset/class, find by name/tag/type/bounds, transforms, parent-child, tags, folders, level load/switch, trace terrain, focus viewport.
- CANNOT: level blueprint (lazy object — see G9/#47), WorldPartition save via duplicate (G3), landscape editing.
- /Temp untitled levels: session-scoped only (G3) — persistence needs manual Save Level As.

## 2. Design conventions
- Placement order: get_current_level → trace_world (terrain height!) → place above ground → PlayerStart-relative for demos (facing = yaw 0:+X/90:+Y/180:−X, 800-1200 units ahead) → FocusOnActors.
- Re-survey after user edits — transforms change silently; find_actors fresh every time (stale UAIDs break actor-typed params).
- Existing-scene integration: prefer zero-touch (see physics-collision §5 scene_watcher) — strategies A(instance props) < B(new logic actor) < C(re-place, red-light) < D(edit their BP, disclose blast radius).

## 3. Tool params (verified signatures)
| Tool | Params |
|---|---|
| `SceneTools.add_to_scene_from_asset` | asset_path, name, xform{location,rotation,scale} [, parent, snap_to_ground] |
| `add_to_scene_from_class` | actor_type_ref, name, xform |
| `find_actors` | name(substring), tag, collision_channels, actor_type, bounds, root — first three required, last three optional (5.8.3). ⚠ `collision_channels` is an ENUM array: `[]` or `[0]` work, `["WorldStatic"]` FAILS `[VERIFIED 2026-09-25 UE5.8.3-EN]` |
| `remove_from_scene` | actor:ref |
| `trace_world` | start{x,y,z}, end → DISTANCE (ground_z = start.z − dist) |
| `get_current_level` / `load_level` | {} / level_path (fails on unsaved changes) |
| `ActorTools.get/set_actor_transform` | actor:ref [, xform, worldspace=true] |
| `ActorTools.set_label` / `get_root_component` / `get_components` | actor:ref [, label] |
| `EditorAppToolset.FocusOnActors` | actors:[ref] |
| `ActorTools.add_tag` / `has_tag` | actor:ref, tag |

## 4. Laws (domain)
- **G11 Scene placement reality (#20 #24 #44)**: trace_world BEFORE placing (OpenWorld terrain buries actors, z≈450 at origin!); PIE instances live at `/Memory/UEDPIE_N_` paths; PlayerStart-first placement.
- **G20 [Flow] Adding a level leaks its WORLD-GLOBAL actors — classic symptom: the host scene goes black** `[VERIFIED 2026-09-29 UE5.8.3-EN — diagnosed from a package scan; the fix was confirmed by the user in-editor]`: bringing another level in (Level Instance / streaming level / simply dragging the `.umap` into the viewport) also brings that level's world-wide actors. The usual killer is a **PostProcessVolume with `Infinite Extent (Unbound)` = true** — an unbound volume applies to the WHOLE world regardless of where it sits, so the incoming level's `bOverride_AutoExposure*` / `AutoExposureMin-MaxBrightness` / colour-grading overrides replace the host scene's exposure and it renders black. Same leak class: unbound lights, sky atmosphere, height fog, reflection captures. **Fix: on the incoming level's PP volume, uncheck Infinite Extent and scale it to cover only its own area (and/or clear the exposure overrides) — or delete it.** That works for EVERY transfer method, Level Instance included. Avoid-carry matrix: **Packed Level Actor / Blueprint-Actor (mesh components only) / Merge Actors carry geometry only**; **Level Instance and "drag the .umap in" carry everything**. Cheap pre-diagnosis without opening the editor: scan the source level's packages for `PostProcessVolume` + `bUnbound` — in a World Partition level it lives under `__ExternalActors__/`, while the persistent `.umap` may hold only `WorldSettings`.
- Cross-domain: G3 (level save untrustworthy), G9 (stale instance refs), G12 (live actor refs for actor-typed params).

## 5. Recipes
| Task | Template |
|---|---|
| AI asset → scene prop pipeline | `templates/ai_asset_import.txt` [PIE] |
| Existing-scene attach workflow | physics-collision.md §5 scene_watcher + few_shots case #8 |

## 6. Evidence
- All 5 PIE features used this placement chain; terrain-burial (#24) and PlayerStart-facing (#44) both discovered in production.
## 7. Level Instance coordinate systems (G14)

Two worlds share one toolset — ALWAYS resolve which one you're in before transform tasks:

| Task | Correct target | How to get it |
|---|---|---|
| Move/rotate instance PLACEMENT in parent level | The SHELL actor | find_actors → pick ref WITHOUT instance-world prefix; or user selects it → GetSelectedActors |
| Edit actors INSIDE the instance | Sub-world refs | edit_level_instance → operate → exit; refs carry instance-world prefix |

Instance tools (SceneTools): create_level_instance / edit_level_instance / commit_level_instance.
Pre-transform assertion (mandatory for instance tasks): enumerate ALL matching refs, state which is shell vs inner, THEN transform the right one. Post-transform: visual capture (R2) — placement change is eye-verifiable only.
