#!/usr/bin/env node
// ensure-migrator.mjs — locate, download, and verify the UiPath Activity Migrator (UiPath.Upgrade.exe).
//
// Usage: node ensure-migrator.mjs [--check-only] [--force]
//   --check-only  report what is cached without downloading; exit 3 with status "missing" when nothing is
//   --force       re-download and re-extract even when cached
// Env:   UIPATH_ACTIVITY_MIGRATOR_DIR      install/cache root (default %LOCALAPPDATA%\UiPath\ActivityMigrator)
//        UIPATH_ACTIVITY_MIGRATOR_URL      archive URL (default https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip)
//        UIPATH_ACTIVITY_MIGRATOR_OFFLINE  set to 1 to never touch the network
// Output: the last stdout line is one JSON object; see references/acquisition-guide.md § Script output contract.
// Exit:  0 ok, 1 error, 3 missing (check-only). No dependencies. Node 18+.
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
const CHECK_ONLY = args.includes('--check-only');
const FORCE = args.includes('--force');

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
  fail('not-windows', 'The Activity Migrator is a Windows-only .NET 8 desktop tool. Run this skill from a Windows machine that holds the project.');
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

if (!exe && CHECK_ONLY) emit({ status: 'missing', dir: root }, 3);
if (!exe && OFFLINE) {
  fail('offline-missing', `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1 and no tool found under ${root}. Place the extracted archive there; see references/acquisition-guide.md § Manual placement.`);
}

// --- 3. Decide whether to download ----------------------------------------
let needDownload = false;
let isUpdate = false;
if (!exe || FORCE) {
  needDownload = true;
} else if (source !== 'env' && !OFFLINE && !CHECK_ONLY) {
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
  if (remoteLm && localLm && remoteLm !== localLm) {
    needDownload = true;
    isUpdate = true;
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

// --- 5. .NET Desktop Runtime 8 ---------------------------------------------
// Check the one place the migrator's launcher loads its runtime from: a set DOTNET_ROOT_X64 or DOTNET_ROOT, with no
// fallback; otherwise the location the .NET installer registers (32-bit registry view), else %ProgramFiles%\dotnet.
// The launcher never looks at PATH, so a dotnet on PATH says nothing about what the tool will load.
let dotnetRootVar = '';
if (process.env.DOTNET_ROOT_X64) dotnetRootVar = 'DOTNET_ROOT_X64';
else if (process.env.DOTNET_ROOT) dotnetRootVar = 'DOTNET_ROOT';
const registeredDotnet = () => {
  const reg = join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'reg.exe');
  const q = run(reg, ['query', 'HKLM\\SOFTWARE\\dotnet\\Setup\\InstalledVersions\\x64', '/v', 'InstallLocation', '/reg:32']);
  const m = q.ok ? /InstallLocation\s+REG_SZ\s+(.+)/i.exec(q.out) : null;
  return m ? m[1].trim() : '';
};
const dotnetDir = dotnetRootVar
  ? process.env[dotnetRootVar]
  : registeredDotnet() || join(process.env.ProgramFiles || 'C:\\Program Files', 'dotnet');
const dotnetExe = join(dotnetDir, 'dotnet.exe');
const list = isFile(dotnetExe) ? run(dotnetExe, ['--list-runtimes']) : null;
let runtime = '';
for (const line of list?.ok ? list.out.split(/\r?\n/) : []) {
  const parts = line.trim().split(/\s+/);
  if (parts[0] === 'Microsoft.WindowsDesktop.App' && /^8\./.test(parts[1] || '')) runtime = parts[1];
}
if (!runtime) {
  const fix = dotnetRootVar
    ? `, the only place the migrator loads its runtime from while ${dotnetRootVar} is set. Unset ${dotnetRootVar}, or install the runtime there, and rerun.`
    : ', where the migrator loads its runtime from. Install the .NET Desktop Runtime 8 (x64) from https://dotnet.microsoft.com/download/dotnet/8.0 and rerun.';
  fail('runtime-missing', `Microsoft.WindowsDesktop.App 8.x not found in ${dotnetDir}` + fix);
}

// --- 6. Verify the tool answers --------------------------------------------
// The tool's own stderr names why it could not start, such as a runtime it cannot resolve; a re-download never fixes
// that. .NET launch errors lead with the cause and end with links, so the start of the text is kept.
const ver = run(exe, ['version'], { timeout: 60000 });
const version = ver.out.split(/\r?\n/).map((l) => l.trim()).filter(Boolean).pop() || '';
if (!ver.ok || !version) {
  const detail = head(ver.err, 400) || (ver.status == null ? 'no output' : `exit code ${ver.status}, no output`);
  fail('verify-failed', `${exe} did not print a version (${detail}). When that names a missing runtime or framework, fix it as it says; otherwise the install may be incomplete: rerun with --force.`);
}

emit({ status: 'ok', exe, version, source, runtime }, 0);
