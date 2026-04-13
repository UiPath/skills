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
