# Rpa Foreground Misconfigured — Non-UI Workflow Wrongly Marked Foreground

This scenario reproduces a runtime fault caused by **a workflow that does
no UI interaction being incorrectly published as a foreground process**.
When another foreground job runs against the same Robot session, the
Robot rejects the misconfigured one with:

```
System.InvalidOperationException: A foreground process is already running.
Only one foreground process can run at a time.
```

The exception is the **same family** as the sibling
`rpa-foreground-already-running` scenario — the cause-branch and
correct fix are different.

## What this scenario uncovers

**Root Cause:** The `MisconfiguredForeground` workflow's `Main.xaml`
contains only `LogMessage` and `Delay` activities — **no UI
automation activities at all**. Yet `project.json` declares
`runtimeOptions.requiresUserInteraction: true`, so the Robot treats it
as a foreground process. It collides with a legitimately foreground
`ForegroundHolder` job that was running on the same Robot session and
faults at start.

This maps to:
`references/products/orchestrator/playbooks/foreground-already-running.md`
(the **"Process does not actually need UI interaction"** fix branch).

## How this differs from `rpa-foreground-already-running`

Both scenarios fault with the same `System.InvalidOperationException`.
The agent must inspect the **source code** to disambiguate the correct
fix:

| Dimension | `rpa-foreground-already-running` | `rpa-foreground-misconfigured` (this) |
|---|---|---|
| Failing process | `ForegroundHolder` (legitimately foreground) | `MisconfiguredForeground` (workflow does no UI work) |
| Blocking job | another `ForegroundHolder` (scheduled, overlap) | `ForegroundHolder` (active, holding the slot) |
| Cause-branch | Two foreground triggers overlap | One workflow is misconfigured as foreground |
| Primary fix | Stagger triggers / "Run only one job at a time" | **Set `requiresUserInteraction: false` in `project.json` / Studio "Starts in Background: Yes"** |
| Required agent action | Read job records to find overlap | **Read `Main.xaml` to confirm no UI activities, then read `project.json` to find the misconfig** |
| Wrong answer | Suggesting the misconfig fix | Suggesting only trigger sequencing without flagging the misconfig |

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | snapshot of `skills/uipath-troubleshoot/fixtures/foreground-already-running/MisconfiguredForeground/` — the misconfigured project |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Like sibling synthetic scenarios, the fixtures
> were authored from the documented playbook rather than captured from
> a real `.investigation/` session. Regenerate via
> `_shared/scripts/generate_scenario.py` from a real failed-job
> session before treating this test's score as a regression signal.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `orchestrator/foreground-already-running` (not the
  sibling maestro `#1230` playbook)
- Agent inspected `Main.xaml` and identified no UI activities
- Agent inspected `project.json` and identified
  `requiresUserInteraction: true` as the misconfiguration
- Conclusion recommends the `project.json` flip / Studio "Starts in
  Background: Yes" as the **primary** fix, targeted at
  `MisconfiguredForeground` (not at `ForegroundHolder`)

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.investigation> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name rpa-foreground-misconfigured --apply
```
