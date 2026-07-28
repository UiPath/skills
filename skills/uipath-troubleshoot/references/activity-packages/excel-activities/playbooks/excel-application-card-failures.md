---
confidence: medium
---

# Use Excel File / Excel Application Card Failures

## Context

The Modern `Use Excel File` activity (class `UiPath.Excel.Activities.ExcelApplicationCard`, also surfaced as "Excel App Card" in some contexts) and the Classic `Excel Application Scope` are the scope containers that govern an Excel workbook's lifecycle for child activities (Read Range, Write Cell, Append Range, etc.). The card / scope acquires the workbook, manages the underlying provider (OpenXML by default for Modern; Excel COM for Classic and for Modern when COM-forcing properties are set), and releases the file when its body completes.

Failures handled here originate at one of four card/scope surfaces: workbook-path resolution (the configured path is empty, null, or contains illegal characters), Excel-process lifecycle (multiple cards collide on the EXCEL.EXE process without an `Excel Process Scope` to govern them), child-activity placement (a Modern Excel child activity dropped outside any card), or sensitivity-label rejection (Microsoft Purview / AIP-protected workbooks under package versions before the sensitivity-label properties were added). Provider acquisition on a host with no desktop Excel is the cross-activity failure mode in [excel-not-installed.md](./excel-not-installed.md), not a card-specific branch.

What this looks like — Use Excel File / Excel Application Card faults surface as one of these signatures:

- `UiPath.Excel.BusinessException: Error opening workbook. Make sure Excel is installed.` (or a raw Interop class-factory error) — route to [excel-not-installed.md](./excel-not-installed.md), whose activity discriminator separates Classic scope, Classic child activity, and Modern-card COM requirements. If Excel is present, that playbook redirects to the installed-but-broken COM diagnostic.
- `System.ArgumentException: Excel File path is empty or not set` / `System.ArgumentException: Illegal characters in path '<path>'` / `System.IO.FileNotFoundException` from the path-binding step — the configured `WorkbookPath` property evaluates to empty, null, whitespace, or a malformed string. Branch 2.
- `System.Runtime.InteropServices.COMException` with `RPC_E_SERVER_UNAVAILABLE` (`0x800706BA`), `RPC_E_DISCONNECTED` (`0x80010108`), or `CO_E_SERVER_EXEC_FAILURE` (`0x80080005`) — multiple scopes raced on the same EXCEL.EXE process, OR a prior scope tore down the process and a follow-up scope tries to attach. Branch 3.
- `UiPath.Excel.BusinessException` mentioning "must be placed inside" / "missing parent container" — a Modern Excel CHILD activity (Read Range, Write Cell, etc.) was dropped outside any `Use Excel File` / `Excel Application Scope`. Branch 4 (cross-cut).
- `System.Runtime.InteropServices.COMException` or `UiPath.Excel.BusinessException` referencing "sensitivity label", "information protection", or "label is required" — the workbook is protected under a Microsoft Purview / Azure Information Protection (AIP) sensitivity policy and the card doesn't supply the required label / operation properties. Branch 5.

What can cause the four card/scope-local failures (cause-branches — pick the right one from evidence):

(No branch 1 - missing-Excel failures route to [excel-not-installed.md](./excel-not-installed.md).)

