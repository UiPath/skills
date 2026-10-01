# Structural BPMN: variables

## Variables

A `bpmn:task` carrying a `BPMN.Variables` mapping is the assignment node: it
writes the variables that mapping's `uipath:output` elements declare, and does
nothing else. With an empty mapping it performs no work at all. A step that
fetches, calls a system, scores, settles, aggregates, or notifies is the typed
task for that work — `bpmn:serviceTask`, `bpmn:sendTask`, `bpmn:userTask`,
`bpmn:businessRuleTask`, `bpmn:scriptTask` — carrying its registry payload.
No rule catches a bare task. `validate` warns `read but never assigned` only
where a later expression reads a variable nothing wrote, so a task whose result
nothing reads is silent and a clean warning list is not proof. Read back each
node's element and mapping.

Declare variables in the process's own `<uipath:variables>` block. Every
declaration needs a stable, unique `id`, a non-empty user-facing `name`, and its
documented `type`; do not use the name as a substitute for the id. Expressions
reference the id as `vars.<id>`. Variable schema bodies are JSON text or CDATA.

The canvas rejects these `name`s on a `uipath:input` or `uipath:inputOutput`,
matched trimmed and case-insensitive (`RESERVED_VARIABLE_NAME`), so ` Result `
is rejected too: `vars`, `iterator`, `metadata`,
`bindings`, `datafabric`, `instanceglobals`, `orchestrator`, `outputs`,
`result`, `runtime`, `senderinfo`, `this`. A public `uipath:output` may still
be named `result`; bridge it from a mutable variable with another name.

Every declaration also carries an `elementId` naming the element that owns it:
the `<bpmn:process>` id for a process-level variable, the start event id for a
caller-supplied input, the end event id for a published output, the owning node's
id for a node-scoped variable. A subprocess-level variable is keyed inside its
own subprocess: the subprocess id, or the node in it that writes the value —
both import cleanly. Without an `elementId` the declaration does not exist to
the canvas, and every `vars.<id>` reference to it fails on import.

A root `uipath:input`/`uipath:output` accepts only `string`, `boolean`,
`integer`, `number`, `array`, `object`, or `json` (or an inline JSON schema).
The canvas float types `double` and `float` are NOT usable on a public
declaration: `validate` reports `Valid`, then `refresh` fails with
`Unsupported process input/output type`. Use `number`. The restriction is
specific to public declarations — `double` on a node-scoped `uipath:inputOutput`
never reaches schema derivation and is fine.

Declare root variables with the `BPMN.Variables` registry template attached to
the process via `extensionElements`, or use the canvas `<uipath:variables>`
block directly.

```xml
<uipath:variables version="v1">
  <uipath:input id="input_ExpenseId" name="expenseId" type="string" elementId="Start_1" />
  <uipath:inputOutput id="Var_Decision" name="decision" type="string" elementId="Process_1" />
  <uipath:output id="output_Decision" name="decision" type="string" elementId="End_1" />
</uipath:variables>
```

The migration marker is optional and `uip maestro bpmn init` omits it, so new
source needs one only when asked for it. Where it appears, the attribute is
`version`, not `value`, and its value is an **integer** migration number:
`<uipath:migrationVersion version="20" />` — illustrative, not a number to
keep current. Preserve an existing value byte-for-byte when editing rather than
normalising or bumping it.

Give every root-level **manual** `bpmn:startEvent` exactly one stable GUID in
`<uipath:entryPointId value="..." />` (generate a fresh one; never the example
UUID), declared as a **direct child** of that start event's own
`<bpmn:extensionElements>`. Direct-child placement is not a style preference:
`validate` finds the element at any depth
(`project-validator.ts` searches descendants), while entry-point derivation
reads only direct children of `extensionElements`. An id nested inside
`uipath:activity` therefore passes `validate` and is invisible to `refresh`.
Subprocess start events do not carry an entry-point id.

Only a **manual** root start becomes an `entry-points.json` entry. Derivation
excludes any start event carrying an `eventDefinition` or a `uipath:event`
extension, so a timer or connector start is never an entry point — an
`entryPointId` on one is accepted but inert. With no manual root start
`refresh` throws `BPMN file must contain a root manual start event with a
uipath:entryPointId`, and a scaffolded project's `entry-points.json` goes
stale, failing `validate` and `pack`.

Public entry-point variables have a two-layer runtime contract:

- Declare each public `uipath:input` with `elementId` bound to its intended
  StartEvent and a mutable internal `uipath:inputOutput` scoped to the process
  (`elementId="<process id>"`) with the stable id used by process expressions.
  Map `=vars.<public-input-id>` to the internal id on that StartEvent.
- Declare a mutable internal `uipath:inputOutput` scoped to the process
  (`elementId="<process id>"`), plus a public
  `uipath:output` bound with `elementId` to the root EndEvent that returns it.
  Map the internal value to the public output id on that EndEvent. If one
  public result must be returned on several normal routes, converge those
  routes on that completion event. Converge routes only when they return the
  same result.

Do not route directly on a public input declaration or assume an internal
variable automatically becomes an entry-point output.

See [expression-authoring.md](expression-authoring.md) for expression rules.
Sub-process-scoped variables go in that sub-process's own `<uipath:variables>`.
