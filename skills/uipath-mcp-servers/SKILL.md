---
name: uipath-mcp-servers
description: "UiPath AgentHub MCP server registration + tool authoring via `uip agenthub mcp` (six server types: uipath / coded / command / remote / platform / swagger) and `uip agenthub mcp-tools` (create-is-activity / create-resource / create-raw on uipath-type servers). Wraps Integration Service activities (Jira, Slack, Outlook, Salesforce, Workday, ServiceNow, etc.) as MCP tools. For Python MCP servers / coded-agent integration→uipath-agents. For raw IS CLI→uipath-platform."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath AgentHub MCP Servers

Register UiPath AgentHub MCP servers via `uip agenthub mcp` (six server types). Author tools on `uipath`-type servers via `uip agenthub mcp-tools` (three tool kinds: `is-activity`, `resource`, `raw`). This skill stays generic — IS-activity authoring (the load-bearing path) has its own reference, [references/is-activity-workflow.md](references/is-activity-workflow.md). Read that file end-to-end whenever the task involves wrapping an Integration Service activity.

## When to Use This Skill

- User asks to create / register an MCP server (any of: uipath, coded, command, remote, swagger, platform).
- User asks to register a remote / swagger / coded / command / platform MCP server pointing at an external URL, OpenAPI spec, published coded-agent process in Orchestrator, subprocess command, or first-party UiPath service.
- User asks to update an MCP server (change a remote URL, swap a swagger spec, repoint a coded process) or `refresh-tools` on an existing server.
- User asks to add an Integration Service activity (Jira, Slack, Outlook, Gmail, Salesforce, Workday, ServiceNow, etc.) as a tool on an AgentHub MCP server → load `references/is-activity-workflow.md` before authoring.
- User asks to add an Orchestrator resource (process, agent, agentic-process, api-workflow) as a tool on an MCP server.
- User asks to add a raw / free-form MCP tool.
- User asks to manage tools on an existing AgentHub MCP server (slugs like `inbox-mcp`, `support-mcp`, `team-helper`) — list, get, enable, disable, delete.
- Skip when request is about Python MCP server implementation (FastMCP / `@uipath/mcp`)→`uipath-agents`. Skip for raw IS CLI usage outside MCP tooling→`uipath-platform`.

## Critical Rules

These rules apply to every server type and every tool kind. IS-activity adds five more rules in [references/is-activity-workflow.md](references/is-activity-workflow.md) — read that file when authoring is-activity tools.

1. **MCP server slug + external SaaS = AgentHub IS-Activity path.** Slugs like `inbox-mcp` / `support-mcp` / `team-helper` name AgentHub servers, not local repos. `uipath-mcp-python` (`@uipath/mcp`) is a server-implementation SDK — different task.

2. **Slug regex.** Backend enforces `^[a-z0-9-]+$`, length 3-50. Lowercase, digits, hyphens only — no underscores, dots, or uppercase. CLI validates client-side before POST.

3. **Folder context is required on every AgentHub call.** Pass `--folder-path <name>` OR `--folder-key <guid>`, never both. `--folder-path` resolves via Orchestrator SDK. Personal workspace folders (`"<user>@<tenant>'s workspace"`) do NOT resolve by name — use `--folder-key <guid>`. Discover GUIDs via `uip or folders list --output json`.

4. **Verify before claiming done.** After `create` / `update` / `delete` / `refresh-tools`, re-list (`mcp list`, `mcp-tools list --mcp <slug>`) or `mcp get <slug>` and confirm the expected state. `refresh-tools` on `coded` / `command` returns HTTP 202 with a runtime id (async) — poll, do not assume.

5. **`mcp delete` looks up by slug, not GUID.** Pass the slug; passing a GUID returns 404.

## Server Types

`uip agenthub mcp create <type>` accepts six types. All share `--name <display>`, `--slug <kebab>`, `--description`, `--version`, `--file`/`--body`/`--print-schema`, `--dry-run`, `--folder-path`/`--folder-key`, `--tenant`, `--login-validity`. The differentiating flag picks the integration shape:

| Type | Differentiating flag | When to use | Tool surface |
|------|---------------------|-------------|--------------|
| `uipath`   | _(none)_              | AgentHub-hosted server you'll fill with `mcp-tools create-*` (is-activity / resource / raw). | Authored via `uip agenthub mcp-tools create-*`. |
| `coded`    | `--process-key <key>` | Wrap an existing coded-agent process (published to Orchestrator) as an MCP server. | Tools discovered via `refresh-tools` (async 202). |
| `command`  | `--command <cmd>`     | Spawn a local subprocess as an MCP server. | Tools discovered via `refresh-tools` (async 202). |
| `remote`   | `--uri <url>` (+ `--file`/`--body` for headers/auth) | Point at an existing HTTP MCP server. Bearer/header auth values can be Orchestrator asset references; `AssetReferenceSubstitutor` resolves them at runtime through the caller's token + folder context. Do NOT introduce a separate AgentHub credential store. | Tools discovered via `refresh-tools` (sync 200). |
| `platform` | `--service <name>`    | Bind to a first-party UiPath service. | Server-defined. |
| `swagger`  | `--spec-url <url>`    | Register an OpenAPI/Swagger spec as MCP tools. Same asset substitution as `remote`. | Tools discovered from the spec via `refresh-tools` (sync 200). |

Headers / auth on `remote` and `swagger` are payload fields, not scalar flags. Read the shape from `uip agenthub mcp create remote --print-schema --output json` (or `uip agenthub mcp template remote --output json`), then submit via `--file <payload.json>` or `--body '<json>'`. Express asset-backed values using the substitution form the schema documents — do NOT invent a syntax.

