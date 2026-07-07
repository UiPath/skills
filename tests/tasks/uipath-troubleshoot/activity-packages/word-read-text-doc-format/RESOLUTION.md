# Final Resolution

---

**Root Cause:** `Main.xaml` reads the document with the **standalone**
`Read Text` activity (`System > File > Word Document`), which is **OpenXML
`.docx`-only**. The input `Contract.doc` is a **legacy binary `.doc`**, so
the OpenXML reader cannot parse it and throws `FileFormatException` ("not a
valid Office Open XML document"). Newer `.docx` files read fine; older
`.doc` files fail.

**What went wrong:** The `LegacyDocReader` job (2026-06-16T09:14) opened
`data\Contract.doc` and faulted with `The file '…\Contract.doc' is not a
valid Office Open XML document. Only .docx files are supported by this
activity` (`System.IO.FileFormatException`). The job uses the standalone
System Read Text (the project depends only on `UiPath.System.Activities`,
not the Word pack).

**Why:** The standalone `System > File > Word Document` `Read Text` parses
documents through OpenXML, which understands the modern `.docx` package
format only. A legacy `.doc` is a different binary format, so OpenXML reads
it as corrupted/invalid. The Microsoft Word **Interop** used by the
`Use Word File` container, by contrast, opens both `.doc` and `.docx` (it
converts the legacy format on open) — which is the migration path.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: LegacyDocReader -- Faulted at 2026-06-16T09:14:04Z (ran ~2s)
- Folder: Legacy Docs (key `a7b8c9d0-e1f2-4193-9d3e-920314a5b6c7`), machine MOCK-ROBOT-11
- Final error: `System.IO.FileFormatException: … not a valid Office Open XML document. Only .docx files are supported` on `data\Contract.doc` -> standalone `Read Text` -> `Main.xaml`

### Project source (Root Cause)
- `Main.xaml`: the `Read Text` activity has its **own** `FileName` (`data\Contract.doc`) and is **not** inside a Word scope — it is the standalone System activity.
- `project.json` depends only on `UiPath.System.Activities` (no `UiPath.Word.Activities`), confirming the OpenXML standalone surface with no Interop path. `.doc` input + OpenXML-only reader = the format fault.

---

**Immediate fix:**

Read the legacy `.doc` through Interop, or convert it first.

### Fix path A -- read .doc through Use Word File (Interop)
- Wrap the read in a **`Use Word File`** container (or legacy
  `Word Application Scope`) and read with the Word-pack `Read Text` inside
  it. The Word Interop the container uses opens and reads **both `.doc` and
  `.docx`** seamlessly (it converts the legacy format on open). Requires
  desktop Word on the host.

### Fix path B -- convert to .docx first
- If you must keep the standalone System activity, convert the `.doc` to
  `.docx` up front (open-and-save-as via a Word scope, or a conversion
  step), then read the resulting `.docx`.
- **Source:** `word-activities/playbooks/read-text-doc-format.md`

> The file exists and the path is correct — it is the legacy `.doc` format
> the OpenXML standalone activity cannot parse, not a missing/corrupt file.

---

**Preventive fix:**

1. **Match the Read Text surface to the file formats you ingest** — if the
   portfolio includes legacy `.doc`, read through a `Use Word File`
   (Interop) rather than the OpenXML standalone activity.
   - **Why:** the standalone System Read Text is `.docx`-only.
   - **Who:** RPA developer.

2. **Normalize inputs** — convert incoming `.doc` to `.docx` at intake so
   downstream OpenXML activities work uniformly.
   - **Who:** RPA developer / intake process.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The standalone System Read Text is OpenXML .docx-only and fails on the legacy binary .doc input | Medium | Confirmed | Yes | `FileFormatException: not a valid Office Open XML document … only .docx` on `Contract.doc` + standalone Read Text with own FileName + project depends only on UiPath.System.Activities | Read the .doc through a Use Word File (Interop reads both), or convert it to .docx first |

---

Would you like help moving the read into a `Use Word File` container, or
adding a `.doc`→`.docx` conversion step before the read?
