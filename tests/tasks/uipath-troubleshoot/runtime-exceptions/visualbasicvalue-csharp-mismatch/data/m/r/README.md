# VisualBasicValue Requires Compilation — Expression-Language Mismatch

This scenario reproduces an Orchestrator job that faults with
`Expression Activity type 'VisualBasicValue`1' requires compilation in order to run.`

## What this scenario uncovers

**Root Cause:** The `OrderRouter` project is `expressionLanguage: CSharp` /
`targetFramework: Windows`, but the `Assign 'Build Route Key'` value is a
`VisualBasicValue` node (a VB `&` concatenation) — a VB expression left in a C#
project, typically from pasting an activity copied out of a VB project. Modern
.NET projects disable runtime expression JIT, so the stray VB expression has no
compiled delegate and throws at run. The designer shows the workflow as valid.

This maps to:
`skills/uipath-troubleshoot/references/runtime-exceptions/playbooks/visualbasicvalue-requires-compilation.md`

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | `OrderRouter` — C# / Windows project; `Assign 'Build Route Key'` value is a `<mva:VisualBasicValue>` node |
| `fixtures/mocks/responses/*.json` | synthetic canned `uip` responses; the faulted job's `Info` carries the `VisualBasicValue`1 requires compilation` error and the stack frame at `Assign 'Build Route Key'` |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The decisive evidence is the mismatch: `project.json` declares
`expressionLanguage: CSharp`, yet `Main.xaml` carries a `VisualBasicValue` node.
The agent must read both the project file and the workflow source to identify it.

## Success criteria

The test scores the conclusion, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause + fix as `RESOLUTION.md`

> **Note on fixtures.** Synthetic. Job key, folder key, and host are placeholders.
> The error is a robot/Orchestrator-runtime fault and is not reproducible via the
> local `uip rpa` CLI (which AOT-compiles expressions); the mocks supply the
> faulted-job evidence.
