# Capability: physics-collision
> toolsets: PrimitiveTools / ActorTools / ObjectTools | status: DEEP-VERIFIED (3 PIE features) | 2026-08-29 UE5.8-EN
> Routing: any task about triggers, touch/contact, physics falling/sinking/simulating, collision responses, pushing objects.

## 1. Boundaries
- CAN: physics activation (gravity), touch/overlap triggers, blocking collision, tag-gated targets, proximity detection, physics on/off at runtime, slow interpolation effects (sink/rotate).
- CANNOT: cloth, destruction (see dataflow capability), vehicle physics, per-bone ragdoll authoring (PhysicsAssetToolset tools live but untested).
- GOTCHA: flying DefaultPawn cannot push physics bodies — proximity triggers, never displacement (#52).

## 2. Design conventions
- **Triggers = BoxComponent** (`ActorTools.add_component "/Script/Engine.BoxComponent"`), NEVER mesh cubes (#41): profiles silently fail on StaticMeshComponent.
- **Physics body mesh must be ROOT** component (#40): `set_parent_component(component=<DefaultSceneRoot_GEN_VARIABLE>, parent=<Mesh_GEN_VARIABLE>)`.
- **Runtime activation only** (#35/#38): serialized bSimulatePhysics flags unreliable → BeginPlay DSL `GetComponentbyClass → SetSimulatePhysics(true)`.
- **Trigger profile** = "Trigger" (QueryOnly + all-Overlap); verify first-of-kind write per session (v3.1). "TriggerOnly" does not exist.
- **Player interaction** = proximity (GetPlayerPawn + GetDistanceTo < 250), not push (#52).
- Settle-detector pattern for physics-falling targets (wait ~30 ticks still before arming).

## 3. Tool params (verified signatures)
| Tool | Params |
|---|---|
| `PrimitiveTools.add_cube` | actor:ref, name, dimensions?{x,y,z}=100, local_transform? — creates StaticMeshComponent under root |
| `ActorTools.add_component` | owner:ref, component_type:ref("/Script/Engine.BoxComponent"), name → ref |
| `ActorTools.set_parent_component` | component:ref, parent:ref — promote mesh to root (parent OMITTED = "attach to world" ERROR) |
| `ObjectTools.set_properties` | instance:ref, values:JSON-str — instance struct props apply FIRST SCALAR ONLY (#53); CDO component refs settable, runtime-instance object vars NOT |
| `ObjectTools.get_properties` | instance:ref, properties:[str] — verify QueryOnly/ECR_Overlap on FIRST profile write of a session/component-class (v3.1 tiering), not every write |
| `ActorTools.add_tag` / `has_tag` | actor:ref, tag:str |
| DSL nodes: `Actor|GetComponentbyClass(:self :ComponentClass "/Script/Engine.StaticMeshComponent")`, `Physics|SetSimulatePhysics(:self :bSimulate)`, `Game|GetPlayerPawn(:PlayerIndex 0)`, `Transformation|GetDistanceTo(:self :OtherActor)`, `Actor|ActorHasTag(:self :Tag)` |

## 4. Laws (domain)
- **G1 Overlap & trigger semantics (#10 #41 #45 #48 #51)**: blocking pairs fire Hit, NEVER BeginOverlap — trigger needs Overlap responses (#45). Overlap delivers OtherActor directly — use it as target; object-ref instance vars not settable (#48); NEVER pair with GetAllActorsOfClass+for (compiler hoists/mis-wires loop bodies) (#48). GATE overlap by tag or the PLAYER becomes the target (#51). Initial overlaps fire at play start.
- **G4 Physics activation chain (#7 #8 #35 #38 #40)**: runtime activation only; mesh must be ROOT (parent omitted = error); EventHit needs sweep on blocking root or physics notify.
- Cross-domain laws that still apply here: save-disk-verify (G3), graph-merge on rewrite (G2), param anarchy (G12) — see SKILL.md.

## 5. Recipes
| Task | Template |
|---|---|
| A touches B → B rotates (door/flip/orbit) | `templates/touch_trigger_rotation.txt` [PIE-VERIFIED] |
| Attach behavior to existing scene actor (zero-touch) | `templates/scene_watcher.txt` [PIE-VERIFIED] |
| Reliable PIE gravity | `templates/physics_runtime.txt` [PIE-VERIFIED] |

## 6. Evidence
- flip-wall 180° + orbit puzzle + sink-on-touch: user PIE-confirmed 2026-08-28.
- Open item: PhysicsAssetToolset (18 tools) untested — no PhysicsAsset found in engine content to probe with.
