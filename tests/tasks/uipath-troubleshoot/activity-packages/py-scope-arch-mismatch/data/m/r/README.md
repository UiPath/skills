# Python Scope — One or More Errors Occurred (Target x86 vs 64-bit Install)

This scenario reproduces a `Python Scope` engine-initialization failure where
the scope's `Target` is `x86` but the Python install on the robot host is
64-bit. The job ends with:

```
Python Scope: One or more errors occurred. (Error initializing the Python engine) ---> System.BadImageFormatException: An attempt was made to load a program with an incorrect format. (0x8007000B)
```

## What this scenario uncovers

**Root Cause:** The `Python Scope` `Target` property is set to `x86`, but the
interpreter at `C:\Program Files\Python311` is 64-bit (the user confirms a
64-bit Python 3.11 install). UiPath cannot load a 64-bit interpreter's native
library into a 32-bit host, so engine initialization fails with an aggregate
error whose inner exception is `BadImageFormatException (0x8007000B)` — the
classic 32-bit/64-bit mismatch signature. The fault is at scope open, before
`Run Python Script: crunch.py` runs.

This maps to:
`skills/uipath-troubleshoot/references/activity-packages/python-activities/playbooks/python-scope-architecture-version-mismatch.md`

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | `PythonDataCruncher` — `Python Scope` with `Target="x86"`, `Path="C:\Program Files\Python311"`, `Version="Python_311"` → `Run Python Script: crunch.py` (stdlib only) |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses; `or jobs get` Info shows `One or more errors occurred. (Error initializing the Python engine)` with an inner `BadImageFormatException (0x8007000B)` at `Python Scope` |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

The decisive evidence is `Target="x86"` on the `Python Scope` in
`process/Main.xaml` combined with the user's statement that the installed
Python is 64-bit, plus the `BadImageFormatException (0x8007000B)` inner error.
The script uses only the standard library, ruling out a missing-module cause.
The test grades whether the agent identifies the bitness mismatch and
recommends setting `Target` to `x64`.

> **Note on fixtures.** Synthetic. Job key, folder key, and host are
> placeholders.
