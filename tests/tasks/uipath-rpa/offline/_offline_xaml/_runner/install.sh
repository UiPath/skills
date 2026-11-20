#!/usr/bin/env bash
# Build the XAML runner into _runner/.build (or $1). Needs the .NET 10 SDK and network once, for
# the NuGet restore; after that the runner and every package it loads are local.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
out="${1:-$here/.build}"
dotnet publish "$here/XamlRunner.csproj" -c Release -o "$out" --nologo -v quiet
echo "runner: $out/XamlRunner.dll"
