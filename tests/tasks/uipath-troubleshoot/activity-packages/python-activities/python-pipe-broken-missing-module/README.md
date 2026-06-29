# Python Scope — Pipe is Broken (Missing pip Module in the Robot Interpreter)

This scenario reproduces a `Python Scope` failure where `Invoke Python Method`
faults with `Pipe is broken`. The invoked script imports `pandas`, which is
installed in the developer's IDE interpreter but **not** in the Python 3.11
interpreter the `Python Scope` resolves on the robot host. The job ends with:

```
UiPath.Python.RemoteException wrapping System.IO.IOException: Pipe is broken: "Invoke Python Method: extract_total"
```

## What this scenario uncovers

**Root Cause:** `UiPath.Python.Activities` runs Python out-of-process and
talks to it over an IPC pipe. `parse_invoice.py` does `import pandas`. The
robot's interpreter (`C:\Program Files\Python311`, the one `Python Scope`
`Path` resolves) does not have `pandas` installed, so the Python host raises
`ModuleNotFoundError` and exits before returning. UiPath only sees the host
die and reports `Pipe is broken` — the underlying Python error is hidden.
The script "runs fine in the developer's IDE" because the IDE uses a
different interpreter that has `pandas`.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/python-activities/playbooks/invoke-python-method-pipe-is-broken.md`

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `PythonInvoiceParser` — `Python Scope` (`Path=C:\Program Files\Python311`, `Target=x64`, `Version=Python_311`) → `Load Python Script: parse_invoice.py` → `Invoke Python Method: extract_total`; `parse_invoice.py` imports `pandas` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; `or jobs get` Info shows the `Pipe is broken` `RemoteException` at `Invoke Python Method`, and the logs show the scope opened and the script loaded before the host died |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The decisive evidence is **not** in the job log (the Python traceback is
swallowed): it is the `import pandas` line in `process/parse_invoice.py`
combined with the user's "runs fine in my IDE" framing. The test grades
whether the agent identifies that the out-of-process Python host died on a
missing third-party module in the robot's interpreter, and recommends
installing it into the scope's interpreter / reproducing the real traceback
standalone.

> **Note on fixtures.** Synthetic. Job key, folder key, and host are
> placeholders representative of a real Robot host layout.
