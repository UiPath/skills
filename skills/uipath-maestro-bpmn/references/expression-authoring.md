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
- Current element outputs use `result` only where the selected registry
  template defines it. Do not infer a `result.response` contract from the
  element name. For deterministic local calculation, prefer a
  `BPMN.Variables` task whose output uses a literal, `=vars.<id>`, or `=js:`
  source; this path is runtime-verifiable without an activity result envelope.
- Multi-instance task bodies read the current item from `iterator.item`.
- Multi-instance subprocess bodies read the current item from
  `iterator[0].item`. Use `iterator[1].item` (and so on) inside nested
  multi-instance subprocesses: the index counts nesting depth from outermost
  (`[0]`) to innermost.
- The current 0-based loop index inside any multi-instance body is exposed as
  `iterator.loopCounter` for tasks and `iterator[N].loopCounter` for
  subprocesses at depth N.
- Error mapping conditions may inspect the built-in error object through
  `vars.error`, for example `=vars.error.code == "SERVICE_UNAVAILABLE"`.

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
- Translate normalization requirements operand by operand. If a rule says that
  several string inputs are compared case-insensitively, normalize every one
  of those inputs at each comparison (for example,
  `vars.Var_Tier.toLowerCase() == "enterprise"` and
  `vars.Var_State.toLowerCase() == "unavailable"`). Normalizing only one field
  silently changes the business truth table. Do not normalize identifiers,
  correlation values, or outputs that the contract says to copy exactly.
- Before validation, audit each conditional expression against the supplied
  truth table: precedence order, both sides of every comparison, fallback
  outcome, exact literal spelling, and output type. Local validator success
  proves structural validity, not business-rule correctness.
- Preserve every eligibility qualifier when a later failure rule depends on
  one. For example, "if a high-severity case needs Jira and Jira is unavailable"
  is not equivalent to "if a Jira route exists and Jira is unavailable" unless
  every Jira route is guaranteed high severity. Do not use a route label as a
  proxy for severity, tier, or another qualifier without auditing the full
  cross-product. Include adversarial rows where an otherwise ineligible case
  has a duplicate/existing identifier and the external system is unavailable.

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
- Subprocess variables stay scoped to that subprocess.
- Output mappings should target `uipath:inputOutput` or `uipath:output`
  variables, not read-only `uipath:input` variables.
- Root variables supplied through an entry point must carry
  `elementId="<start-event-id>"`, and that start event must declare a stable
  `uipath:entryPointId`. A debug run can otherwise complete with unset inputs.
- Entry point inputs that must later be updated need a separate mutable
  `uipath:inputOutput` variable and an explicit mapping from the entry input.
- Trigger-bound values are commonly represented as `uipath:inputOutput`
  variables scoped with `elementId` so the trigger can write them during
  execution.

## Common mistakes

- `=requestId` instead of `=vars.Var_RequestId`.
- `=vars.Var_Count === 0` instead of either `=vars.Var_Count == 0` or
  `=js:vars.Var_Count === 0`.
- `var="requestId"` instead of `var="Var_RequestId"`.
- Assuming `result.response` exists when the registry template does not define
  that result shape.
- Reading `iterator[0].item` outside the multi-instance subprocess body.
- Moving a variable into a subprocess without updating mappings that read it
  from the root scope.
