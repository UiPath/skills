---
confidence: medium
---

# CV — Silent failures and false results (ContinueOnError swallow, InRegion bypass, ElementExists false-negative/positive)

## Context

What this looks like — **no exception is thrown**, yet a CV step behaved wrong. The job either succeeds with a wrong/empty/default output, or a later non-CV activity faults on a garbage value handed to it by a CV activity. There is no error message to match; diagnose from **output values, property settings, trace lines, and the CV dump file**.

Observable symptoms:
- **Click/Type fired at the wrong place** (or did nothing) but the activity reported success.
- **CV Element Exists** (`CvElementExistsWithDescriptor`) returned `True` when the element is plainly absent, or `False` when it is plainly present.
- **CV Get Text** (`CvGetTextWithDescriptor`) returned empty (`""`), `null`, or stale/previous-screen text.
- **OutRegion** consumed downstream is `(0,0,0,0)` (empty `Rectangle`) or a stale rectangle from a prior screen.
- The CV server, descriptor, or window is broken, but the workflow proceeded as if nothing happened — the only sign is a `Trace.TraceError` line and a `{timestamp}_ComputerVision` dump file written before the (swallowed) throw.

What activities can produce this:
- **CV Click** (`CvClickWithDescriptor`) — `ContinueOnError`, `InRegion` arguments.
- **CV Type Into** (`CvTypeIntoWithDescriptor`) — `ContinueOnError`, `InRegion` arguments; clipboard/focus side-paths.
- **CV Element Exists** (`CvElementExistsWithDescriptor`) — `Result`, `ContinueOnError`, `InRegion`, cell-targeting descriptor.
- **CV Get Text** (`CvGetTextWithDescriptor`) — `ContinueOnError`, `InRegion`, `MethodType` (OCR vs clipboard), `RefreshBefore`.
- **CV Screen Scope** (`CVScope`) — `ContinueOnError`, `CvMethod` (detection/OCR flags), `Server` / `UseLocalServer`.

What can cause it (most→least common):
- **`ContinueOnError = true` on a CV activity or the scope.** This is the dominant cause. The shared `Continuable*` base catches **every** exception (element-not-found, server `ArgumentException`, `InvalidDescriptorException`) when `ContinueOnError` evaluates true, traces it, and returns the activity's default output. Defaults: `CvElementExistsWithDescriptor` → `Result = false`; `CvGetTextWithDescriptor` → `Result = null`; `CvClickWithDescriptor` → still sets `OutRegion` to the default empty `Rectangle` `(0,0,0,0)`. A misconfigured server then looks identical to "element not found", and downstream logic proceeds on the default value with no signal the operation failed. `CVScope` is the one exception that still rethrows runtime-**governance** (`RuleViolationException`) faults — everything else it swallows.
- **`InRegion` is bound, which bypasses CV entirely.** When `InRegion` is set, the find pipeline uses that rectangle directly — **no descriptor matching, no screen analysis, no validation** that anything is at those coordinates. Consequences differ by activity: `CvElementExistsWithDescriptor` **always returns `True`** (the region is non-null → it counts as "found"); `CvClickWithDescriptor` / `CvTypeIntoWithDescriptor` **fire at those raw coordinates** wherever they land. A stale or wrong `InRegion` (e.g. a prior `OutRegion` reused after the screen changed, or after a resolution/DPI change) produces wrong-coordinate clicks and false-positive existence checks with no error.
- **`CvElementExistsWithDescriptor` converts infrastructure failures into `Result = false`** even with `ContinueOnError = false`. It catches `ElementNotFoundException` **by design** to return `false`. But a **closed/minimized target window or a failed screenshot** surfaces from session `RefreshAsync` as `ElementNotFoundException` too — so a broken target silently becomes `Result = false` (false negative), not an error. Note: other failure types (server `ArgumentException`, `InvalidDescriptorException`) still propagate from Element Exists when `ContinueOnError = false`.
- **Cell-targeting config errors are swallowed by `CvElementExistsWithDescriptor`.** A descriptor targeting a table cell throws its informative error as an `ElementNotFoundException`, so Element Exists turns even a clear config error (e.g. `Invalid column number 0`) into `Result = false`. The message survives only in the trace and the CV dump.
- **`CvMethod` flags disabled detection.** If the scope's `CvMethod` (or the `Section.CvScope` / `Property.CVMethod` project setting) is OCR-only or detection-only, the missing element family is served from a possibly-empty cache. Children just don't find their elements — no error from the scope. Server URL empty with no local server silently skips CV detection while OCR still runs.
- **Clipboard / OCR side-paths in Get Text swallow errors.** Clipboard mode (`MethodType = ClipboardRow`/`ClipboardAll`): `UiService` click/select/`Ctrl+C` catch `COMException` and return `false`, which Get Text ignores — a failed copy still "succeeds" with `null`/stale clipboard text. OCR mode: `DoOcr` swallows all OCR-engine exceptions and returns no words → empty result; `RefreshBefore = false` reuses a stale OCR cache from a prior screen.

