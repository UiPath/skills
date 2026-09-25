#!/usr/bin/env node
/**
 * Flow diff hook — reports coding-agent edits to `.flow` files to the UiPath
 * VS Code extension, so the canvas can show one before/after review per turn.
 *
 * Usage: node flow-diff-hook.mjs --agent <claude|gemini|cursor|codex>
 *
 * Agent-agnostic protocol (v2): each adapter below maps the agent's native hook
 * payload onto `write` (a reviewed file changed, with hashes of its new content as
 * the attestation), `turn.end`, `prompt` (a new prompt: end a turn that never got
 * its stop event, e.g. after an interrupt), and `proposal` (an edit awaits approval:
 * the turn must report its end even if the edit is rejected and nothing is written).
 * The extension only credits the agent with writes whose content matches an attestation.
 *
 * Contract — never gets in the agent's way:
 *   - Report-only: prints nothing, returns no decision, always exits 0.
 *   - Cheap for other work: exits before touching the filesystem unless the edited
 *     path has a reviewed extension; turn events only act on sessions that wrote
 *     one (a marker file records that).
 *   - Only talks to an extension it can find through a user-private lockfile
 *     (`~/.uipath/ide/*.lock`, or the one named by UIPATH_FLOW_HOOK_LOCK), and
 *     only over a socket path the extension itself would create.
 */

import crypto from 'node:crypto';
import fs from 'node:fs';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';

const PROTOCOL_VERSION = 2;
const REQUEST_TIMEOUT_MS = 2_000;
const MAX_FILE_BYTES = 10 * 1024 * 1024;
const MARKER_MAX_AGE_MS = 24 * 60 * 60 * 1000;
/** File types worth reporting at all; each window's lockfile narrows this to the ones it reviews. */
const REVIEWABLE_EXTENSIONS = ['.flow'];
const LOCK_DIR = path.join(os.homedir(), '.uipath', 'ide');
const SESSION_DIR = path.join(LOCK_DIR, 'sessions');
const TOKEN = /^[0-9a-f]{64}$/;
const UNIX_SOCKET = /^uipath-flow-hook-[0-9a-f]{16}\.sock$/;
const WINDOWS_PIPE = /^\\\\\.\\pipe\\uipath-flow-hook-[0-9a-f]{16}$/;
const EXTENSION = /^\.[a-z0-9]{1,16}$/;

// ── Adapters: native payload → { event, sessionId, files?, content? } ────────

/** Paths a Codex `apply_patch` touches (`*** Add File: …` / `*** Update File: …`). */
function codexPatchFiles(input) {
  const patch = typeof input === 'string' ? input : (input?.input ?? input?.patch ?? '');
  const files = [];
  for (const match of String(patch).matchAll(/^\*\*\* (?:Add|Update) File: (.+)$/gm)) {
    files.push(match[1].trim());
  }
  return files;
}

const ADAPTERS = {
  claude(p) {
    switch (p.hook_event_name) {
      case 'Stop':
      case 'StopFailure':
        return { event: 'turn.end', sessionId: p.session_id };
      case 'UserPromptSubmit':
        return { event: 'prompt', sessionId: p.session_id };
      case 'PermissionRequest':
        return { event: 'proposal', sessionId: p.session_id, files: [p.tool_input?.file_path] };
      case 'PostToolUse':
        // A Write carries the exact content it wrote; Edit/MultiEdit only a patch.
        return {
          event: 'write',
          sessionId: p.session_id,
          files: [p.tool_input?.file_path],
          content: p.tool_name === 'Write' ? p.tool_input?.content : undefined,
        };
      default:
        return undefined;
    }
  },
  gemini(p) {
    switch (p.hook_event_name) {
      case 'AfterAgent':
        return { event: 'turn.end', sessionId: p.session_id };
      case 'BeforeAgent':
        return { event: 'prompt', sessionId: p.session_id };
      case 'AfterTool':
        return { event: 'write', sessionId: p.session_id, files: [p.tool_input?.file_path ?? p.tool_input?.absolute_path] };
      default:
        return undefined;
    }
  },
  cursor(p) {
    switch (p.hook_event_name) {
      case 'stop':
        return { event: 'turn.end', sessionId: p.conversation_id };
      case 'beforeSubmitPrompt':
        return { event: 'prompt', sessionId: p.conversation_id };
      case 'afterFileEdit':
        return { event: 'write', sessionId: p.conversation_id, files: [p.file_path] };
      default:
        return undefined;
    }
  },
  codex(p) {
    switch (p.hook_event_name) {
      case 'Stop':
        return { event: 'turn.end', sessionId: p.session_id };
      case 'UserPromptSubmit':
        return { event: 'prompt', sessionId: p.session_id };
      case 'PostToolUse':
        return p.tool_name === 'apply_patch' ? { event: 'write', sessionId: p.session_id, files: codexPatchFiles(p.tool_input) } : undefined;
      default:
        return undefined;
    }
  },
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      data += chunk;
    });
    const timer = setTimeout(() => resolve(data), 2_000);
    process.stdin.on('end', () => {
      clearTimeout(timer);
      resolve(data);
    });
  });
}

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index === -1 ? undefined : process.argv[index + 1];
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

function isWithin(root, target) {
  const relative = path.relative(root, target);
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));
}

