# Expressions & Context

API workflows use **JavaScript** for all expressions (`evaluate.language: "javascript"`, `evaluate.mode: "strict"`).

## Available Scopes

| Scope | Source | Lifetime |
|-------|--------|----------|
| `$workflow.input` | The workflow's input arguments (from `--input-arguments` JSON or caller). Constant for the entire run. | Workflow run |
| `$workflow` | Workflow runtime info: `{ id, definition, input, startedAt }`. Use `$workflow.input` to read inputs. | Workflow run |
| `$input` | The **current task's input** = the previous task's `$output`. **NOT the workflow's input arguments.** Only equals workflow input on the very first task. | Per-task |
| `$context` | Mutable shared state: `$context.variables.<name>`, `$context.outputs.<TaskName>` | Workflow run |
| `$output` | The current task's raw output. | This task only |
| Loop bindings | `${$currentItem}`, `${$currentItemIndex}` (note the `$` prefix — `for.each: "currentItem"` binds the global as `$currentItem`, with the `$` literal in the identifier name) | Inside the loop body |
| Catch binding | `${$error}` — `catch.as: "error"` binds the global as `$error` (note the `$` prefix, same convention as loop iterators). Reference fields like `${$error.title}` / `${$error.detail}` / `${$error.originatingTaskName}`. | Inside `catch.do` |

> ⚠️ **Critical:** `$input` inside a JS_Invoke that runs *after* other tasks does NOT contain the workflow's input arguments — it contains the previous task's output. To read workflow inputs reliably from anywhere, use `$workflow.input.<name>`.

## Expression Syntax

| Form | Meaning |
|------|---------|
| `"plain string"` | Literal string. |
| `"${expr}"` | Single expression — result replaces the string. |
| `"prefix-${expr}-suffix"` | String interpolation. |
| `"${{ key: value }}"` | Object literal expression (note: double braces). |

Examples:
```json
"url":       "${\"https://api.example.com/users/\" + $workflow.input.userId}"
"body":      { "name": "${$workflow.input.name}" }
"arguments": "${{ \"$context\": $context, \"$workflow\": $workflow, \"$input\": $input }}"
```

## Expression Patterns

### Variable Access

```javascript
// Read a variable
${$context.variables.myVar}

// Read with null safety
${$context.variables?.myVar ?? "default"}
```

### Output Access

```javascript
// Read activity output
${$context.outputs.Javascript_1}

// Read nested property
${$context.outputs.Javascript_1.totalAmount}

// Read with null safety
${$context.outputs?.Javascript_1?.items ?? []}
```

### Input Access

```javascript
// Read workflow input from anywhere — preferred
${$workflow.input.fieldName}

// Read task input — only equals workflow input on the very first task
${$input.fieldName}
```

### Common Idioms

```javascript
// String concatenation
${"Hello, " + $context.variables.name}

// Ternary
${$context.variables.count > 0 ? "has items" : "empty"}

// Array length
${$context.outputs.Javascript_1.items.length}

// JSON stringify
${JSON.stringify($context.outputs.Javascript_1)}

// Type coercion
${Number($context.variables.countStr)}
${String($context.variables.count)}
```

## The `export.as` Pattern

Each task's raw output is in `$output`. To make it available to later tasks, you must `export` it back into `$context`. Two patterns by category:

| Category | Activities | Export Pattern |
|----------|-----------|----------------|
| **Variables** | Assign | `{ ...$context, variables: { ...$context.variables, ...$output } }` |
| **Outputs** | Everything else (JS_Invoke, If, ForEach, DoWhile, TryCatch, Response, Wait) | `{ ...$context, outputs: { ...$context?.outputs, "ActivityKey": $output } }` |

### Output key

The output key in the export pattern matches the activity key as-is. Activity key `Javascript_1` → export key `"Javascript_1"`. Read it back the same way: `$context.outputs.Javascript_1`.

### Without `export`

If you omit `export`, the task's output disappears from context after the next task. Only `$output` (the most recent task's output) is reliably visible. Always `export` unless you specifically want the output discarded.

## Reading Prior Outputs

```js
// Javascript_1 returned { tier: "GOLD", credits: 1500 }
$context.outputs.Javascript_1.tier

// Inside a JS_Invoke script — $context is a global:
"code": "return { greeting: 'Hello ' + $context.outputs.Javascript_1.tier };"
```

## Reading Workflow Inputs

