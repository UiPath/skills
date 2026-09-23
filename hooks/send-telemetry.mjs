#!/usr/bin/env node
// Telemetry hook for the UiPath skills plugin (Claude Code).
//
// Registered on multiple Claude Code hook events (PostToolUse, SessionStart,
// SessionEnd, Stop, StopFailure). Reads the hook JSON payload from stdin, maps
// the event to a canonical eventName, and pipes one flat JSON object to
// `uip track`, which forwards it through the CLI's own telemetry tracker as a
// single uip.skills.<event> Application Insights event.
//
// tool-use is per-call and gated on plugin attribution (skill gate) — calls from
// other plugins or bare Claude Code are dropped. Lifecycle events (session-start,
// session-end, completion) are session-scoped and fire for every session where
// this plugin is installed.
//
// The CLI (see UiPath/cli#2600) owns transport, the App Insights connection,
// the event name, the authenticated cloud identity, the `source:
// "skills-plugin"` dimension, and — since UiPath/cli#2806 — the
// environment/base_url/region base dimensions stamped fresh on every event
// from its own auth context (so this hook sends no environment info). Since
// UiPath/cli#3431 the CLI also owns the session id: it resolves one per process
// (UIPATH_SESSION_ID, else an inherited agent/terminal handle) and puts it on
// App Insights' native ai.session.id tag, and `uip track` no longer accepts a
// session id from the payload — so this hook sends none. Correlation comes from
// set-session-env.mjs, which exports UIPATH_SESSION_ID for the session. This
// hook only derives + sanitizes fields and gates on the opt-out flag; value
// sanitization stays the hook's responsibility because the CLI and skills
// ship co-versioned.
//
// REGION-SCOPED EXTRACTION (see extractFields): the payload embeds free-form
// customer content (prompts, command lines, stdout/stderr, file contents). A
// naive text scan over the whole payload mis-extracts fields when that content
// contains JSON-shaped text (`"success":false`, `uip solution publish`,
// `.flow"`, `"resolvedModel":"..."`). So the payload is parsed as JSON and
// each field is read ONLY from the region it lives in:
//   ENVELOPE (top-level)  -> toolName, toolUseId, permissionMode,
//                            durationMs, effortLevel (effort.level), agentType,
//                            source (-> session_source), reason (session-end),
//                            model (-> agent_model; string or {id,display_name}.
//                            Claude Code omits it on most events, so the
//                            transcript is the fallback -- PILOT-7497)
//   tool_input            -> skillName, uipSubcommand (command), fileExtension
//                            (file_path), subagentType (subagent_type, or
//                            agent_type for a Codex spawn_agent call)
//   tool_response         -> outcome (interrupted/success), subagentModel
//                            (resolvedModel)
//
// CROSS-AGENT: registered as a PostToolUse hook, this also runs under other
// coding agents that honor hooks.json (e.g. Codex, UiPath Autopilot / Delegate).
// Codex's envelope matches Claude's (hook_event_name, tool_name, tool_use_id,
// session_id, permission_mode, tool_input/{command,file_path}), so Bash-`uip`
// and file attribution work unchanged. Differences handled / accepted: agent
// spawns use `spawn_agent` + tool_input.agent_type (see isUipathCall +
// extractFields); Codex omits duration_ms / effort.level (-> durationMs null,
// effortLevel "") and serializes tool_response as a JSON STRING, not an object,
// so success / interrupted / resolvedModel are absent and outcome is ok|unknown
// only. UiPath Autopilot / Delegate keep the same envelope but rename the shell
// and file tools — ExecuteBashCommand / ExecutePowershellCommand (vs Bash /
// PowerShell) and ReadFile / WriteFile / EditFile / LsDirectory (vs Read / Write
// / Edit / Glob / Grep); their tool_input still carries command / file_path, so
// the same attribution + derivation fire once those names are gated (see
// isUipathCall + deriveFields). Only derived, low-cardinality, PII-free
// values ever leave the machine.
//
// Non-blocking by contract: registered as an async hook in hooks.json
// ("async": true) on every event EXCEPT SessionEnd, so the agent runs it in the
// background and never waits for it. SessionEnd is registered SYNCHRONOUSLY
// (30s timeout): async hooks still running at session teardown are killed after
// a short grace window — shorter than `uip track` startup — which would silently
// drop the session-end event. The hand-off therefore runs INLINE on every event
// (spawnSync, never detached): the HOST owns non-blocking dispatch, and
// detaching it here would defeat the synchronous SessionEnd registration by
// letting the hook return before `uip track` has flushed. Always exits 0 and
// swallows every error.
//
// Runs under Node.js (>= 20) on every platform — node is a native executable,
// so no shell dialect or PowerShell execution policy applies. hooks.json guards
// the spawn and silently no-ops when `node` is not on PATH (a machine without
// node has no `uip` either, so there is nothing to hand off to).
//
// Structure: pure helpers + side-effecting procedures (below), driven by main()
// (bottom). Configuration is env only:
//   UIPATH_TELEMETRY_DISABLED   Gate. Reuses the uip CLI's variable name.
//                               Opt-out: send by DEFAULT. Skip ONLY when set to
//                               "1". Unset (default) or "0" -> send. Absent is
//                               treated as enabled.

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

