# Workflows Guide

End-to-end recipes. Run every step yourself; do not hand steps to the user. All commands: [CLI Reference](cli-reference.md). Result shapes: [Results Guide](results-guide.md).

Before step 1 of any recipe, decide the folder once (SKILL.md Critical Rule 5): none unless the user named one or the model lives in one. Keep it on every folder-scoped command that follows.

## 1. Extract one document

```bash
uip documents uploads create "<FILE_PATH>" --output json
uip documents models list --capability extract --output json
uip documents extract --model "<MODEL_ID>" --document-id "<DOCUMENT_ID>" --wait --timeout 100 --output json
```

1. **Upload.** Keep `Data.documentId`. Skip this step when the user already gave a `documentId` or `attachmentId` (`--attachment-id` instead of `--document-id`).
2. **Pick the model.** Match the document type to a model's `name`, then confirm its `outputSchema` holds the fields the user wants. Several candidates → pick the one whose schema covers the requested fields; still ambiguous → ask the user, listing `name` + `modelId`. None fits → stop and hand off to `uipath-ixp` (SKILL.md Critical Rule 4).
3. **Extract.** Check `Result` and `Data.status` ([Results Guide § Run envelope](results-guide.md#run-envelope)). `TimeoutError` → `uip documents runs get <run-id> --wait --timeout 100 --output json`, repeated while it keeps timing out (cap: 10 tries, then report the `runId` and stop).
4. **Report** per [Results Guide § Reporting](results-guide.md#reporting-extracted-values). Keep `Data.digitization.runId` for any further call on this document.

**Same document, another model:** `extract --model "<OTHER_MODEL_ID>" --document-id "<DOCUMENT_ID>"` — no upload; OCR is reused when the model's digitization settings match (same `Data.digitization.runId`).

## 2. Digitize a document

Use when the user wants the content itself (markdown, text, words with boxes) or a specific OCR/layout engine. For fields or a document type, go straight to extract or classify — they digitize on their own.

```bash
uip documents digitizers list --output json
uip documents digitize --document-id "<DOCUMENT_ID>" [--page-range <range>] [--ocr-engine <engine>] [--apply-on-pdf <auto|always|never>] [--layout-engine uipath] --wait --timeout 100 --output json
```

1. **Engines (optional).** The default (`auto` OCR, which picks `uipath` or `uipath_extended` per page by its alphabet; `applyOnPdf: auto`; no layout engine) suits most documents. Pin an OCR `engine` from `digitizers list` only when the user asks or a page's script is misread. `--apply-on-pdf always` when a PDF's text layer is wrong. `--layout-engine uipath` for HTML tables with spans, forms and layout reading order (not with `--apply-on-pdf never`: a layout engine runs on OCR output).
2. **Digitize.** `Data.result.markdown` is the whole document, each page opening with `<!-- page: N -->`; `Data.result.pages[]` lists each page's `number` (from 1 in the order digitized; a `--page-range` digitization counts its own pages, the file's page numbers are not reported), `width`, `height`.
3. **Large documents.** Markdown grows with page count. Read only what you need: `--output-filter "result.pageCount"` first, then one page at a time with `uip documents pages get <n> --run-id "<RUN_ID>" --format text --output json` (text is the only page format a digitize run serves today; `dom` and `image` answer `not-implemented`).
4. **Reuse.** The same document, settings and `--page-range` digitized again answer this same run (not served yet: today every digitize call starts a new digitization). Extract and classify reuse it only when their model's settings equal this call's; otherwise they digitize again with the model's settings. A digitization cannot be passed to them.

## 3. Classify a packet, then extract each segment

```bash
uip documents uploads create "<FILE_PATH>" --output json
uip documents models list --output json
uip documents classify --model "<CLASSIFY_MODEL_ID>" --document-id "<DOCUMENT_ID>" --split --wait --timeout 100 --output json
uip documents extract --model "<EXTRACT_MODEL_ID>" --document-id "<DOCUMENT_ID>" --page-range "<PAGE_RANGE>" --wait --timeout 100 --output json
```

1. **Upload** the packet once.
2. **One `models list`** (no `--capability`) gives both the classifier (`capability: classify`, its `classes`) and the extract models.
3. **Classify with `--split`.** `Data.result.segments[]` = `{ pageRange, class, confidence }`; keep `Data.digitization.runId`.
4. **Map each class to an extract model** from the same listing, by name and schema. A class with no matching model → report that segment as "classified, no extractor", do not extract it.
5. **Extract per segment**: the same `--document-id`, `--page-range` = the segment's `pageRange` verbatim. When the extract model's digitization settings match the classifier's, the run reuses the packet's digitization (same `digitization.runId`, no new OCR) and its attribution pages count within the packet. Independent segments can run in parallel shell calls.
6. **Segments with `class: null`** (or below a threshold the user gave) → list them for human review with their `pageRange` and `confidence`; never extract them with a guessed model (SKILL.md Critical Rule 12).
7. **Report** per segment: page range, class, confidence, then its extracted values.

## 4. Verify a value on its page

When the user asks where a value came from, or a value looks wrong:

```bash
uip documents pages get <PAGE> --run-id "<DIGITIZATION_RUN_ID>" --format image --output-file "<PNG_PATH>" --output json
```

1. Take `attribution[].page` and `attribution[].box` from the field; `<DIGITIZATION_RUN_ID>` is the extract run's `digitization.runId` (not its `runId`).
2. Save the page, then view the PNG (Read tool on `Data.path`). `box` is `{ x, y, width, height }` in that PNG's pixels, origin top left. `<PAGE>` is `attribution[].page` as given: it counts within the digitization, which for a packet segment is the packet.
3. Compare the region with `attribution[].text` (the OCR text) and `value` (the normalised value: `$3,180.50` → `3180.5` is the same amount).
4. Report what the page shows. If the value is wrong, say so — do not replace it with your own reading (SKILL.md Critical Rule 10). Repeated wrong values on a fine-tuned model → suggest improving it with `uipath-ixp`.

Words with boxes (for exact text matching) come from `--format dom`.

## 5. Recover a lost start

The start call printed nothing (dropped connection, killed shell) and you do not have a `runId`:

1. If you sent `--idempotency-key <KEY>`: re-send the identical command with the same key — it returns the run already started.
2. If you did not: re-sending starts a second run (OCR is still reused, the model run is charged again). Tell the user before doing it.

Prevention: for documents that may take long, always pass `--idempotency-key` (e.g. `<DOCUMENT_ID>-<MODEL_ID>`).
