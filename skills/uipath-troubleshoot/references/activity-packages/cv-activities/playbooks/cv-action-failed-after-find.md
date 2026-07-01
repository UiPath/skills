---
confidence: medium
---

# CV — Click/type failed after the element was found (focus, stale coordinates, blocked input, SecureString)

## Context

The CV match **succeeded** — the descriptor resolved to a region — but the subsequent click or keystroke failed or landed in the wrong place. CV activities click/type at screenshot-derived coordinates on a clipped clone of the scope root, with hardware events forced (`SimulateClick`/`SimulateType`/`SendWindowMessages` are disabled internally). Anything that moves the window or steals focus **between analysis and action** clicks/types in the wrong place — often with **no error** — or surfaces a raw driver/COM exception that carries **no CV resource key**.

Affected activities: **CV Click** (`CvClickWithDescriptor`), **CV Type Into** (`CvTypeIntoWithDescriptor`), and **CV Get Text** (`CvGetTextWithDescriptor`) in clipboard mode (`MethodType = ClipboardRow`/`ClipboardAll`, which click + select + Ctrl+C).

What this looks like — match on the symptom class, not a single string:

- **A driver/COM exception with NO `UiPath.CV.*` type and NO CV resource key.** The message is passed through verbatim from the UI driver (`COMException` / `UiNode`-level errors out of `UiElement.Click_Normalized` / `WriteText`). There is no `Element not found`, no `Invalid Descriptor` — the find already passed. `UninitializedNodeException` is remapped to `ElementNotSetException` (`The target Element was not specified for this activity.`).
- `Value cannot be null. (Parameter 'Secure')` — **CV Type Into only.** `ArgumentNullException` on parameter name `Secure`. Thrown before any keystroke when `Text` is a secure `CvString` built from a **null** `SecureString`.
- An exception with its **original type and message preserved** (e.g. `InvalidOperationException`), unwrapped from the find task. CV unwraps and rethrows the find task's inner exception as-is — a non-CV type here is the underlying fault, not a CV error.
- **No error at all** — the click/type/clipboard read appeared to run, but the wrong control was hit, the field stayed empty, or `OutRegion`/`Result` is empty/`null`/stale. CV Click's `OutRegion` comes back `(0,0,0,0)` (`Rectangle.Empty`); clipboard-mode CV Get Text returns `null` or stale text. Clicks, selection keystrokes, and the clipboard read all swallow `COMException` internally — a failed action still "succeeds."

What can cause it (ordered most → least common in unattended/RDP fleets):

- **Window moved/resized/redrawn between analysis and action.** CV clicks **coordinates**, not a live element. Any reflow, popup, animation, or focus shift after the screenshot moves the target out from under the resolved rectangle. The click/keystroke lands on whatever is now there — usually **no error**.
- **Input blocked / no interactive desktop.** Hardware events require an interactive, unlocked, foreground desktop. Locked session, RDP window minimized, secure desktop (UAC consent prompt), or another `SetForegroundWindow` race blocks or misroutes the input. Surfaces as a raw driver/COM exception **or** silently does nothing.
- **Focus stolen between find and type/Ctrl+C.** Another window grabbed focus after the match; keystrokes (or the clipboard select+copy) go to the wrong window. Clipboard mode degrades **silently** to empty/stale `Result`.
- **Null `SecureString` (CV Type Into).** `Text` bound to a secure string that was never assigned — e.g. an upstream Get Credential failed and was ignored. Deterministic `ArgumentNullException(Secure)`. Plain-text `null` is **safe** (coalesced to empty), so this is secure-input only.
- **Clipboard mode on a non-editable target.** The Ctrl+C selection sequence only works on keyboard-selectable editable text. On a label/static target it selects nothing; `Result` is empty with no error. Design-time raises the warning `The Select methods only work on editable text...`.
- **Malformed special-key sequence in `Text` (CV Type Into).** Unbalanced `[k(...)]` syntax surfaces from `WriteText` as a driver-level error, not a CV error.

