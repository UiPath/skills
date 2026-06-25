# Load Python Script Engine-Init Failure - Python Version Unsupported by the Package (L1d)

This scenario reproduces a `Load Python Script` engine-initialization failure
caused by the **installed Python being newer than the package supports**. The
project pins `UiPath.Python.Activities` 1.8.1 (which supports up to Python 3.12),
but the robot now has Python 3.13 (`Version=Auto` detects 3.13), so the scope
cannot initialize the engine and faults with `Error initializing the Python
engine. The detected Python version 3.13 is not supported by
UiPath.Python.Activities 1.8.1`.

## What this scenario uncovers

**Root Cause:** A version-support gap between the pinned package (1.8.1, max
Python 3.12) and the interpreter on the robot (3.13). The pack cannot stand up an
engine for an unsupported Python version, so the failure is at engine init,
before the script loads.

This maps to:
`references/activity-packages/python-activities/playbooks/load-script-failures.md`
sub-case **L1d** (engine init - Version unsupported by the package).

The `Library path` is set correctly (`python313.dll`) and `Target` matches, so
this is explicitly **not** L1c (library path) or L1b (bitness); and the script
never loads, so it is **not** a `ModuleNotFoundError` or top-level error. The
user is framed as **off-host**; the correct agent behavior is to recommend
upgrading the package (or pinning a supported Python version) - not to attempt
host commands.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project pinning `UiPath.Python.Activities` 1.8.1, a `Python Scope` (`Version=Auto`, Library path set) -> `Load Python Script` -> `Invoke Python Method`, and a valid `scripts/forecast.py` |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** Fixtures here were authored from the documented
> playbook signature rather than captured from a real
> `.local/investigations/` session. The Python-version-to-package support map
> (3.12 -> 1.8.1, 3.13 -> 1.10.0) is taken from `load-script-failures.md`.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `load-script-failures.md` (sub-case L1d)
- Agent identified an engine-init failure from the installed/detected Python
  version being unsupported by the pinned package (not Library path, not bitness,
  not a missing module) and recommended upgrading the package to a version
  supporting Python 3.13 (1.10.0) or pinning `Version` to a supported
  interpreter, without fabricating host actions
