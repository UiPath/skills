#!/usr/bin/env node
// ensure-migrator.mjs — locate, download, and verify the UiPath Activity Migrator (UiPath.Upgrade.exe).
//
// Usage: node ensure-migrator.mjs [--check-only] [--force]
//   --check-only  report what is cached without downloading; exit 3 with status "missing" when nothing is
//   --force       re-download and re-extract even when cached
// Env:   UIPATH_ACTIVITY_MIGRATOR_DIR      install/cache root (default %LOCALAPPDATA%\UiPath\ActivityMigrator)
//        UIPATH_ACTIVITY_MIGRATOR_URL      archive URL (default https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip)
//        UIPATH_ACTIVITY_MIGRATOR_OFFLINE  set to 1 to never touch the network
//        UIPATH_ACTIVITY_MIGRATOR_WINDOW_SECONDS  download budget of one run; what is kept is reported and a rerun resumes (default 480)
//        UIPATH_TELEMETRY_DISABLED         read only: a value other than true/false that crashes the tool is reported
// Output: the last stdout line is one JSON object; see references/acquisition-guide.md § Script output contract.
// Exit:  0 ok, 1 error, 3 missing (check-only). No dependencies. Node 18+.
//
// Node runs the whole flow so no .ps1 or .sh file is executed: script execution policies and hosts that gate
// PowerShell script invocations never apply. Network and archive work is delegated to the Windows tools that
// already handle proxies and zips: curl (HTTPS_PROXY), then PowerShell's WebClient as a -Command (system proxy).
// The archive is a few hundred MB behind a CDN; section 4 fetches it in 16 MiB ranges kept under <root>\.chunks, so
// a stalled request costs 30 s, no byte is fetched twice, and a rerun resumes where the last one stopped.

import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { appendFileSync, closeSync, constants as fsConstants, existsSync, mkdirSync, openSync, readFileSync, readSync, readdirSync, renameSync, rmSync, statSync, writeFileSync, writeSync } from 'node:fs';
import { join } from 'node:path';

const DEFAULT_URL = 'https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip';
const ARCHIVE_URL = process.env.UIPATH_ACTIVITY_MIGRATOR_URL || DEFAULT_URL;
const OFFLINE = process.env.UIPATH_ACTIVITY_MIGRATOR_OFFLINE === '1';
const args = process.argv.slice(2);
const CHECK_ONLY = args.includes('--check-only');
const FORCE = args.includes('--force');
const CHUNK_BYTES = 16 * 1024 * 1024;
// One range request is capped at 30 s: a trickling connection ends, the next request continues from the bytes it
// delivered, and the download deadline is checked at least that often.
const REQUEST_TIME_S = 30;
// Download budget of one run. 8 minutes leaves the request that may run past it, the assembly, the MD5 check, the
// extraction (40 s for the real archive) and the version check inside the 10 minutes SKILL.md Step 0 asks the agent to
// allow; a host with another command budget sets the variable.
const windowSeconds = Number(process.env.UIPATH_ACTIVITY_MIGRATOR_WINDOW_SECONDS);
const WINDOW_MS = (Number.isInteger(windowSeconds) && windowSeconds > 0 ? windowSeconds : 480) * 1000;
// Another run downloading into the same folder is waited for up to a fraction of the budget.
const LOCK_WAIT_MS = Math.min(60 * 1000, WINDOW_MS / 8);
// The three extractors share one budget. It is a hang guard that frees the install lock, not part of the 10-minute
// arithmetic above, which counts the 40 s a real extraction takes.
const EXTRACT_MS = 5 * 60 * 1000;
// libuv's UV_FS_O_EXLOCK: on Windows the file is opened with share mode 0, so no other process can open, read or delete
// it while the handle is held. Node does not export the constant on Windows; the value is fixed in libuv's uv/win.h.
const UV_FS_O_EXLOCK = 0x10000000;
const MANUAL = 'Check proxy settings (HTTPS_PROXY for curl, the system proxy for PowerShell) or place the tool manually; see references/acquisition-guide.md § Manual placement.';

