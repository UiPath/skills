# Bindings & Expressions Reference

How to wire values into task inputs — expression prefixes, cross-task output references, and direct JSON editing.

## Two Binding Modes

Every task input is wired using one of two modes. Pick based on the source of the value.

| Mode | Canonical form | Implementation |
|------|----------------|----------------|
| **Literal or expression** | `input = "<value>"` | Write `"<value>"` to `task.data.inputs[i].value` in caseplan.json |
| **Cross-task reference** | `input <- "Stage"."Task".output` | Resolve the source's output reference ID → write `"=vars.<outputReferenceId>"` to target input's `value` |

For the full JSON shapes and binding procedure, see [plugins/variables/io-binding/impl-json.md](plugins/variables/io-binding/impl-json.md).

For connector tasks, input values are written directly to `caseplan.json` — see [plugins/tasks/connector-activity/impl-json.md](plugins/tasks/connector-activity/impl-json.md).

## Expression Prefixes

When using the literal/expression mode, the `--value` string can start with one of these prefixes to resolve dynamically at runtime. Plain strings without a prefix are treated as literals.

| Prefix | Meaning | Example |
|--------|---------|---------|
| `=metadata.` | Case metadata field — closed schema, see [case-schema.md § 1](case-schema.md#1-top-level--metadata). NOT for arbitrary SDD "Case Metadata" business fields (e.g. Priority) — those are case variables, use `=vars.<id>` | `=metadata.ExternalId` |
| `=js:` | Inline JavaScript expression | `=js:new Date().toISOString()` |
| `=vars.` | Case-level variable | `=vars.inbox_config` |
| `=bindings.` | Resource binding (connection, queue, trigger) | `=bindings.slackConnection` |
| `=datafabric.` | Data Fabric entity field | `=datafabric.Customer.id` |
| `=orchestrator.JobAttachments` | Orchestrator job attachments | `=orchestrator.JobAttachments[0]` |
| `=response` | The response object from a previous HTTP step | `=response.body` |
| `=result` | The result of the previous task | `=result.status` |
| `=Error` | Error object from a failed step | `=Error.message` |
| `=jsonString:` | Serialize the following expression to a JSON string | `=jsonString:vars.config` |

> Plain strings (no prefix) are literal values. `"hello"` is literally the string `hello`, not an expression.

> The prefix tells you WHAT the value refers to. The **sink** tells you HOW to wrap it — see [§ Canonical form per sink](#canonical-form-per-sink) below.

> **Variable / binding ids are always letter-leading.** Formal-arg slots use a `v` prefix, bindings use `b`, and companion ids inherit the (letter-leading) variable name — so `<id>` in `=vars.<id>` / `=bindings.<id>` is always a valid C# identifier. Dot notation is always safe; bracket notation (`vars["…"]`) is never needed. A digit-leading id would fail the case BPMN with `illegal ID` — see [global-vars § Formal-arg slot ID format](plugins/variables/global-vars/impl-json.md#formal-arg-slot-id-format).

## Canonical form per sink

Every `=`-prefixed value in `caseplan.json` is dispatched to one of two runtime evaluators based on the sink it lands in. **The wrap form must match the sink** — wrong wrap is a silent runtime fault (the literal string arrives at the consumer instead of the resolved value).

### Two evaluator paths

| Path | Trigger | Capabilities |
|---|---|---|
| **Lookup** | Value starts with `=vars.<id>` or `=bindings.<id>` | Strip prefix, look up by id, return value. NO operators, NO dotted access, NO `=metadata.` |
| **JS eval** | Value starts with `=js:<expr>` | Full JS evaluation. Predefined namespaces: `vars`, `response`, `bindings`, `iterator`, `metadata`. Operators, function calls, dotted access all work. **A condition / rule `conditionExpression` can reference only case variables (`vars.X`) and `metadata`** — there is no `event` namespace (referencing `event` errors with "event not found"). For event-payload gating: in-rule extract-then-gate (extract `response.X -> caseVar` AND gate `=js:vars.caseVar…` on the SAME rule) is **NOT supported at runtime** — the case-backend evaluates the gate against the pre-extract value. Place the case-state gate on the DOWNSTREAM stage-entry / task-entry condition that follows the connector rule. |

`data.inputs[].value` on non-connector tasks runs **lookup** when the value matches `^=vars\.\w+$` or `^=bindings\.\w+$`; **JS eval** otherwise. Connector body fields, filter expressions, and condition expressions ALL run **JS eval** — they require `=js:` wrap regardless of value shape.

### Form by sink (the table)

| Sink | Plain-ref form (when applicable) | Expression form |
|---|---|---|
| **Non-connector task `data.inputs[].value`** | `=vars.<id>` / `=bindings.<id>` (single identifier — no dots, no operators) | `=js:<expr>` (everything else: `=metadata.*`, dotted access, operators, function calls) |
| **Connector body field — dot-notation** (curated connectors) | (no plain branch) | `=js:(<expr>)` — uniform wrap, parens always |
| **Connector trigger filter expression** (`body.filters.expression`) with variable refs | n/a | `` =js:`<JMESPath with ${vars.X} interpolations>` `` |
| **Connector trigger filter expression** plain literal (no variables) | Unwrapped CEQL/JMESPath text | n/a |
| **`conditionExpression`** (stage entry/exit, task entry, case exit, trigger rules) | (no plain branch) | `=js:<expr>` — no outer parens; sub-clauses get manual parens when combining via `&&` / `\|\|` |
| **SLA rule `expression`** | (no plain branch) | `=js:<expr>` (default: `=js:true`) |
| **Task output `source` / `target`** | `=vars.<varId>` / `=<rawFieldName>` | n/a (always plain) |
| **Binding refs in `data.context`, `caseShape.context`** | `=bindings.<id>` | n/a |

> **JIT object mode (out of scope for this version).** When an activity's `inputMetadata.inputMode === "jitObject"` (synthetic HTTP request bodies, generic body-passthrough activities), the whole connector body becomes one `=js:({...})` expression with bare JS variable references inline. The skill currently routes synthetic HTTP through `queryParameters` instead. JIT-mode authoring is not documented in this version.

### Equality operators

In any `=js:` expression use **strict** `===` / `!==`, never loose `==` / `!=`. JS eval coerces types on loose equality (`vars.flag == "true"` is truthy for the string `"true"`), which silently breaks boolean/number routing — and validation passes either way (loose `==` is valid JS), so nothing flags it.

SDD IF columns use natural shorthand — `approved == true`, `status != "done"`. When rewriting into a `conditionExpression` (or any `=js:` sink) you MUST upgrade the operator: `approved == true` → `=js:vars.approved === true`. Do NOT transcribe `==` / `!=` verbatim.

### Null-safe task-output references

A task output is `null` until its task runs — and stays null when its task is adhoc, optional, or skipped, so a task input can hit it as easily as a case-start rule. Only the `=js:` form dereferences, so only it needs a guard.

**`=vars.<id>` — lookup.** A single identifier ([§ Form by sink](#form-by-sink-the-table)): nothing to dereference, no guard. (A dotted `=vars.X.Y` is a different sink — see [io-binding/planning.md § `=` operator](plugins/variables/io-binding/planning.md).)

**`=js:<expr>` — JS eval (Jint, ES2020).** Optional-chain every hop. Unguarded, it throws `Cannot read property 'Y' of null` (or `... of undefined`):

```
=js:vars.X.Y                       ✗  throws while X is null
=js:vars.X?.Y                      ✓

=js:vars.X.Y.Z                     ✗  throws while X or X.Y is null
=js:vars.X?.Y?.Z                   ✓

=js:vars.$xref('Stage','Task','response')?.request_body   ✓  same for a marker
```

`?.` short-circuits to `undefined`, so `vars.X?.Y || <default>` is the way to supply a fallback.

### Conservative rule for `=metadata.X`

The lookup-path resolver has NO `=metadata.` branch — plain `=metadata.X` is NOT resolved at runtime. **Always wrap as `=js:metadata.X`** (or `=js:(metadata.X)` if the sink requires parens). The FE design-time picker may classify `=metadata.X` as "variable" type, but that's a UI hint, not a runtime contract.

`metadata.X` is a **closed field set** — see [case-schema.md § 1](case-schema.md#1-top-level--metadata) for the full list (`caseIdentifier`, `slaRules`, `caseExitRules`, …) plus the platform-only runtime field `metadata.ExternalId`. It is NOT a namespace for arbitrary business data. A field the SDD's "Case Metadata" table lists for human-readability (e.g. `Priority`) is authored as a **case variable**, not a `metadata` key — reference it as `=js:vars.priority`, never `=js:metadata.priority` (which resolves to `undefined`).

### Planner-emit form

The SDD uses SDD-natural references — `=vars.X`, `=metadata.X`, `=bindings.X`, cross-task `<- "Stage"."Task".out` (verbatim, unresolved). Other `=`-prefixed forms (`=response.X`, `=Error.X`, `=datafabric.X`, `=orchestrator.JobAttachments`) also pass through to impl for per-sink wrap; see [Expression Prefixes](#expression-prefixes) for the full set. The implementation step rewrites to the canonical sink form when constructing `caseplan.json`. Detail: [plugins/variables/io-binding/planning.md](plugins/variables/io-binding/planning.md) and each plugin's `impl-json.md`.

## Cross-Task References

Cross-task references wire the output of an earlier task into an input of a later task. The planning syntax uses **names** (human-readable), which the implementation phase resolves to variable IDs via direct JSON lookup.

### Planning syntax (in `sdd.md`)

```
input_name <- "Stage Name"."Task Name".output_name
```

- `Stage Name` — the `display-name` of the containing stage (exactly as written in a `Create stage "<name>"` task)
- `Task Name` — the `display-name` of the source task (exactly as written in an `Add <type> task "<name>"` task)
- `output_name` — a named output field from the source task

### Discovering output names

Run `tasks describe` during planning to list available outputs for a given task type:

```bash
uip maestro case tasks describe --type <type> --id "<taskTypeId>" --output json
uip maestro case tasks describe --type connector-activity --id "<typeId>" --connection-id "<uuid>" --output json
```

Output names appear in the response under the output schema. Record them on the source task's `data.outputs[]` in `caseplan.json` so downstream references can be validated.

### Validation rule

Every cross-task reference in the SDD MUST point to:
1. A stage that exists (created by an earlier `Create stage "..."` task).
2. A task inside that stage that exists (created by an earlier `Add ... task "..." to "<stage>"` task).
3. An output name listed in that task's `outputs:` field.

Missing any of the three → halt planning and ask the user; do not fabricate.

### Implementation translation

The execution phase resolves names to IDs by reading caseplan.json:

```python
# Pseudo-code:
src_stage = find_node_by_label(nodes, "Stage Name")
src_task  = find_task_by_name(src_stage, "Task Name")
src_output = find_output_by_name(src_task, "output_name")
output_reference_id = resolve_output_reference_id(caseplan, src_output)
target_input.value = f"=vars.{output_reference_id}"
# Write updated caseplan.json back to disk
```

See [plugins/variables/io-binding/impl-json.md § Output reference ID](plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative) for the authoritative resolver. It reads a normal / bare / reassigned output's `.id`; only a custom `=` output, which has no `.id`, resolves through its verified root companion's `.id`.

### In-expression references (`vars.$xref(...)`)

Whole-value `<-` (above) resolves only when it IS the entire input value. To reference an upstream task output from **inside** a `=js:` expression — a composite payload, a `conditionExpression`, an SLA `expression`, a computed `=` output — embed a `vars.$xref(...)` marker. This eliminates the "middle variable" that would otherwise exist solely to carry one task's output into a downstream expression.

**Marker form** (quote-safe — single quotes are legal inside a JSON double-quoted value):

```
vars.$xref('Stage Name','Task Name','output_name')
```

- Three args = the same name-triple as whole-value `<-`: source stage `data.label`, source task `displayName`, source output `name`.
- Single quotes ONLY — double quotes break the enclosing JSON string. Names containing a literal `'` are unsupported (re-author the name).
- Drop it anywhere a bare `vars.X` is legal inside an `=js:` expression. It resolves to bare `vars.<outputReferenceId>` (NOT `=vars.` — it is already inside `=js:`).
- Null-guard any dotted access off the resolved reference ([§ Null-safe task-output references](#null-safe-task-output-references)).

**Example** — composite input payload, no middle variables:

```json
"value": "=js:({ approvalDecision: vars.$xref('AP Review','AP lead approval','outcome'), urgentPaymentDecision: vars.$xref('AP Review','Urgent payment','outcome') })"
```

**Resolution** — a single post-pass near the end of Phase 3 (Step 11.5, after conditions and SLA are written) walks every string value in `caseplan.json`, resolves each marker through the common output-reference-ID algorithm, and substitutes `vars.<outputReferenceId>` in place. Because it runs after all outputs are minted and deduped, it reads the real suffixed `.id` (`outcome2`, `data6`) rather than a reassigned output's Case-variable `.var` pointer. An unresolved marker is a build-time ERROR surfaced via **AskUserQuestion** (Check 4), not a silent fail — and `vars.$xref` would throw at runtime too (a method call on `vars`). See [plugins/variables/io-binding/impl-json.md § In-Expression Marker Resolution](plugins/variables/io-binding/impl-json.md#in-expression-marker-resolution-step-115).

> **Additive, not a replacement.** Whole-value `input <- "Stage"."Task".out` resolves to `=vars.<outputReferenceId>` through the same algorithm. The `vars.$xref(...)` marker is only for the in-expression case. Use whole-value `<-` when the output IS the input; use the marker when the output is one term inside a larger `=js:` expression.

## Examples

The blocks below are the **canonical reasoning form** described in [plugins/variables/io-binding/planning.md](plugins/variables/io-binding/planning.md) — a normalized reading of the SDD Inputs/Outputs rows, never written to disk. `registry-resolved.json` records registry lookups only.

### Literal and expression inputs

```text
api-workflow task "Fetch Inbox" in stage "Triage"
- inputs:
  - inbox_config = "=vars.inbox_config"
  - po_patterns  = "=vars.po_patterns"
  - max_results  = "50"
  - requested_at = "=js:new Date().toISOString()"
```

### Cross-task reference

```text
agent task "Classify Emails" in stage "Triage"
- inputs:
  - emails <- "Triage"."Fetch Inbox".emails
  - customer_id <- "Triage"."Fetch Inbox".customer_id
- outputs:
  - category
  - priority_score
```

### Mixed inputs (HITL/action)

```text
action task "Review Classification" in stage "Triage"
- recipient: approver@corp.com
- priority: High
- inputs:
  - classification <- "Triage"."Classify Emails".category
  - priority       <- "Triage"."Classify Emails".priority_score
  - deadline       = "=js:new Date(Date.now() + 86400000).toISOString()"
- outputs:
  - decision
  - comments
```

## Anti-Patterns

- **Mixing `--value` and `--source-*` in the same bind.** The CLI rejects this. Pick one mode per input.
- **Referencing a future task's output.** Cross-task references must target an earlier task in execution order.
- **Fabricating output names.** Always discover via `tasks describe`. A typo becomes a runtime null, not a validation error.
- **Plain-string where expression was intended.** `"metadata.amount"` (no `=`) is the literal string `metadata.amount`, not a reference. Always include the `=` prefix for dynamic values.
- **Nesting expressions inside literals.** `"$metadata.amount"` or `"{{ amount }}"` do not work. Use `=metadata.amount` directly as the full value.
- **Plain `=vars.X` inside connector body JSON.** The runtime does NOT evaluate plain prefix refs in connector body sinks — they arrive at the API as literal strings. Wrap as `=js:(vars.X)`. See [§ Canonical form per sink](#canonical-form-per-sink).
- **Plain `=metadata.X` anywhere.** The lookup-path resolver has no `=metadata.` branch. Always wrap as `=js:metadata.X` (or `=js:(metadata.X)` for connector body / parens-required sinks).
- **Trailing default instead of a guard.** `vars.X.Y || '{}'` guards nothing — the throw lands on `.Y`, before `||` is reached. Guard the object: `vars.X?.Y`.
- **Dotted access via plain prefix.** `=vars.user.email` looks up a variable with id literally `user.email` and fails. Use `=js:vars.user?.email`.
- **`=js:(...)` outer parens on `conditionExpression`.** Conditions use bare `=js:<expr>` per FE convention. Sub-clause parens go inside when combining: `=js:(vars.X) && (vars.Y)` — outer wrap stays bare.
- **Manually building filter-expression strings.** For filter sinks, author a structured FilterTree with `isLiteral: true` values when possible. Variable-bearing filters use `` =js:`<template>` `` with `${vars.X}` interpolations — see [connector-trigger-planning.md](connector-trigger-planning.md).

<!-- END: bindings-and-expressions.md -->
