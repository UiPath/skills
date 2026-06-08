# MCP Server Tool

Walkthrough for adding an **MCP (Model Context Protocol) server** as a resource on a low-code agent. An MCP server is a **cloud resource registered in AgentHub** and discoverable through Orchestrator's Resource Catalog — the agent *references* it (by slug + key), exactly like it references an Orchestrator process or app. The agent does **not** define the server's command/URL; that lives on the cloud server.

The agent exposes a **selected subset** of the server's tools — carefully consider which tools the agent actually needs.

## When to Use

- The agent should call tools provided by an MCP server.
- The MCP server is already registered in AgentHub (discover it below), or you register it first with `uip agenthub mcp create`.

## Server Types

MCP servers come in subtypes — `Command` (stdio, e.g. `npx`/`uvx`), `Remote` (SSE / streamable HTTP URL), `UiPath`, `Coded`, `Platform`. The subtype lives on the cloud server; the agent resource does not carry it. `uip solution resource refresh` reads it from the catalog and files the solution-level resource under the matching subtype folder.

## Discovery

### Step 1 — Scaffold solution + agent (if not already done)

Scaffold per [../../project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent).

### Step 2 — Find the MCP server

```bash
uip solution resource list --kind mcpServer --source remote --output json
```

Each row carries what the agent resource needs:

| `resource list` field | Use as |
|---|---|
| `Name` | `slug` (the server's canonical slug) |
| `Key` | `solutionProperties.resourceKey` (the cloud server UUID) |
| `Folder` | `folderPath` (the literal Orchestrator folder, e.g. `"Shared"`) — same convention as external process tools |
| `Type` | informational — the subtype refresh files the resource under |

If the server doesn't exist yet, register it: `uip agenthub mcp create command|remote|uipath|coded|platform … --output json` (see `uip agenthub mcp create --help`), then re-run the list.

### Step 3 — Fetch the server's full tool list

```bash
uip solution resource get <Key> --solution-folder <SolutionDir> --output json
```

The response is `Data.Spec` with PascalCase fields. `Data.Spec.Tools[]` is the **complete** tool list the server exposes; each entry is `{ Name, Title, Description, InputSchema, OutputSchema }` where **`InputSchema` is an escaped JSON-Schema string** (parse it into an object before writing `availableTools`).

## Tool Selection

**Carefully consider which tools the agent needs.** From `Data.Spec.Tools` (the server's complete tool list), choose the tools relevant to the user's task and write that subset into `availableTools`. When the user's intent doesn't make the subset obvious, **ask the user which tools to include**. Adding more tools than the task needs bloats the agent's tool surface.

## Agent-Level Resource Shape

**Path:** `<AGENT_NAME>/resources/<McpName>/resource.json`

Generate a fresh UUID for the top-level `id` (this is the agent-local resource id — distinct from `solutionProperties.resourceKey`, which is the cloud server's key).

```jsonc
{
  "$resourceType": "mcp",
  "id": "<uuid-v4>",                         // fresh agent-local id (NOT the cloud key)
  "name": "GitHubMcp",                       // folder name & resource name match
  "description": "GitHub MCP server",        // non-empty
  "slug": "github-mcp",                      // from resource list `Name`
  "folderPath": "Shared",                    // the server's real folder from resource list `Folder` (external resource — same as a process tool)
  "availableTools": [                         // the SELECTED subset, mapped from `resource get` Spec.Tools
    {
      "name": "create_issue",                // ← Tool.Name
      "description": "Create a GitHub issue", // ← Tool.Description
      "inputSchema": {                        // ← JSON.parse(Tool.InputSchema)
        "type": "object",
        "properties": { "repo": { "type": "string" }, "title": { "type": "string" } },
        "required": ["repo", "title"]
      },
      "outputSchema": null                    // ← Tool.OutputSchema (usually null)
    }
  ],
  "solutionProperties": { "resourceKey": "<cloud-server-key-uuid>" }  // from resource list `Key`
}
```

Required fields (validated by `uip agent validate`): `$resourceType`, `id`, `name`, `description`, `slug`, `folderPath`, `availableTools` (array; each tool needs `name`, `description`, `inputSchema`), `solutionProperties.resourceKey`. Extra fields sometimes present (`toolsConfiguration`, per-tool `argumentProperties`) are optional and ignored by validation.

## Walkthrough

### Step 4 — Write the agent-level resource.json

Use the shape above, with `availableTools` = your selected subset.

### Step 5 — Refresh, validate, and refresh solution resources

```bash
# Refresh — regenerates entry-points.json + bindings_v2.json (writes the mcpServer binding).
uip agent refresh "<AGENT_NAME>" --output json

# Validate — strict, read-only. Confirm Status: "Valid" and Resources count includes the MCP resource.
uip agent validate "<AGENT_NAME>" --output json

# Refresh solution resources — resolves the mcpServer binding against AgentHub and writes
# the solution-level reference file + debug_overwrites entry.
uip solution resource refresh --output json
```

After `uip solution resource refresh`, confirm the solution-level reference was created:

```
resources/solution_folder/<McpServerKind>/<Type>/<slug>.json   # e.g. .../McpServer/Command/github-mcp.json
```

It is a **reference** (`key` = the cloud server UUID, full `spec` incl. command/URL + tools pulled from AgentHub), placed under `solution_folder` with a `debug_overwrites.json` entry mapping it to its real cloud folder — so the binding is overridable per environment.

### Step 6 — Bundle and upload (with user consent)

```bash
uip solution bundle . -d ./dist --output json
uip solution upload ./dist/<SOLUTION_NAME>.uis --output json
```

## Gotchas

- **`availableTools` is a curated subset** — include the tools the task needs; ask the user when the relevant set is unclear.
- **`inputSchema` must be a JSON object**, not the escaped string `resource get` returns — parse `Tool.InputSchema` first.
- **`id` ≠ `resourceKey`.** `id` is a fresh agent-local UUID; `solutionProperties.resourceKey` is the cloud server's `Key` from `resource list`.
- **`folderPath` is the server's real folder** (the literal `Folder` from `resource list`, e.g. `"Shared"`) — the MCP server is an external/remote resource, so it follows the same convention as external process tools (see [../../agent-definition.md](../../agent-definition.md) § folderPath semantics). The binding is keyed by `slug` + `folderPath`, which resolves uniquely even when a slug repeats across folders (slugs are unique *within* a folder). `uip solution resource refresh` then places the reference under `solution_folder` and records the real folder in `debug_overwrites`, so the binding stays overridable. (An existing reference solution may show `"solution_folder"` here — that comes from a `resourceKey`-based resolution path; CLI `refresh` resolves by `slug`+`folderPath`, so author the real folder.)
- **`uip agent validate` is strict read-only** — it does not write; run `uip agent refresh` first to generate derived files.

## References

- [../../agent-definition.md](../../agent-definition.md) § Resources Convention
- [../../project-lifecycle.md](../../project-lifecycle.md) § Resource Discovery
- [../process/process.md](../process/process.md) — the analogous cloud-referenced tool (process) and its discovery pattern
