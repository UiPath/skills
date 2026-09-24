#!/usr/bin/env node
// SessionStart step: export the agent's session id to the uip CLI.
//
// Reads the SessionStart payload on stdin, takes its top-level `session_id`,
// and appends `export UIPATH_SESSION_ID='<id>'` to $CLAUDE_ENV_FILE so every
// subsequent shell tool subprocess — and therefore every `uip` command the
// agent runs — inherits it. The CLI puts that value on App Insights' native
// `ai.session.id` tag (query it as `session_Id`) for every command it runs,
// including the `uip track --hook` ingestions hooks.json registers
// (UiPath/cli#3431) — so the command stream and the skills events share one
// session id. This
// export is the ONLY way they correlate: since schema v3 the telemetry hook
// sends no session id of its own.
//
// Registered SYNCHRONOUSLY in hooks.json (no "async": true): the write must
// complete before the session's first shell call, or early `uip` commands
// would miss the id. Costs a few ms (regex only, no network, no uip call).
//
// Deliberately NOT gated on UIPATH_TELEMETRY_DISABLED: writing a variable
// transmits nothing — whether any event carrying it is ever sent stays
// governed by the CLI's own telemetry gate.
//
// Safety:
//   - host wins: no-op when UIPATH_SESSION_ID is already set in the env;
//   - idempotent: no-op when the env file already exports it;
//   - injection-safe: $CLAUDE_ENV_FILE is sourced by the agent, so the value
//     is stripped to [A-Za-z0-9._-] and length-capped before being written
//     inside single quotes (agent session ids are UUIDs, so a legitimate
//     value is never altered);
//   - never-fail: always exits 0, never blocks the session.
//
// Runs under Node.js (>= 20); hooks.json guards the spawn and silently no-ops
// when `node` is not on PATH.

import fs from "node:fs";

function main() {
  const envFile = process.env.CLAUDE_ENV_FILE;
  if (!envFile) return;
  if (process.env.UIPATH_SESSION_ID) return;

  let existing = "";
  try {
    existing = fs.readFileSync(envFile, "utf8");
  } catch {
    existing = "";
  }
  if (/^export UIPATH_SESSION_ID=/m.test(existing)) return;

  // Top-level `session_id` from the SessionStart payload. The payload for this
  // event is small and carries no tool output, and the value is hard-sanitized
  // anyway, so a plain regex is sufficient here (no full JSON parse needed).
  let payload = "";
  try {
    payload = fs.readFileSync(0, "utf8");
  } catch {
    return;
  }
  const match = payload.match(/"session_id"\s*:\s*"([^"]*)"/);
  let sid = match ? match[1] : "";
  sid = sid.replace(/[^A-Za-z0-9._-]/g, "").slice(0, 64);
  if (!sid) return;

  // If the file exists but doesn't end with a newline (another hook's partial
  // write), appending directly would concatenate onto its last line and could
  // break the sourced env file for the whole session — repair it first.
  const prefix = existing && !existing.endsWith("\n") ? "\n" : "";

  try {
    fs.appendFileSync(envFile, `${prefix}export UIPATH_SESSION_ID='${sid}'\n`);
  } catch {
    // never-fail
  }
}

try {
  main();
} catch {
  // never-fail: always exit 0, never block the session
}
process.exit(0);
