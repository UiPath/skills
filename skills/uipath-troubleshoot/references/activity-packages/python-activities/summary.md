# Python Activities Playbooks

**Overview:** [overview.md](./overview.md) — `UiPath.Python.Activities` package, Python Scope execution model, properties, and common failure patterns
**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Python Activities investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Load Python Script (LoadScript) Failures | Medium | `UiPath.Python.Activities.LoadScript` fails to load a script. Three families: (L1) **engine initialization** — `The specified Python path is not valid` / `Error initializing Python engine 64 bit` from wrong `Path` (must be the install/venv folder), `Target` bitness mismatch, `Library path` missing for Python > 3.9 on Windows (`pythonXX.dll`), a Python version newer than the package supports, or missing .NET Desktop Runtime 6+ (pkg v1.9.0+); (L2) **script load/import** — `One or more errors occurred` / `Error loading the python script` / `ModuleNotFoundError` from a module missing in the interpreter at `Path` (IDE venv not auto-activated), a top-level syntax error/exception, or an unresolved local import (`WorkingFolder`); (L3) **hang / oversized data** — stdout pipe freeze, `Timeout`, or Script Data Size Limit exceeded | [load-script-failures.md](./playbooks/load-script-failures.md) |
