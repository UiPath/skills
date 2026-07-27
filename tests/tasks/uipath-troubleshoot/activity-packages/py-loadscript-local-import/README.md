# Load Python Script Failure - Unresolved Local Import / WorkingFolder (L2c)

This scenario reproduces a `Load Python Script` failure where a **sibling local
import** is not found. `scripts/ledger_sync.py` does `import ledger_utils` (a
local module that exists in the same `scripts/` folder), but the `Python Scope`
has no `WorkingFolder` set, so the import resolves against the robot's package
directory instead of `scripts/` and faults at load with `ModuleNotFoundError: No
module named 'ledger_utils'`.

## What this scenario uncovers

**Root Cause:** The local sibling module `ledger_utils.py` is present in the
project, but the scope's `WorkingFolder` is unset, so the interpreter's import
path does not include `scripts/`. The sibling import fails at load.

This maps to:
`references/activity-packages/python-activities/playbooks/load-script-failures.md`
sub-case **L2c** (unresolved local import).

The discriminator vs. **L2a**: `ledger_utils` is the user's **own file in the
repo**, not a third-party package — so the fix is `WorkingFolder`, **not** `pip
install`. The user is framed as **off-host**; the correct agent behavior is to
recognize the local import and recommend setting `WorkingFolder` - not to attempt
host commands or install a package.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project with a `Python Scope` (no `WorkingFolder`) -> `Load Python Script` -> `Invoke Python Method`, plus `scripts/ledger_sync.py` (imports `ledger_utils`) and the sibling `scripts/ledger_utils.py` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `load-script-failures.md` (sub-case L2c)
- Agent recognized a local sibling-module import failing because `WorkingFolder`
  is not the script's folder (not a missing third-party package) and recommended
  setting `WorkingFolder` to the script folder (not `pip install`), without
  fabricating host actions