> **Different cause, do not apply this playbook:**
> - `Element not found` / `Scrolled the entire screen, but element was not found` (`UiPath.CV.ElementNotFoundException`) — the find itself failed; the action was never reached. Use [./cv-element-not-found.md](./cv-element-not-found.md) (and [./cv-scroll-search-failures.md](./cv-scroll-search-failures.md) for the scroll variant).
> - `Invalid Descriptor` / `Target must be set` / `Invalid image reference or value` (`UiPath.CV.InvalidDescriptorException`) — thrown before any find. Use [./cv-invalid-descriptor.md](./cv-invalid-descriptor.md).
> - Server/auth/throttling errors (`System.ArgumentException` carrying a server error code, 401/403/429/5xx, OCR word limit) raised during a session refresh — find-pipeline failure, not the action. Use [./cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md).
> - `Activity is valid only inside a CV Screen Scope`, or scope-setup faults (local-server prerequisite, scope window selector not found) — the scope never started, so no find/action ran. Use [./cv-scope-setup-failures.md](./cv-scope-setup-failures.md).
> - `The target Element was not specified for this activity.` **at scope entry, before any child ran** (the faulted activity is the `CV Screen Scope`, not a child) — the scope-side variant, remapped from a root-selector `COMException` or a null scope `Target`. Use [./cv-scope-setup-failures.md](./cv-scope-setup-failures.md). This playbook's variant of the same message fires only **after** a child's find succeeded.
> - CV Get Text returns empty/stale text in **OCR mode** (no clicks/clipboard involved) — different mechanism. Use [./cv-get-text-empty-or-wrong-result.md](./cv-get-text-empty-or-wrong-result.md).
> - General `ContinueOnError`/`InRegion` silent-result traps not specific to a post-find action: [./cv-silent-failures-and-false-results.md](./cv-silent-failures-and-false-results.md).

## Investigation

1. **Confirm the find succeeded.** A timestamped `*_ComputerVision` runtime dump JSON is written **only** when the find throws `ElementNotFoundException`. If no such dump exists for this run but the activity still faulted/misbehaved, the failure is **after** the match — this playbook applies. If the dump exists, route to [./cv-element-not-found.md](./cv-element-not-found.md).
2. **Read the exception type.** If it is `UiPath.CV.*` (`ElementNotFoundException`, `InvalidDescriptorException`) or a `System.ArgumentException` with a server code, leave this playbook (see routing block). A raw `COMException` / driver / `ElementNotSetException` / `ArgumentNullException(Secure)`, or an unwrapped non-CV type, stays here.
3. **For `Value cannot be null. (Parameter 'Secure')`:** confirm the activity is CV Type Into and the `Text` argument is a secure string. This is Branch A — deterministic, no further screen investigation needed.
4. **Determine if there was an exception at all.** No exception + wrong/empty result + `ContinueOnError = false` ⇒ the action ran but missed (Branch B/C silent path). Check `OutRegion` (CV Click: `(0,0,0,0)` = swallowed failure or `ContinueOnError`) and `Result` (CV Get Text clipboard: `null`/stale).
5. **Check `ContinueOnError`.** If `true`, exceptions are suppressed and outputs stay at defaults — a "successful" run can hide a driver failure. Inspect execution logs for traced-but-swallowed `COMException`/driver exceptions. Do not trust the result while `ContinueOnError = true`.
6. **Reconstruct the screen/window state at action time.** From logs, screenshots, and environment: was the session interactive and unlocked? Was the target window foreground, not minimized, not on another desktop? Did a popup/UAC prompt/animation fire between analysis and action? Unattended + RDP + locked/disconnected session is the dominant pattern.
7. **For clipboard-mode CV Get Text:** confirm `MethodType` (`ClipboardRow`/`ClipboardAll`) and whether the target is an editable input box. Check the design-time warning `The Select methods only work on editable text...`. A non-editable target yields empty `Result` silently.
8. **For CV Type Into driver faults:** inspect `Text` for unbalanced `[k(...)]` special-key syntax before blaming the environment.

## Resolution

Walk the branches; pick the first whose evidence holds. Name the evidence that rules a branch **out** — do not recommend a fix the evidence does not support.

### Branch A — Null `SecureString` (CV Type Into)

**Evidence.** `System.ArgumentNullException`, parameter `Secure`, message `Value cannot be null. (Parameter 'Secure')`; the activity is `CvTypeIntoWithDescriptor` and `Text` is a secure string. Thrown before any keystroke. **Ruled out** if the type is not `ArgumentNullException` or the parameter is not `Secure` — plain-text `null` never throws this (it coalesces to empty), so do not chase this branch for a non-secure `Text`.

**Fix.** Ensure the `SecureString` is populated before the activity runs. Trace the upstream source (Get Credential / asset / orchestrator credential) — a failure there that was ignored leaves the variable null. Fix the credential retrieval; do not work around it by switching to plain text for a secret. *(Edits the workflow — see Post-presentation actions.)*

### Branch B — Stale coordinates: window moved/redrew between analysis and action

