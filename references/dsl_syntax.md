# Blueprint DSL Syntax Reference

> Verified against UE5.8 English locale, 2026-08-22; live re-verified rules R1/R24/R25/R26 on 2026-09-06 (CCC test bed).
> Full official grammar: call `BlueprintTools.get_graph_dsl_docs` (runtime, always current).
> ⚠ **One known error in those engine docs** `[VERIFIED 2026-09-24 UE5.8.3-EN]`: its SWITCH ALIASES
> section claims `int → Utilities|FlowControl|SwitchOnInt`, but that id does not exist — the live id is
> `Utilities|FlowControl|Switch|SwitchonInt` (see node_types.md). The `(switch int …)` alias itself is
> fine; only the hand-written full type_id fails. Also note `get_graph_dsl_docs` omits `;` comments,
> the deprecated `(neg expr)` alias, and the `(bind var (NodeType…))` form for naming multi-exec outputs.

## 1. Core Grammar Cheat Sheet

```
(event EventName (Params...) stmts...)     ; event entry point
(fn FuncName (Params...) stmts...)         ; function graph
(bind var expr)                            ; bind node output to var
(exec (NodeType|Id args...))               ; exec node (no output used)
(return) (return expr) (return e1 e2)      ; function returns
(if cond stmts [elif/else])                ; branch
(for i (range stop) stmts)                 ; loop
(for i (range start stop) stmts)
(for elem arrayExpr stmts)                 ; foreach
(while cond stmts)
(switch int value (:Case stmts)...)        ; int/string/name aliases
(break)
```

**Multi-exec (latent) nodes** — named exec outputs as continuations:

```
(NodeType|Id dataArgs...
  (:ExecOut1 stmts...)
  (:ExecOut2 stmts...))
; Pin names with spaces: (:"Is Valid" stmts...)
; Data outputs inside continuations: _prefixed lowercase pin name, e.g. _return_value
```

**Expressions**:

```
literals:  1  3.14  "text"  true  false
operators: (+ a b) (- a b) (* a b) (/ a b) (% a b)   ; ALL binary only
compare:   (== a b) (!= a b) (< a b) (<= a b) (> a b) (>= a b)
boolean:   (and a b) (or a b) (xor a b) (not e)
ternary:   (select cond a b)
vector:    (.x v) (.y v) (.z v)
rotator:   (.pitch r) (.yaw r) (.roll r)
transform: (.location t) (.rotation t) (.scale t)
node call: (Type|Id posArgs... :PinName val ...)
variable:  (Variables|Default|GetVarName)  /  (Variables|Default|SetVarName value)
self:      self  (auto-bound in event/fn bodies)
```

## 2. Verified Rules (battle-tested, sorted)

