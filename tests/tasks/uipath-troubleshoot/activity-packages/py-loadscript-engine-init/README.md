# Load Python Script Failure - Python Engine Fails to Initialize

This scenario reproduces a `Load Python Script` (`UiPath.Python.Activities.LoadScript`)
failure caused by the parent `Python Scope` being unable to **initialize
the Python engine** on the robot host. The job faults at startup with
`Error initializing Python engine 64 bit` before the script body loads.

## What this scenario uncovers

**Root Cause:** The `Python Scope` targets Python 3.11 (`Path=C:\Python311`,
`Version=Auto`, `Target=x64`) but its **`Library path` is empty**. On
Windows, for Python **> 3.9** the `Library path` must point at the matching
`pythonXX.dll` (`python311.dll`); left empty, the engine cannot initialize,
so `Load Python Script` faults before loading the script. A bitness
mismatch between the installed interpreter and `Target = x64` produces the
same error and must be ruled out on the host.

This maps to:
`references/activity-packages/python-activities/playbooks/load-script-failures.md`
(engine-initialization family, sub-causes L1c `Library path` and L1b bitness).

The user is framed as **off-host** (Orchestrator only), so the correct
agent behavior is to identify the engine-init failure, recommend setting
the `Library path` for Python > 3.9 (and/or verifying interpreter bitness),
and hand over the host checks - not to attempt host commands itself.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Python Scope` + `Load Python Script`, `Library path` left empty |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `load-script-failures.md` and identified an engine-initialization
  failure (not a `ModuleNotFoundError` or syntax error)
- Agent recommended setting the `Library path` to the matching `pythonXX.dll`
  for Python > 3.9, and/or verifying the interpreter bitness against
  `Target = x64` (any valid engine-init fix path scores full marks),
  without fabricating host actions
