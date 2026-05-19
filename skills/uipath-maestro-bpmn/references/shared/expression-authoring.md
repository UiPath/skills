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
- Current element outputs use `result` only in output mappings for that element,
  for example `source="=result.response"` for script task results.
- Multi-instance task bodies read the current item from `iterator.item`.
- Multi-instance subprocess bodies read the current item from
  `iterator[0].item`.
- Error mapping conditions may inspect the built-in error object through
  `vars.error`, for example `=vars.error.code == "SERVICE_UNAVAILABLE"`.

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

- Root variables are visible across the root process after they are declared and
  reachable by control flow.
- Subprocess variables stay scoped to that subprocess.
- Output mappings should target `uipath:inputOutput` or `uipath:output`
  variables, not read-only `uipath:input` variables.
- Entry point inputs that must later be updated need a separate mutable
  `uipath:inputOutput` variable and an explicit mapping from the entry input.
- Trigger-bound values are commonly represented as `uipath:inputOutput`
  variables scoped with `elementId` so the trigger can write them during
  execution.

## Common mistakes

- `=requestId` instead of `=vars.Var_RequestId`.
- `var="requestId"` instead of `var="Var_RequestId"`.
- Using `result` outside the output mapping of the element that produced it.
- Reading `iterator[0].item` outside the multi-instance subprocess body.
- Moving a variable into a subprocess without updating mappings that read it
  from the root scope.
