# Capability: materials-assets
> toolsets: MaterialTools / MaterialInstanceTools / TextureTools / AssetTools / StaticMeshTools | status: VERIFIED (pipeline) | 2026-08-29 UE5.8-EN
> Routing: any task about materials, material instances, textures, asset import/export/move/delete, LODs, collisions, Nanite, asset discovery.

## 1. Boundaries
- CAN: create materials/functions, expression graph editing (add/connect/layout/delete), parameter groups, recompile, material instances, texture ops, asset CRUD (find/duplicate/move/delete/exists), static mesh pipeline (import_file, LODs, convex collisions, Nanite toggle, material slots), save+load assets.
- CANNOT: texture painting, material visual preview (thumbnails via EditorAppToolset.CaptureAssetImage), modeling-mode edits.
- AnimBP-type creation dialogs HANG MCP (G13) — general rule: asset types whose editor shows a picker on create are headless-hostile.

## 2. Design conventions
- AI texture pipeline: generate → import via write_file/import path → TextureSample → connect BaseColor → recompile → thumbnail verify (see ai_asset_import.txt).
- Asset moves/renames: AssetTools.move (path+new_path); deletes are RED-light on user assets (Danger Gates).
- Static mesh hygiene: generate_convex_collisions / set_nanite_enabled / LODs via StaticMeshTools.

## 3. Tool params (verified signatures)
| Tool | Params |
|---|---|
| `MaterialTools.create_material` / `create_function` | name/folder refs |
| `add_expression` / `connect_expressions` / `layout_expressions` | material:ref, expression class/pin pairs |
| `recompile` | material:ref |
| `AssetTools.find_assets` | folder_path, name, asset_type:ref[, recursive] — the universal discovery tool |
| `AssetTools.duplicate` / `move` / `delete` | path, new_path / path (return values LIE for WorldPartition — G3) |
| `save_assets` / `load_asset` / `exists` | asset_paths:[] (all dirty) / asset_path / path (in-memory check) |
| `StaticMeshTools.import_file` | mesh params + file path |
| `generate_convex_collisions` / `set_nanite_enabled` / `generate_lods` | mesh:ref |
| `AssetTools.write_file` / `read_file` | ABSOLUTE paths (Content/Saved roots only — #16) |

## 4. Laws (domain)
- Cross-domain (dominant here): G3 save-disk-verify, G12 (per-toolset param anarchy — three create() styles), G9 (CDO/asset ref settability split).
- Cross-project .uasset copies break internal GUID refs (skeleton case proven; likely general) — prefer fresh imports.

## 5. Recipes
| Task | Template |
|---|---|
| AI texture → material pipeline | `templates/ai_asset_import.txt` + `templates/material_pipeline.txt` [PIE] |
| Mesh import + collisions + LODs | StaticMeshTools chain (call-verified 2026-08-28 survey) |

## 6. Evidence
- 2026-08-23 material/MI pipeline PIE-verified; asset CRUD verified across all surveys; NS_Test13 disk-save verified via this toolset family.
