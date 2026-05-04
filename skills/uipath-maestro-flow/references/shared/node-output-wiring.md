# Wiring Node Outputs to Downstream Inputs

How to reference one node's output (or any `$vars.*` value) from another node's input fields. This is the **single source of truth** for `=js:` expression rules in `.flow` JSON. All node-type plugins (connector, http, script, decision, end, etc.) defer to this file.

> **Read this before** writing any field that needs to reference a previous node's output, a workflow variable, or any other `$vars.*` / `$metadata.*` value. Skipping `=js:` is the #1 cause of "the value at runtime was the literal string `vars.X.output.Id`" failures (MST-9107).

---

## The Rule (one sentence)

**Any string that references `$vars.*`, `$metadata.*`, or `$self.*` MUST start with `=js:`. Otherwise it is a literal string at runtime.**

---

## What Goes Wrong Without `=js:`

The Flow runtime serializes string fields into BPMN. The serializer rewrites the canvas-form tokens (`$vars` → `vars`) **whether or not the `=js:` prefix is present**. This means a missing prefix is silent — `flow validate` passes, the file looks plausible, but at runtime the BPMN engine sees a plain string and never evaluates it.

Three failure modes observed in agent-generated `.flow` files:

| What the agent wrote | What ships to runtime | Result |
|---|---|---|
| `"nodes.createEntityRecord1.output.Id"` | `"nodes.createEntityRecord1.output.Id"` | Literal string — invented `nodes.` prefix has no meaning. |
| `"$vars.createEntityRecord1.output.Id"` | `"vars.createEntityRecord1.output.Id"` | Literal string — `$vars` rewritten to `vars` but no `=js:` so never evaluated. |
| `"=js:$vars.createEntityRecord1.output.Id"` | `"=js:vars.createEntityRecord1.output.Id"` | Evaluates correctly. |

**There is no "nodes.X.output.Y" syntax.** Variable references always use `$vars.*`.

---

## The Canonical Pattern

```
"=js:$vars.<sourceNodeId>.output.<field>"
```

- `<sourceNodeId>` — the `id` value of the node that produces the output
- `output` — the literal string `output` (the standard output port; use `error` for errors)
- `<field>` — the field path within the output object

### Examples

| What you want | Expression |
|---|---|
| The whole output object | `=js:$vars.fetchUser1.output` |
| One field from a single-record output | `=js:$vars.createEntityRecord1.output.Id` |
| A field from the first record of a query result (array) | `=js:$vars.queryEntityRecords1.output[0].Id` |
| Filter on a value from a previous node | `=js:$vars.fetchUser1.output.id === $vars.input.userId` |
| A static value (no variables) | `"HDFC Bank"` (no prefix needed) |
| A built-in metadata value | `=js:$metadata.instanceId` |
| A literal that contains a variable | `` =js:`Hello ${$vars.userName}` `` |

---

## Where the Rule Applies

`=js:` is **required** in every field below when the value references `$vars`, `$metadata`, or `$self`:

| Node / context | Field | Required `=js:`? |
|---|---|---|
| **Connector activity nodes** (`uipath.connector.<connector-key>.<activity>`) | `inputs.detail.bodyParameters.*` (all values) | **YES** |
| | `inputs.detail.queryParameters.*` (all values) | **YES** |
| | `inputs.detail.pathParameters.*` (all values) | **YES** |
| **Managed HTTP** (`core.action.http.v2`) | `inputs.detail.bodyParameters.url` / `headers` / `query` / `body` — both manual and connector mode store dynamic fields here in the `.flow` JSON, regardless of how the CLI's `--detail` flag accepts them at the top level | **YES** |
| **Custom HTTP** (`core.action.http`) | `inputs.url` / `headers` / `body` / `queryParams` (deprecated; prefer `core.action.http.v2`) | **YES** |
| **HTTP branches** | `inputs.branches[].conditionExpression` | **NO** — already JS, do not prefix |
| **Decision** (`core.logic.decision`) | `inputs.expression` | **NO** — already JS, do not prefix |
| **Switch** (`core.logic.switch`) | `inputs.cases[].expression` | **NO** — already JS, do not prefix |
| **End nodes** (`core.control.end`) | `outputs.<varId>.source` | **YES** |
| **Variable updates** | `variables.variableUpdates.<nodeId>[].expression` | **YES** (the CLI auto-prefixes if missing, but write it explicitly) |
| **Loop nodes** (`core.logic.loop`) | `inputs.collection` | **YES** |
| **Subflow nodes** (`core.subflow`) | `inputs.<inputId>.source` | **YES** |
| **Script nodes** (`core.action.script`) | `inputs.script` body — `$vars.*` is read inside JS, no `=js:` wrapping | **NO** — the body is already JS |
| **Native flow text fields** (agent prompt, sticky note) | Any string with `{$vars.X}` template interpolation | **NO** — uses `{ }` template, not `=js:` |

