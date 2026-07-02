---
confidence: medium
signatures:
  - kind: message
    value: "FileNotFoundError"
    note: "Python-side, referencing a relative path — CWD is the robot per-package folder, not the project; the activities themselves succeed"
---

# Python Scope — Script Runs but Reads/Writes the Wrong Files (WorkingFolder / Relative Path)

## Context

What this looks like:
- The Python activities succeed — no `Pipe is broken`, no scope error — but the automation "doesn't execute properly": the script writes output that never appears where expected, reads a stale/empty file, or a Python-side `FileNotFoundError` references a relative path.
- Works in Studio / on the developer's machine; misbehaves only on the robot.

What can cause it:
- **Relative paths resolve against `WorkingFolder`, which defaults to the robot's per-package CWD.** A script that opens `open("data.csv")` or writes `out.json` with a bare/relative name resolves it against the process working directory. `Python Scope` `WorkingFolder` sets that directory; when left blank, the robot's unattended CWD is the per-package folder `%LocalAppData%\UiPath\Packages\<process>\<version>\`, not the project folder. The developer sees it "work" because Studio's CWD is the project folder during debugging.
- **`WorkingFolder` set to a developer-only path** — an absolute `WorkingFolder` that exists on the dev machine but not on the robot host.

What to look for:
- Relative file paths inside the `.py` script (`open(...)`, `Path(...)`, `pd.read_csv("...")`, output writes with bare filenames).
- Whether `Python Scope` `WorkingFolder` is set, and to what.
- A resolved path in any Python-side error that carries the `%LocalAppData%\UiPath\Packages\...` prefix — the smoking gun for CWD divergence.

## Investigation

1. Confirm the activities did not fault (or faulted only with a Python-side `FileNotFoundError` on a relative path) — distinguishes this from `Pipe is broken` and scope-resolution errors.
2. Read the `.py` script. List every file path it opens or writes; flag any that is relative (no drive letter, no leading `\`, no UNC).
3. Read the `Python Scope` `WorkingFolder` from the `.xaml`. Note whether it is blank (defaults to the robot per-package CWD) or an absolute path that may not exist on the robot.
4. If a Python-side path error is present, check its prefix: a `%LocalAppData%\UiPath\Packages\<process>\<version>\` prefix confirms the relative path resolved against the package CWD.

## Resolution

- **If the script uses relative paths:** make them absolute. Either set `Python Scope` `WorkingFolder` to a stable absolute directory and keep filenames relative to it, or pass absolute paths into the script as method arguments (`Invoke Python Method` `InputParameters`) built in the workflow from an Orchestrator asset / environment variable. Do not rely on the implicit CWD.
- **If anchoring inside the script:** resolve paths against the script's own location, e.g. `os.path.join(os.path.dirname(os.path.realpath(__file__)), "data.csv")`, so the script is independent of the process CWD.
- **If `WorkingFolder` is a dev-only absolute path:** point it at a directory that exists on the robot host (or source it from an asset / env var per environment).
- **Prevention:** ban bare relative paths in scripts invoked from unattended robots; the robot CWD is the per-package sandbox and differs from Studio's project folder.