What to look for:
- **`ContinueOnError`** on the failing CV activity AND on the enclosing `CVScope` — either being `true` enables the whole silent class.
- Whether **`InRegion`** is bound (wired from a variable / prior `OutRegion`), and whether that source could be stale.
- Trace lines: `Trace.TraceError` of a suppressed exception (the swallowed server/descriptor error), `Could not get screenshot`, OCR-failure traces.
- The **`{timestamp}_ComputerVision` CV dump file** — written just before a swallowed `ElementNotFoundException`; the primary forensic artifact for not-found and cell-targeting failures.
- The actual **output value**: `Result` (`false`/`null`/unexpected `true`), `OutRegion` = `(0,0,0,0)` or a stale rectangle.

> **Different cause, do not apply this playbook:**
> - The activity **threw** `UiPath.CV.ElementNotFoundException` (`Element not found`) and faulted the job — `ContinueOnError` is `false` and `InRegion` is not bound — use [cv-element-not-found.md](./cv-element-not-found.md).
> - The activity threw a **server error** (`[Error code: <N>] <message>`, 401/403/429/5xx, word-limit, local-server) — use [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md).
> - The activity threw `InvalidDescriptorException` (missing `Target`, broken image reference, parse failure) — use [cv-invalid-descriptor.md](./cv-invalid-descriptor.md).
> - `CVScope` itself faulted at setup (window resolution, missing/uninstalled local server, missing server/OCR config) before any child ran — use [cv-scope-setup-failures.md](./cv-scope-setup-failures.md).
> - The element **was found**, then Click/Type failed (focus, stale coordinates after find, blocked input, null `SecureString`) and threw — use [cv-action-failed-after-find.md](./cv-action-failed-after-find.md).
> - **Get Text threw**, or returned wrong text and you have ruled out `ContinueOnError`/`InRegion`/clipboard-vs-OCR — use [cv-get-text-empty-or-wrong-result.md](./cv-get-text-empty-or-wrong-result.md).
> - The element genuinely is below the fold and scroll-search did not reach it — use [cv-scroll-search-failures.md](./cv-scroll-search-failures.md).
> - A table cell was targeted and you have confirmed the table/row/column config is the problem (not the swallowing) — use [cv-cell-targeting-failures.md](./cv-cell-targeting-failures.md).

## Investigation

1. **Identify the symptomatic output.** Determine which is wrong: a wrong-location/no-op Click or Type, an unexpected `CvElementExistsWithDescriptor` `Result`, or an empty/null/stale `CvGetTextWithDescriptor` `Result`. This selects the branch below.
2. **Read `ContinueOnError` on the failing activity AND on the enclosing `CVScope`.** Either `true` means errors are being suppressed and returned as defaults. Check the trace for a `Trace.TraceError` line carrying the suppressed exception — that text is the real error.
3. **Check whether `InRegion` is bound.** If set, the activity skipped all CV detection and used the rectangle verbatim. Trace the source of that rectangle (prior `OutRegion`, a variable) and whether the screen / resolution / DPI changed since it was produced.
4. **Locate the CV dump file** `{timestamp}_ComputerVision` for the run timestamp. Its presence indicates a not-found (or swallowed cell-targeting) condition occurred even if the activity reported success/`false`.
5. **Inspect the target window state at run time** — closed, minimized, off-screen, or a locked/unattended session can fail the screenshot and surface as `ElementNotFoundException` (→ swallowed to `Result = false` in Element Exists).
6. **Read the scope's `CvMethod` and `Server`/`UseLocalServer`** (and any `Section.CvScope` / `Property.CVMethod` project-setting override). A detection-or-OCR-disabled method, or empty server with no local server, silently yields no elements.
7. **For Get Text:** read `MethodType` (OCR vs clipboard) and `RefreshBefore`. Clipboard mode is fragile on non-editable targets; `RefreshBefore = false` reuses stale OCR.

