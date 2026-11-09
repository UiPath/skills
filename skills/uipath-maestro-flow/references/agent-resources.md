# Agent resource families

*Exact signatures, fields, and defaults: `inlineAgent()`. Prompting, inputs, and the sidecar: [inline-agent.md](inline-agent.md).*

Inline-agent capabilities are ARTIFACT nodes on handles, not control-flow steps: tools on `tool`, a context index on `context`, and escalation on `escalation`. Author each as an `inlineAgent` entry; the compiler emits its node and edge. `voiceAgent` and `conversationalAgent` accept the same `tools`, `context`, and `escalation` options, with the same rules ([below](#voice-and-conversational-agents)); only inline agents have `memory`. Context index: [inline-agent.md](inline-agent.md#context-grounding).

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
| `builtin` | Platform tool (`summarize`, `analyzefiles`, `batchtransform`) | tool name |
| `connector` | Integration Service operation | `connector` + `operation` (needs a library), plus `connection` + `folder` (`bindings.json` labels); see [inline-agent.md](inline-agent.md#tools) |
| `process` / `api` / `flow` / `maestro` / `agent` / `function` | Deployed resource or sibling project | `key` (GUID) + `name` + `folderPath` (`'solution_folder'` for a sibling); see [inline-agent.md](inline-agent.md#tools) |
| `ixp` | Published IxP project | `projectId` + `name` |
| `mcp` | MCP server tools | `name` + `key`; `slug` is runtime-resolved |
| `a2a` | Remote agent delegation | `name` + `key` + `slug` (required) |
| `clientside` | Run by the CALLING application | `name` and either `inputs`/`returns` or whole-JSON `inputSchema`/`outputSchema` (property descriptions, `items`, `required`); not both |
| `httpRequest` | Built-in HTTP tool | nothing; see below |

For `mcp`, `a2a`, and per-instance resource kinds, the node TYPE is minted from supplied identity (`…tool.mcp.<name-slug>.<key-slug>`); a wrong key emits an unresolvable tenant node. Read identities from the tenant.

**The HTTP tool's fields are three-way.** For each of `url`, `method`, `headers`, `params`, `body`, and `timeout`, either FIX it with a value or omit it for the MODEL to fill at call time, preserving the definition's prompt-mode default and field description. Fix scenario-pinned fields; fixing all defeats the tool's purpose, while fixing none gives the model no constraints.

**A client-side tool declares only a CONTRACT.** The flow specifies its name, inputs, and returns; the calling application implements and dispatches it. Nothing local runs it.

## Escalation

The default variant is app-backed: `app: { key, name, folderPath }` identifies a deployed Action Center app owning the form. `folderPath` is its Orchestrator folder (`'Shared/Approvals'`); omit it for an app shipped in this solution, and compile writes `'solution_folder'`. `variant: 'quick-form'` makes the form INLINE: provide `fields` (the same rows a human task takes) and no `app`. `check` refuses either mixed combination.

## Memory

Do not give `inlineAgent` a `memory`; `check` refuses it (`AGENT_MEMORY_NOT_AUTHORABLE`). Find the space, declare it in the solution, then attach it to the sidecar after the last `compile`. `add` only attaches an existing space; if the list is empty, stop and report it. `--field` takes a sidecar `inputSchema` key, such as `start__output__userQuestion`. `<MEMORY_SPACE_NAME>` and `<MEMORY_SPACE_FOLDER>` are the list row's `Name` and `Folder`:

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

If `memory add` reports `SolutionResource.Status: NotDeclared`, run the `resources add` line, then run `memory add` again. For threshold, result count, and search mode, run `uip agent memory add --help`. Do not add items: real runs add them after deploy; run `uip agent memory item add --help` for help.

## Evidence boundary

Every resource here is tenant data, runtime behaviour, or both. No local rung calls an MCP server, delegates to a remote agent, or asks a client application to run a tool. Offline `validate` proves minted node types, correct-handle wiring, and declared contracts; resource existence and returned values require platform evidence.

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
- **Voice agent definitions.** Compile writes each resource definition with the voice agent as an allowed source, as the designer does; built-in tools and app escalation therefore use version 1.2.
- **What decompile does not carry back yet.** These receive a `TODO` for their edge: a connector tool; a built-in tool at a version other than the one compile writes for that agent, or an HTTP request tool at a version other than 1.0; and an escalation at a version compile does not write: a quick-form other than 1.2, or an app escalation other than 1.1 (1.2 on a voice agent).

Recompiling that source drops the tool or escalation. Do not recompile such a flow from its decompiled source; edit the `.flow` instead.