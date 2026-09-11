#Requires -Version 5.1
<#
  Encoding-safe MCP HTTP caller for Unreal Engine MCP Server.
  Bypasses ConvertTo-Json (which OOMs on Chinese text) and Get-Content encoding issues.

  Usage:
    # Call a simple MCP tool (no Chinese in args)
    . mcp_call.ps1 -ToolName "list_toolsets" -ResultFile "result.json"

    # Call a toolset tool
    . mcp_call.ps1 -ToolName "describe_toolset" -ToolsetName "editor_toolset.toolsets.scene.SceneTools" -ResultFile "result.json"

    # Execute a Python script via ProgrammaticToolset (encoding-safe path)
    . mcp_call.ps1 -ScriptPath "my_script.py" -ResultFile "result.json"
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$ToolName,
    [string]$ToolsetName,
    [string]$ScriptPath,
    [string]$ArgumentsJson = "{}",
    [string]$ResultFile = "",
    [string]$McpUrl = "http://127.0.0.1:8000/mcp"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Web

# --- Session management (reuse if already initialized in this PS session) ---
if (-not $script:McpSession) {
    $initBody = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"codely","version":"1.0"}}}'
    $r1 = Invoke-WebRequest -Uri $McpUrl -Method POST -Body $initBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 10
    $script:McpSession = $r1.Headers["Mcp-Session-Id"]
    $h2 = @{"Content-Type"="application/json"; "Mcp-Session-Id"=$script:McpSession}
    $notifyBody = '{"jsonrpc":"2.0","method":"notifications/initialized"}'
    Invoke-WebRequest -Uri $McpUrl -Method POST -Body $notifyBody -ContentType "application/json" -Headers $h2 -UseBasicParsing -TimeoutSec 5 | Out-Null
}

$headers = @{"Content-Type"="application/json"; "Mcp-Session-Id"=$script:McpSession}

# --- Build request body with manual JSON escaping (never use ConvertTo-Json) ---
$toolNameEsc = [System.Web.HttpUtility]::JavaScriptStringEncode($ToolName)

if ($ScriptPath) {
    # Encoding-safe: read .py file as UTF-8 bytes, escape for JSON
    $scriptContent = [System.IO.File]::ReadAllText($ScriptPath, [System.Text.Encoding]::UTF8)
    $scriptEsc = [System.Web.HttpUtility]::JavaScriptStringEncode($scriptContent)
    $body = '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"call_tool","arguments":{"tool_name":"execute_tool_script","toolset_name":"editor_toolset.toolsets.programmatic.ProgrammaticToolset","arguments":{"script":"' + $scriptEsc + '"}}}}'
} else {
    $tsEsc = [System.Web.HttpUtility]::JavaScriptStringEncode($ToolsetName)
    $argsEsc = [System.Web.HttpUtility]::JavaScriptStringEncode($ArgumentsJson)

    if ($ToolsetName) {
        $body = '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"call_tool","arguments":{"tool_name":"' + $toolNameEsc + '","toolset_name":"' + $tsEsc + '","arguments":' + $ArgumentsJson + '}}}'
    } else {
        $body = '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"call_tool","arguments":{"tool_name":"' + $toolNameEsc + '","arguments":' + $ArgumentsJson + '}}}'
    }
}

# --- Send request ---
$r = Invoke-WebRequest -Uri $McpUrl -Method POST -Body $body -ContentType "application/json" -Headers $headers -UseBasicParsing -TimeoutSec 120

# --- Output ---
if ($ResultFile) {
    [System.IO.File]::WriteAllText($ResultFile, $r.Content, [System.Text.Encoding]::UTF8)
    Write-Output "Result saved to $ResultFile"
} else {
    Write-Output $r.Content
}
