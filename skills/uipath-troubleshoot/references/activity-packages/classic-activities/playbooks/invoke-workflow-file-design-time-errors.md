---
confidence: high
---

# Invoke Workflow File — Design-Time, Cache & Package-Version Errors

## Context

An `Invoke Workflow File` (`UiPath.Core.Activities.InvokeWorkflowFile`) invocation fails in Studio at
**design time / build time** — validation, compile, or open — not as a faulted robot job. These are
distinct from run-time invoke faults (workflow throws on the robot, isolated/session validation, child
exception) → for those use [invoke-workflow-failed.md](./invoke-workflow-failed.md).

What this looks like (each maps to one cause below):
- `Cannot set unknown member 'UiPath.Core.Activities.InvokeWorkflowFile.ArgumentsVariable'` — Studio
  cannot open/validate the workflow after a package change.
- `Invoked workflows are missing` or a **Cache Mechanism Error** (`Error code: 7`) — child workflows
  exist in source but the build reports them missing.
- `Cannot find the file` / `System.IO.FileNotFoundException` on the invoked `.xaml` at pack/validate.
- `Value for a required activity argument was not supplied` — validation error on the invoke.

What can cause it:
- **Package-version mismatch (ArgumentsVariable):** the XAML was authored/saved with a
  `UiPath.System.Activities` version whose `InvokeWorkflowFile` serializes arguments via the
  `ArgumentsVariable` member, but the project pins an **older** version that lacks that member (or the
  project was upgraded from an old layout). The deserializer rejects the unknown member.
- **Project cache corruption (Error code 7):** the Studio compiler lost track of local workflow
  dependencies — typically after repeated debug runs — so it reports invoked workflows missing even
  though the `.xaml` files are present. Stale `.local`, `bin`, `obj` caches.
- **Invoked file not packable / path unresolved:** the invoked `.xaml` lives **outside** the project
  root, so it is not included in the package; or the dynamic `WorkflowFileName` path resolves to
  null / the wrong value at the invoke.
- **New required argument not mapped:** the invoked workflow added a mandatory `In`/`Out` argument
  (no default), but the parent's `Invoke Workflow File` still carries the old argument layout, leaving
  the required argument unsupplied.

What to look for:
- The exact error string (the four signatures above route to distinct causes).
- `UiPath.System.Activities` version in `project.json` vs the `ArgumentsVariable` member in the XAML.
- Presence of stale `.local` / `bin` / `obj` folders alongside child `.xaml` files that DO exist.
- The invoke's `WorkflowFileName` — literal path outside the project root, or an unassigned variable.
- The invoked workflow's declared arguments vs the arguments mapped on the `Invoke Workflow File`.

## Investigation

Route on the exact error string; stop at the first matching branch.

1. **`Cannot set unknown member ... ArgumentsVariable`** → open `project.json`, read the pinned
   `UiPath.System.Activities` version. Open the workflow XAML and confirm the `InvokeWorkflowFile`
   node carries an `ArgumentsVariable` attribute/member. Mismatch (member present, older package
   pinned) confirms a package-version regression from an upgrade or a shared workflow edited with a
   newer package.
2. **`Invoked workflows are missing` / `Cache Mechanism Error` / `Error code: 7`** → confirm the
   invoked child `.xaml` files actually EXIST in the project source (the invoke's target file is on
   disk). Check for stale `.local` / `bin` / `obj` folders. Child files present + missing-report =
   compiler cache corruption, not a real missing dependency.
3. **`Cannot find the file` / `FileNotFoundException`** → read the invoke's `WorkflowFileName`. If it
   is a literal path, check whether the target `.xaml` sits **inside** the project root (files outside
   the root are not packed). If it is a variable/expression, trace whether it is assigned a non-null
   value before the invoke.
4. **`Value for a required activity argument was not supplied`** → open the invoked workflow's
   declared `<x:Members>` / arguments and compare against the arguments mapped on the parent's
   `Invoke Workflow File`. A mandatory `In`/`Out` argument (no default) that is unmapped confirms a
   drift after the child workflow gained a required argument.

If none of the four branches fits, fall back to the maintenance checklist under Resolution.

## Resolution

- **Package-version mismatch (`ArgumentsVariable`):** align the `UiPath.System.Activities` version —
  update the project's pin to the version that introduced `ArgumentsVariable` (or downgrade the shared
  workflow to match the project). Then open each `Invoke Workflow File`, click **Import Arguments** to
  refresh the parameter layout. Right-click the workflow → **Find References** to reach every
  invocation.
- **Project cache corruption (Error code 7):** close Studio, open the project folder, and delete the
  `.local` folder to clear the project cache. Deleting `bin` and `obj` is also safe. Reopen the
  project to let it rebuild.
- **Invoked file not packable / path unresolved:** move the invoked `.xaml` **inside** the main
  project folder so it is packed. If the path is dynamic, ensure the `WorkflowFileName` variable is
  assigned a valid, non-null value before the invoke runs.
- **New required argument not mapped:** open the `Invoke Workflow File` in the parent, click **Import
  Arguments**, and map the newly required `In`/`Out` variable.

**Maintenance checklist (unresolved after the above), in order:**
1. **Re-add the activity:** delete the broken `Invoke Workflow File` and drag a fresh one in.
2. **Fix extra slashes:** in the file-path field, remove unintended double backslashes (`\\`) that
   break compilation.
3. **Rebuild `project.json`:** close Studio, delete `project.json`, and open `Main.xaml` directly to
   regenerate a fresh configuration file.
