# Capability: anim-sequencer
> toolsets: animation_toolset.sequencer / keyframing / controlrig_sequencer / import_export | status: DEEP-VERIFIED to FBX | 2026-08-29 UE5.8-EN
> Routing: any task about cutscenes, level sequences, keyframe animation, camera animation, transform tracks, animating actors over time, FBX import/export of sequences.

## 1. Boundaries
- CAN: create/open sequences, bind actors (possessables), transform tracks (Location/Rotation/Scale 9 channels), float/int/bool/string keys, playback control, camera cuts (create_camera), event tracks, sub-sequences, folders, **FBX export (disk-verified)**.
- CANNOT: AnimBP creation (tool-layer refusal — see data-ui / SKILL.md G13 note), IK Retargeter, curve editor visual authoring (key APIs exist: open_curve_editor, select_keys — call-level only).
- Related but separate domain: skeletal posing via ControlRig → `anim-controlrig` (pending document; see controlrig_chain.txt meanwhile).

## 2. Design conventions
- Transform animation of a whole Actor = 3DTransformTrack + key float channels; no ControlRig needed for actor-level moves.
- Sequencer workflow order is FIXED: sequence → binding → track → section → channels → keys. Track/section types are CLASS refs (`/Script/MovieSceneTracks.MovieScene3DTransformTrack` / `...Section`), never strings.
- AnimBP state machines: not authorable; set AnimClass/play-rate/blend params on components instead (ObjectTools).

## 3. Tool params (verified signatures)
| Tool | Params |
|---|---|
| `SequencerTools.create_level_sequence` | package_path, asset_name → ref |
| `open_sequence` / `get_focused_sequence` | sequence:ref |
| `add_actors` | actors:[LIVE actor refs] — stale UAIDs fail "not valid Actor for TransientPythonProperty" |
| `get_bindings` | sequence:ref → [{bindingId, sequence}] |
| `add_track_to_binding` | sequence:ref, binding:{bindingId,sequence}, track_type:CLASS-REF |
| `get_sections` / `add_section` | track:ref [, section_type:CLASS-REF] |
| `SequencerKeyframingTools.get_channel_names` | section:ref → ["Location.X"..."Scale.Z"] |
| `add_key_float` | section, channel_name, frame, value, **interpolation:"Auto" (REQUIRED)** |
| `get_keys` | section, channel_name |
| `export_fbx` | sequence:ref, world:WORLD-obj(`/Game/L.L` NOT :PersistentLevel), bindings:[...], fbx_file_path |
| playback: play/pause/is_playing/set_playhead_frame/get_playback_range | sequence:ref |

## 4. Laws (domain)
- Sections don't exist by default on fresh tracks — add_section before keying (archived #31; CR tracks DO auto-create one section).
- Track/filter names like "Transform" as strings fail — class refs only (G12 subtype).
- World-typed params want the World OBJECT; PersistentLevel path is rejected (G12).
- Cross-domain: param anarchy G12 (error messages self-document), save-disk-verify G3 (FBX/export and sequence saves), graph-merge G2 (N/A here), stale-instance re-place G9 (bound actor must be live).

## 5. Recipes
| Task | Template |
|---|---|
| Full chain: sequence→bind→track→section→keys→FBX | `templates/sequencer_keyframe_chain.txt` [DISK-VERIFIED] |
| Legacy notes (pre-chain) | `templates/sequencer_keyframe.txt` [2026-08-24] |

## 6. Evidence
- End-to-end 2026-08-29: LS_Test13 bound flip-wall, Location.X keyed f0=1500/f120=2000 (get_keys readback), exported 25.3KB FBX to C:/UE_Import (disk-verified).
- Camera/event/sub-sequence tools: schema-live, untested.
