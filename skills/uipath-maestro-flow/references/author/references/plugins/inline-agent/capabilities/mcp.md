# MCP Server Tool

Exposes an **MCP (Model Context Protocol) server**'s tools to an inline agent. An MCP server is a **cloud resource registered in AgentHub**, discoverable through Orchestrator's Resource Catalog — the flow *references* it (slug + folder + key); the server's command/URL lives on the cloud server, never in the flow. The MCP server is a **node in the `.flow` file** wired to the agent node's `tool` handle; the full config lives in the node's `inputs`. No `resource.json` is authored — the sidecar artifact derives from the node ([impl.md § Derived Sidecar](../impl.md#10-derived-sidecar--reference)).

The agent gets a **selected subset** of the server's tools (`inputs.selectedTools`) — carefully consider which tools the agent actually needs.

> **Toolchain gap (verified 2026-08) — flow-only MCP authoring is blocked.** `uip maestro flow registry search`/`get` mint **no `…tool.mcp.*` manifests**, even on tenants with MCP servers registered in AgentHub — MCP node manifests are minted by the canvas studio layer, not by the server registry the CLI reads. Without a manifest there is no verbatim `definitions[]` entry, so the definitions-or-nothing law ([impl.md § 3](../impl.md#3-manifest-and-definitions-contract)) cannot be satisfied: validate fails, and a node forced past it would silently vanish from the derived agent and the package. When asked for an inline MCP tool: run § Walkthrough step 0; if `registry search` returns no `tool.mcp.*` entry, **STOP and surface the gap** — point the user to attaching the MCP server in a canvas host (Studio Web / VS Code), which embeds the node and its definition into the `.flow`. Do NOT hand-fabricate a `definitions[]` entry. Everything below is the authoring contract — it applies in full to **editing a canvas-authored flow** (whose `definitions[]` already carries the manifest) and to greenfield authoring once the registry surfaces MCP manifests.

## When to Use

- The agent should call tools provided by an MCP server registered in AgentHub.
- Server not registered yet: `uip agenthub mcp create command|remote|uipath|coded|platform … --output json` (needs folder context — `--folder-path <name>`; see `--help`), then rediscover.

## Node Type

Dynamic — one type minted per registered MCP server:

```text
uipath.agent.resource.tool.mcp.<server-name-slug>.<server-key>
```

`<server-name-slug>` / `<server-key>` = sanitized server name and key (UUID). `typeVersion` `"1.0.0"`. Manifest: `model: {"source": true}` (mint `inputs.source` — validator-required, MST-9265); required input `name`; `inputDefaults` carry the server identity (`name`, `referenceKey`, `folderPath`, `folderKey`, `mcpType`, `serverUrl` = the slug, `selectedTools`/`toolCatalog`, `discoveryMode`) — copy-then-curate. No `model.bindings` ⇒ **no top-level `bindings[]` rows** (same as context and escalation).

```bash
# Gap gate + type discovery — empty Data[] means the toolchain gap above
uip maestro flow registry search mcp --output json

# Manifest → definitions[] verbatim (impl.md § 3)
uip maestro flow registry get "uipath.agent.resource.tool.mcp.<name>.<key>" --output json
```

## Discovery — the MCP Server

### 1. Find the server

```bash
uip solution resources list --kind mcpServer --source remote --output json
```

| `resources list` field | Use as |
|---|---|
| `Name` | the server's canonical **slug** → node `slug` + `serverUrl` (Resource Catalog lists MCP servers by slug) |
| `Key` | node `referenceKey` (the cloud server UUID) |
| `Folder` | node `folderPath` — **literal value** (e.g. `"Shared"`) |
| `FolderKey` | node `folderKey` |
| `Type` | node `mcpType`, lowercased first letter (`Command` → `command`) — cross-check against § Node Shape subtype list |

### 2. Fetch the server's full tool list

```bash
uip solution resources get <KEY> --output json
```

Run from the solution directory (or `--solution-folder <path>`). `Data.Spec` carries `Slug` (canonical — cross-check), `Name`, `Description`, and `Tools[]`: the **complete** tool list, entries `{Name, Title, Description, InputSchema, OutputSchema}` where **`InputSchema` is an escaped JSON-Schema string** — parse it into an object before writing `selectedTools`.

## Tool Selection

From `Spec.Tools` choose the tools relevant to the user's task → `selectedTools`. When the user's intent doesn't make the subset obvious, **ask the user which tools to include**. More tools than the task needs bloats the agent's tool surface. The full discovered list goes in `toolCatalog`.

## MCP Node Shape

Node `inputs` (authoring surface — everything else derives):

| Field | Required | Notes |
|---|---|---|
| `source` | Yes | Lowercase UUIDv4 **you mint** ([planning.md § Identity](../planning.md#identity--mint-the-uuids-yourself)). Validator-enforced (MST-9265). Becomes the derived `resources/<source>/resource.json` id. |
| `name` | Yes | Manifest-required. **Name authority: `inputs.name` only** — projection ignores `display.label`. Name it after the server itself, not the task or tool subset. |
| `description` | No | What the server provides — the LLM reads it. |
| `slug` | Yes | The server's canonical slug — the runtime resolves the server by `folderPath`/`slug`. |
| `serverUrl` | Yes | **Not a URL** — carries the same slug (it is the manifest-default carrier; projection reads `slug`, falls back to `serverUrl`). Author both, same value. |
| `folderPath` | Yes | Literal Orchestrator folder from discovery (e.g. `"Shared"`). Slugs are unique only *within* a folder — never invent it. |
| `folderKey` | No | Folder UUID from discovery (in `inputDefaults`). |
| `referenceKey` | Yes | The cloud server `Key` (UUID) → derived `solutionProperties.resourceKey`. **Unlike process tools, MCP DOES author `referenceKey`** — process tools carry their key in the node-type suffix; MCP resolves by slug+folder and the key rides along for binding. |
| `mcpType` | No | Server subtype: `command` \| `remote` \| `coded` \| `uiPath` \| `platform` (`uiPath` really is camelCase — canonical platform casing). Read by the canvas binding layer; not projected into the resource. |
| `selectedTools` | Yes | The curated subset — § Tool Entries. |
| `toolCatalog` | No | Full discovered tool list (UI selection source, not projected). Hydrated legacy nodes mirror `selectedTools` here; keeping it current is optional. |
| `discoveryMode` | No | `{"type": "cached"}` (default — the `selectedTools` snapshot is the agent's tool surface) or `{"type": "dynamic", "allowAll": <bool>}` (tools discovered at runtime; `allowAll` defaults `true` unless explicitly `false`). Any other value collapses to `cached` at projection. |

### Tool Entries

Each `selectedTools[]` entry, mapped from `Spec.Tools`:

```jsonc
{
  "name": "create_issue",                    // ← Tool.Name — REQUIRED non-empty; nameless entries are silently dropped at projection
  "description": "Create a GitHub issue",    // ← Tool.Description
  "inputSchema": { "type": "object", "properties": { "repo": { "type": "string" }, "title": { "type": "string" } }, "required": ["repo", "title"] },
                                             // ← JSON.parse(Tool.InputSchema) — MUST be an object; a string or invalid schema is replaced with {"type":"object","properties":{}} at projection, silently wiping every property
  "outputSchema": null,                      // ← Tool.OutputSchema (usually null)
  "argumentProperties": {}                   // default {}
}
```

### Example

```json
{
  "id": "githubMcp",
  "type": "uipath.agent.resource.tool.mcp.github-mcp.3f2e1d0c-5b4a-4869-9788-a1b2c3d4e5f6",
  "typeVersion": "1.0.0",
  "display": { "label": "GitHub MCP", "shape": "circle" },
  "inputs": {
    "source": "c7d3e9f1-2a4b-4c6d-8e0f-1a3b5c7d9e2f",
    "name": "github-mcp",
    "description": "GitHub MCP server — issue and repository tools",
    "slug": "github-mcp",
    "serverUrl": "github-mcp",
    "folderPath": "Shared",
    "folderKey": "b3c8e1f6-4d2a-4e9b-8a7c-1d5f0e9b2a64",
    "referenceKey": "3f2e1d0c-5b4a-4869-9788-a1b2c3d4e5f6",
    "mcpType": "remote",
    "selectedTools": [
      { "name": "create_issue", "description": "Create a GitHub issue", "inputSchema": { "type": "object", "properties": { "repo": { "type": "string" }, "title": { "type": "string" } }, "required": ["repo", "title"] }, "outputSchema": null, "argumentProperties": {} }
    ],
    "toolCatalog": [],
    "discoveryMode": { "type": "cached" }
  }
}
```

Wire exactly ONE artifact edge — agent `tool` handle → MCP node `input` (max 1 connection):

```json
{ "id": "e_agent_mcp", "sourceNodeId": "devAgent", "sourcePort": "tool", "targetNodeId": "githubMcp", "targetPort": "input" }
```

**There is no `mcp` source handle.** The autonomous manifest attaches MCP servers via its `tool` handle (that handle's add-node panel IS the canvas MCP picker); an edge with `sourcePort: "mcp"` fails validate as an undeclared handle. The storage projection tolerates a legacy `mcp` sourceHandle for cluster membership — no current manifest declares one; always wire `tool`.

No sequence edges to/from an MCP node — it is not on the trigger→end path.

## Derived Fields — Never Author

Sidecar `resource.json` fields; in node `inputs` they mark a ported resource.json:

- `$resourceType: "mcp"`, `availableTools`, `toolsConfiguration`, `solutionProperties`

Projection (`.flow` → derived resource): id ← `source`; name ← `inputs.name`; slug ← `slug` (fallback `serverUrl`); `solutionProperties.resourceKey` ← `referenceKey`; `availableTools` ← `selectedTools` normalized (nameless entries dropped; JSON-string schemas parsed; invalid `inputSchema` → `{"type":"object","properties":{}}`; missing `outputSchema` → `null`); `toolsConfiguration.discoveryMode` ← `discoveryMode` normalized (absent → `{"type":"cached"}`).

## Walkthrough

```bash
# 0. Gap gate — MCP node types minted? Empty Data[] ⇒ STOP, surface the toolchain gap (top of doc).
uip maestro flow registry search mcp --output json

# 1. Manifest — definitions entry (+ inputDefaults identity skeleton)
uip maestro flow registry get "uipath.agent.resource.tool.mcp.<name>.<key>" --output json

# 2. Server identity (slug, key, folder)
uip solution resources list --kind mcpServer --source remote --output json

# 3. Full tool list + canonical Slug (Tools[].InputSchema are escaped JSON strings — parse)
uip solution resources get <KEY> --output json
```

Then edit the `.flow` directly (`Edit` / `Write`):

4. Add the MCP node per § MCP Node Shape (mint `inputs.source`; curate `selectedTools`; `slug` = `serverUrl` = the canonical slug; literal `folderPath`; `referenceKey` = server key).
5. Copy the manifest **verbatim** into `definitions[]`.
6. Wire the artifact edge: agent `tool` → MCP node `input`.
7. Update the agent's system prompt: name the server (by `inputs.name`) and the selected tools, state when to use them ([prompting guide](../prompting/autonomous-agent-prompting-guide.md)).

```bash
# 8. Validate
uip maestro flow format "<FILE>.flow"
uip maestro flow validate "<FILE>.flow" --output json
```

## Gotchas

1. **The registry gap gates everything** (top of doc): no `tool.mcp.*` manifest ⇒ no valid `definitions[]` entry ⇒ surface, don't hand-fabricate. Editing a canvas-authored flow is unaffected — its definition is already embedded.
2. **`serverUrl` is not a URL.** It carries the server slug (manifest-default carrier). Author `slug` and `serverUrl` with the same value.
3. **Parse `InputSchema` strings.** `Spec.Tools[].InputSchema` is an escaped JSON string; written unparsed, projection replaces it with an empty object schema — every property silently wiped.
4. **Nameless tool entries are silently dropped** at projection — `name` is the tool's identity; copy `Tool.Name` verbatim.
5. **`referenceKey` IS authored here** — the opposite of process-family tools ([process.md](process.md) — release key in the type suffix, never `inputs.referenceKey`). Don't carry that habit over.
6. **`folderPath` is the literal folder from discovery.** Slug resolution is per-folder (`folderPath`/`slug`); a wrong folder resolves to nothing or the wrong server.
7. **Wire `tool`, not `mcp`.** No autonomous manifest declares an `mcp` handle; validate rejects the edge.
8. **`selectedTools` is the runtime surface only in `cached` mode.** `{"type": "dynamic", "allowAll": true}` exposes whatever the server serves at run time — the snapshot is ignored. Prefer `cached` unless the user asks for dynamic discovery.
9. **A tool the prompt never mentions rarely fires.** Name the server and its tools in the system prompt with usage conditions and call caps.
10. **Sidecar-era fields are contamination**: `$resourceType`, `availableTools`, `toolsConfiguration`, `solutionProperties` in node `inputs` mark a ported resource.json — the flow form uses `selectedTools`/`discoveryMode`/`referenceKey` (§ MCP Node Shape).

## References

- [impl.md § Resource Nodes](../impl.md#7-resource-nodes) — universal recipe + kind matrix
- [impl.md § Worked Example](../impl.md#8-worked-example--trigger--agent--end--rpa-tool--context) — full flow skeleton to extend
- [critical-rules.md](../critical-rules.md) — mandatory constraints
- [prompting guide](../prompting/autonomous-agent-prompting-guide.md) — tool usage conditions + call caps
- [process.md](process.md) — the contrasting cloud-referenced tool pattern (key in type suffix, `bindings[]` rows)
