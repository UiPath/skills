<!--skill-flavor:extract-brownfield:start-->
In Studio Web the flow is already here: the open solution is the workspace, and the target `.flow` is the open file ([Project layout](../SKILL.md#project-layout)). Every command in this guide runs against that file directly, and the canvas reloads the open file after a write.
<!--skill-flavor:extract-brownfield:end-->

<!--skill-flavor:extract-eval-files-path:start-->
Sample documents a user uploaded through Studio Web live in the open solution, under the flow project:

```
/solution/<Project>/evals/<dataset-id>/eval-files/
```
<!--skill-flavor:extract-eval-files-path:end-->

<!--skill-flavor:extract-collect-samples:start-->
In Studio Web the taxonomy is set up as a guided conversation. Each step is one chat component: the samples, the clarifications, the draft, then changes on request. Nothing reaches the node until the user approves the write that carries it.

1. **Collect the use case and the samples.** Check for documents uploaded to the node; they need decoding first ([The documents uploaded to the node](#the-documents-uploaded-to-the-node)). With none, your first question is a single `AskUser` call holding one `media` question with `attachable: true` and `optional: false`, so the user gets a file drop zone and a text box in one step. Ask for the extraction use case and the samples together, for example: "What's your extraction use case? For example invoice processing, PO matching or spend analysis. Add 3–5 samples; one is enough to start." The text box carries the use case: what the documents are, which data they need from them, and what happens to it next. Do not ask for the document type as a separate choice question before it; the samples and the use case answer that. Files the user drops arrive as attachments under `/attachments/`; read them from there, even when the user listed the fields. With no file supplied, design from the stated use case and fields and say so in the report.
2. **Read them.** One full `Read` per document returns text and image for both digital and scanned files, so no PDF tooling is needed. Then say in one or two sentences what you found and what you will build: "These are 3 invoices from different vendors, each with a line-item table. From what you described, I'll set the fields up for invoice processing." With no use case in the note, take the closest match to the samples and say so: "You didn't describe a use case, so I'll go with invoice processing. Tell me any time if it's something else."
3. **Clarify only what the samples can't settle.** Ask about a field's instructions only where the documents disagree or leave the reading open: a numeric date such as 04/05/2026 that reads either way, a value printed without its usual label ("Your ref: PO-4471" where the other samples say "PO number"), the same label printed several times ("Total" on each line, above the tax and at the foot). Never ask whether a field is required or optional, and never ask what a sample already answers. With nothing to clarify, go straight to the design.
   Ask in one `AskUser` call: one `text` question per ambiguity, at most three, each `multiSelect: false`.
   - `header` is the field name, for example `invoice_date`.
   - `question` is the short ask followed by its evidence: "How should I read a date like 04/05/2026? invoice_Initech_0098.pdf writes 04/05/2026; your other samples write 5 Apr 2026."
   - Each option's `label` is the reading itself ("4 May 2026 — day first") and its `description` the evidence for it ("Your vendors bill from the UK and EU"). Put the reading the evidence favours first, its label suffixed with "(Recommended)".
   - Set `optional: true` when the recommended reading is a safe default; a skipped question takes it.
   Fold each answer into that field's instructions as a plain rule: "Numeric dates are day first (DD/MM/YYYY): read 04/05/2026 as 4 May 2026."
4. **Design the taxonomy** against the rules below and write it to a JSON file.
5. **Propose it with the `ProposeTaxonomyChange` host tool**, as its own call: `ProxyTool` with `toolName` `ProposeTaxonomyChange`, `method` `execute` and `params` `{ "nodeId": "<id>", "mode": "create", "schema": <the taxonomy JSON> }`. `schema` is that taxonomy as a JSON object with top-level `prompt` and `outputSchema`, the document `nodes schema set` takes: pass the object itself, never a file path or the `schema get` output envelope. Keep your copy of it, since every later change builds on it. The tool's card is the user's Apply / Dismiss. Applying it opens the node's Definition with the taxonomy as unsaved changes, which the user saves or discards there. In Studio Web never write a taxonomy with `uip maestro flow nodes schema set` or by editing the `.flow`.
6. **Fix what it rejects.** A failed call says why the Definition could not take the taxonomy; correct that and propose again. Do not run `flow validate`: nothing is saved until the user saves.
7. **Report the draft** in two or three sentences: "Your draft is ready: 28 fields for invoice processing. It's open on the right, and nothing is saved until you Save." Say they can keep talking to change it, then end with a `followups` block: three changes grounded in these samples, in the user's voice, and the next step last.

   ```followups
   - Our ERP needs addresses split into parts
   - Some fields we need are missing
   - Which fields can I drop to cut noise?
   - The fields look right — set up the model
   ```

   Ground the three in what you saw: split an address the samples print in one layout, add a value the samples carry that the taxonomy misses, drop a field that is empty on every sample, or sharpen a field whose label repeats.

### Changing the taxonomy in chat

A change the user asks for, from a pill or in their own words, comes back as a proposal first. Build it on the last taxonomy you proposed in this chat: an applied draft is not saved until the user saves, so `nodes schema get` may still return the older one. Read the node with `nodes schema get` only when you have proposed nothing yet. Say in one short line what the change does, for example "Here's that change. Nothing is applied until you say so." Then call `ProposeTaxonomyChange` as its own call with `mode` `"edit"`, the complete changed taxonomy as `schema`, and every field-level change in `changes`: `{ "kind": "rename", "field": "supplier_name", "group": "Vendor", "before": "vendor_name", "after": "supplier_name" }`; `kind` is `add`, `remove`, `rename` or `update` (an instruction or type change, with the old and new text as `before` and `after`). The card shows those changes as a diff with Apply / Dismiss; do not list them again in your text.

After a Dismiss, say "Left as it is. Tell me what you had in mind instead." After an Apply, say in one line that it is drafted in the Definition and saved only when they Save, then end with the same kind of `followups` block: further changes grounded in the samples, then `The fields look right — set up the model`.

### Setting up the model

Start this only when the user asks for it: the `The fields look right — set up the model` pill or their own words. In this host it replaces the model-setting refusals in [extract-document-node.md](extract-document-node.md#unsupported-capabilities).

1. **Check what is in the documents.** One `AskUser` call with the `intro` "The model that fits best depends on what's in your documents. Here's what I found — check it before I recommend a setup." and two questions:
   - `header` "Content", `multiSelect: true`, question "What's in your documents? I found what's ticked in all 3 samples — untick anything that's wrong, or tick what I missed." (the real sample count). Options: `Line-item tables`, `Nested or multi-page tables`, `Forms and full-page layouts`, `Scans, skew or blur`, `Handwriting, signatures or stamps`, `Arabic, Chinese, Cyrillic and similar`. Set `initiallySelected: true` and the `description` "Found in your samples" on the ones you saw.
   - `header` "Length", single choice, question "How long is a typical document? Yours are 1–2 pages each." (the page counts you saw). Options: `Under 50 pages`, `50–500 pages`, `500+ pages`, `Mixed / not sure`. Give the one the samples show the `description` "Found in your samples".
2. **Recommend a setup from the answers** with these rules:

   | Setting | Rule | Stored in `inputs.modelConfig` |
   |---|---|---|
   | Extraction strategy | 500+ pages → Advanced; otherwise Standard | `execution_mode`: `standard` / `advanced_harness` |
   | Extraction model | nested or multi-page tables, scans, or handwriting → Gemini 2.5 Pro; otherwise Gemini 2.5 Flash | `model_version`: `gemini_2_5_flash` / `gemini_2_5_pro` |
   | Language support | non-Latin script → Extended languages; otherwise Latin-based languages | `language_support`: `latin` / `extended` |
   | Layout parsing | forms, scans, or handwriting → Full; line-item or nested tables → Tables & forms; otherwise None | `layout_parsing`: `none` / `tables_forms` / `full` |
   | Attribution | Standard strategy with nothing but line-item tables ticked → Rules-based; otherwise Model-based | `attribution_method`: `table_heuristic` / `word_ids` |

   `input_config` mirrors layout parsing and language, and changes with them: `none` for None, `table_model` for Tables & forms, `azure_table_formatting` for Full, `azure_markdown` for Full with Extended languages.

   Say in one line that this is the setup you recommend and that applying it fills in Model configuration in the definition, with nothing saved until the user saves. Do not list the settings in text: the card shows them.
3. **Propose it with the `ProposeModelSetup` host tool**, as its own call: `ProxyTool` with `toolName` `ProposeModelSetup`, `method` `execute` and `params` `{ "nodeId": "<id>", "settings": [ { "key": "execution_mode", "value": "standard", "reason": "One pass fits 28 fields, under 50 pages" }, … ] }`, one entry per setting in the order execution_mode, model_version, language_support, layout_parsing, attribution_method, each with a short reason grounded in the documents. Do not send `input_config`; Flow derives it. The card shows the setup with Apply to definition / Dismiss; applying it fills Model configuration in the Definition as unsaved changes that the user saves or discards there. A setting the user changes in words ("use Gemini 2.5 Pro") goes into a new proposal. Never edit `inputs.modelConfig` or `inputs.schemaDocument` in the `.flow`. With Full layout parsing, the parsing model comes from the tenant, so say the user picks it under Model configuration → Layout parsing.
4. **Report and point to an evaluation.** Applied: "Done — it's filled in under Model configuration in the definition. Next, try it on your documents." Rejected: "I've left Model configuration as it is. Ask me to set up the model any time." End with a `followups` block, next step first:

   ```followups
   - How do I try this on my documents?
   - Use Gemini 2.5 Pro instead
   ```

   Asked how to try it, say: upload the samples in the node's Dataset tab, then choose Run evaluation. Uploading documents and running evaluations stay the user's steps.
<!--skill-flavor:extract-collect-samples:end-->
