#Requires -Version 5.1
<#
  refresh_schemas.ps1 - drift guard for baked tool-signature sources (v2, 2026-08-30).

  DEFAULT (offline, UE NOT required): cross-checks the TWO baked sources against each other:
      references/tool_schemas.md        (core toolset signatures)
      references/capabilities/*.md      (per-domain param tables, section 3)
  Reports: DRIFT (same tool, disjoint params) / WARN (partial mismatch) / INFO (single-source).
  Run this after ANY edit to capability docs or tool_schemas.md - catches the dual-source
  drift flagged by pilot QA 2026-08-29 ("domain docs duplicate schema rows").

  -Live (UE must be running on $McpUrl): additionally pulls describe_toolset from the live
  server and diffs live params vs tool_schemas.md. Diff is toolset-aware (keyed
  "<toolset>::<tool>") because bare tool names collide across toolsets, and it brace-matches
  the schema so nested option objects are not truncated. [VERIFIED 2026-09-24 UE5.8.3-EN]

  Usage:
    powershell -File refresh_schemas.ps1            # offline cross-check only
    powershell -File refresh_schemas.ps1 -Live      # + live diff (UE running)
#>
param(
    [string]$McpUrl = "http://127.0.0.1:8000/mcp",
    [switch]$Live,
    [string[]]$Toolsets = @(
        "editor_toolset.toolsets.blueprint.BlueprintTools",
        "editor_toolset.toolsets.actor.ActorTools",
        "editor_toolset.toolsets.primitive.PrimitiveTools",
        "editor_toolset.toolsets.object.ObjectTools",
        "editor_toolset.toolsets.scene.SceneTools",
        "editor_toolset.toolsets.asset.AssetTools",
        "EditorToolset.EditorAppToolset",
        "EditorToolset.LogsToolset",
        "editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools",
        "editor_toolset.toolsets.static_mesh.StaticMeshTools",
        "PhysicsToolsets.PhysicsAssetToolset",
        "editor_toolset.toolsets.material.MaterialTools"
    )
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillDir = Split-Path -Parent $scriptDir
$schemasPath = Join-Path $skillDir "references\tool_schemas.md"
$capsDir = Join-Path $skillDir "references\capabilities"
$emDash = [char]0x2014
$stopwords = @('str','ref','bool','int','float','num','obj','optional','empty','all','none',
               'true','false','eg','ie','etc','and','or','the','with','for','use','default','if')

# --- param-cell parser: extracts parameter NAMES from a markdown params cell ---
function Parse-ParamCell([string]$cell) {
    if (-not $cell) { return @() }
    $c = $cell -replace '`', ''
    # cut commentary after em-dash
    $idx = $c.IndexOf($emDash)
    if ($idx -ge 0) { $c = $c.Substring(0, $idx) }
    # strip parenthesized asides
    $c = $c -replace '\([^)]*\)', ' '
    $names = @()
    foreach ($seg in ($c -split ',')) {
        $s = $seg.Trim() -replace '[\[\]\{\}\?<>=].*$', ''
        if ($s -match ':') { $s = ($s -split ':')[0].Trim() }
        else { $s = ($s -split '\s+')[0] }
        if ($s -match '^[a-zA-Z_][a-zA-Z0-9_]*$' -and $s.Length -gt 1 -and $stopwords -notcontains $s.ToLower()) {
            $names += $s
        }
    }
    return ($names | Select-Object -Unique)
}

# --- source 1: tool_schemas.md  -> map tool -> params (global by tool name) ---
function Parse-ToolSchemas([string]$path) {
    $map = @{}
    if (-not (Test-Path $path)) { return $map }
    foreach ($line in [System.IO.File]::ReadAllLines($path)) {
        if ($line -notmatch '^\|\s*`([^`]+)`\s*\|(.+)\|\s*$') { continue }
        $tool = $Matches[1].Trim()
        if ($tool -match '/') { continue }   # merged rows ("get/set_actor_transform") - not diffable
        $cell = $Matches[2].Trim()
        $map[$tool] = Parse-ParamCell $cell
    }
    return $map
}

# --- source 2: capabilities/*.md tables -> map tool -> params (union across files) ---
function Parse-CapabilityDocs([string]$dir) {
    $map = @{}
    if (-not (Test-Path $dir)) { return $map }
    foreach ($f in (Get-ChildItem $dir -Filter *.md)) {
        foreach ($line in [System.IO.File]::ReadAllLines($f.FullName)) {
            # rows like: | `tool` | params |   (leading "Toolset:" prefix inside backticks is stripped)
            if ($line -notmatch '^\|\s*`([^`]+)`\s*\|(.+)\|\s*$') { continue }
            $tool = ($Matches[1].Trim() -replace '^\w+:\s*', '')
            $cell = $Matches[2].Trim()
            # merged rows ("a / b") and non-signature rows (no comma/colon/empty cell) are skipped
            if ($tool -match '/' -or $tool -notmatch '^[a-zA-Z_][a-zA-Z0-9_]*$') { continue }
            if ($cell -notmatch '[,:]' -and $cell.Trim() -ne '') { continue }
            # skip idempotency-guards tables: their 2nd column starts with YES/NO/UNKNOWN/silent-fail
            if ($cell -match '^(YES|NO|UNKNOWN|silent-fail)') { continue }
            $p = Parse-ParamCell $cell
            if ($map.ContainsKey($tool)) { $map[$tool] = @($map[$tool] + $p | Select-Object -Unique) }
            else { $map[$tool] = $p }
        }
    }
    return $map
}

Write-Output "=== OFFLINE CROSS-CHECK: tool_schemas.md vs capabilities/*.md ==="
$schemas = Parse-ToolSchemas $schemasPath
$caps = Parse-CapabilityDocs $capsDir
Write-Output ("parsed: tool_schemas.md = {0} tools, capabilities = {1} tools" -f $schemas.Count, $caps.Count)

$drift = 0; $warn = 0; $info = 0
$allTools = @($schemas.Keys + $caps.Keys | Select-Object -Unique) | Sort-Object
foreach ($t in $allTools) {
    $inS = $schemas.ContainsKey($t); $inC = $caps.ContainsKey($t)
    if ($inS -and $inC) {
        $sp = @($schemas[$t]); $cp = @($caps[$t])
        if (-not $sp) { $sp = @() }
        if (-not $cp) { $cp = @() }
        $inter = @($sp | Where-Object { $cp -contains $_ })
        $onlyS = @($sp | Where-Object { $cp -notcontains $_ })
        $onlyC = @($cp | Where-Object { $sp -notcontains $_ })
        if ($inter.Count -eq 0 -and ($sp.Count -gt 0 -or $cp.Count -gt 0)) {
            Write-Output ("DRIFT  {0}: schemas=[{1}] caps=[{2}]" -f $t, ($sp -join ','), ($cp -join ','))
            $drift++
        } elseif ($onlyS.Count -gt 0 -or $onlyC.Count -gt 0) {
            Write-Output ("WARN   {0}: only-in-schemas=[{1}] only-in-caps=[{2}]" -f $t, ($onlyS -join ','), ($onlyC -join ','))
            $warn++
        }
    } else {
        $src = if ($inS) { 'tool_schemas-only' } else { 'caps-only' }
        Write-Output ("INFO   {0}: single-source ({1})" -f $t, $src)
        $info++
    }
}
Write-Output ("--- offline summary: {0} DRIFT, {1} WARN, {2} single-source INFO ---" -f $drift, $warn, $info)
if ($drift -gt 0) { Write-Output "ACTION: fix DRIFT rows first (same tool, disjoint params = one side is stale)." }

# --- optional live pull & diff against tool_schemas.md ---

# Extract a brace-balanced JSON object starting at the first '{' at/after $From.
# The old non-greedy regex ('\{"type":"object".*?\}') stopped at the FIRST closing
# brace, truncating any nested option object - that produced phantom drift on
# tools like StartPIE (whose only top-level param is `options`).
function Get-BracedJson([string]$Text, [int]$From) {
    $k = $Text.IndexOf('{', $From)
    if ($k -lt 0) { return $null }
    $depth = 0
    for ($p = $k; $p -lt $Text.Length; $p++) {
        $ch = $Text[$p]
        if ($ch -eq '{') { $depth++ }
        elseif ($ch -eq '}') {
            $depth--
            if ($depth -eq 0) { return $Text.Substring($k, $p - $k + 1) }
        }
    }
    return $null
}

# JSON-Schema keywords are structure, not parameters.
$script:SchemaKeywords = @('properties', 'required', 'type', 'title', 'description',
                           'items', 'additionalProperties', 'default')

# Top-level parameter names = keys directly under "properties".
function Get-TopLevelProps([string]$Schema) {
    try {
        $obj = $Schema | ConvertFrom-Json
        if ($obj.properties) { return @($obj.properties.PSObject.Properties.Name) }
    } catch { }
    return @()
}

# Property names at ANY depth (nested option/struct fields included), minus schema
# keywords - so a recorded nested param like playMode is not reported as missing.
function Get-AllProps([string]$Schema) {
    $names = @([regex]::Matches($Schema, '"([A-Za-z0-9_]+)"\s*:\s*\{') |
               ForEach-Object { $_.Groups[1].Value })
    return @($names | Where-Object { $script:SchemaKeywords -notcontains $_ } | Select-Object -Unique)
}

if ($Live) {
    Write-Output ""
    Write-Output "=== LIVE PULL: describe_toolset x $($Toolsets.Count) (UE must be running) ==="
    $initBody = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"codely","version":"1.0"}}}'
    try {
        $r1 = Invoke-WebRequest -Uri $McpUrl -Method POST -Body $initBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 10
    } catch {
        Write-Output ("initialize FAILED: {0}" -f $_.Exception.Message)
        Write-Output "ACTION: start UE with -ModelContextProtocolStartServer, then re-run with -Live."
        exit 0
    }
    $sid = $null
    foreach ($k in $r1.Headers.Keys) { if ($k -ieq "Mcp-Session-Id") { $sid = $r1.Headers[$k] } }
    $h = @{ "Content-Type" = "application/json" }
    if ($sid) { $h["Mcp-Session-Id"] = $sid }
    # PS 5.1 quirk: the notification replies with an EMPTY body and
    # Invoke-WebRequest throws NullReferenceException on it. Harmless - ignore.
    try {
        Invoke-WebRequest -Uri $McpUrl -Method POST -Body '{"jsonrpc":"2.0","method":"notifications/initialized"}' -ContentType "application/json" -Headers $h -TimeoutSec 5 | Out-Null
    } catch {
        Write-Output "(note: notifications/initialized returned an empty body - expected on PS 5.1, continuing)"
    }

    # keyed "<toolset>::<tool>" - a bare tool name is NOT unique across toolsets
    # (create / add_variable / connect_pins / get_graph / list_variables all collide),
    # so a global by-name map produced false DRIFTs against the wrong toolset.
    $liveMap = @{}
    foreach ($ts in $Toolsets) {
        $argsJson = '{"toolset_name":"' + $ts + '"}'
        $body = '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"call_tool","arguments":{"tool_name":"describe_toolset","arguments":' + $argsJson + '}}}'
        try {
            $r = Invoke-WebRequest -Uri $McpUrl -Method POST -Body $body -ContentType "application/json" -Headers $h -UseBasicParsing -TimeoutSec 120
            $text = ($r.Content | ConvertFrom-Json).result.content[0].text
            $found = 0
            foreach ($m in [regex]::Matches($text, '"name"\s*:\s*"' + [regex]::Escape($ts) + '\.([A-Za-z0-9_]+)"')) {
                $tool = $m.Groups[1].Value
                $schemaAt = $text.IndexOf('"inputSchema"', $m.Index)
                if ($schemaAt -lt 0) { continue }
                $schema = Get-BracedJson $text $schemaAt
                if (-not $schema) { continue }
                $liveMap[$ts + '::' + $tool] = @{
                    Top = @(Get-TopLevelProps $schema)
                    All = @(Get-AllProps $schema)
                }
                $found++
            }
            Write-Output ("{0}: {1} tools parsed" -f $ts, $found)
        } catch {
            Write-Output ("{0} FAILED: {1}" -f $ts, $_.Exception.Message)
        }
    }

    Write-Output ""
    Write-Output "=== LIVE vs tool_schemas.md diff (toolset-aware) ==="
    $exact = 0; $ld = 0; $lw = 0; $linfo = 0
    foreach ($t in ($schemas.Keys | Sort-Object)) {
        $owners = @($liveMap.Keys | Where-Object { $_.EndsWith('::' + $t) } | Sort-Object)
        if ($owners.Count -eq 0) {
            Write-Output ("LIVE-INFO   {0}: not exposed by any probed toolset" -f $t)
            $linfo++
            continue
        }
        $sp = @($schemas[$t])
        $matched = $false; $superset = $false; $detail = @()
        foreach ($key in $owners) {
            $lpTop = @($liveMap[$key].Top)
            $lpAll = @($liveMap[$key].All)
            # a recorded param counts as present if it is a TOP-LEVEL param, or a
            # nested field (docs abbreviate nested struct/option fields). Top-level
            # is checked first because a real param may share a name with a schema
            # keyword (find_nodes has a `title` param; get_properties has `properties`).
            $missing = @($sp | Where-Object { $lpTop -notcontains $_ -and $lpAll -notcontains $_ })
            # only genuinely new TOP-LEVEL params are worth reporting
            $extraTop = @($lpTop | Where-Object { $sp -notcontains $_ })
            if ($missing.Count -eq 0 -and $extraTop.Count -eq 0) { $matched = $true }
            elseif ($missing.Count -eq 0) { $superset = $true }
            $short = ($key -split '::')[0]
            $detail += ("[{0}] live=[{1}]{2}" -f ($short.Split('.')[-1]), ($lpTop -join ','),
                        $(if ($missing.Count -gt 0) { " missing=[$($missing -join ',')]" } else { "" }))
        }
        if ($matched) { $exact++ }
        elseif ($superset) {
            Write-Output ("LIVE-WARN   {0}: live adds optional params (doc omits them) {1}" -f $t, ($detail -join ' '))
            $lw++
        } else {
            $tag = if ($owners.Count -gt 1) { "LIVE-DRIFT*" } else { "LIVE-DRIFT " }
            Write-Output ("{0} {1}: recorded=[{2}] {3}" -f $tag, $t, ($sp -join ','), ($detail -join ' '))
            $ld++
        }
    }
    Write-Output ("--- live summary: {0} exact, {1} DRIFT, {2} WARN, {3} absent ---" -f $exact, $ld, $lw, $linfo)
    Write-Output "NOTE: '*' = the tool name exists in several probed toolsets (name collision); listed owners are alternatives, not simultaneous conflicts."
    Write-Output "NOTE: live parsing is regex+brace-matching over describe_toolset text; treat LIVE-DRIFT as investigate, not gospel."
} else {
    Write-Output ""
    Write-Output "(offline mode only - add -Live with UE running to also diff live server schemas)"
}