| # | Rule | Detail |
|---|------|--------|
| R1 | Event names | `EventTick`, `EventBeginPlay` work bare (Actor BPs). Collision events need full path: `AddEvent\|Collision\|EventHit`, `AddEvent\|Collision\|EventActorBeginOverlap`. WIDGET (UserWidget) events need `AddEvent\|UserInterface\|` segment: bare `EventTick` FAILS in WBP graphs — use `AddEvent\|UserInterface\|EventTick` (also EventConstruct/EventPreConstruct/EventDestruct/EventOnInitialized) [VERIFIED 2026-09-06] |
| R2 | Keyboard/mouse events | `(event ...)` CANNOT create them (auto `AddEvent\|` prefix breaks). Use `create_node` tool with `Input\|KeyboardEvents\|SpaceBar`, then wire pins via Python script |
| R3 | Arithmetic is binary | `(* a b c)` → error. Nest or bind: `(bind speed (* a b))` then `(* x speed)` |
| R4 | Bool cannot enter operators | Wildcard pins reject bool. Convert: `(select boolVal 1.0 0.0)` |
| R5 | Class/asset/enum strings need quotes | `"/Script/Engine.Actor"`, `"AlwaysSpawn"`, `"/Game/BP_X.BP_X_C"` — unquoted words are variable refs |
| R6 | IsInputKeyDown `self` = PlayerController | Bind `(bind pc (Game\|GetPlayerController :PlayerIndex 0))` first; GetPlayerController has NO `self` pin |
| R7 | SpawnActor Class pin | generated class path with `_C`: `"/Game/BP_Projectile.BP_Projectile_C"` |
| R8 | MakeTransform type_id | `Math\|Transform\|MakeTransform` — run `find_node_types` before hardcoding any type_id |
| R9 | Sweep collision needs root mesh | `AddActorWorldOffset :bSweep true` only collides via Root Component (see Pitfall #7) |
| R10 | `bind` once, reuse everywhere | Repeating same node call = duplicate nodes = double execution (impure fns give different values) |
| R11 | PIE instances | `/Memory/UEDPIE_N_...` prefix paths; find_actors DURING PIE returns them; use for live transform reads |
| R12 | Cross-BP member ids | `Class\|<NameNoUnderscores>\|<Func/Var>` (BP_GridGameMode→BPGridGameMode); same-BP call `(BP_C\|Func)` |
| R13 | bool var b-prefix stripped | bOpening→GetOpening/SetOpening nodes |
| R14 | Top-level = event/fn only | no bare bind/node forms; input-key nodes via create_node |
| R15 | Cast outputs = "As Name" with spaces | get_node_infos first; Object pin needs typed source before compile. Cast NODE id KEEPS underscores: `Utilities\|Casting\|CastToBP_Inventory` — OPPOSITE of R12's stripping (stripped `CastToBPInventory` fails "does not exist", EN-locale verified 2026-09-06). Cast category may localize in Chinese editors (工具\|Casting\|...) while function-node categories stay English — in zh editors avoid Cast entirely via R27. |
| R16 | UMG runtime | CreateWidget pin=`Class`; AddToViewport = `UserInterface\|Viewport\|AddtoViewport` |
| R17 | RInterpTo takes Rotators | wrap floats: MakeRotator(:Yaw v) → RInterpTo → (.yaw result) back |
| R18 | Terrain check before placement | trace_world(start high, end low) → OpenWorld landscape can bury actors (z≈450!) |
| R19 | Engine base classes = dead ends | DataAsset & SaveGame: base classes instantiate/compile but FAIL at runtime; always create BP subclass first, reference with `_C` |
| R20 | Conversion node pins are inconsistent | ToString(Boolean)=InBool, ToString(Integer)=InInt, IsValid=InputObject — always get_node_type_pins first |
| R21 | Spawnable Class must be real | "/Script/Engine.StaticMeshActor" OK; "/Engine/EngineBlueprintResources/StandardAssetCube.StandardAssetCube_C" fails ("Class must be specified") |
| R22 | SaveGame nodes under `SaveGame\|` | CreateSaveGameObject/SaveGametoSlot/LoadGamefromSlot/DoesSaveGameExist — category is SaveGame not Game |
| R23 | Runtime physics activation | BeginPlay: `Actor\|GetComponentbyClass(:ComponentClass "/Script/Engine.StaticMeshComponent")` → `Physics\|SetSimulatePhysics(:bSimulate true)` — 100% reliable in PIE (P38; supersedes editor-flag approach) |
| R24 | Function authoring signature | Body needs top-level `(fn FuncName (params) (return x))` wrapper even in the function's own graph — bare `(return x)` fails (R14 applies). The return TYPE is NOT inferred: declare via `add_function_param(graph, "ReturnValue", type, input_param=false)` then recompile — else call nodes show NO ReturnValue pin. [VERIFIED 2026-09-06 UE5.8-EN] |
| R25 | Multi-param events = ONE list | `(event AddEvent\|UserInterface\|EventTick (MyGeometry InDeltaTime) ...)` — ALL params in ONE parenthesized form. Separate forms `(A) (B)` parse the second as a node call → "B does not exist". [VERIFIED 2026-09-06] |
| R26 | Cross-BP target required | `(Class\|<NameNoUnderscores>\|<Func> :self <targetRef>)` — the self/Target pin is typed `<TargetClass> Object Reference` and MUST be wired (e.g. a SpawnActor return) unless the caller IS the target class; unwired → compile error "This blueprint (self) is not a <TargetClass>_C, therefore ' Target ' must have a connection." Readback prints it positionally: `(Class\|BPInventory\|GetTotalItems _returnvalue)`. create_node with the same id ALSO works (Actor + WBP graphs, uncompiled targets OK); declaring_class is NOT needed and does NOT rescue bare function names. [VERIFIED 2026-09-06 UE5.8-EN, PIE-confirmed returned 42] |
| R27 | Typed-source over Cast (GAOC pattern) | Generic nodes with a Class pin produce TYPED outputs that follow it: `(bind arr (Actor\|GetAllActorsOfClass :ActorClass "/Game/.../BP_Inventory.BP_Inventory_C"))` outputs a BP_Inventory_C array → `(for elem arr ... (Class\|BPInventory\|GetTotalItems :self elem) ...)` — NO Cast node needed. Prefer for scene scans (also `Actor\|GetAllActorsOfClasswithTag`); call nodes in loop bodies are safe (G6 hoisting hits pure nodes only). Avoids the Cast family's inverted underscore rule (R15) AND its locale-sensitive category. [VERIFIED 2026-09-06 UE5.8-EN — PIE printed 42 per found instance] |

## 3. Verified Examples

### 3.1 PrintString (minimal)

```scheme
(event EventBeginPlay
  (Development|PrintString :InString "Game Started"))
```

### 3.2 WASD Movement (variable + input + vector)

Requires: `MoveSpeed` float variable (instance editable).

```scheme
(event EventTick (DeltaSeconds)
  (bind dt (* DeltaSeconds (Variables|Default|GetMoveSpeed)))
  (bind pc (Game|GetPlayerController :PlayerIndex 0))
  (bind wDown (Game|Player|IsInputKeyDown :self pc :Key "W"))
  (bind sDown (Game|Player|IsInputKeyDown :self pc :Key "S"))
  (bind aDown (Game|Player|IsInputKeyDown :self pc :Key "A"))
  (bind dDown (Game|Player|IsInputKeyDown :self pc :Key "D"))
  (bind moveX (* (- (select dDown 1.0 0.0) (select aDown 1.0 0.0)) dt))
  (bind moveY (* (- (select wDown 1.0 0.0) (select sDown 1.0 0.0)) dt))
  (bind moveVec (Math|Vector|MakeVector :X moveX :Y moveY :Z 0.0))
  (Transformation|AddActorWorldOffset :DeltaLocation moveVec))
```

### 3.3 Projectile: fly forward + destroy on wall hit

Requires: sphere mesh component promoted to ROOT, `collisionProfileName="BlockAll"`, `bNotifyRigidBodyCollision=true`.

```scheme
(event EventBeginPlay
  (Development|PrintString :InString "Bullet Fired"))

(event EventTick (DeltaSeconds)
  (bind fwd (Transformation|GetActorForwardVector))
  (bind speed (* 3000.0 DeltaSeconds))
  (bind moveVec (Math|Vector|MakeVector :X (* (.x fwd) speed) :Y (* (.y fwd) speed) :Z (* (.z fwd) speed)))
  (Transformation|AddActorWorldOffset :DeltaLocation moveVec :bSweep true :bTeleport false))

(event AddEvent|Collision|EventHit
  (Actor|DestroyActor :self self))
```

### 3.4 EnableInput in BeginPlay (for non-Pawn actors)

```scheme
(event EventBeginPlay
  (bind pc (Game|GetPlayerController :PlayerIndex 0))
  (Input|EnableInput :self self :PlayerController pc))
```

### 3.5 SpawnActor from class (shooter pattern)

Keyboard event node must be pre-created via `create_node` (`Input|KeyboardEvents|SpaceBar`), then wire via Python:

```python
# ProgrammaticToolset script (see scripts/bp_template.py helpers)
spawn = create_node(graph_ref, "Game|SpawnActorfromClass", x=900, y=0)
set_pin_value(get_pin(oi["input_pins"], "Class"), "/Game/BP_Projectile.BP_Projectile_C")
set_pin_value(get_pin(oi["input_pins"], "CollisionHandlingOverride"), "AlwaysSpawn")
# connect: GetActorLocation -> MakeTransform.Location, GetActorRotation -> .Rotation,
#          MakeTransform -> SpawnActor.SpawnTransform, SpaceBar.Pressed -> SpawnActor.execute
```

DSL-equivalent for the spawn logic (without the keyboard entry):

```scheme
(bind loc (Transformation|GetActorLocation))
(bind rot (Transformation|GetActorRotation))
(bind tf (Math|Transform|MakeTransform :Location loc :Rotation rot))
(Game|SpawnActorfromClass
  :Class "/Game/BP_Projectile.BP_Projectile_C"
  :SpawnTransform tf
  :CollisionHandlingOverride "AlwaysSpawn")
```

### 3.6 Branch + loop

```scheme
(event EventTick (DeltaSeconds)
  (bind loc (Transformation|GetActorLocation))
  (if (> (.z loc) 100.0)
    (for i (range 5)
      (Development|PrintString :InString "high"))))
```

## 4. Error → Fix Lookup

| Error message | Cause | Fix |
|---------------|-------|-----|
| `Unknown input pin "X" on NodeType` | wrong pin name | check node dictionary JSON / `get_node_type_pins`; e.g. `Player`→`self` |
| `(* ...) requires exactly 2 arguments, got 3` | chained arithmetic | R3: nest or bind intermediate |
| `The node could not be created / X does not exist` | wrong type_id or event path | `find_node_types` first; collision events need `AddEvent\|Collision\|` prefix (R1) |
| `Could not connect pin X to Y. incompatible types` | type mismatch (bool→wildcard, Actor→PlayerController) | R4 select conversion; R6 GetPlayerController |
| `X is not valid EdGraph for property 'graph'` | graph path wrong | use `BP.BP:EventGraph` (Pitfall #5); wrong project open? check `get_current_level` |
| `AddEvent\|Input\|KeyboardEvents\|... does not exist` | DSL can't create input-key events | R2: `create_node` tool instead |
| Blueprint compiles but nothing happens at runtime | missing EnableInput / root not mesh / sweep off | Pitfalls #7 #8 #9 |
| `Toolset 'X' not found` | plugin not enabled in .uproject | add ToolsetRegistry/EditorToolset/PythonScriptPlugin (see Prerequisites) |
