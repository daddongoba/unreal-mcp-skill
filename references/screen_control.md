# Screen Control & Native Dialog Handling

Control the physical screen when Slate/MCP can't: native Win32 dialogs (firewall, package restore, crash reporters), blocked startup windows, and UI without MCP coverage.

`[VERIFIED 2026-08-23 Win11]` — proven during T4 C++ tests (firewall dialog + Restore Packages window).

## Modal dialog dismissal — what actually works (`[VERIFIED 2026-08-29]` remote rescue)

When a UE native modal (e.g. Message box "Cannot create a blueprint based on the class 'AnimBlueprint'") blocks the MCP server:

1. **PostMessage WM_CLOSE (0x0010) to the dialog hwnd — WORKS**: `FindWindow(NULL, "Message")` → `PostMessage(hwnd, 0x0010, 0, 0)`. Dialog closed, MCP recovered after ~5-10s (poll `initialize` with 8s timeout).
2. **Simulated mouse click (SetCursorPos + mouse_event) — FAILED twice** on UE modal message boxes: coords verified correct via screenshot + analyze_multimedia, foreground set — UE modal input loops ignore synthetic cursor events. Don't waste rounds on it for UE modals.
3. Post-dismissal: `save_assets([])` immediately if assets were mid-flight, then DISK-verify (G3) — all in-memory assets survived this way.
4. Locating unknown modals: full-screen capture → analyze_multimedia (ask for title/content/button pixel coords) → FindWindow by that title.

## Capability map

| Task | Method | Key API |
|------|--------|---------|
| Find window by title | Get-Process | `MainWindowTitle`, `.MainWindowHandle` |
| Enumerate ALL windows of a process | EnumWindows + pid filter | IsWindowVisible, GetWindowText |
| Check dialog state | process | `Responding`, `IsIconic` (minimized?) |
| Window rect (for coordinate math) | GetWindowRect | origin = (L,T) |
| **Bring to front** | ShowWindow(9) + SetForegroundWindow | handle from above |
| **Click a native button** | SetCursorPos + mouse_event(2/4) | needs screen coords |
| **Send keystrokes to window** | SendKeys ("{ENTER}", "~", text) | AppActivate(pid) first |
| **Post message directly (no focus)** | PostMessage WM_CLOSE=0x0010 / WM_KEYDOWN=0x100 | works on background windows |
| **Screenshot a window/region** | Graphics.CopyFromScreen(origin, 0,0, size) | then analyze_multimedia |
| Full screen capture | same with screen bounds | analyze_multimedia reads coords |

## The win-dialog combat loop (verified)

```
1. Detect:  Get-Process -Name UnrealEditor | select MainWindowTitle, Responding
   → title stuck on a dialog (e.g. "Restore Packages") = blocked
2. Capture: window rect → CopyFromScreen → PNG → analyze_multimedia
   → prompt: "button labels + center coords WITHIN image bounds"
3. Compute: screen = windowOrigin + imageCoord
4. Click:   SetCursorPos(screenX, screenY); mouse_event down/up
   → re-capture to confirm state change
5. If no standard button (Slate-rendered dialog):
   → PostMessage(handle, 0x0010, 0, 0)  # WM_CLOSE — skips/closes the dialog
   → or SendKeys "{ENTER}" after AppActivate
```

## Verified scenarios

1. **Windows firewall prompt** (blocks UnrealBuildTool): full-screen capture → AI reads 允许 button at image coords → screen-click. Note: AI sometimes returns coords outside image bounds — sanity-check (x<width, y<height) before clicking; ask again if out of range.
2. **"Restore Packages" console window** (NuGet restore stuck on firewall block): no Win32 buttons (Slate inside) → `PostMessage WM_CLOSE` skipped it cleanly → editor resumed loading. Permanent fix = admin firewall rule:
   ```
   netsh advfirewall firewall add rule name="UBT_Allow" dir=in action=allow program="E:\UE_5.8\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe" enable=yes
   netsh advfirewall firewall add rule name="UE_Allow" dir=in action=allow program="E:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" enable=yes
   ```
3. **SendKeys console input** (when Slate died): SetForegroundWindow(UE) → SendKeys "~" (open console) + text + "{ENTER}". Worked for typing; effectiveness of the command itself depends on console focus.

## Reusable PowerShell: the Win32 helper block

Paste-once per shell session (Add-Type), then reuse:

```powershell
Add-Type @"
using System; using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern void SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, UIntPtr e);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [StructLayout(LayoutKind.Sequential)] public struct R { public int L, T, Rt, B; }
}
"@
# click: [W]::SetCursorPos(x,y); [W]::mouse_event(2,0,0,0,[UIntPtr]::Zero); [W]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
# close window: [W]::PostMessage($h, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
# capture:
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($originX, $originY, 0, 0, $bmp.Size)
$bmp.Save("C:\UE_Import\shot.png")
```

## Limits & cautions

- analyze_multimedia coord hallucination: ALWAYS validate coords are inside image bounds before clicking; convert image→screen with window origin.
- mouse_event clicks at real cursor — don't move the mouse during automation.
- Cowork's own window loves the foreground; capture the SPECIFIC dialog rect (not full screen) when possible, and say "ignore chat windows" in the analyze prompt.
- SendKeys types into whatever has focus — AppActivate first, and pray.
- This is a fallback layer: prefer SlateInspector (in-editor UI) when alive; use this for native/modals/blocked states only.
