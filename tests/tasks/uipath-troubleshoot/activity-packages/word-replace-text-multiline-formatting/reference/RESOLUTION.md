# Final Resolution

---

**Root Cause:** The `Replace` value passed to `Replace Text` is built with
**`Environment.NewLine`** (`Main.xaml` joins the address lines with
`String.Join(Environment.NewLine, ...)`). `Replace Text` inserts the text as
a **flat run**, so the OS line breaks do not become Word paragraph breaks —
the three-line address collapses to a single line and the intended
formatting is lost. The replacement itself succeeds (1 occurrence replaced),
so the job is **Successful**; only the layout is wrong.

**What went wrong:** The `AddressBlockFill` job (2026-06-15T10:48) ran green
(State=Successful, no error logs). The trace shows
`[Replace Text] Executed. Replaced 1 occurrence(s) of '[AddressBlock]'.` —
the substitution happened. The defect is purely in how the multi-line value
renders, because the `Replace` expression carries `Environment.NewLine`.

**Why:** `Replace Text` substitutes a string into a text run; it does not
interpret `\r\n` / `Environment.NewLine` as Word paragraph marks. So
multi-line content built with environment newlines is inserted as one run
with no paragraph structure, collapsing to a single line and dropping any
paragraph styling. This is an input-formatting limitation of the activity,
not a template, Search-value, or package-version problem (the match
succeeded).

---

**Evidence:**

### Orchestrator (Propagation)
- Job: AddressBlockFill -- **Successful** at 2026-06-15T10:48:07Z; no faulted jobs in the folder; `or jobs logs --level Error` is empty
- Folder: Address Blocks (key `d4e5f6a7-b8c9-4193-8a0b-5e6f70819203`), machine MOCK-ROBOT-09
- Trace: `Replaced 1 occurrence(s) of '[AddressBlock]'` — the replacement succeeded; the issue is layout, not a missing match.

### Project source (Root Cause)
- `Main.xaml`: the `addressBlock` variable is `String.Join(Environment.NewLine, new String() {"Acme Corp", "500 Industrial Way", "Springfield, IL 62704"})`, and that value is bound to the `Replace` field of `Replace Text` (`Search="[AddressBlock]"`).
- Raw `Environment.NewLine` in the `Replace` value is the cause of the single-line collapse.

---

**Immediate fix:**

The match works; the multi-line value is the problem. Don't rely on
`Environment.NewLine` in `Replace`.

### Fix path A -- use Bookmarks / Form Fields (preferred for rich content)
- Place a **Bookmark or Form Field** at the address position in the template
  and fill it with the **`Set Bookmark Text`** activity, which preserves the
  bookmark's paragraph formatting. Reserve `Replace Text` for plain,
  single-line token swaps.

### Fix path B -- insert paragraph breaks via the object model
- If you must inject multiple paragraphs through replacement, split the
  content and insert real Word paragraph breaks through the Word object
  model rather than passing raw `Environment.NewLine`.
- **Source:** `word-activities/playbooks/replace-text-multiline-formatting.md`

> The job being **Successful is misleading** — the replacement succeeded, so
> no error fires even though the layout is wrong. Validate the rendered
> output (line breaks / formatting), not just the green job state.

---

**Preventive fix:**

1. **Keep `Replace Text` values plain and single-line** — for multi-line or
   styled content use Bookmarks / Form Fields, not `Environment.NewLine`.
   - **Why:** the activity inserts a flat run; OS newlines don't become Word
     paragraph breaks.
   - **Who:** RPA developer.

2. **Validate rendered layout** — assert the multi-line output renders as
   expected so a formatting collapse is caught, not shipped on a green run.
   - **Who:** RPA developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The Replace value carries Environment.NewLine, so Replace Text inserts a flat run and the multi-line address collapses to one line | Medium | Confirmed | Yes | Job Successful + no errors + log "Replaced 1 occurrence of '[AddressBlock]'" + Main.xaml Replace = String.Join(Environment.NewLine, ...) | Use Bookmarks / Form Fields + Set Bookmark Text (or object-model paragraph breaks); keep Replace Text plain |

---

Would you like help converting the address insertion to a Bookmark +
`Set Bookmark Text` approach so the line breaks and formatting are preserved?