/** Same hash as the extension: ignores a leading BOM and CRLF vs LF. */
function attestationHash(content) {
  const normalized = content.replace(/^\uFEFF/, '').replace(/\r\n/g, '\n');
  return crypto.createHash('sha256').update(normalized, 'utf8').digest('hex');
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
    return { file, socket: lock.socket, token: lock.token, workspaceFolders: lock.workspaceFolders, extensions };
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

/** Windows with this file in a workspace folder, for a file type they review. */
function locksFor(locks, file) {
  return locks.filter(
    (lock) =>
      lock.extensions.some((extension) => file.endsWith(extension)) &&
      lock.workspaceFolders.some((folder) => typeof folder === 'string' && isWithin(folder, file))
  );
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

function markerPath(agent, sessionId) {
  const id = crypto.createHash('sha256').update(`${agent}:${sessionId}`).digest('hex').slice(0, 32);
  return path.join(SESSION_DIR, id);
}

/** Windows the session reported writes to (the marker lists their lockfiles). */
function readMarker(marker) {
  try {
    const locks = JSON.parse(fs.readFileSync(marker, 'utf8'));
    return Array.isArray(locks) ? locks.filter((file) => typeof file === 'string') : [];
  } catch {
    return [];
  }
}

function writeMarker(marker, lockFiles) {
  fs.mkdirSync(SESSION_DIR, { recursive: true, mode: 0o700 });
  fs.writeFileSync(marker, JSON.stringify(lockFiles), { encoding: 'utf8', mode: 0o600 });
}

/** Markers from turns that never ended (crash, interrupt) would otherwise pile up. */
function sweepOldMarkers() {
  try {
    const now = Date.now();
    for (const name of fs.readdirSync(SESSION_DIR)) {
      const file = path.join(SESSION_DIR, name);
      if (now - fs.statSync(file).mtimeMs > MARKER_MAX_AGE_MS) {
        fs.rmSync(file, { force: true });
      }
    }
  } catch {
    // Best effort.
  }
}

function send(lock, message) {
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

/** Ends the session's turn in every window it wrote to; a no-op for sessions that wrote nothing. */
async function endTurn(base, marker) {
  const lockFiles = readMarker(marker);
  fs.rmSync(marker, { force: true });
  const locks = lockFiles.map(readLock).filter(Boolean);
  await Promise.all(locks.map((lock) => send(lock, { ...base, event: 'turn.end' })));
}

/** Remembers which windows a pending proposal concerns, so `Stop` reaches them even if nothing is written. */
function recordProposal(marker, payload, report) {
  const files = reviewedFiles(payload, report);
  if (files.length === 0) {
    return;
  }
  const locks = liveLocks();
  const windows = new Set(readMarker(marker));
  for (const file of files) {
    for (const lock of locksFor(locks, file)) {
      windows.add(lock.file);
    }
  }
  if (windows.size > 0) {
    writeMarker(marker, [...windows]);
  }
}

function reviewedFiles(payload, report) {
  const cwd = typeof payload.cwd === 'string' ? payload.cwd : process.cwd();
  return (report.files ?? [])
    .filter((file) => typeof file === 'string')
    .map((file) => path.resolve(cwd, file))
    .filter((file) => REVIEWABLE_EXTENSIONS.some((extension) => file.endsWith(extension)));
}

async function reportWrites(base, marker, payload, report) {
  const files = reviewedFiles(payload, report);
  if (files.length === 0) {
    return;
  }
  const locks = liveLocks();
  const notified = new Set(readMarker(marker));
  for (const file of files) {
    const targets = locksFor(locks, file);
    if (targets.length === 0) {
      continue;
    }
    const hashes = [];
    if (typeof report.content === 'string') {
      hashes.push(attestationHash(report.content));
    }
    let content;
    try {
      content = readReviewedFile(file);
    } catch {
      content = undefined;
    }
    if (content !== undefined) {
      const onDisk = attestationHash(content);
      if (!hashes.includes(onDisk)) {
        hashes.push(onDisk);
      }
    }
    if (hashes.length === 0) {
      continue;
    }
    for (const lock of targets) {
      notified.add(lock.file);
    }
    try {
      sweepOldMarkers();
      writeMarker(marker, [...notified]);
    } catch {
      // No marker, no turn.end: the extension's idle check still closes the turn.
    }
    await Promise.all(targets.map((lock) => send(lock, { ...base, event: 'write', file, hashes })));
  }
}

async function main() {
  const agent = argValue('--agent');
  const adapter = Object.hasOwn(ADAPTERS, agent) ? ADAPTERS[agent] : undefined;
  if (!adapter) {
    return;
  }
  let payload;
  try {
    payload = JSON.parse(await readStdin());
  } catch {
    return;
  }
  const report = adapter(payload ?? {});
  if (!report || typeof report.sessionId !== 'string' || !report.sessionId) {
    return;
  }
  // On Windows the hook's parent is a short-lived shell, not the agent, so it proves nothing about liveness.
  const pid = process.platform === 'win32' ? undefined : process.ppid;
  const base = { v: PROTOCOL_VERSION, agent, sessionId: report.sessionId, pid };
  const marker = markerPath(agent, report.sessionId);

  if (report.event === 'turn.end' || report.event === 'prompt') {
    // A new prompt ends the previous turn only if it never got its stop event.
    if (fs.existsSync(marker)) {
      await endTurn(base, marker);
    }
    return;
  }
  if (report.event === 'proposal') {
    try {
      recordProposal(marker, payload, report);
    } catch {
      // No marker: a rejected proposal's canvas diff closes at the next write or turn instead.
    }
    return;
  }
  await reportWrites(base, marker, payload, report);
}

main()
  .catch(() => undefined)
  .finally(() => process.exit(0));
