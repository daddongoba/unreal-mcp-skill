# Capability: data-ui
> toolsets: DataTableTools / CurveTableTools / StringTableTools / DataAssetTools / UMGToolSet / SlateInspectorToolset | status: VERIFIED (save-load, UMG) | 2026-08-29 UE5.8-EN
> Routing: any task about save games, data tables, curve tables, string tables, data assets, UMG widgets/HUD, in-game UI.

## 1. Boundaries
- CAN: slot save/load (BP subclass), DataTable/CurveTable/StringTable create+edit, DataAsset ops, UMG widget creation + runtime HUD, viewport add, slate runtime interaction, HUD text updates.
- CANNOT: AnimBP (refused), visual UI design quality (text layout via widgets only).
- SaveGame: engine base class instantiates-but-fails — ALWAYS BP subclass first (#36).

## 2. Design conventions
- Save chain: create BP_SaveData(SaveGame parent) → compile → save → CreateSaveGameObject("/Game/.../BP_SaveData.BP_SaveData_C") → SaveGameToSlot/LoadGameFromSlot (category `SaveGame|`).
- UMG runtime: CreateWidget pin=Class; AddToViewport = `UserInterface|Viewport|AddtoViewport`; update text via widget refs each tick.
- DataAsset: engine base classes are dead subjects (same family as SaveGame) — BP subclass first.

## 3. Tool params (verified signatures)
| Tool | Params |
|---|---|
| `DataTableTools` / `CurveTableTools` / `StringTableTools` create/edit | path/package_path styles vary (G12 — error-iterate) |
| `DataAssetTools` ops | asset refs |
| `UMGToolSet` widget creation | widget class/name params (see umg_basic.txt) |
| DSL nodes: `SaveGame|CreateSaveGameObject` / `SaveGametoSlot` / `LoadGamefromSlot` / `DoesSaveGameExist` | conversion pins vary (ToString(Boolean)=InBool etc. — get_node_type_pins) |
| `UserInterface|Viewport|AddtoViewport` | widget |

## 4. Laws (domain)
- SaveGame nodes live under `SaveGame|` NOT `Game|` (#37 archived); conversion pin names inconsistent (#37).
- Engine base classes (SaveGame/DataAsset) are invalid subjects — BP subclass first (#36).
- Cross-domain: G2/G3/G12.

## 5. Recipes
| Task | Template |
|---|---|
| Slot save/load | `templates/save_load.txt` [PIE] |
| UMG HUD | `templates/umg_basic.txt` [PIE] |
| Automation regression harness | `templates/automation_test.txt` [VERIFIED] |

## 6. Evidence
- 2026-08-23/24: save_load (TestSlot.sav 2014B written+read), UMG HUD updates (T58 screenshots), automation harness discovered tests.
