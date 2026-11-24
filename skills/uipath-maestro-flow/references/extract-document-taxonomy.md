# Extract document taxonomy

*Commands: the SDK loop: `uip maestro flow decompile`, `check`, then `merge` (existing flow) or `compile` (new flow), and `validate`.*

An Extract document node (`uipath.ixp.extract-document-builder`) extracts from the inline taxonomy at `inputs.schemaDocument` in the `.flow`: groups, fields, field types, and model instructions. In source it is the `schema` of the node's `dynamicExtract()` step. Read it in the decompiled source, edit it there, and write it back:

```bash
uip maestro flow decompile <Name>.flow -o .flow-sdk/<Name>.flow.ts --no-pipeline   # prints each step's schema, ids included
# edit the step's schema in .flow-sdk/<Name>.flow.ts
uip maestro flow check .flow-sdk/<Name>.flow.ts --source --baseline <Name>.flow     # EXTRACT_TAXONOMY_* codes
uip maestro flow merge .flow-sdk/<Name>.flow.ts --original <Name>.flow
uip maestro flow validate <Name>.flow --output json
```

Run them from the project folder, with the cleanup step before `decompile` that [SKILL.md, Editing an existing flow](../SKILL.md#editing-an-existing-flow) gives. Everything here is offline; no login.

This guide assumes the node exists. For adding it, wiring `fileRef`, and when it applies over a published IXP model, see [extract-document-node.md](extract-document-node.md).

## Starting from a flow in Studio Web

<!--skill-flavor:extract-brownfield:start-->
For a Studio Web flow, work on a local copy: download, edit, and upload it. Identify it by solution id or the Studio Web URL's `solutionId` query parameter. If neither was provided, ask for either; if Studio Web was not mentioned and no local `.flow` exists, ask whether the flow is in Studio Web. **When in doubt, ask, rather than working it out.** Nothing lists Studio Web: `uip solution` downloads, uploads, and deletes only by id. Search endpoints and stored CLI credentials are not ways around asking; say either a link or an id works, and continue once it arrives.

Run:

```bash
uip login status --output json
uip solution download <solution-id>
```

The download creates a directory named for the id containing the flow project. Run this guide's loop in that project folder, against its `.flow`. If login expired, report it and ask the user to log in with `uip login`.

Push the finished taxonomy with `uip solution upload` from the downloaded solution root and tell the user where to find the updated flow.
<!--skill-flavor:extract-brownfield:end-->

### The documents uploaded to the node

<!--skill-flavor:extract-eval-files-path:start-->
Studio Web sample documents are downloaded under:

```
<Project>/evals/<dataset-id>/eval-files/
```
<!--skill-flavor:extract-eval-files-path:end-->

List `evals/` rather than guessing its GUID dataset directory. Files retain their extensions but contain:

```
BINARY_FILE:application/pdf:2073
---BASE64---
JVBERi0xLjMKJe…
```

Drop the first two lines and decode before reading:

```bash
mkdir -p decoded
for f in <Project>/evals/*/eval-files/*; do
  tail -n +3 "$f" | base64 -d > "decoded/$(basename "$f")"
done
```

Decode per dataset directory when multiple datasets contain duplicate filenames, then read the decoded copies.

## At a glance

Read sample documents, design and write the taxonomy, fix rejections, and validate. The step's `schema` is the whole document, not a patch ([What compile and merge do for you](#what-compile-and-merge-do-for-you)):

```ts
.step('extractDocument1', dynamicExtract({
  fileRef: input('invoice'),
  schema: { prompt: '…', outputSchema: { type: 'object', properties: { /* groups */ }, $defs: { /* field types */ } } },
}), { label: 'Extract Invoice' })
```

Read documents first: relying only on the user's sentence misses actual fields and invents absent ones.

## The loop

1. **Collect samples.** Check and decode uploaded documents ([The documents uploaded to the node](#the-documents-uploaded-to-the-node)). Without samples, ask for representative documents even if fields were listed; if none are supplied, design from the stated fields and say so in the report.
2. **Read them.** Perform one full `Read` per decoded document; it returns text and image for digital and scanned files, so PDF tooling is unnecessary.
3. **Design** the taxonomy under the rules below.
4. **Write it** into the step's `schema` in the source: the complete document, every existing group, field, id, and field type included ([Editing a taxonomy that already exists](#editing-a-taxonomy-that-already-exists)). A taxonomy the user supplied as a file is pasted in as the value of `schema`.
5. **Check, and fix rejections.** Run `check`; fix each `EXTRACT_TAXONOMY_*` error at the path it names, then check again ([When it refuses](#when-it-refuses)).
6. **Write the `.flow`:** `merge` (existing flow) or `compile` (new flow), as [SKILL.md](../SKILL.md#lifecycle) says. Then run `uip maestro flow validate <file> --output json`; it must return `Valid`.
7. **Report** what was created and the processor file: compile and merge print `wrote resources/solution_folder/idpProcessor/extraction/<Label>.json (IDP processor)` when they create or update it. The schema is stored in that file too; keep it with the `.flow`. Taking the node live is the user's decision.

## The document

The written document has `prompt` (overall extraction instructions) and `outputSchema` (an OpenAI structured-outputs JSON Schema whose top-level `properties` are groups and `$defs` are field types). `config` is the node's copy of its own model settings (`inputs.modelConfig`): keep the one decompile printed for this step unchanged, and never copy another node's. A document with no `config` gets one built from the step's model settings at compile.

Here's a worked invoice taxonomy example, which illustrates the format specification:

```json
{
  "prompt": "Extract the header of the invoice and every billed line. Values are on the page; do not compute totals yourself.",
  "outputSchema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["Invoice", "Invoice > Line Items"],
    "properties": {
      "Invoice": {
        "type": ["object", "null"],
        "description": "The invoice header, which appears once per document.",
        "additionalProperties": false,
        "required": ["Invoice Number", "Invoice Date", "Total"],
        "properties": {
          "Invoice Number": {
            "$ref": "#/$defs/ft-exact-text",
            "description": "The invoice number as printed, without a leading # or the word 'Invoice'."
          },
          "Invoice Date": {
            "$ref": "#/$defs/ft-date",
            "description": "The date the invoice was issued, not the due date and not the delivery date."
          },
          "Total": {
            "$ref": "#/$defs/ft-monetary-quantity",
            "description": "The amount payable including tax, usually the last line of the summary block."
          }
        }
      },
      "Invoice > Line Items": {
        "type": "array",
        "description": "One entry per billed line in the table of charges.",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": ["Description", "Quantity", "Amount"],
          "properties": {
            "Description": {
              "$ref": "#/$defs/ft-inferred-text",
              "description": "What was billed, from the line's description column."
            },
            "Quantity": {
              "$ref": "#/$defs/ft-number",
              "description": "How many units the line bills for. Leave empty where the line has no quantity."
            },
            "Amount": {
              "$ref": "#/$defs/ft-monetary-quantity",
              "description": "The line total, not the unit price."
            }
          }
        }
      }
    },
    "$defs": {
      "ft-exact-text": { "title": "Exact Text", "type": ["string", "null"], "format": "verbatim" },
      "ft-inferred-text": { "title": "Inferred Text", "type": ["string", "null"] },
      "ft-date": { "title": "Date", "type": ["string", "null"], "format": "date" },
      "ft-number": { "title": "Number", "type": ["string", "null"], "format": "decimal" },
      "ft-monetary-quantity": { "title": "Monetary Quantity", "type": ["string", "null"], "format": "monetary" },
      "ft-boolean": { "title": "Boolean", "type": ["boolean", "null"] }
    }
  }
}
```

### Field groups

Each `outputSchema.properties` entry is a group. A single-occurrence group is `"type": ["object", "null"]` with fields directly under `properties`; a repeating group is `"type": "array"` with fields under `items.properties`. Model repeating tables as arrays.

Nesting is by property name: `Invoice > Line Items` is a child of `Invoice`; both remain top-level properties, separated by space-greater-than-space. Compile derives and stores the parent back-reference, so do not write it. A top-level group names no parent. Start with one document-type group and put each table or section beneath it.

### Field types

Fields use `$ref` entries in `outputSchema.$defs`; the node initially provides:

| Use it for | `$defs` key | Returns |
| --- | --- | --- |
| Exact printed value | `ft-exact-text` | verbatim text |
| Derived, summarized, ambiguous, or plain text | `ft-inferred-text` | text |
| Date | `ft-date` | calendar date |
| Non-money count or quantity | `ft-number` | decimal, preserving printed scale |
| Currency amount | `ft-monetary-quantity` | amount with currency |
| Yes/no | `ft-boolean` | true or false |

Carry the whole `$defs` block through unchanged. The step's `schema` replaces the document; omitting an entry removes that type, and every `$ref` must resolve within the same block. Prefer a stricter type only when certain; otherwise use `ft-inferred-text`.

A Choice is the only type you add; add one only when its complete set of allowed values is small, fixed, and evident from documents or user instructions — a status column, not a description column. Use an `ft-` key with a URL-safe suffix (letters, digits, `.`, `_` or `-` only, so the `$ref` naming it needs no escaping) and give every entry a `title`, for example:

```json
"ft-payment-status": { "title": "Payment Status", "type": ["string", "null"], "enum": ["Paid", "Unpaid", "Partially paid"] }
```

Never infer enum values from what appears in the samples: a value they did not show still extracts, and an enum that omits it loses it. For large or open sets, use `ft-inferred-text` and list likely values in field instructions.

### Names

Group and field property keys, and field-type `title` values, must be **128 characters or fewer**, counting spaces. The entire nested key, including ` > `, counts. Names must not be empty, begin with punctuation, a symbol, or a space, and must be unique among siblings. Prefer short wording from the document.

### Instructions

The document `prompt`, every group `description`, and every field `description` must be **4096 characters or fewer**. Write all three: types describe value shape; instructions identify the correct value on the page. `"The date the invoice was issued, not the due date"` earns its place; `"The invoice date"` repeats the field name and tells the model nothing. User instructions for a field outrank document inference; record them even if every sample contradicts them (e.g. a reference number said to exclude a branch prefix).

### Size

These limits are not enforced by `check` but improve extraction:

- Keep groups to a readable number of fields; 25 is a reasonable ceiling (the IXP taxonomy quota, which this node does not share, caps groups at 25).
- Keep distinct field types few; each distinct Choice is another type.
- A long Choice is usually a text field in disguise.

## What compile and merge do for you

- **Stable ids:** Groups and fields carry `x-uipath-field-group-id` and `x-uipath-field-id`, used by annotations, evaluator settings, and taxonomy history. Compile keeps an id the source carries; for an entry with none it takes the id the overwritten `.flow` has for the same name (a group by its key, a field by its name within that group), else mints one; merge writes those ids into an existing flow with SDK 6.124.17 or later. Decompile prints every id, so a decompiled source already has them. An id belongs to one entry: never copy one onto a second group or field.
- **Model settings:** A document with no `config` gets one built from `inputs.modelConfig`.
- **Validation:** `check` refuses a non-schema or limit violation before anything is written ([When it refuses](#when-it-refuses)). Compile does not run `check`; run it first.
- **The processor:** Compile and merge give the node its processor key and, inside a solution, write the processor's resource file with this taxonomy ([extract-document-node.md](extract-document-node.md#making-it-actually-extract)).
- **Draft protection:** When someone left an editing session in Studio Web that was not valid yet, the node's schema carries that draft (`x-uipath-schema-editor-draft`, with the editor's problems in `x-uipath-schema-editor-issues`), and decompile prints both in the step's `schema`. Check for the draft yourself after every decompile, whatever the SDK version: while that key is in the step's `schema`, do not edit the schema and do not merge a change to it until the user, in this conversation, says what to do; report the draft and its issue messages first. Merge's own refusal (SDK 6.124.17 or later, the merge floor: it writes nothing) is only the backstop. Deleting the `x-uipath-schema-editor-draft` key from the source throws the draft away; do it only when the user asked in this conversation. Headless or CI: leave the node unchanged, report the draft and the editor's issue messages, and stop; the request is not done. Do not repair a missing processor either: that writes `inputs.processorKey` into the node. Report it instead. Never hand-edit `inputs.schemaDocument` to bypass this.

## Editing a taxonomy that already exists

Decompile first, then edit the step's `schema` in place and keep the complete document. Preserve every existing id, including through renames: a renamed entry keeps its `x-uipath-field-id` (or `x-uipath-field-group-id`) on the new name, because matching by name would mint a new id and detach the annotations and evaluator settings stored against the old one. Preserve every existing group and field's `description`, type, and id exactly as decompiled; add information only in new groups, fields, or `prompt`. Keep all groups, `$defs`, and the overall prompt, because the `schema` replaces rather than patches. Never write from scratch over existing content; if the user wants a fresh start, first say what will be lost.

To copy one node's taxonomy to another, give the target step the source step's `prompt` and `outputSchema`, and keep the target's own `config`, `fileRef`, label and processor: the target gets a processor of its own, never the source's key.

## Reading the output

The decompiled step's `schema` is the stored document with original key casing, so it can be edited in place. A `x-uipath-schema-editor-draft` key in it is an unsaved Studio Web edit; `x-uipath-schema-editor-issues` says what the editor found wrong with that draft.

Compile prints what it did with the ids, one line per step that has a taxonomy:

```text
compile: "extract" taxonomy ids: 1 group and 2 field id(s) kept, 0 group and 1 field id(s) minted
```

Merge compiles too, and the merged `.flow` carries the result. On an edit, compare the merged node's ids with the decompiled ones before reporting success. A minted id where a rename was intended means the id was dropped: its annotations no longer point at the field. Put the old id back on the renamed entry in the source, and merge again.

## When it refuses

`check` reports each content problem before compile, one code per rule, with the path and the problem in the message:

| Code | Rule it enforces |
| --- | --- |
| `EXTRACT_TAXONOMY_NESTING` | nesting by name: `A > B` needs a group `A`, and a top-level group names no parent ([Field groups](#field-groups)). If an existing group was clearly meant as parent, rename one key to match; never add an empty parent. |
| `EXTRACT_TAXONOMY_REF` | every field names a field type, and every `$ref` resolves inside `$defs` ([Field types](#field-types)) |
| `EXTRACT_TAXONOMY_LIMIT` | names within 128 characters, a nested group's whole composed key included; instructions within 4096 ([Names](#names), [Instructions](#instructions)) |
| `EXTRACT_TAXONOMY_DUPLICATE_ID` | no id on two groups or two fields ([What compile and merge do for you](#what-compile-and-merge-do-for-you)) |
| `EXTRACT_TAXONOMY_FIELD_TYPE` | a `$defs` key needs no escaping in a `$ref`; every field type has a title ([Field types](#field-types)) |
| `EXTRACT_TAXONOMY_STRUCTURE` | every group, field and container is the shape the Schema Editor reads |
| `EXTRACT_TAXONOMY_BARE`, `EXTRACT_TAXONOMY_LEGACY` (warnings) | a bare JSON Schema, or the superseded `{taxonomy, fieldTypes}` form, in place of `{ prompt, outputSchema }`; the processor gets no fields from either, so treat either as an error |

No code checks sibling-name uniqueness ([Names](#names)): each name is a property key, so JSON already makes siblings unique.

`merge` refuses, writing nothing, when the node carries an unsaved Schema Editor draft and the edit changes its schema ([What compile and merge do for you](#what-compile-and-merge-do-for-you)). The refusal names the node and quotes the editor's issues.

## Evidence boundary

Everything here is offline. `check` and `flow validate` prove schema shape, resolved references, and name/instruction limits—not extraction accuracy. Only running the node on real documents shows that; expect a round of tightening afterwards, mostly in the instructions.

When compile or merge prints `wrote …/<Label>.json (IDP processor)`, the write landed in both the `.flow` node and the processor copy; debug runs and deployed extraction read that copy, so carry it with the `.flow`. Outside a solution no second file is written; packing creates it. A read-only mirror (`processorReadOnly`) and a tenant-published processor (`processorFolderPath`) have no copy of their own, so a `schema` on them never reaches deployed extraction. Report these. Taking the node live remains the user's decision.