```js
// User ran: uip api-workflow run wf.json --input-arguments '{"name":"Alice","count":3}'

$workflow.input.name    // "Alice"
$workflow.input.count   // 3
```

`$workflow.input` is bound at workflow start and never changes. Use `$workflow.input.<name>` everywhere — including inside JS_Invoke, where it's also a global.

If the input is missing, `$workflow.input.<name>` is `undefined`. Provide defaults via `document.metadata.variables.schema.document.properties.<name>.default` — `WorkflowStart` hydrates these into `$context.variables` automatically.

## JS_Invoke Context Access

Scripts read `$context`, `$workflow`, `$input` directly as globals.

```js
// Inside a JsInvoke script:
const userName = $context.variables.userName;
const inputArg = $workflow.input.userId;
return { upper: userName.toUpperCase(), id: inputArg };
```

The task body's `run.script.arguments` field — the standard `"${{ \"$context\": $context, \"$workflow\": $workflow, \"$input\": $input }}"` block — is StudioWeb designer scaffolding. Keep it for designer roundtrip; the runtime ignores it.

## Strict Mode Gotchas

`evaluate.mode: "strict"` enforces strict JavaScript:

- Accessing a property on `undefined` throws — always use optional chaining (`?.`)
- Use `?? "default"` for null coalescing
- Array spread on `undefined` throws — guard with `?? []`
- `with` statements rejected
- Duplicate property names rejected in object literals
- Implicit globals rejected — use `const` / `let` inside scripts

```js
// Safe nested access:
${$context.outputs?.Javascript_1?.items ?? []}

// Inside ForEach over a possibly-missing array:
"in": "${$context.outputs?.Javascript_1?.items ?? []}"
```

## Key Patterns

### Globally Unique Keys

Every key in the workflow must be globally unique, including suffixes:
- Activity keys: `Assign_1`, `Javascript_1`, `Wait_1`, `Try_Catch_1`
- Wrapper suffixes: `If_1#Wrapper`, `If_1#Then`, `If_1#Else`
- Body suffixes: `For_Each_1#Body`, `Do_While_1#Body`

When adding activities, scan existing keys to avoid collisions. Increment the number suffix.

### Export Merging

Exports use spread to preserve existing context while adding new data:
```javascript
// Preserves all existing outputs and adds/overwrites the specific activity output
{ ...$context, outputs: { ...$context?.outputs, "ActivityKey": $output } }
```

The `?.` on `$context?.outputs` prevents errors when no outputs exist yet.

### Wrapper Pattern (If)

The If activity uses a wrapper because the designer needs a single container:
1. `If_N#Wrapper` — outer container with export and metadata
2. `If_N` — inner switch with condition logic
3. `If_N#Then` — true branch with `then: "exit"`
4. `If_N#Else` — false branch with `then: "exit"`

`then: "exit"` on branches prevents fall-through to the next branch.

### Body Pattern (Loops)

ForEach and DoWhile both wrap their inner activities in a `#Body`:
- `For_Each_N#Body` — index-aware accumulation pattern (resets `results` array on iteration 0)
- `Do_While_N#Body` — simple accumulation pattern (no reset, since iteration count is condition-driven)

See [task-types.md](task-types.md) for the exact body export expressions.

### Context Chaining

Activities execute sequentially. Each activity's export updates `$context`, making its output available to subsequent activities:

```
WorkflowStart       → sets $context.variables (from variable defaults)
Assign_1            → updates $context.variables (e.g. classifies the input)
For_Each_1          → adds $context.outputs.For_Each_1.results (per-iteration accumulation)
Javascript_1        → adds $context.outputs.Javascript_1 (final summary computation)
Response_1          → reads any $context data, ends workflow
```

## Anti-patterns

- **Do NOT** use `$input.<name>` to read workflow inputs from non-first tasks — `$input` is the previous task's `$output`. Use `$workflow.input.<name>`.
- **Do NOT** mutate `$context` directly inside a JS_Invoke script — return a new value and let `export.as` merge it.
- **Do NOT** rely on `$output` two tasks later — it is overwritten by the next task. Always `export` to `$context.outputs.<TaskName>` if you need it.
- **Do NOT** use `var` inside JS_Invoke scripts — strict mode rejects implicit globals; use `const` / `let`.
- **Do NOT** wrap loop variable names (`each`, `at`) in `${...}` — those fields take plain identifiers.
- **Do NOT** mix `${...}` and string concatenation when a single expression form works: prefer `"${\"prefix-\" + $workflow.input.x}"` over splitting.
