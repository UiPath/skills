---
name: uipath-cli
description: "UiPath `uip` CLI essentials — login, tenants, output formats, global flags, command index. Load this for auth, switching tenants, scripting output, or finding which command lives where. For domain-specific work load uipath-orchestrator / uipath-resources / uipath-solution / uipath-integration-service."
when_to_use: "User wants to authenticate (`uip login`), inspect login status, refresh tokens, switch tenants, configure CLI output (json/yaml/table/plain), filter output with JMESPath, or browse the full command catalogue. Triggers: 'log in', 'log into UiPath', 'switch tenant', 'refresh token', 'list tenants', 'set output format', 'list all uip commands', 'where is command X'. NOT for resource/Orchestrator/solution/IS work — load the focused skill."
allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath CLI Essentials

Auth, tenant selection, global output controls, and the command index for the `uip` CLI.

## Use the CLI. Don't roll your own REST.

The CLI is the single entry point for every UiPath surface that has one. Whenever you find yourself wondering *"which `uip` command does X?"* — load [uip-commands.md](references/uip-commands.md), grep for the keyword, and run `uip <path> --help`. Reach for raw REST only when this skill or a referenced skill explicitly says no command exists.

## Authentication

The CLI stores credentials at **`~/.uipath/.auth`** after login:

```
UIPATH_URL=https://alpha.uipath.com
UIPATH_ORG_NAME=my_org
UIPATH_TENANT_NAME=my_tenant
UIPATH_ACCESS_TOKEN=eyJ...
UIPATH_ORGANIZATION_ID=...
UIPATH_TENANT_ID=...
```

### Interactive login

```bash
uip login --output json
```

Custom authority (e.g. alpha):

```bash
uip login --authority "https://alpha.uipath.com/identity_" --it --output json
```

### Non-interactive (CI)

```bash
uip login --client-id "<ID>" --client-secret "<SECRET>" --tenant "<TENANT>" --output json
```

### Status, refresh, logout

```bash
uip login status --output json
uip login refresh --output json   # rotate token, emit machine-readable session payload
uip logout --output json
```

`login status` reports what's stored and rotates the access token incidentally if it's already expired. `login refresh` is the proactive variant — programmatic consumers (e.g. the Flow VSCode extension) call this to guarantee the returned token is valid for the next N minutes.

### Tenants

```bash
uip login tenant list --output json       # list available tenants
uip login tenant set <tenant-name>        # set the active tenant for subsequent commands
```

## Global flags

Every `uip` command supports:

- `--output <table|json|yaml|plain>` — output format. Always `json` when scripting.
- `--output-filter <jmespath>` — filter/reshape JSON output without piping (e.g. `--output-filter "Data[].Key"`).
- `--tenant <name>` — override the default tenant for one call (does not persist).
- `--log-level <debug|info|warn|error>` — adjust log verbosity. `debug` shows the underlying HTTP request URL and response status.
- `--log-file <path>` — write logs to file instead of stderr.

## Output envelope

All commands emit a uniform envelope:

```json
{ "Result": "Success" | "Failure" | "ValidationError",
  "Code": "<CommandSpecificCode>",
  "Data": <payload>,
  "Pagination": { "Returned": N, "Limit": N, "Offset": N, "HasMore": bool } }
```

Failures surface `Message` and `Instructions` instead of `Data`. Exit code is non-zero on failure — use `set -e` or check `$?` in scripts.

## Pagination

List commands paginate with `--limit` and `--offset`. When `Pagination.HasMore` is `true`, refetch with `--offset $((offset + limit))`.

`bucket-files list` is the one exception — it uses **continuation tokens** (`--continuation-token`, `--take-hint`) instead of offset/limit.

## Command index

[uip-commands.md](references/uip-commands.md) lists every `uip` command path, grouped by tool, with one-line summaries and links to the workflow guide that uses it.

## Cross-skill references

- Orchestrator admin → [`uipath-orchestrator`](../uipath-orchestrator/SKILL.md)
- Resources (assets, queues, buckets, libraries, webhooks, triggers) → [`uipath-resources`](../uipath-resources/SKILL.md)
- Solution lifecycle → [`uipath-solution`](../uipath-solution/SKILL.md)
- Integration Service → [`uipath-integration-service`](../uipath-integration-service/SKILL.md)
