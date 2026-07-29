# Maximum Consecutive System Exceptions Reached

Reproduces the `job-consecutive-system-exceptions` playbook: a
REFramework job aborts on its consecutive-System-Exception ceiling,
but the abort is a **symptom** — the real cause is the exception that
recurs on every transaction.

```
The maximum number of consecutive system exceptions was reached.
Consecutive retry number: 5.
```

## What this scenario uncovers

**Root Cause:** A `SelectorNotFoundException` on the "Click Submit"
activity is thrown on every transaction (the order-portal UI
changed). After 5 consecutive system exceptions the framework
aborts. The graded diagnosis is the **recurring selector failure**,
not the threshold — and the fix is to repair the selector, not to
raise `MaxConsecutiveSystemExceptions`.

Maps to:
`references/products/orchestrator/playbooks/job-consecutive-system-exceptions.md`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../../_shared/mock_template/` |
| `process/` | minimal REFramework-style UiPath project |
| `data/m/r/*.json` | **synthetic** canned `uip` responses — logs carry the recurring SelectorNotFoundException (5×) before the abort; traces show "Click Submit" faulting every transaction |
| `data/m/r/manifest.json` | dispatch table |

> Fixtures authored from the playbook signature, not captured from a
> real session.

## Distinguishing fingerprint

The job Info gives only the abort message — the root cause is
reachable only by reading the logs/traces and spotting the identical
`SelectorNotFoundException` repeated per transaction. This makes the
scenario resist a "read the Info and answer" bypass: an agent that
stops at the abort message (or suggests raising the threshold) scores
low; one that finds the recurring selector failure scores full.

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the recurring "Click Submit" SelectorNotFound-
  Exception as the root cause (not the threshold) and recommended
  fixing the selector (re-indicate / Object Repository / anchor +
  Check State) rather than raising MaxConsecutiveSystemExceptions.
