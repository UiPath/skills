# Task Types Reference

Detailed reference for the activity types supported in the API Workflow DSL — focused on logical/structural building blocks. Each section: required fields, export pattern, metadata, minimal JSON, common mistakes, and where applicable, nesting examples.

| Type | Action selector | Purpose |
|------|-----------------|---------|
| Sequence | `do` | Group child tasks |
| Assign | `set` | Set or update workflow variables |
| JavaScript (JsInvoke) | `run.script` | Run inline JavaScript |
| If | `switch` (inside `#Wrapper`) | Conditional branching |
| ForEach | `for.each` / `for.in` / `for.at` | Iterate over a collection |
| DoWhile | `for.in` + `doWhile` | Repeat-until loop |
| Break | `break: "true"` | Exit nearest loop early |
| TryCatch | `try` + `catch` | Error handling |
| Wait | `wait` | Pause execution |
| Response | `response` + `then: "end"` | Return result and end the workflow |

> **HTTP / Connector activities are intentionally not covered by this skill.** They require StudioWeb-side editor metadata (`metadata.configuration` essential blob + a real connection UUID) that the CLI cannot generate cleanly today. Workflows that need outbound calls should be authored in StudioWeb and merged in. See [troubleshooting.md](troubleshooting.md) for context.

The `metadata.activityType` MUST match the type name above for designer roundtrip and executor dispatch.

For deeply nested patterns (If-in-loop, TryCatch-around-loop, conditional Break, etc.), see [control-flow-patterns.md](control-flow-patterns.md).

---

## 1. Sequence

Groups child tasks. Root of every workflow is `Sequence_1`.

```json
{
  "Sequence_1": {
    "do": [
      { "WorkflowStart": { /* system activity */ } },
      { "Task_A": { /* ... */ } },
      { "Task_B": { /* ... */ } }
    ],
    "metadata": { "activityType": "Sequence", "displayName": "Sequence", "fullName": "Sequence" }
  }
}
```

Child tasks execute in order. `$context` flows between them via `export.as`.

---

## 2. Assign

Sets the value of **one** workflow variable. Output merges into `$context.variables`.

**Required fields:** `set` (single key), `export.as` (variables pattern), `metadata.activityType: "Assign"`, `metadata.isTransparent: false`

**Critical:** Each Assign MUST set exactly ONE variable. StudioWeb's designer collapses multi-key `set` blocks to one key on save, silently dropping the rest — see SKILL.md critical rule 6 and the StudioWeb roundtrip section in [troubleshooting.md](troubleshooting.md). To update N variables, use N sequential Assigns.

**String literals MUST be wrapped:** `"${'literal'}"` (a JS string inside an expression). Plain `"literal"` runs locally but StudioWeb rewrites it to `${literal}` on save → ReferenceError at runtime. See SKILL.md critical rule 5.

**Export pattern:**
```
{ ...$context, variables: { ...$context.variables, ...$output } }
```

**Minimal JSON:**
```json
{
  "Assign_1": {
    "set": { "userName": "${'John Doe'}" },
    "export": { "as": "{ ...$context, variables: { ...$context.variables, ...$output } }" },
    "metadata": { "activityType": "Assign", "displayName": "Set User Name", "fullName": "Assign", "isTransparent": false }
  }
}
```

**Updating multiple variables — chain single-key Assigns inside the parent `do` array:**
```json
"do": [
  { "Assign_UserName": { "set": { "userName": "${'John Doe'}" }, "export": { "as": "{ ...$context, variables: { ...$context.variables, ...$output } }" }, "metadata": { "activityType": "Assign", "displayName": "Set User Name", "fullName": "Assign", "isTransparent": false } } },
  { "Assign_Count":    { "set": { "count":    0 },               "export": { "as": "{ ...$context, variables: { ...$context.variables, ...$output } }" }, "metadata": { "activityType": "Assign", "displayName": "Reset Count",  "fullName": "Assign", "isTransparent": false } } }
]
```

Numbers, booleans, and already-wrapped expressions (`"${$context.variables.X + 1}"`) need no extra wrapping — only bare string literals do.

**Common mistakes:**
- Multi-key `set` (e.g. `"set": { "userName": "...", "count": 0 }`) — survives `uip api-workflow run`, but StudioWeb's designer drops all but one key on save
- Bare string literals (e.g. `"set": { "tier": "GOLD" }`) — StudioWeb rewrites to `${GOLD}` on save → ReferenceError
- Setting `isTransparent: true` (only `WorkflowStart` uses `true`)
- Using outputs export pattern instead of variables pattern
- Forgetting `${...}` wrapper on expression values: `"${$input.value}"` not `"$input.value"`

