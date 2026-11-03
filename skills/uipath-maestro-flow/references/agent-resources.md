# Agent resource families

*Exact signatures, fields, and defaults: `inlineAgent()`. Prompting, inputs and the sidecar: [inline-agent.md](inline-agent.md).*

An inline agent's capabilities are ARTIFACT nodes hanging off its own handles — tools on `tool`, a context index on `context`, an escalation on `escalation` — not steps in the control flow.
Each is authored as an entry on `inlineAgent`, and the compiler emits the node and the edge.
`voiceAgent` and `conversationalAgent` take the same `tools`, `context` and `escalation` options, with the same rules ([below](#voice-and-conversational-agents)); `memory` is the inline agent's alone.
Context index: [inline-agent.md](inline-agent.md#context-grounding).

```ts
.step('triage', inlineAgent({
  model: 'gpt-5.4', systemPrompt: '…', userPrompt: '…',
  tools: [
    { kind: 'mcp', name: 'Ticket MCP', key: '<guid>', slug: 'ticket-mcp', folderPath: 'Shared' },
    { kind: 'a2a', name: 'Research Agent', key: '<guid>', slug: 'research-agent' },
    { kind: 'clientside', name: 'pickFile', inputs: { prompt: 'string' }, returns: { path: 'string' } },
    { kind: 'httpRequest', url: 'https://api.example.test/items', method: 'GET' },
    { kind: 'function', key: '<guid>', name: 'acme-echo', folderPath: 'Shared/acme-echo' },
  ],
  escalation: [{ variant: 'quick-form', name: 'Confirm', outcomes: ['Approve', 'Reject'],
    fields: [{ id: 'approved', type: 'boolean', direction: 'output' }] }],
}))
```

## Tool kinds

| Kind | What it is | Identity you must supply |
| --- | --- | --- |
| `builtin` | A platform tool (`summarize`, `analyzefiles`, `batchtransform`) | the tool name |
| `connector` | An Integration Service operation | `connector` + `operation` (needs a library), plus `connection` + `folder` (`bindings.json` labels) — see [inline-agent.md](inline-agent.md#tools) |
| `process` / `api` / `flow` / `maestro` / `agent` / `function` | A deployed resource, or a sibling project of this solution | `key` (GUID) + `name` + `folderPath` (`'solution_folder'` for a sibling, see [inline-agent.md](inline-agent.md#tools)) |
| `ixp` | A published IxP project | `projectId` + `name` |
| `mcp` | An MCP server's tools | `name` + `key`; `slug` is what the runtime resolves |
| `a2a` | A remote agent to delegate to | `name` + `key` + `slug` (required) |
| `clientside` | The CALLING application runs it | `name`, plus the `inputs`/`returns` contract, or `inputSchema`/`outputSchema` for a whole JSON schema (property descriptions, `items`, `required`); not both |
| `httpRequest` | The built-in HTTP tool | nothing — see below |

For `mcp`, `a2a` and the per-instance resource kinds, the node TYPE is
minted from the identity you give (`…tool.mcp.<name-slug>.<key-slug>`), so a
wrong key emits a node the tenant cannot resolve. Read them from the tenant.

**The HTTP tool's fields are three-way.** Each of `url`, `method`, `headers`,
`params`, `body`, `timeout` is either FIXED (give it a value) or left for the
MODEL to fill at call time (omit it, which keeps the definition's prompt-mode
default and its field description). Fixing everything defeats the point of
giving an agent a tool; fixing nothing gives the model no constraints. Fix what
the scenario pins and leave the rest.

**A client-side tool declares only a CONTRACT.** The flow says what the tool is
called and what it takes and returns; the calling application owns the
implementation and dispatches on the name. Nothing local runs it.

## The Batch Transform tool

`{ kind: 'builtin', tool: 'batchtransform' }` lets the agent add columns to a
CSV; the model passes the file as the tool's `attachment`. A step that always
enriches one CSV is `batchTransform()` instead ([batch-transform.md](batch-transform.md)).

```ts
{
  kind: 'builtin', tool: 'batchtransform',
  query: { value: 'Classify each invoice line' },  // the task
  outputColumns: [
    { name: 'Category', description: 'One of: Utility, Software, Travel, Other' },
  ],
  webSearchGrounding: 'disabled',                  // default 'enabled'
}
```

**`outputColumns` is required:** 1 to 10, each a name of 1 to 64 letters,
digits, `_` or `-` (no spaces) and a description of what goes in the column.
**Disable `webSearchGrounding` unless the scenario needs the web:** unlike the
step's `enableWebSearchGrounding`, it defaults to on.

**`query` takes the canvas's sources:** omitted (the model writes the task), a
string or `{ prompt }` (the model writes it, guided), `{ value }` (pinned), or
`{ variable }` (ONE flow reference, which becomes an agent input). A bare
`query: input('task')` is pinned text, never evaluated. `summarize` takes the
same forms; the other two settings are `batchtransform`'s only.

`check` reports these as `INLINE_AGENT_BATCH_TRANSFORM_*` (`_NO_COLUMNS`,
`_TOO_MANY_COLUMNS`, `_COLUMN_NAME`, `_COLUMN_DESCRIPTION`, `_GROUNDING`) and
`INLINE_AGENT_BUILTIN_*` (`_QUERY_SOURCE`, `_COMPOSITE_REF`,
`_SETTING_NOT_APPLICABLE`). Compile also refuses `_GROUNDING` and the three
`BUILTIN` codes.

**Brownfield.** Decompile reports lossy what it cannot read back: a setting
with no SDK form (a file bound to a variable, a non-`csv` `fileExtension`), a
tool node cut to `{ source }` whose `resource.json` it could not read, and any
Summarize task but Empty. Edit
those flows with `merge --baseline`
([brownfield.md](brownfield.md#agent-resources-added-changed-removed)), which
keeps the original `resource.json`. Adding or removing a column replaces the
whole array.

## Escalation

The default variant is app-backed: `app: { key, name, folderPath }` names a
deployed Action Center app that owns the form. `folderPath` is the app's
Orchestrator folder (`'Shared/Approvals'`); omit it for an app that ships in this
solution, and compile writes `'solution_folder'`. `variant: 'quick-form'` puts the
form INLINE instead — `fields` (the same rows a human task takes) and no `app`.
`check` refuses the two mixed, in either direction.

## Memory

Do not give `inlineAgent` a `memory`; `check` refuses it (`AGENT_MEMORY_NOT_AUTHORABLE`).
Find the space, declare it in the solution, then attach it to the sidecar after the
last `compile`. `add` only attaches an existing space: an empty list means stop and
report it. `--field` takes a sidecar `inputSchema` key, e.g. `start__output__userQuestion`.
`<MEMORY_SPACE_NAME>` and `<MEMORY_SPACE_FOLDER>` are the list row's `Name` and `Folder`:

```bash
uip solution resources list --source remote --kind MemorySpace --search "<MEMORY_SPACE_NAME>" --output json
uip solution resources add --source remote --kind MemorySpace --name "<MEMORY_SPACE_NAME>" \
  --folder-path "<MEMORY_SPACE_FOLDER>" --solution-folder "<Solution>" --output json
uip agent memory add <FeatureName> --memory-space "<MEMORY_SPACE_NAME>" \
  --folder-path "<MEMORY_SPACE_FOLDER>" --field <inputSchema-key>=1 \
  --path "<Solution>/<Name>/<source>" --output json
uip agent refresh "<Solution>/<Name>/<source>" --inline-in-flow \
  --bindings-target "<Solution>/<Name>/bindings_v2.json" --output json
```

`memory add` reporting `SolutionResource.Status: NotDeclared` means the space is not
linked: run the `resources add` line, then `memory add` again. Threshold, result count,
search mode: `uip agent memory add --help`. Do not add items: they come from real runs
after deploy (`uip agent memory item add --help`).

## Evidence boundary

Every resource here is tenant data, runtime behaviour, or both: no local rung
calls an MCP server, delegates to a remote agent, or asks a
client application to run a tool. Offline `validate` proves the minted node
types, the wiring to the right handle, and the declared contracts. Whether the
resources exist and what they return is platform evidence.

## Voice and conversational agents

<!--skill-flavor:voice-conversational-resources-sdk-version:start-->
**Needs `@uipath/maestro-builder-sdk` 6.88.2 or later.** An older SDK accepts
these options with no finding and compiles the agent with no tool, context or
escalation nodes. Upgrade the copy in use: `npm install
@uipath/maestro-builder-sdk@latest` in a workspace that has its own
`node_modules` copy (it is used before the global one), else `npm install -g
@uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:voice-conversational-resources-sdk-version:end-->

- **`check` codes.** The inline agent's rules, under codes all three agents
  share: `FLOW_AGENT_TOOL_*`, `FLOW_AGENT_ESCALATION_*`, `FLOW_AGENT_RESOURCE_*`,
  `FLOW_AGENT_CONTEXT_*`. Each message names the agent's kind (`Voice agent step
  "a" …`). An SDK older than 6.88.2 prints the same rules for an inline agent
  as `INLINE_AGENT_TOOL_*`, `INLINE_AGENT_ESCALATION_*`, `INLINE_AGENT_RESOURCE_*`
  and `AGENT_CONTEXT_*`.
- **Voice agent definitions.** Compile writes each resource's definition with
  the voice agent as an allowed source, as the designer does; the built-in
  tools and the app escalation go out at 1.2 for that reason.
- **What decompile does not carry back yet.** These get a `TODO` for their edge:
  - a connector tool;
  - a built-in tool at a version other than the one compile writes for that
    agent, and an HTTP request tool at a version other than 1.0;
  - an escalation at a version compile does not write: a quick-form other than
    1.2, or an app escalation other than 1.1 (1.2 on a voice agent).

  Recompiling that source drops the tool or escalation. Do not recompile such a
  flow from its decompiled source; edit the `.flow` instead.

