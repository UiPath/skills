# Computer Vision (CV) Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's namespace and class match the reported failure (e.g., `UiPath.CV.Activities.CvClickWithDescriptor`). CV Click / CV Type Into / CV Get Text / CV Element Exists run different post-find paths; the scope (`CVScope`) faults before any of them. Don't treat one CV activity's evidence as another's.
- **Display names are narrative, not evidence** — activity display names, process names, and workflow comments describe intent; they never confirm or eliminate a hypothesis. Decide from exception type, message text, the `*_ComputerVision` runtime dump, traces, and output values. Repro/test workflows carry display names that assert a cause — weigh only the recorded behavior.
- **Descriptor target** — the descriptor target/anchors in evidence are the ones the user reports (the same friendly/label text, the same table cell). A descriptor copied from a different activity or workflow is different evidence. Confirm whether the descriptor is recorder-captured, a variable, or programmatically built — it routes invalid-descriptor causes.
- **Scope (`CVScope`)** — the enclosing scope in evidence is the one wrapping the reported activity, with the same `Server` / `UseLocalServer` / `OCREngine` / `CvMethod` / `Target` config. A different scope = a different session, a different target window, a different server = unrelated data.
- **Workflow file** — if the project has multiple workflows, the error originates from the workflow the user is asking about, not a different `.xaml` / `.cs` using the same CV activity.
- **Timestamp** — the failure occurred during the time window the user reported. The `*_ComputerVision` dump and traces are timestamped; match the dump to the failed run. Load-bearing whenever the screen, window state, or server health may have changed between runs.

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Cross-Cutting Error Classes

Many CV failures are **not specific to one activity** — they come from the shared session/server/find layer and can surface from any CV activity. The exception **type** plus the **message text** is the primary router (server errors all share `System.ArgumentException`; `ElementNotFoundException` covers plain not-found, scroll-exhausted, and cell sentences). The leading `[Error code: <N>]` is informational — match the text, not the HTTP digits. When the class is cross-cutting (server/auth/throttle), investigate the scope/server/network rather than over-focusing on the faulted activity's descriptor.

Route by message / signature:

- `Element not found` (`UiPath.CV.ElementNotFoundException`), or `CV Element Exists` returning `false`, after a find attempt → [cv-element-not-found](./playbooks/cv-element-not-found.md).
- `Scrolled the entire screen, but element was not found` (`ElementNotFoundException`, `ScrollDirection != None`) → [cv-scroll-search-failures](./playbooks/cv-scroll-search-failures.md).
- A cell sentence — `Could not find table. Cell targeting supports only tables as target`, `Invalid column number <n>`, `Table only contains <count> columns and column number is <n>`, `Invalid row number <n>`, `No row in column <c> had a text containing <v>`, etc. (`ElementNotFoundException`, descriptor targets a cell) → [cv-cell-targeting-failures](./playbooks/cv-cell-targeting-failures.md).
- `Invalid Descriptor` / `Reason: Target must be set` / `Reason: Invalid image reference or value` (`UiPath.CV.InvalidDescriptorException`, thrown before any find) → [cv-invalid-descriptor](./playbooks/cv-invalid-descriptor.md).
- `[Error code: 401]` auth, `[Error code: 403]`/5xx unreachable, `[Error code: 429]` throttling, `[Error code: 413]` payload, OCR word limit (cloud `The ComputerVision server has hit the maximum number of words...` or local `UiPath.ComputerVision.LocalServer has hit the maximum number of words...`), `Error while sending request.` / `Response from server is not valid.` transport (`System.ArgumentException`, on a child's first refresh) → [cv-server-auth-throttling-network](./playbooks/cv-server-auth-throttling-network.md).
- Fault **at scope entry** before any child ran — `Please make sure you have UiPath.ComputerVision.LocalServer package installed...`, `Server or OCR engine is required.`, `The target Element was not specified for this activity.`, AVX2 / VC++ local-server prerequisites, `Activity is valid only inside a CV Screen Scope` → [cv-scope-setup-failures](./playbooks/cv-scope-setup-failures.md).
- Element **was found**, then a raw driver/`COMException`, `Value cannot be null. (Parameter 'Secure')`, or an unwrapped non-CV exception on the click/type → [cv-action-failed-after-find](./playbooks/cv-action-failed-after-find.md).
- `CV Get Text` returned empty / `null` / stale / partial / wrong text **without faulting** → [cv-get-text-empty-or-wrong-result](./playbooks/cv-get-text-empty-or-wrong-result.md).
- **No exception** but wrong/empty/default output, false-positive/negative `CV Element Exists`, `OutRegion = (0,0,0,0)`, `ContinueOnError`/`InRegion` suppression → [cv-silent-failures-and-false-results](./playbooks/cv-silent-failures-and-false-results.md).

## Testing Prerequisites

When testing hypotheses for Computer Vision Activities issues, gather and verify these before drawing conclusions:

1. **Activity identity and properties** — capture the class name and display name from the workflow source or stack trace, plus the input properties that address the target: `Descriptor` (and whether it targets a cell — `Target.CellExtraInfo`), `MethodType` (CV Get Text: OCR vs `ClipboardRow`/`ClipboardAll`), `Text` (CV Type Into), `RefreshBefore`, `ScrollDirection` / `NumberOfScrolls` / `DelayScreenshotAfterScroll`, `DelayBefore`. The playbook will name the subset that matters.
2. **Package version** — `UiPath.ComputerVision.Activities` version, and the activity's `Version` / `FeatureVersion` property. `Version < V3` disables cell targeting; messages, friendly mappings, and behavior shift across versions.
3. **`TimeoutMS`** — the configured find timeout. Timeout expiry surfaces as `ElementNotFoundException`, not a timeout type. Note: the `Scroll = true` scrollable-extraction phase and scroll-reset are NOT bounded by `TimeoutMS`.
4. **`ContinueOnError`** — on the failing activity AND on the enclosing `CVScope`. Either being `true` suppresses every exception to a default output and enables the whole silent-failure class.
5. **`InRegion`** — whether it is bound. A set `InRegion` bypasses descriptor matching and screen analysis entirely (false-positive Exists, wrong-coordinate clicks); trace whether its source is stale.
6. **Scope config: server URL vs LocalServer** — read the enclosing `CVScope`: `Server`+`ApiKey` (cloud) vs `UseLocalServer` (local server), `OCREngine`, `CvMethod`, `ScrollOffset`, `Target` selector + `WaitForReady`. Also check **project settings** — `UseLocalServer`, `Server`, and `CvMethod` can be set there and override empty scope-level values. For LocalServer, confirm the package on the **failing** machine, not the dev machine.
7. **Run timestamp** — exact time the activity executed. Required to match the `*_ComputerVision` dump and traces to the failed run, and for any investigation where the screen, window state, or server health changed between runs.
8. **Runtime dump `*_ComputerVision` JSON availability** — locate the timestamped dump written by `RuntimeDumpInfoService` just before a find throws (or swallows) `ElementNotFoundException`. It captures the descriptor, scraped/detected text, detected elements, detected tables, the selector, and the screenshot at failure time — the primary forensic artifact distinguishing "UI changed" from "screen blank" from "OCR degraded". A dump exists only when the **find** failed; its absence with a faulted activity means the failure was after the match (action path) or before it (descriptor/scope).
