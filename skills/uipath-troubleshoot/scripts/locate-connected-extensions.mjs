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

import { emit, requireExtensionsComponent } from './connected-installer.mjs';

emit({ status: 'ok', ...requireExtensionsComponent() }, 0);
