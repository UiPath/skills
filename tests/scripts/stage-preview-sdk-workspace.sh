#!/usr/bin/env bash
set -euo pipefail

sdk_root=${PREVIEW_FLOW_SDK_ROOT:-/opt/preview-flow-sdk}
assets_root=${PREVIEW_FLOW_SDK_ASSETS_ROOT:-/opt/preview-flow-sdk-assets}
package_dir=$sdk_root/node_modules/@uipath/flow-sdk
library_json=${FLOW_SDK_LIBRARY_JSON:-$assets_root/library-json}
registry_root=${UIP_MAESTRO_REGISTRY_HOME:-$assets_root/registry}
registry_current=$registry_root/current.json

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
[[ -f "$registry_current" ]] || {
  echo "stage-preview-sdk-workspace: missing connector registry provenance at $registry_current" >&2
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
sdk_gitref=$(node - "$package_dir/package.json" <<'NODE'
const fs = require('node:fs');
console.log(JSON.parse(fs.readFileSync(process.argv[2], 'utf8')).gitref || '');
NODE
)
registry_hash=$(node - "$registry_current" <<'NODE'
const fs = require('node:fs');
const {libraryHash} = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (typeof libraryHash !== 'string' || !libraryHash) {
  throw new Error('connector registry provenance is missing libraryHash');
}
console.log(libraryHash);
NODE
)

ln -s "$sdk_root/node_modules" node_modules
node - "$sdk_version" "$sdk_gitref" "$registry_hash" <<'NODE'
const fs = require('node:fs');
const version = process.argv[2];
const gitref = process.argv[3];
const connectorLibraryHash = process.argv[4];
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
    gitref: gitref || null,
    connector_library: true,
    connector_library_hash: connectorLibraryHash,
  }, null, 2)}\n`,
);
NODE

node -e "import('@uipath/flow-sdk')"
uip maestro flow compile --help >/dev/null
printf 'stage-preview-sdk-workspace: @uipath/flow-sdk@%s, connector library %s\n' \
  "$sdk_version" "$registry_hash"
