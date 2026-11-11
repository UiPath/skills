# Pattern: `parallel-agents`

Several agents work the same problem at once, each with a perspective, a
section, or an independent attempt, and a synthesis agent merges their outputs
into one answer. Use it when one agent's view is not enough and the views do
not depend on each other.

## Why it works

- **The agents are independent.** No agent reads another's output, so they run
  as parallel arms. Chaining them makes later agents echo earlier ones.
- **One join, then one synthesis.** A merge waits for every arm, and a single
  synthesis agent reads every agent's typed output by step name.
- **Disagreement stays visible.** Synthesis returns the conflicts or the
  dissent as its own field, rather than averaging it away.

## Shape

The `perspective-panel` variant:

| Step | Node | Builder | Role |
| --- | --- | --- | --- |
| `perspectiveA`, `B`, `C` | `uipath.agent.autonomous`, one per arm | `inlineAgent({ returns })` in each arm of `.parallel(...)` | Mechanism: size the panel to the request |
| `joinPerspectives` | `core.logic.merge` | the `.parallel('joinPerspectives', arms)` name | Mechanism |
| `synthesize` | `uipath.agent.autonomous` | `inlineAgent({ inputs, returns })` | Mechanism |
| `endDone` | `core.control.end` | `.return(...)` | Entry |

| From | Port | To |
| --- | --- | --- |
| preceding step | | each `perspective*` |
| each `perspective*` | `success` | `joinPerspectives` |
| `joinPerspectives` | `output` | `synthesize` |
| `synthesize` | `success` | `endDone` |

Each panel agent reads the same input and returns `findings`, `concerns` and
`severity`. `synthesize` takes each agent's output as an input
(`out('perspectiveA')`, ...) and returns `recommendation`, `conflicts` and
`confidence`. The canvas draws a `fanOut` merge before the arms; the builder
fans out from the preceding step, and both are the same shape.

## Variants

| Variant | What the agents get | Synthesis returns |
| --- | --- | --- |
| `perspective-panel` | The same input, each with a different lens (legal, financial, operational) | `recommendation`, `conflicts`, `confidence` |
| `task-sectioning` | One section of the input each | `assembled`, `gaps`, `confidence` |
| `consensus` | The same task, each with a different framing | `verdict`, `agreement` (`unanimous`, `majority`, `split`), `dissent` |

**`task-sectioning`.** Split the input before the pattern, one value per
section, and give each agent only its section. The assembler reports `gaps`
that no single section could resolve.

**`consensus`.** Each attempt works without seeing the others. Attempts differ by
prompt and framing.

## What to bind

- **Each agent**: a published agent, else an `inlineAgent` with `returns`, never
  `mock()`. Write its lens, section or framing into its prompt; never produce
  the findings yourself.
- **`synthesize`**: every arm's output as an input, and a prompt that keeps
  conflicts or dissent separate from the answer.

## Adapting it

Add or remove arms to match the number of perspectives the request names. An
arm must not end in a human task or a `.return()` (`check`:
`HITL_FAN_OUT_INTO_JOIN`, `PARALLEL_ARM_RETURNS`); keep reviews and early exits
after `synthesize`.
