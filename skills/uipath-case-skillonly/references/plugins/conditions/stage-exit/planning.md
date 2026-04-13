# Stage Exit Conditions — Planning

Stage exit conditions control when a stage completes and what happens to control flow afterward.

## Exit Type Selection

| Scenario | `type` |
|---|---|
| Stage finishes and flow follows the next edge automatically | `"exit-only"` |
| Stage finishes but waits for a human to select the next stage manually | `"wait-for-user"` |
| Stage finishes and control returns to whichever stage triggered entry | `"return-to-origin"` |

`"return-to-origin"` is the standard exit type for [exception stages](../../stage-types/exception-stage/impl.md).

## Exit Rule Selection

| Scenario | Rule |
|---|---|
| Exit when all required tasks finish | `required-tasks-completed` |
| Exit when specific tasks finish | `selected-tasks-completed` |
| Exit when a specific stage finishes | `selected-stage-completed` |
| Exit when a stage exits | `selected-stage-exited` |
| Exit when connector event fires | `wait-for-connector` |

**Most common pattern:** `required-tasks-completed` with `"exit-only"` and `marksStageComplete: true`.

## marksStageComplete

Set to `true` when this exit condition marks the stage as officially complete. Triggers any other conditions elsewhere in the case that depend on `selected-stage-completed` for this stage.

## exitToStageId

Optional on `"exit-only"` conditions — explicitly routes flow to a specific stage instead of following the graph edge. Omit if you want flow to follow the edge normally.
