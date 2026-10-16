#!/usr/bin/env node
/**
 * Flow diff hook — reports a coding agent's writes to Maestro files (`.flow`, `.bpmn`, `.case`)
 * to the UiPath VS Code extension, so its canvas can show one before/after review per turn.
 * Each window's lockfile narrows the file types to the ones it reviews.
 *
 * Claude Code events → protocol v2 messages:
 *   - PostToolUse Write/Edit/MultiEdit → `write` {file, hashes}: the content the tool wrote,
 *     hashed, is the attestation. The extension credits the agent only with matching content.
 *   - PostToolUse or PostToolUseFailure Bash running `uip maestro …` (or naming a reviewed file
 *     type) → `write` for every reviewed file in a window's workspace modified since the session's checkpoint
 *     (set at the prompt and after each such command).
 *   - PermissionRequest → remembers the windows a proposed edit concerns, so a rejected edit
 *     still ends the turn there.
 *   - Stop/StopFailure, or the next UserPromptSubmit after a turn that never stopped →
 *     re-attests every file the turn reported, then `turn.end`.
 *
 * Contract — never gets in the agent's way:
 *   - Report-only: prints nothing, returns no decision, always exits 0.
 *   - Off when UIPATH_FLOW_DIFF_DISABLED is 1/true or ~/.uipath/ide does not exist.
 *   - Cheap for other work: a Bash command is ignored before any file access unless it
 *     mentions `uip maestro` or a reviewed file type.
 *   - Only talks to an extension found through a user-private lockfile (`~/.uipath/ide/*.lock`,
 *     or the one named by UIPATH_FLOW_HOOK_LOCK), over a socket owned by this user.
 */

import crypto from 'node:crypto';
import fs from 'node:fs';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const AGENT = 'claude';
const PROTOCOL_VERSION = 2;
const REQUEST_TIMEOUT_MS = 2_000;
const STDIN_TIMEOUT_MS = 2_000;
const MAX_FILE_BYTES = 10 * 1024 * 1024;
const SESSION_MAX_AGE_MS = 24 * 60 * 60 * 1000;
const MAX_SCAN_DEPTH = 8;
const MAX_SCAN_ENTRIES = 20_000;
/** File types worth reporting at all; each window's lockfile narrows this to the ones it reviews. */
const REVIEWABLE_EXTENSIONS = ['.flow', '.bpmn', '.case'];
const RELEVANT_COMMAND = /\buip\b.*\bmaestro\b|\.(?:flow|bpmn|case)\b/s;
const LOCK_DIR = path.join(os.homedir(), '.uipath', 'ide');
const SESSION_DIR = path.join(LOCK_DIR, 'sessions');
const CHECKPOINT = 'since';
/** `w-` a reported write, `p-` a pending proposal; then short hashes of the lockfile and the file. */
const ENTRY = /^[pw]-[0-9a-f]{16}-[0-9a-f]{16}$/;
const TOKEN = /^[0-9a-f]{64}$/;
const UNIX_SOCKET = /^uipath-flow-hook-[0-9a-f]{16}\.sock$/;
const WINDOWS_PIPE = /^\\\\\.\\pipe\\uipath-flow-hook-[0-9a-f]{16}$/;
const EXTENSION = /^\.[a-z0-9]{1,16}$/;

// ── Payload → report ─────────────────────────────────────────────────────────

export function isRelevantCommand(command) {
  return typeof command === 'string' && RELEVANT_COMMAND.test(command);
}

/** Applies one string replacement the way Edit does; undefined when it would not apply cleanly. */
function applyEdit(content, oldString, newString, replaceAll) {
  if (typeof oldString !== 'string' || typeof newString !== 'string' || oldString === '' || !content.includes(oldString)) {
    return undefined;
  }
  if (replaceAll) {
    return content.split(oldString).join(newString);
  }
  const index = content.indexOf(oldString);
  return content.slice(0, index) + newString + content.slice(index + oldString.length);
}