## Resolution

Walk to the branch matching the symptom. Each names the evidence that confirms it and the evidence that rules it OUT.

### Branch A — `ContinueOnError = true` is masking a real failure

Evidence: `ContinueOnError` is `true` on the failing CV activity or on the enclosing `CVScope`; the trace shows a `Trace.TraceError`-logged exception (server `ArgumentException`, `InvalidDescriptorException`, or `ElementNotFoundException`) at that activity; the output is the bare default (`Result = false`/`null`, `OutRegion = (0,0,0,0)`).

Ruled out when: no suppressed exception appears in the trace and no CV dump file exists for the run — then the activity genuinely succeeded and the wrong value has a different cause (try Branch B or C).

Fix: the swallowed exception **is** the bug. Diagnose it under the matching sibling playbook (server → [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md), descriptor → [cv-invalid-descriptor.md](./cv-invalid-descriptor.md), not-found → [cv-element-not-found.md](./cv-element-not-found.md)). Then recommend setting `ContinueOnError = false` on that activity (or scope) so the failure surfaces instead of returning a default, unless the author deliberately wants a best-effort step — in which case recommend an explicit guard on the output (check `Result`/`OutRegion` before downstream use). Do NOT recommend leaving `ContinueOnError = true` with unguarded downstream consumption.

### Branch B — `InRegion` bypassed detection (false-positive Exists, wrong-coordinate Click/Type)

Evidence: `InRegion` is bound on the activity. For `CvElementExistsWithDescriptor`, `Result` is `True` regardless of screen content (and `OutRegion` equals the supplied `InRegion`). For Click/Type, the action landed at fixed coordinates unrelated to the descriptor. The supplied rectangle traces to a stale source (prior `OutRegion`, a hard-coded/old variable) or the screen/resolution/DPI changed between producer and consumer.

Ruled out when: `InRegion` is unbound/empty — detection ran normally; the wrong result is then Branch A or a genuine match/scroll/cell issue (route to the sibling playbooks).

Fix: stop relying on `InRegion` for validated targeting. Either clear `InRegion` so the activity matches the descriptor against the live screen, or recompute the region immediately before use from a fresh find. For an existence check, an `InRegion`-bound `CvElementExistsWithDescriptor` is meaningless — it cannot return `False`; replace it with a descriptor-based check. Confirm the producing activity ran on the same screen state and DPI as the consumer.

### Branch C — Element Exists false negative: closed/minimized window or failed screenshot

Evidence: `CvElementExistsWithDescriptor` returned `False`, but the element is present when checked manually; a `{timestamp}_ComputerVision` dump exists; the target window was closed, minimized, off-screen, or the session was locked at run time; trace may show `Could not get screenshot`. `ContinueOnError = false` and `InRegion` unbound (otherwise Branch A/B).

Ruled out when: the target window was confirmed visible and foreground at run time and a screenshot succeeded — then `False` is a genuine descriptor mismatch, route to [cv-element-not-found.md](./cv-element-not-found.md).

Fix: ensure the target window is open, restored, and able to come to the foreground before the check (an unattended/locked session blocks the screenshot). The scope re-resolves its root window by cached selector until `TimeoutMS`; if the window legitimately may be absent, treat `False` as "could not verify" rather than "definitely absent" and add an explicit window-state guard upstream.

### Branch D — Cell-targeting config error swallowed into `Result = false`

Evidence: the descriptor targets a **table cell**; `CvElementExistsWithDescriptor` returned `False`; the CV dump / trace contains an informative cell message such as `Invalid column number <N>`, `Table only contains <N> columns and column number is <M>`, `Invalid row number <N>`, `Could not find table. Cell targeting supports only tables as target`, or `Table does not have any column with column name containing <name>`. These never reach the workflow level because Element Exists swallows them.

Ruled out when: the descriptor does not target a cell, or no cell message appears in the trace/dump — then it is a plain match failure (Branch C / not-found).