// schemaVersion of the emitted event. Bump on ANY change to the key set so App
// Insights can segment events emitted with older/churned schemas. v2: adds the
// eventName / session_source / reason / agent_model keys, renames
// sessionId -> session_id (canonical casing, matches the CLI command stream,
// UiPath/cli#2800), and drops environment/baseUrl (the CLI stamps fresh
// environment/base_url/region base dimensions itself, UiPath/cli#2806). v3:
// drops session_id — the session is no longer a custom dimension; the CLI puts
// its own per-process id on the native ai.session.id tag and `uip track`
// rejects a payload session id (UiPath/cli#3431).
const SCHEMA_VERSION = 3;

// --- extraction ------------------------------------------------------------

/** A JSON object literal — not null, not an array. Region gates below only
 * descend into plain objects, so a string-serialized tool_response (Codex) or
 * an array-shaped model can never contribute fields. */
function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** String values only; any other JSON shape is malformed input for a string
 * field and is dropped, so `null`/`true` never reach telemetry. */
function str(value) {
  return typeof value === "string" ? value : "";
}

function isTrue(value) {
  return value === true || value === "true";
}

function isFalse(value) {
  return value === false || value === "false";
}

/** extractFields: read each field ONLY from the region it lives in (see
 * header), so embedded customer content can never false-match a top-level
 * field. Returns the field globals as one object. */
function extractFields(payload) {
  const input = isPlainObject(payload.tool_input) ? payload.tool_input : {};
  const response = isPlainObject(payload.tool_response) ? payload.tool_response : {};
  const effort = isPlainObject(payload.effort) ? payload.effort : {};

  // Object-shaped model emits no top-level string; use id, then display_name.
  let agentModel = str(payload.model);
  if (!agentModel && isPlainObject(payload.model)) {
    agentModel = str(payload.model.id) || str(payload.model.display_name);
  }

  // durationMs is numeric only: a non-negative integer (number or all-digit
  // string) passes; anything else resolves to null so a missing value doesn't
  // skew latency aggregations.
  let durationMs = null;
  const rawDuration = payload.duration_ms;
  if (Number.isInteger(rawDuration) && rawDuration >= 0) durationMs = rawDuration;
  else if (typeof rawDuration === "string" && /^[0-9]+$/.test(rawDuration)) {
    durationMs = Number.parseInt(rawDuration, 10);
  }

  return {
    event: str(payload.hook_event_name),
    tool: str(payload.tool_name),
    toolUseId: str(payload.tool_use_id),
    permissionMode: str(payload.permission_mode),
    durationMs,
    agentType: str(payload.agent_type),
    sessionSource: str(payload.source),
    reason: str(payload.reason),
    agentModel,
    transcriptPath: str(payload.transcript_path),
    skill: str(input.skill),
    command: str(input.command),
    filePath: str(input.file_path),
    // Codex spawn_agent carries the spawned type in tool_input.agent_type;
    // normalize it to the same field as Claude's tool_input.subagent_type so it
    // never collides with the envelope agent_type (agentType).
    subagentType: str(input.subagent_type) || str(input.agent_type),
    interrupted: response.interrupted,
    success: response.success,
    resolvedModel: str(response.resolvedModel),
    effortLevel: str(effort.level),
    responseSeen: "tool_response" in payload,
  };
}

/** Fallback when the envelope carried no `model` (PILOT-7497). Reads the LAST
 * assistant entry, so a mid-session /model switch is tracked. Subagent turns go
 * to <session>/subagents/agent-<id>.jsonl, so this yields the main-loop model.
 * 256KB tail: the last assistant entry is within ~28KB of EOF even at 5MB.
 * An absent, unreadable or not-yet-written transcript resolves to empty. */
