# Template Library Index

Verified DSL workflows — **reference starting points, NOT verbatim copy-paste**.
Before using any template: run the design check (ue_conventions.md §5 / SKILL.md Workflow step 0) and ADAPT components, events, and params to the actual requirement. Lesson (2026-08-28): blindly copying interactive_door.txt's mesh-cube trigger into the flip-wall task caused the failure — the template's approach was wrong for that context; the design conventions (BoxComponent trigger) were right.

## Standard template structure

Every `<name>.txt` contains:
1. `# Template` / `# Verified` / `# Requires` / `# MCP calls` — metadata header
2. `--- DSL ---` — the graph code
3. `--- Steps ---` — ordered MCP tool calls to apply it
4. `--- Verify ---` — how to confirm it works (PIE behavior)

## Index

| Template | Domain | Verified | Requires |
|----------|--------|----------|----------|
| [movement_wasd.txt](movement_wasd.txt) | Movement/Input | 2026-08-22 UE5.8 EN | MoveSpeed float var |
| [projectile_basic.txt](projectile_basic.txt) | Combat/Collision | 2026-08-22 UE5.8 EN | sphere root + BlockAll |
| [ai_asset_import.txt](ai_asset_import.txt) | AI asset pipeline | 2026-08-23 UE5.8 EN | AllToolsets + scripts/import_asset.ps1 |
| [material_pipeline.txt](material_pipeline.txt) | Material/MI | 2026-08-23 UE5.8 EN | none |
| [umg_basic.txt](umg_basic.txt) | UMG + runtime HUD | 2026-08-23 UE5.8 EN | none |
| [interactive_door.txt](interactive_door.txt) | Trigger + lerp anim + cross-BP | 2026-08-23 UE5.8 EN | trace terrain first (SKILL#24) |
| [cpp_workflow.txt](cpp_workflow.txt) | C++ + UBT + BP inheritance | 2026-08-23 UE5.8 EN | VS + DOTNET_ROOT + UE closed |
| [sequencer_keyframe.txt](sequencer_keyframe.txt) | Sequencer keyframes | 2026-08-24 UE5.8 EN | none |
| [automation_test.txt](automation_test.txt) | Regression harness | 2026-08-23 UE5.8 EN | AllToolsets |
| [spawn_despawn.txt](spawn_despawn.txt) | Actor lifecycle cycle | 2026-08-24 UE5.8 EN | spawnable class + terrain check |
| [save_load.txt](save_load.txt) | Slot persistence | 2026-08-24 UE5.8 EN | BP_SaveData subclass FIRST (SKILL#36) |
| [physics_runtime.txt](physics_runtime.txt) | Reliable PIE gravity physics | 2026-08-24 UE5.8 EN | mesh component + terrain check |
| [touch_trigger_rotation.txt](touch_trigger_rotation.txt) | Touch trigger → slow rotation (flip-wall / orbit puzzle) | 2026-08-28 UE5.8 EN | BoxComponent trigger + ROOT-physics driver |
| [scene_watcher.txt](scene_watcher.txt) | Zero-touch attach to existing scene actors (tag + sense box + settle + proximity) | 2026-08-28 UE5.8 EN | tagged targets + user-placed watcher |
| [sequencer_keyframe_chain.txt](sequencer_keyframe_chain.txt) | Full animation chain: sequence→bind→track→section→keys→FBX export | 2026-08-29 UE5.8 EN | live actor ref + writable export path |
| [controlrig_chain.txt](controlrig_chain.txt) | ControlRig authoring: rig→bones→controls→track→pose/key (call-verified; visual result OPEN) | 2026-08-29 UE5.8 EN | intact-skeleton skeletal mesh |
| [niagara_authoring.txt](niagara_authoring.txt) | Niagara VFX: create system→add emitter→add module→verify | 2026-08-29 UE5.8 EN | engine templates inventory |

## Adding a new template (per Self-Maintenance Protocol)

1. Develop DSL → PIE verify → user confirms.
2. Save as `references/templates/<name>.txt` with full standard structure.
3. Add row to the index above with verified date.
4. If the workflow revealed a new pitfall/rule, also update SKILL.md Pitfalls and dsl_syntax.md.
5. Templates record the VERIFIED SOLUTION for one context — when requirements differ (different trigger type, different event semantics, different component layout), the design conventions file wins over the template.
