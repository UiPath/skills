#!/usr/bin/env node
// SessionStart step: export the agent's session context to the uip CLI.
//
// Reads the SessionStart payload on stdin and appends `export` lines to
// $CLAUDE_ENV_FILE so every subsequent shell tool subprocess — and therefore
// every `uip` command the agent runs — inherits them:
//
//   UIPATH_SESSION_ID       top-level `session_id`. The CLI puts it on App
//                           Insights' native `ai.session.id` tag (query it as
//                           `session_Id`) for every command it runs, including
//                           the `uip track --hook` ingestions hooks.json
//                           registers (UiPath/cli#3431) — so the command stream
//                           and the skills events share one session id. This
//                           export is the ONLY way they correlate: since schema
//                           v3 the telemetry hook sends no session id of its
//                           own.
//   UIPATH_AGENT_MODEL      top-level `model` (string, or `{id, display_name}`)
//   UIPATH_PERMISSION_MODE  top-level `permission_mode`
//   UIPATH_EFFORT_LEVEL     `effort.level`
//   UIPATH_SKILLS_VERSION   `skillsVersion` from this plugin's
//                           version-manifest.json
//
// The CLI stamps the last four on every command request as the optional
// `agent_model` / `permissionMode` / `effortLevel` / `skillsVersion`
// dimensions — the same keys the skills events carry. They are the
// session-start snapshot: SessionStart re-fires on resume/clear/compact and
// re-exports any value that changed (the last export wins when sourced).
//
// Registered SYNCHRONOUSLY in hooks.json (no "async": true): the write must
// complete before the session's first shell call, or early `uip` commands
// would miss the values. Costs a few ms (one small JSON parse, no network, no
// uip call).
//
// Deliberately NOT gated on UIPATH_TELEMETRY_DISABLED: writing a variable
// transmits nothing — whether any event carrying it is ever sent stays
// governed by the CLI's own telemetry gate.
//
// Safety:
//   - host wins: no UIPATH_SESSION_ID export when it is already set in the env;
//   - idempotent: the id is appended only when the env file exports none yet;
//     a context variable only when the file does not already export that
//     exact value;
//   - injection-safe: $CLAUDE_ENV_FILE is sourced by the agent, so every value
//     is stripped to a quote-free charset and length-capped before being
//     written inside single quotes (agent session ids are UUIDs, so a
//     legitimate id is never altered);
//   - never-fail: always exits 0, never blocks the session.
//
// Runs under Node.js (>= 20); hooks.json guards the spawn and silently no-ops
// when `node` is not on PATH.

import fs from "node:fs";

const MANIFEST_URL = new URL("../version-manifest.json", import.meta.url);

function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function str(value) {
  return typeof value === "string" ? value : "";
}

// Same bound the CLI applies to every agent-supplied dimension.
function sanitizeToken(value) {
  return value.replace(/[^A-Za-z0-9:._/ -]/g, "_").slice(0, 120);
}

function sanitizeSessionId(value) {
  return value.replace(/[^A-Za-z0-9._-]/g, "").slice(0, 64);
}

function readSkillsVersion() {
  try {
    return str(JSON.parse(fs.readFileSync(MANIFEST_URL, "utf8")).skillsVersion);
  } catch {
    return "";
  }
}

function agentModel(payload) {
  const model = payload.model;
  if (isPlainObject(model)) return str(model.id) || str(model.display_name);
  return str(model);
}

/** The value the env file currently exports for `name` (the last export
 * wins when the file is sourced), or undefined when it exports none. */
function exportedValue(existing, name) {
  let value;
  for (const match of existing.matchAll(new RegExp(`^export ${name}='([^']*)'\\r?$`, "gm"))) {
    value = match[1];
  }
  return value;
}

function main() {
  const envFile = process.env.CLAUDE_ENV_FILE;
  if (!envFile) return;

  let payload;
  try {
    payload = JSON.parse(fs.readFileSync(0, "utf8"));
  } catch {
    return;
  }
  if (!isPlainObject(payload)) return;

  let existing = "";
  try {
    existing = fs.readFileSync(envFile, "utf8");
  } catch {
    existing = "";
  }

  const lines = [];

  const sid = sanitizeSessionId(str(payload.session_id));
  if (sid && !process.env.UIPATH_SESSION_ID && !/^export UIPATH_SESSION_ID=/m.test(existing)) {
    lines.push(`export UIPATH_SESSION_ID='${sid}'`);
  }

  const effort = isPlainObject(payload.effort) ? payload.effort : {};
  const context = [
    ["UIPATH_AGENT_MODEL", agentModel(payload)],
    ["UIPATH_PERMISSION_MODE", str(payload.permission_mode)],
    ["UIPATH_EFFORT_LEVEL", str(effort.level)],
    ["UIPATH_SKILLS_VERSION", readSkillsVersion()],
  ];
  for (const [name, raw] of context) {
    const value = sanitizeToken(raw.trim());
    if (value && exportedValue(existing, name) !== value) {
      lines.push(`export ${name}='${value}'`);
    }
  }

  if (lines.length === 0) return;

  // If the file exists but doesn't end with a newline (another hook's partial
  // write), appending directly would concatenate onto its last line and could
  // break the sourced env file for the whole session — repair it first.
  const prefix = existing && !existing.endsWith("\n") ? "\n" : "";

  try {
    fs.appendFileSync(envFile, `${prefix}${lines.join("\n")}\n`);
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
