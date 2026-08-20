#!/usr/bin/env bash
set -euo pipefail

sdk_root="${PREVIEW_FLOW_SDK_ROOT:-/opt/preview-flow-sdk}"
assets_root="${PREVIEW_FLOW_SDK_ASSETS_ROOT:-/opt/preview-flow-sdk-assets}"
package_dir="$sdk_root/node_modules/@uipath/flow-sdk"

[ -f "$package_dir/package.json" ] || {
  echo "stage-preview-sdk-workspace: missing $package_dir/package.json" >&2
  exit 1
}
[ ! -e node_modules ] || {
  echo "stage-preview-sdk-workspace: node_modules already exists" >&2
  exit 1
}

# coder-eval defines TASK_DIR from the host checkout path. The preview arm
# deliberately mounts that checkout at SKILLS_REPO_PATH instead, so recreate
# the host path as a container-local symlink for frozen criteria that execute
# `python3 $TASK_DIR/check_*.py`.
case "${TASK_DIR:-}" in
  */tests/tasks/*) task_repo_path="${TASK_DIR%%/tests/tasks/*}" ;;
  *)
    echo "stage-preview-sdk-workspace: TASK_DIR must be an absolute tests/tasks path" >&2
    exit 1
    ;;
esac
[ -d "${SKILLS_REPO_PATH:?SKILLS_REPO_PATH is required}/tests/tasks" ] || {
  echo "stage-preview-sdk-workspace: $SKILLS_REPO_PATH is not the checker repo" >&2
  exit 1
}
if [ "$task_repo_path" != "$SKILLS_REPO_PATH" ]; then
  mkdir -p "$(dirname "$task_repo_path")"
  if [ -e "$task_repo_path" ] || [ -L "$task_repo_path" ]; then
    [ "$(realpath "$task_repo_path")" = "$(realpath "$SKILLS_REPO_PATH")" ] || {
      echo "stage-preview-sdk-workspace: $task_repo_path already exists and is not $SKILLS_REPO_PATH" >&2
      exit 1
    }
  else
    ln -s "$SKILLS_REPO_PATH" "$task_repo_path"
  fi
fi

library_json="${FLOW_SDK_LIBRARY_JSON:?FLOW_SDK_LIBRARY_JSON is required}"
[ -f "$library_json/index.json" ] || {
  echo "stage-preview-sdk-workspace: missing connector library index at $library_json" >&2
  exit 1
}
flow_builder_sdk_commit="$(tr -d '[:space:]' < "$assets_root/flow-builder-sdk.sha")"
[ -n "$flow_builder_sdk_commit" ] || {
  echo "stage-preview-sdk-workspace: missing flow-builder-sdk provenance" >&2
  exit 1
}
node - "$library_json/index.json" <<'NODE'
const fs = require('node:fs');
const index = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const required = 'uipath.connector.uipath-uipath-dataservice.query-entity-records';
if (!index.entries?.some(({ nodeType }) => nodeType === required)) {
  throw new Error(`connector library is missing ${required}`);
}
NODE

sdk_version="$(node -p "require('$package_dir/package.json').version")"
ln -s "$sdk_root/node_modules" node_modules
node - "$sdk_version" "$flow_builder_sdk_commit" <<'NODE'
const fs = require('node:fs');
const version = process.argv[2];
const flowBuilderSdkCommit = process.argv[3];
const packageJson = {
  private: true,
  type: 'module',
  devDependencies: { '@uipath/flow-sdk': version },
  flowSdk: { emitOnly: true },
};
fs.writeFileSync('package.json', `${JSON.stringify(packageJson, null, 2)}\n`);
fs.writeFileSync(
  'preview-sdk-provenance.json',
  `${JSON.stringify({
    package: '@uipath/flow-sdk',
    version,
    mode: 'emit-only',
    flow_builder_sdk_commit: flowBuilderSdkCommit,
    connector_library: true,
  }, null, 2)}\n`,
);
NODE

node -e "import('@uipath/flow-sdk')"
uip maestro flow compile --help >/dev/null
prepare-connector --help >/dev/null
printf 'stage-preview-sdk-workspace: @uipath/flow-sdk@%s, flow-builder-sdk@%s, connector library, emit-only\n' \
  "$sdk_version" "$flow_builder_sdk_commit"
