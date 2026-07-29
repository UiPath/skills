# If — Condition Compiler / Expression Error (Design-Time)

Design-time (Studio) troubleshooting scenario for `System.Activities.Statements.If`.

## What this scenario exercises

Studio's Error List flags an `If` with `Compiler error(s) encountered processing expression` /
`Option Strict On disallows implicit conversions`. The agent must recognize this as a **type-mismatch
comparison in the `If` Condition** — `responseCode` is `System.Int32`, compared against the `String`
literal `"200"` — and prescribe comparing like types (`responseCode = 200`, or an explicit
`.ToString()` / `CInt` conversion). This is a design-time validation error, not a robot job fault and
not corrupt XAML / a missing package.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted VB project source: `Main.xaml` with an `If` whose Condition is `responseCode = "200"` where `responseCode` is declared `System.Int32`; `project.json` sets `expressionLanguage: VisualBasic` |
| `data/m/r/manifest.json` | `docsai ask` passthrough + permissive empty `unmocked_default` — no job/trace exists for a design-time error |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the `Integer`-vs-`String` type mismatch in the `If` Condition and the fix (compare
  like types / convert explicitly — do NOT rebuild the `.xaml`, reinstall the package, or hunt for a
  faulted job).

Playbook: `references/runtime-exceptions/playbooks/if-condition-compiler-error.md`.
