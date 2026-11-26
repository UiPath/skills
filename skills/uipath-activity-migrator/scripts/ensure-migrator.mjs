#!/usr/bin/env node
// ensure-migrator.mjs — locate and verify the UiPath Activity Migrator: Helm's, through uip, else UiPath.Upgrade.exe;
// download the archive only when asked.
//
// Usage: node ensure-migrator.mjs [--install] [--force]
//   (no flag)  ask uip, else locate a cached archive tool, verify it, and report whether UiPath serves a newer
//              version; never download. Exit 3 with status "missing" when nothing is cached: the caller asks the user
//              before installing.
//   --install  archive fallback: download and extract when nothing is cached; replace the cache when the server holds
//              a newer version
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
// forwards its arguments to `UiPath.Upgrade.exe` in Helm's folder (Helm's apphost under another name), on the dotnet
// uip resolves for Helm. The script asks
// `uip rpa project migrate version`. The public archive of the standalone UiPath.Upgrade.exe is the fallback for a
// machine without uip, a uip without `project migrate`, a uip without Helm (helm-missing), or a Helm without the verb.
//
// Node runs the whole flow so no .ps1 or .sh file is executed: script execution policies and hosts that gate
// PowerShell script invocations never apply. Network and archive work is delegated to the Windows tools that
// already handle proxies and zips: curl (HTTPS_PROXY), then PowerShell's WebClient as a -Command (system proxy).

import { spawnSync } from 'node:child_process';
import { mkdirSync, readFileSync, renameSync, rmSync, statSync } from 'node:fs';
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
// Windows refuses to delete a file another process holds, such as a scanner or a running build. Every removal here is
// cleanup that a later run repeats, so a refusal is retried briefly, then left on disk; it never ends the run without
// its JSON line.
const remove = (p) => {
  try { rmSync(p, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 }); return true; } catch { return false; }
};
// Git Bash may hand a POSIX-style path (/c/tools) to a native process; normalize it to a Windows path.
const toWin = (p) => p.replace(/^\/([a-zA-Z])(\/|$)/, (_, d) => d.toUpperCase() + ':\\').replace(/\//g, '\\');
const tail = (s, n) => s.replace(/[\r\n]+/g, ' ').trim().slice(-n);
const head = (s, n) => s.replace(/\s+/g, ' ').trim().slice(0, n);

// Semantic-version order over the versions UiPath publishes, such as 26.10.0 and 26.10.0-alpha.26345: the numeric core
// first, then a release above its pre-releases. A version that does not parse is never newer and never outdated.
const parseVersion = (v) => {
  const m = /^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+.*)?$/.exec(String(v).trim());
  return m && { core: [+m[1], +m[2], +m[3]], pre: m[4] ? m[4].split('.') : null };
};
const newer = (a, b) => {
  const x = parseVersion(a);
  const y = parseVersion(b);
  if (!x || !y) return false;
  for (let i = 0; i < 3; i++) if (x.core[i] !== y.core[i]) return x.core[i] > y.core[i];
  if (!x.pre || !y.pre) return !x.pre && Boolean(y.pre);
  for (let i = 0; i < Math.max(x.pre.length, y.pre.length); i++) {
    const p = x.pre[i];
    const q = y.pre[i];
    if (p === undefined || q === undefined) return q === undefined;
    if (p === q) continue;
    const pn = /^\d+$/.test(p);
    const qn = /^\d+$/.test(q);
    if (pn && qn) return +p > +q;
    if (pn !== qn) return qn;
    return p > q;
  }
  return false;
};

