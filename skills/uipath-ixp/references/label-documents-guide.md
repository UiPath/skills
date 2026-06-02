# Label Documents Guide

Reusable workflow for labelling documents in an IXP project. Used by:

- [Project Setup](project-setup-guide.md) — initial labelling after creating a project
- [Improve Prompts](improve-prompts-guide.md) — reviewing predictions during optimization

Claude acts as a **reviewer** — IXP generates predictions, Claude validates them field-by-field against the document. Only fields that are correct get confirmed. Fields that are wrong are left unannotated. Fields where the prediction found the right location but the value is OCR-mangled get corrected.

## Step 1 — Get Documents and Taxonomy

```bash
mkdir -p /tmp/ixp/<project-name>/{docs,text,taxonomies,prompts}
uip ixp documents list <project-name> --output json
uip ixp projects get-taxonomy <project-name> --output json
```

Save the taxonomy to `/tmp/ixp/<project-name>/taxonomies/v1.json` (increment the version on each re-fetch).

From the taxonomy, review the field groups and field types so you understand what each predicted field represents.

## Step 2 — Process Each Document

For each document from the list, process one at a time: get predictions, download image/text, review, confirm.

### 2a. Get predictions for this document

```bash
uip ixp labellings get-predictions <project-name> <document-id> --output json
```

This returns the document's predicted `Labels` (grouped by field group name), each containing `Fields` with `FieldId`, `FieldName`, and `FormattedValue`.

### 2b. Download the document file

- **If the file already exists** in `/tmp/ixp/<project-name>/docs/` from a previous session, reuse it — do NOT re-download.
- **Otherwise, download:**

```bash
uip ixp documents download <project-name> <document-id> -o /tmp/ixp/<project-name>/docs/<document-id> --output json
```

Use the document ID as the filename. Pass `-o` **without an extension** — the CLI detects the actual format (PDF, PNG, JPG, …) from the file content and appends the correct extension. Read the resolved `Path` from the response and use that for the next step. Files persist across sessions — check for existing files before downloading.

### 2c. Review predictions field-by-field

Use the **Read tool** to view the document file (the Read tool handles PDF, PNG, JPG, etc. natively), then review each predicted field against the document:

1. **Look at the document** to understand the layout and where field values appear.
2. **For each predicted field**, assign one of four verdicts:
   - **CONFIRMED** — the predicted value matches what is in the document. Minor OCR-level differences (capitalization, whitespace) are acceptable.
   - **CORRECTED** — **OCR-mangled values only.** The prediction found the right field in the right location, the bytes-on-page are correct, but the text was garbled in transcription (e.g., `MSIÓÓÓ601020/` instead of `MSI0601020`, `lNGRAM` instead of `INGRAM`). The reference is correct, only the literal characters need fixing. Do NOT use CORRECTED for booleans that came back with the wrong answer, inferred/computed values that came back wrong, or any case where IXP picked the wrong source on the page — those are NOT CONFIRMED.
   - **MISSING** — IXP predicted **no value** (empty `FormattedValue`) AND the field is genuinely absent from the document. Both conditions must hold. If IXP predicted a value but the field isn't actually in the document, that's NOT CONFIRMED, not MISSING — Critical Rule 12 forbids overriding a non-empty prediction with "missing".
   - **NOT CONFIRMED** — the prediction is wrong for any reason other than OCR mangling. Covers: wrong literal value on the right field, wrong-source extraction, hallucinated value, boolean came back with the wrong answer, inferred/computed value came back wrong, predicted a value the document doesn't contain. Left unannotated. Do NOT try to "fix" these with `--corrections` — `--corrections` is OCR-only (see Critical Rule 8). Improve the prompt instead.
3. **Report your verdict for every field.** Print a table per document:

