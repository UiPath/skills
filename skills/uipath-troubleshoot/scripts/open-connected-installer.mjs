#!/usr/bin/env node
// open-connected-installer.mjs — open the UiPath Connected installer window (Updater `change -interactive`) so the
// user can add or remove components. Installs nothing by itself. Windows only.
//
// Usage: node open-connected-installer.mjs
// Output: the last stdout line is one JSON object:
//   status             opened | open-failed | connected-missing | unsupported-os
//   scope              user | machine
//   updaterAppPath     the Connected Updater executable, from its apiconfig.json
//   error              with open-failed: why the Updater could not be started
// Exit:  0 opened, 1 unsupported OS or open-failed, 3 connected-missing. No dependencies. Node 18+.

import { spawn } from 'node:child_process';
import { emit, requireUpdater } from './connected-installer.mjs';

const { scope, updaterAppPath, scopeArgs } = requireUpdater();

// The window outlives this script: start it detached and report as soon as it is launched.
const installer = spawn(updaterAppPath, ['change', '-interactive', ...scopeArgs], { detached: true, stdio: 'ignore' });
installer.on('error', (e) => emit({ status: 'open-failed', scope, updaterAppPath, error: e.message }, 1));
installer.on('spawn', () => {
  installer.unref();
  emit({ status: 'opened', scope, updaterAppPath }, 0);
});
