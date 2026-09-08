<#
Sets up the Microsoft Entra public-client app used for interactive (and
device-code) MSAL login with msgraph-mcp-full.

Bicep/ARM cannot register Entra apps - app registrations live in Microsoft
Graph (Entra ID), not Azure Resource Manager - so automation goes through the
Azure CLI (az ad app) or the Graph API. This script is the az CLI path.

Examples:
    .\scripts\setup_entra_app.ps1                              create app, print IDs
    .\scripts\setup_entra_app.ps1 -SetEnv                       also persist MSGRAPH_CLIENT_ID via setx
    .\scripts\setup_entra_app.ps1 -OutFile ~\msgraph-app.json  write clientId/tenantId/scopes for other tooling
    .\scripts\setup_entra_app.ps1 -Delete -AppId <clientId>     remove the registration afterwards

Requires: Azure CLI (az) with a signed-in identity in the target tenant.
#>
[CmdletBinding()]
param(
    [string]$ApplicationName = "msgraph-mcp-local",
    [string]$Scopes = "User.Read,Mail.Read,Calendars.ReadWrite,Files.ReadWrite",
    [switch]$SetEnv,
    [string]$OutFile = "",
    [switch]$Delete,
    [string]$AppId = ""
)

$ErrorActionPreference = "Stop"

function Get-AzAccount {
    $acct = az account show 2>$null | ConvertFrom-Json
    if (-not $acct) {
        Write-Host "Not signed in - running az login (complete the browser prompt)."
        az login
        $acct = az account show | ConvertFrom-Json
    }
    return $acct
}

if ($Delete) {
    if (-not $AppId) { throw "Provide -AppId when using -Delete." }
    az ad app delete --id $AppId
    Write-Host "Deleted app registration $AppId."
    exit 0
}

$acct = Get-AzAccount

$existing = az ad app list --display-name $ApplicationName | ConvertFrom-Json
if ($existing.Count -gt 0) {
    $clientId = $existing[0].appId
    Write-Host "Reusing existing app: $ApplicationName (clientId $clientId)"
    az ad app update --id $clientId `
        --public-client-redirect-uris "http://localhost" `
        --is-fallback-public-client true
}
else {
    $created = az ad app create `
        --display-name $ApplicationName `
        --sign-in-audience AzureADMyOrg `
        --public-client-redirect-uris "http://localhost" `
        --is-fallback-public-client true | ConvertFrom-Json
    $clientId = $created.appId
    Write-Host "Created app: $ApplicationName (clientId $clientId)"
}

$tenantId = $acct.tenantId

Write-Host "Entra app ready. Configure the MCP with:"
Write-Host "  MSGRAPH_AUTH_MODE=interactive"
Write-Host "  MSGRAPH_CLIENT_ID=$clientId"
Write-Host "  MSGRAPH_TENANT_ID=$tenantId"
Write-Host "  MSGRAPH_SCOPES=$Scopes"

if ($SetEnv) {
    setx MSGRAPH_CLIENT_ID $clientId | Out-Null
    setx MSGRAPH_TENANT_ID $tenantId | Out-Null
    Write-Host "MSGRAPH_CLIENT_ID and MSGRAPH_TENANT_ID persisted (restart your terminal to pick them up)."
}

if ($OutFile) {
    @{
        clientId    = $clientId
        tenantId    = $tenantId
        scopes      = @($Scopes -split ",")
        displayName = $ApplicationName
    } | ConvertTo-Json | Set-Content -Path $OutFile -Encoding utf8
    Write-Host "Wrote $OutFile"
}