/**
 * Post-edit content rebuilt from an Edit/MultiEdit PostToolUse payload: the file before the edit
 * (`tool_response.originalFile`) with the edit applied. Undefined when the payload lacks it.
 */
export function editedContent(payload) {
  const response = payload?.tool_response;
  let content = response?.originalFile;
  if (typeof content !== 'string') {
    return undefined;
  }
  const edits =
    payload.tool_name === 'MultiEdit'
      ? payload.tool_input?.edits
      : [{ old_string: response.oldString, new_string: response.newString, replace_all: response.replaceAll }];
  if (!Array.isArray(edits) || edits.length === 0) {
    return undefined;
  }
  for (const edit of edits) {
    content = applyEdit(content, edit?.old_string, edit?.new_string, edit?.replace_all === true);
    if (content === undefined) {
      return undefined;
    }
  }
  return content;
}

function toReport(payload) {
  const sessionId = payload.session_id;
  switch (payload.hook_event_name) {
    case 'Stop':
    case 'StopFailure':
      return { event: 'turn.end', sessionId };
    case 'UserPromptSubmit':
      return { event: 'prompt', sessionId };
    case 'PermissionRequest':
      return { event: 'proposal', sessionId, files: [payload.tool_input?.file_path] };
    case 'PostToolUse':
      if (payload.tool_name === 'Bash') {
        return isRelevantCommand(payload.tool_input?.command) ? { event: 'command', sessionId } : undefined;
      }
      return {
        event: 'write',
        sessionId,
        files: [payload.tool_input?.file_path],
        content: payload.tool_name === 'Write' ? payload.tool_input?.content : editedContent(payload),
      };
    case 'PostToolUseFailure':
      // A command that exits non-zero may still have written its output.
      return payload.tool_name === 'Bash' && isRelevantCommand(payload.tool_input?.command) ? { event: 'command', sessionId } : undefined;
    default:
      return undefined;
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function isDisabled() {
  return /^(1|true)$/i.test(process.env.UIPATH_FLOW_DIFF_DISABLED ?? '');
}

function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    const timer = setTimeout(() => resolve(data), STDIN_TIMEOUT_MS);
    const finish = () => {
      clearTimeout(timer);
      resolve(data);
    };
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      data += chunk;
    });
    process.stdin.on('end', finish);
    process.stdin.on('error', finish);
  });
}

/** Only a live process of this user counts; a foreign pid (EPERM) may be a reused number. */
function isAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

export function isWithin(root, target) {
  const relative = path.relative(root, target);
  if (relative === '..' || relative.startsWith(`..${path.sep}`)) {
    return false;
  }
  return !path.isAbsolute(relative);
}

/** Same hash as the extension: ignores a leading BOM and CRLF vs LF. */
export function attestationHash(content) {
  const normalized = content.replace(/^﻿/, '').replace(/\r\n/g, '\n');
  return crypto.createHash('sha256').update(normalized, 'utf8').digest('hex');
}

function shortHash(value) {
  return crypto.createHash('sha256').update(value).digest('hex').slice(0, 16);
}

/** A private regular file owned by this user — never a symlink or something another user planted. */
function isPrivateFile(file) {
  const stat = fs.lstatSync(file);
  if (!stat.isFile()) {
    return false;
  }
  if (process.platform === 'win32') {
    return true;
  }
  return stat.uid === process.getuid() && (stat.mode & 0o077) === 0;
}

/** A lockfile is trusted only if it has the shape and permissions the extension writes. */
function readLock(file) {
  try {
    if (path.dirname(file) !== LOCK_DIR || !isPrivateFile(file)) {
      return undefined;
    }
    const lock = JSON.parse(fs.readFileSync(file, 'utf8'));
    const socketOk =
      typeof lock?.socket === 'string' &&
      (process.platform === 'win32'
        ? WINDOWS_PIPE.test(lock.socket)
        : path.isAbsolute(lock.socket) && UNIX_SOCKET.test(path.basename(lock.socket)));
    if (
      lock?.v !== PROTOCOL_VERSION ||
      !socketOk ||
      typeof lock.token !== 'string' ||
      !TOKEN.test(lock.token) ||
      !Number.isInteger(lock.pid) ||
      !Array.isArray(lock.workspaceFolders) ||
      !isAlive(lock.pid)
    ) {
      return undefined;
    }
    const extensions = Array.isArray(lock.extensions)
      ? lock.extensions.filter((extension) => typeof extension === 'string' && EXTENSION.test(extension))
      : REVIEWABLE_EXTENSIONS;
    const workspaceFolders = lock.workspaceFolders.filter((folder) => typeof folder === 'string' && path.isAbsolute(folder));
    return { file, socket: lock.socket, token: lock.token, workspaceFolders, extensions };
  } catch {
    return undefined;
  }
}

