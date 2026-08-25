---
confidence: medium
---

# Python Scope — Hangs / Freezes Indefinitely (Missing .NET Desktop Runtime)

## Context

What this looks like:
- **Design time:** Studio freezes / becomes unresponsive when you open, drop, or step into a `Python Scope` — often with **no error dialog**.
- **Runtime:** a job containing a `Python Scope` hangs and makes no progress — **no Python traceback, no aggregate exception** — and is eventually killed or stopped on timeout (or faults with a .NET host-activation error rather than a Python one).
- The defining tell is the **absence of an error message**: the scope neither opens nor returns a clean fault — it just hangs.

What can cause it:
- **Missing .NET Desktop Runtime (most common).** On `UiPath.Python.Activities` **v1.9.0+** with the project **target framework = Windows** (not Windows-Legacy), the Python host process runs on the .NET Desktop Runtime and requires the **.NET Desktop Runtime 6.0 (x64)** (current packs also accept .NET 8; older packs need **5.0**). If that runtime is not installed on the host, the host process cannot start and the scope hangs/freezes instead of returning an error.
- **Target framework switched to Windows without provisioning the runtime.** Moving a project from Windows-Legacy to Windows pulls in the .NET Desktop Runtime dependency; a host image that lacks it freezes on the first `Python Scope`.

What to look for:
- The project **`targetFramework`** in `project.json` (`Windows` vs `Legacy` / `Windows-Legacy`) and the installed `UiPath.Python.Activities` version.
- Whether **.NET Desktop Runtime 6.0 (x64)** (or 5.0 for packs < v1.9.0) is present on the host — `dotnet --list-runtimes` should list `Microsoft.WindowsDesktop.App 6.x` (or `8.x`).
- **OS Event Viewer → Windows Logs → Application** around the time of the hang for a `.NET Runtime` activation / framework-not-found error — this is the decisive evidence when UiPath surfaces no error of its own.

## Investigation

1. Confirm the symptom is a **hang/freeze with no error** — Studio unresponsive on the `Python Scope`, or a runtime job stuck with no Python traceback — rather than an aggregate engine-init error (that is [python-scope-architecture-version-mismatch.md](./python-scope-architecture-version-mismatch.md)) or a `The specified Python path is not valid` error ([python-path-not-valid.md](./python-path-not-valid.md)).
2. Read `project.json`: the `targetFramework` (`Windows` vs `Windows-Legacy`) and the `UiPath.Python.Activities` version. The risk pattern is **`Windows` + v1.9.0+**.
3. On the host (out-of-band if you are off-host), check installed runtimes: `dotnet --list-runtimes` and look for `Microsoft.WindowsDesktop.App 6.*` (pkg v1.9.0+) or `5.*` (older packs).
4. Check **Event Viewer → Windows Logs → Application** around the hang for a `.NET Runtime` / `framework: 'Microsoft.WindowsDesktop.App'` "not found" activation error — this surfaces the missing-runtime root cause that UiPath swallows.

## Resolution

- **If the .NET Desktop Runtime is missing (pkg v1.9.0+):** install the **.NET Desktop Runtime 6.0 (x64)** (.NET 8 also supported by current packs) on the host from the Microsoft download portal, then re-run. For older `UiPath.Python.Activities` (< v1.9.0) install **.NET Desktop Runtime 5.0**. Match the **x64** runtime to a 64-bit robot (the common case).
- **If installing the runtime is not possible on the host:** set the project **target framework to Windows-Legacy**, which does not depend on the .NET Desktop Runtime, then republish.
- **After the fix:** re-open the scope in Studio (design-time) or re-run the job (runtime) and confirm it no longer hangs.

> **Related:** when the scope returns an actual error instead of hanging — `One or more errors occurred` / `Error initializing the Python engine` / `BadImageFormatException` from a bitness, `Version`, or `Library path` mismatch — use [python-scope-architecture-version-mismatch.md](./python-scope-architecture-version-mismatch.md). The missing .NET Desktop Runtime is listed there as one engine-init cause; **this** playbook is for the **hang/freeze with no error** presentation.
