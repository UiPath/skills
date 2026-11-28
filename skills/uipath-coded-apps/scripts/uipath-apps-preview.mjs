#!/usr/bin/env node
// uipath-apps-preview.mjs — ask the UiPath Apps extension (VS Code or Studio Desktop) to open the preview of a coded
// web app or dashboard.
//
// Usage:  node uipath-apps-preview.mjs [<app folder>]
//         The folder that holds the app's package.json (<project>/source in a solution); default the current folder.
// Output: one line, exit 0 — OPENING | SHOWN | REFUSED <reason> | NOT_AVAILABLE. Exit 2 on bad usage.
// No dependencies. Node 18+.
//
// Each editor window running UiPath Apps writes ~/.uipath/ide/appshift-<pid>-<id>.lock with its socket, token and
// workspace folders; a window that takes this request lists "preview" in its "requests". The windows whose folders hold
// the app are asked in turn, deepest folder first, then newest lockfile; the next is asked only when the connection
// never opened or the window answered no_app. Everything that is not a verdict — no window, no match, no reply in
// time, the {} an older window answers — is NOT_AVAILABLE, and the caller falls back to running the dev server itself.

import { randomUUID } from 'node:crypto';
import { lstatSync, readdirSync, readFileSync, realpathSync } from 'node:fs';
import { createConnection } from 'node:net';
import { homedir } from 'node:os';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const MAX_LOCKFILE_BYTES = 64 * 1024;
const MAX_REPLY_BYTES = 64 * 1024;
// A window replies as soon as its extension host runs the handler, so this passes only when that host is blocked.
const TIMEOUT_MS = 10_000;
const LOCKFILE = /^appshift-.*\.lock$/;
const TOKEN = /^[0-9a-f]{64}$/;
// A reason is printed on the verdict line, so only a plain word gets through.
const REASON = /^[a-z][a-z0-9_]{0,31}$/;

export const lockDir = () => join(homedir(), '.uipath', 'ide');

// ESRCH: no such process, so the lockfile is stale. EPERM: the process exists but cannot be signalled from here;
// keep it, and let the connect decide.
const alive = (pid) => {
  try {
    process.kill(pid, 0);
    return true;
  } catch (err) {
    return err?.code === 'EPERM';
  }
};

const isPreviewWindow = (lock) =>
  lock?.v === 2 &&
  Number.isInteger(lock.pid) &&
  lock.pid > 0 &&
  typeof lock.socket === 'string' &&
  /^uipath-agent-hook-/.test(lock.socket.split(/[\\/]/).pop()) &&
  typeof lock.token === 'string' &&
  TOKEN.test(lock.token) &&
  Array.isArray(lock.workspaceFolders) &&
  lock.workspaceFolders.every((f) => typeof f === 'string') &&
  Array.isArray(lock.requests) &&
  lock.requests.includes('preview');

/** The live windows that take the preview request, from the lockfiles in `dir`. */
export function discoverWindows(dir = lockDir()) {
  let names;
  try {
    names = readdirSync(dir);
  } catch {
    return [];
  }
  const windows = [];
  for (const name of names) {
    if (!LOCKFILE.test(name)) continue;
    try {
      const file = join(dir, name);
      const stat = lstatSync(file);
      if (!stat.isFile() || stat.size > MAX_LOCKFILE_BYTES) continue;
      const lock = JSON.parse(readFileSync(file, 'utf8'));
      if (!isPreviewWindow(lock) || !alive(lock.pid)) continue;
      windows.push({ socket: lock.socket, token: lock.token, folders: lock.workspaceFolders, mtimeMs: stat.mtimeMs });
    } catch {
      // Unreadable, or not JSON: not a window.
    }
  }
  return windows;
}

const real = (p) => {
  try {
    return realpathSync.native(p);
  } catch {
    return resolve(p);
  }
};
// Windows paths ignore case. macOS volumes usually do too, but realpath.native returns the case on disk there, so an
// exact compare is right on both kinds of volume.
const key = (p) => (process.platform === 'win32' ? p.toLowerCase() : p);
const holds = (dir, path) => {
  const d = key(dir);
  const p = key(path);
  return p === d || p.startsWith(d.endsWith(sep) ? d : d + sep);
};

