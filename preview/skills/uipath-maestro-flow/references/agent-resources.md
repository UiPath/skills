# Agent resource families

*Exact signatures, fields, and defaults: [`inlineAgent()`](api.md#inlineagent-function). Prompting, inputs and the sidecar: [inline-agent.md](inline-agent.md).*

An inline agent's capabilities are ARTIFACT nodes hanging off its own handles —
tools on `tool`, an escalation on `escalation`, a memory on `memory` — not steps
in the control flow. Each is authored as an entry on `inlineAgent`, and the
compiler emits the node and the edge.

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
  memory: { name: 'Support History', id: '<guid>' },
  escalation: [{ variant: 'quick-form', name: 'Confirm', outcomes: ['Approve', 'Reject'],
    fields: [{ id: 'approved', type: 'boolean', direction: 'output' }] }],
}))
```

## Tool kinds

| Kind | What it is | Identity you must supply |
| --- | --- | --- |
| `builtin` | A platform tool (`summarize`, `analyzefiles`, `batchtransform`) | the tool name |
| `connector` | An Integration Service operation | `connector` + `operation` (needs a library) |
| `process` / `api` / `flow` / `maestro` / `agent` / `function` | A deployed resource | `key` (GUID) + `name` + `folderPath` |
| `ixp` | A published IxP project | `projectId` + `name` |
| `mcp` | An MCP server's tools | `name` + `key`; `slug` is what the runtime resolves |
| `a2a` | A remote agent to delegate to | `name` + `key` + `slug` (required) |
| `clientside` | The CALLING application runs it | `name`, plus the `inputs`/`returns` contract |
| `httpRequest` | The built-in HTTP tool | nothing — see below |

For `mcp`, `a2a`, `memory` and the per-instance resource kinds, the node TYPE is
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

## Escalation

The default variant is app-backed: `app: { key, name, folderPath }` names a
deployed Action Center app that owns the form. `variant: 'quick-form'` puts the
form INLINE instead — `fields` (the same rows a human task takes) and no `app`.
`check` refuses the two mixed, in either direction.

## Memory

`memory: { name, id }` attaches an episodic memory so the agent learns from past
runs, with optional retrieval tuning (`dynamicFewShotLearning`,
`semanticSimilarity`, `kValue`, `searchMode`). Naming one selects the agent's
**1.4** definition — the version that declares the `memory` handle. Omitting it
leaves the agent on 1.2 exactly as before.

## Evidence boundary

Every resource here is tenant data, runtime behaviour, or both: no local rung
calls an MCP server, delegates to a remote agent, retrieves a memory, or asks a
client application to run a tool. Offline `validate` proves the minted node
types, the wiring to the right handle, and the declared contracts. Whether the
resources exist and what they return is platform evidence.