---

## 3. JavaScript (JsInvoke)

Runs inline JavaScript. **Access context via `$context`, `$workflow`, `$input` as globals** — they are bound on `globalThis` before the script runs. `arguments` is empty (`arguments.length === 0`); do NOT try `arguments[0]`. Empirically verified against `@uipath/api-workflow-executor` 12.10.2 and 12.12.2.

**Required fields:** `run.script.code`, `run.script.language` (`"javascript"`), `run.script.arguments`, `export.as`, `metadata`

The `run.script.arguments` field is required by StudioWeb's designer for roundtrip but is **not read by the runtime**. Keep it as the standard block: `"${{ \"$context\": $context, \"$workflow\": $workflow, \"$input\": $input }}"`.

**Export pattern:**
```
{ ...$context, outputs: { ...$context?.outputs, "Javascript_N": $output } }
```

**Minimal JSON:**
```json
{
  "Javascript_1": {
    "run": {
      "script": {
        "code": "return $context.variables.userName.toUpperCase();",
        "language": "javascript",
        "arguments": "${{ \"$context\": $context, \"$workflow\": $workflow, \"$input\": $input }}"
      }
    },
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"Javascript_1\": $output } }" },
    "metadata": { "activityType": "JsInvoke", "displayName": "JavaScript", "fullName": "JsInvoke" }
  }
}
```

Inside the script, reference globals directly: `$context.variables.X`, `$context.outputs.X`, `$workflow.input.X`. Loop and catch bindings get a literal `$` prefix in the identifier name — `for.each: "currentItem"` is read as `$currentItem`, `for.at: "currentItemIndex"` as `$currentItemIndex`, `catch.as: "error"` as `$error`. Forgetting the `$` produces `<name> is not defined`.

**Common mistakes:**
- `language: "js"` instead of `"javascript"`
- Trying to use `arguments[0]` — the runtime does NOT pass arguments. Use globals.
- Reading workflow inputs as `$input.<name>` from a non-first script — `$input` is the previous task's output. Use `$workflow.input.<name>`.
- Missing `return` — script must return a value
- Using `var` — strict mode rejects implicit globals; use `const` / `let`

---

## 4. If (Switch Wrapper)

Conditional branching. Requires a `#Wrapper` container with `#Then` and `#Else` branches.

**Structure:** `If_N#Wrapper` contains: `If_N` (switch) + `If_N#Then` (true branch) + `If_N#Else` (false branch)

**Export pattern (on `#Wrapper`):**
```
{ ...$context, outputs: { ...$context?.outputs, "If_N": $output } }
```

**Minimal JSON:**
```json
{
  "If_1#Wrapper": {
    "do": [
      {
        "If_1": {
          "switch": [
            {
              "case": {
                "when": "${$context.variables.amount > 1000}",
                "then": "If_1#Then"
              }
            },
            { "default": { "then": "If_1#Else" } }
          ],
          "metadata": { "displayName": "If" }
        }
      },
      {
        "If_1#Then": {
          "do": [],
          "then": "exit"
        }
      },
      {
        "If_1#Else": {
          "do": [],
          "then": "exit"
        }
      }
    ],
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"If_1\": $output } }" },
    "metadata": { "activityType": "If", "displayName": "If", "fullName": "If" }
  }
}
```

**Common mistakes:**
- Missing `#Wrapper` suffix on the outer container
- Missing `then: "exit"` on `#Then` and `#Else` branches (causes fall-through)
- Condition not wrapped in `${...}` (e.g., `$context.variables.x > 5` instead of `${$context.variables.x > 5}`)
- Missing `metadata` on the inner `If_N` switch element

**Nesting:**
- An `If` placed **inside another If's `#Then` or `#Else`** must use its OWN unique number suffix — e.g., `If_2#Wrapper` / `If_2#Then` / `If_2#Else`. Do NOT reuse `If_1#Then` for an inner If's branch — keys are globally unique across the whole workflow.
- An `If` placed inside a loop's `#Body` is fine. The wrapper still has the standard `export.as`. Loop iteration variables are usable in the `when` expression with the `$` prefix: `"when": "${$currentItem.priority === 'high'}"`.
- Multi-way branching: add more `case` entries before `default`. First match wins.
  ```json
  "switch": [
    { "case": { "when": "${$context.variables.x > 100}", "then": "If_1#Then" } },
    { "case": { "when": "${$context.variables.x > 50}",  "then": "If_1#Else" } },
    { "default": { "then": "If_1#Else" } }
  ]
  ```
  For more than two branches, you generally chain Ifs (one per cutoff) rather than packing many cases — StudioWeb's designer renders true two-way If cleanly.

