#!/usr/bin/env node
// read-extensions-status.mjs — read the installation status of the UiPath extensions (Chrome, Edge, Firefox, Java,
// remote-desktop clients, ...) from the SetupExtensions.exe of the Connected installer's extensions component.
// Read-only. Windows only.
//
// Usage: node read-extensions-status.mjs [EXTENSION_NAME] [--per-user]
//   --per-user   read the per-user status: its commands install for the current user only
// Output: the last stdout line is one JSON object:
//   status             ok | bad-arguments | status-failed | component-missing | connected-missing | unsupported-os
//   scope              user | machine
//   setupExtensionsPath  the tool that was asked
//   perUser            whether the per-user status was read
//   extensions         what the tool reports, unfiltered, keyed by extension name: the named extension only, or
//                      all of them when none is named
//   error              with status-failed: why the tool gave no status
// Exit:  0 ok, 1 unsupported OS, bad-arguments or status-failed, 3 the component could not be located.
// No dependencies. Node 18+.

import { emit, readExtensionsStatus, requireExtensionsComponent } from './connected-installer.mjs';

const perUser = process.argv.includes('--per-user');
const [extension] = process.argv.slice(2).filter((a) => a !== '--per-user');

const located = requireExtensionsComponent();
const status = readExtensionsStatus(located, perUser);
if (extension && !status[extension]) emit({ status: 'bad-arguments', usage: 'read-extensions-status.mjs [EXTENSION_NAME] [--per-user]', extensions: Object.keys(status) }, 1);

const extensions = extension ? { [extension]: status[extension] } : status;
emit({ status: 'ok', scope: located.scope, setupExtensionsPath: located.component.setupExtensionsPath, perUser, extensions }, 0);
