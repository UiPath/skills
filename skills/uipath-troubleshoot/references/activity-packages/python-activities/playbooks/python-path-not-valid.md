---
confidence: high
---

# Python Scope — The Specified Python Path Is Not Valid

## Context

What this looks like:
- `Python Scope` faults immediately on open with:
  - `Python Scope: The specified Python path is not valid: <path>`.
- The fault is at scope open — no Python code has run yet.
- The `<path>` in the error is exactly the `Path` property value, and the file/folder it names does exist on disk, so "the path is right, why is it invalid?"

What can cause it:
- **`Path` points at `python.exe` instead of the install folder** — the most common cause. `Path` must be the **folder** that contains `python.exe` (e.g. `C:\Program Files\Python311`), not the executable itself (`C:\Program Files\Python311\python.exe`). The scope appends the interpreter name internally.
- **`Path` points at the Microsoft Store alias** — `%LocalAppData%\Microsoft\WindowsApps\python` (or `...\python.exe`) is a 0-byte execution-alias stub installed by the Store "App execution aliases", not a real Python install. The scope cannot resolve a real interpreter from it.
- **`Path` resolves to an interpreter the robot user can't see** — a per-user install under the developer's profile (`C:\Users\<dev>\AppData\Local\Programs\Python\...`) does not exist for the unattended robot user. From the robot's perspective the path is invalid.
- **`Library path` / `Version` mismatch** (Python > 3.9 on Windows) — `Path` is correct but `Library path` does not point at the matching `pythonXY.dll`, so the engine can't bind. (If the error is `One or more errors occurred` / `Error initializing the Python engine` rather than "path is not valid", use the architecture/version playbook instead.)

What to look for:
- The trailing segment of the `Path` value: does it end in `\python.exe`? Is it under `\WindowsApps\`?
- Whether the path is under a per-user profile (`C:\Users\<name>\...`) that differs between the developer and the robot user.

## Investigation

1. Read the error from job evidence. Confirm it is `The specified Python path is not valid: <path>` at `Python Scope` (not a `Pipe is broken` or engine-init error — different playbooks).
2. Read the `Python Scope` `Path` property from the `.xaml`. Compare the literal against the two traps: a `\python.exe` suffix, or a `\WindowsApps\python` Store-alias path.
3. If `Path` is a folder and not a Store alias, check whether it is under a per-user profile (`C:\Users\<dev>\...`) that the unattended robot user would not have.
4. Confirm the real interpreter location out-of-band: the install **folder** that contains `python.exe` on the robot host (e.g. `where python` / the actual `Programs\Python\PythonXXX` folder).

## Resolution

- **If `Path` ends in `\python.exe`:** remove the executable name — set `Path` to the containing folder only. Example: change `C:\Program Files\Python311\python.exe` → `C:\Program Files\Python311`.
- **If `Path` is the `WindowsApps\python` Store alias:** install Python from python.org (or use an existing real install) and point `Path` at that install folder. Disable the Store "App execution aliases" for `python` / `python3` (Settings → Apps → Advanced app settings → App execution aliases) so the alias stops shadowing the real interpreter on `PATH`.
- **If `Path` is a per-user install the robot can't see:** install Python for **all users** (machine-wide, e.g. `C:\Program Files\Python311`) or install it under the robot's own user, then point `Path` at a folder the robot user can read.
- **After fixing `Path`** (Python > 3.9 on Windows): set `Library path` to the matching `pythonXY.dll` in that folder (e.g. `C:\Program Files\Python311\python311.dll`) and set `Version` to the installed version; leave `Library path` empty for installs ≤ 3.9. Re-run and confirm the scope opens.

This is a high-confidence configuration fix: the error names the exact bad `Path`, and the scope opening successfully after the edit is immediate confirmation.
