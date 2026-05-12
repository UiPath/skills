# Control Flow Patterns

Hierarchical structures combining If, ForEach, DoWhile, Break, and TryCatch. Use this reference when authoring workflows whose logic goes more than one level deep.

For per-activity field-level details (required fields, export patterns, minimal JSON), see [task-types.md](task-types.md). This document focuses on **how to combine them**.

## Core Structural Rules

1. **Every key in the workflow must be globally unique.** This includes wrapper / branch / body suffixes. Two `If_1#Then` blocks anywhere in the workflow — even at totally different nesting levels — is invalid. Increment the number suffix when you reuse a pattern.
2. **Wrapper / Body suffixes are part of the key.** `If_1#Wrapper`, `If_1#Then`, `If_1#Else`, `For_Each_1#Body`, `Do_While_1#Body` are FOUR separate keys (or five for If). All five count toward uniqueness.
3. **`then: "exit"` exits the immediately enclosing container** (the If's branch, the Sequence, etc.) — it's a "stop processing this list" signal, not a workflow terminator.
4. **`then: "end"` terminates the entire workflow run.** Only Response activities use it.
5. **Break exits only the innermost enclosing loop.** To exit multiple loops, use a flag variable + a check + another Break.
6. **`#Wrapper` and `#Body` are not interchangeable.** If's wrapper is `#Wrapper`. ForEach/DoWhile body is `#Body`. There is no `#Body` for If, and no `#Wrapper` for loops.
7. **Loop iteration variables (`for.each` / `for.at`) are scoped to that loop's body** AND get a literal `$` prefix when referenced. `for.each: "currentItem"` → reference as `$currentItem` (with the `$` character in the identifier name). Same for `for.at: "currentItemIndex"` → `$currentItemIndex`, and `catch.as: "error"` → `$error`. Nested loops MUST use distinct names — `outerItem` / `outerIndex` for the outer, `innerItem` / `innerIndex` for the inner (referenced as `$outerItem` / `$innerItem` in expressions).

## Key Numbering Convention

When you nest, increment numbers monotonically across the whole workflow — don't restart per scope.

```
Sequence_1
├─ Assign_1
├─ For_Each_1
│   └─ For_Each_1#Body
│       ├─ If_1#Wrapper        ← inside the loop body, but uses _1 because no other If yet
│       │   ├─ If_1
│       │   ├─ If_1#Then
│       │   └─ If_1#Else
│       └─ Try_Catch_1         ← _1 because no other TryCatch yet
└─ If_2#Wrapper                ← _2 because If_1 was already used inside the loop
    ├─ If_2
    ├─ If_2#Then
    └─ If_2#Else
```

The numbering reflects **author order across the whole workflow**, not nesting depth.

## Pattern Catalog

### 1. Nested If (multi-level decision tree)

When you have decisions inside decisions. Each If gets its own wrapper/then/else suffix set.

```
Sequence_1
└─ If_1#Wrapper                         (outer: amount > 1000?)
    ├─ If_1
    ├─ If_1#Then
    │   └─ If_2#Wrapper                 (inner: priority === 'high'?)
    │       ├─ If_2
    │       ├─ If_2#Then  → [Assign tier=PLATINUM]
    │       └─ If_2#Else  → [Assign tier=GOLD]
    └─ If_1#Else
        └─ Assign tier=STANDARD
```

The inner If is a child of `If_1#Then.do[]`. Its `If_2#Then` and `If_2#Else` are siblings of `If_2`. **All five suffixes are unique keys.**

```json
{
  "If_1#Then": {
    "do": [
      {
        "If_2#Wrapper": {
          "do": [
            { "If_2": { "switch": [
                { "case": { "when": "${$context.variables.priority === 'high'}", "then": "If_2#Then" } },
                { "default": { "then": "If_2#Else" } }
              ], "metadata": { "displayName": "If" } } },
            { "If_2#Then": { "do": [ /* tier=PLATINUM */ ], "then": "exit" } },
            { "If_2#Else": { "do": [ /* tier=GOLD */ ], "then": "exit" } }
          ],
          "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"If_2\": $output } }" },
          "metadata": { "activityType": "If", "displayName": "If", "fullName": "If" }
        }
      }
    ],
    "then": "exit"
  }
}
```

### 2. Multi-way branching (3+ outcomes)

The cleanest authorings is **a chain of two-way Ifs**. Each If's `#Else` contains the next If.

```
If_1#Wrapper        (x > 100?)
├─ If_1#Then  → [tier=PLATINUM]
└─ If_1#Else
    └─ If_2#Wrapper (x > 50?)
        ├─ If_2#Then  → [tier=GOLD]
        └─ If_2#Else
            └─ If_3#Wrapper (x > 0?)
                ├─ If_3#Then  → [tier=STANDARD]
                └─ If_3#Else  → [tier=NONE]
```

Why chain rather than packing many cases into one switch: StudioWeb's designer renders two-way If cards cleanly; multi-case switches render less predictably.

### 3. ForEach with per-iteration If (filter / classify)

Common pattern: iterate, decide per item, do something different per branch.

```
For_Each_1
└─ For_Each_1#Body
    ├─ If_1#Wrapper          ($currentItem.priority === 'high'?)
    │   ├─ If_1#Then  → [Assign highCount = highCount + 1]
    │   └─ If_1#Else  → [Assign lowCount = lowCount + 1]
    └─ Javascript_1          (transform $currentItem and accumulate)
```

Inside `If_1`'s `when`, use `$currentItem` (with the `$` literal prefix — NOT `currentItem`, NOT `$context.variables.currentItem`):

```json
"when": "${$currentItem.priority === 'high'}"
```

### 4. ForEach inside ForEach (nested iteration)

Outer and inner loops MUST use distinct iterator/index names — either semantic (`outerItem` / `innerItem`, `customer` / `order`) or incremental (`item1` / `item2`, `currentItem` / `currentItem2`). The constraint is "not the same string", not "different concepts".

```
For_Each_1 (each: outerItem, in: $workflow.input.matrix, at: outerIdx)
└─ For_Each_1#Body
    └─ For_Each_2 (each: innerItem, in: ${$outerItem.children}, at: innerIdx)
        └─ For_Each_2#Body
            └─ Javascript_1   (sees $outerItem, $innerItem, $outerIdx, $innerIdx as globals)
```

The inner loop's `for.in` reads from the outer iterator: `"${$outerItem.children}"`. Both `$outerItem` and `$innerItem` are globals available inside the inner body.

### 5. Conditional Break inside a loop

Break must be wrapped in an If — there's no "break when" condition on Break itself.

```
For_Each_1#Body
├─ Javascript_1   (process $currentItem)
└─ If_1#Wrapper   (some stop condition?)
    ├─ If_1#Then  → [Break_1]
    └─ If_1#Else  → []
```

The Break exits the *innermost* loop. To break out of TWO nested loops:

```
For_Each_1 (outer)
└─ For_Each_1#Body
    ├─ For_Each_2 (inner)
    │   └─ For_Each_2#Body
    │       └─ If_1#Wrapper
    │           ├─ If_1#Then → [Assign abortFlag = true, Break_1]   ← exits inner only
    │           └─ If_1#Else → []
    └─ If_2#Wrapper                                                 ← after inner loop
        ├─ If_2 (when: ${$context.variables.abortFlag})
        ├─ If_2#Then  → [Break_2]                                   ← exits outer
        └─ If_2#Else  → []
```

`abortFlag` must be a workflow variable so it persists across iteration boundaries.

### 6. TryCatch around a loop (whole-batch error handling)

If any iteration throws, the whole loop aborts and execution jumps to `catch.do`. Use when one bad item should kill the batch.

```
Try_Catch_1
├─ try:
│   └─ For_Each_1
│       └─ For_Each_1#Body
│           └─ Javascript_1   (might throw)
└─ catch (as: error):
    └─ Assign  errorMsg = ${$error.title}, status = "batch-failed"
```

### 7. TryCatch inside a loop body (skip-and-continue error handling)

Each iteration has its own try/catch. A failure in one iteration is caught locally; the loop continues to the next iteration. **More common in practice than pattern 6.**

```
For_Each_1
└─ For_Each_1#Body
    └─ Try_Catch_1
        ├─ try:
        │   └─ Javascript_1   (might throw)
        └─ catch (as: error):
            └─ Assign  failedItems = failedItems + 1
```

The TryCatch's number suffix (`Try_Catch_1`) is fine inside the body even though the body runs N times — keys are checked structurally, not per-iteration. Each iteration sees the same key.

### 8. DoWhile with mid-body Break

Use a DoWhile when the iteration count depends on per-iteration logic, not a precomputed array. Add a Break for early exit.

```
Do_While_1                       (doWhile: ${$context.variables.attempts < maxAttempts && !$context.variables.found})
└─ Do_While_1#Body
    ├─ Javascript_1              (does some probe; sets $output)
    ├─ Assign  attempts = attempts + 1
    └─ If_1#Wrapper              (success?)
        ├─ If_1#Then  → [Assign found = true, Break_1]
        └─ If_1#Else  → []
```

The `doWhile` condition is evaluated AFTER each iteration. The body always runs at least once. The Break takes effect immediately — the `doWhile` re-evaluation is skipped.

### 9. TryCatch inside If branch

Handle a risky operation that's only attempted on certain conditions.

```
If_1#Wrapper                     (should we attempt the risky op?)
├─ If_1#Then
│   └─ Try_Catch_1
│       ├─ try:  → [Javascript_1 risky]
│       └─ catch (as: e):
│           └─ Assign  status = "failed-with-fallback"
└─ If_1#Else
    └─ Assign  status = "skipped"
```

### 10. Per-iteration result aggregation across nested control flow

If you want a clean array of per-iteration results that includes results from inside nested Ifs, the For_Each body's standard accumulation pattern (the index-aware `results: [...]` export) handles it — the body's `$output` is whatever the last activity in the body produced.

```
For_Each_1#Body
├─ If_1#Wrapper
│   ├─ If_1#Then → [Javascript_1 → returns { kind: "high", ... }]
│   └─ If_1#Else → [Javascript_2 → returns { kind: "low", ... }]
└─ Javascript_3 → returns { ...$context.outputs.If_1, processed_at: Date.now() }
```

The body's `$output` will be `Javascript_3`'s return value (last activity wins). The accumulation pattern appends that to `For_Each_1.results`.

If you want to capture the If's own output too, use `$context.outputs.If_1` (the wrapper exports under the If's number, not the branch name).

