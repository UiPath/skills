# Expression Authoring

Use this reference whenever pass 2 writes Maestro runtime expressions in BPMN XML. Pass 1 may use business-readable placeholder conditions; pass 2 replaces them only after variables and scopes exist.

## Stored expression shape

- Prefix Maestro expressions with `=`; without it, values are literals. Read BPMN variables as `vars.<variableId>` (for example, `=vars.Var_RequestId`), never bare names such as `=requestId`; read context bindings as `=bindings.<bindingId>`.
- Use `result` only in the producing element's output mappings. A script task at `uipath:scriptVersion` v2 or later returns its value directly, wrapped by the runtime as `result.response`: use `return value;` with `source="=result.response"` for a scalar, or return an object with `source="=result.response.<field>"` for a field. Do not return `{ response: value }` (which double-wraps as `result.response.response`) or use `source="=result"` (which reads the wrapper).
- Multi-instance task bodies use `iterator.item`; subprocess bodies use `iterator[0].item`, then `iterator[1].item` and so on for nested subprocesses, indexed outermost (`[0]`) to innermost. The task loop index is `iterator.loopCounter`; a subprocess at depth N uses `iterator[N].loopCounter`. Do not read `iterator[0].item` outside a multi-instance subprocess body.
- Failed-element errors use capital-`Error` and lowercase fields `code`, `message`, `detail`, `category`, `status`, `traceId`, `response`, `element`; read them as `vars.Error.<field>` (for example, `=vars.Error.code == "SERVICE_UNAVAILABLE"`). Both evaluators are case-sensitive: `vars.error` does not resolve. `category` is `User` (HTTP 4xx), `System`, or `Deployment`.
- An **error event subprocess** is handed the error context as its payload, so its conditions read `vars.Error` with nothing authored. An **error boundary event** or activity's own **error mapping** is evaluated against that element's declared outputs: add `uipath:output` with `source="=Error"` before `vars.Error` resolves.

## Inline JavaScript with `=js:`

When a mapping body or context value needs more than simple `=vars.<id>` or `=bindings.<id>`, prefix it with `=js:` (case-sensitive, no space) followed by a JavaScript expression. The runtime evaluates it against the same `vars`, `bindings`, `result`, and `iterator` namespaces. Use it inside CDATA mapping bodies; it is the runtime-supported escape hatch for expressions unavailable in the BPMN grammar.

```xml
<uipath:input name="JobArguments" type="json" target="bodyField"><![CDATA[
{"startRow":"=js:iterator[0].loopCounter * vars.Var_RowsPerShard",
 "endRow":"=js:(iterator[0].loopCounter + 1) * vars.Var_RowsPerShard - 1"}
]]></uipath:input>
```

- Keep lint-sensitive read-only fields free of assignment operators.
- Prefer plain `=vars.<id>` or `=bindings.<id>` when the value needs no computation; reserve `=js:` for arithmetic, string manipulation, or conditional selection.
- A `=js:` expression returning an object or array must produce valid JSON for fields typed `json`.
- Prefer JavaScript-safe ids such as `Var_RequestId`. In brownfield files with non-identifier ids, preserve them and let the product editor or CLI normalize access; do not silently rename variables without updating all mappings, expressions, and generated metadata.

## Lint-sensitive fields

Gateway `bpmn:conditionExpression` values, activity skip conditions, multi-instance completion and filter conditions, `uipath:errorMapping` condition values, and mapping values that read variables or element outputs must be read-only expressions. Do not use assignment operators; comparisons including `==`, `===`, `!=`, `!==`, `>=`, and `<=` are allowed.

## Scope and availability

- Process-level variables are readable anywhere in the root process and surfaced by `debug-instance variables-all` and `instance variables`; declare them scoped to the process—see [structural-bpmn.md](structural-bpmn.md). Node-scoped variables belong to their node and are not process-level runtime variables; they cannot be shown by `debug-instance variables-all`.
- Keep a mutable root `uipath:inputOutput` for every value used by decisions, tasks, or diagnostics. Scope it to the process with `elementId="<process id>"`; the `elementId` must never be absent (see [Structural BPMN: Variables](structural-bpmn.md#variables)). Reference it as `vars.<id>`, not by its caller-facing declaration. Use `var="Var_RequestId"`, not `var="requestId"`; use `=vars.Var_RequestId`, not `=requestId`.
- Public caller inputs and outputs use the event bridge contract in [Structural BPMN: Variables](structural-bpmn.md#variables). Do not route on a public input before its StartEvent bridge or treat a mutable internal value as an implicit public output.
- Preserve exact variable ids: for requested id `product`, declare `id="product"` and map to `var="product"`, not `Product` or `Var_Product`. Live debug may expose the root output definition while returning its value as `null`; treat this as a debug API limitation, not evidence that the authored mapping is absent.
- Subprocess variables remain scoped to that subprocess. Output mappings target `uipath:inputOutput` or `uipath:output`, not read-only `uipath:input` variables.
- Entry point inputs that must later be updated require a separate mutable `uipath:inputOutput` scoped to the process (`elementId="<process id>"`) and an explicit mapping from the entry input.
- Trigger-bound values are `uipath:inputOutput` variables scoped to the trigger node, allowing the trigger to write them during execution.
- Use `result` only in the producing element's output mapping, and do not move a variable into a subprocess without updating mappings that read it from the root scope.