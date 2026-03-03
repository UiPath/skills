#!/usr/bin/env bash
#
# Builds the InspectPackage tool if not already built (or if source has changed).
# Safe to run multiple times — skips the build when the binary is up to date.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSPROJ="$SCRIPT_DIR/InspectPackage.csproj"
DLL="$SCRIPT_DIR/bin/Release/net7.0/InspectPackage.dll"

# Check if dotnet SDK is available
if ! command -v dotnet &>/dev/null; then
  echo "ERROR: dotnet SDK not found. Install .NET 7.0+ from https://dotnet.microsoft.com/download" >&2
  exit 1
fi

# Skip build if the DLL exists and is newer than both source files
if [[ -f "$DLL" && "$DLL" -nt "$SCRIPT_DIR/Program.cs" && "$DLL" -nt "$CSPROJ" ]]; then
  echo "InspectPackage is already built and up to date."
  exit 0
fi

echo "Building InspectPackage..."
dotnet build "$CSPROJ" -c Release --nologo -v quiet
echo "Build complete: $DLL"