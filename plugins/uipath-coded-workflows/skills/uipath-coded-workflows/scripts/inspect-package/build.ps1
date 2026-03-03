#
# Builds the InspectPackage tool if not already built (or if source has changed).
# Safe to run multiple times - skips the build when the binary is up to date.
#
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Csproj = Join-Path $ScriptDir "InspectPackage.csproj"
$Dll = Join-Path $ScriptDir "bin" "Release" "net7.0" "InspectPackage.dll"

# Check if dotnet SDK is available
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Error "dotnet SDK not found. Install .NET 7.0+ from https://dotnet.microsoft.com/download"
    exit 1
}

# Skip build if the DLL exists and is newer than both source files
if (Test-Path $Dll) {
    $dllTime = (Get-Item $Dll).LastWriteTime
    $csTime = (Get-Item (Join-Path $ScriptDir "Program.cs")).LastWriteTime
    $csprojTime = (Get-Item $Csproj).LastWriteTime

    if ($dllTime -gt $csTime -and $dllTime -gt $csprojTime) {
        Write-Host "InspectPackage is already built and up to date."
        exit 0
    }
}

Write-Host "Building InspectPackage..."
dotnet build $Csproj -c Release --nologo -v quiet
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Build complete: $Dll"