---
confidence: medium
---

# CV — Screen Scope setup failures (window resolution, local server prerequisites, missing server/OCR config)

## Context

The **CV Screen Scope** (`CVScope`) is the container every CV activity runs inside. Its `ExecuteAsync` resolves the target window, builds a CV session (`CVSessionData`), and only then runs the body. A fault during that setup faults the scope **before any child activity executes** — and the scope's `OnFault` rethrows the inner fault **unwrapped**, so the exception you see may have originated in the scope, not in the child.

**Core diagnostic split — do this first:**
- **Fault BEFORE any child activity ran** (no `CV Click` / `CV Type Into` / `CV Element Exists` / `CV Get Text` trace line; the faulted activity in XAML is the `CV Screen Scope` itself) → scope-setup problem. **This playbook.**
- **Fault INSIDE a child** (a child activity has a start trace, the descriptor match was attempted) → find/server/action problem. Route to [cv-element-not-found.md](./cv-element-not-found.md), [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md), or [cv-action-failed-after-find.md](./cv-action-failed-after-find.md). Not this playbook.

What this looks like — any of these patterns, all faulting at scope entry:

- `Please make sure you have UiPath.ComputerVision.LocalServer package installed in order to use local server mode.` — `UseLocalServer=true` but the LocalServer package is absent. Fires at both design time (validation, blocks run) and runtime (`System.ArgumentException`).
- `Server or OCR engine is required.` — design-time validation only: no `Server`, `UseLocalServer` not true, no `OCREngine`, no project-settings `Server`. Blocks the run; never a runtime throw.
- `The target Element was not specified for this activity.` — scope `Target` was set, but reading the root element's selector raised a `COMException` at session creation; the COM failure is remapped to this message (`ElementNotSetException`). Also the literal message when `Target` is genuinely null.
- `UiPath.ComputerVision.LocalServer requires a processor that accepts AVX2 instructions.` — local server runtime error: CPU lacks AVX2.
- `UiPath.ComputerVision.LocalServer requires Microsoft Visual C++ Redistributable 2015-2022 for X64.` — local server runtime error: MSVC redistributable missing.
- `Activity is valid only inside a CV Screen Scope` — design-time validation: a child CV activity is outside any scope.
- `Activity can not be in another Screen Scope container` — design-time validation: a `CV Screen Scope` is nested inside another `CV Screen Scope`.
- `Descriptor or InputRegion is required` — design-time validation: a child CV activity has neither a `Descriptor` nor an `InputRegion`.
- A **raw `System.NullReferenceException` with no message** — a child CV activity executed **outside** a `CV Screen Scope` at runtime (validation bypassed). See Branch F.

What activities can produce this:
- **CV Screen Scope** (`CVScope`) — the scope itself, for window-resolution / local-server / missing-config faults.
- **All child CV activities** — **CV Click** (`CvClickWithDescriptor`), **CV Type Into** (`CvTypeIntoWithDescriptor`), **CV Element Exists** (`CvElementExistsWithDescriptor`), **CV Get Text** (`CvGetTextWithDescriptor`) — when the enclosing scope faults before their body runs, OR for the design-time validation constraints (`Activity is valid only inside a CV Screen Scope`, `Descriptor or InputRegion is required`) that attach to the child.

What can cause it (ordered most→least common):
- **LocalServer package missing on the robot machine.** `UseLocalServer=true` (set directly or via project settings) but `UiPath.ComputerVision.LocalServer` is not installed. The runtime check (`VerifyEdgeServerInstalled`) cannot load `UiPath.CVLocalServer.ServiceConfig`. Most common on first deploy to a new machine: the workflow ran fine where the package was present.
- **Scope window selector no longer resolves.** `Target` selector doesn't match (app not open, title/version/language drift, no visible window). Standard UiAutomation target-resolution errors surface from the scope.
- **Root element selector unreadable (COMException).** The target window matched, but died/changed between attach and session creation, so reading its selector throws `COMException` → remapped to `The target Element was not specified for this activity.`
- **Missing server/OCR configuration (design time).** Neither a cloud `Server`+`ApiKey`, nor `UseLocalServer`, nor an `OCREngine` is configured → `Server or OCR engine is required.`
- **Local server runtime prerequisites.** CPU without AVX2, or MSVC 2015-2022 x64 redistributable missing → the LocalServer cannot start.
- **Design-time constraint violations.** Child outside scope, nested scope, no descriptor/region.
- **Child executed outside a scope at runtime (rare).** Validation bypassed via dynamic/composed workflow → raw `NullReferenceException`.