Fix: this is a configuration error, not an absent element. Correct the cell descriptor per the captured message (column/row index must be ≥ 1 and within range; column-name/row-contains text must match the extracted table text). Diagnose the cell config under [cv-cell-targeting-failures.md](./cv-cell-targeting-failures.md). Recommend switching off the swallowing path (validate the cell config with a throwing CV activity, or set `ContinueOnError = false` and read the surfaced message) so the informative error is no longer lost.

### Branch E — Get Text returns null / empty / stale silently

Evidence: `CvGetTextWithDescriptor` `Result` is `null` (→ check Branch A; `ContinueOnError = true` yields `null`), `""`, or text from a previous screen. Clipboard mode (`MethodType = ClipboardRow`/`ClipboardAll`) on a non-editable target, focus stolen between click and `Ctrl+C`, or another process holding the clipboard → empty/stale; the click/copy `COMException` is swallowed. OCR mode with `RefreshBefore = false` reuses a stale OCR cache; a swallowed OCR-engine failure yields zero words → `""`.

Ruled out when: `ContinueOnError = false`, `MethodType` matches the target type (clipboard only for editable/selectable text), and `RefreshBefore = true` — then route detailed wrong-text diagnosis to [cv-get-text-empty-or-wrong-result.md](./cv-get-text-empty-or-wrong-result.md).

Fix: pick the right mode — use OCR mode for non-editable on-screen text; use clipboard mode only for selectable/editable inputs. Set `RefreshBefore = true` when the screen changed since the prior CV activity. If `ContinueOnError = true`, see Branch A.

### Branch F — `CvMethod` disabled the needed detection family

Evidence: multiple children in the scope silently find nothing (or only text, or only controls); the scope's `CvMethod` (or `Section.CvScope` / `Property.CVMethod` project setting) is OCR-only or detection-only, or `Server` is empty with no local server. No error from the scope.

Ruled out when: `CvMethod` includes both element detection and OCR and a server (cloud or local) is configured — then missing elements are a genuine match failure or server issue, not a disabled method.

Fix: set `CvMethod` to include the families the descriptors need (control detection for control descriptors, OCR for text descriptors), and ensure a `Server` URL or `UseLocalServer` is configured so detection can run. This is a scope-setting change — see also [cv-scope-setup-failures.md](./cv-scope-setup-failures.md).

## Post-presentation actions

This resolution path is **interactive** whenever the fix edits the user's workflow — changing `ContinueOnError`, clearing or rebinding `InRegion`, changing `MethodType` / `RefreshBefore`, correcting a cell descriptor, or changing the scope's `CvMethod`. You MUST call `AskUserQuestion` before any edit (approval gate), and follow these rules:

1. **Sharing a file path is not approval.** A path the user gave for reading the project does not authorize editing it. Issue a separate `AskUserQuestion` before any edit.
2. **Never bundle "gather input" with "apply fix" in one option.** Split into two steps: gather the input, then surface the specific diff and confirm separately.
3. **Surface the concrete diff before asking** — file path, activity `IdRef` or line, current value, proposed value (e.g. `ContinueOnError: True → False`, `InRegion: <bound> → <unbound>`, `CvMethod: OcrOnly → ControlsAndOcr`).
4. **One question per file/fix; list every file touched** (e.g. XAML plus any mirrored Object Repository file). Do not silently propagate a substitution to side-channel files.
5. **If interactive approval is unavailable or errors, do not edit.** Present the diff as a recommendation and stop. A recommendation-only close is acceptable; a silent edit is never acceptable.

## Stop / escalate

If `ContinueOnError` is `false` on the activity and scope, `InRegion` is unbound, the target window was visible and foreground (screenshot succeeded), `CvMethod` includes the needed families with a reachable server, Get Text uses the correct mode with `RefreshBefore = true`, and no swallowed exception or cell message appears in the trace or the `{timestamp}_ComputerVision` dump — then the wrong result is NOT a silent-suppression artifact. Stop applying this playbook and route by what actually happened: a genuine match failure ([cv-element-not-found.md](./cv-element-not-found.md)), a server error ([cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md)), or a post-find action failure ([cv-action-failed-after-find.md](./cv-action-failed-after-find.md)). Do not recommend toggling `ContinueOnError` or `InRegion` when the evidence does not show suppression — that is a fabricated fix.
