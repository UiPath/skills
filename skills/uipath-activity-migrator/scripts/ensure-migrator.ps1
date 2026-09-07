<#
.SYNOPSIS
    Locate, download, and verify the UiPath Activity Migrator (UiPath.Upgrade.exe).
.DESCRIPTION
    TWIN SCRIPT: scripts/ensure-migrator.sh is the bash twin of this file.
    The two must stay behaviorally identical; change both in the same PR.

    The last stdout line is one JSON object; see references/acquisition-guide.md § Script output contract.
    Exit codes: 0 ok, 1 error, 3 missing (check-only).
    Compatible with Windows PowerShell 5.1 and PowerShell 7+.
.PARAMETER CheckOnly
    Report what is cached without downloading (bash: --check-only).
.PARAMETER Force
    Re-download and re-extract even when cached (bash: --force).
#>
param(
    [switch]$CheckOnly,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$DefaultUrl = 'https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip'
$Url = $DefaultUrl
if ($env:UIPATH_ACTIVITY_MIGRATOR_URL) { $Url = $env:UIPATH_ACTIVITY_MIGRATOR_URL }
$Offline = ($env:UIPATH_ACTIVITY_MIGRATOR_OFFLINE -eq '1')

function Emit-Json([hashtable]$Fields) {
    $ordered = [ordered]@{}
    foreach ($k in $Fields.Keys) { $ordered[$k] = $Fields[$k] }
    Write-Output ($ordered | ConvertTo-Json -Compress)
}
function Emit-Error([string]$Code, [string]$Message) {
    Emit-Json @{ status = 'error'; code = $Code; message = $Message }
    exit 1
}
function Get-LastModified($Headers) {
    if ($null -eq $Headers) { return '' }
    $v = $Headers['Last-Modified']
    if ($null -eq $v) { return '' }
    return ([string]$v).Trim()
}

# --- 1. Windows only -------------------------------------------------------
$isWin = $true
if ($PSVersionTable.PSVersion.Major -ge 6) { $isWin = [bool]$IsWindows }
if (-not $isWin) {
    Emit-Error 'not-windows' 'The Activity Migrator is a Windows-only .NET 8 desktop tool. Run this skill from a Windows machine that holds the project.'
}

# --- 2. Resolve install root and any existing exe --------------------------
$Source = ''
if ($env:UIPATH_ACTIVITY_MIGRATOR_DIR) {
    $Root = $env:UIPATH_ACTIVITY_MIGRATOR_DIR
    $Source = 'env'
} else {
    if (-not $env:LOCALAPPDATA) { Emit-Error 'verify-failed' 'LOCALAPPDATA is not set. Set UIPATH_ACTIVITY_MIGRATOR_DIR to an install folder.' }
    $Root = Join-Path $env:LOCALAPPDATA 'UiPath\ActivityMigrator'
}
$Current = Join-Path $Root 'current'
$Stamp = Join-Path $Root '.last-modified'
$Exe = ''
if (Test-Path -LiteralPath (Join-Path $Root 'UiPath.Upgrade.exe')) {
    $Exe = Join-Path $Root 'UiPath.Upgrade.exe'
} elseif (Test-Path -LiteralPath (Join-Path $Current 'UiPath.Upgrade.exe')) {
    $Exe = Join-Path $Current 'UiPath.Upgrade.exe'
}
if (-not $Source) { $Source = 'cached' }

if (-not $Exe -and $CheckOnly) {
    Emit-Json @{ status = 'missing'; dir = $Root }
    exit 3
}
if (-not $Exe -and $Offline) {
    Emit-Error 'offline-missing' "UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1 and no tool found under $Root. Place the extracted archive there; see references/acquisition-guide.md § Manual placement."
}

# --- 3. Decide whether to download ----------------------------------------
$NeedDownload = $false
$IsUpdate = $false
if (-not $Exe) {
    $NeedDownload = $true
} elseif ($Force) {
    $NeedDownload = $true
} elseif ($Source -eq 'env' -or $Offline -or $CheckOnly) {
    $NeedDownload = $false
} else {
    $remoteLm = ''
    try {
        $head = Invoke-WebRequest -Uri $Url -Method Head -UseBasicParsing -TimeoutSec 20
        $remoteLm = Get-LastModified $head.Headers
    } catch { $remoteLm = '' }
    $localLm = ''
    if (Test-Path -LiteralPath $Stamp) { $localLm = ((Get-Content -LiteralPath $Stamp -Raw) -replace "[`r`n]", '').Trim() }
    if ($remoteLm -and $localLm -and ($remoteLm -ne $localLm)) {
        $NeedDownload = $true
        $IsUpdate = $true
    }
    if ($remoteLm -and -not $localLm) {
        Set-Content -LiteralPath $Stamp -Value $remoteLm -Encoding ascii -NoNewline
    }
}

# --- 4. Download and extract ----------------------------------------------
if ($NeedDownload) {
    New-Item -ItemType Directory -Force -Path $Root | Out-Null
    $tmpZip = Join-Path $Root 'UiPath.Upgrade.Cli.zip.tmp'
    if (Test-Path -LiteralPath $tmpZip) { Remove-Item -LiteralPath $tmpZip -Force }
    $newLm = ''
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        $wc = New-Object System.Net.WebClient
        $wc.Proxy = [System.Net.WebRequest]::DefaultWebProxy
        if ($null -ne $wc.Proxy) { $wc.Proxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials }
        $wc.DownloadFile($Url, $tmpZip)
        $newLm = Get-LastModified $wc.ResponseHeaders
        $wc.Dispose()
    } catch {
        if (Test-Path -LiteralPath $tmpZip) { Remove-Item -LiteralPath $tmpZip -Force }
        Emit-Error 'download-failed' ('Download failed: ' + $_.Exception.Message + '. Check proxy settings or place the tool manually; see references/acquisition-guide.md § Manual placement.')
    }
    $stage = Join-Path $Root '.extract-tmp'
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    try {
        Expand-Archive -LiteralPath $tmpZip -DestinationPath $stage -Force
    } catch {
        Remove-Item -LiteralPath $stage -Recurse -Force
        Emit-Error 'extract-failed' ('Could not extract ' + $tmpZip + ': ' + $_.Exception.Message + '. Extract it manually into ' + $Current + '.')
    }
    if (-not (Test-Path -LiteralPath (Join-Path $stage 'UiPath.Upgrade.exe')) -or -not (Test-Path -LiteralPath (Join-Path $stage 'Extensions'))) {
        Remove-Item -LiteralPath $stage -Recurse -Force
        Emit-Error 'extract-failed' 'Archive layout unexpected: UiPath.Upgrade.exe or Extensions/ missing after extraction.'
    }
    if (Test-Path -LiteralPath $Current) { Remove-Item -LiteralPath $Current -Recurse -Force }
    Move-Item -LiteralPath $stage -Destination $Current
    Remove-Item -LiteralPath $tmpZip -Force
    if ($newLm) { Set-Content -LiteralPath $Stamp -Value $newLm -Encoding ascii -NoNewline }
    $Exe = Join-Path $Current 'UiPath.Upgrade.exe'
    if ($IsUpdate) { $Source = 'updated' } else { $Source = 'downloaded' }
}

