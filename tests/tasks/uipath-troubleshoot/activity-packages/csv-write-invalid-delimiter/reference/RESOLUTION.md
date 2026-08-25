# Final Resolution

---

**Root Cause:** The `Write CSV` activity's `Delimiter` property is bound to a
`String` variable `delimiterName` whose value is the **word** `"Tab"`. The
activity's `Delimiter` expects its delimiter enum value (or the actual delimiter
character), not a localized name — so it cannot convert the text `"Tab"` into a
delimiter and faults with `Failed to create a 'Delimitator' from the text 'Tab'`.

**What went wrong:** The `DelimitedExport` job (started 2026-06-15T10:33:24Z)
read the source CSV successfully, then faulted at the `Write CSV` step with
`Write CSV: Failed to create a 'Delimitator' from the text 'Tab'`
(`FormatException`). `Main.xaml` declares `delimiterName` (`String`) = `"Tab"`
and binds `Delimiter="[delimiterName]"`.

**Why:** The `Delimiter` property is a delimiter selection, not free text. When
it receives a word like `Tab` / `Comma` / `Pipe` (e.g. from a string variable or
typed expression), the activity tries to parse that text into a delimiter and
fails. It needs the enum value chosen in the Properties panel, or the actual
character (`vbTab`, `","`, `"|"`).

---

**Evidence:**

### Orchestrator (Propagation)
- Job: DelimitedExport -- Faulted at 2026-06-15T10:33:26.020Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Extracts (key `ea020002-d4e5-4f60-8a02-000000000002`)
- Final error: `Write CSV: Failed to create a 'Delimitator' from the text 'Tab'.` (`FormatException`) -> `Main.xaml` -> `WriteCsvFile "Write CSV"` (the Read CSV step succeeded first)

### CSV Activities (Root Cause)
- Activity surface: `UiPath.Core.Activities.WriteCsvFile` (Write CSV), `Delimiter="[delimiterName]"`.
- `Main.xaml` variable `delimiterName` (`String`) defaults to `"Tab"` — the word, not a delimiter value/character. The error names the exact text `'Tab'`.

---

**Immediate fix:**

Give `Delimiter` a real delimiter value, not the word.

### Fix path A -- use the dropdown (preferred)
In the Properties panel, select the delimiter (`Tab`) from the `Write CSV`
`Delimiter` drop-down. This sets the correct enum value rather than a string.

### Fix path B -- pass the character literal
If the delimiter must come from an expression, use the actual character — `vbTab`
(or `"\t"`) for tab, `","` for comma, `"|"` for pipe, `";"` for semicolon — not
the words `"Tab"` / `"Comma"` / `"Pipe"`. If `delimiterName` is data-driven, map
the incoming label to the correct enum/character before assigning it.

### Verification
Open `Main.xaml`, confirm `Delimiter` is bound to `delimiterName = "Tab"`; after
selecting `Tab` from the dropdown (or passing `vbTab`), the Write CSV produces the
tab-delimited file and the error is gone.

- **Source:** `csv-activities/playbooks/write-csv-invalid-delimiter.md`

---

**Preventive fix:**

1. **Configuration** -- set `Delimiter` from the activity dropdown, or pass a
   character literal; never feed the activity a localized delimiter name.
   - **Why:** A word like "Tab" cannot be parsed into a delimiter and fails at
     runtime.
   - **Who:** RPA developer.

2. **Data-driven delimiters** -- when the delimiter comes from config/input, map
   the label to the enum/character in code with validation, so an unexpected
   string can't reach the activity.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Write CSV Delimiter is bound to a string variable holding the word "Tab" instead of the enum/character, so the activity can't create a delimiter | High | Confirmed | Yes | `Failed to create a 'Delimitator' from the text 'Tab'`; Main.xaml delimiterName="Tab" bound to Delimiter; Read CSV succeeded first | Select the delimiter from the dropdown, or pass the character literal (vbTab / "\t") instead of the word |

---

Would you like help switching the Delimiter to the dropdown / character literal,
or cleaning up the `.local/investigations/` folder?
