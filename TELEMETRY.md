# UiPath Skills Plugin Telemetry

Opt-out usage telemetry for the UiPath skills plugin. On by default. One
`PostToolUse` hook (`hooks/send-telemetry.sh`) hands a single flat JSON object
per relevant tool call to the hidden `uip track` CLI command, which forwards it
through the CLI's own telemetry tracker as one `uip.skills.tool-use`
Application Insights event. No local state file, no session daemon —
session-level metrics are computed at query time from the event stream (see
[Correlation](#correlation)).

## Enabling / disabling

Telemetry is **opt-out / on by default**. The hook and `uip track` share one
gate:

| Env var | Effect |
|---------|--------|
| `UIPATH_TELEMETRY_DISABLED` | Reuses the `uip` CLI's variable name. Sends by default; set to `1` or `true` to disable. Unset (default), `0`, or any other value → send. |

Default (var unset) sends telemetry on a machine signed in to UiPath
(`uip login`). To opt out, set `UIPATH_TELEMETRY_DISABLED=1` (or `true`). The CLI owns the
Application Insights connection — there is **no** connection string to configure
on the skills side.

## What triggers an event

The hook fires on every tool call but emits only for calls attributable to this
plugin; everything else exits silently. A call qualifies when:

| Tool | Qualifies when |
|------|----------------|
| `Skill` | skill name starts with `uipath:` / `uipath-` |
| `Agent` / `spawn_agent` | spawned type is a UiPath agent (`uipath:` / `uipath-`) or a built-in/generic type (Claude's `general-purpose`, `Explore`, `Plan`, `claude`, `claude-code-guide`, `statusline-setup`, `fork`, or Codex's `default`) — **not** other plugins' (`<plugin>:<name>`) or user-defined custom agents. Claude spawns via `Agent` + `tool_input.subagent_type`; Codex via `spawn_agent` + `tool_input.agent_type` |
| `Bash` / `PowerShell` | command invokes the `uip` CLI or `rpa-tool` |
| `Edit` / `Write` / `Read` / `Glob` / `Grep` | path targets `.cs` (coded workflows), `.flow`, `.xaml`, `.uipx`, `.bpmn`, `agent.json`, `caseplan.json`, `project.json`, `app.config.json`, `action-schema.json` |

## How it works

1. The `PostToolUse` hook fires on every tool call and exits silently unless
   the call is attributable to this plugin (table above).
2. For a qualifying call it derives a small set of low-cardinality fields,
   sanitizes each value (charset + 120-char cap), and resolves the UiPath
   environment from `uip login status` (cached 1h). Field extraction is
   **region-scoped**: a single string-aware `awk` pass walks the payload once,
   tracking brace/string depth, and pulls each field only from the region it
   lives in — envelope (top-level keys), `tool_input`, `tool_response`, or
   `effort`. Free-form customer content embedded in a string (a prompt, a
   command line, `stdout`) can never false-match an envelope field (see
   [Region scoping](#region-scoping)).
3. It pipes one flat `key:value` JSON object to `uip track` on stdin, in a
   detached subshell, then exits 0.
4. `uip track` ([UiPath/cli#2600](https://github.com/UiPath/cli/pull/2600))
   reads that object, hard-codes the event name `uip.skills.tool-use`, stamps a
   `source: "skills-plugin"` dimension, attaches the authenticated UiPath cloud
   identity and the CLI app version, and forwards it through the CLI's
   telemetry tracker. Every key becomes an event property; non-scalar values
   (objects / arrays / `null`) are dropped.

The hook builds **no** App Insights envelope and makes **no** direct HTTP POST.
Transport, the connection, the event name, the `source` dimension, and identity
all belong to the CLI.

## What is collected

Each event is the App Insights event `uip.skills.tool-use`. Every key the hook
sends becomes an event property.

### Properties sent by the hook

| Field | Example | Notes |
|-------|---------|-------|
| `schemaVersion` | `1` | Constant in the hook. JSON **number**. Bumped on any change to the key set, so App Insights can segment events emitted with older/churned schemas |
| `toolName` | `Skill`, `Bash` | Claude Code tool. From the top-level `tool_name` |
| `toolUseId` | `toolu_01ABC` | Unique per call — correlation key + ordering tiebreaker |
| `sessionId` | `b3f1...` | Claude Code `session_id` — the coding-agent session; session correlation key |
| `subagentModel` | `opus` | From `tool_response.resolvedModel`, normalized to a family — `opus` / `sonnet` / `haiku` / `fable` (`other` if unrecognized). The context-window marker is dropped (`claude-opus-4-8[1m]` → `opus`). Set on an Agent-**spawn** event; empty otherwise |
| `subagentType` | `general-purpose` | From `tool_input.subagent_type` — requested subagent type. Set on an Agent-**spawn** event; empty otherwise |
| `agentType` | `Explore` | From the top-level `agent_type` — type of the subagent the call runs **inside**. Empty on a main-loop call |
| `skillName` | `uipath:uipath-platform` | From `tool_input.skill`. `Skill` calls only |
| `uipSubcommand` | `solution publish` | First 1–2 verbs derived from `tool_input.command` — never the full command line, never `stdout` |
| `fileExtension` | `.flow` | Derived from `tool_input.file_path`. File-tool calls only |
| `environment` | `alpha` / `staging` / `prod` / `other` / `unknown` | From `uip login status` `BaseUrl`, cached 1h |
| `baseUrl` | `https://cloud.uipath.com` | Cloud base URL only |
| `outcome` | `ok` / `failure` / `interrupted` / `unknown` | From the `tool_response` region **only**, never output content — see [Outcome semantics](#outcome-semantics) |
| `permissionMode` | `bypassPermissions` | From the top-level `permission_mode` |
| `effortLevel` | `high` | From the top-level `effort.level`, when present (`low` / `medium` / `high` / `xhigh` / `max`) |
| `skillsVersion` | `1.196.0` | `skillsVersion` from `version-manifest.json` |
| `durationMs` | `1234` | Tool-call wall-clock from the payload's `duration_ms`. JSON **number**; the CLI stringifies it for App Insights, so latency queries use `toreal(tostring(durationMs))`. `null` when absent → dropped |

`skillsVersion` tracks the CLI version (`version-manifest.json` `targetCli`); it
is **not** the `.claude-plugin/plugin.json` plugin package version. The hook no
longer sends `cliVersion` or `operatingSystem` — the CLI tracker already records
its own version as `application_Version` and the OS / client context by default.

### Region scoping

The payload embeds free-form customer content — prompts, command lines,
`stdout` / `stderr`, file contents. A grep over the **whole** payload
mis-extracts fields when that content happens to contain JSON-shaped text: a
`stdout` with `"success":false`, an Agent prompt naming `uip solution publish`
or `.flow"`, a log line with `"resolvedModel":"x"`. To prevent this, a single
string-aware `awk` pass walks the payload once, tracks brace/string nesting
depth (honoring `\"` and `\\` escapes), and emits each field **only** from the
region where it actually lives:

| Region | Fields |
|--------|--------|
| Envelope (top-level keys) | `toolName`, `toolUseId`, `sessionId`, `permissionMode`, `durationMs`, `effortLevel` (`effort.level`), `agentType` |
| `tool_input` | `skillName`, `uipSubcommand` (from `command`), `fileExtension` (from `file_path`), `subagentType` (from `subagent_type`, or `agent_type` on a Codex `spawn_agent` call — normalized to the same field so it never collides with the envelope `agent_type`) |
| `tool_response` | `outcome` (`interrupted` / `success`), `subagentModel` (`resolvedModel`) |

Content nested inside a JSON string, or at the wrong depth, can never satisfy a
top-level match — so `stdout` / prompt text cannot corrupt a field or cause
over-attribution. The relevance gate is scoped the same way (the `uip` command
is matched against `tool_input.command`, file extensions against
`tool_input.file_path`).

### Outcome semantics

`outcome` is computed from the `tool_response` region **only** — output content
never flips it:

| Value | Condition |
|-------|-----------|
| `interrupted` | top-level `tool_response.interrupted == true` (takes precedence) |
| `failure` | top-level `tool_response.success == false` |
| `ok` | `tool_response` present with no failure signal — the default for tools that report no status (`Read`, `Edit`, `Write`, `Glob`, most MCP) |
| `unknown` | no `tool_response` in the payload at all |

A `tool_response` that is a JSON **string** or **array** (some MCP tools) yields
`ok` — it is present but exposes no `success` / `interrupted` field.

### Subagent fields — distinct meanings

The three subagent fields describe two different viewpoints and are independent:

- **`subagentType` + `subagentModel`** describe an Agent-**spawn** event — i.e.
  `toolName == Agent` (Claude) or `spawn_agent` (Codex), the **parent's** view of
  the child it launched (`tool_input.subagent_type` / Codex's
  `tool_input.agent_type`, and the resolved `tool_response.resolvedModel`).
- **`agentType`** is set on calls made **inside** a subagent — the **child's**
  own view, from the top-level `agent_type`.

All three are empty on a plain main-loop tool call.

### Cross-agent compatibility

The hook is a `PostToolUse` hook, so it also runs under any coding agent that
honors `hooks.json` (e.g. **Codex**). Codex's payload envelope matches Claude
Code's — `hook_event_name`, `tool_name`, `tool_use_id`, `session_id`,
`permission_mode`, and `tool_input.{command,file_path}` are identical — so the
`PostToolUse` gate, the `Bash`/`uip` attribution, and the file-extension
attribution all work unchanged. Three differences are handled or accepted:

| Difference | Handling |
|------------|----------|
| **Agent spawns.** Codex uses `tool_name: "spawn_agent"` with the spawned type in `tool_input.agent_type` (Claude uses `Agent` + `tool_input.subagent_type`). | Handled. `spawn_agent` is gated like `Agent`; the `awk` normalizes `tool_input.agent_type` → `subagentType`, distinct from the envelope `agent_type` (→ `agentType`). Codex's generic `default` type qualifies, like Claude's `general-purpose`/`claude` |
| **`tool_response` is a JSON-encoded string,** not an object — even when its content is JSON. So `success` / `interrupted` / `resolvedModel` are absent. | Accepted. `outcome` is `ok` (response present, no failure signal) or `unknown`; it is never `failure`/`interrupted` for Codex. `subagentModel` stays empty. No content is parsed out of the string |
| **`duration_ms` and `effort.level` are omitted.** | Accepted. `durationMs` → `null` (dropped by the CLI), `effortLevel` → `""`. No latency or effort data for Codex |

Codex has no `Skill` tool, so `skillName` and the Skill-based attribution path
never fire — Codex attribution relies on the `uip`-command and file-extension
signals. The key set is unchanged, so `schemaVersion` stays `1`; events are
distinguished by agent through the CLI-stamped client/`source` context, not a
hook field.

### Added by the CLI

The CLI stamps these on every `uip.skills.tool-use` event — the hook never
sends them, and a `source` value sent by the hook would be overridden:

| Field | Notes |
|-------|-------|
| `source` | Always `skills-plugin` |
| `CloudUserId` / `CloudTenantId` / `CloudOrganizationId` | Authenticated UiPath cloud identity |
| `application_Version` | The `uip` CLI's own version (replaces the hook's former `cliVersion`) |
| OS / client context | Recorded by the tracker by default (replaces the hook's former `operatingSystem`) |

## Privacy

Skills telemetry rides the CLI's telemetry tracker, so each event is
**associated with the signed-in UiPath identity** — `CloudUserId`,
`CloudTenantId`, `CloudOrganizationId`, plus the CLI app version, all stamped by
the CLI. It is **not** anonymous.

What the hook **never** sends:

- File contents, `stdout`, `stderr` — only `outcome` and `durationMs`.
- Full command lines — only the derived `uip` subcommand verb.
- File paths — only the extension / known filename.
- The `cwd` / project path and `transcript_path` — neither is collected.

All fields the hook derives are low-cardinality. To stop all sending, opt out
with `UIPATH_TELEMETRY_DISABLED=1` (or `true`).

## Missing fields

Every property above is **always sent** by the hook, even when the source value
is absent from the payload, so query schemas stay stable:

- **String properties** fall back to an empty string `""` — a scalar the CLI
  keeps (it drops only objects, arrays, and `null`).
- **`durationMs`** falls back to JSON `null` when absent; the CLI drops `null`
  values, so a missing duration records as "no data" rather than `0` (which
  would skew latency aggregations).

## Correlation

Session-level metrics need no local state file — they are query-time
aggregations over events sharing `sessionId`:

| Metric | Query shape |
|--------|-------------|
| Tool calls per session | `count() by sessionId` |
| Session duration | `max(timestamp) - min(timestamp) by sessionId` |
| Time-to-first-skill | first `Skill` event − first event, per session |
| Retries | repeated `uipSubcommand` flipping `failure → ok`, ordered by `timestamp` then `toolUseId` |

## Reliability & performance

- **Non-blocking:** the hook is registered as an async hook in `hooks.json`
  (`"async": true`), so Claude Code runs it in the background and never waits
  for it. It pipes to `uip track` in a detached subshell and always exits 0 —
  it never delays or fails a tool call. `uip track` is itself never-fail (always
  exits 0, emits nothing when telemetry is off or on any error).
- **Best-effort delivery:** an event is dropped on failure (no local retry
  queue). Telemetry is for aggregate trends, not exact accounting.
- **Environment cost:** `uip login status` (~0.5s) runs at most once per hour;
  the result is cached in a per-user, `chmod 700` directory and parsed as data,
  never sourced.
- **Cross-platform:** pure POSIX `bash` + `grep`/`sed`/`awk`, no `jq`
  dependency (macOS, Linux, Windows Git Bash). Requires the `uip` CLI on `PATH`
  — the plugin's `SessionStart` hook ensures it is installed.