> **Different cause, do not apply this playbook:**
> - A child activity **started** and the descriptor match timed out → [cv-element-not-found.md](./cv-element-not-found.md).
> - Server reachable but returns 401/403/429/5xx, payload/word errors **during a child's analysis call** (not at scope entry) → [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md).
> - `... has hit the maximum number of words it is able to identify (<count>). Please indicate a screen with less words.` — the OCR word cap. It surfaces **lazily on the first child's analysis call**, not at scope entry, so it is an analysis-time fault → [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md).
> - The descriptor itself is malformed (missing `Target`, broken image refs, parse failure) → [cv-invalid-descriptor.md](./cv-invalid-descriptor.md).
> - `The target Element was not specified for this activity.` remapped from `UninitializedNodeException` **after the find succeeded** (a child started and matched, then the action ran) → [cv-action-failed-after-find.md](./cv-action-failed-after-find.md). This playbook's variant is the **scope-entry** one: the message fires before any child ran.
> - Click/type failed **after** the element was found (focus, stale coords, blocked input) → [cv-action-failed-after-find.md](./cv-action-failed-after-find.md).
> - Activity returned a wrong/empty result without faulting → [cv-silent-failures-and-false-results.md](./cv-silent-failures-and-false-results.md).

## Investigation

1. **Confirm the fault is at scope entry, not in a child.** Read the trace/log order: is there any `CV Click` / `CV Type Into` / `CV Element Exists` / `CV Get Text` start line before the fault? If a child started, this is not a scope-setup failure — route per the negative-match block. If the faulted activity in XAML is the `CV Screen Scope` itself and no child ran, continue.
2. **Identify the message pattern** against the Context list. The message text is the primary router — match on it, not on the exception type alone (the scope rethrows children's exceptions unwrapped, and several distinct causes share `System.ArgumentException`).
3. **Determine design-time vs runtime.** Validation messages (`Server or OCR engine is required.`, `Activity is valid only inside a CV Screen Scope`, `Activity can not be in another Screen Scope container`, `Descriptor or InputRegion is required`, and the design-time form of the LocalServer message) **block the run** as `InvalidWorkflowException` / `ValidationError` — the job never started. A faulted *running* job points to the runtime branches instead.
4. **Read scope properties from XAML** when relevant: `UseLocalServer`, `Server`, `ApiKey`, `OCREngine`, `CvMethod`, `Target` (selector + `WaitForReady`), `ContinueOnError`. Also check **project settings** — `UseLocalServer` and `Server` can be set there and override an empty scope-level value.
5. **For LocalServer messages, confirm the package on the failing machine** — not the dev machine. The package presence is machine/project-local.
6. **For window-resolution faults**, confirm the target app is open and its window visible at the moment the scope runs (same checks as a UIA application scope: title/version/language drift, minimized-to-tray, second monitor on unattended).

## Resolution

Walk the decision tree. Match the **message text** first, then the corroborating evidence. Choose the first branch whose evidence holds.

### Branch A — LocalServer package missing (runtime)

**Evidence.** Running job faulted with `System.ArgumentException`: `Please make sure you have UiPath.ComputerVision.LocalServer package installed in order to use local server mode.` `UseLocalServer=true` (scope or project settings). No child ran.

**Fix.** Add the `UiPath.ComputerVision.LocalServer` NuGet package to the project so the robot machine has it (project dependency change, not a workflow XAML edit) — **OR**, if local-server mode was not intended, set `UseLocalServer=false` on the scope (or in project settings) and configure a cloud `Server`+`ApiKey` instead (XAML/properties edit → see Post-presentation actions).

**Ruled out** if the project already references `UiPath.ComputerVision.LocalServer` and the dependency restored on this machine — then the failure is a local server *runtime* error (Branch E), not a missing package.

### Branch B — Server or OCR engine missing (design time)

**Evidence.** `Server or OCR engine is required.` The run was **blocked at validation** — the job never started. No `Server`, `UseLocalServer` not true, no `OCREngine`, and no `Server` in project settings.

**Fix.** Configure exactly one analysis source on the scope: set `Server`+`ApiKey` (cloud), or set `UseLocalServer=true` with the LocalServer package installed, or attach an `OCREngine` (XAML/properties edit → Post-presentation actions). This is design-time only; it never appears on a running job.

### Branch C — Scope window selector did not resolve

**Evidence.** Scope-entry fault with target-resolution / UIA selector errors (e.g. selector-not-found, scope timeout) — `Target` was set but the window was not located. No COM failure on a matched window. The app is closed, or the selector drifted (title/version/language), or the window is not visible.

**Fix.** Same remediation family as a UIA application scope: confirm the app is open with a visible window when the scope runs; relax the scope `Target` selector (wildcard volatile parts, prefer stable attributes); ensure an earlier step launches/activates the app; raise `WaitForReady` / scope timeout for cold-start races (XAML/properties edit → Post-presentation actions).

**Distinct from Branch D:** here no window matched. In D a window matched but its selector became unreadable.

### Branch D — Root element selector unreadable at session creation (COMException)

**Evidence.** `The target Element was not specified for this activity.` on a scope where `Target` **is** set (not null). The window matched, then died/changed between attach and `CVSessionData` construction, so reading the root selector threw `COMException`. Often intermittent; clusters with apps that close/repaint fast.

**Fix.** Stabilize the window before the scope: precede with an app-state/Element-Exists wait so the scope only runs against a live, settled window; add retry around the scope; raise `DelayBefore` if the window repaints immediately after appearing (XAML/properties edit → Post-presentation actions).

**Ruled out** when `Target` is actually empty/null in XAML — then the same message is the literal "target not set" case, fixed by setting `Target` (still Post-presentation).

### Branch E — Local server runtime error (service unavailable / AVX2 / VC++)

**Evidence.** `UseLocalServer=true`, package **present**, but a runtime `System.ArgumentException` carrying a `LocalServerError`:
- `UiPath.ComputerVision.LocalServer requires a processor that accepts AVX2 instructions.` → CPU lacks AVX2 (older/virtualized hardware).
- `UiPath.ComputerVision.LocalServer requires Microsoft Visual C++ Redistributable 2015-2022 for X64.` → MSVC redistributable missing.
- Service-unavailable / engine-load text → the local server process failed to start.

**Fix (environment, not workflow):**
- **AVX2.** Move the robot to AVX2-capable hardware, or switch the scope to cloud mode (`UseLocalServer=false` + `Server`+`ApiKey`). AVX2 is not installable.
- **VC++.** Install the Microsoft Visual C++ Redistributable 2015-2022 (x64) on the robot machine.
- **Service failed to start.** Confirm the LocalServer install is intact; reinstall the package; check for a broker/dependency load failure in the robot logs.

LocalServer-error responses bypass the throttling retry loop, so they surface immediately (no slow-then-fail). Do **not** treat AVX2/VC++ as transient — they will not self-heal on retry.

### Branch F — Child executed outside a CV Screen Scope at runtime

**Evidence.** A **raw `System.NullReferenceException` with no message** from a child CV activity, where the workflow was composed/invoked dynamically (e.g. `Invoke Workflow` into a fragment, dynamically loaded XAML) so the design-time `InCVScope` constraint was bypassed. Normally impossible in Studio-authored workflows — the constraint blocks publish.

**Fix.** Ensure the child CV activity runs inside a real `CV Screen Scope` ancestor. If the workflow dynamically composes activities, wrap them so the scope is present at runtime (XAML/structure edit → Post-presentation actions). Do **not** chase the `NullReferenceException` as a CV server or descriptor bug — the null is the missing `CVSessionData` data-context, nothing more.

### Design-time constraint violations (Branches in validation, run blocked)

These never appear on a running job; they block publish/run as validation errors. Fix in the designer, then re-run:
- `Activity is valid only inside a CV Screen Scope` — move the child CV activity inside a `CV Screen Scope`.
- `Activity can not be in another Screen Scope container` — un-nest the inner `CV Screen Scope`; a scope cannot contain another scope.
- `Descriptor or InputRegion is required` — set the child's `Descriptor`, or supply an `InputRegion`.
- The design-time form of the LocalServer message → Branch A's package fix.

## Post-presentation actions

Branches A (when flipping `UseLocalServer` / setting cloud `Server`+`ApiKey`), B, C, D, F, and the design-time constraint fixes **edit user source files** (scope XAML properties, child placement, project settings). That resolution path is **interactive**.

Rules the agent MUST follow:

1. **Sharing a file path is not approval.** A path the user gave for reading the project does not authorize editing. Issue a separate `AskUserQuestion` before any edit.
2. **Surface the diff before asking.** The apply-fix question must name the file path, the activity `IdRef` (or property/line), the current value, and the proposed value — e.g. `CVScope.UseLocalServer: true → false` plus the `Server`/`ApiKey` to add.
3. **Never bundle "gather input" with "apply fix" in one option.** Splitting required: gather input, then surface the concrete diff and confirm separately.
4. **One question per file/fix.** List every file touched (scope XAML, plus `project.json` for a package add, plus project settings if `UseLocalServer` lives there) — ask file-by-file. Do not silently propagate a substitution to side-channel files.
5. **If interactive approval is unavailable or errors, do not edit.** Present the diff as a recommendation and stop. A recommendation-only close is acceptable; a silent edit is never acceptable.

Environment-only fixes (Branch A package install on the robot, Branch E AVX2/VC++/reinstall) are not source-file edits — present them as remediation steps for the operator; no `AskUserQuestion` gate is required for those.

## Stop / escalate

If the message is matched, the corroborating evidence holds, and the prescribed fix is applied (package present, valid `Server`+`ApiKey` or `OCREngine`, window open and selector resolving, AVX2+VC++ present, child inside a real scope) **and the scope still faults at entry**, the cause is outside scope setup — escalate (machine/driver issue, LocalServer install corruption, or a Server-side fault during the child's first analysis call → re-route to [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md)) rather than continue under this playbook. Do not recommend a second config change the evidence does not support.
