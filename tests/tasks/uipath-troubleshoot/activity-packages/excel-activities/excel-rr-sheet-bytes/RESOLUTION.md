# Final Resolution

---

**Outcome:** The `uip` CLI evidence confirms the playbook match
and rules out most cause-branches. Distinguishing branch 5
(whitespace) from branch 6 (look-alike Unicode) requires
byte-level inspection — visual comparison can never settle it.
Two outcomes are correct:

- **(a) Byte-verified branch identification.** The raw
  `Get Workbook Sheets` JSON payload preserves the actual name's
  bytes. An agent that byte-dumps its saved raw response, proves
  the specific code-point difference (here: `C2 A0` = NBSP
  `U+00A0` inside the workbook's tab name vs regular `U+0020` in
  the configured `SheetName`), and names branch 6 with the
  matching fix has fully resolved the case.
- **(b) Diagnostic recommendation.** If the byte-level evidence
  is not inspected, the correct action is to recommend the
  host-side PowerShell byte-compare snippet from the playbook,
  NOT to guess which character differs.

Asserting branch 5 or branch 6 WITHOUT byte-level verification is
the failure mode.

**What the CLI evidence does establish:**

- Failing job `cc333333-7777-8888-9999-000011112222` faulted at
  `2026-05-19T08:00:02.812Z` with `UiPath.Excel.BusinessException:
  The sheet with the name 'Quarterly Data' does not exist.`
- The fingerprint matches the read-range-sheet-not-found playbook.
- The workflow's `Get Workbook Sheets` activity ran successfully
  and logged the actual sheet titles. The logged list **visually**
  contains `Quarterly Data`. Workflow source has a literal
  `SheetName: "Quarterly Data"` on the failing `Read Range`.
- The configured name and the logged name render identically in
  every UI surface — terminal output, editor, log viewer.

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

**What visual comparison CANNOT determine (byte-level
inspection required):**

- Whether the apparent space in the actual name is a regular
  space `U+0020` or a non-breaking space `U+00A0`, an ideographic
  space, or another whitespace code point (branch 5 / 6).
- Whether any other character in the name (the letters
  themselves) is a Latin or Cyrillic or other-script look-alike
  (branch 6).
- Whether there is invisible leading or trailing whitespace
  (branch 5).

JSON serialization in the agent's tool output preserves the bytes,
so a byte-level dump of the saved raw response is conclusive for
the actual name — but the agent's rendering of the strings
(terminal, editor) is not; look-alikes render identically. If the
raw bytes are not inspected, the only reliable way to identify the
differing code point is a byte-level dump on a host that can run
PowerShell or an equivalent.

---

**Recommended Fix (Resolution):**

Ask the user to capture host-side evidence on `MOCK-HOST` (or any
host with PowerShell access — the comparison itself does not
require the Robot host). The bytes do not change between hosts:

1. **Run the byte-compare snippet from the playbook.**
   ```powershell
   $configured = 'Quarterly Data'        # exactly as in the workflow's SheetName
   $actual     = 'Quarterly Data'        # copy from the workbook's tab name in Excel
   "configured: $($configured.Length) chars  bytes: $(([System.Text.Encoding]::UTF8.GetBytes($configured) | ForEach-Object { $_.ToString('X2') }) -join ' ')"
   "actual:     $($actual.Length) chars  bytes: $(([System.Text.Encoding]::UTF8.GetBytes($actual) | ForEach-Object { $_.ToString('X2') }) -join ' ')"
   ```

2. **Interpret the result:**
   - **Equal `.Length`, differing byte sequences** → branch 6
     (look-alike Unicode). Identify the offending code point
     from the byte diff (the most common offenders: `C2 A0` =
     NBSP `U+00A0`, `D0 B0` = Cyrillic `а` `U+0430`).
   - **Differing `.Length`** → branch 5 (whitespace). One of the
     names has leading or trailing whitespace the other lacks.
   - **Equal `.Length`, equal byte sequences** → not this
     playbook; re-triage with a different fingerprint.

3. **Apply the per-branch fix from the playbook:**
   - Branch 5 (whitespace): trim in the workflow (`SheetName =
     name.Trim()`) and audit the upstream source of the
     configured name; or coordinate with the workbook publisher
     to rename without the whitespace.
   - Branch 6 (look-alike): replace the offending character with
     the intended code point in whichever side has the wrong
     one. Common in this scenario: the workbook's sheet name was
     copy-pasted from an email or Word doc that auto-converted
     space → NBSP. Rename the sheet in Excel to use a regular
     space.

**Anti-pattern to avoid:** Confidently picking branch 5 or
branch 6 (or any other branch) from visual intuition without
byte-level verification (a dump of the raw payload bytes, or the
byte-compare snippet). Visual comparison narrows the candidates
but does not identify the specific code point; recommending the
WRONG fix wastes operator time and erodes trust.

**Prevention:** Workflow authors should normalize sheet names
sourced from external data (email, Word, internationalized
inputs). Replace any non-`U+0020` whitespace code points
(`U+00A0` NBSP, `U+202F` narrow NBSP, `U+205F` math space,
`U+3000` ideographic space, etc.) with regular space, then
`.Trim()` the result. Workbook publishers should
avoid copy-pasting sheet names from rich-text sources without
verifying with a byte-dump tool.