// UiPath's pipeline publishes latest.json next to the archive, with the version of the build the archive holds. A
// mirror that serves no such file, or a failed request, yields no version and so no update report. The text is cut to
// its JSON object: the file starts with a byte-order mark. A plain run waits for this read, so each attempt gives up
// early: a server that never answers costs about 15 seconds.
const servedVersion = () => {
  let url;
  try { url = new URL('latest.json', ARCHIVE_URL).href; } catch { return ''; }
  const read = (text) => {
    try {
      const v = JSON.parse(text.slice(text.indexOf('{'), text.lastIndexOf('}') + 1)).version;
      return typeof v === 'string' ? v.trim() : '';
    } catch { return ''; }
  };
  const curl = run('curl', ['-fsSL', '--connect-timeout', '5', '--max-time', '10', url], { timeout: 12000 });
  if (curl.ok && read(curl.out)) return read(curl.out);
  // Behind a system proxy curl fails every time; without this retry an update would never be reported and nothing would say so.
  const ps = powershell(
    `try { ${PS_TLS}$r = [System.Net.WebRequest]::Create(${psq(url)}); $r.Timeout = 8000; $r.ReadWriteTimeout = 8000; ${psProxy('$r')}` +
    '$resp = $r.GetResponse(); $sr = New-Object System.IO.StreamReader($resp.GetResponseStream()); [Console]::Out.Write($sr.ReadToEnd()); $resp.Close() } catch { exit 1 }',
    { timeout: 12000 },
  );
  return ps.ok ? read(ps.out) : '';
};

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
  // The last line that reads as a version: a notice uip prints after Helm's output does not hide it.
  const version = r.out.split(/\r?\n/).map((l) => l.trim()).findLast((l) => /^\d+\.\d+/.test(l)) || '';
  if (r.ok && version) emit({ status: 'ok', source: 'uip', command: UIP_COMMAND, version }, 0);
  // No uip on PATH, a uip without the command, or a Helm that does not know `migrate`: their own error text.
  const detail = head(r.err, 300) || head(r.out, 300) || (r.status == null ? 'no output' : `exit code ${r.status}, no output`);
  uipMessage = `${UIP_COMMAND} version: ${detail}`;
};

if (!process.env.UIPATH_ACTIVITY_MIGRATOR_DIR && !process.env.UIPATH_ACTIVITY_MIGRATOR_URL) fromUip();

