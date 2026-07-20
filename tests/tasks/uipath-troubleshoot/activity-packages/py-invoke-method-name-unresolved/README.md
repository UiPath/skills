# Invoke Python Method Failure - Function Not Bound at Module Level

This scenario reproduces an `Invoke Python Method`
(`UiPath.Python.Activities.InvokeMethod`) failure. The Python engine
initializes and `Load Python Script` succeeds, then the invoke step faults
with `AttributeError: module 'transform' has no attribute 'clean_records'`
because the target function is defined only inside the script's
`if __name__ == "__main__":` block.

## What this scenario uncovers

**Root Cause:** `Load Python Script` binds functions defined at **module
level** and skips the `if __name__ == "__main__":` block on import. In
`scripts/transform.py`, `clean_records` is defined inside that guard, so it
is never bound and `Invoke Python Method` cannot resolve it. The script
"works standalone" (`python transform.py` runs the `__main__` block) but
fails under UiPath (which imports the module instead of running the file).

This maps to:
`references/activity-packages/python-activities/playbooks/invoke-method-failures.md`
(sub-cause M1 - function name does not resolve at module level).

The user is framed as **off-host** (Orchestrator only). The fix is a
script-structure change in the project source the agent can recommend (and
optionally apply) without host access; the correct behavior is to identify
the invoke-resolution fault and recommend moving the function to module
level - not to attempt host commands or misdiagnose it as an engine-init,
load, or argument failure.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project: `Python Scope` -> `Load Python Script` -> `Invoke Python Method`, with `clean_records` defined only under `__main__` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session. The job logs deliberately show the
> engine initializing and the script loading BEFORE the fault, to
> distinguish this from a load-script-failures issue.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `invoke-method-failures.md` and identified that the function
  is not bound at module level (defined under `__main__`), NOT an engine-init,
  script-load, or argument-mismatch failure
- Agent recommended moving `clean_records` to module level (and/or validating
  by `python -c "import transform; print(transform.clean_records)"`), without
  fabricating host actions