## Anti-patterns

- **Reusing `If_1#Then` in two different Ifs** — even at different nesting levels. Always increment.
- **Forgetting `then: "exit"` on inner If branches** — fall-through still happens at every nesting level.
- **Putting Break in a TryCatch's catch.do that's not inside a loop** — Break has no enclosing loop to exit.
- **Reusing iteration variable names across nested loops** — inner loop's `currentItem` shadows the outer one. Use `outerItem` / `innerItem` or descriptive names.
- **Using a workflow variable as a loop iterator** — the variable's value will be the LAST iteration's item after the loop ends, plus you've polluted `$context.variables`. Use `for.each` (a loop-local binding), not Assign-then-iterate.
- **Mixing `then: "exit"` and `then: "end"`** — `exit` stops the current container; `end` terminates the workflow. Only Response uses `end`.
- **Trying to short-circuit evaluation in the switch via `case` ordering** — first matching case wins, but ALL cases' `when` expressions are evaluated. Don't rely on side effects in earlier `when`s.

## Decision Cheat Sheet

| You want… | Use |
|-----------|-----|
| Branch on a condition | If with `#Wrapper` / `#Then` / `#Else` |
| Three+ branches | Chain of two-way Ifs (each `#Else` holds the next If) |
| Iterate over an array | ForEach with `for.each` / `for.in` / `for.at` |
| Loop until a condition | DoWhile with `for.in: "${ [1] }"` and `doWhile: "${...}"` |
| Exit a loop early | Break inside an If inside the loop's `#Body` |
| Exit nested loops | Flag variable + Break in inner + If + Break in outer |
| Catch errors anywhere | TryCatch — choose `around-loop` vs `inside-body` based on whether one error should kill the batch |
| Run two activities in order | Place both inside a Sequence's `do` array — order is preserved |
| Branch on an error type | If inside `catch.do`, switching on `${$error.title}` or `${$error.originatingTaskName}` |
| Conditionally return early | Response inside an If's `#Then` (with `then: "end"`) |
