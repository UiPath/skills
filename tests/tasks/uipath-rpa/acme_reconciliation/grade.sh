#!/usr/bin/env bash
# Grade the candidate project in the working directory against the spec, one tier at a time:
#   grade.sh static    loads and compiles every workflow and checks the argument contract
#   grade.sh runtime   runs Main.xaml headlessly under CoreWF in every scenario
#
# The verifier runs the workflow with the XAML runner (_runner, CoreWF with UiPath.System.Activities
# 26.8.2), built once per sandbox into $XAML_RUNNER_DIR (default /tmp/xaml-runner) because this folder
# is mounted read-only. The build needs the .NET 10 SDK and the public NuGet feeds in _runner/nuget.config.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
tier="${1:?usage: grade.sh static|runtime}"
dir="${XAML_RUNNER_DIR:-/opt/xaml-runner}"
if [ ! -f "$dir/XamlRunner.dll" ]; then
  build="$(mktemp -d)"
  cp -R "$here/_runner/." "$build/"
  dotnet publish "$build/XamlRunner.csproj" -c Release -o "$dir" --nologo -v quiet >&2
fi
export XAML_RUNNER="$dir/XamlRunner.dll"
exec python3 "$here/_verifier/verify.py" --spec "$here/specs/acme_reconciliation.json" --tiers "$tier" --reward-file "$tier.json"