function resolveAgentModel(fields) {
  if (fields.agentModel || !fields.transcriptPath) return;

  let tail = "";
  try {
    const fd = fs.openSync(fields.transcriptPath, "r");
    try {
      const size = fs.fstatSync(fd).size;
      const length = Math.min(size, 262144);
      const buffer = Buffer.alloc(length);
      fs.readSync(fd, buffer, 0, length, size - length);
      tail = buffer.toString("utf8");
    } finally {
      fs.closeSync(fd);
    }
  } catch {
    return;
  }

  // Whitespace-tolerant: the transcript format is undocumented. The FIRST
  // `"model"` match per line wins — the real key precedes free-form assistant
  // content, and embedded quotes inside content are escaped (\"), so
  // JSON-shaped text in a message can never out-match the real key.
  let model = "";
  for (const line of tail.split("\n")) {
    if (!/"type"[ \t\r]*:[ \t\r]*"assistant"/.test(line)) continue;
    const match = line.match(/"model"[ \t\r]*:[ \t\r]*"([^"]*)"/);
    if (!match) continue;
    // <synthetic> is a local turn (interrupt/error), not a model id.
    if (match[1] !== "" && match[1] !== "<synthetic>") model = match[1];
  }
  if (model) fields.agentModel = model;
}

// --- relevance gate --------------------------------------------------------

/** isUipathCall: true if this call is attributable to the plugin. No "active
 * plugin" field exists, so attribute per-call from tool_input signals only
 * (command / file_path), so stdout or prompt content can never over-attribute. */
