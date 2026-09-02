#!/usr/bin/env node
/**
 * Flow diff hook — bridges Claude Code tool events to the UiPath VS Code
 * extension so `.flow` edits can be reviewed on the canvas before they apply.
 *
 * Wired in hooks.json for PreToolUse (Edit|MultiEdit|Write) and Stop.
 *
 * Contract (safety-first — never blocks the agent on hook failure):
 *   - Only acts on `*.flow` files; everything else exits 0 silently.
 *   - Discovers the extension's IPC socket via `.uipath/flow-agent-hook.json`,
 *     walked up from the edited file's directory (and cwd). If absent, the
 *     extension isn't running / the feature is off → exit 0 (no decision).
 *   - PreToolUse: forwards the event and waits for an allow/deny/ask decision.
 *     - allow/deny → emit the corresponding Claude Code permissionDecision.
 *     - ask / no response / any error → emit nothing → Claude's normal prompt.
 *   - Stop: notifies the extension to release manual hook control; exits 0.
 */

import net from 'node:net';
import fs from 'node:fs';
import path from 'node:path';

const RESPONSE_TIMEOUT_MS = 125_000; // Slightly under the hooks.json command timeout.

function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => (data += chunk));
    process.stdin.on('end', () => resolve(data));
    // If stdin never closes (shouldn't happen for hooks), don't hang forever.
    setTimeout(() => resolve(data), 2000);
  });
}

/** Walk up from `startDir` looking for `.uipath/flow-agent-hook.json`; return the socket path. */
function discoverSocket(startDir) {
  let dir = startDir;
  for (let i = 0; i < 40 && dir; i++) {
    const candidate = path.join(dir, '.uipath', 'flow-agent-hook.json');
    try {
      if (fs.existsSync(candidate)) {
        const parsed = JSON.parse(fs.readFileSync(candidate, 'utf8'));
        if (parsed && typeof parsed.socket === 'string') {
          return parsed.socket;
        }
      }
    } catch {
      /* ignore and keep walking */
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

/** Send one request over the socket and resolve with the parsed response (or null). */
function sendRequest(socketPath, request) {
  return new Promise((resolve) => {
    let settled = false;
    const done = (value) => {
      if (!settled) {
        settled = true;
        resolve(value);
      }
    };

    const socket = net.createConnection(socketPath);
    let buffer = '';

    const timer = setTimeout(() => {
      socket.destroy();
      done(null);
    }, RESPONSE_TIMEOUT_MS);

    socket.on('connect', () => {
      socket.write(`${JSON.stringify(request)}\n`);
    });
    socket.on('data', (chunk) => {
      buffer += chunk.toString('utf8');
      const idx = buffer.indexOf('\n');
      if (idx !== -1) {
        clearTimeout(timer);
        socket.end();
        try {
          done(JSON.parse(buffer.slice(0, idx)));
        } catch {
          done(null);
        }
      }
    });
    socket.on('error', () => {
      clearTimeout(timer);
      done(null);
    });
    socket.on('close', () => {
      clearTimeout(timer);
      done(null);
    });
  });
}

async function main() {
  const raw = await readStdin();
  let payload;
  try {
    payload = JSON.parse(raw);
  } catch {
    process.exit(0);
  }

  const event = payload.hook_event_name;
  const cwd = payload.cwd || process.cwd();

  if (event === 'Stop') {
    const socketPath = discoverSocket(cwd);
    if (socketPath) {
      await sendRequest(socketPath, { event: 'Stop', sessionId: payload.session_id });
    }
    process.exit(0);
  }

  if (event !== 'PreToolUse') {
    process.exit(0);
  }

  const toolInput = payload.tool_input || {};
  const filePath = toolInput.file_path;
  if (typeof filePath !== 'string' || !filePath.endsWith('.flow')) {
    process.exit(0); // Not a flow edit — let it proceed normally.
  }

  const socketPath = discoverSocket(path.dirname(filePath)) || discoverSocket(cwd);
  if (!socketPath) {
    process.exit(0); // Extension not listening — defer to Claude's normal flow.
  }

  const response = await sendRequest(socketPath, {
    event: 'PreToolUse',
    tool: payload.tool_name,
    filePath,
    permissionMode: payload.permission_mode,
    toolInput,
    sessionId: payload.session_id,
  });

  const decision = response && response.decision;
  if (decision === 'allow' || decision === 'deny') {
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: decision,
          permissionDecisionReason:
            decision === 'allow' ? 'Approved on the UiPath flow canvas.' : 'Declined on the UiPath flow canvas.',
        },
      })
    );
  }
  // decision === 'ask' / null → emit nothing → Claude falls back to its prompt.
  process.exit(0);
}

main().catch(() => process.exit(0));
