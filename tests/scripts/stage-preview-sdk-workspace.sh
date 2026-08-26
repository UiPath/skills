#!/usr/bin/env bash
set -euo pipefail

sdk_root=${PREVIEW_FLOW_SDK_ROOT:-/opt/preview-flow-sdk}
assets_root=${PREVIEW_FLOW_SDK_ASSETS_ROOT:-/opt/preview-flow-sdk-assets}
package_dir=$sdk_root/node_modules/@uipath/flow-sdk
library_json=${FLOW_SDK_LIBRARY_JSON:-$assets_root/typescript/sdk/lib/library-json}

[[ -f "$package_dir/package.json" ]] || {
  echo "stage-preview-sdk-workspace: missing $package_dir/package.json" >&2
  exit 1
}
[[ ! -e node_modules ]] || {
  echo "stage-preview-sdk-workspace: node_modules already exists" >&2
  exit 1
}
[[ -f "$library_json/index.json" ]] || {
  echo "stage-preview-sdk-workspace: missing connector library index at $library_json" >&2
  exit 1
}

flow_builder_sdk_commit=$(tr -d '[:space:]' < "$assets_root/flow-builder-sdk.sha")
[[ -n "$flow_builder_sdk_commit" ]] || {
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

sdk_version=$(node - "$package_dir/package.json" <<'NODE'
const fs = require('node:fs');
console.log(JSON.parse(fs.readFileSync(process.argv[2], 'utf8')).version);
NODE
)

ln -s "$sdk_root/node_modules" node_modules
node - "$sdk_version" "$flow_builder_sdk_commit" <<'NODE'
const fs = require('node:fs');
const version = process.argv[2];
const flowBuilderSdkCommit = process.argv[3];
let packageJson = {};
if (fs.existsSync('package.json')) {
  packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
}
packageJson.private = true;
packageJson.type = 'module';
packageJson.devDependencies = {
  ...(packageJson.devDependencies || {}),
  '@uipath/flow-sdk': version,
};
fs.writeFileSync('package.json', `${JSON.stringify(packageJson, null, 2)}\n`);
fs.writeFileSync(
  'preview-sdk-provenance.json',
  `${JSON.stringify({
    package: '@uipath/flow-sdk',
    version,
    flow_builder_sdk_commit: flowBuilderSdkCommit,
    connector_library: true,
  }, null, 2)}\n`,
);
NODE

node -e "import('@uipath/flow-sdk')"
uip maestro flow compile --help >/dev/null
prepare-connector --help >/dev/null
printf 'stage-preview-sdk-workspace: @uipath/flow-sdk@%s, flow-builder-sdk@%s, connector library\n' \
  "$sdk_version" "$flow_builder_sdk_commit"
