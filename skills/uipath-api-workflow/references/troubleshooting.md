# Troubleshooting

Common failure modes when authoring, running, packaging, or publishing API workflows. Organized by category — each entry: symptom → cause → fix.

## Structure Pitfalls

### Missing `#Wrapper` on If activity
- **Symptom:** Validation error about invalid If structure or missing container
- **Cause:** If activity placed directly without the `If_N#Wrapper` outer container
- **Fix:** Wrap with `If_N#Wrapper` containing the switch `If_N`, `If_N#Then`, and `If_N#Else` as children

### Missing `#Body` on loop
- **Symptom:** ForEach or DoWhile validation error; loop body not recognized
- **Cause:** Loop `do` array contains activities directly instead of inside a `#Body` element
- **Fix:** Wrap loop contents in `For_Each_N#Body` or `Do_While_N#Body` with proper export pattern

### Missing `then: "exit"` on If branches
- **Symptom:** Activities after If execute twice or unexpected fall-through
- **Cause:** `#Then` and `#Else` branches missing `"then": "exit"`
- **Fix:** Add `"then": "exit"` to both `If_N#Then` and `If_N#Else`

### Duplicate activity keys
- **Symptom:** Validation error about duplicate keys; only one activity rendered in designer
- **Cause:** Two activities share the same key (e.g., two `Assign_1`)
- **Fix:** Every key must be globally unique. Increment the suffix number.

