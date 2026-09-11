# Capability: env-session
> toolsets: EditorAppToolset / LogsToolset / SlateInspectorToolset / ConfigSettingsToolset / AutomationTestToolset | status: DEEP-VERIFIED (rescue + forensics) | 2026-08-29 UE5.8-EN
> Routing: any task about UE startup, MCP connectivity, stuck dialogs, log reading, console, PIE control, screenshots, viewport camera, session diagnostics.

## 1. Boundaries
- CAN: PIE start/stop/status, viewport capture + camera transforms, actor/asset selection, console var search, log reading (all categories + regex patterns + verbosity control), native-window rescue (PostMessage), Slate UI automation (Click/FillForm/PressKey/Hover/Drag), config section reads, automation test discovery.
- CANNOT: executing arbitrary console commands via toolset (no exec tool — Output-Log-drawer UI route exists but fragile), synthetic cursor clicks on UE modals (ignored — use PostMessage).

## 2. Design conventions
- Startup order (CRITICAL): UE with -ModelContextProtocolStartServer → port 8000 answers → THEN Codely. Wrong order = no native tools all session (#15).
- Log forensics = primary diagnostic: GetLogEntries(category:"", pattern, maxEntries) — prints carry per-UAID actor identity + timestamps; print text doubles as build fingerprint (which graph version ran).
- Modal rescue: screenshot → analyze_multimedia (title/button coords) → FindWindow(title) → PostMessage WM_CLOSE(0x0010) → poll MCP ~5-10s → save_assets([]) + disk-verify if mid-flight.

## 3. Tool params (verified signatures)
| Tool | Params |
|---|---|
| `StartPIE` | options:{bSimulate, playMode:"PlayMode_InViewPort", warmupSeconds} |
| `StopPIE` / `IsPIERunning` | {} |
| `CaptureViewport` | captureTransform?, annotations?, bShowUI? |
| `FocusOnActors` / `GetSelectedActors` / `SelectActors` | actors:[ref] |
| `GetLogEntries` | category:""(empty=all!), pattern:regex, maxEntries |
| `SetVerbosity` | category, verbosity:"Error..VeryVerbose" |
| SlateInspector: `Observe(ref:"")` → `Windows` → `Snapshot(ref, maxDepth:45)` → `Click`/`FillForm`/`PressKey` | observer workflow; allow ~5s tick; depth 45 for drawers |
| Win32 rescue: FindWindow(NULL,"title") → PostMessage(hwnd, 0x0010, 0, 0) | PowerShell; full block in screen_control.md |

## 4. Laws (domain)
- **G10 Environment & session traps (#15 #16 #18 #22 + #4/#42 family)**: scripts abort on first tool error (idempotent + results[] + risky-last); UE-before-Codely; write_file absolute paths; native dialogs block headlessly; SlateInspector recovers via Observe cycle + 5s wait; archived specifics #17 #21 #23 #39 in pitfalls_archive.md.
- **G13 Modal dismissal (2026-08-29)**: synthetic clicks FAIL on UE modals (twice-verified); PostMessage WM_CLOSE works instantly; AnimBP create refused at tool layer (dialog is the symptom).
- Cross-domain: G3 (post-rescue save+disk-verify), G5 (log-forensics pattern).

## 5. Recipes
| Task | Recipe |
|---|---|
| Stuck-MCP rescue (modal) | `references/screen_control.md` full procedure [VERIFIED ×2] |
| Who-sank-what diagnostics | G5 log forensics (SinkZone case, 2026-08-28) |
| PIE verification sampling | /Memory/UEDPIE_N_ paths + find_actors during PIE |

## 6. Evidence
- 2026-08-29 remote rescue: dialog dismissed via PostMessage, MCP recovered, all mid-flight assets saved (user was away from machine).
- Slate automation verified 2026-08-23 (console typing); degraded after PIE cycles (recovers via re-Observe).
