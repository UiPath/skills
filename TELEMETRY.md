# UiPath Skills Plugin Telemetry

Opt-out usage telemetry for the UiPath skills plugin. On by default. One
emitting hook (`hooks/send-telemetry.sh` / its PowerShell twin
`send-telemetry.ps1`), registered on several Claude Code hook events, hands a
single flat JSON object to the hidden `uip track` CLI command, which forwards
it through the CLI's own telemetry tracker as one `uip.skills.<event>`
Application Insights event. A second, synchronous SessionStart step
(`hooks/set-session-env.sh` / `.ps1`) exports the agent session id as
`UIPATH_SESSION_ID` so native `uip` command telemetry carries the same
`session_id` (see [Correlation](#correlation)). No local state file, no
session daemon — session-level metrics are computed at query time from the
event stream.

## Events

The hook carries an `eventName` token; `uip track` owns the `uip.skills.*`
namespace and maps the token to the emitted event. `tool-use` is **per tool
call** and gated on plugin attribution (table below); the lifecycle events are
**session-scoped** and fire for every session where this plugin is installed —
they are the denominator for activation-rate and session-mix metrics.

| Claude Code hook | `eventName` | Emitted event | Scope |
|------------------|-------------|---------------|-------|
| `PostToolUse` | `tool-use` | `uip.skills.tool-use` | per tool call (gated) |
| `SessionStart` | `session-start` | `uip.skills.session-start` | per session |
| `Stop` | `completion` | `uip.skills.completion` | per turn (`outcome=ok`) |
| `StopFailure` | `completion` | `uip.skills.completion` | per turn (`outcome=failure`, API error) |
| `SessionEnd` | `session-end` | `uip.skills.session-end` | per session |

`Stop` and `StopFailure` both map to `completion`, distinguished by `outcome`,
so an API-error turn is not lost from completion/abandonment metrics.

### Per-agent availability

The hook runs under any agent that honors `hooks.json`. **Codex fires
`SessionStart` and `Stop` under the same names with a matching envelope**
(`session_id`, `source`, `model` — [Codex hooks
docs](https://developers.openai.com/codex/hooks)), so the mapping above works
for both agents unchanged:

| Event | Claude Code | Codex | Field differences on Codex |
|-------|-------------|-------|----------------------------|
| `session-start` | ✓ `SessionStart` | ✓ `SessionStart` | none relevant — `source` and `model` present on both |
| `completion` | ✓ `Stop` (`outcome=ok`) / `StopFailure` (`outcome=failure`) | ✓ `Stop` only — `outcome` is always `ok` (Codex has no `StopFailure`; API-error turns are not distinguished) | extras `turn_id` / `stop_hook_active` / `last_assistant_message` are **not read**; no `duration_ms` → `durationMs: null` |
| `session-end` | ✓ `SessionEnd` (`reason`) | ✗ — no `SessionEnd` hook; `completion` is the terminal signal | `reason` never present |
| `tool-use` | ✓ `PostToolUse` | ✓ `PostToolUse` | `tool_response` is a JSON string → `outcome` is `ok`/`unknown` only; no `duration_ms`/`effort.level` (see [Cross-agent compatibility](#cross-agent-compatibility)) |

**Gemini CLI and the Cursor CLI** expose the same lifecycle moments under
different hook names/registration formats and are separate follow-ups.
**Cursor cloud agents are out of scope** — they run in an ephemeral
remote VM with no local `uip` CLI, no authenticated identity, and no
session-start/-end trigger point.

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
| `Bash` / `PowerShell` (Autopilot / Delegate: `ExecuteBashCommand` / `ExecutePowershellCommand`) | command invokes the `uip` CLI or `rpa-tool` |
| `Edit` / `Write` / `Read` / `Glob` / `Grep` (Autopilot / Delegate: `ReadFile` / `WriteFile` / `EditFile` / `LsDirectory`) | path targets `.cs` (coded workflows), `.flow`, `.xaml`, `.uipx`, `.bpmn`, `agent.json`, `caseplan.json`, `project.json`, `app.config.json`, `action-schema.json` |

## How it works

1. The hook fires on every registered event. On `PostToolUse` it exits
   silently unless the tool call is attributable to this plugin (table above);
   the lifecycle events (`SessionStart` / `SessionEnd` / `Stop` /
   `StopFailure`) are session-scoped and skip that per-call gate — steps 2–4
   below describe the richer tool-use path, lifecycle events carry only the
   envelope fields (see [Events](#events)).
2. For a qualifying call it derives a small set of low-cardinality fields and
   sanitizes each value (charset + 120-char cap). Field extraction is
   **region-scoped**: each field is read only from the region it lives in —
   envelope (top-level keys), `tool_input`, `tool_response`, or `effort`
   (the bash twin walks the JSON with a string-aware `awk` pass; the
   PowerShell twin parses it with `ConvertFrom-Json`). Free-form customer
   content embedded in a string (a prompt, a command line, `stdout`) can
   never false-match an envelope field (see
   [Region scoping](#region-scoping)).
3. It pipes one flat `key:value` JSON object to `uip track` on stdin, then
   exits 0.
4. `uip track` ([UiPath/cli#2600](https://github.com/UiPath/cli/pull/2600),
   extended for lifecycle events in
   [UiPath/cli#2815](https://github.com/UiPath/cli/pull/2815)) reads that
   object, maps the `eventName` token to the CLI-owned `uip.skills.<event>`
   name (an unrecognized token drops the event; an absent one means
   `tool-use`), stamps a `source: "skills-plugin"` dimension, attaches the
   authenticated UiPath cloud identity and the CLI app version, and forwards it
   through the CLI's telemetry tracker. Every key becomes an event property;
   non-scalar values (objects / arrays / `null`) are dropped.

The hook builds **no** App Insights envelope and makes **no** direct HTTP POST.
Transport, the connection, the event name, the `source` dimension, and identity
all belong to the CLI.

## What is collected

Each event is an App Insights event named `uip.skills.<event>` (see
[Events](#events)). Every key the hook sends becomes an event property.

### Properties sent by the hook

| Field | Example | Notes |
|-------|---------|-------|
| `schemaVersion` | `2` | Constant in the hook. JSON **number**. Bumped on any change to the key set, so App Insights can segment events emitted with older/churned schemas. `2` added `eventName` / `session_source` / `reason` / `agent_model`, renamed `sessionId` → `session_id`, and dropped `environment` / `baseUrl` (CLI-stamped since [UiPath/cli#2806](https://github.com/UiPath/cli/pull/2806) — see [Added by the CLI](#added-by-the-cli)) |
| `eventName` | `session-start` | Which lifecycle event this is (see [Events](#events)). Consumed by `uip track` to pick the `uip.skills.<event>` name; **not** emitted as an event property |
| `toolName` | `Skill`, `Bash` | Claude Code tool. From the top-level `tool_name`. `tool-use` only |
| `toolUseId` | `toolu_01ABC` | Unique per call — correlation key + ordering tiebreaker |
| `session_id` | `b3f1...` | Claude Code `session_id` — the coding-agent session; session correlation key. Canonical snake_case, matching the CLI command stream ([UiPath/cli#2800](https://github.com/UiPath/cli/pull/2800)); `uip track` still accepts the v1 `sessionId` spelling and maps it |
| `subagentModel` | `opus` | From `tool_response.resolvedModel`, normalized to a family — `opus` / `sonnet` / `haiku` / `fable` (`other` if unrecognized). The context-window marker is dropped (`claude-opus-4-8[1m]` → `opus`). Set on an Agent-**spawn** event; empty otherwise |
| `subagentType` | `general-purpose` | From `tool_input.subagent_type` — requested subagent type. Set on an Agent-**spawn** event; empty otherwise |
| `agentType` | `Explore` | From the top-level `agent_type` — type of the subagent the call runs **inside**. Empty on a main-loop call |
| `agent_model` | `claude-sonnet-5` | The session's **main** model, from the top-level `model` where the agent provides it — Claude Code sends it on `SessionStart` payloads, Codex on every hook event. Full sanitized slug (no family collapse — model-comparison views need version granularity); distinct from `subagentModel` (a spawned child's model family). Empty when the payload carries none; Claude sessions get full coverage at query time by joining on `session_id` from the `session-start` event |
| `skillName` | `uipath:uipath-platform` | From `tool_input.skill`. `Skill` calls only |
| `uipSubcommand` | `solution publish` | First 1–2 verbs derived from `tool_input.command` — never the full command line, never `stdout` |
| `fileExtension` | `.flow` | Derived from `tool_input.file_path`. File-tool calls only |
| `outcome` | `ok` / `failure` / `interrupted` / `unknown` | On `tool-use`, from the `tool_response` region **only**; on `completion`, `ok` (`Stop`) or `failure` (`StopFailure`) — see [Outcome semantics](#outcome-semantics) |
| `session_source` | `startup` / `resume` / `clear` / `compact` | `session-start` only. From the top-level `source` (renamed to avoid the CLI-owned `source` dimension) |
| `reason` | `logout` / `clear` / `resume` / … | `session-end` only. Why the session ended, from the top-level `reason` (values are agent-specific) |
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
`stdout` / `stderr`, file contents. A text scan over the **whole** payload
mis-extracts fields when that content happens to contain JSON-shaped text: a
`stdout` with `"success":false`, an Agent prompt naming `uip solution publish`
or `.flow"`, a log line with `"resolvedModel":"x"`. To prevent this, the hook
reads each field **only** from the region where it actually lives (the bash
twin via a single string-aware `awk` pass that tracks brace/string nesting;
the PowerShell twin via a real `ConvertFrom-Json` parse):

| Region | Fields |
|--------|--------|
| Envelope (top-level keys) | `toolName`, `toolUseId`, `session_id`, `permissionMode`, `durationMs`, `effortLevel` (`effort.level`), `agentType`, `source` (→`session_source`, session-start), `reason` (session-end), `model` (→`agent_model`) |
| `tool_input` | `skillName`, `uipSubcommand` (from `command`), `fileExtension` (from `file_path`), `subagentType` (from `subagent_type`, or `agent_type` on a Codex `spawn_agent` call — normalized to the same field so it never collides with the envelope `agent_type`) |
| `tool_response` | `outcome` (`interrupted` / `success`), `subagentModel` (`resolvedModel`) |

Content nested inside a JSON string, or at the wrong depth, can never satisfy a
top-level match — so `stdout` / prompt text cannot corrupt a field or cause
over-attribution. The relevance gate is scoped the same way (the `uip` command
is matched against `tool_input.command`, file extensions against
`tool_input.file_path`).

### Outcome semantics

On `tool-use`, `outcome` is computed from the `tool_response` region **only** —
output content never flips it:

| Value | Condition |
|-------|-----------|
| `interrupted` | top-level `tool_response.interrupted == true` (takes precedence) |
| `failure` | top-level `tool_response.success == false` |
| `ok` | `tool_response` present with no failure signal — the default for tools that report no status (`Read`, `Edit`, `Write`, `Glob`, most MCP) |
| `unknown` | no `tool_response` in the payload at all |

A `tool_response` that is a JSON **string** or **array** (some MCP tools) yields
`ok` — it is present but exposes no `success` / `interrupted` field.

On `completion`, `outcome` comes from the hook event itself, not a tool
response: `ok` for `Stop` (normal turn end) and `failure` for `StopFailure` (the
turn ended on an API error). `session-start` and `session-end` carry no
`outcome` (an empty string); `session-end`'s `reason` conveys why it ended.

### Subagent fields — distinct meanings

The three subagent fields describe two different viewpoints and are independent:

- **`subagentType` + `subagentModel`** describe an Agent-**spawn** event — i.e.
  `toolName == Agent` (Claude) or `spawn_agent` (Codex), the **parent's** view of
  the child it launched (`tool_input.subagent_type` / Codex's
  `tool_input.agent_type`, and the resolved `tool_response.resolvedModel`).
- **`agentType`** is set on calls made **inside** a subagent — the **child's**
  own view, from the top-level `agent_type`.

All three are empty on a plain main-loop tool call. **`agent_model`** is none
of these: it is the **session's main model** (from the envelope `model`),
independent of any subagent — the dimension for model-comparison views
(UiPath/cli#2785).

### Cross-agent compatibility

The hook is a `PostToolUse` hook, so it also runs under any coding agent that
honors `hooks.json` (e.g. **Codex**). Codex's payload envelope matches Claude
Code's — `hook_event_name`, `tool_name`, `tool_use_id`, `session_id`,
`permission_mode`, and `tool_input.{command,file_path}` are identical — so the
`PostToolUse` gate, the `Bash`/`uip` attribution, and the file-extension
attribution all work unchanged. Three differences are handled or accepted:

| Difference | Handling |
|------------|----------|
| **Agent spawns.** Codex uses `tool_name: "spawn_agent"` with the spawned type in `tool_input.agent_type` (Claude uses `Agent` + `tool_input.subagent_type`). | Handled. `spawn_agent` is gated like `Agent`; extraction normalizes `tool_input.agent_type` → `subagentType`, distinct from the envelope `agent_type` (→ `agentType`). Codex's generic `default` type qualifies, like Claude's `general-purpose`/`claude` |
| **`tool_response` is a JSON-encoded string,** not an object — even when its content is JSON. So `success` / `interrupted` / `resolvedModel` are absent. | Accepted. `outcome` is `ok` (response present, no failure signal) or `unknown`; it is never `failure`/`interrupted` for Codex. `subagentModel` stays empty. No content is parsed out of the string |
| **`duration_ms` and `effort.level` are omitted.** | Accepted. `durationMs` → `null` (dropped by the CLI), `effortLevel` → `""`. No latency or effort data for Codex |

Codex has no `Skill` tool, so `skillName` and the Skill-based attribution path
never fire — Codex attribution relies on the `uip`-command and file-extension
signals. The cross-agent handling itself changes no keys; the current key set
is **schema v2** (see the [field table](#properties-sent-by-the-hook)). Events
are distinguished by agent through the CLI-stamped client/`source` context, not
a hook field.

**UiPath Autopilot / Delegate** honor `hooks.json` with the same envelope and
lifecycle events, but name their shell and file tools differently. Attribution
is gated on both spellings:

| Tool role | Claude Code | Autopilot / Delegate |
|-----------|-------------|----------------------|
| Shell command | `Bash` / `PowerShell` | `ExecuteBashCommand` / `ExecutePowershellCommand` |
| File read/write/edit/list | `Read` / `Write` / `Edit` / `Glob` / `Grep` | `ReadFile` / `WriteFile` / `EditFile` / `LsDirectory` |

Their `tool_input` still carries `command` / `file_path`, so the `uip`-command
and file-extension attribution and the `uipSubcommand` / `fileExtension`
derivation work unchanged once the renamed tool names are gated. No key changes.

### Added by the CLI

The CLI stamps these on every `uip.skills.*` event — the hook never sends them,
and a `source` value sent by the hook would be overridden:

| Field | Notes |
|-------|-------|
| `source` | Always `skills-plugin` |
| `CloudUserId` / `CloudTenantId` / `CloudOrganizationId` | Authenticated UiPath cloud identity |
| `environment` / `base_url` / `region` | Normalized from the CLI's **own** auth context at startup ([UiPath/cli#2806](https://github.com/UiPath/cli/pull/2806)) — always fresh, `base_url` reduced to its origin. Replaces the hook's former `environment` / `baseUrl` (schema v1), which came from a 1h-cached `uip login status` and could go stale |
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
aggregations over events sharing `session_id`:

| Metric | Query shape |
|--------|-------------|
| Tool calls per session | `count() by session_id` |
| Session duration | `session-end` − `session-start` per `session_id` (fallback `max(timestamp) − min(timestamp)` where no `session-end`, e.g. Codex) |
| Activation rate | sessions with ≥1 `tool-use` ÷ all `session-start`, by `session_id` |
| Session outcome mix | `session-end` count by `reason`; sessions containing a `completion` with `outcome=failure` |
| Time-to-first-skill | first `Skill` event − `session-start`, per session |
| Retries | repeated `uipSubcommand` flipping `failure → ok`, ordered by `timestamp` then `toolUseId` |
| Hook coverage % | sessions with ≥1 `uip.skills.*` lifecycle event ÷ agent sessions seen on the command stream (`execution_context == "agent"`), per period — report alongside any hook-based rate |

### Cross-stream correlation (`UIPATH_SESSION_ID`)

The synchronous SessionStart step (`hooks/set-session-env.sh` / `.ps1`) writes
`export UIPATH_SESSION_ID='<session_id>'` to Claude Code's `CLAUDE_ENV_FILE`,
so every `uip` command the agent runs inherits it and the CLI stamps the same
`session_id` on **native command telemetry**
([UiPath/cli#2800](https://github.com/UiPath/cli/pull/2800)). Skills events and
command events then join on `session_id` — e.g. "commands per turn" or
"sessions whose skill invocation produced no successful build/operate command".
Safety: a host-provided `UIPATH_SESSION_ID` always wins (the step is a no-op
when the variable is already set), the value is sanitized to `[A-Za-z0-9._-]`
before being written into the sourced env file, and the step is not gated on
`UIPATH_TELEMETRY_DISABLED` — writing a variable transmits nothing; the CLI's
own gate governs whether any event carrying it is sent.

This mechanism is **Claude Code-only**: Codex offers no env-file equivalent for
hooks, and its `CODEX_THREAD_ID` matches the payload `session_id` only for the
root thread (subagent threads carry their own thread id) — so native-command
correlation is currently not available under Codex. Codex **skills events**
still carry `session_id` and correlate with each other normally.

## Reliability & performance

- **Non-blocking:** the hook is registered as an async hook in `hooks.json`
  (`"async": true`) on every event except `SessionEnd`, so Claude Code runs it
  in the background and never waits for it — it never delays or fails a tool
  call. It swallows every error and always exits 0. `uip track` is itself
  never-fail (always exits 0, emits nothing when telemetry is off or on any
  error).
- **`SessionEnd` is synchronous (30s timeout):** async hooks still running at
  session teardown are killed after a short grace window — shorter than the
  hook's PowerShell + `uip track` startup — which silently drops the
  session-end event. Registering it synchronously makes session exit wait for
  the handoff (typically ~1–2s, capped at 30s), so session-duration and
  session-outcome metrics keep their `session-end` anchor.
- **Best-effort delivery:** an event is dropped on failure (no local retry
  queue). Telemetry is for aggregate trends, not exact accounting.
- **Session id export:** `set-session-env.sh` / `.ps1` is the one synchronous
  SessionStart step (it must run before the session's first shell call); it
  costs a few milliseconds — pure text processing, no network and no `uip`
  invocation.
- **Cross-platform, zero-install:** the hook ships as twin scripts —
  `send-telemetry.sh` (bash: macOS, Linux, Windows with Git Bash) and
  `send-telemetry.ps1` (PowerShell 5.1/7+: Windows without Git Bash). A
  bash/PowerShell polyglot command in `hooks.json` dispatches to the twin
  matching the executing shell; the twins are kept behaviorally identical
  (see CLAUDE.md). No `jq`, `node`, or `python` dependency. Requires the
  `uip` CLI on `PATH` (`npm install -g @uipath/cli`); when the CLI is
  absent, events are silently dropped — the hook never fails the session.
