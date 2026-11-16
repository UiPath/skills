#!/usr/bin/env node
// ensure-migrator.mjs — locate and verify the UiPath Activity Migrator: Helm's, through uip, else UiPath.Upgrade.exe;
// download the archive only when asked.
//
// Usage: node ensure-migrator.mjs [--install] [--force]
//   (no flag)  ask uip, else locate a cached archive tool, verify it, and report whether UiPath published a newer
//              archive; never download. Exit 3 with status "missing" when nothing is cached: the caller asks the user
//              before installing.
//   --install  archive fallback: download and extract when nothing is cached; replace the cache when the archive changed
//   --force    archive fallback: re-download and re-extract even when cached (implies --install)
// Env:   UIPATH_ACTIVITY_MIGRATOR_DIR      archive fallback: a folder holding UiPath.Upgrade.exe, used as is; also the
//                                          cache root (default %LOCALAPPDATA%\UiPath\ActivityMigrator). Skips uip
//        UIPATH_ACTIVITY_MIGRATOR_URL      archive fallback: the archive URL. Skips uip
//                                          (default https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip)
//        UIPATH_ACTIVITY_MIGRATOR_OFFLINE  archive fallback: set to 1 to never touch the network; wins over --install
//                                          and --force
//        UIPATH_TELEMETRY_DISABLED         archive fallback, read only: a value other than true/false that crashes the
//                                          25.10 builds is reported
// Output: the last stdout line is one JSON object; see references/acquisition-guide.md § Script output contract.
// Exit:  0 ok, 1 error, 3 missing. No dependencies. Node 18+.
//
// The migrator ships inside Helm, which uip installs with rpa-tool: `uip rpa project migrate analyze|upgrade|bulk|version`
// forwards its arguments to `UiPath.Studio.Helm.exe migrate`, and uip resolves the dotnet Helm runs on. The script asks
// `uip rpa project migrate version`. The public archive of the standalone UiPath.Upgrade.exe is the fallback for a
// machine without uip, a uip without `project migrate`, a uip without Helm (helm-missing), or a Helm without the verb.
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

