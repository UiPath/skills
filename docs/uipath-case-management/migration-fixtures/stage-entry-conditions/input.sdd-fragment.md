# Minimal sdd fragment — stage-entry-conditions plugin

Exercises all five stage-entry rule-types by attaching five entry conditions to a single target stage. Intentionally omits edges, tasks, and stage exit rules — validation is expected to fail on those orthogonal concerns.

## Stages

| Stage | Purpose |
|---|---|
| Upstream | Source stage referenced by `selected-stage-*` rules. |
| Target | Receives all five entry conditions below. |

## Target — Entry Conditions

| # | Display name | Rule type | is-interrupting | Extra |
|---|---|---|---|---|
| 1 | From case start | `case-entered` | (default `false`) | — |
| 2 | After Upstream completes | `selected-stage-completed` | (default `false`) | selected-stage = "Upstream" |
| 3 | After Upstream exits | `selected-stage-exited` | `true` | selected-stage = "Upstream" |
| 4 | User-routed | `user-selected-stage` | (default `false`) | — |
| 5 | Fraud detected | `wait-for-connector` | `true` | condition-expression = `event.fraudScore > 0.8` |

Each condition is a separate T-task in `tasks.md` per the plugin's "No omission" rule.