**Evidence.** No exception (or a driver exception), and the action hit the wrong place or did nothing. Logs/screenshots show the target window moved, resized, scrolled, or a popup/animation rendered after the CV analysis. Common with dynamic web pages, async-loading panels, and notification toasts. **Ruled out** if the window was provably static (no reflow, single static dialog) — then look at Branch C (focus/input).

**Fix.** Stabilize the screen before the action so coordinates stay valid: add a wait/`Element Exists`-style settle before the CV activity, increase `DelayBefore` so the screen quiesces before the find, disable animations/transitions on the target app, and avoid reusing a stale `InRegion`/`OutRegion` rectangle from an earlier activity after the screen has changed. *(Edits the workflow — see Post-presentation actions.)*

### Branch C — Input blocked or focus stolen (no interactive/foreground desktop)

**Evidence.** Raw driver/`COMException` out of the click/type, **or** silent no-op, on an **unattended/RDP** robot. Session was locked, RDP window minimized, a UAC/secure-desktop prompt was up, or another process grabbed foreground between find and action. Clipboard-mode degrades to empty/stale `Result` here. **Ruled out** on an attended, unlocked, foreground session with no competing app — then revisit Branch B.

**Fix.**
- Keep the session interactive and unlocked for the whole job — use an unattended runtime that holds an active console session; never run CV against a locked or minimized RDP window. Do not minimize/lock the RDP client during execution.
- Eliminate the focus thief — suppress notifications/popups, or bring the target window to the foreground immediately before the action.
- Suppress UAC/secure-desktop interruptions on the robot machine (admin/policy) so they don't seize the desktop mid-action.
- For clipboard-mode CV Get Text, confirm the target is editable text; if not, switch `MethodType` to OCR (clipboard select cannot work on non-editable targets). *(App/policy fixes are environment-side; any `MethodType`/property change edits the workflow — see Post-presentation actions.)*

### Branch D — Malformed special-key sequence in `Text` (CV Type Into)

**Evidence.** Driver-level error out of `WriteText` and `Text` contains `[k(...)]` special-key syntax that is unbalanced/invalid. **Ruled out** if `Text` is plain literal text with no `[k(...)]` tokens.

**Fix.** Correct the special-key syntax in `Text` (balanced `[k(...)]`). *(Edits the workflow — see Post-presentation actions.)*

### Branch E — Unwrapped non-CV exception from the find task

**Evidence.** The exception's type and message are not from `UiPath.CV.*` and not a known driver/COM signature — e.g. `InvalidOperationException` surfaced verbatim. CV unwraps and rethrows the find task's inner exception as-is.

**Fix.** Treat the surfaced exception on its own terms — it is the genuine underlying fault (its message/type is authoritative), not a CV-layer error. Diagnose by that exception, not by this playbook's CV mechanics. If it points outside the activity package, escalate accordingly.

## Post-presentation actions

This resolution is **interactive** whenever a fix edits user source files — Branch A (credential wiring), Branch B (add wait / change `DelayBefore` / drop a stale `InRegion`), Branch C (`MethodType` change), and Branch D (`Text` edit) all touch the workflow. The orchestrator MUST call `AskUserQuestion` before any edit.

1. **Sharing a file path is not approval.** A path given so you could read the project does not authorize editing it. Issue a separate `AskUserQuestion` before any write.
2. **Never bundle "gather input" with "apply fix" in one option.** Split into two steps: gather the input, then surface the concrete diff and confirm separately.
3. **Surface the diff before asking.** Include the file path, the activity `IdRef` or line, the current value, and the proposed value (e.g. `CvTypeIntoWithDescriptor` `DelayBefore` `300` → `1500`; or the `Text`/credential binding change). Vague approvals are not enough.
4. **One question per file/fix.** If multiple files are touched, list each or ask file-by-file. Do not silently propagate a change to side-channel files.
5. **Environment/policy fixes are recommendations, not edits** — keeping the session unlocked, suppressing UAC/notifications, or running an interactive unattended runtime are operator actions; present them as recommendations.
6. **If interactive approval is unavailable or errors, do not edit.** Present the diff as a recommendation and stop. A recommendation-only close is acceptable; a silent edit is never.

## Stop / escalate

Stop and escalate when: the SecureString is confirmed populated yet `ArgumentNullException(Secure)` persists; the session is provably interactive, unlocked, and foreground with no focus thief and no screen movement, yet the click/type still faults or misses; or the surfaced exception is an unwrapped non-CV type (Branch E) whose root cause lies outside `UiPath.CV.Activities`. In those cases the cause is outside this activity's post-find action path — escalate (UI driver, target-app stability, robot/desktop environment, or the upstream component that produced the unwrapped exception) rather than continue under this playbook.
