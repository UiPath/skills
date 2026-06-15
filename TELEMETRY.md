# UiPath Skills Plugin Telemetry

Opt-in, privacy-preserving usage telemetry for the UiPath skills plugin. Off by
default. One `PostToolUse` hook (`hooks/send-telemetry.sh`) emits a single event
per relevant tool call to Azure Application Insights. No local state file, no
session daemon — session-level metrics are computed at query time from the event
stream (see [Correlation](#correlation)).

## Enabling / disabling

Telemetry is **opt-in / off by default**. It sends only when both are true:

| Env var | Effect |
|---------|--------|
| `UIPATH_TELEMETRY_DISABLED` | Reuses the `uip` CLI's variable name. Send **only** when explicitly set to `0`. Unset (default) or `1` → no send. |
| `UIPATH_TELEMETRY_CONNECTION_STRING` | App Insights connection string (`InstrumentationKey=...;IngestionEndpoint=https://<region>.in.applicationinsights.azure.com/`). Without it there is nothing to send to. `APPLICATIONINSIGHTS_CONNECTION_STRING` is read as a fallback. |

Default (var unset) is a silent no-op. To opt in, set
`UIPATH_TELEMETRY_DISABLED=0` and configure a connection string.

## What triggers an event

The hook fires on every tool call but emits only for calls attributable to this
plugin; everything else exits silently. A call qualifies when:

| Tool | Qualifies when |
|------|----------------|
| `Skill` | skill name starts with `uipath:` / `uipath-` |
| `Bash` / `PowerShell` | command invokes the `uip` CLI or `rpa-tool` |
| `Edit` / `Write` / `Read` / `Glob` / `Grep` | path targets `.flow`, `.xaml`, `.uipx`, `.bpmn`, `agent.json`, `caseplan.json`, `project.json`, `app.config.json`, `action-schema.json` |

## What is collected

Each event is an App Insights `customEvent` named `ToolUse`.

### Properties (dimensions)

| Field | Example | Notes |
|-------|---------|-------|
| `toolName` | `Skill`, `Bash` | Claude Code tool |
| `toolUseId` | `toolu_01ABC` | Unique per call — correlation key + ordering tiebreaker |
| `skillName` | `uipath:uipath-platform` | `Skill` calls only |
| `uipSubcommand` | `solution publish` | Derived first 1–2 verbs of a `uip` command — never the full command line |
| `fileExt` | `.flow` | File-tool calls only |
| `environment` | `alpha` / `staging` / `prod` / `other` / `unknown` | From `uip login status` `BaseUrl`, cached 1h |
| `baseUrl` | `https://cloud.uipath.com` | Cloud base URL only |
| `outcome` | `ok` / `failure` / `interrupted` | From `tool_response`, not output content |
| `permissionMode` | `bypassPermissions` | |
| `effortLevel` | `high` | When present in payload |
| `os` | `Linux`, `Darwin`, `MINGW64_NT-...` | |
| `pluginVersion` | `1.197.0` | `skillsVersion` from `version-manifest.json` |
| `cliVersion` | `1.197.0-beta...` | From `uip --version` |

`pluginVersion` is designed to track `cliVersion`; both are sent so drift is
visible in queries.

### Measurements (metrics)

| Field | Notes |
|-------|-------|
| `durationMs` | Tool-call wall-clock from the payload's `duration_ms` |

### Tags (envelope)

| Tag | Value |
|-----|-------|
| `ai.cloud.role` | `uipath-skills-plugin` |
| `ai.cloud.roleInstance` | resolved environment |
| `ai.session.id` | Claude Code `session_id` |
| `ai.user.id` | **SHA-256 of `cwd`** (stable anonymous workspace id) |
| `ai.application.ver` | `pluginVersion` |

## Privacy

What **never** leaves the machine:

- Raw `cwd` / project path — only a SHA-256 hash (`ai.user.id`).
- `transcript_path`.
- Full command lines — only the derived `uip` subcommand verb.
- File contents, `stdout`, `stderr` — only `outcome` and `durationMs`.
- File paths — only the extension / known filename.

All emitted fields are low-cardinality and PII-free. Nothing is sent unless
explicitly opted in.

## Missing fields

Every field above is **always emitted**, even when the source value is absent
from the payload, so query schemas stay stable:

- **Properties** fall back to an empty string `""` — never JSON `null`, because
  App Insights drops null-valued properties (which would make the field
  disappear from the event).
- The **`durationMs` measurement** falls back to JSON `null` when absent, so a
  missing value is recorded as "no data" rather than `0` (which would skew
  latency aggregations).

## Correlation

Session-level metrics need no local state file — they are query-time
aggregations over events sharing `ai.session.id`:

| Metric | Query shape |
|--------|-------------|
| Tool calls per session | `count() by session_id` |
| Session duration | `max(timestamp) - min(timestamp) by session_id` |
| Time-to-first-skill | first `Skill` event − first event, per session |
| Retries | repeated `uipSubcommand` flipping `failure → ok`, ordered by `timestamp` then `toolUseId` |

## Reliability & performance

- **Non-blocking:** the hook POSTs in a detached subshell with a 4s cap and
  always exits 0 — it never delays or fails a tool call.
- **Best-effort delivery:** an event is dropped on network failure (no local
  retry queue). Telemetry is for aggregate trends, not exact accounting.
- **Environment cost:** `uip login status` (~0.5s) runs at most once per hour;
  the result is cached in a per-user, `chmod 700` directory and parsed as data,
  never sourced.
- **Cross-platform:** pure POSIX `bash` + `grep`/`sed`/`awk`, no `jq`
  dependency (macOS, Linux, Windows Git Bash).
