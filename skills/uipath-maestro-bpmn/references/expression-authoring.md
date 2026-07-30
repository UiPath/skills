# Expression Authoring

Use this reference whenever pass 2 writes Maestro runtime expressions in BPMN
XML. Pass 1 may use business-readable placeholder conditions; pass 2 replaces
them with expressions only after the variables and scopes exist.

## Stored expression shape

- Use a leading `=` where Maestro expects expression content.
- Treat values without `=` as literals.
- XML mapping attributes are lexical, so bare `true`, `false`, and `42` are
  string literals. Assign typed constants with expressions (`=true`, `=false`,
  `=42`); never pass a JSON boolean or number as a declarative mapping
  `source`.
- Read BPMN variables through `vars.<variableId>`, for example
  `=vars.Var_RequestId`.
- Do not use bare variable names such as `=requestId` in generated runtime XML.
- Context bindings use `=bindings.<bindingId>`.
- Current element outputs use `result` only in output mappings for that
  element. For new v3 ScriptTasks, return the intended scalar or object
  directly and map the standard response variable from
  `source="=result.response"`. Do not wrap the return in another
  `{ response: ... }` object.
- Multi-instance task bodies read the current item from `iterator.item`.
- Direct mappings in multi-instance subprocess bodies read the current item
  from `iterator[0].item`. Use `iterator[1].item` (and so on) inside nested
  multi-instance subprocesses: the index counts nesting depth from outermost
  (`[0]`) to innermost. A ScriptTask in such a body must map that expression
  to a typed named arg and read the named arg in its JavaScript; passing the
  whole `=iterator` object can yield null.
- The current loop index is exposed as the **1-based** `iterator.loopCounter`
  inside a task marker and `iterator[N].loopCounter` inside a subprocess
  marker at depth N. The engine stores a zero-based internal instance index
  but publishes `index + 1` in the iterator namespace.
- Error mapping conditions may inspect the built-in error object through
  `vars.error`, for example `=vars.error.code == "SERVICE_UNAVAILABLE"`.
- Treat sibling conditions from one exclusive gateway as an unordered set.
  They must be mutually exclusive; encode business precedence in each guard or
  use cascaded gateways instead of relying on first-match evaluation order.

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

Do not use assignment operators in these fields. A plain Maestro expression
(`=vars...`) uses the BPMN expression grammar: use `==`, `!=`, `>=`, and `<=`.
JavaScript-only operators such as `===` and `!==` require an `=js:` prefix;
without it they can pass the local structural validator but fail at runtime
with `Expression expected`. Use `=js:` for compound JavaScript conditions as
well, including `&&`, `||`, and `!`.

## Scope and availability

- Root variables are visible across the root process after they are declared and
  reachable by control flow.
- Keep a mutable root `uipath:inputOutput` for each value used by decisions,
  tasks, or diagnostics. Public caller inputs and outputs are separate
  declarations bound with `elementId` to the entry StartEvent and completion
  EndEvent, respectively. Bridge them explicitly with `BPMN.Variables`
  mappings on those events.
- Subprocess variables stay scoped to that subprocess. Map values needed by
  the parent explicitly on the `bpmn:subProcess`; do not infer propagation from
  a successful inner assignment.
- Output mappings should target `uipath:inputOutput` or `uipath:output`
  variables, not read-only `uipath:input` variables.
- A declared public output has no portable implicit default. Ensure a visible
  Variables task assigns it on every path that can reach a root end, including
  the neutral value (`""`, `=false`, `=0`, `=js:[]`, and so on) where required.
- Root variables supplied through an entry point need a public `uipath:input`
  carrying `elementId="<start-event-id>"`; that start event must declare a
  stable `uipath:entryPointId` and map the public value to a separate mutable
  `uipath:inputOutput`.
- Trigger-bound values are commonly represented as `uipath:inputOutput`
  variables scoped with `elementId` so the trigger can write them during
  execution.

## Common mistakes

- `=requestId` instead of `=vars.Var_RequestId`.
- `=vars.Var_Count === 0` instead of either `=vars.Var_Count == 0` or
  `=js:vars.Var_Count === 0`.
- `var="requestId"` instead of `var="Var_RequestId"`.
- Using `result` outside the output mapping of the element that produced it.
- Reading `iterator[0].item` outside the multi-instance subprocess body.
- Passing `{"iterator":"=iterator"}` to a ScriptTask nested inside a
  multi-instance subprocess instead of mapping `=iterator[0].item` to a typed
  named argument.
- Moving a variable into a subprocess without updating mappings that read it
  from the root scope.
