// connected-installer.mjs — what the Connected installer scripts share: the JSON result line and finding the Updater.
// Not run on its own. No dependencies. Node 18+.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';

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
