# Classic Activities

The classic UiPath activities — the original (non-"modern", non-"Next") activities that appear in
Studio under `UiPath.Core.Activities`. They split across two NuGet packages:

- **UI Automation (classic)** — `UiPath.UIAutomation.Activities`. Selector- and image-based desktop
  and browser automation: `Click`, `Type Into`, `Send Hotkey`, `Open Browser`, `Close Tab`,
  `Open Application`, `Attach Browser` (Browser Scope), `Attach Window` (Window Scope),
  `Take Screenshot`, `Wait Image Vanish`, `Wait UI Element Appear`.
- **System / Core** — `UiPath.System.Activities`. Workflow, file, process, data, and Orchestrator
  activities: `Invoke Workflow File`, `Invoke Code`, `Add Queue Item`, `Rename File`, `Move File`,
  `Append Line`, `Log Message`, `Kill Process`, `Start Triggers`, `For Each Row`.

> These are the **classic** activities. The modern UI Automation "Next" activities (`NClick`,
> `Use Application/Browser`, healing agent) are covered by the **ui-automation** package, and the
> modern Orchestrator-resource activities (`Get Asset`, `Get Credential`) by the
> **system-activities** package. `Get Robot Asset` / `Get Robot Credential` failures are covered by
> the existing **system-activities** `get-asset-*` playbooks — use those, this package does not
> duplicate them.

## Common Failure Families

**UI Automation (classic):**
- Target element not found within the timeout (`SelectorNotFoundException`) — selector drift, wrong
  scope/window, application not open or not ready.
- Activity timeout (`ActivityTimeoutException`, "Activity timeout exceeded") — element/state never
  reached; `Wait UI Element Appear` element never appeared; `Wait Image Vanish` image never vanished.
- Element found but the action failed (`ElementOperationException`) — disabled, occluded,
  off-screen, or focus lost between find and act.
- Browser could not be opened or attached (`BrowserOperationException`) — browser not installed,
  extension missing, browser crashed, wrong browser type for the communication method.
- Application could not be launched (`Open Application` / `Open Browser`) — file/path not found, bad
  arguments, app never produced a window.
- Design-time configuration / validation errors — mutually-exclusive options both set, conflicting
  scope properties, communication-method incompatibilities.
- Image automation reliability — `Wait Image Vanish` is sensitive to display scaling, resolution,
  theme, and rendering differences between design and run time.

**System / Core:**
- File operations (`Rename File`, `Move File`, `Append Line`) — source not found, destination not a
  folder, file already exists, path is a directory, access denied, file locked.
- Workflow invocation (`Invoke Workflow File`, `Start Triggers`) — file not found, argument
  name/type/direction mismatch, isolated/elevated/session validation, persistence not supported.
- Code invocation (`Invoke Code`) — compilation failure, unsupported language, or exceptions thrown
  by the user's own code at run time.
- Queue operations (`Add Queue Item`) — empty queue name, invalid/duplicate item-information keys,
  Orchestrator permission/HTTP/timeout errors, queue not found.
- Process control (`Kill Process`) — process not found, access denied, errors across multiple
  processes.
- Data iteration (`For Each Row`) — null DataTable, invalid iterator variable name, or an exception
  thrown by an activity inside the loop body.

## Packages

NuGet: `UiPath.UIAutomation.Activities`, `UiPath.System.Activities`
