# Case Study: TestT1 — Inventory/Pickup chain (CCC, 2026-09-06 live forensics)

> A real-world failure-and-repair case, forensically reconstructed from live readbacks of
> `/Game/TestT1/*` (BP_Inventory / BP_Pickup / WBP_InventoryUI) in the CCC test bed.
> Every "problem" below is backed by an actual graph artifact; every "fix" maps to a law
> verified the same day (G16/G17/R24-R27). Use this as the reference example when a
> cross-BP + widget + scene-scan feature misbehaves.

## 1. Background — two generations of TestT1

- **Generation 1 (2026-08-22/24, historical)**: `BP_T11_Complex` — 307-node DSL stress sample
  (single write_graph_dsl + compile + save; variables ×10 types, function graphs, elif chains,
  nested for, bool→select). Proved the DSL pipeline scales; asset since deleted.
- **Generation 2 (current)**: a real mini-game — pickups collected into an inventory with a
  live UI count (`BP_Inventory` + `BP_Pickup` + `WBP_InventoryUI` + NewMap). Built across
  sessions including the user's reports that triggered the G16/G17 investigations.

## 2. The intended architecture (as-built, from function bodies)

```
BP_Pickup (OverlapAll on PickupMesh child SMC)
  └─ OnComponentBeginOverlap(PickupMesh)
      → find the BP_Inventory instance in the level
      → call BP_Inventory.AddItem("宝石", 1)          [Map accumulate + TotalCollected += Count]
      → DestroyActor (pickup disappears)

BP_Inventory (BeginPlay)
  → CreateWidget(WBP_InventoryUI) → store InvUIRef → AddToViewport
  (EventTick)
  → GetTotalCollected → InvUIRef.UpdateCount(total)   [cross-BP call into widget fn]

WBP_InventoryUI.UpdateCount(Count)
  → CountText.SetText(ToText(Count))                  [Variables|WBP_InventoryUI|GetCountText]
```

Verified GOOD parts (user/agent authored, readback-confirmed):
- `(fn AddItem (ItemName Count)` — Map|Add + Map|Find increment + SetTotalCollected: **correct accumulate idiom**
- `(fn UpdateCount (Count)` — `Widget|SetText(Text)` + `Utilities|Text|ToText(Integer)`: **correct widget fn**
- BP_Inventory Tick's cross-BP call `|UpdateCount (Variables|Default|GetInvUIRef) _total`: **positional target form matches R26 readback** — this is the "WBP Tick calling" chain from the user report, mechanism now fully recorded (G16)
- WBP events `AddEvent|UserInterface|EventPreConstruct/EventConstruct` present — the R1/R25 widget event path, already landed

## 3. Problems found in the live graphs (with artifacts)