function isUipathCall(fields) {
  switch (fields.tool) {
    case "Skill":
      return fields.skill.startsWith("uipath:") || fields.skill.startsWith("uipath-");
    case "Agent":
    case "spawn_agent": {
      // UiPath agents, or a built-in/generic agent type — NOT custom agents from
      // other plugins (`<plugin>:<name>`) or user-defined ones. Claude Code spawns
      // via `Agent` + tool_input.subagent_type; Codex via `spawn_agent` +
      // tool_input.agent_type (extractFields normalizes that to subagentType).
      // `default` is Codex's generic agent — the equivalent of Claude's
      // general-purpose/claude.
      const type = fields.subagentType;
      if (type.startsWith("uipath:") || type.startsWith("uipath-")) return true;
      return [
        "general-purpose",
        "Explore",
        "Plan",
        "claude",
        "claude-code-guide",
        "statusline-setup",
        "fork",
        "default",
      ].includes(type);
    }
    case "Bash":
    case "PowerShell":
    case "ExecuteBashCommand":
    case "ExecutePowershellCommand":
      return (
        /(^|[\\"\s;|&(])(uip|rpa-tool)\s/.test(fields.command) ||
        /\$UIP\b/.test(fields.command)
      );
    case "Edit":
    case "Write":
    case "Read":
    case "Glob":
    case "Grep":
    case "ReadFile":
    case "WriteFile":
    case "EditFile":
    case "LsDirectory":
      return (
        /\.(cs|flow|xaml|uipx|bpmn)$/i.test(fields.filePath) ||
        /(^|[/\\])(agent|caseplan|project|app\.config|action-schema)\.json$/i.test(
          fields.filePath,
        )
      );
    default:
      return false;
  }
}

// --- field derivation ------------------------------------------------------

/** deriveFields: skillName, uipSubcommand, fileExtension from the parsed
 * tool_input values (so stdout content can't leak in). */
function deriveFields(fields) {
  const derived = { skillName: "", uipSubcommand: "", fileExtension: "" };
  switch (fields.tool) {
    case "Skill":
      derived.skillName = fields.skill;
      break;
    case "Bash":
    case "PowerShell":
    case "ExecuteBashCommand":
    case "ExecutePowershellCommand": {
      // e.g. "solution publish" from "uip solution publish --output json".
      const match = fields.command.match(/(uip|\$UIP)\s+[a-z][a-z-]*(\s+[a-z][a-z-]*)?/);
      if (match) derived.uipSubcommand = match[0].replace(/^(uip|\$UIP)\s+/, "");
      break;
    }
    case "Edit":
    case "Write":
    case "Read":
    case "Glob":
    case "Grep":
    case "ReadFile":
    case "WriteFile":
    case "EditFile":
    case "LsDirectory": {
      const match = fields.filePath.match(/\.[A-Za-z0-9]+$/);
      derived.fileExtension = match ? match[0] : "";
      if (fields.filePath.endsWith("agent.json")) derived.fileExtension = "agent.json";
      if (fields.filePath.endsWith("caseplan.json")) derived.fileExtension = "caseplan.json";
      break;
    }
  }
  return derived;
}

/** computeOutcome: outcome from the tool_response region ONLY — content never
 * flips it.
 *   interrupted == true -> interrupted (takes precedence)
 *   success     == false -> failure
 *   tool_response present, no failure signal -> ok (Read/Edit/Write/most MCP)
 *   no tool_response at all -> unknown */
function computeOutcome(fields) {
  if (isTrue(fields.interrupted)) return "interrupted";
  if (isFalse(fields.success)) return "failure";
  if (fields.responseSeen) return "ok";
  return "unknown";
}

/** mapEventName: translate the agent hook event into the canonical eventName
 * token the CLI's `uip track` maps to a uip.skills.<event> event. An
 * unrecognized event returns empty so main() drops it. Stop and StopFailure
 * both map to `completion`, distinguished by outcome (see lifecycleOutcome).
 * CROSS-AGENT: Codex fires SessionStart and Stop under these SAME names with a
 * matching envelope (session_id/source/model; docs: developers.openai.com/
 * codex/hooks), so both map here unchanged. Codex has NO SessionEnd (completion
 * is its terminal signal) and no StopFailure (its API-error turns are not
 * distinguished). Gemini/Cursor use different hook names — separate follow-ups. */
function mapEventName(event) {
  switch (event) {
    case "PostToolUse":
      return "tool-use";
    case "SessionStart":
      return "session-start";
    case "SessionEnd":
      return "session-end";
    case "Stop":
    case "StopFailure":
      return "completion";
    default:
      return "";
  }
}

/** lifecycleOutcome: outcome for the non-tool events. A normal turn end (Stop)
 * is `ok`; an API-error turn end (StopFailure) is `failure`. session-start and
 * session-end carry no turn outcome (session-end's `reason` conveys the why). */
function lifecycleOutcome(event) {
  switch (event) {
    case "Stop":
      return "ok";
    case "StopFailure":
      return "failure";
    default:
      return "";
  }
}

/** modelFamily: the low-cardinality family, dropping the context-window marker
 * (e.g. claude-opus-4-8[1m] -> opus). Empty when absent (plain main-loop
 * call); `other` for an unrecognized family. */
function modelFamily(resolvedModel) {
  if (!resolvedModel) return "";
  if (resolvedModel.includes("opus")) return "opus";
  if (resolvedModel.includes("sonnet")) return "sonnet";
  if (resolvedModel.includes("haiku")) return "haiku";
  if (resolvedModel.includes("fable")) return "fable";
  return "other";
}

/** readSkillsVersion: skills/CLI co-version from version-manifest.json (NOT
 * git, NOT the plugin package version). The CLI's own app version already rides
 * the tracker as application_Version, so no separate cliVersion is sent. */
function readSkillsVersion() {
  try {
    const manifest = fs.readFileSync(
      path.join(process.env.CLAUDE_PLUGIN_ROOT || ".", "version-manifest.json"),
      "utf8",
    );
    const match = manifest.match(/"skillsVersion"\s*:\s*"([^"]*)"/);
    return match ? match[1] : "";
  } catch {
    return "";
  }
}

/** san: sanitize free-ish text to keep the emitted JSON bounded and
 * low-cardinality. Maps anything outside a safe charset to `_` (so no quotes /
 * backslashes / control chars / pipes survive) and caps length. */
function san(value) {
  return value.replace(/[^A-Za-z0-9:._/ -]/g, "_").slice(0, 120);
}

/** buildEventJson: assemble the canonical, ordered, flat JSON from the
 * (already sanitized) fields + SCHEMA_VERSION. The key set is defined ONCE
 * here (fixed order, every key always emitted). */
function buildEventJson(event) {
  return JSON.stringify({
    schemaVersion: SCHEMA_VERSION,
    eventName: event.eventName,
    toolName: event.toolName,
    skillName: event.skillName,
    uipSubcommand: event.uipSubcommand,
    fileExtension: event.fileExtension,
    outcome: event.outcome,
    permissionMode: event.permissionMode,
    effortLevel: event.effortLevel,
    skillsVersion: event.skillsVersion,
    toolUseId: event.toolUseId,
    subagentModel: event.subagentModel,
    subagentType: event.subagentType,
    agentType: event.agentType,
    agent_model: event.agentModel,
    session_source: event.sessionSource,
    reason: event.reason,
    durationMs: event.durationMs,
  });
}

// --- main ------------------------------------------------------------------

function main() {
  // Opt-out: send by default; skip only when telemetry is explicitly disabled
  // (UIPATH_TELEMETRY_DISABLED=1 or =true). Matches the CLI's isTelemetryDisabled()
  // gate, so `uip track` and this hook short-circuit on the same values.
  const disabled = process.env.UIPATH_TELEMETRY_DISABLED || "0";
  if (disabled === "1" || disabled === "true") return;

  let payload;
  try {
    payload = JSON.parse(fs.readFileSync(0, "utf8"));
  } catch {
    return;
  }
  if (!isPlainObject(payload)) return;

  const fields = extractFields(payload);
  resolveAgentModel(fields);

  // Map the hook event to a canonical eventName; drop unrecognized events.
  const eventName = mapEventName(fields.event);
  if (!eventName) return;

  // Derived only on tool-use; keep defined so the fixed key set always assembles.
  let derived = { skillName: "", uipSubcommand: "", fileExtension: "" };
  let outcome;
  let subagentModel = "";

  if (eventName === "tool-use") {
    // tool-use is per-call: gate on plugin attribution, then derive tool fields.
    if (!isUipathCall(fields)) return;
    derived = deriveFields(fields);
    outcome = computeOutcome(fields);
    subagentModel = modelFamily(fields.resolvedModel);
  } else {
    // Lifecycle events are session-scoped — they fire for every session where
    // this plugin is installed (the activation-rate denominator), so they skip
    // the per-call attribution gate and tool-field derivation.
    outcome = lifecycleOutcome(fields.event);
  }

  // Enforce the per-event field scoping the contract documents: session_source
  // only on session-start, reason only on session-end. extractFields reads
  // `source`/`reason` from ANY event's envelope, so a future payload that adds
  // either key to another event must not bleed into these dimensions.
  const sessionSource = eventName === "session-start" ? fields.sessionSource : "";
  const reason = eventName === "session-end" ? fields.reason : "";

  // Sanitize every string field before assembly.
  const json = buildEventJson({
    eventName: san(eventName),
    toolName: san(fields.tool),
    skillName: san(derived.skillName),
    uipSubcommand: san(derived.uipSubcommand),
    fileExtension: san(derived.fileExtension),
    outcome: san(outcome),
    permissionMode: san(fields.permissionMode),
    effortLevel: san(fields.effortLevel),
    skillsVersion: san(readSkillsVersion()),
    toolUseId: san(fields.toolUseId),
    subagentModel: san(subagentModel),
    subagentType: san(fields.subagentType),
    agentType: san(fields.agentType),
    agentModel: san(fields.agentModel),
    sessionSource: san(sessionSource),
    reason: san(reason),
    durationMs: fields.durationMs,
  });

  // Hand off to the CLI telemetry tracker. The CLI maps our eventName token to
  // the uip.skills.<event> name, stamps source: "skills-plugin", attaches the
  // authenticated cloud identity + CLI app version, owns transport + flush,
  // redacts PII, and drops any non-scalar value (so a null durationMs
  // disappears). Send no envelope, no `source` (the CLI overrides it), and no
  // session id (the CLI resolves its own and drops a payload one).
  //
  // INLINE, never detached: hooks.json registers this hook async on every event
  // except SessionEnd (see header), so the host — not this script — owns
  // non-blocking dispatch. A detached hand-off would return before `uip track`
  // flushed, silently dropping the very session-end event the synchronous
  // SessionEnd registration exists to protect. `uip track` is never-fail (exits
  // 0, emits nothing when telemetry is opted out); handing off to it is
  // harmless even if the CLI is absent (spawnSync reports the error in its
  // result instead of throwing).
  //
  // shell: true on Windows only — `uip` there is a `uip.cmd` npm shim, which
  // Node refuses to spawn directly (CVE-2024-27980); the argument list is
  // constant, so no untrusted text ever reaches that shell.
  spawnSync("uip", ["track"], {
    input: json,
    stdio: ["pipe", "ignore", "ignore"],
    shell: process.platform === "win32",
  });
}

try {
  main();
} catch {
  // never-fail: always exit 0 and swallow every error
}
process.exit(0);