```text
Document: <document-id>

Field                    | Verdict       | Reason
-------------------------|---------------|-----------------------------------------------
Invoice Number           | CORRECTED     | OCR mangled "MSIÓÓÓ601020/" → "MSI0601020", top-right of page 1
Invoice Date             | CONFIRMED     | Predicted "2018-02-28" matches document
Vendor Address           | NOT CONFIRMED | Predicted "123 Main St" but actual is "456 Oak Ave", top-left of page 1
Has Signature            | NOT CONFIRMED | Predicted "false" but signature visible bottom-right (boolean came back wrong — NOT CORRECTED)
Total After Tax          | NOT CONFIRMED | Predicted "$1100.00" but Subtotal+Tax = "$1210.00" (inferred value wrong — NOT CORRECTED)
Terms of Payment         | MISSING       | IXP predicted no value AND field not visible in document
Discount                 | MISSING       | IXP predicted no value AND no discount section on the page
Line Items > Description | CONFIRMED     | Predicted "Widget A" matches row 1 in the table
```

**Repeatable field groups produce one extraction per row.** Count them in `get-predictions` — `Line Items` on a multi-line invoice has N entries under that label, indexed 0..N-1. When validation differs across rows, give per-occurrence verdicts:

```text
Line Items > Description (occurrence 0) | CONFIRMED     | "Widget A" matches line 1
Line Items > Description (occurrence 1) | CONFIRMED     | "Widget B" matches line 2
Line Items > Description (occurrence 3) | NOT CONFIRMED | Predicted "Widget D" but line 4 shows "Widget Z"
```

For **CORRECTED** fields: state the mangled predicted value, the corrected value, and where it appears. The mistake must be at the character level — same field, same location, garbled bytes.
For **MISSING** fields: state that the prediction was empty AND describe how you verified the field is absent (e.g., "no payment-terms section anywhere in the document").
For **NOT CONFIRMED** fields: state the predicted value, the actual value (if visible) and location. Includes any non-OCR mistake — wrong source, wrong boolean, wrong inferred value, hallucination, value the document doesn't contain. **Do NOT use `--corrections` to fix these** — improve the field's prompt instructions instead.

