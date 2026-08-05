# Integration Service Tool Capability

Tools that call an Integration Service connector activity (e.g., Slack Send Message, Web Search, Jira Create Issue) — third-party SaaS / APIs exposed via pre-built connectors and authenticated connections. Each tool is a **node in the `.flow` file** wired to the agent node's `tool` handle. Connector config lives in the tool node's `inputs.detail` — **CLI-populated via `uip maestro flow node configure`, never hand-written**. No `resource.json` is authored — the sidecar artifact derives from the node ([impl.md § Derived Sidecar](../impl.md#10-derived-sidecar--reference)).

For Orchestrator process tools (RPA / agent / API / agentic process), see [process.md](process.md).

## When to Use

- Agent needs to call a third-party SaaS / API exposed via UiPath Integration Service (Slack, Salesforce, Jira, ServiceNow, Web Search, etc.)
- A connection (authenticated link to the target system) already exists or can be created in IS

## Key Differences from Process-Family Tools

- Bound to a **connection** resource, not a process — `bindings[]` rows carry `resource: "connection"`, keyed by connection id (no `folderPath` propagation)
- Config is one `inputs.detail` blob (endpoint, method, connection, parameter values), not per-argument ValueSourceField entries
- **`inputs.detail` is CLI-owned.** `uip maestro flow node configure` builds it, including the `essentialConfiguration` block hand-authoring misses — a hand-written `detail` passes validate but fails at runtime. Same carve-out as flow-level connector nodes ([editing-operations.md](../../../editing-operations.md))
- Derived resource `type` is `"integration"`, derived `location` is `"external"` (only integration and ixp tools derive `"external"`)
- **Validate checks only `inputs.source`** on connector tool nodes. Missing `bindings[]` rows, missing `detail`, missing `name` all pass validate silently (unlike process-family tools, where a missing binding row is a validate error) — the configure step and your own review own those

## Node Type

`uipath.agent.resource.tool.connector.<connector-key>.<activity-slug>` (e.g. `uipath.agent.resource.tool.connector.uipath-uipath-airdk.web-search`), version `1.0.0`. The registry mints one node type per connector activity — **never construct the type string by hand; discover it** (§ Discovery). Manifest `inputDefinition`/`inputDefaults` are empty: all config flows through `detail`.

## Discovery

### 1. Find the connector

```bash
uip is connectors list --output json
# Or filter: uip is connectors list --filter "slack" --output json
```

Note the connector `Key` (e.g., `uipath-salesforce-slack`).

### 2. Find a connection

```bash
uip is connections list "<CONNECTOR_KEY>" --all-folders --output json
```

> **Always pass `--all-folders`** — connections often live in a specific Orchestrator folder and are invisible to the default folder-scoped list.

Present connections to the user. Recommend the default enabled one but let the user confirm. Note the connection `Id` and `FolderKey`. If none exists, prompt the user to create one via `uip is connections create "<CONNECTOR_KEY>"`.

This command also populates the local IS cache used when solution-level connection resources are generated — run it even when the connection id is already known.

### 3. Find the activity and its endpoint

```bash
uip is activities list "<CONNECTOR_KEY>" --output json
```

Note the chosen activity's `DisplayName`, `Description`, `ObjectName`. Then:

```bash
uip is resources describe "<CONNECTOR_KEY>" "<OBJECT_NAME>" \
  --connection-id "<CONNECTION_ID>" --operation Create --output json
```

Gives `Operation.Path` (→ configure `endpoint`), `Operation.Method` (→ `method`), `Operation.Description` (→ node `inputs.description`), and `RequestFields` (parameter names + descriptions — configure seeds these automatically; you need them only to override specific values).

### 4. Find the node type and manifest

```bash
uip maestro flow registry search "<ACTIVITY_NAME>" --output json
```

Pick the `Data[]` entry whose `NodeType` starts with `uipath.agent.resource.tool.connector.<CONNECTOR_KEY>.` and check `AvailableOnTenant: true` (the same search also returns `uipath.connector.*` — that is the flow-level activity node, NOT an agent tool). Then:

```bash
uip maestro flow registry get <NODE_TYPE> --output json
```

Whole manifest → `definitions[]` verbatim ([impl.md § 3](../impl.md#3-manifest-and-definitions-contract)). `model.bindings` (resource `connection`, two `values[]` rows) is the template `node configure` instantiates — informational here, nothing to copy by hand.

## Tool Node Shape

Node `inputs` you author (everything else lands via `node configure` or derives):

| Field | Required | Notes |
|---|---|---|
| `source` | Yes | Lowercase UUIDv4 **you mint** ([planning.md § Identity](../planning.md#identity--mint-the-uuids-yourself)). Validator-enforced (MST-9265). Becomes the derived `resources/<source>/resource.json` id. |
| `name` | Yes | Tool name the LLM selects by. Name authority: `inputs.name`, fallback `display.label`. |
| `description` | Yes | Full activity `Description` from discovery — shown to the LLM for tool selection. Do not truncate. |
| `detail` | Yes — via CLI | **Do not hand-write.** Absent until `node configure` populates it (§ Configure). |

No instance `outputs`, no instance `model` block, no `inputSchema`/`outputSchema`/`properties` (unlike process tools — connector schemas derive from `detail`).

Example (pre-configure):

```json
{
  "id": "webSearch",
  "type": "uipath.agent.resource.tool.connector.uipath-uipath-airdk.web-search",
  "typeVersion": "1.0.0",
  "display": { "label": "Web Search" },
  "inputs": {
    "source": "7f3c2a10-9e4b-4c8d-a1f2-5b6d7e8f9a0b",
    "name": "WebSearch",
    "description": "Performs a web search operation, returning relevant and current information from the internet."
  }
}
```

Wire exactly ONE artifact edge — agent `tool` handle → tool node `input`:

```json
{ "id": "e_agent_ws", "sourceNodeId": "researcher", "sourcePort": "tool", "targetNodeId": "webSearch", "targetPort": "input" }
```

No sequence edges to/from a tool node.

## Configure — Populate `inputs.detail` (CLI Carve-Out)

After the node, its `definitions[]` entry, and the edge exist:

```bash
uip maestro flow node configure "<FILE>.flow" <NODE_ID> \
  --detail '{"connectionId":"<CONNECTION_ID>","folderKey":"<FOLDER_KEY>","method":"<METHOD>","endpoint":"<PATH>"}' \
  --output json
```

`--detail` keys:

| Key | Required | Value |
|---|---|---|
| `connectionId` | Yes | Connection `Id` from discovery step 2 |
| `folderKey` | Yes | Connection `FolderKey` from discovery step 2 |
| `method` | Yes | `Operation.Method` from `resources describe` |
| `endpoint` | Yes | `Operation.Path` from `resources describe` |
| `objectName` | Generic activities only | Object to operate on (manifest `activityType: "Generic"`, e.g. `*.insert-record`) |
| `bodyParameters` / `queryParameters` / `pathParameters` | No | Per-field value overrides (§ Parameter Values) |

Success: `{"Data": {"NodeId": "...", "BindingsCreated": 2, "DetailPopulated": true}}`. One command writes four things:

1. **`inputs.detail`** — `connector`, `connectionId`, `connectionResourceId`, `connectionFolderKey`, `method`, `endpoint`, `uiPathActivityTypeId`, `configuration` (`=jsonString:` wrapper with the `essentialConfiguration` block), and per-field `bodyParameters` seeded from the activity metadata: required/optional fields get LLM-fillable `{{prompt: "<field description>"}}` chips, single-value enums get their static default
2. **Top-level `bindings[]`** — the two rows (§ Bindings)
3. **`bindings_v2.json`** at the flow project root — connection declaration `uip solution resources refresh` reads
4. **`resources/solution_folder/connection/<CONNECTOR_KEY>/`** — the solution-level connection resource (`authenticationType: "AuthenticateAfterDeployment"` — credentials supplied post-deploy)

Re-run configure with a different `connectionId` to re-point the tool — never edit `detail` fields by hand.

### Parameter Values

Default (no buckets passed): every request field stays LLM-fillable — correct for most agent tools. Override per field via the bucket matching its location (`bodyParameters` for body fields, `queryParameters`/`pathParameters` for query/path):

| Bucket value | Meaning | Derived parameter |
|---|---|---|
| omitted / `{{prompt}}` chip | LLM fills at run time | `fieldVariant: "dynamic"` |
| Literal (e.g. `"GoogleCustomSearch"`) | Fixed value | `fieldVariant: "static"` |
| Single `$vars` ref — `"=js:$vars.<nodeId>.output.<field>"` | Bound to flow data | `fieldVariant: "argument"`; scanned into derived `agentInputVariables` like a prompt token ([impl.md § 4](../impl.md#4-wire-flow-data-into-prompts)) |
| Composite expression (e.g. `"=js:'PREFIX-' + $vars.start.output.id"`) | Computed flow-side | Promoted to a synthetic agent input automatically |

Cross-node refs REQUIRE the `$vars.` prefix inside the `=js:` expression — a bare `=js:someNode.output.x` resolves to `undefined` at runtime.

## Bindings

Connector tools require two top-level `bindings[]` rows (root of the `.flow`, sibling of `nodes[]`) — **created by `node configure`**, shown for review:

```json
"bindings": [
  { "id": "b1", "name": "<CONNECTOR_KEY> connection", "type": "string", "resource": "connection", "resourceKey": "<CONNECTION_ID>", "propertyAttribute": "ConnectionId", "default": "<CONNECTION_ID>" },
  { "id": "b2", "name": "FolderKey", "type": "string", "resource": "connection", "resourceKey": "<CONNECTION_ID>", "propertyAttribute": "FolderKey", "default": "<FOLDER_KEY>" }
]
```

`resourceKey` = connection id on both rows (scopes rows per connection — two connectors keep distinct `FolderKey` rows). All tools sharing a connection share its rows. **Validate does NOT enforce these** (unlike process-family rows) — after configure, verify both rows exist before calling the flow done.

## Derived Fields — Never Author

Projection injects these into the derived `resource.json`; they are not node inputs:

- `type: "integration"`, `location: "external"`
- `properties.*` — `toolPath`/`objectName`/`method` (from `detail`), `toolDisplayName`, `connection` block (from `detail.connectionId` + the manifest's `connectorKey`), `parameters[]`, `bodyStructure`
- `inputSchema` / `outputSchema` (from the activity's field metadata)
- `guardrail.policies` (filtered from the **agent node's** `inputs.guardrails`), `iconUrl` (manifest icon), `$resourceType`, `settings`

The `.flow` node also survives flag-off canvas saves intact — the flag-off strip preserves `source` and `detail`.

## Walkthrough

```bash
# 1. Connector key
uip is connectors list --filter "<SEARCH>" --output json

# 2. Connection — note Id + FolderKey (user confirms the pick)
uip is connections list "<CONNECTOR_KEY>" --all-folders --output json

# 3. Activity + endpoint/method — note ObjectName, Operation.Path, Operation.Method, Description
uip is activities list "<CONNECTOR_KEY>" --output json
uip is resources describe "<CONNECTOR_KEY>" "<OBJECT_NAME>" --connection-id "<CONNECTION_ID>" --operation Create --output json

# 4. Node type + manifest
uip maestro flow registry search "<ACTIVITY_NAME>" --output json
uip maestro flow registry get <NODE_TYPE> --output json
```

Then edit the `.flow` directly (`Edit` / `Write`):

5. Add the tool node per § Tool Node Shape (mint `inputs.source`; `typeVersion` = manifest `version`; NO `detail` yet).
6. Copy the manifest **verbatim** into `definitions[]`.
7. Wire the artifact edge: agent `tool` → tool `input`.
8. Update the agent's system prompt: name the tool, give per-tool call/stop criteria ([prompting guide](../prompting/autonomous-agent-prompting-guide.md)).

```bash
# 9. Configure — populates detail + bindings + solution connection files
uip maestro flow node configure "<FILE>.flow" <NODE_ID> \
  --detail '{"connectionId":"<CONNECTION_ID>","folderKey":"<FOLDER_KEY>","method":"POST","endpoint":"/v2/webSearch"}' --output json

# 10. Validate
uip maestro flow format "<FILE>.flow"
uip maestro flow validate "<FILE>.flow" --output json
```

## Gotchas

1. **Definitions-or-nothing law** ([impl.md § 3](../impl.md#3-manifest-and-definitions-contract)): a tool node without its `(type, typeVersion)`-matched `definitions[]` entry fails validate and silently vanishes from the derived agent and the package.
2. **Never hand-write `inputs.detail`.** A hand-built blob passes validate but misses `essentialConfiguration` — the activity fails at runtime. `node configure` is the only sanctioned writer; re-run it to change anything.
3. **`--all-folders` on connection discovery** — folder-scoped connections don't appear in the default list; "no connection found" is usually a missing flag, not a missing connection.
4. **Validate silence ≠ done.** `inputs.source` is the only validator-enforced field on connector nodes. A connector tool with no `detail`, no `bindings[]` rows, or no `name` validates clean and ships broken — check all three after configure.
5. **The prompt names the tool by `inputs.name`** — renaming the tool means updating the prompt (and any `guardrails[].selector.matchNames` on the agent node).
6. **Tool nodes carry no prompts** — prompts live on the agent node only.
7. **Don't duplicate solution-level connection files** — configure generates `bindings_v2.json` and `resources/solution_folder/connection/`; never create either manually ([shared/cli-commands.md § resources refresh](../../../../../shared/cli-commands.md#uip-solution-resources-refresh)).

## References

- [impl.md § Resource Nodes](../impl.md#7-resource-nodes) — universal recipe + kind matrix
- [process.md](process.md) — Orchestrator process-family tools
- [critical-rules.md](../critical-rules.md) — mandatory constraints
- [prompting guide](../prompting/autonomous-agent-prompting-guide.md) — per-tool call/stop criteria
