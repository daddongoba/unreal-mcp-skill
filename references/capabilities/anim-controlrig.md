# Capability: anim-controlrig
> toolsets: animation_toolset.controlrig / controlrig_sequencer | status: DEEP-VERIFIED (visual) | 2026-08-29 UE5.8-EN
> Routing: any task about posing characters via controls, rig authoring (bones/controls/nulls), rig graphs, anim layers, baking.

## 1. Boundaries
- CAN (VERIFIED end-to-end 2026-08-29 incl. VISUAL + FBX): create rig assets, import bones from skeletal meshes, add controls/nulls/bones, CR tracks in sequences, set_rotator+key_controls → **pose animation renders** (f0 vs f60 viewport capture showed bone bent 90°); **export_fbx with CR track bindings works** (CR_Cube_Anim.fbx 64.1KB disk-verified — CR animation exports same as transform tracks, just pass the sequence+bindings). Rig graph editing, anim layers, mirror/zero/snap, bake_to_control_rig, import_fbx_to_rig: call-level verified.
- READBACK CAVEAT: `get_rotator` returns 0.0 even when animation works — it reads the rig's static/editor state, NOT sequencer-evaluated values. Verify poses VISUALLY: set_playhead_frame(f) → CaptureViewport → compare frames. (2026-08-29 verified working method.)
- CaptureViewport REQUIRED params (all of): captureTransform{location,rotation,scale} + annotations{gridSpacing,gridExtent,gridHeight,maxLabelDistance,classFilter:{refPath},maxLabels} + bShowUI — omitting any → 400 "needs a default value".
- CANNOT: IK Retargeter (no tools anywhere).
- Prereq: skeletal mesh with INTACT skeleton — cross-project copied .uassets have broken skeleton refs (set_properties cannot fix asset-level Skeleton; CDO component refs ARE settable but asset refs NOT — G9).

## 2. Design conventions
- Rig authoring order: create → import_bones_from_asset(skeletal_mesh, NOT skeleton) → add_control(per bone) → verify get_all_bones/controls.
- Sequencing: sequence → binding → find_or_create_track(control_rig_asset_path) → set_rotator(frame) → key_controls(section).
- Engine test subject: /Engine/EngineMeshes/SkeletalCube (Bone01/Bone02, intact skeleton).

## 3. Tool params (verified signatures)
| Tool | Params |
|---|---|
| `ControlRigTools.create` | path:"/Game/TN/CR_Name" |
| `import_bones_from_asset` | control_rig:ref, skeletal_mesh:ref |
| `add_control` | control_rig:ref, name, bone |
| `get_all_bones` / `get_all_controls` / `get_all_nulls` | control_rig:ref |
| `get_graph` / `list_graphs` (+ forward_solve etc.) | control_rig:ref [, graph_name] |
| graph editing: create_node / connect_pins / set_pin_value / add_variable / list_nodes | rig-graph refs |
| `SequencerControlRigTools.find_or_create_track` | sequence:ref, binding:{bindingId,sequence}, control_rig_asset_path:str |
| `get_control_rigs` | sequence:ref → [{track, control_rig_name, is_layered}] |
| `set_rotator` | sequence:ref, control_rig_asset_path, control_name, frame, value{pitch,yaw,roll} |
| `key_controls` | section:ref, control_rig_asset_path, control_names:[...], frame |
| `get_rotator` | sequence:ref, control_rig_asset_path, control_name, frame |
| CR track sections: `SequencerTools.get_sections(track)` → auto-created MovieSceneControlRigParameterSection_0 |

## 4. Laws (domain)
- Param duality: some calls want control_rig as REF, others control_rig_asset_path as STRING — read error messages (G12).
- key_controls wants SECTION while set_rotator wants SEQUENCE (both + asset path).
- Cross-project asset copy breaks skeleton GUIDs — verify with get_bone_names before import attempts.
- Cross-domain: G12 param anarchy, G3 save-verify, G2 (rig graph edits share merge semantics caution).

## 5. Recipes
| Task | Template |
|---|---|
| Rig authoring + track + pose/key chain | `templates/controlrig_chain.txt` [CALL-VERIFIED] |

## 6. Evidence
- 2026-08-29 FULL VERIFICATION: CR_Cube + Ctrl_Bone01 + track + keys(f0=0°/f60=90°) all created; **viewport captures at f0 (straight) vs f60 (bone bent 90° — two-segment silhouette with kink, bulge, split shadow) confirm pose animation renders**; **CR sequence exported to FBX** (64.1KB, disk-verified). get_rotator 0.0 is a readback tool limitation, not a pipeline failure.
- Visual verification method: set_playhead_frame → CaptureViewport → analyze_multimedia frame comparison.
