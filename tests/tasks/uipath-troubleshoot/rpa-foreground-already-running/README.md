# Rpa Foreground Already Running — Concurrent Foreground Job Rejection

This scenario reproduces a runtime fault caused by **two foreground
(UI-interactive) jobs scheduled against the same Robot session with
overlapping start times**. The Robot rejects the second start with:

```
System.InvalidOperationException: A foreground process is already running.
Only one foreground process can run at a time.
```

## What this scenario uncovers

**Root Cause:** A second `ForegroundHolder` job (key `c0a1b2c3-...`)
was triggered at `2026-05-12T10:15:00Z` while an earlier
`ForegroundHolder` job (key `b0a1b2c3-...`, started
`2026-05-12T10:14:50Z`) was still in `Running` state on the same
machine. Both have `RequiresUserInteraction: true` (foreground). The
Robot enforces a single-foreground-job-per-session constraint and
faults the second start within ~0.7s.

This maps to:
`references/products/orchestrator/playbooks/foreground-already-running.md`
(the "Two foreground triggers fire on overlapping schedules" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | snapshot of `skills/uipath-troubleshoot/fixtures/foreground-already-running/ForegroundHolder/` — the foreground project that's failing |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

> **Note on fixtures.** Like sibling synthetic scenarios, the fixtures
> here were authored from the documented playbook signature rather
> than captured from a real `.investigation/` session. Regenerate via
> `_shared/scripts/generate_scenario.py` from a real failed-job
> session before treating this test's score as a regression signal.

## How this differs from the sibling foreground playbook

There are **two** UiPath playbooks that mention "foreground" — agents
must pick the right one:

| Dimension | `maestro/foreground-unattended-robot` (sibling) | `orchestrator/foreground-already-running` (this) |
|---|---|---|
| HTTP status | 409 | n/a (Robot-side guard, not HTTP) |
| Error code / class | Orchestrator `#1230` | .NET `System.InvalidOperationException` |
| Error message anchor | "Foreground job requires an unattended robot to be defined on your user" | "A foreground process is already running. Only one foreground process can run at a time." |
| Root cause class | Missing unattended robot configuration on the user | Concurrent foreground execution on a single Robot session |
| Fix | Provision unattended robot + machine credentials | Sequence triggers / "Run only one job at a time" / convert to background |

A correct agent matches the **this** playbook by the exception text
and the presence of an overlapping Running job in the same folder,
NOT by the word "foreground" alone.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `orchestrator/foreground-already-running` (not the
  maestro `#1230` playbook) AND reached the same root cause as
  `RESOLUTION.md`
- Conclusion must explicitly name the concurrent foreground job
  conflict (overlapping Running job at the time of failure) and
  propose a valid fix from the playbook's resolution list

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.investigation> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name rpa-foreground-already-running --apply
```
