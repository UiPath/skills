# Computer Vision (CV) Activities

Activities from the `UiPath.ComputerVision.Activities` package. They target UI elements by **visual analysis of a screenshot** instead of selectors — built for virtualized/Citrix/RDP, image-based, and remote desktops where standard selectors are unavailable. Every CV activity runs inside a **CV Screen Scope** (`CVScope`) container that resolves the target window and builds a CV session; the analysis itself runs on a CV server (cloud or local) plus an OCR engine.

## How CV Targeting Works

1. **Screenshot.** The scope captures a screenshot of the target window (a clipped clone of the scope root element).
2. **CV server analysis.** The screenshot is sent to the CV server (`Server`+`ApiKey` cloud endpoint, or `UseLocalServer` local server). The server detects UI elements (controls, text via OCR, tables) and returns their regions.
3. **Descriptor matching with anchors.** The activity's `Descriptor` (a target + optional anchors) is matched against the detected elements. `Anchor2Service` locates the target and each anchor individually, then validates the **geometric relationship** between them — a match requires both the elements and their relative positions to hold.
4. **Action at screenshot-derived coordinates.** The matched region yields **coordinates**, not a live element. The activity clicks / types / reads text at those coordinates with hardware events forced (`SimulateClick`/`SimulateType`/`SendWindowMessages` are disabled internally). Because it acts on coordinates, anything that moves the window between analysis and action lands the action in the wrong place.

The find runs with retries until `TimeoutMS`; `ScrollDirection != None` adds scroll-search (scroll + re-analyze). Failures originate at any layer — scope setup, server analysis call, descriptor matching, or the post-find action — and knowing which layer threw narrows the investigation.

## Key Activity Types

| Display Name | Class Name |
|---|---|
| CV Screen Scope | `CVScope` |
| CV Click | `CvClickWithDescriptor` |
| CV Type Into | `CvTypeIntoWithDescriptor` |
| CV Get Text | `CvGetTextWithDescriptor` |
| CV Element Exists | `CvElementExistsWithDescriptor` |

`CV Element Exists` is special: it catches `ElementNotFoundException` internally and returns `Result = false` rather than faulting. Server, descriptor, and scope errors still throw from it.

## Exception Types

- **`UiPath.CV.ElementNotFoundException`** — the descriptor (target/anchors) did not match within `TimeoutMS`. Message is usually the literal `Element not found`. **Timeout expiry surfaces as this type, NOT `TimeoutException`** — there is no separate timeout exception. The scroll-exhausted variant (`Scrolled the entire screen, but element was not found`) and the nine cell-targeting sentences are also this type.
- **`UiPath.CV.InvalidDescriptorException`** — the `Descriptor` argument is null-`Target`, has broken image references, or failed to parse/evaluate. Thrown **before any find attempt**, synchronously when the activity resolves the descriptor.
- **`System.ArgumentException`** — CV **server** errors. Built by `CVSessionData.Compute` via `cvData.ToErrorMessageWithCode()` when the analysis response is null, carries an `Error`/`LocalServerError`, or has `OCRWordLimitPassed = true`. Carries `[Error code: <N>]` text — auth (401), unreachable/forbidden (403/5xx), throttling (429), payload too large (413), OCR word limit. Also the type for the local-server-package-missing scope-setup error.

## Common Failure Patterns

### Find (descriptor matching)

- **Element not found** — `ElementNotFoundException` / `Element not found` after the retry loop exhausts `TimeoutMS`. UI changed since design time, wrong screen state, broken anchor geometry, DPI/scale mismatch, scope refresh failure, or silent OCR degradation.
- **Invalid descriptor** — `InvalidDescriptorException`. Null `Target`, image references unresolvable across copied descriptors, or expression parse failure. Mostly hits programmatically built / copied / hand-edited descriptors, not recorder-captured ones.
- **Cell-targeting failures** — `ElementNotFoundException` carrying one of nine cell-specific sentences (`Could not find table...`, `Invalid column number <n>`, `Table only contains <count> columns...`, `No row in column <c> had a text containing <v>`, etc.). Table not detected, index out of range / `< 1` (1-based), name/value mismatch, or old `FeatureVersion` (< V3) with cell targeting disabled.
- **Scroll-search failures** — `Scrolled the entire screen, but element was not found`. Wrong scroll axis, scroll point off the scrollable pane, `NumberOfScrolls` too large, silent scroll skip on a non-driver scope root, or genuine absence.

### Server (analysis call)

- **Auth / unreachable / throttling / payload / word-limit / network** — `System.ArgumentException` with `[Error code: <N>]` text. 401 auth, 403/5xx unreachable, 429 rate limit, 413 payload, OCR word limit, or transport (`Error while sending request.` / masking `Response from server is not valid.`). Surfaces lazily on the first child activity's first refresh, not at scope entry.

### Scope (setup)

- **Scope setup failures** — fault at scope entry before any child runs: LocalServer package missing, scope window selector did not resolve, root element selector unreadable (`COMException` → `The target Element was not specified for this activity.`), missing server/OCR config, AVX2/VC++ local-server prerequisites, design-time placement constraints.

### Silent (no fault)

- **Silent failures / false results** — no exception, wrong/empty/default output. `ContinueOnError = true` swallows every exception to a default; `InRegion` bypasses CV entirely (false-positive Exists, wrong-coordinate clicks); `CV Element Exists` converts infrastructure failures to `Result = false`; `CvMethod` disables a detection family.
- **Action failed after find** — element found, then the click/type failed: window moved (stale coordinates), focus stolen, input blocked (locked/RDP/UAC), null `SecureString` (`Value cannot be null. (Parameter 'Secure')`), or an unwrapped non-CV exception.
- **Get Text empty/stale/wrong** — `CV Get Text` returned without fault but text is empty/stale/partial/wrong: silent OCR scrape failure, stale OCR cache (`RefreshBefore = false`), region clipping, OCR language mismatch, or clipboard mode on a non-editable target.

## Package

NuGet: `UiPath.ComputerVision.Activities`