2. **Empty / invalid / illegal WorkbookPath** — the `WorkbookPath` property is bound to a variable / expression that evaluates to null, empty string, whitespace-only, OR contains characters illegal in Windows file paths (control chars, NUL, asterisks in mid-path, mixed `/` and `\` separators in some package versions). Common causes: variable declared in an inner scope so the card sees it as `Nothing`; preceding `Read Cell` returned empty; `String.Format` against a `Nothing` produced an empty literal; a config file lookup failed silently.
3. **COM / RPC failures across scopes (race condition or torn-down process)** — common scenarios: two `Use Excel File` cards in sequence against the same path with no `Excel Process Scope` wrapping them (the first card closes EXCEL.EXE; the second tries to attach to a process that no longer exists); parallel branches both opening the same path; a child `Execute Macro` activity called `Application.Quit` from VBA (see also `execute-macro-failures.md` branch 3 for the macro-tears-down-Excel chain). The Modern `Use Excel File` is generally OpenXML by default and avoids this; the failure mode is concentrated on Classic `Excel Application Scope` and Modern cards with COM-forcing properties.
4. **Modern Excel child activity outside any card / scope** — a Read Range, Write Cell, Append Range, Delete Range, Execute Macro, etc. sits at the workflow root without a `Use Excel File` (Modern) or `Excel Application Scope` (Classic) wrapping it. The child activity throws `BusinessException: <activity> must be placed inside a 'Use Excel File' container`. This is a child-activity failure surface — see the individual activity playbooks (`append-range-failures.md`, `delete-range-failures.md`, etc.) for the per-activity diagnostic chain; this playbook's branch 4 is a brief cross-cut.
5. **Sensitivity label rejection (Microsoft Purview / AIP)** — the workbook has a sensitivity label applied (e.g., "Confidential", "Highly Confidential", "Internal Use Only") under Microsoft Purview / Azure Information Protection. The Excel card opens the file but cannot write to it without supplying the appropriate `SensitivityLabel` / `SensitivityOperation` properties (introduced in `UiPath.Excel.Activities` v2.23.4+). On pre-v2.23.4 packages the card has no way to supply the label; on v2.23.4+ the failure means the workflow needs to set the properties explicitly.

What to look for:

- **The exception class and message** — first signal. `BusinessException: Error opening workbook. Make sure Excel is installed.` / `REGDB_E_CLASSNOTREG` → [excel-not-installed.md](./excel-not-installed.md). `ArgumentException: path is empty` / `Illegal characters in path` → branch 2. `COMException RPC_E_*` / `0x800706BA` / `0x80010108` / `0x80080005` → branch 3. `BusinessException: must be placed inside` (on a child activity, NOT the card itself) → branch 4. `COMException` / `BusinessException` mentioning sensitivity / label / information protection → branch 5.
- **Workflow source** — which surface is in use (Modern `Use Excel File` / Classic `Excel Application Scope`), the configured `WorkbookPath` (literal vs. expression), the `ReadOnly` property, any COM-forcing properties (`Read Formatting`, `Edit Password`, `Visible`), and whether the workflow has multiple Excel scopes in sequence or parallel.
- **The `WorkbookPath`'s runtime value** — what does the variable / expression resolve to immediately before the card? Log it with `Log Message Level=Info Message=$"WorkbookPath: '{path}' (length={path.Length})"` — empty, whitespace, illegal characters all become visible.
- **Excel Process Scope presence** — if the workflow has multiple `Use Excel File` cards in sequence (or in a loop), is there an outer `Excel Process Scope` wrapping the whole sequence? Without it, each card opens/closes EXCEL.EXE independently and races. Relevant to branch 3.
- **Package version** — `UiPath.Excel.Activities` version from `project.json`. Branch 5 is gated at v2.23.4 (the SensitivityLabel properties weren't available before that).
- **Workbook protection state** — does the workbook have a sensitivity label applied? Open it in Excel and look for the label badge in the title bar / status bar (typically "Sensitivity: Confidential" or similar). Relevant to branch 5.

## Investigation

Go in this order — cheaper checks first.

1. **Capture the exact error, activity surface, and configuration.** From `uip or jobs get <job-key> --output json` → `Info`: exception class, full message, HRESULT, inner exception. From workflow source: which Excel scope surface (Modern card vs. Classic scope), the configured `WorkbookPath`, `ReadOnly`, any COM-forcing properties, whether multiple scopes exist in sequence / parallel, and whether an `Excel Process Scope` wraps them. From `project.json`: the `UiPath.Excel.Activities` version. From job logs: any `Log Message` lines capturing the `WorkbookPath` value before the scope.

2. **Branch the diagnostic on the exception signature.**
   - `BusinessException: Error opening workbook. Make sure Excel is installed.` / raw Interop class-factory failure → open [excel-not-installed.md](./excel-not-installed.md) and stop this playbook.
   - `ArgumentException` referencing "path is empty" / "Illegal characters in path" → branch 2; go to step 3.
   - `COMException` with `RPC_E_SERVER_UNAVAILABLE` / `RPC_E_DISCONNECTED` / `CO_E_SERVER_EXEC_FAILURE` HRESULTs → branch 3; go to step 4.
   - `BusinessException` on a CHILD activity referencing "must be placed inside a Use Excel File / Excel Application Scope" → branch 4; pivot to the per-activity sibling playbook (see [`../summary.md`](../summary.md)).
   - `COMException` / `BusinessException` referencing "sensitivity label" / "information protection" / "label is required" → branch 5; go to step 5.

3. **Confirm branch 2 (empty / illegal WorkbookPath).** Inspect the workflow source. The `WorkbookPath` property is either a literal (rare for branch 2) or an expression. For expression cases:
   - Trace the expression's source variable backward. If it's an `Assign`, did the assignment run in this execution path? If it's an `Out Argument` from an invoked workflow / sub-workflow, did the producer return a non-empty value?
   - Add a `Log Message Level=Info Message=$"WorkbookPath resolved to: '{path}' (length={path.Length}, IsNothing={path Is Nothing})"` immediately before the card and re-run. The log makes the resolved value visible.
   - Check for illegal characters: control chars (NUL, BEL, etc.), embedded newlines (from a config-file read that didn't trim), mixed `\` and `/` separators, mid-path asterisks / question marks, leading/trailing whitespace, unbalanced quotes. The `System.IO.Path.GetInvalidPathChars()` API enumerates the strict illegal-char set.
   - For UNC paths: confirm the share is reachable from the Robot host's session (mapped drive letters from interactive sessions don't auto-map under a Robot session).

4. **Confirm branch 3 (COM/RPC across scopes).** Check:
   - **Multiple sequential `Use Excel File` cards or `Excel Application Scope` blocks?** Look at the workflow source for two or more Excel-scope activities in the same Sequence. Are they wrapped by an `Excel Process Scope` (Modern, outermost)?
   - **Parallel Excel access?** Look for `Parallel` activities containing Excel scopes against the same file path. Excel COM is single-threaded apartment (STA); parallel access is a hard violation.
   - **Macro tearing down Excel?** If a child `Execute Macro` ran VBA that called `Application.Quit` / `Workbooks.Close`, the NEXT card / scope sees an `RPC_E_DISCONNECTED` because its workbook reference points at a process that no longer exists. Cross-cut to [`./execute-macro-failures.md`](./execute-macro-failures.md) branch 3 for the macro-side diagnostic.
   - **Multi-Robot host?** Multiple Robot jobs concurrently invoking Excel COM on the same host hit the STA apartment from different threads. Failures are intermittent (race-dependent).

5. **Confirm branch 5 (sensitivity label rejection).** Check:
   - **Package version**: read `UiPath.Excel.Activities` from `project.json`. If < 2.23.4, the SensitivityLabel / SensitivityOperation properties don't exist in the card. The fix requires a package upgrade. If ≥ 2.23.4, continue.
   - **Workbook protection state**: open the target workbook in Excel on a developer host. Look for the sensitivity badge in the title bar (e.g., "Sensitivity: Confidential — UiPath Internal"). If absent, the failure isn't branch 5; recheck against the other branches.
   - **The card's `SensitivityLabel` / `SensitivityOperation` properties**: are they configured on the failing card? If left empty AND the workbook has a label that requires programmatic acknowledgement, the write fails. The fix is to set the properties to match the workbook's label.

The root cause is **which of the four local surfaces** the failure maps to after the missing-Excel redirect is excluded. A confirmed finding names the surface (Modern card / Classic scope), the resolved `WorkbookPath` value (for branch 2), the scope-nesting topology (for branch 3), or the workbook's sensitivity label state (for branch 5).

## Resolution

Map the branch identified in Investigation to the fix:

- **Branch 2 — Empty / invalid / illegal WorkbookPath:**
  - **Empty / null variable**: trace the variable's source upstream. If the producer can legitimately return empty (e.g., a config-file read where the key is missing), guard the card with `If` checking `Not String.IsNullOrWhiteSpace(workbookPath)`. Skip the card or log/throw a clear error in the false branch.
  - **Variable scope drift**: move the variable declaration to the parent scope of the card so the card sees the assignment. Or initialize the variable at declaration to a known-default value.
  - **Illegal characters**: sanitize the path before passing to the card. Strip control chars with `Regex.Replace(path, "[\x00-\x1F]", "")`. Trim whitespace with `path.Trim()`. Normalize separators with `path.Replace("/", "\\")`. Validate against `Path.GetInvalidPathChars()` and abort with a clear error if any remain.
  - **For paths built from string interpolation**: log the resolved value before the card to confirm the expression evaluates as expected. A `Log Message` of the full resolved path is the cheapest debugging insurance.
  - **For UNC paths**: confirm the Robot user has access to the share. Test with `Test-Path` PowerShell on the Robot host; if it fails, the share isn't reachable from the Robot's session and the path string is irrelevant (the file open will fail regardless).

- **Branch 3 — COM / RPC failures across scopes:**
  - **Wrap multiple sequential Excel scopes in an `Excel Process Scope`** (Modern, outermost). The Process Scope is the recommended pattern for any workflow with more than one `Use Excel File` against the same or different paths in sequence. It governs the EXCEL.EXE lifecycle across the inner scopes, so the second card doesn't try to attach to a dead process.
  - **Avoid `Parallel` activities containing Excel scopes against the same file** — STA apartment is single-threaded; the parallel design is incompatible. Restructure to sequential.
  - **For macro-tears-down-Excel**: see `execute-macro-failures.md` branch 3. Remove `Application.Quit` / `Workbooks.Close` from the VBA so UiPath owns the lifecycle.
  - **For multi-Robot host concurrency**: serialize Excel access at the orchestration layer (single-performer queue, per-host lock asset) so only one job per host has Excel COM open at a time.
  - **Stop-gap, NOT a fix**: add a `Retry Scope` around the failing card with exponential back-off (3 attempts, 5s/15s/30s). RPC errors are sometimes transient; a retry can mask intermittent races. Treat this as a diagnostic patch — the underlying race condition is still there.

- **Branch 4 — Modern Excel child activity outside any card / scope:**
  - This is the per-activity failure surface — see the individual activity playbooks for the per-activity diagnostic and fix chain (e.g., [`./append-range-failures.md`](./append-range-failures.md) branch 1, [`./delete-range-failures.md`](./delete-range-failures.md) branch 1, etc.). The card's playbook briefly mentions this branch because the user's first hypothesis is often "the card is failing" when in fact the child activity is failing because the card was removed or never present.
  - General fix: wrap the failing child activity in the appropriate scope (Modern `Use Excel File` for Modern activities; Classic `Excel Application Scope` for Classic activities).

- **Branch 5 — Sensitivity label rejection:**
  - **Upgrade `UiPath.Excel.Activities` to v2.23.4 or newer** if currently on an older version. The SensitivityLabel and SensitivityOperation properties are required to write to AIP-protected workbooks.
  - **Configure the card's `SensitivityLabel` property** to match the target workbook's label name (e.g., `"Confidential - UiPath Internal"`). The exact label string must match the Microsoft Purview / AIP policy's label name verbatim.
  - **Set `SensitivityOperation`** to the appropriate operation (`Keep` to preserve the label, `Apply` to set/change it, `Remove` to clear it — naming may vary by package version).
  - **Verify the Robot user has the AIP rights** to operate on the label. Microsoft Purview enforces label-level user / group permissions; if the Robot user isn't in the label's allowed list, the operation will fail with a different error (auth-related) at the AIP layer.
  - **For workbooks where label management isn't part of the workflow's intent**: use `Keep` to pass through the label unchanged. The workflow reads / writes data; the label stays.

## Anti-patterns (what NOT to do)

Common advice for Use Excel File / Excel Application Card failures contains workarounds that hide bugs rather than fix them. The agent should NOT recommend any of these as a primary resolution.

- **"Add a `Delay` before the Use Excel File card."** A Delay is a workaround for a race condition the workflow author hasn't diagnosed. For branch 3 (COM/RPC across scopes), the Delay sometimes works because the prior EXCEL.EXE finally terminates within the delay window — but the underlying race is still there. A reliable fix is wrapping the scopes in an `Excel Process Scope` to govern the EXCEL.EXE lifecycle. If a Delay seems to "fix" the issue, treat it as a diagnostic hint that there's a real race condition to address.

- **"Wrap the Use Excel File card in a bare `Try Catch` and continue on error."** A bare Try-Catch that catches `Exception` / `BusinessException` / `COMException` and only logs without re-throwing turns scope failures into silent skips — the child activities inside the catch don't run, and the workflow proceeds with stale or missing data. It hides COM/RPC races, sensitivity-label denial, and the externally routed missing-Excel failure. Use Try-Catch only with a real recovery path (retry with cleaned config, notify ops, fall back to Workbook activities, etc.).

- **"Set `Visible: True` on the card to 'see what's happening'."** For unattended Robots, `Visible: True` makes the Excel UI appear on the desktop session — but in many unattended sessions the desktop isn't rendered, so the property has no effect. Worse, for headless / no-Excel deployments, `Visible: True` is a COM-forcing property that turns a Modern OpenXML workflow into a Modern COM workflow and routes the failure to [excel-not-installed.md](./excel-not-installed.md). Don't set `Visible: True` unless you specifically need to interact with the Excel UI from the workflow.

- **"Downgrade `UiPath.Excel.Activities` to silence the sensitivity-label error."** Branch 5's error was added because pre-v2.23.4 packages had no way to handle AIP-protected workbooks correctly — the workflow would either silently produce wrong data OR throw a confusing AIP-side error elsewhere. The explicit SensitivityLabel properties are the FIX, not the symptom. Downgrading the package reintroduces the original problem.

## Prevention (cross-branch)

- For workflows with multiple `Use Excel File` cards in sequence (or in a loop), default to wrapping them in an `Excel Process Scope`. The Process Scope is cheap (no per-iteration cost when there's only one card) and prevents the branch 3 race conditions when the workflow grows.
- For Robot hosts without Excel installed, follow [excel-not-installed.md](./excel-not-installed.md): audit all `Use Excel File` cards for COM-forcing properties and migrate data-only work to OpenXML-capable activities.
- For workflows whose `WorkbookPath` is dynamic (from config, scraping, queue payload, etc.), validate the resolved path with a guard activity (`If Not String.IsNullOrWhiteSpace(path) AndAlso File.Exists(path) Then ...`) before the card. The validation is cheap; the alternative is debugging an opaque path error later.
- For workbooks under enterprise sensitivity-label policies, pin `UiPath.Excel.Activities` to v2.23.4 or newer in `project.json`. Document the sensitivity-label requirement in the workflow comments so future contributors don't accidentally downgrade.
- Avoid `Parallel` activities containing Excel scopes. STA apartment is a hard constraint; design around it with sequential or queue-serialized access.
- When refactoring a workflow that removes a `Use Excel File` card, audit every nested Excel activity to ensure the scope removal didn't orphan any of them (branch 4 cross-cut).

## Related

- Other Excel Activities failure fingerprints (per-child-activity playbooks) are separate; see [`../summary.md`](../summary.md) for navigation. Branch 4 (child activity outside any card) pivots to the corresponding per-activity playbook (`append-range-failures.md`, `delete-range-failures.md`, `execute-macro-failures.md`, etc.).
- [`./excel-not-installed.md`](./excel-not-installed.md) — failure-mode playbook for missing desktop Excel across Classic activities, Classic scopes, and Modern cards that selected COM.
- [`./execute-macro-failures.md`](./execute-macro-failures.md) — branch 3's cross-cut on macros tearing down Excel via `Application.Quit` / `Workbooks.Close`. The card-side and macro-side symptoms are linked; fixing one without the other leaves the workflow brittle.
- [`./delete-range-failures.md`](./delete-range-failures.md) — sibling range-mutation playbook; branch 4 of this playbook cross-cuts that playbook's branch 1.
- [`../overview.md`](../overview.md) — package overview, including the scope-container model and the OpenXML-vs-COM provider distinction load-bearing for branch 3 and the missing-Excel redirect ([excel-not-installed.md](./excel-not-installed.md)).
- For headless workflows that can't (or shouldn't) require Excel installed: consider migrating Excel automation to the cloud surface via `o365-activities/` (Microsoft Graph API). That surface has no Excel COM dependency and avoids branches 3 and 5's COM-side failures and the missing-Excel failure mode entirely. Sensitivity labels are still respected via the Graph API but through a different property model.
