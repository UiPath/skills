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
| `process` / `api` / `flow` / `maestro` / `agent` / `function` | A deployed resource, or a sibling project of this solution | `key` (GUID) + `name` + `folderPath` (`'solution_folder'` for a sibling, see [inline-agent.md](inline-agent.md#tools)) |
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

## Process tool arguments

A `process` / `agent` / `api` / `flow` / `maestro` / `function` tool declares
its arguments in `inputs`. Each argument takes one of four forms, the canvas's
Prompt / Fixed value / Variable or a cleared argument:

```ts
{ kind: 'process', key: '<guid>', name: 'Create Account', folderPath: 'Shared',
  inputs: {
    title:      'string',                                          // cleared
    notes:      { type: 'string', prompt: 'Any extra notes' },     // Prompt
    region:     { type: 'string', value: 'EU' },                   // Fixed value
    maxResults: { type: 'integer', value: 10 },                    // Fixed value, typed
    topic:      { type: 'string', variable: input('topic') },      // Variable
  },
  returns: { accountId: 'string' } }
```

| Form | The model | Use it when |
| --- | --- | --- |
| bare type | fills it from name and type | the name says enough |
| `{ type, prompt }` | fills it, reading `prompt` as the argument's description | the model chooses, but needs guidance (format, allowed values) |
| `{ type, value }` | never chooses it | the scenario pins a constant |
| `{ type, variable }` | never chooses it | the value comes from the flow at run time |

1. **Declare every argument the resource takes.** A Fixed or Variable argument still stays in the tool's `inputSchema` and `required`: the source pins the value, it does not hide the argument.
2. **An argument object has a `type` (`string`, `number`, `integer`, `boolean`, `object`, `array`) and exactly ONE of `prompt`, `value`, `variable`.** To leave an argument to the model with no guidance, write the bare type, not `{ type }`.
3. **Write a fixed `value` in its JSON type** (`10`, `true`, an object, an array), not as text (a later Studio Web save rewrites it as text, `10` → `'10'`). A `value` is plain JSON: an SDK expression anywhere in it (top level, nested, in an array), `lit()` included, refuses compile with `INLINE_AGENT_TOOL_ARGUMENT_EXPRESSION`; bind a flow value with `variable`. `{{ … }}` inside a string is written as given.
4. **A `variable` is ONE reference:** `input('x')`, `out('step', 'field')` or `v('name')`. For anything computed (`$vars.a + $vars.b`, a template), compute it in a `script()` step first and bind `variable: out('<thatStep>')`; for a constant, use `value`. Compile turns the reference into an agent input (`input('topic')` → `start__output__topic`); the prompts need no `{{input.…}}` placeholder for it.
5. **Other tool kinds take no sources.** A `clientside` tool's `inputs` are bare types; the HTTP tool has its own fixed fields (above).

Run `check` after editing `inputs`. `_SOURCE`, `_COMPOSITE` and `_EXPRESSION`
refuse compile; `_EMPTY_PROMPT` and `_TYPE` are `check` warnings, and compile
writes those as authored:

| Code | Level | Fix |
| --- | --- | --- |
| `INLINE_AGENT_TOOL_ARGUMENT_SOURCE` | error, refuses compile | Give the object a valid `type` and exactly one source; for none, write the bare type |
| `INLINE_AGENT_TOOL_ARGUMENT_COMPOSITE` | error, refuses compile | The `variable` is a constant (use `value`) or a computed expression (compute it in a `script()` step, bind its `out(...)`) |
| `INLINE_AGENT_TOOL_ARGUMENT_EXPRESSION` | error, refuses compile | Write the fixed `value` as a plain JSON constant; for a flow value use `variable`; for a value built from flow data, compute it in a `script()` step and bind `variable: out(...)` |
| `INLINE_AGENT_TOOL_ARGUMENT_EMPTY_PROMPT` | warning | Say what the model should put there, or write the bare type |
| `INLINE_AGENT_TOOL_ARGUMENT_TYPE` | warning | Make the fixed `value` match `type`: `integer` takes a whole number; `null`, `NaN` and infinities match no type. The canvas's text form is accepted (`'42'` for a `number` or `integer`, `'true'` for a `boolean`) |

`check` reports one compile refusal per agent: fix it and rerun. Another error
on the agent (a composite input, an unknown tool kind, …) is reported before a
malformed argument; when the arguments are the only error, `check` reports the
first malformed one, in tool and then argument order.

**Brownfield.** Decompile reads each argument's source back, from the tool's
`resource.json` or, in a canvas-saved flow, from the tool node (the node wins;
a disagreement is reported). The canvas stores fixed values as text, so a
decompiled `number` argument can read `value: '42'`. Leave it as decompiled:
on an embedded (canvas-saved) agent, changing `'42'` to `42` is a tool edit,
and merge does not carry it.

Decompile reports what has no `inputs` form as lossy (a warning, an error
under `--strict`), and the argument or property comes back as its bare type:

- Agent Builder's `textBuilder`, `dynamic`, `objectBuilder` and `arrayBuilder` entries;
- a schema property carrying more than `type`, `title`, `description`, `minimum` or `maximum` (`items`, nested `properties`, `enum`, `format`, …).

Do not "fix" these in the source: leave the tool alone, and merge keeps its
original `resource.json` byte for byte.

**On an embedded canvas-saved agent, merge withholds EVERY edit to a
process-family tool's `resource.json`** (a source, an added or removed
argument, `returns`): it keeps the original file and reports the changed paths
(a warning, an error under `--strict`). Built-in, HTTP-request, IxP and
connector tool edits are still carried, since their configuration lives on the
node, which merge carries. Make process tool changes on the canvas, and say so
in the final response ([brownfield.md](brownfield.md#why-three-directories-inline-agents)).

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
