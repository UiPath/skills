// connected-installer.mjs — what the Connected installer scripts share: the JSON result line, finding the Updater,
// finding the extensions component, and reading the extension status from it. Not run on its own. Windows only. No dependencies. Node 18+.

import { spawnSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

// The last stdout line of every script is one JSON object.
export const emit = (obj, code) => {
  process.stdout.write(JSON.stringify(obj) + '\n');
  process.exit(code);
};

const readUpdaterAppPath = (configRoot) => {
  try {
    const text = readFileSync(join(configRoot, 'UiPathConnected', 'Updater', 'apiconfig.json'), 'utf8');
    return JSON.parse(text.replace(/^\uFEFF/, '')).UpdaterAppPath || null;
  } catch {
    return null;
  }
};

// Returns { scope, updaterAppPath, scopeArgs } for the Connected install on this machine, per-user first, then
// per-machine. scopeArgs go after the verb on every Updater command. Ends the script with status unsupported-os
// (exit 1) off Windows, or connected-missing (exit 3) when no Updater is configured.
export const requireUpdater = () => {
  if (process.platform !== 'win32') emit({ status: 'unsupported-os', os: process.platform }, 1);
  const updater = [
    { scope: 'user', configRoot: process.env.LOCALAPPDATA, scopeArgs: ['-perUser'] },
    { scope: 'machine', configRoot: process.env.ProgramData, scopeArgs: [] },
  ]
    .map(({ scope, configRoot, scopeArgs }) => ({ scope, updaterAppPath: configRoot && readUpdaterAppPath(configRoot), scopeArgs }))
    .find((u) => u.updaterAppPath);
  if (!updater) emit({ status: 'connected-missing' }, 3);
  return updater;
};

// Returns { scope, updaterAppPath, component } where component is the extensions component: name, version, directory,
// setupExtensionsPath. Ends the script with status component-missing (exit 3) when it is not on disk.
export const requireExtensionsComponent = () => {
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
      if (existsSync(setupExtensionsPath)) return { scope, updaterAppPath, component: { name, version, directory, setupExtensionsPath } };
    }
  }
  emit({ status: 'component-missing', scope, updaterAppPath }, 3);
};

// Returns what the SetupExtensions.exe of a located component reports: one entry per extension, including the install
// and uninstall command for each. perUser asks for the per-user status, whose commands install for the current user
// only. Ends the script with status status-failed (exit 1) when the tool gives no status.
export const readExtensionsStatus = ({ scope, component: { setupExtensionsPath } }, perUser = false) => {
  // A per-user Connected install manages per-user extensions; a per-machine one manages them for all users.
  const statusVerb = perUser || scope === 'user' ? '/status-user' : '/status-admin';
  const r = spawnSync(setupExtensionsPath, [statusVerb, '/silent'], { encoding: 'utf8', windowsHide: true, timeout: 60_000, maxBuffer: 16 * 1024 * 1024 });
  try {
    if (r.status !== 0) throw new Error(`SetupExtensions.exe ${statusVerb} exited ${r.status ?? r.error?.message}`);
    return JSON.parse(r.stdout.replace(/^\uFEFF/, ''));
  } catch (e) {
    emit({ status: 'status-failed', scope, setupExtensionsPath, error: e.message }, 1);
  }
};
