# UE Development Conventions (design-time knowledge base)

> Purpose: the API dictionaries answer "what exists"; this file answers "what to choose and why".
> Confidence tags per SKILL.md protocol: `[VERIFIED <date> UE<ver>-<lang>]` / `[DOC]` (transcribed from engine docs, not battle-tested) / `[UNVERIFIED]`.
> Growth rule: user corrections and PIE-verified lessons get promoted here, cross-referencing SKILL.md pitfall IDs.
> **Consult BEFORE any design decision involving runtime behavior** (collision / events / physics / input / animation).

## 1. Component Selection (what to use for what)

| Need | Correct component | Why / gotchas |
|---|---|---|
| Touch / area trigger | **BoxComponent / SphereComponent / CapsuleComponent** (ShapeComponent family) via `ActorTools.add_component(component_type="/Script/Engine.BoxComponent")` | No rendering cost; "Trigger" profile applies cleanly (QueryOnly + Overlap responses); that's what they exist for. NEVER a mesh cube as trigger (SKILL#41). `[VERIFIED 2026-08-28 UE5.8-EN]` |
| Visible solid / physics body | StaticMeshComponent — **promoted to ROOT** | Physics & sweep act on the root; child mesh + SetSimulatePhysics = frozen actor (SKILL#40). `[VERIFIED 2026-08-28 UE5.8-EN]` |
| Invisible anchor / attach point | SceneComponent | Zero-cost transform holder. `[DOC]` |
| Playable character | Character class (capsule + CharacterMovementComponent) | Built-in movement modes, input consumption, camera support. `[DOC]` |
| Camera rig | SpringArmComponent + CameraComponent | Third-person lag, collision probe. `[DOC]` |
| In-world text | TextRenderComponent | `[DOC]` |
| Attached sound | AudioComponent | `[DOC]` |
| Editor-only marker | BillboardComponent | `[DOC]` |

## 2. Collision & Event Semantics (what fires what)

### Overlap events (EventActorBeginOverlap / OnComponentBeginOverlap)
- Fire when: both sides are collision-enabled for **queries** (QueryOnly or QueryAndPhysics), the pair is **not mutually blocking**, and **at least one side has bGenerateOverlapEvents=true** (the event delivers through that side). `[DOC]`
- **Mutually BLOCKING pairs never generate overlap events** — they resolve penetration and report Hit instead (SKILL#45). Symptom: object rests on the "trigger" and nothing happens. `[DOC]`
- Initial overlaps (actor spawned inside a trigger) fire at play start — gate one-shot logic with a bool flag. `[DOC]`

### Hit events (EventHit)
- Sweep path: movement node with `bSweep=true` on a blocking ROOT → Hit per blocking contact. `[VERIFIED via projectile template]`
- Physics path: `bNotifyRigidBodyCollision=true` (at least one side) + collision includes physics. `[DOC]`

### collisionEnabled states
`NoCollision` / `QueryOnly` (traces + overlaps only, no physics resolution) / `PhysicsOnly` / `QueryAndPhysics`. `[DOC]`

### Per-channel responses
`Ignore` / `Overlap` (touch without block) / `Block`. A profile = objectType + enabled-state + response matrix preset. `[DOC]`

### Stock profile names (all that exist)
BlockAll, BlockAllDynamic, OverlapAll, OverlapAllDynamic, PhysicsActor, Trigger, Pawn, NoCollision, Destructible, CharacterMesh, Vehicle...
- **"TriggerOnly" does NOT exist** — writing it is a silent no-op. `[VERIFIED 2026-08-28]`
- Profile application via `set_properties` is unreliable on StaticMeshComponent (silently fails for Trigger-family) but works on BoxComponent — **always read back and verify** (SKILL#41). `[VERIFIED 2026-08-28 UE5.8-EN]`

## 3. Physics Activation
- Editor-time property setting is unreliable → runtime activation: `BeginPlay → GetComponentbyClass → SetSimulatePhysics(true)` (physics_runtime.txt). `[VERIFIED 2026-08-24 UE5.8-EN]`
- Physics only moves the actor when the simulating mesh is the **ROOT** component (SKILL#40). `[VERIFIED 2026-08-28 UE5.8-EN]`
- Prerequisites: Movable mobility + physics-enabled collision + non-zero mass. `[DOC]`

## 4. Interaction Patterns (mini design recipes)

| Pattern | Recipe |
|---|---|
| A touches B → B reacts | BoxComponent trigger on B (Trigger profile + bGenerateOverlapEvents) → EventActorBeginOverlap → set bool flag → Tick handles the animation. One-shot: gate with the flag. `[VERIFIED 2026-08-28 UE5.8-EN — PIE user-confirmed, template touch_trigger_rotation.txt]` |
| Attach behavior to an actor in an EXISTING scene (zero-touch) | Invisible watcher BP near the target: tag the target, sense-box overlap arms ONLY on the tag, settle-detector waits out physics falling, PROXIMITY to player = touch (flying pawn can't push). Effect acts on TargetActor only. `[VERIFIED 2026-08-28 UE5.8-EN — PIE user-confirmed, template scene_watcher.txt]` |
| Slow rotation / move to target | Tick + RInterpTo / FInterpTo (InterpSpeed 1–3 ≈ 1–3 s settle). Timeline = richer curves, editor-friendly, but more graph plumbing. `[VERIFIED 2026-08-28 PIE user-confirmed]` |
| Orbiting satellites around a pivot | ALL pivot-coincident components (center box, switch, trigger) sit at the rotation center — self-symmetric, so rotating the whole ACTOR leaves them visually static; only satellites appear to orbit. No per-box math. `[VERIFIED 2026-08-28 UE5.8-EN — PIE user-confirmed]` |
| Driver / test object | Physics cube (ROOT, PhysicsActor profile, runtime activation), dropped above the trigger zone. `[VERIFIED 2026-08-24 UE5.8-EN; re-confirmed 2026-08-28]` |
| Impact reaction | Hit event + ApplyImpulse. `[DOC]` |
| Continuous proximity check | Tick + line/sphere trace (DrawDebug* for human inspection). `[DOC]` |

## 5. Design-time Protocol (mandatory)

1. Any design involving collision / events / physics / input → **check sections 1–4 first**.
2. Needed entry missing → fetch official UE docs (web) BEFORE building; do not rely on model memory alone.
3. Runtime-behavior-sensitive feature → state the one-line design (component + event + why) to the user before building.
4. New verified lesson → promote into the relevant section (with tag) and cross-ref the SKILL.md pitfall ID; user corrections take priority over model priors.

## 6. Performance rails (web-researched 2026-09-06, gap-fill after TestT1 case)

- **GAOC cost**: `GetAllActorsOfClass` iterates ALL actors in the world (official node warning: DO NOT use every frame). Correct usage: call ONCE at BeginPlay/level-load and cache the array; runtime-spawned actors should self-register (pub-sub) instead of re-scanning; single-instance lookups use `GetActorOfClass` (non-plural). `[DOC — Epic docs + Epic Myth-Busting video + forum consensus; our R27 usage is event-driven (overlap/BeginPlay) = compliant]`
- **Tick-driven UI refresh = antipattern** (TestT1 P5): pulling a value every frame to push into a widget wastes cycles and couples systems. Event-driven alternatives: (a) call the widget's update fn directly inside the mutating function (AddItem → UpdateCount), or (b) Event Dispatcher: owner broadcasts `OnXxxChanged`, widget binds at Construct and refreshes on broadcast. `[DOC — community-verified dispatcher pattern; MCP tools: add_event_dispatcher / list_event_dispatchers exist, path UNVERIFIED]`
- Light per-frame logic in Tick is tolerable for tiny games, but replace with timers/events when checks are world-scans or UI pushes. `[DOC]`

## 7. Widget lifecycle & refresh timing (web-researched 2026-09-06)

| Event | When it runs | Safe for |
|---|---|---|
| `PreConstruct(IsDesignTime)` | editor AND game (design-time previews too) | COSMETIC-ONLY, locally-owned data — Epic official WARNING: cannot safely access game state; gate with IsDesignTime |
| `Construct` | runtime only (≈ BeginPlay for widgets) | delegate bindings, game-state reads, initial refresh |
- Standard chain: `CreateWidget(:Class="WBP_C")` → store ref → `AddtoViewport` → mutate data → push update (fn call or dispatcher). Never read game state in PreConstruct. `[DOC — Epic UUserWidget::PreConstruct page + community]`

## 8. Overlap event granularity (web-researched 2026-09-06 + live readback)

- **Actor-level** (`AddEvent|Collision|EventActorBeginOverlap`): aggregates ANY component's overlap — simplest for single-collider actors (all verified templates).
- **Component-level** (`OnComponentBeginOverlap(<CompName>)`): per-component semantics — when an actor has multiple colliders that must behave differently (TestT1 BP_Pickup: PickupMesh-only overlap). Readback DSL form: `(event OnComponentBeginOverlap(PickupMesh) (OverlappedComponent OtherActor OtherComp OtherBodyIndex bFromSweep SweepResult))` — CREATION via this DSL form or `add_component_bound_event` tool is UNVERIFIED (V4 open item); the live node existed (K2Node_ComponentBoundEvent_0). `[DOC Epic community tutorial + live artifact]`

## 9. Map accumulate idiom (from TestT1 AddItem live body + [DOC] Map docs)

```scheme
(fn AddItem (ItemName Count)
  (Utilities|Map|Add (Variables|Default|GetItems) ItemName
    (+ (Utilities|Map|Find (Variables|Default|GetItems) ItemName) Count))
  (Variables|Default|SetTotalCollected (+ (Variables|Default|GetTotalCollected) Count))
  (return))
```
- Works because `Map|Find` returns the value-type's ZERO-VALUE when the key is missing (bFound=false output) — so `Find + Count` is a safe first-insert increment. `[DOC — UE Map behavior; pattern readback-verified live 2026-09-06 in TestT1]`
- Parallel scalar accumulator (TotalCollected) keeps the UI stat cheap (no Map iteration).

## 10. Chinese-editor display-name localization (web-researched 2026-09-06 — G17 root-cause)

- Engine standard palette categories ARE localized in zh editors (Utilities→工具 — Epic's localization pipeline translates marked engine strings; UFUNCTION Category metadata mostly stays English). This is why Cast ids (palette-resolved) break in zh editors while function-node ids (registry-resolved) survive — see G17.
- **Fix at the source**: the editor has separate localization toggles for BLUEPRINT display names (Editor Preferences) — turning them off forces English node/category names; the `culture = en` console command does NOT affect blueprint function display names. `[DOC — newsn.net UE5 tutorial; Epic CJK localization blog]`
- zh-environment defensive patterns: prefer locale-independent paths — R27 typed-source (GAOC), `Class|<NoUnderscores>|<Func>` calls, function-registry ids; avoid the Cast family unless the id is confirmed live.
