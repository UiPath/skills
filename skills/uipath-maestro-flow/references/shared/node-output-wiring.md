# Wiring Node Outputs to Downstream Inputs

Use this reference whenever a `.flow` JSON field references a previous node output, workflow variable, or `$metadata.*` / `$self.*`. It is the source of truth for `=js:` expressions; node-type plugins defer to it.

## Core rule

In value-typed fields, every `$vars.*`, `$metadata.*`, or `$self.*` reference must start with `=js:`. Otherwise, runtime treats the rewritten value as a literal.

Use `$vars.<sourceNodeId>.output.<field>`—never `nodes.X.output.Y`. `<sourceNodeId>` is the producing node's `id`; `output` is the standard output port (`error` is the error port); `<field>` is the output path.

```text
=js:$vars.fetchUser1.output
=js:$vars.createRecord1.output.Id
=js:$vars.queryRecords1.output[0].Id
=js:$vars.fetchUser1.output.id === $vars.input.userId
=js:$metadata.instanceId
=js:`Hello ${$vars.userName}`
```

Static values do not need `=js:`. For mixed strings, use `=js:` with JavaScript template literals and `${}`.

## Where `=js:` applies

| Context | Field | Rule |
|---|---|---|
| Connector activity nodes (`uipath.connector.<connector-key>.<activity>`) | `inputs.detail.bodyParameters.*`, `queryParameters.*`, `pathParameters.*` | **YES** |
| Managed HTTP (`core.action.http.v2`) | `inputs.detail.bodyParameters.url`, `headers`, `query`, `body` | **YES**; dynamic fields are stored here in `.flow` JSON in both manual and connector mode, regardless of how the CLI `--detail` flag accepts them at the top level |
| Custom HTTP (`core.action.http`) | `inputs.url`, `headers`, `body`, `queryParams` | **YES**; deprecated, prefer `core.action.http.v2` |
| HTTP branches | `inputs.branches[].conditionExpression` | **NO**; already JS |
| Decision (`core.logic.decision`) | `inputs.expression` | **NO**; already JS |
| Switch (`core.logic.switch`) | `inputs.cases[].expression` | **NO**; already JS |
| End nodes (`core.control.end`) | `outputs.<varId>.source` | **YES** |
| Variable updates | `variables.variableUpdates.<nodeId>[].expression` | **NO**; use `{ "type": "jsExpression", "expression": "<bare JS>", "fieldType": "<target variable type>" }`. A `=js:` string fails `flow validate` at the 1.9→1.10 migration. See [variables-and-expressions.md § Variable Updates](variables-and-expressions.md#variable-updates-variableupdates). |
| Loop nodes (`core.logic.loop`) | `inputs.collection` | **YES** |
| Subflow nodes (`core.subflow`) | `inputs.<inputId>.source` | **YES** |
| Script nodes (`core.action.script`) | `inputs.script` body | **NO**; the body is already JS and reads `$vars.*` directly |
| Inline-agent prompt (`uipath.agent.autonomous` `agent.json` `messages[].content`) | Flow-node tokens | **NO**; use `{{ $vars.<flowNodeId>.output[.<field>] }}` with spaced braces and mirror it in `contentTokens[]` as `{ "type": "variable", "rawString": " $vars.<flowNodeId>.output[.<field>] " }`. `rawString` must include leading and trailing space. Never use `{{input.<id>}}` or bare `{{name}}`. See [author/references/plugins/inline-agent/impl.md § Wiring Flow Variables into Agent Prompts](../author/references/plugins/inline-agent/impl.md#wiring-flow-variables-into-agent-prompts). |

Do not add `=js:` to Decision, Switch, or HTTP branch conditions, script bodies, variable-update expressions, or inline-agent tokens; these formats are parsed separately.

## Connector and HTTP wiring

```jsonc
"inputs": {
  "detail": {
    "method": "POST",
    "endpoint": "/v2/{entityName}/UpdateEntityRecord",
    "pathParameters": { "entityName": "Entity" },
    "queryParameters": {
      "recordId": "=js:$vars.createRecord1.output.Id",
      "expansionLevel": "3"
    },
    "bodyParameters": {
      "Name": "static-value",
      "AccountId": "=js:$vars.queryAccounts1.output[0].Id",
      "Notes": "=js:`Created from flow run ${$metadata.instanceId}`"
    }
  }
}
```

Plugin-specific path fields are not value fields; follow the plugin reference. In particular, Transform `inputs.collection` must be a path such as `"$vars.orders.output.items"`, without `=js:`.

## Never do this

1. **Never invent `nodes.X.output.Y`;** use `$vars` references.
2. **Never write `$vars.X.output.Y` without `=js:`** in an expression value field. The `$vars→vars` rewrite still occurs, producing a literal. Use the plugin-specific format for path fields such as Transform `inputs.collection`.
3. **Never wrap Decision, Switch, or HTTP branch conditions in `=js:`.** They already parse JS.
4. **Never use `{ }` template interpolation in connector or HTTP activity inputs.** The flow-layer template runner skips these fields; the `$` is stripped and `{vars.X}` ships literally to the IS runtime. Use `=js:` with JS template literals instead.
5. **Never quote `=js:` itself in an expression.** `"=js:$vars.X"` is correct; `"\"=js:$vars.X\""` is a string containing the prefix.

## Runtime and migration behavior

`expression-transform.ts` rewrites `$vars` → `vars` in every node-data string, whether or not `=js:` is present. The prefix tells the BPMN engine to evaluate the result; without it, the rewritten value remains literal. `bpmn-moddle.ts` has an `ensureJsPrefix` fallback only for variable updates. Connector and HTTP activity inputs have no equivalent fallback, so write `=js:` explicitly.

## Validation

When a flow outputs literal `vars.X.output.Y`, `nodes.X.output.Y`, or another unevaluated expression:

1. Open the `.flow` file.
2. Search for the token: `grep '"vars\.' <project>.flow` or `grep '"\$vars\.' <project>.flow`.
3. In `bodyParameters`, `queryParameters`, `pathParameters`, end-node `source`, and other value fields, prepend `=js:` to each variable reference.
4. Run `uip maestro flow validate` and re-debug.