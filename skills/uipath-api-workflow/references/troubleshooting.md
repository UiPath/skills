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

### Activities outside the root sequence
- **Symptom:** Activities not visible in designer or not executing
- **Cause:** Activities placed at wrong nesting level (not inside the root sequence's `do` array)
- **Fix:** All user activities go inside the root sequence, after `WorkflowStart`

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
- **Cause:** StudioWeb's designer doesn't recognize the activity type. For HTTP-style cards specifically, the designer's `restoreFromTaskItem` (`connector-translator.ts:113`) requires `call: "UiPath.Http"` (or `"UiPath.IntSvc"`, `"UiPath.IntSvcEvent"`) AND a `metadata.configuration` blob containing at minimum `instanceParameters` (`connector-translator.ts:121-136`). Plain `call: "http"` and missing/empty configurations both produce the block icon.
- **Fix:** Run the discovery flow in [connector-activity-discovery.md](connector-activity-discovery.md) to get a stub with the right `uiPathActivityTypeId` and `metadata.configuration` already filled in. The [connector-call-example.json](../assets/templates/connector-call-example.json) template shows the correct shape verified end-to-end. Common mistakes that produce block / legacy icons:
  - Used `call: "http"` (deprecated simple form). **Fix:** switch to `call: "UiPath.Http"` (Http kind) or `call: "UiPath.IntSvc"` (IntSvc kind) — re-stub via `uip api-workflow registry stub <guid>` and replace the activity.
  - Used `call: "UiPath.Http"` but `metadata.configuration` is missing or `"{}"`. **Fix:** re-stub via `uip api-workflow registry stub <guid>` — the stub builds `essentialConfiguration` (with `unifiedTypesCompatible: true` + `savedJitInputFieldId`) automatically.
  - Invented a `uiPathActivityTypeId` value or used the default fallback (`111d59b7-...`). **Fix:** look up the real GUID via `uip api-workflow registry resolve "<keyword>"`.

### `uip is connections ping` returns 404 `"Connection [<uuid>] is invalid or you do not have access to it"`

- **Symptom:** A connection appeared in `uip is connections list <connectorKey> --output json` with `State: "Enabled"`. Pinging it returns HTTP 404 with the message above (sometimes also `Code: "ConnectionNotEnabled"`). The agent is tempted to proceed anyway because the listing said the connection was enabled.
- **Cause:** The filtered `uip is connections list <connectorKey>` listing is not authoritative. It can return **stale or orphaned records** — connections where the underlying element instance was deleted upstream, or that were created in a different org/tenant. The unfiltered `uip is connections list` (no connector argument) often shows a different, working UUID for the same `ConnectorKey`.
- **Fix:** Run the unfiltered listing and find the working UUID:
  ```bash
  uip is connections list --output json
  # Search Data[] for entries with ConnectorKey == "<connector-key>"
  # Take a different Id, then ping it:
  uip is connections ping <alternate-uuid> --output json
  # If Code: "ConnectionPing" — use this UUID in the workflow
  ```
- **What NOT to do:** do NOT proceed with the failing UUID and "flag for follow-up." A workflow authored against a non-pinging connection will 401 in cloud regardless of how correct the JSON is. If neither the filtered nor unfiltered listing yields a working UUID, abort and tell the user to re-authenticate (`uip is connections edit <uuid>` opens an OAuth browser flow) or create a fresh connection in the StudioWeb UI.
- **See also:** [connector-activity-discovery.md — Step 2](connector-activity-discovery.md#step-2--verify-a-vendor-connection-intsvc-kind-only) for the full discovery+fallback flow.

### IntSvc kind activity output read at the root returns `undefined`

- **Symptom:** A `UiPath.IntSvc` activity (Outlook GetNewestEmail, Gmail Send Email, GitHub Search Issues, …) ran successfully — the run output shows the vendor data in the activity result. Downstream code that reads `$context.outputs.<Activity>.<field>` gets `undefined`. If conditions like `${$context.outputs.getNewestEmail_1?.subject?.length > 15}` always evaluate false. JsInvoke scripts return empty values.
- **Cause:** IntSvc kind (`call: "UiPath.IntSvc"`) wraps the vendor payload in `.content`. The full activity output is `{ statusCode, statusText, headers, ok, request, content: { <vendor fields> }, vendorProcessingTimeMs }` — the actual data is one level deeper than the root, under `.content`. The other keys carry HTTP-level metadata you usually don't need.
- **Fix:** Read through `.content`:
  ```javascript
  // ✗ Wrong — always undefined
  "${$context.outputs.getNewestEmail_1?.subject}"

  // ✓ Correct
  "${$context.outputs.getNewestEmail_1?.content?.subject}"
  ```
  For list-shaped operations, `.content` itself holds the result — usually as a bare array (the IS proxy strips vendor-native envelopes like M365 Graph's `{ value: [...] }` before it reaches you), but the exact shape is per-operation. **Read the stub's `optionalConfiguration.fieldsContainer.outputJsonSchema.type` to know which:**
  - `type: "array"` → `.content` IS the array. Read `.content[0].<field>`.
  - `type: "object"` → `.content` is a single object. Read `.content.<field>`.

  Verified shapes: Outlook `ListEmails` → `.content[0].subject` (bare array). Slack `send_message_to_user_v2` → `.content.ok`, `.content.ts` (single object). HTTP Request → `.content.<field>` (single object). For unverified vendors, log the activity output once and inspect.
- **Defensive form for JsInvoke** (handles the local-CLI quirk where `.content` is sometimes a JSON string):
  ```javascript
  const out = $context.outputs.getNewestEmail_1;
  const raw = out && (out.content !== undefined ? out.content : out);
  const body = (typeof raw === 'string') ? JSON.parse(raw) : raw;
  const item = Array.isArray(body) ? body[0] : body;
  return { subject: (item && (item.subject || item.Subject)) || '' };
  ```
- **Use the stub's `Data.ExportBucketKey`** for downstream reads — for Outlook `getNewestEmail` it's `getNewestEmail_1`, not the slot's `GetNewestEmail_1`. Connector activities can have a slot/export divergence — see "Connector slot key and export-bucket key can differ — use the stub's values" below.
- **Http kind (`UiPath.Http`) is the same shape:** `{ statusCode, statusText, headers, ok, request, content, vendorProcessingTimeMs }`. The `.content` field carries the parsed response body. The wrapping is universal across both kinds.

### Connector `bodyParameters` fields disappear after StudioWeb save (nested objects dropped)

- **Symptom:** Authored a connector activity with nested body — `{ message: { toRecipients: "...", subject: "...", body: { content: "..." } }, saveToSentItems: true }`. Workflow runs locally. Open it in StudioWeb (or save via the designer); the `message` block is gone from the file. Only fields whose names appear at the top level of `bodyParameters` survive (e.g. `saveToSentItems`). The vendor receives a payload missing the actual message data.
- **Cause:** StudioWeb's connector deserializer (`buildConnectorProperties` in `connector-translator-utils.ts`) scans `bodyParameters` for keys that match the connector's input-field names verbatim. Field names like `message.toRecipients` are flat dotted strings — the dot is a literal character, not a path separator. The deserializer does NOT recurse into nested objects. Nested-object values aren't found, the field model shows them empty, and the next save persists the empty model.
- **Fix:** Use flat dotted keys matching the schema's `requestFields[].name` verbatim:
  ```json
  // ✗ Wrong — dropped on save
  "bodyParameters": {
    "message": {
      "toRecipients": "andrei.hodoroaga@uipath.com",
      "subject": "test",
      "body": { "content": "<p>hi</p>", "contentType": "Html" }
    },
    "saveToSentItems": true
  }

  // ✓ Correct — survives roundtrip
  "bodyParameters": {
    "message.toRecipients": "andrei.hodoroaga@uipath.com",
    "message.subject": "test",
    "message.body.content": "<p>hi</p>",
    "message.body.contentType": "Html",
    "saveToSentItems": true
  }
  ```
- **Same rule** applies to `queryParameters` and `pathParameters`. The IS proxy unflattens the dotted keys into a nested wire payload before calling the vendor — so the over-the-wire JSON ends up identical, but the on-disk shape must be flat. See [connector-activity-discovery.md#rule-a--bodyparameters--queryparameters--pathparameters-use-flat-dotted-keys](connector-activity-discovery.md#rule-a--bodyparameters--queryparameters--pathparameters-use-flat-dotted-keys).

### Connector `bodyParameters` literal cleared after StudioWeb save (`${'literal'}` read as expression)

- **Symptom:** Authored connector body with literals wrapped per the Assign rule — `"message.toRecipients": "${'andrei.hodoroaga@uipath.com'}"`. Workflow runs locally. After StudioWeb save, the field becomes empty (or shows a non-literal expression marker in the designer); the email goes out with no recipient.
- **Cause:** SKILL.md rule 5 (literal-wrap as `${'foo'}`) applies to **Assign / Response / If `when`**, NOT to connector params. StudioWeb's connector field detector treats `${...}` as a non-literal expression — it's looking for either a bare literal value or a real reference. `${'foo'}` looks like neither (it's a literal-disguised-as-expression), so the value isn't bound as a field literal and is dropped.
- **Fix:** Bare literals in connector params:
  ```json
  // ✗ Wrong — cleared on save
  "bodyParameters": {
    "message.toRecipients": "${'andrei.hodoroaga@uipath.com'}",
    "message.subject": "${'this is a claude skill test'}"
  }

  // ✓ Correct — bare literals
  "bodyParameters": {
    "message.toRecipients": "andrei.hodoroaga@uipath.com",
    "message.subject": "this is a claude skill test"
  }
  ```
  References (`${$context.variables.X}`, `${$workflow.input.Y}`) stay wrapped because they're real expressions — the rule applies to literal *values*, not to references. See [connector-activity-discovery.md#rule-b--literals-in-connector-params-are-bare-not-literal-wrapped](connector-activity-discovery.md#rule-b--literals-in-connector-params-are-bare-not-literal-wrapped).

### Connector slot key and export-bucket key can differ — use the stub's values

- **Symptom:** Authored a connector activity using the slot key for the export — `"GetNewestEmail_1"` in the `do` array AND in the `export.as`. Workflow runs locally; downstream `$context.outputs.GetNewestEmail_1.content.subject` returns the correct value. After opening or saving in StudioWeb, downstream reads return `undefined`. The TypeScript linter shows `TS2551: Property 'GetNewestEmail_1' does not exist on type 'typeof outputs'. Did you mean 'getNewestEmail_1'?`. Diff of the file shows the export bucket key was rewritten to `getNewestEmail_1` — the slot key in the `do` array stayed `GetNewestEmail_1`.
- **Cause:** Connector activities are the only activity type where the slot key (in the `do` array) and the export-bucket key (what `$context.outputs.<X>` reads as) can differ. Every other type (Assign, JsInvoke, If, ForEach, DoWhile, TryCatch, Wait, Response) keeps "slot key === export key." For connector activities, StudioWeb's serializer normalizes the export bucket to a stub-computed form. The stub returns both keys correctly in `Data.SlotKey` and `Data.ExportBucketKey` — they are sometimes identical (Outlook `ListEmails` → both `ListEmails_1`) and sometimes different (Outlook `getNewestEmail` → slot `GetNewestEmail_1` / bucket `getNewestEmail_1`; HTTP `http-request` → slot `HttpRequest_1` / bucket `http_request_1`). Reconstructing either key from `objectName` by hand is what produces the mismatch.
- **Fix:** Use `Data.SlotKey` and `Data.ExportBucketKey` from the stub verbatim. The slot key goes in the `do` array; the export-bucket key goes in `export.as` AND in every downstream `$context.outputs.<X>` reference:
  ```json
  // ✓ Correct — both keys taken from the stub output
  {
    "GetNewestEmail_1": {                          // Data.SlotKey
      "call": "UiPath.IntSvc",
      "with": { ... },
      "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"getNewestEmail_1\": $output } }" }
                                                   // Data.ExportBucketKey
    }
  }
  ```
  And every downstream consumer:
  ```json
  "when": "${$context.outputs.getNewestEmail_1?.content?.subject?.length > 15}"
  "response": "${{ subject: $context.outputs.getNewestEmail_1.content.subject }}"
  ```
- **Rule:** Read `Data.SlotKey` and `Data.ExportBucketKey` from `uip api-workflow registry stub` output. Use both verbatim. Never derive either from `objectName` by hand. See [connector-activity-discovery.md — Rule (c)](connector-activity-discovery.md#rule-c--use-dataslotkey-and-dataexportbucketkey-from-the-stub-verbatim).

### `400 "Unable to parse multipart body"` from a curated send-email-style endpoint

- **Symptom:** Workflow runs against a vendor curated activity (Outlook `send-mail-v2`, Gmail `sendEmail` with attachments, etc.) and the vendor returns `400 "Unable to parse multipart body"`. The request `Content-Type` header was `application/json`. The body looked structurally correct (recipient, subject, body all present).
- **Cause:** The endpoint expects `multipart/form-data`, not `application/json`. Multipart-only endpoints typically support file attachments — they encode the email JSON as one form part and any attached files as other parts. The activity needs a `multipartParameters` declaration alongside `bodyParameters`. Without it, the executor sends `application/json` with the raw `bodyParameters` payload, and the vendor's multipart parser rejects it.
- **Detection:** Re-stub the activity (`uip api-workflow registry stub <guid> --connection-id <uuid> --output json`) — the CLI calls IS Elements internally and declares `multipartParameters` automatically when it sees `parameters[].type === "multipart"`. If `Data.Activity.with.multipartParameters` is missing from the stub output, the endpoint isn't multipart. (Manual fallback if the stub's enrichment failed: `uip is resources describe <connector-key> <object-name> --output json` and read the `parameters` section.)
- **Fix:** Mirror the parameters on the activity. For Outlook `send-mail-v2`:
  ```json
  "with": {
    "endpoint": "/hubs/productivity/send-mail-v2",
    "bodyParameters": {
      "message.toRecipients": "andrei.hodoroaga@uipath.com",
      "message.subject": "...",
      "message.body.content": "...",
      "message.body.contentType": "Text",
      "saveToSentItems": true
    },
    "queryParameters": { "saveAsDraft": false },
    "multipartParameters": [
      { "name": "file", "dataType": "file" },
      { "name": "body", "dataType": "string" }
    ]
  }
  ```
- **What the executor does with `multipartParameters`:** `is-utils.js:constructMultipartFormData` walks the array. For `dataType: "string"` parts, it JSON-stringifies the **entire `bodyParameters` object** and stuffs the resulting string into the multipart part with that name. So `bodyParameters` (with its flat-dotted keys) becomes the JSON content of the multipart `body` part. For `dataType: "file"` parts, the part is left empty unless the activity supplies a file reference (rarely needed for the no-attachment case — Outlook accepts an empty `file` part). See [connector-activity-discovery.md#multipart-endpoints--multipartparameters-declaration](connector-activity-discovery.md#multipart-endpoints--multipartparameters-declaration).

### Properties panel: "to debug this resource, select a connection for it from the resource definition page"

- **Symptom:** The workflow runs locally with `uip api-workflow run` AND from "Run" in StudioWeb. Open the activity card in the designer, click the connection field, and the properties panel renders the connection as invalid with the message **"to debug this resource, select a connection for it from the resource definition page."** `bindings_v2.json` contains a correct `Connection` resource entry; `Workflow.json` has `connectionId` / `connectionResourceId` set to the same pinged UUID.
- **Cause:** **In a Solutions-mode project, every connection used by an activity must ALSO be declared in two Solution-level artefacts.** The catalogue resource file (`Solution/resources/solution_folder/connection/<connector-key>/<connection-name>.json`) declares that the Solution uses the connection; the per-user debug overwrites file (`Solution/userProfile/<guid>/debug_overwrites.json`) maps the connection's UUID to a runtime folder+key. StudioWeb's properties panel resolves connections by calling `getResourceDebugReference({ key: <uuid> })` — when that returns null (because either file is missing), `activityState.realConnectionId` becomes null, and the workflow serializer writes `with.connectionId: null` to `Workflow.json` on the next save. The runtime resolves connections from `Workflow.json` directly (which is why "Run" works against a freshly-authored workflow), but the panel resolves via the Solution resource tree (which is why the click breaks). `uip api-workflow registry stub` does not write either file — both are created by the post-authoring sync flow described in the Fix below. Distinct from `bindings_v2.json`: that file is the *input* to the sync (StudioWeb computes it in-memory; the CLI's `bindings sync` emits the same content offline); the catalogue + debug-overwrite files are the *outputs*.
- **Detection:** Look for the file:
  ```bash
  ls Solution/resources/solution_folder/connection/<connector-key>/ 2>/dev/null
  # → ENOENT or empty → file missing → this is the bug
  ```
  Also check that `bindings_v2.json`'s `"key"` matches `Workflow.json`'s `connectionId` matches the missing resource file's intended `"key"` — same UUID across all three.
- **Fix (preferred — two CLI commands):**
  ```bash
  # 1. Generate bindings_v2.json from Workflow.json (pure local; no auth needed):
  uip api-workflow bindings sync --workflow <path-to-Workflow.json> --output json

  # 2. Sync catalogue + debug overwrites via @uipath/resource-builder-sdk (requires uip login):
  uip solution resource refresh --solution-folder <path-to-solution-root> --output json
  ```
  Step 1 walks the workflow, extracts IntSvc connector activities, dedupes by connection UUID, and writes the canonical `bindings_v2.json` next to the workflow — what StudioWeb normally produces in-memory on workflow open. Step 2 reads that file, uses the SDK's `addOrUpdateResourceToSolutionAsync` to write the catalogue file, and `editOverwritesAsync` to write the per-user debug overwrites. Both commands are idempotent and safe to re-run.

  Reload the workflow in StudioWeb. The connection pill should resolve to the connection name, the "resource definition page" error should be gone, and clicking the activity should no longer null `with.connectionId`.

- **Fix (hand-authored fallback — when the CLI is unavailable):** Start from [assets/templates/solution-connection-resource-template.json](../assets/templates/solution-connection-resource-template.json) and fill in the placeholders:
  ```json
  {
    "docVersion": "1.0.0",
    "resource": {
      "name": "<connection Name from `uip is connections list`>",
      "kind": "connection",
      "type": "<connector key, e.g. uipath-microsoft-outlook365>",
      "apiVersion": "integrationservice.uipath.com/v1",
      "isOverridable": true,
      "dependencies": [],
      "runtimeDependencies": [],
      "folders": [{ "fullyQualifiedName": "solution_folder" }],
      "spec": {
        "connectorName": "<ConnectorName from `uip is connections list`, e.g. Microsoft Outlook 365>",
        "name": "<same connection Name>",
        "authenticationType": "AuthenticateAfterDeployment",
        "connectorVersion": "<from stub's metadata.configuration.essentialConfiguration.connectorVersion, fallback \"1.0.0\">",
        "connectorKey": "<connector key>",
        "pollingInterval": 5
      },
      "locks": [],
      "key": "<connection UUID — MUST equal Workflow.json's connectionId>",
      "files": []
    }
  }
  ```
  Place it at `Solution/resources/solution_folder/connection/<connector-key>/<connection-name>.json`. Reuse the `solution_folder` name from any existing `Solution/resources/<folder>/package/<workflow>.json` (`folders[0].fullyQualifiedName`); default is `"solution_folder"`. One file per unique connection UUID — if the workflow has two activities reusing one connection, write one file; two distinct connections → two files.
- **Note on the user-profile debug overwrite.** StudioWeb additionally writes `Solution/userProfile/<guid>/debug_overwrites.json` mapping `solutionResourceKey` to a concrete folder + connection at debug time. That file is per-user state, written by the designer the first time you assign a debug connection. The agent does not author it; if it's missing, debug runs from the StudioWeb UI will prompt for a connection but won't 401.
- **See also:** [connector-activity-discovery.md — Step 5](connector-activity-discovery.md#step-5--solutions-mode-intsvc-kind-declare-the-connection-as-a-solution-resource) for the full flow, including where each field value comes from.

### Required request field dropped by `registry stub`

- **Symptom:** A vendor curated activity (Outlook `getNewestEmail`, Gmail `searchMessages`, …) runs locally — sometimes returning unexpected results (wrong folder, no filter applied) — and fails in cloud with a 4xx, OR the StudioWeb properties panel marks a field with a red border and an "invalid" badge but no clear error text. `registry stub`'s output shows `queryParameters: {}`, `pathParameters: {}`, or `bodyParameters: {}` for an endpoint that obviously needs inputs.
- **Cause:** **`uip api-workflow registry stub` silently drops `required: true` request fields that weren't passed via `--inputs`.** The IS Elements metadata is correct (`fieldsContainer.inputFields[]` inside the stub's `metadata.configuration` blob lists every field with the right `required` flag), but the stub doesn't populate the matching `<location>Parameters` slot from it. Verified for `getNewestEmail`: requires `parentFolderId` (`fieldLocation: "query"`), stub returns `queryParameters: {}`.
- **Detection:** Two ways to surface the missing fields.
  - **From the stub output directly.** Parse the JSON-encoded string at `Data.Activity.<SlotKey>.metadata.configuration` → `optionalConfiguration.fieldsContainer.inputFields[]`. Filter for `required === true`. Any entry whose `name` is absent from the corresponding `with.<fieldLocation>Parameters` block is missing.
  - **Cleaner: re-describe the operation.** Call `uip is resources describe`:
    ```bash
    uip is resources describe <connector-key> <object-name> \
      --operation <operation> \
      --connection-id <pinged-uuid> \
      --output json
    ```
    `<operation>` is the IS-Elements operation name (`List`, `Create`, `Get`, …) — listed by the same command without `--operation`. The returned `Data.queryParameters[]` / `Data.pathParameters[]` / `Data.bodyParameters[]` arrays mark each entry with `required`.
- **Fix:** Either re-run the stub with the missing fields included via `--inputs`:
  ```bash
  uip api-workflow registry stub <activity-type-id> \
    --connection-id <uuid> \
    --inputs '{"parentFolderId": "inbox"}' \
    --output json
  ```
  Or hand-edit the activity to insert the missing field — **bare literal** (rule 16(b)), **flat dotted key** if a body/nested field (rule 16(a)). Example:
  ```json
  "with": {
    ...
    "queryParameters": {
      "parentFolderId": "inbox"
    }
  }
  ```
- **Well-known shortcuts.** MS Graph accepts well-known folder names (`"inbox"`, `"sentitems"`, `"drafts"`) as `parentFolderId`. They run, but StudioWeb's FolderPicker only displays the friendly folder name when the value matches an ID from its lookup cache. For exact UI fidelity, fetch the real ID via `uip is resources execute <connector-key> list <object-name> --connection-id <uuid>` against the field's `lookup.path` (often `/MailFolders`, `/Folders`, etc.).
- **Heuristic:** when the stub returns empty `queryParameters` / `pathParameters` / `bodyParameters` for a non-trivial vendor operation, treat it as the bug. Real endpoints (CRUD on real objects, list-with-filters operations) almost never have zero required inputs.
- **Upstream:** the stub IS surfacing the metadata it has — `metadata.configuration` contains the full `inputFields` list — so this is a CLI-side fix where the stub should populate defaults/placeholders from `required: true` fields, not a missing-data issue. Until that ships, the cross-check is mandatory per skill rule 16 step 4.
- **See also:** [connector-activity-discovery.md — Required-field cross-check](connector-activity-discovery.md#required-field-cross-check--the-stub-drops-required-true-request-fields).

### `401 — Failed to execute IS call to /<endpoint>: Invalid Organization or User secret, or invalid Element token provided`

- **Symptom:** The workflow runs locally with `uip api-workflow run` but fails in StudioWeb cloud (or against the real IS proxy) with a 401 status. The error detail says `"Invalid Organization or User secret, or invalid Element token provided."` — sounds like a credential / auth-token issue but is often something else.
- **Cause:** The IS proxy's auth flow for `/elements_/v3/element/instances/{connectionId}/{operationName}` rejected the call. There are two distinct sub-cases — diagnose by looking at the URL the proxy hit:

  **Sub-case A — Wrong endpoint on the connection's element.** The endpoint in the proxy URL doesn't exist on the target connection's connector. Most common when an agent uses Http kind (`call: "UiPath.Http"` with `endpoint: "/http-request"`) but `connectionId` points at a vendor connection (Outlook, Gmail, etc.) instead of a `uipath-uipath-http` connection. The Outlook connector has no `/http-request` operation, only its curated ones (`/getNewestEmail`, `/sendEmail`, …) — so the proxy returns 401 as a generic "I can't service this request" rather than "operation not found."
  - **Fix:** Switch to IntSvc kind (`call: "UiPath.IntSvc"`, `with.connector` = the vendor key, `with.endpoint` = `"/<curated-operation-name>"`). See [connector-activity-discovery.md — IntSvc kind](connector-activity-discovery.md#intsvc-kind--call-uipathintsvc-vendor-curated-activity) — IntSvc kind is for vendor activities, Http kind is only for the `uipath-uipath-http` HTTP Request activity.

  **Sub-case B — Connection is in a broken state.** The endpoint is right (e.g. `/getNewestEmail` on an Outlook connection), but the connection's upstream OAuth token is expired, never properly authorized, or the running identity doesn't have access to the connection.
  - **Fix:** Run `uip is connections ping <connection-uuid> --output json`. If it returns `Code: "ConnectionNotEnabled"`, re-authenticate via `uip is connections edit <connection-uuid>` (opens browser for OAuth) or fix in the StudioWeb UI. If it returns `Code: "ConnectionPing"` (success) but the cloud still 401s, check that your CLI login (`uip login status`) is in the same org+tenant your browser is using at alpha.uipath.com — a tenant mismatch will reject the connection ID at the proxy layer.

- **Prevention:** The discovery flow's Step 4b (`uip is connections ping`) is mandatory specifically to catch sub-case B before authoring. Don't author against a connection that doesn't ping — the workflow shape will look right and even run locally, but fail at deployment time.

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
