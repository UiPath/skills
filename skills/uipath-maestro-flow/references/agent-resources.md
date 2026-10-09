# Agent resource families

*Exact signatures, fields, and defaults: `inlineAgent()`. Prompting, inputs and the sidecar: [inline-agent.md](inline-agent.md).*

An inline agent's capabilities are ARTIFACT nodes hanging off its own handles — tools on `tool`, a context index on `context`, an escalation on `escalation` — not steps in the control flow.
Each is authored as an entry on `inlineAgent`, and the compiler emits the node and the edge.
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
| `process` / `api` / `flow` / `maestro` / `agent` / `function` | A deployed resource | `key` (GUID) + `name` + `folderPath` |
| `ixp` | A published IxP project | `projectId` + `name` |
| `mcp` | An MCP server's tools | `name` + `key`; `slug` is what the runtime resolves |
| `a2a` | A remote agent to delegate to | `name` + `key` + `slug` (required) |
| `clientside` | The CALLING application runs it | `name`, plus the `inputs`/`returns` contract |
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

## Escalation

The default variant is app-backed: `app: { key, name, folderPath }` names a
deployed Action Center app that owns the form. `variant: 'quick-form'` puts the
form INLINE instead — `fields` (the same rows a human task takes) and no `app`.
`check` refuses the two mixed, in either direction.

## Memory

Do not attach `memory`. The platform's autonomous agent declares no `memory`
handle, so `check` refuses it (`AGENT_MEMORY_NOT_AUTHORABLE`), and a flow
compiled past `check` fails `uip maestro flow validate` with "does not declare
that handle". Give the agent knowledge to retrieve through a context index
([inline-agent.md](inline-agent.md#context-grounding)); in a chat flow, the
history reaches a conversational agent through its conversation context
([conversational.md](conversational.md)).

## Evidence boundary

Every resource here is tenant data, runtime behaviour, or both: no local rung
calls an MCP server, delegates to a remote agent, or asks a
client application to run a tool. Offline `validate` proves the minted node
types, the wiring to the right handle, and the declared contracts. Whether the
resources exist and what they return is platform evidence.
