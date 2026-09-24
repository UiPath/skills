#!/usr/bin/env node
/**
 * Flow diff hook — reports coding-agent edits to `.flow` files to the UiPath
 * VS Code extension, so the canvas can show one before/after review per turn.
 *
 * Usage: node flow-diff-hook.mjs --agent <claude|gemini|cursor|codex>
 *
 * Agent-agnostic protocol (v2): each adapter below maps the agent's native hook
 * payload onto two events — `write` (a `.flow` file changed, with a sha256 of its
 * new content as the attestation) and `turn.end`. The extension only credits the
 * agent with writes whose content matches an attestation.
 *
 * Contract — never gets in the agent's way:
 *   - Report-only: prints nothing, returns no decision, always exits 0.
 *   - Cheap for non-flow work: exits before touching the filesystem unless the
 *     edited path ends in `.flow`; `turn.end` is sent only for sessions that
 *     actually wrote a flow (a marker file records that).
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
const LOCK_DIR = path.join(os.homedir(), '.uipath', 'ide');
const SESSION_DIR = path.join(LOCK_DIR, 'sessions');
const TOKEN = /^[0-9a-f]{64}$/;
const UNIX_SOCKET = /^uipath-flow-hook-[0-9a-f]{16}\.sock$/;
const WINDOWS_PIPE = /^\\\\\.\\pipe\\uipath-flow-hook-[0-9a-f]{16}$/;

// ── Adapters: native payload → { event, sessionId, files } ───────────────────

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
    if (p.hook_event_name === 'Stop') {
      return { event: 'turn.end', sessionId: p.session_id };
    }
    if (p.hook_event_name === 'PostToolUse') {
      return { event: 'write', sessionId: p.session_id, files: [p.tool_input?.file_path] };
    }
    return undefined;
  },
  gemini(p) {
    if (p.hook_event_name === 'AfterAgent') {
      return { event: 'turn.end', sessionId: p.session_id };
    }
    if (p.hook_event_name === 'AfterTool') {
      return { event: 'write', sessionId: p.session_id, files: [p.tool_input?.file_path ?? p.tool_input?.absolute_path] };
    }
    return undefined;
  },
  cursor(p) {
    if (p.hook_event_name === 'stop') {
      return { event: 'turn.end', sessionId: p.conversation_id };
    }
    if (p.hook_event_name === 'afterFileEdit') {
      return { event: 'write', sessionId: p.conversation_id, files: [p.file_path] };
    }
    return undefined;
  },
  codex(p) {
    if (p.hook_event_name === 'Stop') {
      return { event: 'turn.end', sessionId: p.session_id };
    }
    if (p.hook_event_name === 'PostToolUse' && p.tool_name === 'apply_patch') {
      return { event: 'write', sessionId: p.session_id, files: codexPatchFiles(p.tool_input) };
    }
    return undefined;
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
    process.stdin.on('end', () => resolve(data));
    setTimeout(() => resolve(data), 2_000);
  });
}

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index === -1 ? undefined : process.argv[index + 1];
}

function isAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (err) {
    return err.code === 'EPERM';
  }
}

function isWithin(root, target) {
  const relative = path.relative(root, target);
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));
}

/** A lockfile is trusted only if it has the shape the extension writes. */
function readLock(file) {
  try {
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
    return { file, ...lock };
  } catch {
    return undefined;
  }
}

/** The extension window that owns `filePath`: the terminal's own window first, else a matching lockfile. */
function findLock(filePath) {
  const fromEnv = process.env.UIPATH_FLOW_HOOK_LOCK;
  if (fromEnv && path.dirname(fromEnv) === LOCK_DIR) {
    const lock = readLock(fromEnv);
    if (lock) {
      return lock;
    }
  }
  let entries = [];
  try {
    entries = fs.readdirSync(LOCK_DIR).filter((name) => name.endsWith('.lock'));
  } catch {
    return undefined;
  }
  for (const name of entries) {
    const lock = readLock(path.join(LOCK_DIR, name));
    if (lock && lock.workspaceFolders.some((folder) => typeof folder === 'string' && isWithin(folder, filePath))) {
      return lock;
    }
  }
  return undefined;
}

function markerPath(agent, sessionId) {
  const id = crypto.createHash('sha256').update(`${agent}:${sessionId}`).digest('hex').slice(0, 32);
  return path.join(SESSION_DIR, id);
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
  const base = { v: PROTOCOL_VERSION, agent, sessionId: report.sessionId, pid: process.ppid };
  const marker = markerPath(agent, report.sessionId);

  if (report.event === 'turn.end') {
    // Only sessions that wrote a flow have anything to end.
    let lockFile;
    try {
      lockFile = fs.readFileSync(marker, 'utf8').trim();
      fs.rmSync(marker, { force: true });
    } catch {
      return;
    }
    const lock = path.dirname(lockFile) === LOCK_DIR ? readLock(lockFile) : undefined;
    if (lock) {
      await send(lock, { ...base, event: 'turn.end' });
    }
    return;
  }

  const cwd = typeof payload.cwd === 'string' ? payload.cwd : process.cwd();
  const flows = (report.files ?? [])
    .filter((file) => typeof file === 'string' && file.endsWith('.flow'))
    .map((file) => path.resolve(cwd, file));
  for (const file of flows) {
    const lock = findLock(file);
    if (!lock) {
      continue;
    }
    let content;
    try {
      content = fs.readFileSync(file, 'utf8');
    } catch {
      continue;
    }
    const sha256 = crypto.createHash('sha256').update(content, 'utf8').digest('hex');
    try {
      fs.mkdirSync(SESSION_DIR, { recursive: true, mode: 0o700 });
      fs.writeFileSync(marker, lock.file, { encoding: 'utf8', mode: 0o600 });
    } catch {
      /* no marker → no turn.end; the extension's idle/liveness check still closes the turn */
    }
    await send(lock, { ...base, event: 'write', file, sha256 });
  }
}

main()
  .catch(() => undefined)
  .finally(() => process.exit(0));