---

## 5. ForEach

Iterates over a collection. Requires `#Body` inside `do`.

**Required fields:** `for.each` (iterator name, plain string), `for.in` (expression), `for.at` (index name, plain string), `do` (with `#Body`), `output.as`, `metadata`

**Body export pattern (index-aware accumulation):**
```
{ ...$context, outputs: { ...$context?.outputs, "For_Each_N": { ...$context?.outputs?.For_Each_N, results: [ ...($currentItemIndex == 0 ? [] : ($context?.outputs?.For_Each_N?.results ?? [])), ...([$output] ?? []) ] } } }
```

**Output pattern:** `${$context.outputs.For_Each_N}`

**Minimal JSON:**
```json
{
  "For_Each_1": {
    "for": {
      "each": "currentItem",
      "in": "${$input.items}",
      "at": "currentItemIndex"
    },
    "do": [
      {
        "For_Each_1#Body": {
          "do": [],
          "export": {
            "as": "{ ...$context, outputs: { ...$context?.outputs, \"For_Each_1\": { ...$context?.outputs?.For_Each_1, results: [ ...($currentItemIndex == 0 ? [] : ($context?.outputs?.For_Each_1?.results ?? [])), ...([$output] ?? []) ] } } }"
          }
        }
      }
    ],
    "output": { "as": "${$context.outputs.For_Each_1}" },
    "metadata": { "activityType": "ForEach", "displayName": "For Each", "fullName": "ForEach" }
  }
}
```

