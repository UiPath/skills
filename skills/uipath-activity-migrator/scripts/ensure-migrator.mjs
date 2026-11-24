#!/usr/bin/env node
// ensure-migrator.mjs — locate and verify the UiPath Activity Migrator (UiPath.Upgrade.exe); install it only when asked.
//
// Usage: node ensure-migrator.mjs [--install] [--force]
//   (no flag)  locate a cached tool, verify it, and report whether UiPath published a newer archive; never download.
//              Exit 3 with status "missing" when nothing is cached: the caller asks the user before installing.
//   --install  download and extract when nothing is cached; replace the cache when the archive changed
//   --force    re-download and re-extract even when cached (implies --install)
// Env:   UIPATH_ACTIVITY_MIGRATOR_DIR      install/cache root (default %LOCALAPPDATA%\UiPath\ActivityMigrator)
//        UIPATH_ACTIVITY_MIGRATOR_URL      archive URL (default https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip)
//        UIPATH_ACTIVITY_MIGRATOR_OFFLINE  set to 1 to never touch the network; wins over --install and --force
//        UIPATH_TELEMETRY_DISABLED         read only: a value other than true/false that crashes the tool is reported
// Output: the last stdout line is one JSON object; see references/acquisition-guide.md § Script output contract.
// Exit:  0 ok, 1 error, 3 missing. No dependencies. Node 18+.
//
// Node runs the whole flow so no .ps1 or .sh file is executed: script execution policies and hosts that gate
// PowerShell script invocations never apply. Network and archive work is delegated to the Windows tools that
// already handle proxies and zips: curl (HTTPS_PROXY), then PowerShell's WebClient as a -Command (system proxy).

import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const DEFAULT_URL = 'https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip';
const ARCHIVE_URL = process.env.UIPATH_ACTIVITY_MIGRATOR_URL || DEFAULT_URL;
const OFFLINE = process.env.UIPATH_ACTIVITY_MIGRATOR_OFFLINE === '1';
const args = process.argv.slice(2);
// Downloading an executable is opt-in: the flag comes from a caller that holds the user's consent. Offline wins over
// it; nothing else makes the script touch the archive.
const FORCE = args.includes('--force') && !OFFLINE;
const INSTALL = !OFFLINE && (FORCE || args.includes('--install'));

const emit = (obj, code) => {
  process.stdout.write(JSON.stringify(obj) + '\n');
  process.exit(code);
};
const fail = (code, message) => emit({ status: 'error', code, message }, 1);

