# Python Activities Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — data correlation rules and testing prerequisites for Python Activities investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Pipe is broken / Error invoking Python method | Medium | `Invoke Python Method` / `Run Python Script` faults with `Pipe is broken` (often `RemoteException wrapping System.IO.IOException: Pipe is broken`). The out-of-process Python host died and UiPath hides the Python-side cause: a pip module missing from the scope's interpreter, an unhandled exception, a hard `sys.exit`, or flooding stdout. "Runs in my IDE" = different interpreter | [invoke-python-method-pipe-is-broken.md](./playbooks/invoke-python-method-pipe-is-broken.md) |
| The specified Python path is not valid | High | `Python Scope` fails resolving the interpreter: `The specified Python path is not valid: <path>`. `Path` points at `python.exe` (the file) instead of the install **folder**, or at the `WindowsApps\python` Store alias | [python-path-not-valid.md](./playbooks/python-path-not-valid.md) |
| One or more errors occurred / Error initializing the Python engine | Medium | `Python Scope` fails to load the interpreter. `Target` bitness (x86/x64) doesn't match the install, `Version`/`Library path` is wrong, or the required .NET Desktop Runtime is missing | [python-scope-architecture-version-mismatch.md](./playbooks/python-scope-architecture-version-mismatch.md) |
| Script runs but reads/writes the wrong files | Medium | The script completes but relative file paths inside it resolve against `WorkingFolder` — which defaults to the robot's per-package CWD, not the project folder. Same CWD-divergence class as relative workflow paths | [working-folder-relative-path.md](./playbooks/working-folder-relative-path.md) |
