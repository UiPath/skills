# Python Scope — The Specified Python Path Is Not Valid (Path Points at python.exe)

This scenario reproduces a `Python Scope` failure where the scope cannot
resolve the interpreter because its `Path` property points at `python.exe`
(the executable) instead of the install **folder**. The job ends with:

```
Python Scope: The specified Python path is not valid: C:\Program Files\Python311\python.exe
```

## What this scenario uncovers

**Root Cause:** The `Python Scope` `Path` property must be the **folder** that
contains `python.exe` (e.g. `C:\Program Files\Python311`). It is set to
`C:\Program Files\Python311\python.exe` — the executable itself. The scope
appends the interpreter name internally, so it cannot resolve a real
interpreter from a path that already ends in `python.exe`, and fails at scope
open before any Python runs. The named file does exist on disk, which is why
the user thinks "the path is right."

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/python-activities/playbooks/python-path-not-valid.md`

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `PythonHelloWorld` — `Python Scope` with `Path="C:\Program Files\Python311\python.exe"` (trailing `\python.exe`) → `Run Python Script: hello.py` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; `or jobs get` Info shows `The specified Python path is not valid: C:\Program Files\Python311\python.exe` at `Python Scope`, faulting at scope open |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The decisive evidence is the trailing `\python.exe` on the `Python Scope`
`Path` in `process/Main.xaml`, matching the path echoed in the error. The
test grades whether the agent identifies the file-vs-folder mistake and
recommends stripping `\python.exe` to the containing folder.

> **Note on fixtures.** Synthetic. Job key, folder key, and host are
> placeholders.
