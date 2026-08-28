# Mixed-extension upload inbox

Fixture for `../../smoke/upload_multiple_documents.yaml`. `inbox/` holds five
files spanning both sides of the extension whitelist documented in
`skills/uipath-ixp/references/cli-reference.md` § Supported document files:

| File | Verdict | Why it is here |
|------|---------|----------------|
| `invoice_2411.pdf` | supported | plain lower-case case |
| `invoice_2412.png` | supported | second supported extension, so the loop must run more than once |
| `receipt_scan.TIF` | supported | the whitelist is **case-insensitive**; an agent globbing only lower-case extensions skips this one |
| `supplier_notes.docx` | unsupported | `documents upload` rejects it with `Unsupported file type ".docx"` before any network call |
| `manifest.csv` | unsupported | a sidecar an agent might mistake for a document |

**The contents are placeholders, not real documents.** `uip` is PATH-shadowed by
`../mock_template/mocks/uip`, which records the invocation and exits 1 without
reading the file, so only the names and extensions matter. Keeping them as short
text files (rather than copying real PNGs from `../fixtures/`) keeps the repo free
of binaries that no criterion inspects.

Do NOT add a sixth supported file without updating the task's criteria — each
supported file carries its own positive assertion by name.
