# Exception Stage — Planning

An `ExceptionStage` is a stage used as an error or exception handler that branches off the main flow.

## When to Use ExceptionStage vs Regular Stage

| Situation | ExceptionStage? |
|---|---|
| Stage handles errors or exceptions from another stage | Yes |
| All tasks should always re-run if the stage is re-entered | Yes |
| Stage is part of the normal sequential workflow | No — use regular Stage |
| Stage may have some tasks that run once and others that repeat | No — use regular Stage with per-task `shouldRunOnlyOnce` |

## Key Behavioural Difference

In an `ExceptionStage`, **all tasks always run on re-entry** regardless of `shouldRunOnlyOnce`. This is forced by the runtime. Use this when every step of the error-handling flow should re-execute each time the exception handler is invoked.

## Typical Pattern

```
Main Stage ──(error path)──► ExceptionStage ──(return-to-origin)──► back to Main Stage
```

1. Main stage has a task that can fail
2. On failure, flow enters the ExceptionStage (via `adhoc` or `selected-stage-exited` entry condition)
3. ExceptionStage handles the error (notifies team, logs, retries)
4. ExceptionStage exits with `return-to-origin` — control returns to the originating main stage

## Exit Type

Always use `"return-to-origin"` exit condition on ExceptionStage unless the exception is terminal (case should end). For terminal exceptions, use a case exit condition instead.

## Graph Layout

Place ExceptionStage **below** the main flow and connect with `bottom` → `top` handles to distinguish it visually from the sequential flow.

## Multi-Source Entry Pattern

ExceptionStages often receive entries from **multiple** main-flow stages. For example, a "Pending with customer" stage may activate from Intake, Review, Settlement, or Closure — any stage where the case needs customer input.

In the spec, look for:
- "Can be triggered from any stage where..."
- "Activated when decision is X from multiple stages"
- "Global exception handler for..."

In tasks.md, create **one entry condition per source stage**:

```
## T50: Add stage entry condition for "Pending with customer" — from Intake
- rule-type: selected-stage-exited
- selected-stage-id: "Intake"
- condition: decision == "Claim needs info from customer"
- isInterrupting: true
- order: after T49

## T51: Add stage entry condition for "Pending with customer" — from Review
- rule-type: selected-stage-exited
- selected-stage-id: "Review"
- condition: decision == "Claim needs info from customer"
- isInterrupting: true
- order: after T50

## T52: Add stage entry condition for "Pending with customer" — from Settlement
- rule-type: selected-stage-exited
- selected-stage-id: "Settlement"
- condition: decision == "Claim needs info from customer"
- isInterrupting: true
- order: after T51
```

Key points:
- Each entry needs `isInterrupting: true` to preempt the source stage
- Use `selected-stage-exited` (not `selected-stage-completed`) when the source stage is still active
- The `condition` field is human-readable; implementation phase translates to `=js:vars.decision == "..."`

## Re-entry Counter Variables

When an ExceptionStage returns to a main-flow stage that can be re-entered, the spec may describe different behavior on re-entry (e.g., "skip initial tasks on second run"). This requires a counter variable.

In the spec, look for:
- "On re-entry, only run the follow-up task"
- "Skip initial processing if returning from exception"
- "First run vs subsequent runs"

In tasks.md, declare the counter:

```
## T70: Declare re-entry counter for "Intake"
- variable-name: finishedRunCountIntake
- type: number
- internal: true
- order: after T69
```

Then reference it in task entry conditions:

```
## T75: Add task entry condition for "Incident reports" in "Intake" — re-entry only
- rule-type: current-stage-entered
- condition: finishedRunCountIntake > 0
- order: after T74
```

See [impl.md](impl.md) for the full JSON patterns.
