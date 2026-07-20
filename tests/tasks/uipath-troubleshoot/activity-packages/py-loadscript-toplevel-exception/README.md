# Load Python Script Failure - Top-Level Exception at Module Load (L2b)

This scenario reproduces a `Load Python Script` failure caused by **module-level
(top-level) code that raises at import time**. `Load Python Script` executes the
module body to bind its functions, so a statement at module scope that throws
aborts the load with `Error loading the python script` / `One or more errors
occurred` before any function is invoked.

## What this scenario uncovers

**Root Cause:** `scripts/order_import.py` has a module-level statement
`DEFAULT_DISCOUNT = 100 / 0` that raises `ZeroDivisionError` when the module is
imported. Load Python Script runs the module body at load, so the top-level line
faults the activity before `import_orders` is ever called.

This maps to:
`references/activity-packages/python-activities/playbooks/load-script-failures.md`
sub-case **L2b** (script load / compile / top-level exception).

The engine initializes fine (logs show "Python engine initialized") and there is
no `ModuleNotFoundError`, so this is explicitly **not** the L1 engine-init case
or the L2a missing-package case. The user is framed as **off-host**, so the
correct agent behavior is to tie the load error to top-level code and recommend
guarding it - not to attempt host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Python Scope` -> `Load Python Script` -> `Invoke Python Method` and `scripts/order_import.py` (module-level divide-by-zero) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `load-script-failures.md` (sub-case L2b)
- Agent identified a top-level / module-scope exception at load as the cause
  (not engine init, not ModuleNotFoundError) and recommended moving the code
  into a function or behind `if __name__ == "__main__":`, without fabricating
  host actions