Inside the body, the iterator and index are accessible as globals **with a `$` prefix**: `${$currentItem}`, `${$currentItemIndex}`. **NOT** `${currentItem}` (unprefixed — undefined) and **NOT** `${$context.variables.currentItem}` (those names aren't in `$context.variables`).

**Common mistakes:**
- Missing `#Body` suffix
- Wrapping `each` or `at` in `${...}` — they are plain variable names, not expressions
- Missing `for.at`
- Wrong body export pattern (must use the index-aware reset shown above, not the simpler DoWhile pattern)

**Nesting:**
- Each ForEach activity's iterator and index variable names are scoped to that loop. Inner loops MUST use distinct names — e.g. outer `for.each: "outerItem"` / inner `for.each: "innerItem"`. Reusing `currentItem` in both loops shadows the outer one.
- An `If`, another `ForEach`, a `DoWhile`, or a `TryCatch` placed inside a `#Body` is fine — drop them into the body's `do` array. Each gets its own `export.as` as usual; the body's outer `export.as` (the index-aware accumulation) is unchanged.
- The body's accumulation export merges per-iteration `$output` into `$context.outputs.For_Each_N.results`. If you want per-iteration data, capture it via Assign / JsInvoke inside the body — those activities' `$output` become the body's per-iteration `$output`.

---

## 6. DoWhile

Repeat-until loop. Body always executes at least once.

**Required fields:** `for.in` (always `"${ [1] }"`), `doWhile` (condition), `do` (with `#Body`), `output.as`, `metadata`

**Body export pattern (simple accumulation, no index reset):**
```
{ ...$context, outputs: { ...$context?.outputs, "Do_While_N": { ...$context?.outputs?.Do_While_N, results: [ ...($context?.outputs?.Do_While_N?.results ?? []), ...([$output] ?? []) ] } } }
```

**Minimal JSON:**
```json
{
  "Do_While_1": {
    "for": { "in": "${ [1] }" },
    "doWhile": "${$context.variables.counter < 10}",
    "do": [
      {
        "Do_While_1#Body": {
          "do": [],
          "export": {
            "as": "{ ...$context, outputs: { ...$context?.outputs, \"Do_While_1\": { ...$context?.outputs?.Do_While_1, results: [ ...($context?.outputs?.Do_While_1?.results ?? []), ...([$output] ?? []) ] } } }"
          }
        }
      }
    ],
    "output": { "as": "${$context.outputs.Do_While_1}" },
    "metadata": { "activityType": "DoWhile", "displayName": "Do While", "fullName": "DoWhile" }
  }
}
```

The body MUST update the condition variable, otherwise the loop runs forever.

**Common mistakes:**
- Using a real collection for `for.in` instead of `"${ [1] }"`
- Missing `#Body` suffix
- Body does not update the `doWhile` condition variable → infinite loop
- Missing `output.as` on the loop itself

**Nesting:**
- A DoWhile placed inside a ForEach `#Body` (or vice versa) is fine. Each loop's body has its own `export.as`; they don't interfere.
- The condition variable should usually be a workflow-level variable (declared in `document.metadata.variables.schema.document.properties`) so it persists across iterations. Updating it inside `#Body` requires an Assign with the variables export pattern.
- Beware: `doWhile` is evaluated AFTER each iteration. The body always runs at least once. If you need pre-condition checking ("while", not "do-while"), wrap the body in an `If` whose `#Else` exits via `Break`.

---

## 7. Break

Exits a loop early. Only valid inside `For_Each_N#Body` or `Do_While_N#Body`.

**Required fields:** `break: "true"` (string!), `then: "exit"`, `set: "${$input}"`, `metadata`

**Minimal JSON:**
```json
{
  "Break_1": {
    "break": "true",
    "then": "exit",
    "set": "${$input}",
    "metadata": { "activityType": "Break", "displayName": "Break", "fullName": "Break" }
  }
}
```

Typically wrapped in an `If` inside the body — break only when a condition is met.

**Common mistakes:**
- Boolean `true` instead of string `"true"` (must be a JSON string)
- Placing Break outside a loop `#Body`
- Missing `set: "${$input}"` (required for context propagation)

**Scoping:**
- Break exits **only the innermost enclosing loop**. To exit an outer loop from inside a nested loop, set a flag variable (Assign) before Break, then check the flag in the outer loop's `doWhile` (or in an `If` after the inner loop) and Break again.
- Break inside a `TryCatch.catch.do` works as long as the TryCatch itself is inside a loop body — Break still targets the loop, not the catch. The catch is not a loop scope.
- Conditional Break: wrap Break in an `If` so it only fires when needed:
  ```
  ForEach_1#Body
    └─ If_1#Wrapper
         ├─ If_1 (when: ${$currentItem.done})
         ├─ If_1#Then → [ Break_1 ]
         └─ If_1#Else → [ /* keep iterating */ ]
  ```

---

## 8. TryCatch

Wraps activities in error handling.

**Required fields:** `try` (array of activities), `catch.as` (error variable name), `catch.do` (array of error-handling activities), `export.as`, `metadata`

**Export pattern:**
```
{ ...$context, outputs: { ...$context?.outputs, "Try_Catch_N": $output } }
```

**Minimal JSON:**
```json
{
  "Try_Catch_1": {
    "try": [
      {
        "Javascript_1": { "run": { "script": { "code": "if ($context.variables.amount < 0) throw new Error('negative'); return $context.variables.amount * 2;", "language": "javascript", "arguments": "${{ \"$context\": $context, \"$workflow\": $workflow, \"$input\": $input }}" } }, "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"Javascript_1\": $output } }" }, "metadata": { "activityType": "JsInvoke", "displayName": "Risky Compute", "fullName": "JsInvoke" } }
      }
    ],
    "catch": {
      "as": "error",
      "do": [
        {
          "Assign_2": {
            "set": { "errorMsg": "${$error.title}" },
            "export": { "as": "{ ...$context, variables: { ...$context.variables, ...$output } }" },
            "metadata": { "activityType": "Assign", "displayName": "Set Error", "fullName": "Assign", "isTransparent": false }
          }
        }
      ]
    },
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"Try_Catch_1\": $output } }" },
    "metadata": { "activityType": "TryCatch", "displayName": "Try Catch", "fullName": "TryCatch" }
  }
}
```

`catch.as` is the variable name bound to the caught error inside `catch.do`. Reference it with the `$` prefix: `${$error.title}` (or `${$<your-name>.title}` if you used a different `as`).

The bound value is a **ProblemDetails-shaped object**, NOT a JavaScript Error. Useful keys:
- `$error.title` — short message (e.g., `"Worker operation failed: <user error message>"`)
- `$error.detail` — full detail including stack trace
- `$error.status` — HTTP-style status code (`500` for runtime errors, `400` for validation)
- `$error.originatingTaskName` — which task threw
- `$error.type` — RFC 7807 error type URL

There is **no** `.message` / `.name` / `.stack` property — those would return `undefined`. Always use `.title` or `.detail` for the human-readable text.

**Common mistakes:**
- Missing `catch.as`
- Empty `catch.do` without any error handling
- Forgetting the export on the TryCatch wrapper itself

**Nesting:**
- **TryCatch around a loop:** wraps the entire loop. If any iteration throws, the loop stops and execution jumps to `catch.do`. Use this when one bad item should abort the whole batch.
- **TryCatch inside a loop body:** each iteration gets its own try/catch. A failure in one iteration is caught locally; the loop continues to the next iteration. Use this for "skip and continue on error" semantics — the more common pattern.
- **TryCatch inside a TryCatch:** legal. Inner catch fires first; if the inner catch itself throws, the outer catch fires. Use sparingly — usually a single TryCatch is enough.
- **Catch can contain control flow:** `catch.do` may include Assigns, JsInvokes, Ifs, even nested TryCatches. It does NOT include the loop/break that surrounds it — Break inside a catch still targets the enclosing loop.
- **Keys must stay unique** across `try` and `catch.do`. The error variable (`catch.as`) is scoped to `catch.do` only — outside the catch, it's gone (you'll need to capture it into a workflow variable via Assign if you want it later).