// Why uip could not supply the migrator, once the script fell back to the archive; reported with every later result.
let uipMessage = '';
const emit = (obj, code) => {
  process.stdout.write(JSON.stringify({ ...obj, ...(uipMessage && { uipMessage }) }) + '\n');
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

// --- 2. Ask uip ------------------------------------------------------------
// `uip rpa project migrate version` prints Helm's version as its last stdout line: the migrator is there. It downloads
// nothing, so a plain run and offline mode ask it too; the first run of a Helm version copies Helm into its run slot,
// which can take a while. The command line is fixed text, so the shell (needed for the uip.cmd shim) sees no input.
// uip's own failures are a JSON FailureOutput with a Code, on stdout or stderr. not-windows ends the run; helm-missing,
// an unknown command (a uip older than `project migrate`), no uip at all, or a Helm without the verb fall back.
const lastLine = (s) => s.split(/\r?\n/).map((l) => l.trim()).findLast(Boolean) || '';
const uipFailure = (text) => {
  for (let start = text.indexOf('{'); start >= 0; start = text.indexOf('{', start + 1)) {
    for (let end = text.lastIndexOf('}'); end > start; end = text.lastIndexOf('}', end - 1)) {
      try {
        const reply = JSON.parse(text.slice(start, end + 1));
        if (reply && reply.Result === 'Failure') return reply;
      } catch {
        // not this span
      }
    }
  }
  return null;
};
const UIP_COMMAND = 'uip rpa project migrate';
const fromUip = () => {
  const env = { ...process.env };
  delete env.UIPATH_STUDIO_PID;
  const r = run(`${UIP_COMMAND} version`, [], { shell: true, env, timeout: 5 * 60 * 1000 });
  const reply = uipFailure(r.out) || uipFailure(r.err);
  if (reply) {
    const message = [reply.Message, reply.Instructions].filter(Boolean).join(' ');
    if (reply.Code === 'not-windows') fail('not-windows', `${UIP_COMMAND}: ${message}`);
    uipMessage = `${UIP_COMMAND} version: ${reply.Code ? `${reply.Code}: ` : ''}${message}`;
    return;
  }
  const version = lastLine(r.out);
  if (r.ok && /^\d+\.\d+/.test(version)) emit({ status: 'ok', source: 'uip', command: UIP_COMMAND, version }, 0);
  // No uip on PATH, a uip without the command, or a Helm that does not know `migrate`: their own error text.
  const detail = head(r.err, 300) || head(r.out, 300) || (r.status == null ? 'no output' : `exit code ${r.status}, no output`);
  uipMessage = `${UIP_COMMAND} version: ${detail}`;
};

if (!process.env.UIPATH_ACTIVITY_MIGRATOR_DIR && !process.env.UIPATH_ACTIVITY_MIGRATOR_URL) fromUip();

// --- 3. Archive fallback: resolve install root and any existing exe -------
let source = '';
let exe = '';
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
if (isFile(join(root, 'UiPath.Upgrade.exe'))) exe = join(root, 'UiPath.Upgrade.exe');
else if (isFile(join(current, 'UiPath.Upgrade.exe'))) exe = join(current, 'UiPath.Upgrade.exe');
if (!source) source = 'cached';

if (!exe && OFFLINE) {
  fail('offline-missing', `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1 and no tool found under ${root}. Place the extracted archive there; see references/acquisition-guide.md § Manual placement.`);
}
// Nothing cached and nobody consented to a download: report, so the caller can ask the user.
if (!exe && !INSTALL) emit({ status: 'missing', dir: root, url: ARCHIVE_URL }, 3);

// --- 3b. Decide whether to download ---------------------------------------
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

// --- 5. .NET Desktop Runtime -----------------------------------------------
// The runtime the build asks for comes from UiPath.Upgrade.runtimeconfig.json next to the exe: the 25.10 archives
// target .NET 8, later builds a later major. The host keeps the major version unless the roll-forward policy (the
// file's, or DOTNET_ROLL_FORWARD) is Major or LatestMajor; a prerelease runtime counts only for a prerelease request.
// Check the one place the migrator's launcher loads its runtime from: a set DOTNET_ROOT_X64 or DOTNET_ROOT, with no
// fallback; otherwise the location the .NET installer registers (32-bit registry view), else %ProgramFiles%\dotnet.
// The launcher never looks at PATH, so a dotnet on PATH says nothing about what the tool will load.
const DESKTOP = 'Microsoft.WindowsDesktop.App';
const parseVer = (s) => {
  const m = /^(\d+)\.(\d+)\.(\d+)(-.+)?$/.exec(String(s || '').trim());
  return m ? { parts: [+m[1], +m[2], +m[3]], pre: m[4] !== undefined } : null;
};
const cmpVer = (a, b) => a.parts[0] - b.parts[0] || a.parts[1] - b.parts[1] || a.parts[2] - b.parts[2];
const desktopRuntime = () => {
  const runtimeConfig = exe.replace(/\.exe$/i, '.runtimeconfig.json');
  let need;
  try {
    const opts = JSON.parse(readFileSync(runtimeConfig, 'utf8')).runtimeOptions || {};
    const fw = (opts.frameworks || (opts.framework ? [opts.framework] : [])).find((f) => f && f.name === DESKTOP);
    const parsed = parseVer(fw && fw.version);
    if (!parsed) throw new Error(`it names no ${DESKTOP} version`);
    need = {
      version: fw.version,
      parsed,
      rollForward: String(process.env.DOTNET_ROLL_FORWARD || fw.rollForward || opts.rollForward || 'Minor').toLowerCase(),
    };
  } catch (e) {
    fail('verify-failed', `Cannot read the runtime ${exe} needs from ${runtimeConfig} (${e.message}). The install is incomplete: rerun with --force.`);
  }
  const accepts = (candidate) => {
    const have = parseVer(candidate);
    const want = need.parsed;
    if (!have || (have.pre && !want.pre) || cmpVer(have, want) < 0) return false;
    switch (need.rollForward) {
      case 'disable': return cmpVer(have, want) === 0;
      case 'latestpatch': return have.parts[0] === want.parts[0] && have.parts[1] === want.parts[1];
      case 'major': case 'latestmajor': return true;
      default: return have.parts[0] === want.parts[0];
    }
  };
  const major = need.parsed.parts[0];
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
  let best = '';
  for (const line of list?.ok ? list.out.split(/\r?\n/) : []) {
    const parts = line.trim().split(/\s+/);
    if (parts[0] === DESKTOP && accepts(parts[1]) && (!best || cmpVer(parseVer(parts[1]), parseVer(best)) > 0)) best = parts[1];
  }
  if (best) return best;
  const installer = `the .NET Desktop Runtime ${major} (x64)`;
  const fix = dotnetRootVar
    ? `, the only place the migrator loads its runtime from while ${dotnetRootVar} is set. Unset ${dotnetRootVar}, or install ${installer} there, and rerun.`
    : `, where the migrator loads its runtime from. Install ${installer} from https://dotnet.microsoft.com/download/dotnet/${major}.0 and rerun.`;
  const wanted = need.rollForward === 'major' || need.rollForward === 'latestmajor' ? `${need.version} or later` : `${major}.x (${need.version} or later)`;
  fail('runtime-missing', `${DESKTOP} ${wanted} not found in ${dotnetDir}` + fix);
};
const runtime = desktopRuntime();

// --- 6. Verify the tool answers --------------------------------------------
// The tool's own stderr names why it could not start, such as a runtime it cannot resolve; a re-download never fixes
// that. .NET launch errors lead with the cause and end with links, so the start of the text is kept.
const ver = run(exe, ['version'], { timeout: 60000 });
const version = lastLine(ver.out);
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
if (!ver.ok || !version) {
  const detail = head(ver.err, 400) || (ver.status == null ? 'no output' : `exit code ${ver.status}, no output`);
  fail('verify-failed', `${exe} did not print a version (${detail}). When that names a missing runtime or framework, fix it as it says; otherwise the install may be incomplete: rerun with --force.`);
}

const result = { status: 'ok', source, command: exe, exe, version, runtime };
if (updateAvailable) result.update = true;
emit(result, 0);
