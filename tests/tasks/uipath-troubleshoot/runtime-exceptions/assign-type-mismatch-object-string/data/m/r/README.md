# Assign — Type Mismatch (Object → String, Design-Time)

Design-time (Studio) troubleshooting scenario for `System.Activities.Statements.Assign`.

## What this scenario exercises

Studio's Error List flags an `Assign` with `Cannot assign from type 'System.Object' to
'System.String'`. The agent must recognize this as a **type mismatch between the right-hand-side
expression and the target variable** — the RHS (`config("AccountName")` on a
`Dictionary(Of String, Object)`) returns `System.Object`, the target (`accountName`) is
`System.String` — and prescribe converting the RHS (`.ToString()` / cast) or realigning the target
type. This is a design-time validation error, not a robot job fault and not corrupt XAML.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` | shared manifest-driven mock dispatcher from `../../_shared/mock_template/` |
| `process/` | crafted VB project source: `Main.xaml` with an `Assign` whose `To` is a `String` variable and whose `Value` is `config("AccountName")` where `config` is `Dictionary(Of String, Object)`; `project.json` sets `expressionLanguage: VisualBasic` |
| `data/m/r/manifest.json` | `docsai ask` passthrough + permissive empty `unmocked_default` — no job/trace exists for a design-time error |

## Success criteria

Scores the **conclusion**, not the trajectory (`skill_triggered` + `llm_judge` against `RESOLUTION.md`):

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the `Object`→`String` type mismatch on the `Assign` and the fix (convert the RHS
  with `.ToString()` / an explicit cast, or change the target variable's type — do NOT rebuild the
  `.xaml` or hunt for a faulted job).

Playbook: `references/runtime-exceptions/playbooks/assign-type-mismatch.md`.