---

## 9. Wait

Pauses execution.

**Required fields:** `wait` (object with time fields), `export.as`, `metadata`

**Export pattern:**
```
{ ...$context, outputs: { ...$context?.outputs, "Wait_N": $output } }
```

**Minimal JSON:**
```json
{
  "Wait_1": {
    "wait": { "minutes": 0, "seconds": 5, "milliseconds": 0 },
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"Wait_1\": $output } }" },
    "metadata": { "activityType": "Wait", "displayName": "Wait", "fullName": "Wait" }
  }
}
```

Provide all three time fields — set unused ones to `0`.

---

## 10. Response

Returns a result and ends the workflow execution path.

**Required fields:** `response` (single expression string), `markJobAsFailed` (boolean, sibling of `response`), `then: "end"`, `export.as`, `metadata`

**Critical (StudioWeb roundtrip):** `response` MUST be a **single expression string**. For object-valued returns, use the `${{ ... }}` (double-brace) object-literal expression form, NOT a JSON object with `${...}` fields. The JSON-object form is corrupted by StudioWeb's designer on save (issue **SW-28452** / [UiPath/cli#1537](https://github.com/UiPath/cli/issues/1537)) — each field becomes the literal text of its expression instead of the evaluated value. See SKILL.md critical rule 15 and the [troubleshooting entry](troubleshooting.md#object-valued-response-gets-corrupted-fields-evaluate-to-literal-expression-text-sw-28452--cli1537).

**Export pattern:**
```
{ ...$context, outputs: { ...$context?.outputs, "Response_N": $output } }
```

**Minimal JSON — object payload (use this for multi-field returns):**
```json
{
  "Response_1": {
    "response": "${{ result: $context.outputs.Javascript_1, status: 'success' }}",
    "markJobAsFailed": false,
    "then": "end",
    "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"Response_1\": $output } }" },
    "metadata": { "activityType": "Response", "displayName": "Response", "fullName": "Response" }
  }
}
```

Inside the outer `${{ ... }}` you're already in JS expression scope. Reference rules:
- Unquoted keys are valid identifiers (`result:`, `status:`)
- Variables/outputs evaluate directly without inner `${...}`: `$context.variables.X`, `$context.outputs.Y`, `$workflow.input.Z`
- String literals use single quotes: `status: 'ok'` (single quotes avoid JSON escaping)
- Numbers/booleans are bare: `count: 0`, `flag: true`
- The whole thing is one expression — adding inner `${...}` re-triggers the SW-28452 corruption

**Single-value response (one variable or one expression):**
```json
"response": "${$context.outputs.Javascript_1}"
```
or
```json
"response": "${'done'}"
```
The simple single-expression form is fine; the SW-28452 issue only affects object payloads.

**Common mistakes:**
- **Object payload with `${...}` fields** (`"response": { "tier": "${$context.variables.tier}" }`) — runs locally, corrupted by StudioWeb on save. Use single-expression `${{ ... }}` instead.
- Missing `then: "end"` — workflow does not terminate
- Nesting `markJobAsFailed` inside `response` — it MUST be a sibling
- Placing Response in the middle of a sequence — it should be at the end of an execution path
- Using legacy `set: <object>` form instead of `response` + `then: "end"` — runtime accepts it but designer roundtrip breaks
