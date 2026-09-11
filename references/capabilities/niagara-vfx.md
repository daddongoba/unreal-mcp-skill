# Capability: niagara-vfx
> toolsets: NiagaraToolsets.System / Component / Blueprint / Assets | status: DEEP-VERIFIED (authoring loop) | 2026-08-29 UE5.8-EN
> Routing: any task about particle effects, VFX, emitters, modules, renderers, Niagara systems.

## 1. Boundaries
- CAN: create systems from engine templates, add emitters (from engine emitter templates), add modules (from NiagaraScript assets), add renderers, read full topology (emitter/script/module/input schemas), user variables, compile state, stack issues + auto-fix, component instances on actors, dynamic input chains.
- CANNOT: author new module SCRIPTS from scratch (only reference existing assets), GPU-sim specifics untested, mesh renderers untested.
- Trap: template-copied emitters can be HOLLOW (scripts/modules None, writes fail "emitter data is invalid") — always AddEmitter fresh from engine template.

## 2. Design conventions
- Authoring order: CreateNiagaraSystem(template) → AddEmitter(engine emitter template) → AddModule(NiagaraScript path) → verify topology → save+disk-verify.
- All template/asset params need OBJECT paths with dot suffix (`/Niagara/.../X.X`).
- Module paths: find_assets(/Niagara/Modules, type=NiagaraScript) when guesses fail — real layout is /Modules/Update/Color/ScaleColor (not /Update/ScaleColor).
- 6-field stack refs everywhere: {system, emitterName, scriptName, moduleName, rendererIndex, inputNameStack}.

## 3. Tool params (verified signatures)
| Tool | Params |
|---|---|
| `NiagaraToolset_System.CreateNiagaraSystem` | assetPath, assetName, templateSystem:OBJ-path |
| `GetSystemSummary` | system:ref → emitters+variables |
| `GetEmitterTopology` | emitterRef:6-field → scripts+modules+renderers |
| `AddEmitter` | system:ref, emitterName, templateEmitter:OBJ-path → complete emitter |
| `AddModule` | moduleAsset:OBJ-path(NiagaraScript), moduleLocationRef:6-field(scriptName targets stack) → auto-named e.g. ScaleColor001 |
| `AddRenderer` | emitterRef, rendererClass:ref, newRendererLocation:6-field (valid emitters only — hollow ones reject) |
| `SetEmitterData` / `SetModuleEnabled` / `Remove*` | 6-field refs + data |
| `GetSystemCompileState` / `GetStackIssues` / `ApplyStackIssueFix` | system/emitter refs |

## 4. Laws (domain)
- Hollow-template-emitter trap (2026-08-29): FountainLightweight-copied Fountain emitter has None scripts/modules — writes rejected. Fresh AddEmitter from SimpleSpriteBurst lands COMPLETE.
- Engine inventory: Systems under /Niagara/DefaultAssets/Templates/Systems/, Emitters under .../Emitters/, Modules under /Niagara/Modules/<Stage>/<Category>/.
- Cross-domain: G12 (object-path suffix rule born here), G3 (save+disk-verify — NS grew 138→306KB on disk).

## 5. Recipes
| Task | Template |
|---|---|
| System→emitter→module authoring loop | `templates/niagara_authoring.txt` [VERIFIED] |

## 6. Evidence
- 2026-08-29: MyBurst added (renderer+modules verified in topology), ScaleColor001 module added (input schema returned), NS_Test13 saved 306KB disk-verified.
