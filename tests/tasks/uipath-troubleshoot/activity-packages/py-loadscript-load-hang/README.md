# Load Python Script Hang - stdout Flood at Module Load (L3)

This scenario reproduces a `Load Python Script` hang. `scripts/aggregate.py` has
a module-level loop that prints every row to stdout at import; because Load
Python Script executes the module body, the stdout flood saturates the engine
pipe and the load never completes within the 30s `Timeout`, so the scope faults
with a `TimeoutException`.

## What this scenario uncovers

**Root Cause:** A module-level `for _i in range(5_000_000): ... print(...)` loop
runs at import. The per-row stdout floods the engine's output pipe and the heavy
loop never finishes within `Timeout`, hanging the scope.

This maps to:
`references/activity-packages/python-activities/playbooks/load-script-failures.md`
sub-case **L3** (hang or oversized data).

The engine initializes fine and there is no syntax error or `ModuleNotFoundError`
- this is explicitly **not** the L1 engine-init or L2 script-error cases. The
user is framed as **off-host**, so the correct agent behavior is to tie the hang
to load-time stdout / heavy module-level work and recommend removing it (and/or
raising `Timeout`) - not to attempt host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Python Scope` (`Timeout=30000`) -> `Load Python Script` -> `Invoke Python Method` and `scripts/aggregate.py` (module-level print-flood loop) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `load-script-failures.md` (sub-case L3)
- Agent identified a hang from load-time stdout flood / heavy module-level work
  exceeding `Timeout` (not engine init, not a missing module) and recommended
  removing/reducing the load-time stdout (move work into a function) and/or
  raising `Timeout`, without fabricating host actions
