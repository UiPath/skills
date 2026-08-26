# Final Resolution

---

**Root Cause:** The workbook's actual sheet tab name is `Quarterly Data`
with a **non-breaking space `U+00A0`** between the words, while the
workflow's `Read Range` uses the literal `SheetName: "Quarterly Data"`
with a regular space `U+0020`. The two names render identically in every
human-facing UI surface (Excel tab bar, Orchestrator log viewer, Studio),
but the exact/ordinal string comparison fails, so the activity throws
`UiPath.Excel.BusinessException: The sheet with the name 'Quarterly Data'
does not exist.`

**What the CLI evidence establishes:**

- Failing job `cc333333-7777-8888-9999-000011112222` faulted at
  `2026-05-19T08:00:02.812Z` with `UiPath.Excel.BusinessException:
  The sheet with the name 'Quarterly Data' does not exist.`
- The fingerprint matches the read-range-sheet-not-found playbook.
- The workflow's `Get Workbook Sheets` activity ran successfully
  and logged the actual sheet titles. The logged list **visually**
  contains `Quarterly Data`. Workflow source has a literal
  `SheetName: "Quarterly Data"` on the failing `Read Range`.

**What the CLI evidence RULES OUT:**

- **Branch 1 (typo):** the configured name and the logged actual
  name are visually identical.
- **Branch 2 (case mismatch):** identical visible characters,
  identical apparent casing.
- **Branch 3 (sheet renamed):** the configured name appears in
  the Get Workbook Sheets output — the publisher did not rename
  it away.
- **Branch 4 (sheet deleted):** the configured name appears in
  the Get Workbook Sheets output — the sheet is present.
- **Branch 7 (dynamic expression resolved wrong):** workflow
  source shows `SheetName="Quarterly Data"` as a literal string,
  not an expression.

**The decisive evidence:** the `Get Workbook Sheets` entry in the job
logs preserves the actual tab name **byte-for-byte** — JSON tool output
carries the real code points even though every human rendering collapses
them to an ordinary space. Inspecting the logged title at the byte /
code-point level (reading the raw log payload, dumping the string's code
points, or any equivalent) reveals `U+00A0` between `Quarterly` and
`Data`, while the configured literal uses `U+0020`.

**Acceptable diagnosis paths (either is correct):**

1. **Byte-level identification from the captured evidence** — state that
   the actual tab name contains a non-breaking space `U+00A0` where the
   configured name has a regular space `U+0020`, citing the byte /
   code-point content of the `Get Workbook Sheets` log output (branch 6,
   look-alike whitespace).
2. **Impasse + host-side byte-compare** — if the byte content was not
   extracted from the logs, narrow the cause to branch 5 / branch 6
   (invisible whitespace or look-alike code point), state that the
   specific code point still needs byte-level confirmation, and hand the
   user the PowerShell byte-compare snippet below — WITHOUT asserting
   which code point it is.

---

**Recommended Fix (Resolution):**

1. **Rename the sheet tab** in the workbook to use a regular space.
   Common origin in this scenario: the tab name was copy-pasted from an
   email or Word document that auto-converted space → NBSP. Alternatively
   (when the workbook cannot be changed) normalize in the workflow:
   resolve the sheet name from `Get Workbook Sheets` output by comparing
   with whitespace normalization (replace `U+00A0` and friends with
   `U+0020`, then trim) instead of a hardcoded literal.

2. **Confirm with the byte-compare snippet** (also the fallback
   diagnostic when the code point could not be read from the logs):
   ```powershell
   $configured = 'Quarterly Data'        # exactly as in the workflow's SheetName
   $actual     = 'Quarterly Data'        # copy from the workbook's tab name in Excel
   "configured: $($configured.Length) chars  bytes: $(([System.Text.Encoding]::UTF8.GetBytes($configured) | ForEach-Object { $_.ToString('X2') }) -join ' ')"
   "actual:     $($actual.Length) chars  bytes: $(([System.Text.Encoding]::UTF8.GetBytes($actual) | ForEach-Object { $_.ToString('X2') }) -join ' ')"
   ```
   `C2 A0` in the byte dump = NBSP `U+00A0`; equal lengths with differing
   bytes = look-alike code point (branch 6); differing lengths = extra
   whitespace (branch 5).

**Anti-pattern to avoid:** asserting a SPECIFIC code point without
byte-level evidence — picking NBSP (or Cyrillic, or trailing space) from
playbook priors when neither the logs' bytes nor a host-side byte-compare
was inspected. Recommending a fix for a code point that was never
observed wastes operator time and erodes trust. Identification is only as
good as the bytes it cites.

**Prevention:** Workflow authors should normalize sheet names
sourced from external data (email, Word, internationalized
inputs). Replace any non-`U+0020` whitespace code points
(`U+00A0` NBSP, `U+202F` narrow NBSP, `U+205F` math space,
`U+3000` ideographic space, etc.) with regular space, then
`.Trim()` the result. Workbook publishers should
avoid copy-pasting sheet names from rich-text sources without
verifying with a byte-dump tool.
