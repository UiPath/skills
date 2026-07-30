# Expression Authoring

Use this reference whenever pass 2 writes Maestro runtime expressions in BPMN
XML. Pass 1 may use business-readable placeholder conditions; pass 2 replaces
them with expressions only after the variables and scopes exist.

## Stored expression shape

- Use a leading `=` where Maestro expects expression content.
- Treat values without `=` as literals.
- Read BPMN variables through `vars.<variableId>`, for example
  `=vars.Var_RequestId`.
- Do not use bare variable names such as `=requestId` in generated runtime XML.
- Context bindings use `=bindings.<bindingId>`.
- Current element outputs use `result` only in output mappings for that
  element. A script task at `uipath:scriptVersion` v2 or later returns its value
  directly and the runtime wraps it as `result.response`. Use `return value;`
  with `source="=result.response"` for a scalar variable, or return an object
  and use `source="=result.response.<field>"` for one of its fields. Do not wrap
  the return yourself — `return { response: value };` double-wraps to
  `result.response.response` — and do not use `source="=result"`, which reads
  the wrapper object instead of the value.
- Multi-instance task bodies read the current item from `iterator.item`.
- Multi-instance subprocess bodies read the current item from
  `iterator[0].item`. Use `iterator[1].item` (and so on) inside nested
  multi-instance subprocesses: the index counts nesting depth from outermost
  (`[0]`) to innermost.
- The current 0-based loop index inside any multi-instance body is exposed as
  `iterator.loopCounter` for tasks and `iterator[N].loopCounter` for
  subprocesses at depth N.
- The engine surfaces a failed element's error under the capital-`Error` key
  with lowercase fields: `code`, `message`, `detail`, `category`, `status`,
  `traceId`, `response`, `element`. Read it as `vars.Error.<field>` — for example
  `=vars.Error.code == "SERVICE_UNAVAILABLE"`. Both evaluators are
  case-sensitive, so `vars.error` does not resolve. `category` is `User`
  (HTTP 4xx), `System`, or `Deployment`.
- Whether a binding is needed depends on what catches the failure. An **error
  event subprocess** is handed the error context as its payload, so its
  conditions read `vars.Error` with nothing authored. An **error boundary event**
  and an activity's own **error mapping** are evaluated against that element's
  declared outputs, so those need a `uipath:output` with `source="=Error"` before
  `vars.Error` resolves.

## Inline JavaScript with `=js:`

When a mapping body or context value needs computation that a simple
`=vars.<id>` expression cannot express, prefix the body with `=js:` and follow
it with a JavaScript expression. The runtime evaluates the rest of the value
against the same `vars`, `bindings`, `result`, and `iterator` namespaces.
Use this form inside CDATA mapping bodies; it is the runtime-supported
escape hatch the BPMN expression grammar does not otherwise expose.

```xml
<uipath:input name="JobArguments" type="json" target="bodyField"><![CDATA[
{"startRow":"=js:iterator[0].loopCounter * vars.Var_RowsPerShard",
 "endRow":"=js:(iterator[0].loopCounter + 1) * vars.Var_RowsPerShard - 1"}
]]></uipath:input>
```

Rules:

- The prefix is `=js:` (case-sensitive, no space).
- The body must still satisfy lint-sensitive constraints: no assignment
  operators in fields where read-only expressions are required.
- Prefer plain `=vars.<id>` or `=bindings.<id>` when the value does not need
  computation — `=js:` should be reserved for arithmetic, string
  manipulation, or conditional selection.
- A `=js:` expression that returns an object or array must produce valid JSON
  for fields typed `json`.

Prefer JavaScript-safe variable ids such as `Var_RequestId`. If a brownfield
file contains non-identifier ids, preserve them and let the product editor or
CLI normalize the access form; do not silently rename variables without updating
all mappings, expressions, and generated metadata.

## Lint-sensitive fields

These fields must be read-only expressions:

- Gateway `bpmn:conditionExpression` values.
- Activity skip conditions.
- Multi-instance completion and filter conditions.
- `uipath:errorMapping` condition values.
- Mapping values that read variables or element outputs.

Do not use assignment operators in these fields. Comparisons such as `==`,
`===`, `!=`, `!==`, `>=`, and `<=` are allowed.

## Scope and availability

- A process-level variable is readable from anywhere in the root process, and is
  what `debug-instance variables-all` and `instance variables` surface. Declare
  it scoped to the process — see [structural-bpmn.md](structural-bpmn.md). A
  variable scoped to a node is bound to that node and is not surfaced as a
  process-level runtime variable.
- Keep a mutable root `uipath:inputOutput` for each value used by decisions,
  tasks, or diagnostics. Process expressions reference that mutable variable
  as `vars.<id>`, not the caller-facing declaration.
- Public caller inputs and outputs use the event bridge contract documented in
  [Structural BPMN: Variables](structural-bpmn.md#variables-bpmnvariables).
  Do not route on a public input before its StartEvent bridge or treat a mutable
  internal value as an implicit public output.
- Preserve exact variable ids: if the requested variable id is `product`,
  declare `id="product"` and map to `var="product"`, not `Product` or
  `Var_Product`.
- Subprocess variables stay scoped to that subprocess.
- Output mappings should target `uipath:inputOutput` or `uipath:output`
  variables, not read-only `uipath:input` variables.
- Entry point inputs that must later be updated need a separate mutable
  `uipath:inputOutput` variable and an explicit mapping from the entry input.
- Trigger-bound values are `uipath:inputOutput` variables scoped to the trigger
  node, so the trigger can write them during execution.

## Common mistakes

- `=requestId` instead of `=vars.Var_RequestId`.
- `var="requestId"` instead of `var="Var_RequestId"`.
- Using `result` outside the output mapping of the element that produced it.
- Reading `iterator[0].item` outside the multi-instance subprocess body.
- Moving a variable into a subprocess without updating mappings that read it
  from the root scope.
