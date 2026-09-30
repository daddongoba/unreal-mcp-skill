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
- **G18 [Other] Inventory counting artifact (2026-09-24)**: the server's own listings over-report if counted naively — `list_toolsets` output contains multi-line descriptions whose bullet lines also start with `- `, and `describe_toolset` repeats the toolset's own name once, so line-counting or `"name"`-counting inflates both the toolset total and each per-toolset tool count by 1. This produced the long-standing wrong "67 toolsets" figure (real: 52 toolsets / 830 tools on UE 5.8.3). Count only entries matching `^[A-Za-z_][A-Za-z0-9_.]*$` before the `:`, and count qualified names `"name":"<toolset>.<tool>"`. `scripts/snapshot_toolsets.py` does this correctly. Also: `list_toolsets` prints 3 entries that are NOT toolsets (`GetAssetDiscoveryInfo`, `FindNiagaraScripts`, `GetNiagaraScriptDigest` — tools inside `NiagaraToolsets.NiagaraToolset_Assets`). `[VERIFIED 2026-09-24 UE5.8.3-EN]`
- **G19 [Other] Enum-array params: the schema lies and the error hides the culprit (2026-09-25)**: some params are declared as `array of string` in `inputSchema` but are ENUM arrays at runtime, so string values fail to convert. Confirmed on `SceneTools.find_actors.collision_channels`: `[]` ✅ and `[0]` ✅ (numeric enum index) work; `["WorldStatic"]` ❌ and `["ECC_WorldStatic"]` ❌ both fail with a generic `could not convert incoming function input params Json to a UStruct` that does **not** name the offending parameter — it reads like a malformed whole-request error and sends you hunting the wrong param. **Rule: when an "array of string" param fails conversion, retry with numeric enum indices or an empty array; then isolate by removing params one at a time.** Expect more of these (full catalogue needs write probes). `[VERIFIED 2026-09-25 UE5.8.3-EN]`
- **G21 [Other] Host memory exhaustion masquerades as GPU OOM (2026-09-30)**: an editor crash of type `OutOfMemory` whose fatal error reads `D3D12Util.cpp:815 Out of video memory trying to allocate a rendering resource` does **NOT** prove VRAM ran out. Read the whole block the fatal error prints: `Local Budget / Local Used` (VRAM) *and* `Process Physical Memory` + `Physical/Virtual Memory` (host). Observed shape: VRAM 3396 MB used of a 9283 MB budget — plenty free — while physical RAM had 1764 MB free of 32473 MB and commit was 46972 MB of a 48345 MB limit; the D3D12 allocation died for lack of **host commit**, not VRAM. Trigger: a heavy WP/OpenWorld map load + N `ShaderCompileWorker` processes + ordinary desktop apps on a 32 GB machine. Fixes to apply **before** retrying (all `[UNVERIFIED — applied 2026-09-30; retry had not been run]`): (a) halve the shader workers in the project's `Config/DefaultEngine.ini` — `[DevOptions.Shaders]` / `PercentageUnusedShaderCompilingThreads=75` (24 logical cores above `ShaderCompilerCoreCountThreshold=12` → 6 workers instead of 12; confirm via the log line `Using 6 local workers for shader compilation`); (b) lift the commit limit with a bigger pagefile — WMI `Win32_ComputerSystem.AutomaticManagedPagefile` `Put()` fails with a bare `Generic failure` (`常规故障`) even elevated, but writing the registry MultiString `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PagingFiles` = `C:\pagefile.sys 16384 32768` (+ a second entry on another drive) succeeds, read-back verifies, reboot required; (c) close other RAM-hungry apps. **Diagnosis `[VERIFIED 2026-09-30 UE5.8-EN]`, mitigation `[UNVERIFIED]`** — never report "显存不够" from the error text alone.
- **G22 [Flow] `ue_connect.py wait` timing out is NOT failure (2026-09-30)**: the 420 s timeout means "port 8000 has not answered yet", not "the launch failed". Legitimate startups overshoot it — the first launch after enabling a new targeted shader format recompiles shader maps (measured **1136 s** editor startup that session) and a 140 MB WP map load adds minutes on top. Before killing/relaunching, read `Saved/Logs/<Project>.log`: an advancing mtime + `LogMaterial: Missing cached shadermap ... compiling` + live `ShaderCompileWorker` processes = healthy load. Just poll `/mcp` again (it answered **~1 s** after the load finished; `wait` run later reported `CONNECTED after 1s`). `[VERIFIED 2026-09-30 UE5.8-EN]`
- **G23 [Other] Nanite "Missing Project Settings" dialog = SM6 missing from the Windows *targeted* shader formats (2026-09-30)**: startup shows *"Shader Model 6 (SM6) is required to use Nanite assets … Project Settings -> Platforms -> Windows -> D3D12 Targeted Shader Formats"* (raised in `Runtime/Engine/Private/StaticMesh.cpp`, `NaniteNeedsSM6Setting`) even though D3D12/Lumen already run SM6 at runtime. Engine default is `+D3D12TargetedShaderFormats=PCD3D_SM5` (`Engine/Config/BaseEngine.ini:3410`), so the project must add `[/Script/WindowsTargetPlatform.WindowsTargetSettings]` → `+D3D12TargetedShaderFormats=PCD3D_SM6` (append keeps SM5 and adds SM6). Verify functionally: relaunch, then grep the log for `required to use Nanite` = 0. Cost: the first launch after the change compiles SM6 shader maps (1136 s observed here); once the DDC is warm startup fell to **~14 s**. `[VERIFIED 2026-09-30 UE5.8-EN]`
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