// Set while this run owns the install lock (section 4), so an error exit from anywhere inside releases it.
let beforeExit = () => {};
const emit = (obj, code) => {
  beforeExit();
  process.stdout.write(JSON.stringify(obj) + '\n');
  process.exit(code);
};
const fail = (code, message, extra = {}) => emit({ status: 'error', code, message, ...extra }, 1);
const sleepMs = (ms) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);

const run = (cmd, argv, opts = {}) => {
  const r = spawnSync(cmd, argv, { encoding: 'utf8', windowsHide: true, maxBuffer: 16 * 1024 * 1024, ...opts });
  return { ok: !r.error && r.status === 0, status: r.status, missing: r.error?.code === 'ENOENT', timedOut: r.error?.code === 'ETIMEDOUT', out: r.stdout || '', err: (r.stderr || '') + (r.error ? String(r.error.message) : '') };
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
const fileSize = (p) => { try { return statSync(p).size; } catch { return -1; } };
// Git Bash may hand a POSIX-style path (/c/tools) to a native process; normalize it to a Windows path.
const toWin = (p) => p.replace(/^\/([a-zA-Z])(\/|$)/, (_, d) => d.toUpperCase() + ':\\').replace(/\//g, '\\');
// Headers of the last response in a curl -I/-D dump (redirects leave several blocks), keys lower-cased.
const parseHeaders = (text) => {
  let h = {};
  for (const line of text.split(/\r?\n/)) {
    if (/^HTTP\//i.test(line)) { h = {}; continue; }
    const m = /^([^:]+):\s*(.*)$/.exec(line);
    if (m) h[m[1].trim().toLowerCase()] = m[2].trim();
  }
  return h;
};
const tail = (s, n) => s.replace(/[\r\n]+/g, ' ').trim().slice(-n);
const head = (s, n) => s.replace(/\s+/g, ' ').trim().slice(0, n);
const lastLine = (s) => s.split(/\r?\n/).map((l) => l.trim()).findLast(Boolean) || '';
const mb = (n) => (n / (1024 * 1024)).toFixed(0);
const md5Base64 = (p) => {
  const hash = createHash('md5');
  const fd = openSync(p, 'r');
  try {
    const buf = Buffer.alloc(8 * 1024 * 1024);
    let n;
    while ((n = readSync(fd, buf, 0, buf.length, null)) > 0) hash.update(buf.subarray(0, n));
  } finally {
    closeSync(fd);
  }
  return hash.digest('base64');
};
const tryRemove = (p) => { try { rmSync(p, { recursive: true, force: true }); } catch { /* another process holds it; it is not needed */ } };
// A file still open in a downloader or extractor that outlived its run (the host killed node, the child went on) cannot
// be deleted (EBUSY/EPERM). That child ends on its own, so this is the busy case: holder: true routes the agent to a rerun.
const removeOrFail = (p) => {
  try { rmSync(p, { recursive: true, force: true }); } catch (e) {
    fail('download-failed', `Cannot remove ${p} (${e.code || e.message}): a process from an earlier run of this script is still holding it and ends on its own. Rerun in a minute.`, { holder: true });
  }
};
// Windows refuses to rename a file another process has open; an on-access scanner holds a just-written one briefly.
const renameOrError = (from, to) => {
  for (let t = 0; ; t++) {
    try { renameSync(from, to); return ''; } catch (e) {
      if (t >= 5) return `cannot rename ${from} (${e.code || e.message}): another process is holding it`;
      sleepMs(200);
    }
  }
};

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
if (FORCE && OFFLINE) fail('offline-missing', 'UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1 forbids the download that --force asks for. Drop one of the two and rerun.');
if (!exe && OFFLINE) {
  fail('offline-missing', `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1 and no tool found under ${root}. Place the extracted archive there; see references/acquisition-guide.md § Manual placement.`);
}

// --- 3. Probe the archive and decide whether to download ------------------
// One HEAD is both the update check (Last-Modified) and the download plan (Content-Length, Accept-Ranges, ETag,
// Content-MD5); references/acquisition-guide.md § Download has the stages. Behind a system proxy curl's HEAD fails every
// time; without the PowerShell retry the cache would never update. `via` names the tool that reached the server: only
// curl performs the chunked download, and a curl whose HEAD failed where PowerShell's succeeded is not tried again.
const probeArchive = () => {
  const curlHead = run('curl', ['-sSIL', '--max-time', '20', ARCHIVE_URL], { timeout: 30000 });
  if (curlHead.ok) {
    const h = parseHeaders(curlHead.out);
    return { lastModified: h['last-modified'] || '', length: Number(h['content-length']) || 0, ranges: /bytes/i.test(h['accept-ranges'] || ''), etag: h['etag'] || '', md5: h['content-md5'] || '', via: 'curl' };
  }
  const psHead = powershell(
    `try { ${PS_TLS}$r = [System.Net.WebRequest]::Create(${psq(ARCHIVE_URL)}); $r.Method = 'HEAD'; $r.Timeout = 20000; ${psProxy('$r')}` +
    "$resp = $r.GetResponse(); $h = $resp.Headers; [Console]::Out.Write((@{ lm = [string]$h['Last-Modified']; len = [string]$h['Content-Length']; ar = [string]$h['Accept-Ranges']; etag = [string]$h['ETag']; md5 = [string]$h['Content-MD5'] } | ConvertTo-Json -Compress)); $resp.Close() } catch { exit 1 }",
    { timeout: 40000 },
  );
  if (psHead.ok) {
    try {
      const j = JSON.parse(psHead.out.trim());
      return { lastModified: (j.lm || '').trim(), length: Number(j.len) || 0, ranges: /bytes/i.test(j.ar || ''), etag: (j.etag || '').trim(), md5: (j.md5 || '').trim(), via: 'powershell' };
    } catch { /* fall through */ }
  }
  return { lastModified: '', length: 0, ranges: false, etag: '', md5: '', via: '' };
};
const readStamp = () => (existsSync(stamp) ? readFileSync(stamp, 'utf8').replace(/^\uFEFF/, '').replace(/[\r\n]/g, '').trim() : '');

let probe = null;
let needDownload = false;
let isUpdate = false;
if (!exe || FORCE) {
  needDownload = true;
} else if (source !== 'env' && !OFFLINE && !CHECK_ONLY) {
  probe = probeArchive();
  const remoteLm = probe.lastModified;
  // A stamp written by hand may carry a UTF-8 BOM; readStamp strips it or every run looks like an update.
  const localLm = readStamp();
  if (remoteLm && localLm && remoteLm !== localLm) {
    needDownload = true;
    isUpdate = true;
  }
  if (remoteLm && !localLm) writeFileSync(stamp, remoteLm, 'ascii');
}

// --- 4. Download and extract ----------------------------------------------
// One run at a time per install root (guide § Download): <root>\.lock is held as an exclusive handle (UV_FS_O_EXLOCK),
// released by the OS the moment the holder ends, however it ends, so there is no pid to probe and no stale clock.
// <root>\.lock.pid names the holder for the busy message only. A second run waits a while, since an agent's impatient
// second call usually lands while the first extracts, and reports the holder otherwise.
const lockFile = join(root, '.lock');
const pidFile = join(root, '.lock.pid');
let lockFd = -1;
const openExclusive = () => openSync(lockFile, fsConstants.O_RDWR | fsConstants.O_CREAT | UV_FS_O_EXLOCK);
const releaseLock = () => {
  if (lockFd < 0) return;
  tryRemove(pidFile); // while the handle is still ours: a waiter that takes over next writes its own
  try { closeSync(lockFd); } catch { /* already closed */ }
  lockFd = -1;
  tryRemove(lockFile); // a waiter that already took the handle keeps the file; its EBUSY is ignored
};
// Returns { held: true } once the lock is ours, else { held: false, holder } for a live holder (its pid, or true while
// .lock.pid is not readable) or { held: false, error } when the file cannot be created or the lock cannot be exclusive.
const takeLock = () => {
  const waitUntil = Date.now() + LOCK_WAIT_MS;
  for (;;) {
    try {
      lockFd = openExclusive();
      break;
    } catch (e) {
      if (e.code !== 'EBUSY') return { held: false, error: `Cannot create ${lockFile} (${e.code || e.message}).` };
      if (Date.now() > waitUntil) {
        let holder = true;
        try { const pid = Number(readFileSync(pidFile, 'utf8').trim()); if (Number.isInteger(pid) && pid > 0) holder = pid; } catch { /* not written yet */ }
        return { held: false, holder };
      }
      sleepMs(500);
    }
  }
  // The flag is outside Node's documented surface on Windows: prove it is honoured, or the lock is no lock at all.
  let secondHandle = false;
  try { closeSync(openExclusive()); secondHandle = true; } catch { /* EBUSY: exclusive, as required */ }
  if (secondHandle) {
    closeSync(lockFd);
    lockFd = -1;
    return { held: false, error: `Cannot take an exclusive lock on ${lockFile} with this Node build (${process.version}): a second handle was granted. The script refuses to download unprotected; report this.` };
  }
  try { writeFileSync(pidFile, String(process.pid), 'ascii'); } catch { /* informational only */ }
  return { held: true };
};

// Chunked download, guide § Download step 2: sequential 16 MiB ranges into <root>\.chunks, each request capped at
// REQUEST_TIME_S with its bytes kept in part-NNN.bin.tmp so the next request, or a rerun, continues from that offset;
// .etag ties the parts to one archive, .bust remembers the switch from the plain URL to one query string per request
// after a request ran out of time. Returns { ok } | { ok: false, rangesIgnored } | { ok: false, error, retry, progress,
// completedBytes, totalBytes }, retry meaning a rerun is worth it.
const chunkUrl = (i, bust) => (!bust || ARCHIVE_URL.includes('?') ? ARCHIVE_URL : `${ARCHIVE_URL}?r=${i}-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`);
const downloadChunked = (p, chunksDir, tmpZip, deadline) => {
  const total = p.length;
  const count = Math.ceil(total / CHUNK_BYTES);
  const marker = `${p.etag || p.lastModified || 'unknown'}:${total}`;
  const stampFile = join(chunksDir, '.etag');
  const bustFile = join(chunksDir, '.bust');
  const partName = (i) => `part-${String(i).padStart(3, '0')}.bin`;
  const partPath = (i) => join(chunksDir, partName(i));
  const partial = (i) => partPath(i) + '.tmp';
  const expected = (i) => Math.min(CHUNK_BYTES, total - i * CHUNK_BYTES);
  const complete = (i) => fileSize(partPath(i)) === expected(i);
  const kept = () => { let b = 0; for (let i = 0; i < count; i++) b += complete(i) ? expected(i) : Math.max(0, fileSize(partial(i))); return b; };
  const done = () => { let n = 0; for (let i = 0; i < count; i++) if (complete(i)) n++; return n; };
  const stop = (error, retry) => {
    const bytes = kept();
    if (bytes === 0) tryRemove(chunksDir);
    return { ok: false, error, retry, completedBytes: bytes, totalBytes: total, progress: `${done()} of ${count} chunks (${mb(bytes)} of ${mb(total)} MB) are kept under ${chunksDir}` };
  };
  try { mkdirSync(chunksDir, { recursive: true }); } catch (e) { return stop(`cannot create ${chunksDir} (${e.code || e.message})`, false); }
  // Parts of another archive and attempt files of earlier runs are dropped file by file; one a stale curl still holds
  // stays and is ignored.
  const sameArchive = isFile(stampFile) && readFileSync(stampFile, 'utf8').trim() === marker;
  for (const f of readdirSync(chunksDir)) if (!sameArchive || /^part-\d{3}\.bin\.\d+-\d+\.tmp(\.headers)?$/.test(f)) tryRemove(join(chunksDir, f));
  if (!sameArchive) writeFileSync(stampFile, marker, 'ascii');
  const startBytes = kept();
  let bust = isFile(bustFile);
  let lastError = '';
  let idle = 0;
  let attempt = 0;
  for (let i = 0; i < count; i++) {
    while (!complete(i)) {
      const have = Math.max(0, fileSize(partial(i)));
      if (have >= expected(i)) {
        const err = renameOrError(partial(i), partPath(i));
        if (err) return stop(err, true);
        break;
      }
      if (Date.now() > deadline) {
        // A full budget that moved less than a third of what is left would need more than the three reruns SKILL.md
        // allows: not worth them.
        const bytes = kept();
        const hopeless = (bytes - startBytes) * 3 < total - bytes;
        return stop(`no complete download within ${WINDOW_MS / 1000} seconds (${lastError || 'transfer too slow'})${hopeless ? '; at this pace it would need more than three more runs' : ''}`, !hopeless);
      }
      const from = i * CHUNK_BYTES + have;
      const to = i * CHUNK_BYTES + expected(i) - 1;
      const file = `${partPath(i)}.${process.pid}-${++attempt}.tmp`;
      const hdr = file + '.headers';
      // --max-filesize stops a server that ignores the range from sending the whole archive into one attempt.
      const r = run('curl', ['-fsSL', '--connect-timeout', '20', '--max-time', String(REQUEST_TIME_S), '--speed-limit', '1024', '--speed-time', '20', '--max-filesize', String(to - from + 1), '-r', `${from}-${to}`, '-D', hdr, '-o', file, '-w', '%{http_code}', chunkUrl(i, bust)], { timeout: (REQUEST_TIME_S + 15) * 1000 });
      const code = (r.out || '').trim().slice(-3);
      const h = isFile(hdr) ? parseHeaders(readFileSync(hdr, 'utf8')) : {};
      tryRemove(hdr);
      if (code === '200') { tryRemove(file); return { ok: false, rangesIgnored: true }; }
      if (p.etag && h.etag && h.etag !== p.etag) {
        tryRemove(file);
        tryRemove(chunksDir);
        return stop('the archive changed on the server during the download; the parts were discarded', true);
      }
      // A 206 must start where it was asked to; a proxy that answers another offset would corrupt the part.
      const range = /^bytes\s+(\d+)-/i.exec(h['content-range'] || '');
      const misplaced = code === '206' && range && Number(range[1]) !== from;
      // A 206 that ended early (time cap, dropped connection) still delivered a valid prefix of the range: keep it.
      const got = code === '206' && !misplaced ? Math.min(Math.max(0, fileSize(file)), to - from + 1) : 0;
      if (got > 0) {
        try { appendFileSync(partial(i), readFileSync(file).subarray(0, got)); } catch (e) {
          tryRemove(file);
          return stop(`cannot write ${partial(i)} (${e.code || e.message})`, kept() > 0);
        }
      }
      tryRemove(file);
      // curl exit 28: the request ran out of time (--max-time or --speed-limit) before its range was complete.
      if (!bust && r.status === 28 && got < to - from + 1) {
        bust = true;
        try { writeFileSync(bustFile, '', 'ascii'); } catch { /* a rerun then pays one more stall */ }
      }
      if (misplaced) lastError = `the server answered the request for offset ${from} with bytes from offset ${range[1]}`;
      else if (!r.ok) lastError = tail(r.err.trim().split(/\r?\n/).filter(Boolean).pop() || `HTTP ${code || 'error'}`, 200);
      idle = got > 0 ? 0 : idle + 1;
      if (idle >= 3) return stop(lastError || 'three requests in a row delivered nothing', kept() > 0);
    }
  }

  rmSync(tmpZip, { force: true });
  try {
    const fd = openSync(tmpZip, 'w');
    try {
      // Each part is dropped once appended, so the archive never needs twice its size on disk.
      for (let i = 0; i < count; i++) { writeSync(fd, readFileSync(partPath(i))); tryRemove(partPath(i)); }
    } finally { closeSync(fd); }
  } catch (e) {
    return stop(`cannot assemble ${tmpZip} (${e.code || e.message})`, true);
  }
  const size = fileSize(tmpZip);
  const bad = size !== total ? `the assembled archive is ${size} bytes, the server announced ${total}` : p.md5 && md5Base64(tmpZip) !== p.md5 ? "the assembled archive failed the server's Content-MD5 check" : '';
  tryRemove(chunksDir);
  if (bad) {
    rmSync(tmpZip, { force: true });
    return stop(`${bad}; the download starts over on the next run`, true);
  }
  return { ok: true };
};

if (needDownload) {
  try { mkdirSync(root, { recursive: true }); } catch { fail('download-failed', `Cannot create ${root}.`); }
  // Must end in .zip: Windows PowerShell 5.1's Expand-Archive rejects any other extension.
  const tmpZip = join(root, 'UiPath.Upgrade.Cli.download.zip');
  const headers = join(root, '.headers.tmp');
  const chunksDir = join(root, '.chunks');
  // One deadline for the whole download stage, the wait for the lock included: every downloader ends at it.
  const deadline = Date.now() + WINDOW_MS;
  const lock = takeLock();
  if (!lock.held) {
    if (lock.error) fail('download-failed', lock.error);
    const who = typeof lock.holder === 'number' ? ` (process ${lock.holder})` : '';
    fail('download-failed', `Another run of this script${who} is downloading into ${root}. Rerun when it has finished; a minute is usually enough.`, { holder: lock.holder });
  }
  beforeExit = releaseLock;

  let newLm = '';
  let downloaded = false;
  let installedByOther = false;
  const errors = [];
  // Another run may have done the work since section 2 looked: a first install put the exe in place, an update rewrote
  // the stamp. --force always downloads, and an update whose stamp still differs from the server's was not done by it.
  if (!FORCE && isFile(join(current, 'UiPath.Upgrade.exe')) && (!isUpdate || readStamp() === probe.lastModified)) {
    downloaded = true;
    installedByOther = true;
    exe = join(current, 'UiPath.Upgrade.exe');
    source = 'cached';
  } else {
    removeOrFail(tmpZip);
    removeOrFail(headers);
    if (FORCE) tryRemove(chunksDir);
    if (!probe) probe = probeArchive();
  }
  if (!downloaded && probe.ranges && probe.length > 0 && probe.via === 'curl') {
    const r = downloadChunked(probe, chunksDir, tmpZip, deadline);
    if (r.ok) {
      downloaded = true;
      newLm = probe.lastModified;
    } else if (r.rangesIgnored) {
      // The server answered a range request with the whole archive (a proxy that drops Range): one stream below.
      tryRemove(chunksDir);
    } else {
      const detail = `Download failed (curl, chunked: ${r.error}).`;
      const keptText = r.completedBytes > 0 ? ` ${r.progress}` : '';
      if (r.retry) fail('download-failed', `${detail}${keptText ? `${keptText}; rerun this script to resume from them.` : ' Rerun this script.'}`, { completedBytes: r.completedBytes, totalBytes: r.totalBytes });
      fail('download-failed', `${detail}${keptText ? `${keptText}.` : ''} ${MANUAL}`);
    }
  }
  if (!downloaded) {
    // No range support, a curl that cannot reach the server, or a server that answers ranges with the whole archive:
    // one curl stream (HTTPS_PROXY; a stall below 1 KB/s for a minute fails instead of hanging), then PowerShell's
    // WebClient (system proxy and the signed-in user's credentials; no stall detection of its own).
    const left = () => Math.max(30 * 1000, deadline - Date.now());
    if (probe.via === 'powershell') {
      errors.push("curl: not tried, its HEAD request failed where PowerShell's succeeded");
    } else {
      const budget = left();
      const curl = run('curl', ['-fsSL', '--retry', '3', '--retry-delay', '2', '--connect-timeout', '20', '--max-time', String(Math.ceil(budget / 1000)), '--speed-limit', '1024', '--speed-time', '60', '-D', headers, '-o', tmpZip, ARCHIVE_URL], { timeout: budget + 5000 });
      if (curl.ok && isFile(tmpZip)) {
        downloaded = true;
        newLm = existsSync(headers) ? parseHeaders(readFileSync(headers, 'utf8'))['last-modified'] || '' : '';
      } else {
        // curl repeats its error once per retry; the last line is the one that ended it.
        const curlLast = curl.err.trim().split(/\r?\n/).filter(Boolean).pop() || '';
        errors.push(curl.missing ? 'curl: not found' : curl.timedOut ? `curl: no complete download within ${Math.round(budget / 1000)} seconds` : tail(curlLast, 300) || 'curl failed');
        tryRemove(tmpZip);
      }
    }
    if (!downloaded) {
      const budget = left();
      // The catch reports the innermost exception's message, such as a proxy's "(407) Proxy Authentication
      // Required", not PowerShell's error-record formatting.
      const ps = powershell(
        `try { ${PS_TLS}$wc = New-Object System.Net.WebClient; ${psProxy('$wc')}` +
        `$wc.DownloadFile(${psq(ARCHIVE_URL)}, ${psq(tmpZip)}); $lm = $wc.ResponseHeaders['Last-Modified']; if ($lm) { [Console]::Out.Write(([string]$lm).Trim()) } ` +
        '} catch { $e = $_.Exception; while ($e.InnerException) { $e = $e.InnerException }; [Console]::Error.Write($e.Message); exit 1 }',
        { timeout: budget },
      );
      if (ps.ok && isFile(tmpZip)) {
        downloaded = true;
        newLm = ps.out.trim();
      } else {
        errors.push('PowerShell WebClient: ' + (ps.missing ? 'not found' : ps.timedOut ? `no complete download within ${Math.round(budget / 1000)} seconds` : tail(ps.err, 300)));
      }
    }
  }
  tryRemove(headers);
  if (!downloaded) {
    tryRemove(tmpZip);
    fail('download-failed', `Download failed (${errors.join('; ')}). ${MANUAL}`);
  }

  if (!installedByOther) {
    const stage = join(root, '.extract-tmp');
    tryRemove(stage);
    try { mkdirSync(stage, { recursive: true }); } catch (e) { fail('extract-failed', `Cannot create ${stage} (${e.code || e.message}). Extract ${tmpZip} manually into ${current}.`); }
    const extractUntil = Date.now() + EXTRACT_MS;
    const extractLeft = () => Math.max(1000, extractUntil - Date.now());
    const systemTar = join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'tar.exe');
    const extracted =
      powershell(`Expand-Archive -LiteralPath ${psq(tmpZip)} -DestinationPath ${psq(stage)} -Force`, { timeout: extractLeft() }).ok ||
      (isFile(systemTar) && run(systemTar, ['-xf', tmpZip, '-C', stage], { timeout: extractLeft() }).ok) ||
      run('unzip', ['-q', '-o', tmpZip, '-d', stage], { timeout: extractLeft() }).ok;
    if (!extracted) {
      tryRemove(stage);
      fail('extract-failed', `Could not extract ${tmpZip} with Expand-Archive, tar, or unzip. Extract it manually into ${current}.`);
    }
    if (!isFile(join(stage, 'UiPath.Upgrade.exe')) || !isDir(join(stage, 'Extensions'))) {
      tryRemove(stage);
      fail('extract-failed', 'Archive layout unexpected: UiPath.Upgrade.exe or Extensions/ missing after extraction.');
    }
    try {
      rmSync(current, { recursive: true, force: true });
      renameSync(stage, current);
    } catch {
      fail('extract-failed', `Could not replace ${current}.`);
    }
    tryRemove(tmpZip);
    if (newLm) writeFileSync(stamp, newLm, 'ascii');
    exe = join(current, 'UiPath.Upgrade.exe');
    source = isUpdate ? 'updated' : 'downloaded';
  }
  // current\ is in place: the runs waiting on the lock can use it while this one checks the runtime and the version.
  releaseLock();
  beforeExit = () => {};
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

emit({ status: 'ok', exe, version, source, runtime }, 0);
