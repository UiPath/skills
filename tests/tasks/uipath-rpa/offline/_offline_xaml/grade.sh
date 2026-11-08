#!/usr/bin/env bash
# Grade the candidate project in the working directory against a task's spec, one tier at a time:
#   grade.sh <task> static    loads and compiles every workflow and checks the argument contract
#   grade.sh <task> runtime   runs Main.xaml headlessly under CoreWF in every scenario
# <task> names a sibling folder holding specs/<task>.json.
#
# The verifier runs the workflow with the XAML runner (_runner, CoreWF with UiPath.System.Activities
# 26.8.2), which pre_run builds into $XAML_RUNNER_DIR (default /opt/xaml-runner), and which is built here
# if missing; the build needs the .NET 10 SDK and the public NuGet feeds in _runner/nuget.config.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
task="${1:?usage: grade.sh <task> static|runtime}"
tier="${2:?usage: grade.sh <task> static|runtime}"
dir="${XAML_RUNNER_DIR:-/opt/xaml-runner}"
if [ ! -f "$dir/XamlRunner.dll" ]; then
  build="$(mktemp -d)"
  cp -R "$here/_runner/." "$build/"
  dotnet publish "$build/XamlRunner.csproj" -c Release -o "$dir" --nologo -v quiet >&2
fi
export XAML_RUNNER="$dir/XamlRunner.dll"
exec python3 "$here/_verifier/verify.py" --spec "$here/../$task/specs/$task.json" --tiers "$tier" --reward-file "$tier.json"
