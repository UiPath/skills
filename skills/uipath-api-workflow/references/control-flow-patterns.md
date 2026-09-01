# Control Flow Patterns

Hierarchical combinations of If, ForEach, DoWhile, Break, and TryCatch. Use this reference for workflows whose logic goes beyond one level of nesting.

For per-activity fields, required values, export patterns, and minimal JSON, see [task-types.md](task-types.md). This document covers composition.

## Core Structural Rules

1. Every workflow key must be globally unique, including wrapper, branch, and body suffixes. Reusing `If_1#Then` anywhere is invalid; increment the number suffix.
2. Wrapper and body suffixes are separate keys: an If has `#Wrapper`, `#Then`, and `#Else`; ForEach and DoWhile have `#Body`. If has no `#Body`; loops have no `#Wrapper`.
3. `then: "exit"` exits the immediately enclosing container or branch and stops processing that list; it does not terminate the workflow.
4. `then: "end"` terminates the entire workflow run and is used only by Response activities.
5. Break exits only the innermost enclosing loop. To exit multiple loops, use a workflow flag, check it after the inner loop, and issue another Break.
6. Loop bindings are scoped to their loop body and require a literal `$` when referenced: `for.each: "currentItem"` becomes `$currentItem`; `for.at: "currentItemIndex"` becomes `$currentItemIndex`; `catch.as: "error"` becomes `$error`. Nested loops must use distinct names.

## Key Numbering Convention

Number activity patterns monotonically across the entire workflow in author order, not per scope. Every suffix counts toward uniqueness.

```text
Sequence_1
├─ Assign_1
├─ For_Each_1
│  └─ For_Each_1#Body
│     ├─ If_1#Wrapper
│     │  ├─ If_1
│     │  ├─ If_1#Then
│     │  └─ If_1#Else
│     │  └─ Try_Catch_1
└─ If_2#Wrapper
   ├─ If_2
   ├─ If_2#Then
   └─ If_2#Else
```

## Pattern Catalog

### 1. Nested If

Give each If its own globally unique wrapper, condition, then, and else keys. Nest the inner wrapper in the outer branch's `do[]`, and end each branch with `then: "exit"` to prevent fall-through.

```text
If_1#Wrapper
├─ If_1
├─ If_1#Then
│  └─ If_2#Wrapper
│     ├─ If_2
│     ├─ If_2#Then
│     └─ If_2#Else
└─ If_1#Else
```

The inner If is a child of `If_1#Then.do[]`; its branches are siblings of `If_2` and all suffixes are unique.

### 2. Multi-way branching (3+ outcomes)

Use a chain of two-way Ifs: put the next If in the preceding If's `#Else`.

```text
If_1#Wrapper
├─ If_1#Then → outcome 1
└─ If_1#Else
   └─ If_2#Wrapper
      ├─ If_2#Then → outcome 2
      └─ If_2#Else
         └─ If_3#Wrapper → remaining outcomes
```

This renders more predictably than packing many cases into one switch.

### 3. ForEach with per-iteration If

Put the If in `For_Each_1#Body` to filter or classify each item. Reference the iterator as `$currentItem`, not `currentItem` or `$context.variables.currentItem`.

```json
"when": "${$currentItem.priority === 'high'}"
```

### 4. ForEach inside ForEach

Use distinct iterator and index names, such as `outerItem`/`outerIdx` and `innerItem`/`innerIdx`.

```text
For_Each_1 (each: outerItem, in: $workflow.input.matrix, at: outerIdx)
└─ For_Each_1#Body
   └─ For_Each_2 (each: innerItem, in: ${$outerItem.children}, at: innerIdx)
      └─ For_Each_2#Body
         └─ Javascript_1
```

Inside the inner body, `$outerItem`, `$innerItem`, `$outerIdx`, and `$innerIdx` are available. The inner `for.in` may read from the outer iterator, for example `${$outerItem.children}`.

### 5. Conditional Break inside a loop

Break has no condition of its own; wrap it in an If inside the loop body.

```text
For_Each_1#Body
├─ Javascript_1
└─ If_1#Wrapper
   ├─ If_1#Then → Break_1
   └─ If_1#Else → []
```