// --- Archive fallback: start a build and read its answer -------------------
// .NET's launcher exits with these codes before any tool code runs. FRAMEWORK_MISSING: it found a .NET install without
// the runtime this build needs. HOST_MISSING: it found no .NET install; a broken install exits the same way, so there
// the launcher's text decides, and anything else stays a verify failure that relays the text.
const FRAMEWORK_MISSING = 0x80008096;
const HOST_MISSING = 0x80008083;
// Starts the build at `path`: { version } when it answers, else { code, message } and, for the telemetry crash, the
// `env` assignment it does start with. `name` is how the message calls the build; `redo` ends the verify-failed
// message. Starting the tool is the only check of its .NET runtime. Which runtime a build needs, where the launcher
// looks for it and what a roll-forward setting lets it accept are the launcher's rules; a copy of them here would name
// the wrong runtime for a build that targets another .NET, and refuse a tool that starts.
const verify = (path, name, redo = 'the install may be incomplete: rerun with --force.') => {
  const ver = run(path, ['version'], { timeout: 60000 });
  const version = lastLine(ver.out);
  if (ver.status === FRAMEWORK_MISSING || (ver.status === HOST_MISSING && /You must install \.NET to run this application/i.test(ver.err))) {
    const hostLine = (re) => (re.exec(ver.err) || [])[1]?.trim() || '';
    // The build's runtimeconfig, next to the exe, names the .NET it targets. It only words the fix; unreadable, the
    // launcher's text is relayed instead. The launcher's first missing framework is the base runtime, and its download
    // link installs that one alone, so the fix names the Desktop Runtime, which holds both frameworks the tool loads.
    let major = '';
    try {
      const opts = JSON.parse(readFileSync(path.replace(/\.exe$/i, '.runtimeconfig.json'), 'utf8')).runtimeOptions;
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
    const rootVar = [`DOTNET_ROOT_${arch.toUpperCase()}`, 'DOTNET_ROOT'].find((v) => process.env[v] && isDir(process.env[v]));
    if (rootVar) {
      return { code: 'runtime-missing', message: `${name} needs ${runtimeName}, which is not in ${process.env[rootVar]}, the only place the migrator loads its runtime from while ${rootVar} is set.${others} Unset ${rootVar}, or install the runtime there, and rerun.${reported}` };
    }
    const where = hostLine(/^\.NET location:[ \t]*(\S.*)$/m);
    const place = where && !/^not found$/i.test(where) ? ` in ${where}, where the migrator loads its runtime from.` : ': no .NET install was found on this machine.';
    return { code: 'runtime-missing', message: `${name} needs ${runtimeName}, which is not installed${place}${others} Install ${runtimeName} from ${page} and rerun.${reported}` };
  }
  // The 25.10 builds parse UIPATH_TELEMETRY_DISABLED with bool.Parse and crash at startup on any value but true or
  // false, such as the documented 1. Prove it with a retry under the strict spelling of the user's choice; never unset
  // the variable, which would turn the user's telemetry back on.
  const telemetry = process.env.UIPATH_TELEMETRY_DISABLED;
  if ((!ver.ok || !version) && telemetry !== undefined && !/^\s*(true|false)\s*$/i.test(telemetry)) {
    const strict = /^\s*(0|no|off)\s*$/i.test(telemetry) ? 'false' : 'true';
    const retry = run(path, ['version'], { timeout: 60000, env: { ...process.env, UIPATH_TELEMETRY_DISABLED: strict } });
    if (retry.ok && lastLine(retry.out)) {
      return { code: 'telemetry-flag', env: `UIPATH_TELEMETRY_DISABLED=${strict}`, message: `${name} crashes at startup while UIPATH_TELEMETRY_DISABLED is ${JSON.stringify(telemetry)}: this build accepts only true or false. It starts with UIPATH_TELEMETRY_DISABLED=${strict}, the same choice. Prefix this script and every UiPath.Upgrade.exe command with it; never unset the variable.` };
    }
  }
  // Any other failure: the tool's own stderr names why it could not start. .NET launch errors lead with the cause and
  // end with links, so the start of the text is kept.
  if (!ver.ok || !version) {
    const detail = head(ver.err, 400) || (ver.status == null ? 'no output' : `exit code ${ver.status}, no output`);
    return { code: 'verify-failed', message: `${name} did not print a version (${detail}). When that names a missing runtime or framework, fix it as it says; otherwise ${redo}` };
  }
  return { version };
};
const report = (v) => emit({ status: 'error', code: v.code, ...(v.env && { env: v.env }), message: v.message }, 1);

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
const previous = join(root, 'current.old');
// A run killed between the two renames of a replacement leaves the previous build in current.old: put it back when
// current/ is gone, drop it once current/ holds a build. When putting it back fails it is the only build on disk, so it
// stays for the next run to restore.
if (isDir(previous)) {
  if (!isDir(current)) { try { renameSync(previous, current); } catch { /* kept; the next run tries again */ } }
  if (isDir(current)) remove(previous);
}
if (isFile(join(root, 'UiPath.Upgrade.exe'))) exe = join(root, 'UiPath.Upgrade.exe');
else if (isFile(join(current, 'UiPath.Upgrade.exe'))) exe = join(current, 'UiPath.Upgrade.exe');
if (!source) source = 'cached';

if (!exe && OFFLINE) {
  fail('offline-missing', `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1 and no tool found under ${root}. Place the extracted archive there; see references/acquisition-guide.md § Manual placement.`);
}
// Nothing cached and nobody consented to a download: report, so the caller can ask the user.
if (!exe && !INSTALL) emit({ status: 'missing', dir: root, url: ARCHIVE_URL }, 3);

// --- 3b. Verify the cached tool and decide whether to download -------------
let needDownload = !exe || FORCE;
let isUpdate = false;
let updateAvailable = false;
let version = '';
if (!needDownload) {
  const cached = verify(exe, exe);
  if (cached.code) report(cached);
  version = cached.version;
  // Only the build this script installed, under current/ of the default root, is checked for a newer version. An
  // update installs into current/, which a build placed by hand at the root keeps hiding: checked, it would make every
  // install run download again and change nothing. An override dir is used as is, and offline never asks the server.
  // A newer version is installed only on an install run; a plain run reports it and keeps the tool.
  const installedByScript = source !== 'env' && exe === join(current, 'UiPath.Upgrade.exe');
  if (installedByScript && !OFFLINE && newer(servedVersion(), version)) {
    if (INSTALL) {
      needDownload = true;
      isUpdate = true;
    } else {
      updateAvailable = true;
    }
  }
}

// --- 4. Download, extract, verify and install -------------------------------
if (needDownload) {
  // The build a failed download must leave in place; empty on a first install.
  const installed = exe;
  try { mkdirSync(root, { recursive: true }); } catch { fail('download-failed', `Cannot create ${root}.`); }
  // Must end in .zip: Windows PowerShell 5.1's Expand-Archive rejects any other extension.
  const tmpZip = join(root, 'UiPath.Upgrade.Cli.download.zip');
  remove(tmpZip);

  let downloaded = false;
  const errors = [];
  // A stalled connection (under 1 KB/s for a minute) fails instead of hanging.
  const curl = run('curl', ['-fsSL', '--retry', '3', '--retry-delay', '2', '--connect-timeout', '20', '--speed-limit', '1024', '--speed-time', '60', '-o', tmpZip, ARCHIVE_URL]);
  if (curl.ok && isFile(tmpZip)) {
    downloaded = true;
  } else {
    // curl repeats its error once per retry; the last line is the one that ended it.
    const curlLast = curl.err.trim().split(/\r?\n/).filter(Boolean).pop() || '';
    errors.push(curl.missing ? 'curl: not found' : tail(curlLast, 300) || 'curl failed');
    remove(tmpZip);
    // The catch reports the innermost exception's message, such as a proxy's "(407) Proxy Authentication
    // Required", not PowerShell's error-record formatting.
    const ps = powershell(
      `try { ${PS_TLS}$wc = New-Object System.Net.WebClient; ${psProxy('$wc')}$wc.DownloadFile(${psq(ARCHIVE_URL)}, ${psq(tmpZip)}) ` +
      '} catch { $e = $_.Exception; while ($e.InnerException) { $e = $e.InnerException }; [Console]::Error.Write($e.Message); exit 1 }',
    );
    if (ps.ok && isFile(tmpZip)) downloaded = true;
    else errors.push('PowerShell WebClient: ' + (ps.missing ? 'not found' : tail(ps.err, 300)));
  }
  if (!downloaded) {
    remove(tmpZip);
    fail('download-failed', `Download failed (${errors.join('; ')}). Check proxy settings (HTTPS_PROXY for curl, the system proxy for PowerShell) or place the tool manually; see references/acquisition-guide.md § Manual placement.`);
  }

  const stage = join(root, '.extract-tmp');
  // A staging folder that will not clear would mix an earlier archive's files into the new build: stop, with the zip kept.
  if (!remove(stage)) fail('extract-failed', `Could not clear ${stage}, left by an earlier run. Remove it and rerun, or extract ${tmpZip} manually into ${current}.`);
  mkdirSync(stage, { recursive: true });
  const systemTar = join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'tar.exe');
  const extracted =
    powershell(`Expand-Archive -LiteralPath ${psq(tmpZip)} -DestinationPath ${psq(stage)} -Force`).ok ||
    (isFile(systemTar) && run(systemTar, ['-xf', tmpZip, '-C', stage]).ok) ||
    run('unzip', ['-q', '-o', tmpZip, '-d', stage]).ok;
  if (!extracted) {
    remove(stage);
    fail('extract-failed', `Could not extract ${tmpZip} with Expand-Archive, tar, or unzip. Extract it manually into ${current}.`);
  }
  if (!isFile(join(stage, 'UiPath.Upgrade.exe')) || !isDir(join(stage, 'Extensions'))) {
    remove(stage);
    remove(tmpZip);
    fail('extract-failed', 'Archive layout unexpected: UiPath.Upgrade.exe or Extensions/ missing after extraction.');
  }

  // The new build is started where it was extracted, before it replaces anything. One that does not start never
  // replaces a build that does: the archive URL is unversioned, so the replaced build could not be fetched again. A
  // first install has nothing to protect: its build is put in place either way and reported under its final path.
  const target = join(current, 'UiPath.Upgrade.exe');
  const stagedExe = join(stage, 'UiPath.Upgrade.exe');
  const staged = installed ? verify(stagedExe, 'The downloaded build', 'the download may be incomplete.') : verify(stagedExe, target);
  if (installed && staged.code && !staged.env) {
    remove(stage);
    remove(tmpZip);
    fail(staged.code, `${staged.message} It was not installed: ${installed} is unchanged.`);
  }

  // Swap, then delete: the previous build is removed only once the new one is in place, so a failed replacement
  // leaves the installed build as it was.
  const hadCurrent = isDir(current);
  try {
    if (hadCurrent) renameSync(current, previous);
    renameSync(stage, current);
  } catch (e) {
    remove(stage);
    const refused = e?.code ? ` (${e.code})` : '';
    // Nothing was in current/: the archive is kept, so it can be extracted by hand.
    if (!hadCurrent) fail('extract-failed', `Could not move the extracted build to ${current}${refused}. Extract ${tmpZip} manually into ${current}.`);
    // current/ held a build, which Windows will not let go of while a program runs from it. Put it back if the first
    // rename had moved it; the archive is of no further use.
    let restored = isDir(current);
    if (!restored) { try { renameSync(previous, current); restored = true; } catch { /* the next run puts it back */ } }
    remove(tmpZip);
    const kept = restored ? 'the installed build is unchanged' : `the installed build is in ${previous}, and the next run puts it back`;
    fail('extract-failed', `Could not replace ${current}${refused}: the folder is in use or not writable. Close any UiPath.Upgrade.exe that is still running and rerun; ${kept}.`);
  }
  remove(previous);
  remove(tmpZip);
  // Written by earlier versions of this script; nothing reads it now.
  remove(join(root, '.last-modified'));
  exe = target;
  source = isUpdate ? 'updated' : 'downloaded';
  if (staged.code) report(staged);
  version = staged.version;
}

const result = { status: 'ok', source, command: exe, exe, version };
if (updateAvailable) result.update = true;
emit(result, 0);
