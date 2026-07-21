# VisualBasicValue Requires Compilation — Smart Quotes

This scenario reproduces an Orchestrator job that faults with
`Expression Activity type 'VisualBasicValue`1' requires compilation in order to run.`

## What this scenario uncovers

**Root Cause:** The `Assign 'Build Greeting'` value expression in `Main.xaml` was
pasted from rich text and uses curly/smart double quotes (U+201C and U+201D)
instead of straight ASCII quotes (U+0022). The expression could not be compiled
ahead-of-time; the project is `VisualBasic` / `targetFramework: Windows` (.NET 6+,
runtime JIT disabled), so the uncompiled expression throws at run. The designer
shows the workflow as valid.

This maps to:
`skills/uipath-troubleshoot/references/runtime-exceptions/playbooks/visualbasicvalue-requires-compilation.md`

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | `InvoiceNotifier` — VB / Windows project; `Assign 'Build Greeting'` value uses smart quotes |
| `fixtures/mocks/responses/*.json` | synthetic canned `uip` responses; the faulted job's `Info` carries the `VisualBasicValue`1 requires compilation` error and the stack frame at `Assign 'Build Greeting'` |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The decisive evidence is the smart double quotes (U+201C/U+201D) in the
`Assign 'Build Greeting'` value in `process/Main.xaml` — the agent must read the
workflow source, not just the job logs, to identify them.

## Success criteria

The test scores the conclusion, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause + fix as `RESOLUTION.md`

> **Note on fixtures.** Synthetic. Job key, folder key, and host are placeholders.
> The error is a robot/Orchestrator-runtime fault and is not reproducible via the
> local `uip rpa` CLI (which AOT-compiles expressions); the mocks supply the
> faulted-job evidence.
