# Final Resolution

---

**Root Cause:** The `Write CSV` activity's `Encoding` property is set to
`"utf8-bom"`, which is **not a valid .NET encoding name**. When the activity
resolves the encoding (`Encoding.GetEncoding("utf8-bom")`), .NET throws
`System.ArgumentException: 'utf8-bom' is not a supported encoding name`.

**What went wrong:** The `CsvEncode` job (started 2026-06-15T15:18:42Z) read the
source CSV successfully, then faulted at the `Write CSV` step with `Write CSV:
'utf8-bom' is not a supported encoding name`. `Main.xaml` sets
`Encoding="utf8-bom"` on the Write CSV — an invented name (the user wanted
"UTF-8 with BOM"), not a canonical .NET encoding.

**Why:** The `Encoding` property must be a name .NET's `Encoding.GetEncoding`
accepts (e.g. `UTF-8`, `utf-8`, `Windows-1252`, `us-ascii`, `utf-16`). Made-up or
descriptive labels like `utf8-bom`, `Unicode (UTF-8)`, or `UTF8 with BOM` are not
recognized and raise an `ArgumentException`. (BOM behavior is not selected via a
special name here.)

---

**Evidence:**

### Orchestrator (Propagation)
- Job: CsvEncode -- Faulted at 2026-06-15T15:18:44.010Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Encoders (key `ea040004-d4e5-4f60-8a04-000000000004`)
- Final error: `Write CSV: 'utf8-bom' is not a supported encoding name.` (`System.ArgumentException`, Parameter 'name') -> `Main.xaml` -> `WriteCsvFile "Write CSV"` (the Read CSV step succeeded first)

### CSV Activities (Root Cause)
- Activity surface: `UiPath.Core.Activities.WriteCsvFile` (Write CSV), `Encoding="utf8-bom"`.
- `Main.xaml` sets the `Encoding` to the invalid string `utf8-bom`; the error names the exact value.

---

**Immediate fix:**

Use a valid .NET encoding name (or none).

### Fix path A -- valid encoding name (preferred)
Set the `Encoding` property to a name .NET accepts — `"UTF-8"` (or `"utf-8"`),
`"Windows-1252"`, `"us-ascii"`, `"utf-16"`, etc. For plain UTF-8 output, use
`"UTF-8"`.

### Fix path B -- leave it default
If a specific encoding isn't required, clear the `Encoding` property to use the
activity default.

### Fix path C -- need a BOM / full control (bulletproof alternative)
If you specifically need UTF-8 **with BOM** or precise encoding control, build the
CSV yourself: **Output Data Table** (DataTable → string) then **Write Text File**,
which lets you control the encoding/BOM cleanly.

### Verification
Open `Main.xaml`, confirm `Encoding="utf8-bom"`; after setting it to `"UTF-8"`
(or clearing it), the Write CSV succeeds.

- **Source:** `csv-activities/playbooks/write-csv-unsupported-encoding.md`

---

**Preventive fix:**

1. **Configuration** -- use canonical .NET encoding names in the `Encoding`
   property; don't invent labels.
   - **Why:** `Encoding.GetEncoding` only accepts registered names; descriptive
     strings throw.
   - **Who:** RPA developer.

2. **BOM/encoding needs** -- when a BOM or specific codepage is required, prefer
   Output Data Table → Write Text File for explicit control.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Write CSV Encoding is set to an invalid .NET encoding name ("utf8-bom"), so Encoding.GetEncoding throws ArgumentException | High | Confirmed | Yes | `'utf8-bom' is not a supported encoding name` at Write CSV; Main.xaml Encoding="utf8-bom"; Read CSV succeeded first | Use a valid .NET encoding name (UTF-8 / Windows-1252), leave default, or Output Data Table -> Write Text File for BOM control |

---

Would you like help setting a valid encoding (or the Write Text File approach for
UTF-8 with BOM), or cleaning up the `.local/investigations/` folder?
