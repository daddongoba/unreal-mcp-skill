# UE Blueprint Node Type Reference

UE 5.8 English locale node `type_id` strings. Use these directly in `create_node`, `write_graph_dsl`, and Python scripts.

**⚠ NAMESPACE LAW (live-verified 2026-09-06)**: the node dictionary (`node_dictionary_merged.json`) stores PALETTE DISPLAY names (`float * float`, category `Flow Control`, `To String (Integer)`) — these are NOT usable tool type_ids. Tool type_ids use compact forms (`Utilities|Operators|Multiply`, `Utilities|FlowControl|Branch`, `Utilities|String|ToString(Integer)`). When the dictionary and this file disagree, THIS FILE (live-probed) wins. The 2026-08-30 "dict-verified" round wrongly converted two tables to display forms; live probes on 2026-09-06 (UE5.8, CCC test bed) reverted them.

**Offline lookup FIRST**: for any node not in the tables below, run `scripts/search_node_dict.ps1 -Query <name>` [-Exact] — it searches the merged node dictionary + `references/node_dict_extras.json` and prints pins/defaults. Remember the namespace law: dictionary `display_name`/`category` fields may differ from tool type_ids; verify candidate ids with `find_node_types` before `create_node` when the entry came from the dictionary. Only fall back to runtime probing when offline lookup returns 0 hits.

## How to Discover Node Types

```python
# In ProgrammaticToolset Python:
types = call("find_node_types", {"graph": graph_ref, "type_id_filter": "keyword", "context_pins": []})
```

- `type_id_filter` is case-insensitive substring match against the full `type_id`
- Append `|` to list all nodes in a category: `"Math|"` lists all math nodes
- Filter results by `t.split("|")[-1] == "ExactName"` to avoid false matches
- Cross-BP nodes appear WITHOUT context (context_pins=[] works) — verified 2026-09-06

## Operators (arithmetic)

DSL syntax sugar preferred and always available: `(+ a b)` `(- a b)` `(* a b)` `(/ a b)` `(% a b)` — binary only (R3); bool NOT accepted (R4: wrap with `(select b 1.0 0.0)`).

Tool type_ids [live-probed 2026-09-06]:

| Name | type_id | Pins |
|------|---------|------|
| Add / Subtract / Multiply / Divide | `Utilities\|Operators\|Add` etc. | A, B (wildcard) → ReturnValue |
| Equal / NotEqual / Less / LessEqual / Greater / GreaterEqual | `Utilities\|Operators\|Equal(==)` `NotEqual(!=)` `Less(<)` `LessEqual(<=)` `Greater(>)` `GreaterEqual(>=)` | A, B → ReturnValue (bool) |

**Wildcard pins accept float/int but NOT bool.** Use `select` (SelectFloat node) to convert bool→float.

## Math (Math)

| Name | type_id |
|------|---------|
| MakeVector | `Math\|Vector\|MakeVector` |
| MakeVector2D | `Math\|Vector2D\|MakeVector2D` |
| BreakVector | `Math\|Vector\|BreakVector` |
| SelectFloat | `Math\|Float\|SelectFloat` (pins: A:double B:double bPickA:bool; DSL sugar `(select cond a b)` = bPickA?A:B) |
| MakeTransform | `Math\|Transform\|MakeTransform` — category is `Transform`, NOT `Transformation` |

## Transformations (conversions, `Utilities|String|ToString*`)

Full family [live-probed 2026-09-06]: `Utilities\|String\|ToString(Integer)` (pin `InInt`), `ToString(Boolean)` (pin `InBool`), `ToString(Float)`, `ToString(Object)`, `ToString(Name)`, `ToString(Vector)`, `ToString(Rotator)`, `ToString(Transform)`...
⚠ `Utilities|ToString(Integer)` (no String segment) does NOT exist — always include the category segment. Dictionary display form `To String (Integer)` (with space) also FAILS as a type_id.

## Transformation (Transformation)

| Name | type_id |
|------|---------|
| AddActorWorldOffset | `Transformation\|AddActorWorldOffset` |
| AddActorWorldRotation | `Transformation\|AddActorWorldRotation` |
| SetActorLocation | `Transformation\|SetActorLocation` |
| GetActorLocation | `Transformation\|GetActorLocation` |

## Input (Game|Player)

| Name | type_id | Notes |
|------|---------|-------|
| IsInputKeyDown | `Game\|Player\|IsInputKeyDown` | Needs PlayerController on `self` pin |
| GetPlayerController | `Game\|GetPlayerController` | Feed to IsInputKeyDown |

## Events (AddEvent)

| Name | type_id |
|------|---------|
| EventTick | `AddEvent\|EventTick` |
| EventBeginPlay | `AddEvent\|EventBeginPlay` |
| EventActorBeginOverlap | `AddEvent\|Collision\|EventActorBeginOverlap` |
| EventHit | `AddEvent\|Collision\|EventHit` |

**In DSL (Actor BPs):** use bare `EventTick` / `EventBeginPlay` — template-verified across all PIE templates (2026-08-30 cross-check; the old "use ReceiveTick override names" advice was WRONG). Collision events need the full path above (R1).

