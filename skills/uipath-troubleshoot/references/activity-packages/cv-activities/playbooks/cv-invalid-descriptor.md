---
confidence: high
---

# CV — Invalid Descriptor (missing Target, broken image references, parse/evaluation failure)

## Context

What this looks like — `UiPath.CV.InvalidDescriptorException`, a multi-line composite message assembled from up to three parts (in order):

- `Invalid Descriptor` — always present, first line.
- `Reason: Target must be set` — second line, ONLY when the descriptor's `Target` is null.
- `Reason: Invalid image reference or value` — second line, ONLY when the descriptor uses image targets/anchors that can't be resolved at runtime.
- `Descriptor value: '<expression>'` — always last line. `<expression>` is the **expression text** of the `Descriptor` argument (the variable name or literal), NOT the serialized descriptor payload. Empty (`Descriptor value: ''`) when the expression text can't be extracted.

When there is no `Reason:` line — just `Invalid Descriptor` followed directly by `Descriptor value: '<expression>'` — the descriptor expression itself failed to evaluate or parse (generic wrap). The original parse/evaluation exception is traced but replaced; it is NOT attached as an inner exception, so the trace is the only place to recover the underlying cause.

The job faults **synchronously the moment the activity resolves the `Descriptor` argument** — thrown in `GetDescriptor` during `GetRuntimeContext`, **before any find attempt**. This is what cleanly separates it from element-not-found: the activity never ran a search.

What activities can produce this error:
- **CV Click** (`CvClickWithDescriptor`) — `Descriptor` argument.
- **CV Type Into** (`CvTypeIntoWithDescriptor`) — `Descriptor` argument.
- **CV Get Text** (`CvGetTextWithDescriptor`) — `Descriptor` argument.
- **CV Element Exists** (`CvElementExistsWithDescriptor`) — `Descriptor` argument. **This activity FAULTS — it does NOT return `Result = false`.** `GetRuntimeContext` (which resolves the descriptor) runs before the `try` block that swallows `ElementNotFoundException`, so `InvalidDescriptorException` escapes uncaught. A `false` result means the element wasn't found, not a bad descriptor — different cause (see below).

What can cause it:
- **Descriptor's `Target` is null.** The runtime `Descriptor` argument evaluated to a `CvDescriptor` with no `Target`. Produces the `Reason: Target must be set` line. Almost always a **programmatically built `CvDescriptor`** missing its `Target` node, a variable passed to `Descriptor` that wasn't fully populated, or a hand-edited/corrupted descriptor string in XAML.
- **Image references can't be resolved.** The descriptor uses image-based targets/anchors (`IsImageUsed`) but the image payloads can't be copied from the activity's hidden `DesignTimeDescriptor` (`TrySetImages` failed). Produces the `Reason: Invalid image reference or value` line. Happens when a **descriptor variable is copied/passed between activities** and references images by id that exist only in the *originating* activity's design-time data, or a hand-edited descriptor carries image ids with no embedded payload.
- **Descriptor expression fails to evaluate/parse.** Any exception while evaluating the `Descriptor` InArgument — null variable, bad VB/C# expression, malformed/truncated serialized descriptor string, deserialization error. Produces **no `Reason:` line** (just `Invalid Descriptor` + `Descriptor value:`).

Rare in Studio-authored workflows — the CV recorder/designer always sets `Target` and embeds design-time images. Hit mainly by **programmatically built descriptors, descriptor variables copied between activities, or hand-edited XAML**.

What to look for:
- The `Reason:` line (present/absent and which text) is the primary branch key — read it first.
- The faulted activity is a `Cv*WithDescriptor` whose `Descriptor` argument is bound to a **variable or expression**, not a recorder-captured inline descriptor.

> **Different cause, do not apply this playbook:**
> - Descriptor was captured by the recorder and the element simply wasn't on screen within the timeout → `ElementNotFoundException` / descriptor match failed *after* a find attempt. Use [cv-element-not-found.md](./cv-element-not-found.md).
> - `CvElementExistsWithDescriptor` returns `Result = false` (no fault) → element not found, descriptor was valid. Use [cv-element-not-found.md](./cv-element-not-found.md) or [cv-silent-failures-and-false-results.md](./cv-silent-failures-and-false-results.md) for false-negative/positive traps.
> - The CV Screen Scope (`CVScope`) failed to set up (target window, server URL, API key, OCR config) — fault originates in the scope, before any descriptor activity ran. Use [cv-scope-setup-failures.md](./cv-scope-setup-failures.md).
> - `System.ArgumentException` from CV server analysis (auth 401, unreachable 403/5xx, throttling 429, word limits) → server-side, not descriptor. Use [cv-server-auth-throttling-network.md](./cv-server-auth-throttling-network.md).
> - Element was found but the click/type then failed → [cv-action-failed-after-find.md](./cv-action-failed-after-find.md).

## Investigation

The error is unambiguous about the *class* of failure; the `Reason:` line selects the branch. No find ever ran, so logs/screenshots of "what was on screen" are irrelevant here.