| # | Symptom artifact (readback) | Root cause | Fix (law) |
|---|---|---|---|
| P1 | `(bind _asbp_inventory (Utilities\|Casting\|Badcastnode (Utilities\|Array\|Get(acopy) _outactors)))` — a DEAD cast node ("Badcastnode") left in the chain | Cast creation failed in an earlier session (wrong id form / locale), half-built node persisted (G2 #33 residue) | **Avoid the cast entirely**: GAOC typed output → for-each elem feeds `Class\|BPInventory\|AddItem :self elem` directly (R27); or use underscore-kept `CastToBP_Inventory` (R15) |
| P2 | `(Actor\|GetAllActorsOfClass 0)` — ActorClass pin literal **0**, not a class path | Cross-BP class params need quoted `"/Game/.../BP_Inventory.BP_Inventory_C"` (R5); a bare/wrong arg serialized as 0 | Quote + `_C` suffix; and per R26 the GAOC output type only follows a correctly-set ActorClass |
| P3 | `(ListView\|AddItem _asbp_inventory "宝石" 1)` — the call resolved to **UMG ListView.AddItem** instead of BP_Inventory.AddItem | Wrong type_id namespace: the intended cross-BP call should be `Class\|BPInventory\|AddItem` (R12); a name-only lookup drifted into the widget toolset's same-named function | Always use the full `Class\|<NameNoUnderscores>\|<Func>` form for cross-BP calls — same-name collisions across toolsets are real (this case proves it) |
| P4 | `(bind _returnvalue (UserInterface\|CreateWidget 0 (Game\|GetPlayerController 0)))` — CreateWidget **Class pin = 0** (unwired literal) | Class pin wants `"/Game/TestT1/WBP_InventoryUI.WBP_InventoryUI_C"` (R16: pin is `Class`, `_C` suffix); leaving it 0 breaks the whole UI reference chain silently | Wire the quoted WBP `_C` path; verify with get_node_infos after write |
| P5 | BP_Inventory **EventTick** pulls GetTotalCollected and calls UpdateCount every frame | Tick-driven UI refresh = performance antipattern; should be event-driven (call UpdateCount inside AddItem, or event dispatcher) | Event-driven refresh pattern (see case-lessons below, [DOC]-grade) |
| P6 | PickupMesh is a **child StaticMeshComponent** doing overlap duty with runtime `Collision\|SetCollisionProfileName "OverlapAll"` | Distinct from the #41 trap: #41 is about EDITOR `set_properties` silently failing profiles on SMC — a RUNTIME SetCollisionProfileName node is a different path (R23 analogy: runtime nodes reliable) [UNVERIFIED by PIE in this case] | For pickups (visible, no physics response needed) mesh-as-overlap-source is acceptable; use component-level `OnComponentBeginOverlap(PickupMesh)` bound event (exists here: K2Node_ComponentBoundEvent_0) |
| P7 | readback shows `UserInterface\|Viewport\|AddToViewport` (capital T) while the registered id is `AddtoViewport` (lowercase t — probe-confirmed both spellings resolve to it) | Readback prints display-styled casing; registered id is lowercase-t | **Readback comparisons must be case-insensitive** — extend G2 verification practice (new rule detail) |

Bonus morphology finding: widget's own component variable getter appeared as `Variables|WBP_InventoryUI|GetCountText` — the `Variables|<OwnBPName>|GetVar` form (vs `Variables|Default|GetVar` used in Actor templates). Both parse; record both as valid.

## 4. Verified-solutions map (what the 2026-09-06 battery proved, keyed to this case)

| Case problem | Verified solution | Where encoded |
|---|---|---|
| P1 dead Cast | GAOC typed output feeds calls without any Cast; PIE-printed 42 per found instance | G17, R27, extras GAOC entry |
| P2 GAOC class=0 | quoted `_C` class paths; GAOC typed output verified end-to-end | R5, R27 |
| P3 wrong AddItem | full `Class\|BPInventory\|AddItem` form + :self target; create_node AND DSL both work | G16, R26, R12 |
| P4 CreateWidget 0 | Class pin = quoted WBP `_C` path (umg_basic template) | R16/#30 |
| "mechanism unrecorded" | readback shows cross-BP call as positional `(Func target)`; node stores bare `|FuncName` type_id | G16 |
| WBP event creation | `AddEvent\|UserInterface\|` prefix + single-list multi-params | R1, R25 |
| function return values | add_function_param(input_param=false) — GetTotalCollected's return feeds UpdateCount only if signature declared | R24 |

## 5. Open items (UNVERIFIED — next PIE pass on NewMap should check)

- V1: runtime `SetCollisionProfileName` on a child SMC actually enables overlap in PIE (P6 claim)
- V2: whether the full repaired chain (GAOC→AddItem→UpdateCount) reaches the UI in PIE — requires CreateWidget Class fix (P4) first
- V3: `Variables|<OwnBPName>|GetVar` vs `Variables|Default|GetVar` equivalence matrix (both seen live; Default = category placeholder, BPName = explicit)
- V4: component-bound event creation via `add_component_bound_event` tool (the K2Node_ComponentBoundEvent_0 here was hand-made or GUI-made — tool path untested)

## 6. Teaching value (why this case is the canonical reference)

One real mini-game touches: child-component overlap source (P6), runtime collision profile
setting, GAOC scene scan (P2), cast pitfalls (P1), cross-BP same-name collisions (P3),
widget creation+refresh chain (P4/P5), cross-BP function signatures (S4), widget event
namespaces (R25), and readback casing normalization (P7). When any part of a
"scene → logic → UI" feature fails, start from this case's problem table.