/**
 * The windows to ask for `appDir`, in order: deepest folder that holds the app first, then newest lockfile. Each
 * carries the app path to send it: the window's folder as its lockfile writes it, plus the path from there, so the
 * window's own path comparisons match.
 */
export function matchWindow(windows, appDir) {
  const app = real(appDir);
  const matches = [];
  for (const window of windows) {
    let best;
    for (const folder of window.folders) {
      if (!isAbsolute(folder)) continue;
      const root = real(folder);
      if (!holds(root, app) || (best && root.length <= best.depth)) continue;
      const rest = relative(root, app);
      best = { depth: root.length, path: rest ? join(folder, rest) : folder };
    }
    if (best) matches.push({ window, ...best });
  }
  return matches
    .sort((a, b) => b.depth - a.depth || b.window.mtimeMs - a.window.mtimeMs)
    .map(({ window, path }) => ({ socket: window.socket, token: window.token, app: path }));
}

/**
 * Send the request. Resolves to `{ opened, reply }`: `opened` is false when the connection never opened, so nothing
 * was sent; `reply` is the reply line, or undefined on an error or no reply within `timeoutMs`.
 */
export function requestPreview(target, { timeoutMs = TIMEOUT_MS } = {}) {
  const request = {
    v: 2,
    agent: 'uipath-coded-apps',
    sessionId: randomUUID(),
    pid: process.pid,
    event: 'preview',
    app: target.app,
    token: target.token,
  };
  return new Promise((done) => {
    const chunks = [];
    let size = 0;
    let opened = false;
    const socket = createConnection(target.socket);
    const finish = (reply) => {
      clearTimeout(timer);
      socket.destroy();
      done({ opened, reply });
    };
    const timer = setTimeout(() => finish(undefined), timeoutMs);
    socket.on('connect', () => {
      opened = true;
      socket.write(`${JSON.stringify(request)}\n`);
    });
    socket.on('error', () => finish(undefined));
    socket.on('end', () => finish(Buffer.concat(chunks).toString('utf8')));
    socket.on('data', (chunk) => {
      chunks.push(chunk);
      size += chunk.length;
      const text = Buffer.concat(chunks).toString('utf8');
      if (text.includes('\n')) finish(text.slice(0, text.indexOf('\n')));
      else if (size > MAX_REPLY_BYTES) finish(undefined);
    });
  });
}

/** The line to print for a reply. */
export function verdict(line) {
  let reply;
  try {
    reply = JSON.parse(line);
  } catch {
    return 'NOT_AVAILABLE';
  }
  if (reply?.ok === true && reply.status === 'opening') return 'OPENING';
  if (reply?.ok === true && reply.status === 'shown') return 'SHOWN';
  if (reply?.ok === false && typeof reply.reason === 'string' && REASON.test(reply.reason)) return `REFUSED ${reply.reason}`;
  return 'NOT_AVAILABLE';
}

/**
 * Ask the matching windows in turn. Only a window that never got the request, or that answered no_app, passes it to
 * the next: any other answer, or silence after the request went out, may mean a preview is opening there.
 */
export async function preview(appDir, { dir = lockDir(), timeoutMs } = {}) {
  let result = 'NOT_AVAILABLE';
  for (const target of matchWindow(discoverWindows(dir), appDir)) {
    const { opened, reply } = await requestPreview(target, { timeoutMs }).catch(() => ({ opened: false }));
    if (!opened) continue;
    result = verdict(reply);
    if (result !== 'REFUSED no_app') return result;
  }
  return result;
}

const entry = (() => {
  try {
    return pathToFileURL(realpathSync(process.argv[1])).href;
  } catch {
    return '';
  }
})();
if (import.meta.url === entry) {
  const args = process.argv.slice(2);
  if (args.length > 1 || args[0]?.startsWith('-')) {
    process.stderr.write('usage: node uipath-apps-preview.mjs [<app folder>]\n');
    process.exit(2);
  }
  process.stdout.write(`${await preview(resolve(args[0] ?? '.'))}\n`);
}