**Rule of thumb:** If the field is *value-typed* (anything other than a hardcoded condition), `=js:` is required for `$vars`/`$metadata`/`$self` references. The two condition fields (Decision, Switch) and the script body are the only exceptions — they are always parsed as JS regardless.

---

## Connector Node Wiring — Quick Reference

For connector nodes (`uipath.connector.*`), the most common wiring patterns:

```jsonc
"inputs": {
  "detail": {
    "method": "POST",
    "endpoint": "/v2/{entityName}/UpdateEntityRecord",
    "pathParameters": {
      "entityName": "BankDetails"
    },
    "queryParameters": {
      "recordId": "=js:$vars.createEntityRecord1.output.Id",
      "expansionLevel": "3"
    },
    "bodyParameters": {
      "BankName": "HDFC Bank",
      "AccountId": "=js:$vars.queryAccounts1.output[0].Id",
      "Notes": "=js:`Created from flow run ${$metadata.instanceId}`"
    }
  }
}
```

- **Static values** (`"HDFC Bank"`, `"3"`) — no prefix, written as plain JSON values.
- **Variable references** (`$vars.X.output.Y`) — **always** wrap with `=js:`.
- **Mixed strings** (template literals) — wrap the whole expression in `=js:` and use JS template literal syntax with `${ }`.

---

## Anti-Patterns (Never Write These)

1. **Never invent a `nodes.X.output.Y` syntax.** It does not exist. All variable references use `$vars`.
2. **Never write `$vars.X.output.Y` without `=js:`** in any value field. The `$vars→vars` rewrite happens regardless of prefix, leaving you with a literal string `"vars.X.output.Y"` at runtime — looks like an expression, isn't one.
3. **Never wrap conditions** (Decision, Switch, HTTP branch) in `=js:`. Those are parsed as JS automatically.
4. **Never use `{ }` template interpolation in connector or HTTP activity inputs.** The flow-layer template runner skips these fields. The `$` is stripped and `{vars.X}` ships literally to the IS runtime. Use `=js:` and JS template literals (`` `…${$vars.X}…` ``) instead.
5. **Never quote `=js:` itself in an expression.** `"=js:$vars.X"` is correct. `"\"=js:$vars.X\""` is a string containing the prefix.

---

## Why The Engine Works This Way

The flow-workbench serializer (`expression-transform.ts`) walks every string in node data and rewrites `$vars` → `vars` so the BPMN runtime sees engine-form tokens. It does **not** check for the `=js:` prefix when doing this rewrite — the prefix is what tells the BPMN engine to actually evaluate the result as JavaScript. Without it, the BPMN engine treats the string as a literal value and binds it to the activity input as-is.

For variable updates only, `bpmn-moddle.ts` has a fallback (`ensureJsPrefix`) that warns and auto-prefixes. There is **no equivalent fallback for connector/HTTP activity inputs** — values pass through verbatim. Always include `=js:` explicitly.

---

## Validation Tip

When debugging a flow whose output is the literal string `vars.X.output.Y` (or `nodes.X.output.Y`, or any other unevaluated expression) instead of the expected value:

1. Open the `.flow` file
2. Search for the literal token in the failed field — `grep '"vars\.' <project>.flow` or `grep '"\$vars\.' <project>.flow`
3. For each match in `bodyParameters`, `queryParameters`, `pathParameters`, end-node `source`, or any value field, prepend `=js:`
4. Re-run `uip maestro flow validate` and re-debug
