#Requires -Version 5.1
<#
  import_asset.ps1 — TJGenerators → UE asset import pipeline (step 1-3 of 5)
  Verified end-to-end: 2026-08-23 (image import, CCC project, UE5.8)

  Full pipeline (steps 4-5 are MCP calls made by the agent):
    1. [this script] Download asset URL -> $TempDir
    2. [this script] Fill import_task.template.py -> <Project>/Saved/import_<name>.py
    3. [this script] Print READY line
    4. [agent] AssetTools.write_file the py (or use file written here directly),
       SlateInspector: Click "Output Log" button (bottom bar) -> Snapshot ->
       Type into console textbox [focused] near bottom: "py <abs py path>" submit=true
    5. [agent] Verify: GetLogEntries pattern="IMPORT_DONE" -> find_assets -> CaptureAssetImage

  Usage:
    . import_asset.ps1 -Url "https://...jpeg" -AssetName "ai_red_sphere"
    . import_asset.ps1 -LocalFile "C:\UE_Import\x.png" -AssetName "x"   # skip download
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$AssetName,
    [string]$Url = "",
    [string]$LocalFile = "",
    [string]$DestPath = "/Game/AIAssets",
    [string]$TempDir = "C:\UE_Import",
    [string]$ProjectSaved = ""
)

$ErrorActionPreference = "Stop"
if ($ProjectSaved -eq "") {
    # Default: UE project Saved dir next to the .uproject you use; pass -ProjectSaved explicitly otherwise
    $ProjectSaved = Join-Path (Get-Location) "Saved"
}
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

# 1. Resolve local file
if ($LocalFile -eq "" -and $Url -ne "") {
    $ext = [System.IO.Path]::GetExtension(($Url -split '\?')[0])
    if (-not $ext) { $ext = ".png" }
    $LocalFile = Join-Path $TempDir "$AssetName$ext"
    Invoke-WebRequest -Uri $Url -OutFile $LocalFile -UseBasicParsing -TimeoutSec 120
}
if (-not (Test-Path $LocalFile)) { throw "File not found: $LocalFile" }

# 2. Fill template
$tplPath = Join-Path $PSScriptRoot "py\import_task.template.py"
$tpl = [System.IO.File]::ReadAllText($tplPath, [System.Text.Encoding]::UTF8)
$py = $tpl.Replace("{{FILE}}", $LocalFile).Replace("{{DEST}}", $DestPath)
$pyPath = Join-Path $ProjectSaved "import_$AssetName.py"
[System.IO.File]::WriteAllText($pyPath, $py, [System.Text.Encoding]::UTF8)

# 3. Ready
$fwdPy = $pyPath -replace '\\','/'
Write-Output "READY file=$LocalFile"
Write-Output "READY py=$fwdPy"
Write-Output "NEXT: SlateInspector Click 'Output Log' -> Type `"py $fwdPy`" submit=true -> GetLogEntries pattern=IMPORT_DONE"
