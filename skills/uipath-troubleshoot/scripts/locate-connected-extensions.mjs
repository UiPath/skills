#!/usr/bin/env node
// locate-connected-extensions.mjs — find the extensions component (SetupExtensions.exe and the extension
// files) that the UiPath Connected installer put on this machine. Read-only. Windows only.
//
// Usage: node locate-connected-extensions.mjs
// Output: the last stdout line is one JSON object:
//   status             ok | component-missing | connected-missing | unsupported-os
//   scope              user | machine
//   updaterAppPath     the Connected Updater executable, from its apiconfig.json
//   component          name, version, directory, setupExtensionsPath
// Exit:  0 found, 1 unsupported OS, 3 anything else. No dependencies. Node 18+.

import { existsSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { emit, requireUpdater } from './connected-installer.mjs';

const { scope, updaterAppPath } = requireUpdater();
// The Updater is at <platform root>\Updater\<exe>; a product is at <platform root>\<name>\<version>.
const platformRoot = dirname(dirname(updaterAppPath));

// The component folder may be named BrowserExtensions or DriverExtensions.
for (const name of ['BrowserExtensions', 'DriverExtensions']) {
  let versions = [];
  try {
    versions = readdirSync(join(platformRoot, name));
  } catch {
    continue;
  }
  // Intentionally not sorted: the first version folder that holds SetupExtensions.exe is used.
  for (const version of versions) {
    const directory = join(platformRoot, name, version);
    const setupExtensionsPath = join(directory, 'SetupExtensions.exe');
    if (existsSync(setupExtensionsPath)) emit({ status: 'ok', scope, updaterAppPath, component: { name, version, directory, setupExtensionsPath } }, 0);
  }
}
emit({ status: 'component-missing', scope, updaterAppPath }, 3);