/** Every live window: the terminal's own first, then every other lockfile. */
function liveLocks() {
  const files = [];
  const fromEnv = process.env.UIPATH_FLOW_HOOK_LOCK;
  if (fromEnv) {
    files.push(fromEnv);
  }
  try {
    for (const name of fs.readdirSync(LOCK_DIR)) {
      if (name.endsWith('.lock')) {
        files.push(path.join(LOCK_DIR, name));
      }
    }
  } catch {
    // No lock directory: no extension is running.
  }
  const locks = [];
  for (const file of new Set(files)) {
    const lock = readLock(file);
    if (lock) {
      locks.push(lock);
    }
  }
  return locks;
}

function isReviewedBy(lock, file) {
  return lock.extensions.some((extension) => REVIEWABLE_EXTENSIONS.includes(extension) && file.endsWith(extension));
}

/** Windows with this file in a workspace folder, for a file type they review. */
function locksFor(locks, file) {
  return locks.filter((lock) => isReviewedBy(lock, file) && lock.workspaceFolders.some((folder) => isWithin(folder, file)));
}

/** Reads a reviewed file only if it is a regular file of sane size (never a FIFO or device). */
function readReviewedFile(file) {
  const handle = fs.openSync(file, fs.constants.O_RDONLY | (fs.constants.O_NONBLOCK ?? 0));
  try {
    const stat = fs.fstatSync(handle);
    if (!stat.isFile() || stat.size > MAX_FILE_BYTES) {
      return undefined;
    }
    return fs.readFileSync(handle, 'utf8');
  } finally {
    fs.closeSync(handle);
  }
}

function hashOnDisk(file) {
  try {
    const content = readReviewedFile(file);
    return content === undefined ? undefined : attestationHash(content);
  } catch {
    return undefined;
  }
}

/** Reviewed files under `root` modified after `since`; bounded, skipping dot-folders and node_modules. */
function modifiedSince(root, lock, since) {
  const found = [];
  const stack = [{ dir: root, depth: 0 }];
  let seen = 0;
  while (stack.length > 0) {
    const { dir, depth } = stack.pop();
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      seen += 1;
      if (seen > MAX_SCAN_ENTRIES) {
        return found;
      }
      const file = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (depth < MAX_SCAN_DEPTH && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
          stack.push({ dir: file, depth: depth + 1 });
        }
      } else if (entry.isFile() && isReviewedBy(lock, file)) {
        try {
          if (fs.statSync(file).mtimeMs > since) {
            found.push(file);
          }
        } catch {
          // Removed mid-scan.
        }
      }
    }
  }
  return found;
}

// ── Session state: sessions/<session>/ holds one entry per (window, file) plus a checkpoint ──

function sessionPath(sessionId) {
  const id = crypto.createHash('sha256').update(`${AGENT}:${sessionId}`).digest('hex').slice(0, 32);
  return path.join(SESSION_DIR, id);
}

/** Atomic add: `wx` never overwrites another process's entry, and an existing one is already recorded. */
function addEntry(dir, kind, lockFile, file) {
  fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
  const name = path.join(dir, `${kind}-${shortHash(lockFile)}-${shortHash(file)}`);
  try {
    fs.writeFileSync(name, JSON.stringify({ lock: lockFile, file }), { encoding: 'utf8', mode: 0o600, flag: 'wx' });
  } catch (error) {
    if (error?.code !== 'EEXIST') {
      throw error;
    }
  }
}