`mcp update <slug>`: dispatches by the existing server type (e.g. change a `remote` `--uri`, swap a `swagger` `--spec-url`, repoint a `coded` `--process-key`). Flag shape mirrors `create <type>`. Verify via `uip agenthub mcp get <slug> --output json` before claiming done.

`mcp refresh-tools <slug>`: re-scan tools. `coded` / `command` return HTTP 202 with a runtime id (async — surface the id so the user can poll); `remote` / `swagger` return 200 after a synchronous fetch+upsert. Verify via `uip agenthub mcp-tools list --mcp <slug> --output json` after the call (sync) or after polling completes (async).

`mcp template <type>`: emit a `--file` skeleton. Types include `uipath`, `coded`, `command`, `remote`, `platform`, `swagger`, plus `process-assistant` and `selfhosted` — note that `process-assistant` and `selfhosted` have templates but NO `mcp create` subcommand (backend enum only; skip).

`mcp get <slug>` / `mcp list` / `mcp delete <slug>`: single-shot CRUD. `delete` looks up by slug, not GUID.

## Tool Kinds

Three `create-*` verbs author tools on `uipath`-type servers. All share an identical flag set (`--mcp`, `--name`, `--description`, `--target-name`/`--target-identifier`, `--category`, `--input-schema`, `--output-schema`, `--metadata`, `--folder-*`, `--dry-run`, `--continue-on-error`/`--fail-fast`, `--file`/`--body`). They differ in (a) metadata shape, (b) discovery path, (c) server-side validation strictness.

| Kind | Discovery | Validation | When to use |
|------|-----------|------------|-------------|
| `is-activity` | `mcp-tools candidates --category is-activity` + `is resources describe` | Connector schema | Wrap an Integration Service connector activity (Jira, Slack, Outlook, Salesforce, Workday, ServiceNow, etc.) as an MCP tool. **Read [references/is-activity-workflow.md](references/is-activity-workflow.md) end-to-end before authoring** — five extra Critical Rules, a Pre-flight, and an `ActivityMetadata` schema apply. |
| `resource`    | `mcp-tools candidates --category <kind>` (kind ∈ `automation` / `agent` / `agentic-process` / `api-workflow`) | Resource schema | Bind an Orchestrator resource (process, agent, agentic-process, api-workflow) to an MCP tool. Pass `--target-identifier <resource-id>`, walk the same folder-context + dry-run + verify pattern as is-activity. Metadata schema is resource-kind-specific — emit `uip agenthub mcp-tools template resource --output json` to read the skeleton. |
| `raw`         | None | None | Free-form JSON tool — caller owns correctness end-to-end. No discovery, no schema validation, no reference-value labeling. Use the `uip agenthub mcp-tools template raw --output json` skeleton; supply the full payload (name, description, input/output schemas, custom metadata). |

`mcp-tools template <kind>` accepts `is-activity` / `resource` / `raw`. The `--category` enum on `candidates` is `automation | agent | agentic-process | api-workflow | is-activity` — the first four are resource kinds; `is-activity` is the IS path.

Other `mcp-tools` verbs:
- `mcp-tools get <id> --mcp <slug>` — fetch one tool.
- `mcp-tools list --mcp <slug>` — list tools on a server (use for the Rule 5 verify step).
- `mcp-tools enable <id>` / `disable <id>` — toggle tool visibility on the server without deleting.
- `mcp-tools delete <id> --mcp <slug>` — delete a tool.
- `mcp-tools update <tool-id>` — update an existing tool. Pass `--metadata` / `--input-schema` / `--output-schema` as scalars (not `--file`). Pass `--output-schema "{}"` when the underlying activity has no responseFields.

## Troubleshooting

Generic (any tool kind / server type):

- **HTTP 400 with no detail** — re-run with `--dry-run` to inspect the resolved body. The CLI surfaces ASP.NET ProblemDetails as an `Errors` field listing per-field validation failures.
- **`InvalidFolderKey: "--folder-key requires a GUID; use --folder-path for folder names"`** — switch to `--folder-path <name>`.
- **`No folder named '<personal workspace name>' was found. Did you mean: Shared?`** — personal workspaces are unresolvable by name; pass `--folder-key <guid>` (Critical Rule 3).
- **`ConflictingInput: "Pass either --folder-path or --folder-key, not both."`** — drop one.
- **Slug rejected with validation error** — backend enforces `^[a-z0-9-]+$`, length 3-50 (Critical Rule 2). Pick a new slug.
- **`mcp delete <guid>` returns 404** — `mcp delete` looks up by slug, not GUID (Critical Rule 5).
- **`refresh-tools` returns 202 with a runtime id** — coded / command refreshes are async. Surface the runtime id so the user can poll; do not claim refreshed until a follow-up `mcp-tools list --mcp <slug>` confirms the new set.

IS-activity-specific troubleshooting (cross-folder connection, missing path tokens, missing `designTimeLookups`, curated operation not found, etc.) lives in [references/is-activity-workflow.md](references/is-activity-workflow.md) § IS-Activity Troubleshooting.

## References

- [references/is-activity-workflow.md](references/is-activity-workflow.md) — **load before any IS-activity authoring task.** IS-Activity-Specific Critical Rules, Pre-flight, full Workflow, `ActivityMetadata` schema, IS-Activity Troubleshooting. Also points at the two load-bearing IS reference sections in `uipath-platform`.