4. **Build two lists from the table:**
   - **Submit field IDs** — all CONFIRMED + CORRECTED + MISSING fields (one combined list — the CLI applies the right semantic per field based on IXP's prediction)
   - **Corrections JSON** — only CORRECTED fields: `[{"field_id":"...","value":"corrected text"}]`

### 2d. Confirm and correct

Submit confirmed, corrected, and missing fields for this document — all in one `confirm` call.

**If there are corrections:**

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<all_submitted_ids>" \
  --corrections '[{"field_id":"<id>","value":"<corrected_value>"}]' \
  --output json
```

The `--fields` list includes CONFIRMED, CORRECTED, and MISSING field IDs together — the CLI writes the right annotation per field based on IXP's prediction (content → confirm, content with override → correct, empty → missing marker). The `--corrections` JSON overrides the predicted value for corrected fields while keeping their document references (bounding boxes).

**If there are no corrections (all approved fields are exact matches):**

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<field_id_1>,<field_id_2>,<field_id_3>" --output json
```

If ALL predicted fields for a document are correct with no corrections needed, you can omit `--fields` to confirm everything:

```bash
uip ixp labellings confirm <project-name> <document-id> --output json
```

**If there are missing fields**, include their IDs in the same `--fields` list as the CONFIRMED and CORRECTED IDs. The `confirm` command applies one uniform rule per listed field: if IXP predicted content, the content is confirmed; if IXP predicted nothing, a missing marker is written. No separate call needed.

```bash
uip ixp labellings confirm <project-name> <document-id> \
  --fields "<confirmed_id>,<corrected_id>,<missing_id_1>,<missing_id_2>" \
  --corrections '[{"field_id":"<corrected_id>","value":"<corrected_value>"}]' \
  --output json
```

**Only include a field in the `--fields` list for the MISSING case when IXP itself predicted nothing for it** — see Critical Rule 12. If IXP predicted a wrong value, omit the field entirely (don't list it).

Use `labellings mark-missing` only as a fallback when `confirm --fields` is a no-op for a field you expected it to handle — typically a field with a prior annotation that the current prediction no longer includes (e.g., model behavior changed after a retrain). Verify by re-running `labellings get-predictions <project-name> <document-id>` and checking whether the field appears in the Fields[] array: if yes, `confirm --fields` is the right tool; if no, `mark-missing` reaches the stale annotation that `confirm` can't.

**Per-occurrence confirm for repeatable groups.** When a repeatable group's verdicts differ across occurrences (some lines correct, some not), `confirm --fields f001` is the wrong shape — it confirms `f001` in **every** occurrence, including the wrong ones. Target each correct occurrence by index:

```bash
# All predicted fields in occurrence 0:
uip ixp labellings confirm <project-name> <document-id> \
  --field-group "Line Items" --occurrence 0 --output json

# Just Quantity in occurrence 2:
uip ixp labellings confirm <project-name> <document-id> \
  --field-group "Line Items" --occurrence 2 --fields f005000000000001 --output json
```

Occurrences not targeted carry forward whatever annotation they already had (so wrong predictions in untouched occurrences stay unannotated). For batching many occurrences in one call, use `--updates '[…]'` — see [CLI Reference § Labellings](cli-reference.md#labellings). See Critical Rule 13.

### 2e. Move to the next document

Repeat steps 2a–2d for all documents in the list.

### Removing a document from the project

If a document is unusable (wrong document type, corrupted, duplicate), delete it instead of confirming or skipping:

```bash
uip ixp documents delete <project-name> <document-id> --output json
```

`<document-id>` is the `DocumentId` from `documents list` (e.g., `3453547f3538febd.1fc885607f2aac621f8f2d3ef1847f22`). Pass it whole. Do NOT pass the AttachmentRef or the Filename.

**Finding the DocumentId:**

| You have | How to get the DocumentId |
|----------|---------------------------|
| Filename (e.g., `invoice-001.pdf`) | `uip ixp documents list <project-name> --output json --output-filter "[?Filename=='invoice-001.pdf'].DocumentId \| [0]" --output plain` |
| A distinctive predicted field value (e.g., Invoice Number `MSI0601020`) | Run `uip ixp labellings get-predictions <project-name> --output json`, find the document whose `Labels[].Fields[].FormattedValue` matches, take its `DocumentId` |
| Nothing — need to find by content | `uip ixp documents list <project-name> --output json`, then `documents download` candidates and read with the Read tool |

`documents list` returns `Filename` alongside `DocumentId` (the original upload filename, or `null` if none was sent at upload time). When filenames aren't unique within the project, the JMESPath filter returns multiple IDs — review them with `documents download` before deleting.

Deletion is irreversible and triggers a model retrain. Do NOT use deletion to skip documents you simply don't want to label — leave those unconfirmed instead.

## Step 3 — Summary

After processing all documents, track progress and errors:

- Do NOT stop on the first error — continue with remaining documents
- If a download or text fetch fails, skip the document and note the failure
- If confirmation fails, log the error and UID, then continue

At the end, report a full summary:

```text
Labelling complete.

Documents: N processed, M confirmed, K skipped (no predictions)
Fields: X confirmed, Y corrected, W marked missing, Z not confirmed

OCR Corrections Applied:
  Doc <uid-1>: Invoice Number "MSIÓÓÓ601020/" → "MSI0601020"
  Doc <uid-1>: Vendor Name "INGRAM NTCRO INC" → "INGRAM MICRO INC"
  Doc <uid-3>: Bill-To Address "123 Mam St" → "123 Main St"

Marked Missing (IXP predicted empty AND field absent from document):
  Doc <uid-2>: Terms of Payment
  Doc <uid-4>: Discount

Not Confirmed (skipped):
  Doc <uid-3>: Total Amount — predicted "500.00" but actual is "5000.00" (bottom-right, page 1)
  Doc <uid-5>: Vendor Address — predicted "123 Main St" but actual is "456 Oak Ave"
```
