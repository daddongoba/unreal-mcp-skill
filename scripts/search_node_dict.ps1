#Requires -Version 5.1
<#
  search_node_dict.ps1 - offline blueprint-node lookup for the unreal-mcp skill.
  Searches BOTH dictionaries:
    references/node_dictionary_merged.json  (1665 nodes: library static functions)
    references/node_dict_extras.json        (PIE-verified Actor/Component members, special K2Nodes, patterns)
  Use this BEFORE writing DSL for any node not already verified in a template - it answers
  exact type_id + pin names + defaults offline (cheaper than runtime find_node_types).

  Usage:
    powershell -File search_node_dict.ps1 -Query "spawn"                 # substring search, all fields
    powershell -File search_node_dict.ps1 -Query "MakeTransform" -Exact  # exact display_name / dsl_type_id
    powershell -File search_node_dict.ps1 -Query "Math|"                 # browse a category
    powershell -File search_node_dict.ps1 -Query "transform" -Max 40     # more results

  Output: one block per node - [MAIN]/[EXTRA] tag, synthesized DSL type_id (category|display_name),
  pin list (exec pins filtered), defaults shown as =value, extras carry notes + verification source.
  Exit note: if 0 hits, rerun with a shorter/looser query (e.g. "Spawn" instead of "SpawnActorFromClass").
#>
param(
    [Parameter(Mandatory = $true)][string]$Query,
    [switch]$Exact,
    [int]$Max = 15
)

$ErrorActionPreference = "Stop"
$skillDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$mainPath = Join-Path $skillDir "references\node_dictionary_merged.json"
$extraPath = Join-Path $skillDir "references\node_dict_extras.json"

function Format-PinList($pins) {
    if (-not $pins) { return "(none)" }
    $parts = @()
    foreach ($p in $pins) {
        if ($p.type -eq "exec") { continue }  # exec flow is implicit in DSL
        $d = ""
        if ($null -ne $p.default -and "$($p.default)" -ne "") { $d = "=" + $p.default }
        $parts += "$($p.name):$($p.type)$d"
    }
    if ($parts.Count -eq 0) { return "(exec only)" }
    return $parts -join " "
}

function Test-Match([string]$field, [string]$q, [bool]$exact) {
    if ([string]::IsNullOrEmpty($field)) { return -1 }
    if ($exact) { return $(if ($field -ieq $q) { 0 } else { -1 }) }
    if ($field -ieq $q) { return 0 }
    if ($field -ilike "*$q*") { return 1 }
    return -1
}

# rank: 0 exact | 1 substring on id/display | 2 substring on category | 3 substring on function/key
function Get-Rank($node, [string]$key, [string]$q, [bool]$exact) {
    $display = "$($node.display_name)"
    $id = if ($node.PSObject.Properties["dsl_type_id"]) { "$($node.dsl_type_id)" } else { $null }
    $best = -1
    foreach ($r in @(
            (Test-Match $display $q $exact),
            (Test-Match $id $q $exact)
        )) { if ($r -ge 0 -and ($best -lt 0 -or $r -lt $best)) { $best = $r } }
    if ($best -ge 0) { return $best }
    if ($exact) { return -1 }
    $cat = "$($node.category)"
    if ($cat -ilike "*$q*") { return 2 }
    $fn = "$($node.function_name)"
    if ($fn -ilike "*$q*") { return 3 }
    if ($key -ilike "*$q*") { return 3 }
    return -1
}

$hits = New-Object System.Collections.Generic.List[object]

# --- main dictionary ---
$mainObj = [System.IO.File]::ReadAllText($mainPath) | ConvertFrom-Json
foreach ($prop in $mainObj.nodes.PSObject.Properties) {
    $n = $prop.Value
    $rank = Get-Rank $n $prop.Name $Query ([bool]$Exact)
    if ($rank -ge 0) {
        $cat = "$($n.category)"
        $disp = "$($n.display_name)"
        $id = if ($cat -and $disp) { "$cat|$disp" } elseif ($disp) { $disp } else { $prop.Name }
        $hits.Add([pscustomobject]@{
            Rank = $rank; Id = $id; Src = "MAIN "; Node = $n; Key = $prop.Name
        })
    }
}

# --- extras dictionary ---
if (Test-Path $extraPath) {
    $extraObj = [System.IO.File]::ReadAllText($extraPath) | ConvertFrom-Json
    foreach ($prop in $extraObj.nodes.PSObject.Properties) {
        $n = $prop.Value
        $rank = Get-Rank $n $prop.Name $Query ([bool]$Exact)
        if ($rank -ge 0) {
            $hits.Add([pscustomobject]@{
                Rank = $rank; Id = "$($n.dsl_type_id)"; Src = "EXTRA"; Node = $n; Key = $prop.Name
            })
        }
    }
}

$sorted = $hits | Sort-Object Rank
$shown = if ($Max -gt 0) { $sorted | Select-Object -First $Max } else { $sorted }

if (-not $shown -or @($shown).Count -eq 0) {
    Write-Output "0 hits for '$Query'. Try a shorter substring (e.g. 'Spawn' not 'SpawnActorFromClass'), drop -Exact, or browse a category ('Math|')."
    return
}

foreach ($h in $shown) {
    $n = $h.Node
    $owner = ""
    if ($n.PSObject.Properties["function_owner"] -and $n.function_owner) { $owner = "  (" + ($n.function_owner -replace "^/Script/Engine\.", "") + ")" }
    elseif ($n.PSObject.Properties["ue_class"] -and $n.ue_class) { $owner = "  ($($n.ue_class))" }
    Write-Output "[$($h.Src)] $($h.Id)$owner"
    Write-Output "  in : $(Format-PinList $n.inputs)"
    if ($n.outputs) { Write-Output "  out: $(Format-PinList $n.outputs)" }
    if ($n.PSObject.Properties["notes"] -and $n.notes) { Write-Output "  ! $($n.notes)" }
    if ($h.Src -eq "EXTRA" -and $n.PSObject.Properties["source"] -and $n.source) { Write-Output "  src: $($n.source)" }
    Write-Output ""
}
$total = $hits.Count        # NOT @($hits).Count - PS5.1 @() on List[object] throws ArgumentException
$shownN = @($shown).Count
if ($total -gt $shownN) { Write-Output "($shownN of $total hits shown - raise -Max to see more)" }
else { Write-Output "($total hit(s))" }