**In DSL (Widget BPs / UserWidget)** [live-verified 2026-09-06]: bare `EventTick` does NOT exist in WBP graphs — widget events need the `UserInterface|` category segment: `(event AddEvent|UserInterface|EventTick (MyGeometry InDeltaTime) ...)` plus `AddEvent|UserInterface|EventConstruct` / `EventPreConstruct` / `EventDestruct` / `EventOnInitialized`. Multi-param events list ALL params in ONE parenthesized form: `(MyGeometry InDeltaTime)` — separate forms `(MyGeometry) (InDeltaTime)` parse the second as a node call and fail.

**In code:** `add_event` historically used `"ReceiveTick"` [UNVERIFIED — prefer writing events via DSL `(event ...)` which is the verified path].

## Cross-BP node creation [live-verified 2026-09-06 — supersedes "DSL-only" belief]

BOTH paths work for creating cross-BP function-call nodes:
1. `create_node` with type_id `Class\|<BPNameNoUnderscores>\|<Func>` — WORKS, even against an uncompiled target, in Actor BP AND WBP graphs. declaring_class param is NOT needed (and does NOT make bare function names work).
2. `write_graph_dsl` with `(Class|<BPNameNoUnderscores>|<Func> :self <targetRef>)` — WORKS and wires in one shot.

Failure forms (all live-tested → "does not exist"): `Class|BP_Inventory|Func` (underscores kept — R12 stripping is MANDATORY), `BPInventory|Func` (no Class| prefix), bare `Func` + declaring_class.

**Target requirement**: cross-BP call nodes have a `self` pin typed `<TargetClass> Object Reference`; leaving it unwired fails compile with "This blueprint (self) is not a <TargetClass>_C, therefore ' Target ' must have a connection" — wire `:self` to an instance of the target class (e.g. a SpawnActor return) unless the caller BP IS the target class. Readback form: `(Class|BPInventory|GetTotalItems _returnvalue)` — positional target, no :self label.

## Function authoring (BlueprintTools) [live-verified 2026-09-06]

| Tool | Params | Note |
|------|--------|-------|
| `add_function_graph` | blueprint, graph_name | creates the function graph |
| `add_function_param` | graph, param_name, param_type, input_param:bool | input_param=false declares the RETURN value (param_name usually "ReturnValue") |
| `list_functions` / `list_graphs` | blueprint | discovery + existence guards |
| `remove_function_param` / `remove_function_graph` / `add_object_function_param` / `add_struct_function_param` | | param/graph CRUD |

Laws: (a) writing the function body via DSL needs the `(fn FuncName (params) (return x))` TOP-LEVEL wrapper even in the function's own graph — bare `(return 42)` fails "Top-level form must start with event or fn" (R14 applies). (b) The SIGNATURE return type is NOT inferred from `(return 42)` — declare it with `add_function_param(..., input_param=false)` then recompile, or call nodes show NO ReturnValue pin. (c) Same-name event rewrite via write_graph_dsl REPLACED the body in clean tests (G2's merge concern applies to failed/partial writes leaving residue — #33).

## Flow Control

DSL syntax sugar preferred: `(if ...)` `(for i (range ...))` `(while ...)` `(switch int ...)` — the compiler expands these into the nodes below.

Tool type_ids [live-probed 2026-09-06 — ALL under `Utilities|FlowControl|`, NO space; the dictionary's display category "Flow Control" is palette-only]:

| Name | type_id | Pins |
|------|---------|------|
| Branch | `Utilities\|FlowControl\|Branch` | Condition:bool=true |
| Sequence | `Utilities\|FlowControl\|Sequence` | exec only |
| ForLoop | `Utilities\|FlowControl\|ForLoop` (also `ForLoopwithBreak`) | FirstIndex/LastIndex → Index |
| WhileLoop | `Utilities\|FlowControl\|WhileLoop` | Condition:bool=true |
| Delay | `Utilities\|FlowControl\|Delay` (also `RetriggerableDelay`, `DelayUntilNextTick`, `DelayUntilNextFrame`) | WorldContextObject Duration:float LatentInfo |
| Switch on Int / Name / String | `Utilities\|FlowControl\|Switch\|SwitchonInt` (lowercase 'on'; same for SwitchonName/SwitchonString) | Selection |
| DoOnce / DoN / FlipFlop / Gate / MultiGate | `Utilities\|FlowControl\|DoOnce` etc. | |

## Development

| Name | type_id |
|------|---------|
| PrintString | `Development\|PrintString` (pin `InString`) |

## Pin Type Names (English)

| Type | type_id field |
|------|---------------|
| Exec | exec |
| Bool | bool |
| Float | float |
| Double | double |
| Int | int |
| String | string |
| Vector | Vector |
| Rotator | Rotator |
| Transform | Transform |
| Wildcard | wildcard |
| Object ref | object |
| Key | Key |

## Common Pin Names

### Event nodes (Tick, BeginPlay)
- Output: `then` (exec), `DeltaSeconds` (float, Actor Tick only; widget Tick outputs `MyGeometry` + `InDeltaTime`)

### Function call nodes
- Input: `execute` (exec), `self`/`Target` (object ref), data pins...
- Output: `then` (exec), `ReturnValue` (data)

### Operator nodes (Add, Subtract, Multiply)
- Input: `A`, `B` (wildcard)
- Output: `ReturnValue`

### IsInputKeyDown
- Input: `self` (PlayerController ref), `Key` (Key struct)
- Output: `ReturnValue` (bool)