function hasEntries(dir) {
  try {
    return fs.readdirSync(dir).some((name) => ENTRY.test(name));
  } catch {
    return false;
  }
}

/** Takes the session's entries; an entry another process already unlinked is theirs. */
function claimEntries(dir) {
  let names;
  try {
    names = fs.readdirSync(dir).filter((name) => ENTRY.test(name));
  } catch {
    return [];
  }
  const claimed = [];
  for (const name of names) {
    const file = path.join(dir, name);
    let entry;
    try {
      entry = JSON.parse(fs.readFileSync(file, 'utf8'));
    } catch {
      continue;
    }
    try {
      fs.unlinkSync(file);
    } catch (error) {
      if (error?.code === 'ENOENT') {
        continue;
      }
      // Could not remove it: still end the turn it records.
    }
    if (typeof entry?.lock === 'string' && typeof entry?.file === 'string') {
      claimed.push({ kind: name[0], lock: entry.lock, file: entry.file });
    }
  }
  return claimed;
}

function readCheckpoint(dir) {
  try {
    return fs.statSync(path.join(dir, CHECKPOINT)).mtimeMs;
  } catch {
    return undefined;
  }
}

function writeCheckpoint(dir) {
  fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
  fs.writeFileSync(path.join(dir, CHECKPOINT), '', { mode: 0o600 });
}

/** Sessions that never ended (crash, interrupt) would otherwise pile up. */
function sweepOldSessions() {
  let names;
  try {
    names = fs.readdirSync(SESSION_DIR);
  } catch {
    return;
  }
  const cutoff = Date.now() - SESSION_MAX_AGE_MS;
  for (const name of names) {
    const dir = path.join(SESSION_DIR, name);
    try {
      const touched = Math.max(fs.statSync(dir).mtimeMs, readCheckpoint(dir) ?? 0);
      if (touched < cutoff) {
        fs.rmSync(dir, { recursive: true, force: true });
      }
    } catch {
      // Gone already, or not ours to remove.
    }
  }
}

/** Sends one message; skips a Unix socket that is not a socket owned by this user. */
function send(lock, message) {
  if (process.platform !== 'win32') {
    try {
      const stat = fs.lstatSync(lock.socket);
      if (!stat.isSocket() || stat.uid !== process.getuid()) {
        return Promise.resolve();
      }
    } catch {
      return Promise.resolve();
    }
  }
  return new Promise((resolve) => {
    const socket = net.createConnection(lock.socket);
    const done = () => {
      clearTimeout(timer);
      socket.destroy();
      resolve();
    };
    const timer = setTimeout(done, REQUEST_TIMEOUT_MS);
    socket.on('connect', () => socket.write(`${JSON.stringify({ ...message, token: lock.token })}\n`));
    socket.on('data', done);
    socket.on('error', done);
    socket.on('close', done);
  });
}

// ── Main ─────────────────────────────────────────────────────────────────────

function reviewedFiles(payload, report) {
  const cwd = typeof payload.cwd === 'string' ? payload.cwd : process.cwd();
  return (report.files ?? [])
    .filter((file) => typeof file === 'string')
    .map((file) => path.resolve(cwd, file))
    .filter((file) => REVIEWABLE_EXTENSIONS.some((extension) => file.endsWith(extension)));
}

/** Records each (window, file) pair as reported, then attests it to that window. */
async function attest(base, dir, writes) {
  sweepOldSessions();
  for (const { lock, file } of writes) {
    addEntry(dir, 'w', lock.file, file);
  }
  await Promise.all(writes.map(({ lock, file, hash }) => send(lock, { ...base, event: 'write', file, hashes: [hash] })));
}

