#Requires -Version 5.1
<#
  Search the full UE API dictionary (ue_dict_full.json.gz, 346K+ entries).
  Usage:
    . search_ue_dict.ps1 -Keyword "AddActorWorldOffset"
    . search_ue_dict.ps1 -Keyword "collision" -Limit 5
    . search_ue_dict.ps1 -Keyword "Destroy" -Field description
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$Keyword,
    [string]$Field = "display_name",
    [int]$Limit = 10,
    [string]$DictPath = "E:\UE\UEBackup\ue_dict_full.json.gz"
)

$ErrorActionPreference = "Stop"

# Decompress and search
$gz = [System.IO.Compression.GzipStream]::new([System.IO.File]::OpenRead($DictPath), [System.IO.Compression.CompressionMode]::Decompress)
$sr = [System.IO.StreamReader]::new($gz, [System.Text.Encoding]::UTF8)
$content = $sr.ReadToEnd()
$sr.Close()
$gz.Close()

$json = $content | ConvertFrom-Json
$entries = $json.entries

$results = @()
foreach ($e in $entries) {
    $val = ""
    if ($Field -eq "display_name" -and $e.display_name) { $val = $e.display_name }
    elseif ($Field -eq "description" -and $e.description) { $val = $e.description }
    elseif ($Field -eq "syntax" -and $e.syntax) { $val = $e.syntax }
    elseif ($Field -eq "owner_class" -and $e.owner_class) { $val = $e.owner_class }
    elseif ($Field -eq "entry_id" -and $e.entry_id) { $val = $e.entry_id }

    if ($val -and $val -match $Keyword) {
        $results += $e
        if ($results.Count -ge $Limit) { break }
    }
}

Write-Output "Found $($results.Count) entries matching '$Keyword' in field '$Field':"
foreach ($r in $results) {
    Write-Output ""
    Write-Output "  display_name: $($r.display_name)"
    Write-Output "  description:  $($r.description)"
    Write-Output "  owner_class:  $($r.owner_class)"
    Write-Output "  syntax:       $($r.syntax)"
    Write-Output "  return_type:  $($r.return_type)"
    Write-Output "  entry_id:     $($r.entry_id)"
}