Break exits the innermost loop. To exit two nested loops, assign `abortFlag = true` and Break in the inner loop, then check the workflow variable after that loop and Break in the outer loop.

### 6. TryCatch around a loop (whole-batch error handling)

Place the loop in `try.do` when any iteration failure should abort the whole loop and transfer control to `catch.do`.

```text
Try_Catch_1
├─ try.do
│  └─ For_Each_1
│     └─ For_Each_1#Body
│        └─ Javascript_1
└─ catch.do (as: error)
   └─ Assign using $error
```

### 7. TryCatch inside a loop body (skip-and-continue)

Place a TryCatch in `For_Each_1#Body` when each iteration should handle its own failure and allow the loop to continue.

```text
For_Each_1
└─ For_Each_1#Body
   └─ Try_Catch_1
      ├─ try.do → risky activity
      └─ catch.do → record failure
```

`Try_Catch_1` is valid inside the body even though the body executes repeatedly; keys are checked structurally, not once per runtime iteration. This is more common than whole-batch handling.

### 8. DoWhile with mid-body Break

Use DoWhile when iteration depends on per-iteration logic rather than a precomputed array. Its body runs at least once; `doWhile` is evaluated after each iteration. Break exits immediately and skips reevaluation.

```text
Do_While_1 (doWhile: ${$context.variables.attempts < maxAttempts && !$context.variables.found})
└─ Do_While_1#Body
   ├─ Javascript_1
   ├─ Assign attempts = attempts + 1
   └─ If_1#Wrapper
      ├─ If_1#Then → set found = true, Break_1
      └─ If_1#Else → []
```

For a DoWhile, use `for.in: "${ [1] }"` when a single-element input is required.

### 9. TryCatch inside If branch

Put a risky operation in a TryCatch inside `#Then` when it should run only for the selected condition; handle fallback in `catch.do` and the skipped case in `#Else`.

```text
If_1#Wrapper
├─ If_1#Then
│  └─ Try_Catch_1
│     ├─ try.do → risky activity
│     └─ catch.do → fallback
└─ If_1#Else → skipped status
```

### 10. Per-iteration result aggregation across nested control flow

The standard index-aware ForEach `results: [...]` export appends the body's `$output`. The body's output is the last activity in that body, including an activity after a nested If.

```text
For_Each_1#Body
├─ If_1#Wrapper
│  ├─ If_1#Then → Javascript_1
│  └─ If_1#Else → Javascript_2
└─ Javascript_3 → returns the per-item result
```

To include the If's output, reference `$context.outputs.If_1`; the wrapper exports under the If number, not the branch name.

## Anti-patterns

- Reusing `If_1#Then` or any other key, even at another nesting level; increment suffixes.
- Omitting `then: "exit"` on inner If branches; fall-through occurs at every nesting level.
- Putting Break in a TryCatch `catch.do` with no enclosing loop.
- Reusing iterator names in nested loops; the inner binding shadows the outer one.
- Using a workflow variable as a loop iterator. It remains set to the last item and pollutes `$context.variables`; use `for.each` instead.
- Mixing `then: "exit"` and `then: "end"`; `exit` stops the current container, while `end` terminates the workflow and is only for Response.
- Relying on switch `case` ordering to short-circuit evaluation. The first matching case wins, but all `when` expressions are evaluated; do not rely on earlier side effects.

## Decision Cheat Sheet

| You want… | Use |
|---|---|
| Branch on a condition | If with `#Wrapper` / `#Then` / `#Else` |
| Three or more branches | Chain two-way Ifs, nesting the next in `#Else` |
| Iterate over an array | ForEach with `for.each` / `for.in` / `for.at` |
| Loop until a condition | DoWhile with `for.in: "${ [1] }"` and `doWhile: "${...}"` |
| Exit a loop early | Break inside an If inside the loop's `#Body` |
| Exit nested loops | Workflow flag + inner Break + outer check and Break |
| Catch errors | TryCatch around the loop or inside the body, depending on batch semantics |
| Run activities in order | Put them in a Sequence's `do` array |
| Branch on an error type | If inside `catch.do`, using `${$error.title}` or `${$error.originatingTaskName}` |
| Conditionally return early | Response inside an If's `#Then`, with `then: "end"` |