# --- 5. .NET Desktop Runtime 8 ---------------------------------------------
$dotnetPath = ''
$dotnetCmd = Get-Command dotnet -ErrorAction SilentlyContinue
if ($dotnetCmd) {
    $dotnetPath = $dotnetCmd.Source
} else {
    $candidate = Join-Path $env:ProgramFiles 'dotnet\dotnet.exe'
    if (Test-Path -LiteralPath $candidate) { $dotnetPath = $candidate }
}
$runtime = ''
if ($dotnetPath) {
    try {
        $lines = & $dotnetPath --list-runtimes
        foreach ($line in $lines) {
            $parts = ([string]$line).Trim() -split ' '
            if ($parts.Length -ge 2 -and $parts[0] -eq 'Microsoft.WindowsDesktop.App' -and $parts[1] -like '8.*') { $runtime = $parts[1] }
        }
    } catch { $runtime = '' }
}
if (-not $runtime) {
    Emit-Error 'runtime-missing' 'Microsoft.WindowsDesktop.App 8.x not found. Install the .NET Desktop Runtime 8 (x64) from https://dotnet.microsoft.com/download/dotnet/8.0 and rerun.'
}

# --- 6. Verify the tool answers --------------------------------------------
$version = ''
try {
    $out = & $Exe version
    if ($null -ne $out) { $version = ([string]($out | Select-Object -Last 1)).Trim() }
} catch { $version = '' }
if (-not $version) {
    Emit-Error 'verify-failed' "$Exe did not print a version. The install may be incomplete; rerun with -Force."
}

Emit-Json @{ status = 'ok'; exe = $Exe; version = $version; source = $Source; runtime = $runtime }
exit 0
