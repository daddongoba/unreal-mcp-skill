# Changelog

All notable changes to this skill. Format: one version block per batch; the authoritative
state lives in SKILL.md → Current state.

## v3.12.0 (2026-09-11)
- **Project-open intake law**: user gives project link/name → resolve → ONE confirmation
  round with full pre-flight (path, engine, plugin audit, UE-running state; doubles as
  --fix-plugins consent) → only then launch. Never raw-shell spawn.

## v3.11.0 (2026-09-11)
- **One-Click Connect**: `scripts/ue_connect.py` (check / launch / wait / all).
  Read-only diagnosis of UE process, port-8000-vs-real-/mcp, ghost port listeners,
  .uproject plugin audit; detached launch; progress-printing wait; state cached.
  E2E-verified live: caught a real ghost process on port 8000 → launch → 289s →
  67 toolsets → all-mode reconnect 1s.
- few_shots #4 rewritten around the script.

## v3.10.0 (2026-09-11)
- **macOS twin**: cross-platform Python script twins (search_node_dict / mcp_call /
  refresh_schemas, stdlib only, BOM-safe) + `references/platform-macos.md` with §0
  platform-detection dispatch. Behavior parity with ps1 twins verified on Windows.

## v3.9.0 (2026-09-06)
- **TestT1 forensics case study** (`references/history/case_testT1_inventory.md`):
  live reconstruction of a real inventory/pickup mini-game — 7 evidence-backed
  problems (dead-cast residue, GAOC class=0, same-name call drift, CreateWidget
  Class=0, Tick-refresh antipattern, readback casing) each mapped to a fix law.
- **Web-researched gap-fill** (ue_conventions §6-§10): GAOC performance rails,
  event-driven UI refresh, widget lifecycle, overlap granularity, Map accumulate
  idiom, zh-editor display-name localization root cause. All tagged [DOC].

## v3.8.0 (2026-09-06)
- **G17 Cast-family trap**: project-BP cast ids KEEP underscores
  (CastToBP_Inventory — opposite of the cross-BP rule); locale layer (工具|Casting|)
  documented; **R27 typed-source-over-Cast pattern** (GAOC typed output) PIE-verified.

## v3.7.0 (2026-09-06)
- **G16 cross-BP battery**: create_node DOES create cross-BP nodes (naming-form
  failures were the cause); dictionary display_name ≠ tool type_id (two wrongly
  "fixed" tables reverted); R24 function signatures, R25 multi-param one-list,
  R26 target wiring, `AddEvent|UserInterface|` widget events. PIE end-to-end "42".

## v3.6.0 (2026-08-30)
- Correctness audit round: node dictionary made searchable (search_node_dict.ps1 +
  node_dict_extras.json); node_types.md contradictions fixed; refresh_schemas.ps1
  offline cross-check; verification hard rail (non-verbatim DSL write → readback
  mandatory); idempotency guards table restored.

## v3.3.0 (2026-08-29)
- Layered slim-down (35.4KB → ~14KB), capability-domain architecture (11 docs +
  router), compatibility.md weak-model fallback.

## ≤ v3.2 (2026-08-22 .. 2026-08-29)
- Origin: T1-T9 capability test rounds (58 tests), 17 verified templates, pitfall
  lawbook G1-G15, P1-P53 incident archive, AllToolsets 67-toolset survey.
