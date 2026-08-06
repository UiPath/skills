# Python Scope Hangs / Freezes with No Error - Missing .NET Desktop Runtime

This scenario reproduces a `Python Scope` that **hangs with no error**. A
Windows-target project on `UiPath.Python.Activities` 1.10.0 runs on a robot host
that is **missing the .NET Desktop Runtime**, so the Python host process never
becomes ready. The job stalls until it is stopped on the max-execution timeout -
with no Python traceback and no engine-init exception.

## What this scenario uncovers

**Root Cause:** On `UiPath.Python.Activities` v1.9.0+ with the project target
framework set to **Windows**, the Python host runs on the .NET Desktop Runtime.
The new robot host lacks it, so the host process never starts and the scope
hangs (here, a runtime job that is killed after 15 minutes; the same root cause
freezes Studio at design time).

This maps to:
`references/activity-packages/python-activities/playbooks/python-scope-hang-dotnet-runtime.md`

The discriminator vs `python-scope-architecture-version-mismatch.md`: that
playbook keys on an engine-init **error** (bitness / Version / Library path); a
**hang with no error** points at the missing .NET Desktop Runtime. The scope
config here is otherwise valid (Path, `LibraryPath` python311.dll, Target x64),
and the script never runs - so it is not a bitness, Library-path, or script bug.
The user is framed as **off-host**, so the correct agent behavior is to hand
over the Event Viewer / `dotnet --list-runtimes` host check and recommend
installing the runtime (or switching to Windows-Legacy) - not to run host
commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `process/` | hand-authored UiPath project with `targetFramework: Windows`, `UiPath.Python.Activities 1.10.0`, a validly-configured `Python Scope` -> `Load Python Script` -> `Invoke Python Method`, and a clean `scripts/score_model.py` |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `python-scope-hang-dotnet-runtime.md`
- Agent identified a missing .NET Desktop Runtime on a Windows-target (v1.9.0+)
  project as the cause of the hang (not a bitness / Library-path / script bug)
  and recommended installing the .NET Desktop Runtime 6.0 (x64) or switching to
  Windows-Legacy, handing over the host check, without fabricating host actions

## Fixture isolation

`data/uip-fixture.json` is a finite command/response map mounted only into coder-eval's UID/GID-isolated mock service. The evaluated agent receives a bounded `uip` client and cannot read the fixture or mock implementation.