### Missing `WorkflowStart`
- **Symptom:** Variables not initialized; `$context.variables` is undefined
- **Cause:** `WorkflowStart` activity removed or not included as first activity in `Sequence_1`
- **Fix:** Always include `WorkflowStart` as the first activity with `isTransparent: true`. See [workflow-file-format.md](workflow-file-format.md#workflowstart--system-activity).

### Missing `evaluate` block
- **Symptom:** Expressions not evaluated; workflow behaves unexpectedly
- **Cause:** `"evaluate": { "mode": "strict", "language": "javascript" }` block missing from root
- **Fix:** Add the evaluate block at the root level

### Activities outside `Sequence_1`
- **Symptom:** Activities not visible in designer or not executing
- **Cause:** Activities placed at wrong nesting level (not inside `Sequence_1.do`)
- **Fix:** All user activities go inside `Sequence_1.do`, after `WorkflowStart`

---

## Export Pattern Pitfalls

### Wrong export for Assign (using outputs instead of variables)
- **Symptom:** Assigned variable not accessible via `$context.variables.X`
- **Cause:** Using outputs export pattern (`...$context?.outputs, "Assign_1": $output`) instead of variables pattern
- **Fix:** Assign must use: `{ ...$context, variables: { ...$context.variables, ...$output } }`

### Losing existing context in export
- **Symptom:** Previous activity outputs disappear after an activity runs
- **Cause:** Export does not spread existing context (`$context`) or outputs (`$context?.outputs`)
- **Fix:** Always spread: `{ ...$context, outputs: { ...$context?.outputs, "Key": $output } }`

### Missing `?.` on `$context.outputs` in export
- **Symptom:** Error when activity is the first to write to outputs (outputs is undefined)
- **Cause:** Using `$context.outputs` without optional chaining when no outputs exist yet
- **Fix:** Always use `$context?.outputs` in export patterns

### ForEach body export missing index reset
- **Symptom:** Results array grows incorrectly across loop iterations
- **Cause:** Using the simpler DoWhile accumulation pattern instead of the ForEach index-aware pattern
- **Fix:** ForEach body must use: `...($currentItemIndex == 0 ? [] : ($context?.outputs?.For_Each_N?.results ?? []))`

---

## Expression Pitfalls

### Missing `${}` wrapper
- **Symptom:** Expression treated as literal string instead of evaluated
- **Cause:** Expression written as `$context.variables.x` instead of `${$context.variables.x}`
- **Fix:** Always wrap expressions in `${...}`

### Accessing property on undefined (strict mode)
- **Symptom:** Runtime error: "Cannot read property 'X' of undefined"
- **Cause:** Accessing nested property without null checks in strict evaluation mode
- **Fix:** Use optional chaining: `${$context.outputs?.Javascript_1?.items ?? []}`

### Wrong variable reference for loop iterator
- **Symptom:** `currentItem is not defined` inside the ForEach body, or `$context.variables.currentItem` returns `undefined`.
- **Cause:** Two related mistakes. (1) Reading the iterator from `$context.variables.<name>` — the executor does NOT put it there. (2) Reading it as `${currentItem}` (no `$` prefix) — the executor binds the global with a literal `$` *in the identifier name*, so the unprefixed name has no binding.
- **Fix:** Reference the iterator with the `$` prefix: `${$currentItem}` and `${$currentItemIndex}` (and same for whatever names you passed to `for.each` / `for.at`). The `$` is part of the identifier, not expression syntax. Example: `"when": "${$currentItem.priority === 'high'}"`. See critical rule 11 in `SKILL.md` and the `for.each` binding source at `dist/handlers/for-task-handler.js:67-70`.

### Type coercion errors
- **Symptom:** String concatenation instead of arithmetic, or comparison fails
- **Cause:** Values stored as strings (from input arguments or upstream); strict mode does not auto-coerce
- **Fix:** Explicit coercion: `${Number($context.variables.countStr) + 1}`

### Using `${}` in `for.each` and `for.at`
- **Symptom:** Validation error on ForEach loop definition
- **Cause:** `"each": "${item}"` instead of `"each": "item"` — these declare variable names, not expressions
- **Fix:** `for.each` and `for.at` take plain strings. Only `for.in` takes an expression.

### `arguments[0]` is undefined inside JsInvoke
- **Symptom:** Script throws `Cannot read properties of undefined (reading '$context')` on a line like `const ctx = arguments[0]; ctx.$context.X`
- **Cause:** Trying to read context through `arguments[0]`. The runtime does NOT pass arguments to the script. `arguments.length === 0` inside the body. The task's `arguments` field exists for designer roundtrip but is ignored by the runtime.
- **Fix:** Drop the `arguments[0]` indirection. Reference `$context`, `$workflow`, `$input` directly — they are globals. `return $context.variables.userName.toUpperCase();` instead of `return arguments[0].$context.variables.userName.toUpperCase();`

### `$workflow.input.<name>` is undefined (or `$input.<name>` returns the wrong thing)
- **Symptom:** Read returns `undefined` or wrong value (the previous task's output)
- **Cause:** Either the input was not declared in `input.schema`, was not passed via `--input-arguments`, no default exists, or the agent used `$input.<name>` instead of `$workflow.input.<name>`
- **Fix:**
  - Use `$workflow.input.<name>` everywhere — `$input.<name>` is the previous task's output for any non-first task
  - Confirm the input is declared in `input.schema` or has a default in `document.metadata.variables.schema.document.properties`
  - Pass the value at runtime via `--input-arguments`

---

## Loop Pitfalls

### Infinite DoWhile loop
- **Symptom:** Workflow never completes; timeout or resource exhaustion
- **Cause:** Condition variable not updated inside `#Body`, so `doWhile` condition never becomes false
- **Fix:** Always update the condition variable inside `Do_While_N#Body`

### Wrong `for.in` on DoWhile
- **Symptom:** DoWhile executes wrong number of times or fails to start
- **Cause:** Using an actual collection for `for.in` instead of `"${ [1] }"`
- **Fix:** DoWhile always uses `"for": { "in": "${ [1] }" }`. The `doWhile` condition controls repetition.

### Break outside loop body
- **Symptom:** Validation error; Break activity not recognized
- **Cause:** Break placed outside a `#Body` element (e.g., directly in Sequence)
- **Fix:** Break must be inside `For_Each_N#Body` or `Do_While_N#Body`

### Break with boolean instead of string
- **Symptom:** Break does not exit loop; validation error
- **Cause:** `"break": true` (boolean) instead of `"break": "true"` (string)
- **Fix:** Must be `"break": "true"` (string literal)

### ForEach on non-array
- **Symptom:** Runtime error; loop fails to iterate
- **Cause:** `for.in` expression resolves to a non-array value (object, string, null)
- **Fix:** Ensure `for.in` resolves to an array. Guard with: `${$context.variables?.items ?? []}` or `${$workflow.input.items ?? []}`

---

## Nesting Pitfalls

### Reusing keys across nested scopes
- **Symptom:** "Duplicate key" validation error, or designer renders only one instance
- **Cause:** Two activities share a key (e.g., two `If_1#Then` blocks at different nesting levels)
- **Fix:** Keys are globally unique across the WHOLE workflow, regardless of nesting depth. Increment numbers monotonically: outer If is `If_1`, inner If is `If_2`. See [control-flow-patterns.md](control-flow-patterns.md#key-numbering-convention).

### Reusing iteration variable names across nested loops
- **Symptom:** Inner loop's iterator value leaks into outer scope or vice versa
- **Cause:** Outer ForEach uses `for.each: "currentItem"` and inner ForEach also uses `for.each: "currentItem"` — the inner shadows the outer
- **Fix:** Use distinct names per nesting level: `outerItem` / `innerItem`, `customer` / `order`, etc.

### Break exits the wrong loop
- **Symptom:** You expected Break to exit BOTH nested loops, but only the inner exits
- **Cause:** Break exits only the innermost enclosing loop — that's the spec
- **Fix:** Set a flag variable before Break, then check it in the outer loop and Break again. See [control-flow-patterns.md](control-flow-patterns.md) pattern #5.

### `then: "exit"` confused with `then: "end"`
- **Symptom:** Workflow terminates unexpectedly when an If branch finishes
- **Cause:** Used `then: "end"` on a `#Then` or `#Else` branch — that ends the WORKFLOW, not the branch
- **Fix:** Use `then: "exit"` to exit the current container; use `then: "end"` only on Response activities

---

## Response Pitfalls

### Missing `then: "end"`
- **Symptom:** Workflow does not terminate properly; subsequent activities run
- **Cause:** Response activity missing `"then": "end"`
- **Fix:** Always include `"then": "end"`

### `markJobAsFailed` nested inside `response`
- **Symptom:** Job runs even though intent was to mark it failed
- **Cause:** `markJobAsFailed` placed inside `response` object instead of as a sibling
- **Fix:** `markJobAsFailed` is a SIBLING of `response`:
  ```json
  "response": "${expression}",
  "markJobAsFailed": false,
  "then": "end"
  ```

### Workflow returns `Data: { "message": "(no output)" }`
- **Symptom:** Run succeeds but no output value
- **Cause:** No Response task in the workflow, OR Response uses legacy `set:` form without `then: "end"`
- **Fix:** Use `response: <value>` + `markJobAsFailed: false` + `then: "end"`

---

## StudioWeb Roundtrip Pitfalls

These are issues that surface only when a workflow is opened or run in **StudioWeb** (alpha.uipath.com). Workflows that pass `uip api-workflow run --no-auth` may still fail in cloud for these reasons.

### `ReferenceError: <literal> is not defined` after opening in StudioWeb

- **Symptom:** Workflow runs cleanly under `uip api-workflow run`. Open it in StudioWeb's designer, run from there, get `Worker operation failed: PASS is not defined` (or `FAIL`, `INVALID`, `done`, etc. — whatever literal string you used).
- **Cause:** StudioWeb's designer normalizes Assign `set` values and Response `response` literals when it parses or saves the JSON. It treats unwrapped strings (e.g. `"grade": "PASS"`) as expressions typed into the property panel and rewrites them to `"grade": "${PASS}"` — turning the literal into a bare identifier reference. At run time `PASS` has no binding, so the expression evaluator throws `<name> is not defined`.
- **Fix:** Pre-wrap every string literal in `Assign.set` and `Response.response` (and similar expression-typed slots) as a JS string inside an expression: `"${'literal'}"`. The single-quoted form avoids JSON escaping. Examples:
  ```json
  "set": { "tier": "${'PLATINUM'}" }              // ✓ roundtrips cleanly
  "set": { "tier": "PLATINUM" }                   // ✗ becomes ${PLATINUM} → ReferenceError

  "response": "${'done'}"                          // ✓
  "response": { "status": "${'ok'}", "code": 200 } // ✓ — numbers/booleans need no wrap

  "response": { "status": "ok" }                   // ✗ — gets rewritten on save
  ```
- **What does NOT need wrapping:** numbers (`0`, `42`), booleans (`true`/`false`), values that already evaluate expressions (`"${$workflow.input.x}"`, `"${$context.variables.tier}"`), and the activity-control strings `then: "exit"` / `then: "end"`.
- **Heuristic:** any time you'd write `"foo"` as a *literal value* you intend the workflow to use, wrap it as `"${'foo'}"`. The CLI evaluates the expression and gets the string `'foo'`; StudioWeb leaves the already-wrapped form alone.

### Object-valued Response gets corrupted; fields evaluate to literal expression text (SW-28452 / cli#1537)

- **Symptom:** Workflow runs correctly under `uip api-workflow run` and Response returns the expected object (e.g. `{ tier: "GOLD", count: 3 }`). After opening + saving in StudioWeb, the same Response now returns each field's value as the **literal text of its expression** rather than the evaluated value — `tier` becomes the string `"${$context.variables.tier}"` (one long string, often 100+ chars), not `"GOLD"`. StudioWeb's own output-schema validator may flag the mismatch ("Output-ul nu corespunde schemei de output configurate").
- **Cause:** StudioWeb's designer rewrites Response object payloads on save. Authored `{ "response": { "tier": "${...}", "count": "${...}" } }` is collapsed into a single stringified expression: `"response": "${{\"tier\":\"${...}\",\"count\":\"${...}\"}}"`. The outer `${{ ... }}` is a JS object-literal expression form, but inside it the keys/values are inside JS **double-quoted** strings (`"tier":"${...}"`) — and JS double-quoted strings don't interpolate `${...}`, only template literals do. So each field's value resolves to the literal characters `${...}`, not the evaluated expression.
- **Fix:** Pre-author the Response in the single-expression `${{ ... }}` form yourself, with raw context references inside (no inner `${...}` wrapping):
  ```json
  // ✗ Wrong — CLI runs fine, designer corrupts on save
  {
    "Response_1": {
      "response": {
        "tier": "${$context.variables.tier}",
        "count": "${$context.variables.count}"
      },
      "markJobAsFailed": false,
      "then": "end",
      "metadata": { "...": "..." }
    }
  }

  // ✓ Correct — roundtrips cleanly through the designer
  {
    "Response_1": {
      "response": "${{ tier: $context.variables.tier, count: $context.variables.count }}",
      "markJobAsFailed": false,
      "then": "end",
      "metadata": { "...": "..." }
    }
  }
  ```
- **Why it works:** Inside the outer `${{ ... }}` you're already in JS expression scope. The body is a JS object literal where unquoted keys are identifiers (`tier:`, `count:`), references like `$context.variables.tier` evaluate directly, string literals use single quotes (`status: 'ok'`), and numbers/booleans are bare (`count: 0`, `flag: true`). The designer recognizes the whole thing as a single expression and leaves it alone — it doesn't try to reinterpret each field.
- **Either expression-form works:** `"${ { ... } }"` (single-brace expression containing a JS object literal) and `"${{ ... }}"` (double-brace object-literal-expression form) evaluate to the same value. Pick one convention; this skill standardizes on the double-brace form, but you may see single-brace in the wild and they are interchangeable.
- **Single-value responses are fine as-is:** `"response": "${$context.outputs.Javascript_1}"` or `"response": "${'done'}"` — the designer only mangles object payloads, not single expressions.
- **On-disk is authoritative — re-validate after every designer save.** Even with the single-expression workaround, every StudioWeb designer save may re-trigger normalization passes that corrupt the Response shape. Treat the file on disk as the source of truth: after any designer roundtrip, re-run `uip api-workflow run --no-auth --output json` and inspect the Response output. If a field has become the literal text of its expression (a long string instead of the evaluated value), the file was re-corrupted — re-apply the single-expression workaround in the file directly, and consider keeping CLI-authored workflows out of designer save cycles until SW-28452 ships.
- **Upstream:** designer-side bug SW-28452. CLI issue with full pre/post diff and runtime evidence: [UiPath/cli#1537](https://github.com/UiPath/cli/issues/1537). Fix lives in the api-workflows translator for Response tasks (needs to preserve object payloads losslessly). Until that ships, the single-expression workaround is required and may need re-applying after each designer roundtrip.

### Multi-key `Assign.set` silently drops all but one variable

- **Symptom:** Workflow runs correctly under `uip api-workflow run` and updates several variables in one Assign. Open it in StudioWeb, run from the designer (or after a save+reload), and now only one variable is being updated each iteration. The others stay at their schema default. Loops produce results like `{sum: 10, count: 0, max: 0}` when all three should have been computed.
- **Cause:** **StudioWeb's designer collapses multi-key `Assign.set` blocks to a single key on save.** The Assign activity card in the designer represents one variable assignment, and the persistence layer normalizes the JSON to match. After a roundtrip: `"set": { "sum": "${...}", "count": "${...}", "max": "${...}" }` becomes `"set": { "sum": "${...}" }`. The other keys are gone from the file; the runtime executes what's left.
- **Fix:** Use one Assign per variable. Place them sequentially in the same `do` array. Each Assign has a single-key `set` that StudioWeb's designer leaves intact. Example:
  ```json
  // ✗ Multi-key — loses count and max after StudioWeb save
  {
    "Assign_1": {
      "set": {
        "sum": "${$context.variables.sum + $currentItem}",
        "count": "${$context.variables.count + 1}",
        "max": "${Math.max($context.variables.max, $currentItem)}"
      },
      ...
    }
  }

  // ✓ Single-key per Assign — roundtrips cleanly
  { "Assign_Sum":   { "set": { "sum":   "${$context.variables.sum + $currentItem}" }, "export": {...}, "metadata": {...} } },
  { "Assign_Count": { "set": { "count": "${$context.variables.count + 1}" },         "export": {...}, "metadata": {...} } },
  { "Assign_Max":   { "set": { "max":   "${Math.max($context.variables.max, $currentItem)}" }, "export": {...}, "metadata": {...} } }
  ```
- **Cost:** N Assigns instead of 1. The variables export pattern (`{ ...$context, variables: { ...$context.variables, ...$output } }`) on each one merges its single key into `$context.variables` cleanly — the next Assign sees the previous one's update.

### `TS2708: Cannot use namespace '$workflow' as a value` (and `$context`, `$input`)

- **Symptom:** StudioWeb's expression editor shows a warning marker on conditions like `${$workflow.input.score >= 50}`.
- **Cause:** The editor's ambient TypeScript typings declare `$workflow` (and `$context`, `$input`) as **namespaces**, which in TypeScript are type-only constructs erased at compile time and cannot be used as values. The TS checker flags any expression that reads them like values.
- **Status:** Cosmetic, ignore. At run time the executor binds `$workflow`/`$context`/`$input` as real values on `globalThis` via `setVariables` — the TS check has no relationship to runtime behavior. Same warning fires for any `when`, `set`, `response`, or `for.in` expression that touches these names. Workflows containing this warning still execute correctly.
- **What NOT to do:** do not "fix" by rewriting the expression. There is no syntax that satisfies the TS check without breaking runtime — `$workflow` IS the binding name. Workarounds like `(globalThis as any).$workflow` are nonsensical in expression strings.
- **Proper fix is on StudioWeb's side:** ship `declare const $workflow: WorkflowRuntime` instead of `declare namespace $workflow { ... }`. That's not a skill-level concern.

### Activity card renders with a "block" / "forbidden" icon in the designer

- **Symptom:** StudioWeb shows the activity as blocked; you can only delete it. Run-time behavior depends — sometimes the activity is silently skipped, leading to downstream `$context.outputs.<missing>` errors.
- **Cause:** StudioWeb's designer doesn't recognize the activity type. For HTTP-style cards specifically, the designer's `restoreFromTaskItem` (`connector-translator.ts`) requires `call: "UiPath.Http"` (or `"UiPath.IntSvc"`, `"UiPath.IntSvcEvent"`) AND a `metadata.configuration` blob containing at minimum `instanceParameters`. Plain `call: "http"` and missing/empty configurations both produce the block icon.
- **Status:** This skill does NOT cover HTTP/Connector activities — they're out of scope precisely because of this metadata requirement. If you encounter this, either: (a) author the offending activity directly in StudioWeb's designer (which generates the correct metadata), or (b) wait for the skill to grow `uip case registry`-backed metadata generation for known activity types.

---

## Run-Time Errors (CLI)

### `"File not found: <path>"`
- **Cause:** The workflow file path passed to `uip api-workflow run` does not resolve
- **Fix:** Use an absolute path or run from the directory containing the workflow

### `"Invalid JSON in workflow file"`
- **Cause:** Malformed JSON — trailing comma, unquoted key, mismatched brace, comment
- **Fix:** Validate before running:
  ```bash
  node -e "JSON.parse(require('fs').readFileSync('./wf.json','utf8'))"
  ```
  JSON does NOT permit comments. Strip them.

### `"Invalid JSON in --input-arguments"`
- **Cause:** The string passed to `--input-arguments` is not valid JSON
- **Fix:** Wrap the entire JSON in single quotes; double-quote all keys and string values:
  ```bash
  --input-arguments '{"name":"Alice","count":3}'
  ```

### `Workflow status is not "Successful"` (executor returns failure)
- **Cause:** A task threw during execution
- **Fix:** Read `Message` and `Instructions` in the failure output. Common patterns:
  - JS_Invoke: missing `return` statement, runtime error in script body, undefined `$context.outputs.<TaskName>` (prior task did not run or did not `export`)
  - Assign expression: invalid `${...}` syntax, referencing an undefined variable in strict mode
  - Loop body: condition variable not updated (DoWhile infinite loop), missing `#Body` suffix, wrong export pattern

### `$context.outputs.<TaskName>` is undefined
- **Cause:** The prior task did not `export` its output back into context
- **Fix:** Add the standard export to the prior task — see [expressions-and-context.md](expressions-and-context.md)

### Strict-mode JS error inside a JS_Invoke
- **Cause:** Implicit globals, `var` hoisting, unsafe property access, duplicate object keys
- **Fix:**
  - Replace `var` with `const` / `let`
  - Use optional chaining: `$context?.outputs?.Javascript_1?.items`
  - Ensure object literals have unique keys

---

## Packaging Errors

### `"No CLI tool mapping found for project type 'X'"`
- **Cause:** The solution `.uipx` declares a project type the packager has not loaded
- **Fix:** For API workflows, ensure `Type: "Api"` exactly (case-sensitive)

### `Failed to parse <solution>.uipx`
- **Cause:** Solution file is malformed JSON
- **Fix:** Re-create with `uip solution new <name>` and re-add projects via `uip solution project add`

### Generated `operate.json` or `package-descriptor.json` mismatch
- **Cause:** Stale files committed by hand or from an older CLI version
- **Fix:** Delete both files from the project directory and re-run `uip solution pack`. The packager regenerates them.

### `.nupkg` produced but missing workflow files
- **Cause:** Workflow JSON not located in the project directory the packager scanned
- **Fix:** Verify workflow files are in the project folder declared in the solution `.uipx`, alongside `project.json`

---

## Publish Errors

### `"Invalid file type. Expected a .zip file"`
- **Cause:** Passing a `.nupkg` directly instead of the wrapping `.zip`
- **Fix:** Publish the `.zip` produced by `uip solution pack`, not its contents

### Publish 401 / 403
- **Cause:** Not logged in, wrong tenant, or insufficient role
- **Fix:** `uip login`, confirm `--tenant` matches deployment target

### Publish 409 / "name conflict"
- **Cause:** A package with the same name and version already exists
- **Fix:** Bump version with `--version <newVersion>` and re-pack/publish

---

## Validation Pitfalls

### Not re-running after a fix
- **Symptom:** Reported "fixed" but errors remain
- **Cause:** Skipped re-running `uip api-workflow run --no-auth` after applying a fix
- **Fix:** ALWAYS re-run after every edit. The CLI is the only validator — there is no `uip api-workflow validate` command.

### Fixing in wrong order
- **Symptom:** Fixing one error creates more errors; thrashing
- **Cause:** Fixing logic errors before structure errors; lower-priority fixes destabilize higher-priority structure
- **Fix:** Fix in order: Structure > Expression > Activity Config > Logic. Higher categories often resolve lower ones automatically.

### Assuming an edit succeeded
- **Symptom:** File appears unchanged after edit
- **Cause:** Edit's `old_string` did not exactly match file content (whitespace, escaping)
- **Fix:** Always read the file before editing. After edit, re-run the workflow.

---

## Debugging Strategy

1. **Always run with `--output json`** so failures are machine-parseable
2. **Run `--no-auth` first** to confirm structural validity. If structure passes but the real run fails, the issue is auth, network, or input data — not the workflow shape
3. **Reduce to minimal repro** — comment out (delete + restore via git) downstream tasks to isolate which task fails
4. **Check exit code** — `0` = success, `1` = failure
5. **Read `Instructions` first** — the executor often suggests the fix directly