const run = (cmd, argv, opts = {}) => {
  const r = spawnSync(cmd, argv, { encoding: 'utf8', windowsHide: true, maxBuffer: 16 * 1024 * 1024, ...opts });
  return { ok: !r.error && r.status === 0, status: r.status, missing: r.error?.code === 'ENOENT', out: r.stdout || '', err: (r.stderr || '') + (r.error ? String(r.error.message) : '') };
};
// PowerShell -Command, never -File: execution policy governs script files only. Stop makes a failing cmdlet a
// non-zero exit; without it -Command exits 0 after Expand-Archive fails and rolls back.
const powershell = (command, opts) =>
  run('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; " + command], opts);
const psq = (s) => "'" + String(s).replace(/'/g, "''") + "'";
// Windows curl reads only HTTPS_PROXY; these give PowerShell requests the system proxy and the signed-in user's credentials.
const PS_TLS = '[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12; ';
const psProxy = (v) => `${v}.Proxy = [System.Net.WebRequest]::DefaultWebProxy; if ($null -ne ${v}.Proxy) { ${v}.Proxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials }; `;
const isFile = (p) => { try { return statSync(p).isFile(); } catch { return false; } };
const isDir = (p) => { try { return statSync(p).isDirectory(); } catch { return false; } };
// Git Bash may hand a POSIX-style path (/c/tools) to a native process; normalize it to a Windows path.
const toWin = (p) => p.replace(/^\/([a-zA-Z])(\/|$)/, (_, d) => d.toUpperCase() + ':\\').replace(/\//g, '\\');
const lastModified = (headerText) => {
  let v = '';
  for (const line of headerText.split(/\r?\n/)) {
    const m = /^last-modified:\s*(.*)$/i.exec(line);
    if (m) v = m[1].trim();
  }
  return v;
};
const tail = (s, n) => s.replace(/[\r\n]+/g, ' ').trim().slice(-n);
const head = (s, n) => s.replace(/\s+/g, ' ').trim().slice(0, n);

// --- 1. Windows only -------------------------------------------------------
if (process.platform !== 'win32') {
  fail('not-windows', 'The Activity Migrator is a Windows-only .NET desktop tool. Run this skill from a Windows machine that holds the project.');
}

// --- 2. Resolve install root and any existing exe --------------------------
let source = '';
let root;
if (process.env.UIPATH_ACTIVITY_MIGRATOR_DIR) {
  root = toWin(process.env.UIPATH_ACTIVITY_MIGRATOR_DIR);
  source = 'env';
} else {
  if (!process.env.LOCALAPPDATA) fail('verify-failed', 'LOCALAPPDATA is not set. Set UIPATH_ACTIVITY_MIGRATOR_DIR to an install folder.');
  root = join(process.env.LOCALAPPDATA, 'UiPath', 'ActivityMigrator');
}
const current = join(root, 'current');
const stamp = join(root, '.last-modified');
let exe = '';
if (isFile(join(root, 'UiPath.Upgrade.exe'))) exe = join(root, 'UiPath.Upgrade.exe');
else if (isFile(join(current, 'UiPath.Upgrade.exe'))) exe = join(current, 'UiPath.Upgrade.exe');
if (!source) source = 'cached';

if (!exe && OFFLINE) {
  fail('offline-missing', `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1 and no tool found under ${root}. Place the extracted archive there; see references/acquisition-guide.md § Manual placement.`);
}
// Nothing cached and nobody consented to a download: report, so the caller can ask the user.
if (!exe && !INSTALL) emit({ status: 'missing', dir: root, url: ARCHIVE_URL }, 3);

// --- 3. Decide whether to download ----------------------------------------
let needDownload = !exe || FORCE;
let isUpdate = false;
let updateAvailable = false;
if (!needDownload && source !== 'env' && !OFFLINE) {
  const head = run('curl', ['-sSIL', '--max-time', '20', ARCHIVE_URL], { timeout: 30000 });
  let remoteLm = head.ok ? lastModified(head.out) : '';
  // Behind a system proxy curl's HEAD fails every time; without this retry the cache would never update and nothing would say so.
  if (!remoteLm) {
    const psHead = powershell(
      `try { ${PS_TLS}$r = [System.Net.WebRequest]::Create(${psq(ARCHIVE_URL)}); $r.Method = 'HEAD'; $r.Timeout = 20000; ${psProxy('$r')}` +
      "$resp = $r.GetResponse(); $lm = $resp.Headers['Last-Modified']; $resp.Close(); if ($lm) { [Console]::Out.Write(([string]$lm).Trim()) } } catch { exit 1 }",
      { timeout: 40000 },
    );
    if (psHead.ok) remoteLm = psHead.out.trim();
  }
  // A stamp written by hand may carry a UTF-8 BOM; strip it or every run looks like an update.
  const localLm = existsSync(stamp) ? readFileSync(stamp, 'utf8').replace(/^\uFEFF/, '').replace(/[\r\n]/g, '').trim() : '';
  // A changed archive is replaced only on an install run; a plain run reports it and keeps the cached tool.
  if (remoteLm && localLm && remoteLm !== localLm) {
    if (INSTALL) {
      needDownload = true;
      isUpdate = true;
    } else {
      updateAvailable = true;
    }
  }
  if (remoteLm && !localLm) writeFileSync(stamp, remoteLm, 'ascii');
}

// --- 4. Download and extract ----------------------------------------------
if (needDownload) {
  try { mkdirSync(root, { recursive: true }); } catch { fail('download-failed', `Cannot create ${root}.`); }
  // Must end in .zip: Windows PowerShell 5.1's Expand-Archive rejects any other extension.
  const tmpZip = join(root, 'UiPath.Upgrade.Cli.download.zip');
  const headers = join(root, '.headers.tmp');
  rmSync(tmpZip, { force: true });
  rmSync(headers, { force: true });

  let newLm = '';
  let downloaded = false;
  const errors = [];
  // A stalled connection (under 1 KB/s for a minute) fails instead of hanging.
  const curl = run('curl', ['-fsSL', '--retry', '3', '--retry-delay', '2', '--connect-timeout', '20', '--speed-limit', '1024', '--speed-time', '60', '-D', headers, '-o', tmpZip, ARCHIVE_URL]);
  if (curl.ok && isFile(tmpZip)) {
    downloaded = true;
    newLm = existsSync(headers) ? lastModified(readFileSync(headers, 'utf8')) : '';
  } else {
    // curl repeats its error once per retry; the last line is the one that ended it.
    const curlLast = curl.err.trim().split(/\r?\n/).filter(Boolean).pop() || '';
    errors.push(curl.missing ? 'curl: not found' : tail(curlLast, 300) || 'curl failed');
    rmSync(tmpZip, { force: true });
    // The catch reports the innermost exception's message, such as a proxy's "(407) Proxy Authentication
    // Required", not PowerShell's error-record formatting.
    const ps = powershell(
      `try { ${PS_TLS}$wc = New-Object System.Net.WebClient; ${psProxy('$wc')}` +
      `$wc.DownloadFile(${psq(ARCHIVE_URL)}, ${psq(tmpZip)}); $lm = $wc.ResponseHeaders['Last-Modified']; if ($lm) { [Console]::Out.Write(([string]$lm).Trim()) } ` +
      '} catch { $e = $_.Exception; while ($e.InnerException) { $e = $e.InnerException }; [Console]::Error.Write($e.Message); exit 1 }',
    );
    if (ps.ok && isFile(tmpZip)) {
      downloaded = true;
      newLm = ps.out.trim();
    } else {
      errors.push('PowerShell WebClient: ' + (ps.missing ? 'not found' : tail(ps.err, 300)));
    }
  }
  rmSync(headers, { force: true });
  if (!downloaded) {
    rmSync(tmpZip, { force: true });
    fail('download-failed', `Download failed (${errors.join('; ')}). Check proxy settings (HTTPS_PROXY for curl, the system proxy for PowerShell) or place the tool manually; see references/acquisition-guide.md § Manual placement.`);
  }

  const stage = join(root, '.extract-tmp');
  rmSync(stage, { recursive: true, force: true });
  mkdirSync(stage, { recursive: true });
  const systemTar = join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'tar.exe');
  const extracted =
    powershell(`Expand-Archive -LiteralPath ${psq(tmpZip)} -DestinationPath ${psq(stage)} -Force`).ok ||
    (isFile(systemTar) && run(systemTar, ['-xf', tmpZip, '-C', stage]).ok) ||
    run('unzip', ['-q', '-o', tmpZip, '-d', stage]).ok;
  if (!extracted) {
    rmSync(stage, { recursive: true, force: true });
    fail('extract-failed', `Could not extract ${tmpZip} with Expand-Archive, tar, or unzip. Extract it manually into ${current}.`);
  }
  if (!isFile(join(stage, 'UiPath.Upgrade.exe')) || !isDir(join(stage, 'Extensions'))) {
    rmSync(stage, { recursive: true, force: true });
    fail('extract-failed', 'Archive layout unexpected: UiPath.Upgrade.exe or Extensions/ missing after extraction.');
  }
  try {
    rmSync(current, { recursive: true, force: true });
    renameSync(stage, current);
  } catch {
    fail('extract-failed', `Could not replace ${current}.`);
  }
  rmSync(tmpZip, { force: true });
  if (newLm) writeFileSync(stamp, newLm, 'ascii');
  exe = join(current, 'UiPath.Upgrade.exe');
  source = isUpdate ? 'updated' : 'downloaded';
}

// --- 5. Verify the tool answers --------------------------------------------
// Starting the tool is the only check of its .NET runtime. Which runtime a build needs, where the launcher looks for it
// and what a roll-forward setting lets it accept are the launcher's rules; a copy of them here would name the wrong
// runtime for a build that targets another .NET, and refuse a tool that starts.
const ver = run(exe, ['version'], { timeout: 60000 });
const lastLine = (s) => s.split(/\r?\n/).map((l) => l.trim()).findLast(Boolean) || '';
const version = lastLine(ver.out);

// .NET's launcher exits with these codes before any tool code runs. FRAMEWORK_MISSING: it found a .NET install without
// the runtime this build needs. HOST_MISSING: it found no .NET install; a broken install exits the same way, so there
// the launcher's text decides, and anything else stays a verify failure that relays the text.
const FRAMEWORK_MISSING = 0x80008096;
const HOST_MISSING = 0x80008083;
if (ver.status === FRAMEWORK_MISSING || (ver.status === HOST_MISSING && /You must install \.NET to run this application/i.test(ver.err))) {
  const hostLine = (re) => (re.exec(ver.err) || [])[1]?.trim() || '';
  // The build's runtimeconfig, next to the exe, names the .NET it targets. It only words the fix; unreadable, the
  // launcher's text is relayed instead. The launcher's first missing framework is the base runtime, and its download
  // link installs that one alone, so the fix names the Desktop Runtime, which holds both frameworks the tool loads.
  let major = '';
  try {
    const opts = JSON.parse(readFileSync(exe.replace(/\.exe$/i, '.runtimeconfig.json'), 'utf8')).runtimeOptions;
    const frameworks = opts.frameworks || [opts.framework];
    const target = frameworks.find((f) => f.name === 'Microsoft.WindowsDesktop.App') || frameworks.find((f) => f.name === 'Microsoft.NETCore.App');
    major = /^(\d+)\./.exec(target.version)[1];
  } catch { /* no major: the launcher's text names the version */ }
  const arch = hostLine(/^Architecture:\s*(\S+)/m) || 'x64';
  const runtimeName = major ? `the .NET Desktop Runtime ${major} (${arch})` : `a .NET Desktop Runtime (${arch})`;
  const page = 'https://dotnet.microsoft.com/download/dotnet' + (major ? `/${major}.0` : '');
  const reported = major ? '' : ` The launcher names the version: ${head(ver.err, 400)}`;
  // The launcher lists what it found of the framework it missed: the reason an installed .NET did not count.
  const found = [...ver.err.matchAll(/^[ \t]+(\d+\.\d+\.\S+) at \[/gm)].map((m) => m[1]);
  const others = found.length ? ` Versions found there, none of which this build accepts: ${found.join(', ')}.` : '';
  // The launcher takes the first of DOTNET_ROOT_<ARCH> and DOTNET_ROOT that names an existing folder and looks nowhere
  // else, so an install into the default location would change nothing. A variable that names no folder is skipped;
  // with neither left, the launcher uses the default location, reported below.
  const rootVar = [`DOTNET_ROOT_${arch.toUpperCase()}`, 'DOTNET_ROOT'].find((name) => process.env[name] && isDir(process.env[name]));
  if (rootVar) {
    fail('runtime-missing', `${exe} needs ${runtimeName}, which is not in ${process.env[rootVar]}, the only place the migrator loads its runtime from while ${rootVar} is set.${others} Unset ${rootVar}, or install the runtime there, and rerun.${reported}`);
  }
  const where = hostLine(/^\.NET location:[ \t]*(\S.*)$/m);
  const place = where && !/^not found$/i.test(where) ? ` in ${where}, where the migrator loads its runtime from.` : ': no .NET install was found on this machine.';
  fail('runtime-missing', `${exe} needs ${runtimeName}, which is not installed${place}${others} Install ${runtimeName} from ${page} and rerun.${reported}`);
}

// The 25.10 builds parse UIPATH_TELEMETRY_DISABLED with bool.Parse and crash at startup on any value but true or
// false, such as the documented 1. Prove it with a retry under the strict spelling of the user's choice; never unset
// the variable, which would turn the user's telemetry back on.
const telemetry = process.env.UIPATH_TELEMETRY_DISABLED;
if ((!ver.ok || !version) && telemetry !== undefined && !/^\s*(true|false)\s*$/i.test(telemetry)) {
  const strict = /^\s*(0|no|off)\s*$/i.test(telemetry) ? 'false' : 'true';
  const retry = run(exe, ['version'], { timeout: 60000, env: { ...process.env, UIPATH_TELEMETRY_DISABLED: strict } });
  if (retry.ok && lastLine(retry.out)) {
    emit({ status: 'error', code: 'telemetry-flag', env: `UIPATH_TELEMETRY_DISABLED=${strict}`, message: `${exe} crashes at startup while UIPATH_TELEMETRY_DISABLED is ${JSON.stringify(telemetry)}: this build accepts only true or false. It starts with UIPATH_TELEMETRY_DISABLED=${strict}, the same choice. Prefix this script and every UiPath.Upgrade.exe command with it; never unset the variable.` }, 1);
  }
}
// Any other failure: the tool's own stderr names why it could not start. .NET launch errors lead with the cause and end
// with links, so the start of the text is kept.
if (!ver.ok || !version) {
  const detail = head(ver.err, 400) || (ver.status == null ? 'no output' : `exit code ${ver.status}, no output`);
  fail('verify-failed', `${exe} did not print a version (${detail}). When that names a missing runtime or framework, fix it as it says; otherwise the install may be incomplete: rerun with --force.`);
}

const result = { status: 'ok', exe, version, source };
if (updateAvailable) result.update = true;
emit(result, 0);
