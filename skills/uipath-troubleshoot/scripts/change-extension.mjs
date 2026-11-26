#!/usr/bin/env node
// change-extension.mjs — install or uninstall one UiPath extension with the SetupExtensions.exe of the Connected
// installer's extensions component, using the command of one of the install methods its status lists. Runs the tool
// silently: it shows nothing, and an install may close a running target browser without asking. A command that needs
// admin rights is started elevated, so a UAC prompt appears unless this script already runs elevated. Windows only.
//
// Usage: node change-extension.mjs <install|uninstall> <EXTENSION_NAME> [METHOD_NAME] [--per-user]
//   METHOD_NAME  the Name of the install method to use; without it the first one is used (uninstall: the first
//                installed one)
//   --per-user   without METHOD_NAME, use only a method that needs no admin rights: it changes the extension for the current user only
// Output: the last stdout line is one JSON object:
//   status             installed | uninstalled | change-failed | not-allowed | bad-arguments |
//                      status-failed | component-missing | connected-missing | unsupported-os
//   action, extension, perUser   what was asked
//   method             the Name of the install method whose command was used
//   command            the SetupExtensions.exe arguments that were run
//   exitCode           what SetupExtensions.exe returned
//   entry              what the tool reports for the extension after the command, unfiltered
//   logFile            with change-failed: a file holding everything the tool logged during the command, or null
//                      when nothing was logged where this script can read it
//   reason             with not-allowed: why the action cannot be done on this machine
//   extensions         with bad-arguments: the extension names the tool knows
//   methods            with bad-arguments: the method names of the extension, when METHOD_NAME is not one of them
// Exit:  0 installed or uninstalled, 1 anything else except 3 the component could not be located.
// No dependencies. Node 18+.

import { spawnSync } from 'node:child_process';
import { readFileSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { emit, readExtensionsStatus, requireExtensionsComponent } from './connected-installer.mjs';

const perUser = process.argv.includes('--per-user');
const [action, extension, methodName] = process.argv.slice(2).filter((a) => a !== '--per-user');
const install = action === 'install';
const usage = 'change-extension.mjs <install|uninstall> <EXTENSION_NAME> [METHOD_NAME] [--per-user]';

const located = requireExtensionsComponent();
const { setupExtensionsPath } = located.component;
const status = readExtensionsStatus(located, perUser);
const entry = status[extension];
if ((!install && action !== 'uninstall') || !entry) emit({ status: 'bad-arguments', usage, extensions: Object.keys(status) }, 1);

const asked = { action, extension, perUser };
if (install && !entry.CanInstallExtension) emit({ status: 'not-allowed', ...asked, reason: entry.InstallDisabledReason || null }, 1);

// The command comes from the install methods only; the extension's own InstallCommand and UninstallCommand are not
// used. A named method is taken as is. Otherwise an install takes the first method, an uninstall the first
// installed one; per-user leaves out the methods that need admin rights.
const methods = entry.InstallMethods || [];
if (methodName && !methods.some((m) => m.Name === methodName)) emit({ status: 'bad-arguments', usage, methods: methods.map((m) => m.Name) }, 1);
const isMethod = (m) => (methodName ? m.Name === methodName : (!perUser || !m.NeedsAdminRights) && (install || m.IsInstalled));
const method = methods.find(isMethod);
if (!method) emit({ status: 'not-allowed', ...asked, reason: install ? 'No install method without admin rights.' : `The extension is not installed${perUser ? ' by a method without admin rights' : ''}.` }, 1);
asked.method = method.Name;
const allowed = install ? method.CanInstall : method.CanUninstall;
if (!allowed) emit({ status: 'not-allowed', ...asked, reason: (install ? method.InstallDisabledReason : method.UninstallDisabledReason) || null }, 1);

// Always silent, so that no prompt of the tool can block the run. /force lets a silent install close a running
// browser, in the cases where it has to; an uninstall does not close the browser. /enable-deploy and the product
// name are what the UiPath products pass for a Connected install.
const listed = (install ? method.InstallCommand : method.UninstallCommand).split(' ').filter((a) => a && a !== '/silent');
const args = [...listed, '/silent', '/force', '/enable-deploy', '/product-name=StudioConnected'];
const command = args.join(' ');

// A silent SetupExtensions.exe cannot ask for elevation, so a command that needs admin rights is started elevated
// here: a UAC prompt appears unless this script already runs elevated. When the prompt is not accepted the tool
// never starts: the run fails with nothing logged. The timeout leaves time to answer the prompt.
const quote = (s) => `'${s.replace(/'/g, "''")}'`;
const elevated = `$p = Start-Process -FilePath ${quote(setupExtensionsPath)} -ArgumentList ${quote(command)} -Verb RunAs -WindowStyle Hidden -Wait -PassThru -ErrorAction Stop; exit $p.ExitCode`;
// The tool writes to the driver log of the day when these two variables are set. On a failure, what was appended
// during the command is saved to a file of its own, so that it can be searched without the rest of the day's log.
const env = { ...process.env, UIPATH_FILE_LOGGING: '1', UIPATH_LOG_LEVEL: 'VERBOSE' };
const logPath = join(process.env.LOCALAPPDATA || '', 'UiPath', 'Logs', `${new Date().toLocaleDateString('sv-SE')}_UiPath.Driver.log`);
let logStart = 0;
try {
  logStart = statSync(logPath).size;
} catch {}
const saveLog = () => {
  try {
    const appended = readFileSync(logPath).subarray(logStart);
    if (!appended.length) return null;
    const logFile = join(tmpdir(), `uipath-change-extension-${Date.now()}.log`);
    writeFileSync(logFile, appended);
    return logFile;
  } catch {
    return null;
  }
};

const options = { encoding: 'utf8', windowsHide: true, timeout: 300_000, env };
const r = method.NeedsAdminRights
  ? spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', elevated], options)
  : spawnSync(setupExtensionsPath, args, options);

const after = readExtensionsStatus(located, perUser)[extension];
const done = r.status === 0 && (after.InstallMethods || []).some((m) => m.Name === method.Name && m.IsInstalled === install);
if (done) emit({ status: `${action}ed`, ...asked, command, exitCode: r.status, entry: after }, 0);
emit({ status: 'change-failed', ...asked, command, exitCode: r.status, entry: after, logFile: saveLog() }, 1);