/** Re-attests what the turn reported (a later `format` may have rewritten it), then ends the turn in each window. */
async function endTurn(base, dir) {
  const byLock = new Map();
  for (const entry of claimEntries(dir)) {
    const files = byLock.get(entry.lock) ?? new Set();
    if (entry.kind === 'w') {
      files.add(entry.file);
    }
    byLock.set(entry.lock, files);
  }
  await Promise.all(
    [...byLock].map(async ([lockFile, files]) => {
      const lock = readLock(lockFile);
      if (!lock) {
        return;
      }
      for (const file of files) {
        const hash = hashOnDisk(file);
        if (hash) {
          await send(lock, { ...base, event: 'write', file, hashes: [hash] });
        }
      }
      await send(lock, { ...base, event: 'turn.end' });
    })
  );
}

/** Remembers which windows a pending proposal concerns, so `Stop` reaches them even if nothing is written. */
function recordProposal(dir, payload, report) {
  const files = reviewedFiles(payload, report);
  if (files.length === 0) {
    return;
  }
  const locks = liveLocks();
  const pairs = files.flatMap((file) => locksFor(locks, file).map((lock) => ({ lock, file })));
  if (pairs.length === 0) {
    return;
  }
  sweepOldSessions();
  for (const { lock, file } of pairs) {
    addEntry(dir, 'p', lock.file, file);
  }
}

async function reportWrites(base, dir, payload, report) {
  const files = reviewedFiles(payload, report);
  if (files.length === 0) {
    return;
  }
  const locks = liveLocks();
  const writes = [];
  for (const file of files) {
    const targets = locksFor(locks, file);
    if (targets.length === 0) {
      continue;
    }
    // Write and a rebuilt Edit carry the exact content; the disk is only a fallback.
    const hash = typeof report.content === 'string' ? attestationHash(report.content) : hashOnDisk(file);
    if (!hash) {
      continue;
    }
    for (const lock of targets) {
      writes.push({ lock, file, hash });
    }
  }
  if (writes.length > 0) {
    await attest(base, dir, writes);
  }
}

/** A `uip maestro …` command: attests the reviewed files it changed since the session's checkpoint. */
async function reportCommand(base, dir) {
  const locks = liveLocks();
  if (locks.length === 0) {
    return;
  }
  const since = readCheckpoint(dir);
  writeCheckpoint(dir);
  if (since === undefined) {
    return;
  }
  const writes = [];
  for (const lock of locks) {
    for (const folder of lock.workspaceFolders) {
      for (const file of modifiedSince(folder, lock, since)) {
        const hash = hashOnDisk(file);
        if (hash) {
          writes.push({ lock, file, hash });
        }
      }
    }
  }
  if (writes.length > 0) {
    await attest(base, dir, writes);
  }
}

async function main() {
  if (isDisabled() || !fs.existsSync(LOCK_DIR)) {
    return;
  }
  let payload;
  try {
    payload = JSON.parse(await readStdin());
  } catch {
    return;
  }
  const report = payload && typeof payload === 'object' ? toReport(payload) : undefined;
  if (!report || typeof report.sessionId !== 'string' || !report.sessionId) {
    return;
  }
  // On Windows the hook's parent is a short-lived shell, not the agent, so it proves nothing about liveness.
  const pid = process.platform === 'win32' ? undefined : process.ppid;
  const base = { v: PROTOCOL_VERSION, agent: AGENT, sessionId: report.sessionId, pid };
  const dir = sessionPath(report.sessionId);

  switch (report.event) {
    case 'turn.end':
      if (hasEntries(dir)) {
        await endTurn(base, dir);
      }
      return;
    case 'prompt':
      // A new prompt ends the previous turn only if it never got its stop event.
      if (hasEntries(dir)) {
        await endTurn(base, dir);
      }
      writeCheckpoint(dir);
      return;
    case 'proposal':
      recordProposal(dir, payload, report);
      return;
    case 'command':
      await reportCommand(base, dir);
      return;
    default:
      await reportWrites(base, dir, payload, report);
  }
}

function isMain() {
  try {
    return import.meta.url === pathToFileURL(fs.realpathSync(process.argv[1])).href;
  } catch {
    return false;
  }
}

if (isMain()) {
  main()
    .catch(() => undefined)
    .finally(() => process.exit(0));
}