1. Read the full message. Note whether a `Reason:` line is present and its exact text (`Target must be set` vs `Invalid image reference or value`), and capture the `Descriptor value: '<expression>'` text — it names the offending argument expression.
2. Locate the faulted activity in XAML by the exception's activity `IdRef`. Confirm it is a `Cv*WithDescriptor` and read its `Descriptor` argument binding.
3. Determine how `Descriptor` is set: an inline recorder-captured descriptor, a variable assigned earlier, or an expression. Recorder-captured inline descriptors with no further mutation rarely produce this error — a variable/expression binding is the usual culprit.
4. If `Reason: Target must be set` — trace where the bound variable/descriptor was constructed and confirm its `Target` is populated.
5. If `Reason: Invalid image reference or value` — confirm the descriptor uses image targets/anchors and was sourced from a **different** activity than the one running it (copied variable, cross-workflow reuse). The running activity's own `DesignTimeDescriptor` is the only image source it can copy from.
6. If **no `Reason:` line** — the descriptor expression threw. Pull the underlying cause from the **trace** (it is traced but not attached as an inner exception). Inspect the `Descriptor value: '<expression>'` expression for null variables, malformed serialized strings, or bad VB/C# syntax.

## Resolution

Branch on the `Reason:` line. Each branch maps to a distinct fix; the evidence that selects it is the message text plus the descriptor's origin.

### Branch A — `Reason: Target must be set`

Evidence: message second line is `Reason: Target must be set`. The runtime `CvDescriptor` has a null `Target`.

Fix: ensure the `Descriptor` argument resolves to a descriptor with a populated `Target`.
- **If the descriptor is built programmatically:** set its `Target` before passing it in. Do not pass a partially-constructed descriptor.
- **If a recorder-captured descriptor would be simpler:** re-capture the target in the designer (CV recorder always sets `Target`) and bind the activity to that, instead of the hand-built variable.
- **If the XAML descriptor string was hand-edited/corrupted:** re-capture via the recorder rather than patching the string.

> Ruled out: if `Target` is populated in the source descriptor and the activity still throws `Target must be set`, the variable being passed at runtime is not the one inspected — trace the actual binding before recommending a `Target` change.

### Branch B — `Reason: Invalid image reference or value`

Evidence: message second line is `Reason: Invalid image reference or value`. The descriptor uses image targets/anchors but the runtime image payloads couldn't be copied from the running activity's `DesignTimeDescriptor`.

Fix: the image-based descriptor must be **owned by the activity that uses it** — image payloads live in each activity's hidden `DesignTimeDescriptor`, captured at design time, and cannot be borrowed from another activity.
- **If a descriptor variable was copied/reused from another activity or workflow:** re-capture the image target directly on the failing activity in the designer so its own `DesignTimeDescriptor` holds the image bytes. Do not pass an image-based descriptor variable across activities.
- **If the descriptor was serialized/deserialized (lost image payloads):** stop round-tripping image-based descriptors through serialization; bind the activity to a freshly captured descriptor.

> Ruled out: text/non-image descriptors never hit this branch (the image-copy path only runs when `IsImageUsed` is true). If the descriptor has no image target/anchor, this is not your message — re-read the `Reason:` line.

### Branch C — No `Reason:` line (expression parse/evaluation failure)

Evidence: message is `Invalid Descriptor` followed directly by `Descriptor value: '<expression>'`, with NO `Reason:` line. The `Descriptor` expression itself threw while evaluating.

Fix: correct the expression named in `Descriptor value: '<expression>'`.
- **Null variable:** the variable bound to `Descriptor` was never assigned (or assigned null). Ensure it is populated before the activity runs.
- **Malformed/truncated serialized descriptor string:** a hand-edited or programmatically assembled descriptor string failed to deserialize. Re-capture via the recorder or fix the serialization.
- **Bad VB/C# expression:** syntax/type error in the `Descriptor` expression. Fix the expression.
- The underlying exception is in the **trace** (traced, not attached) — read it to identify which of the above applies before recommending a fix.

## Post-presentation actions

Every fix above edits user source files (the `Descriptor` argument binding, the descriptor-building code, or re-capture in XAML). The resolution is **interactive** — you MUST obtain explicit approval via `AskUserQuestion` before any edit.

1. **Sharing a file path is not approval.** A path the user gave for reading the project does not authorize editing it. Issue a separate `AskUserQuestion` before any edit.
2. **Never bundle "gather input" with "apply fix" in one option.** Split into two steps: gather the input, then surface the concrete diff and confirm separately.
3. **Surface the diff before asking.** The apply-fix question MUST include the file path, the activity `IdRef`, the `Descriptor` argument's current value, and the proposed value.
4. **One question per file/fix.** If multiple files are touched (e.g. XAML plus the code that builds the descriptor), list every file or ask file-by-file.
5. **If interactive approval is unavailable or errors, do not edit.** Present the diff as a recommendation and stop. A recommendation-only close is acceptable; a silent edit is never.

## Stop / escalate

If the `Reason:` line and the descriptor's origin are confirmed and the fix above is applied, the error is resolved at the activity. If `Target` is verifiably populated, the descriptor is non-image yet throws the image-reason, or the expression is valid and assigned — the runtime binding being evaluated is not the one inspected: stop and re-trace the actual `Descriptor` value at the faulted activity rather than continuing under this playbook.
