# Job Stopped — Exit Code 0xE0434352 (hidden KeyNotFoundException)

Reproduces the `0xE0434352` branch of the **Job Stopped —
Unexpected Exit Code (generic)** playbook: an unhandled managed .NET
exception escapes to the process boundary and collapses to the raw
CLR exit code. The job shows only:

```
System.Exception: Job stopped with an unexpected exit code: 0xE0434352
```

The real cause is recoverable only from execution traces.

## What this scenario uncovers

**Root Cause:** An unhandled
`System.Collections.Generic.KeyNotFoundException` ("the given key
'EMEA-NORTH' was not present in the dictionary") at the "Lookup
region total" Assign. With no top-level Try/Catch or Global
Exception Handler, it reached the process boundary. The host robot
(`23.4.0`) is an old build that reports the raw OS/CLR code instead
of the managed exception — so the job Info and logs show only
`0xE0434352`, and the real error lives in `uip or jobs traces`.

Maps to:
`references/products/orchestrator/playbooks/job-stopped-generic-exit-code.md`
(0xE0434352 branch). Also exercises the `KeyNotFoundException`
"given key was not present in the dictionary" signature.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../../_shared/mock_template/` |
| `process/` | minimal unattended UiPath project (LogMessage + Delay) |
| `data/m/r/*.json` | **synthetic** canned `uip` responses (jobs get/list/logs, **jobs traces** carrying the real exception, machines list with old robot version) |
| `data/m/r/manifest.json` | dispatch table mapping each command to its fixture |

> Fixtures are authored from the playbook signature, not captured
> from a real session. Regenerate via
> `_shared/scripts/generate_scenario.py` before treating the score
> as a strict regression signal.

## Distinguishing fingerprints

| Code / playbook | Fingerprint that rules it out here |
|---|---|
| `0x40010004` external kill | Different code; that playbook is for `TerminateProcess`. Here the process died from its own managed exception. |
| `0xC0000005` native access violation | The traced exception is managed (`KeyNotFoundException`), not a native crash. |
| `0xC000026B` session teardown | No logoff/shutdown; fault is in workflow logic. |
| **`0xE0434352`** *(this scenario)* | Traces show an unhandled managed exception (`KeyNotFoundException`) that escaped to the process boundary. |

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent did NOT stop at the raw code or merely suggest a rerun — it
  recovered the real `KeyNotFoundException` (missing dictionary key)
  from traces, and recommended guarding the lookup, adding top-level
  exception handling, and upgrading the old robot so codes surface
  as managed exceptions.
