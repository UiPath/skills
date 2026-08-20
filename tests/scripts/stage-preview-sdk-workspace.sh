#!/usr/bin/env bash
set -euo pipefail

sdk_root="${PREVIEW_FLOW_SDK_ROOT:-/opt/preview-flow-sdk}"
package_dir="$sdk_root/node_modules/@uipath/flow-sdk"

[ -f "$package_dir/package.json" ] || {
  echo "stage-preview-sdk-workspace: missing $package_dir/package.json" >&2
  exit 1
}
[ ! -e node_modules ] || {
  echo "stage-preview-sdk-workspace: node_modules already exists" >&2
  exit 1
}

sdk_version="$(node -p "require('$package_dir/package.json').version")"
ln -s "$sdk_root/node_modules" node_modules
node - "$sdk_version" <<'NODE'
const fs = require('node:fs');
const version = process.argv[2];
const packageJson = {
  private: true,
  type: 'module',
  devDependencies: { '@uipath/flow-sdk': version },
  flowSdk: { emitOnly: true },
};
fs.writeFileSync('package.json', `${JSON.stringify(packageJson, null, 2)}\n`);
fs.writeFileSync(
  'preview-sdk-provenance.json',
  `${JSON.stringify({ package: '@uipath/flow-sdk', version, mode: 'emit-only' }, null, 2)}\n`,
);
NODE

node -e "import('@uipath/flow-sdk')"
uip maestro flow compile --help >/dev/null
printf 'stage-preview-sdk-workspace: @uipath/flow-sdk@%s, emit-only\n' "$sdk_version"
