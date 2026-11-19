# Extract document taxonomy

*Commands: `uip maestro flow nodes schema get` and `uip maestro flow nodes schema set`.*

An Extract document node (`uipath.ixp.extract-document-builder`) extracts from the inline taxonomy at `inputs.schemaDocument` in the `.flow`: groups, fields, field types, and model instructions. Read or replace it with:

```bash
uip maestro flow nodes schema get <file> --node-id <id> --output json
uip maestro flow nodes schema set <file> --node-id <id> --schema @<taxonomy.json> --output json
```

Both commands edit the `.flow` without login. `--schema` accepts JSON or a file when its value starts with `@`.

**These commands are new.** If the CLI returns `error: unknown command 'schema'` with `"Result": "ValidationError"`, tell the user to update `uip`; this is not a bad node or flow.

This guide assumes the node exists. For adding it, wiring `fileRef`, when it applies over a published IXP model, and why these commands do not survive a `.flow-sdk/` project (the next compile overwrites the taxonomy), see [extract-document-node.md](extract-document-node.md).

## Starting from a flow in Studio Web

<!--skill-flavor:extract-brownfield:start-->
For a Studio Web flow, work on a local copy: download, edit, and upload it. Identify it by solution id or the Studio Web URL's `solutionId` query parameter. If neither was provided, ask for either; if Studio Web was not mentioned and no local `.flow` exists, ask whether the flow is in Studio Web. **When in doubt, ask, rather than working it out.** Nothing lists Studio Web: `uip solution` downloads, uploads, and deletes only by id. Search endpoints and stored CLI credentials are not ways around asking; say either a link or an id works, and continue once it arrives.

Run:

```bash
uip login status --output json
uip solution download <solution-id>
```

The download creates a directory named for the id containing the flow project. Run this guide's commands against its `.flow`. If login expired, report it and ask the user to log in with `uip login`.

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

Read sample documents, design and write the taxonomy, fix rejections, and validate:

```bash
uip maestro flow nodes schema get Flow/Flow.flow --node-id extractDocument1 --output json   # what is there now
uip maestro flow nodes schema set Flow/Flow.flow --node-id extractDocument1 --schema @taxonomy.json --output json
uip maestro flow validate Flow/Flow.flow --output json
```

`set` replaces the whole document, not a patch ([What `set` does for you](#what-set-does-for-you)). Read documents first: relying only on the user's sentence misses actual fields and invents absent ones.

## The loop

<!--skill-flavor:extract-collect-samples:start-->
1. **Collect samples.** Check and decode uploaded documents ([The documents uploaded to the node](#the-documents-uploaded-to-the-node)). Without samples, ask for representative documents even if fields were listed; if none are supplied, design from the stated fields and say so in the report.
2. **Read them.** Perform one full `Read` per decoded document; it returns text and image for digital and scanned files, so PDF tooling is unnecessary.
3. **Design** the taxonomy under the rules below and write it to a JSON file.
4. **Write:** run `uip maestro flow nodes schema set <file> --node-id <id> --schema @<path> --output json`.
5. **Fix rejections.** Exit 3 means a rule-violating schema; fix each problem `Data.Issues` lists at its path and rerun the same command.
6. **Validate:** run `uip maestro flow validate <file> --output json`; it must return `Valid`.
7. **Report** what was created, `Data.ProcessorSync`, and `Data.ResourceFile`. The write stores the schema in that file too; keep it with the `.flow`. Taking the node live is the user's decision.
<!--skill-flavor:extract-collect-samples:end-->

## The document

The written document has `prompt` (overall extraction instructions) and `outputSchema` (an OpenAI structured-outputs JSON Schema whose top-level `properties` are groups and `$defs` are field types). Do not write `config`: `set` rebuilds it from `inputs.modelConfig`, so supplied `config` is discarded.

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

Nesting is by property name: `Invoice > Line Items` is a child of `Invoice`; both remain top-level properties, separated by space-greater-than-space. `set` derives and stores the parent back-reference, so do not write it. A top-level group names no parent. Start with one document-type group and put each table or section beneath it.

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

Carry the whole `$defs` block through unchanged. `set` replaces the document; omitting an entry removes that type, and every `$ref` must resolve within the same block. Prefer a stricter type only when certain; otherwise use `ft-inferred-text`.

A Choice is the only type you add; add one only when its complete set of allowed values is small, fixed, and evident from documents or user instructions — a status column, not a description column. Use an `ft-` key with a URL-safe suffix (letters, digits, `.`, `_` or `-` only, so the `$ref` naming it needs no escaping) and give every entry a `title`, for example:

```json
"ft-payment-status": { "title": "Payment Status", "type": ["string", "null"], "enum": ["Paid", "Unpaid", "Partially paid"] }
```

Never infer enum values from what appears in the samples: a value they did not show still extracts, and an enum that omits it loses it. For large or open sets, use `ft-inferred-text` and list likely values in field instructions.

### Names

Group and field property keys, and field-type `title` values, must be **64 characters or fewer**, counting spaces. The entire nested key, including ` > `, counts. Names must not be empty, begin with punctuation, a symbol, or a space, and must be unique among siblings. Prefer short wording from the document.

### Instructions

The document `prompt`, every group `description`, and every field `description` must be **4096 characters or fewer**. Write all three: types describe value shape; instructions identify the correct value on the page. `"The date the invoice was issued, not the due date"` earns its place; `"The invoice date"` repeats the field name and tells the model nothing. User instructions for a field outrank document inference; record them even if every sample contradicts them (e.g. a reference number said to exclude a branch prefix).

### Size

These limits are not CLI-enforced but improve extraction:

- Keep groups to a readable number of fields; 25 is a reasonable ceiling (the IXP taxonomy quota, which this node does not share, caps groups at 25).
- Keep distinct field types few; each distinct Choice is another type.
- A long Choice is usually a text field in disguise.

## What `set` does for you

- **Stable ids:** Groups and fields carry `x-uipath-field-group-id` and `x-uipath-field-id`, used by annotations, evaluator settings, and taxonomy history. First writes mint ids; later writes preserve supplied ids and assign a missing entry the id of the same-named replaced entry. An id belongs to one entry: never copy one onto a second group or field.
- **Model settings:** It rebuilds them from `inputs.modelConfig`.
- **Validation:** A non-schema or limit violation returns exit 3 and changes nothing on disk.
- **Draft protection:** When someone left an editing session open in Studio Web, the node carries that draft and `set` stops. `--discard-draft` proceeds and throws the draft away; pass it only when the user asked in this conversation. Headless or CI: leave the node unchanged, report the draft and `DraftIssueMessages`, and stop; the request is not done. Run no `nodes provision` either: it writes `inputs.processorKey` into the node. Report a missing processor instead. Never hand-edit `inputs.schemaDocument` to bypass this.

## Editing a taxonomy that already exists

Run `get` first, then send the complete document back. Preserve every existing id, including through renames, because ids connect annotations and evaluator settings; missing ids cause position-based fallback and can repoint annotations. Preserve every existing group and field's `description`, type, and id exactly as returned; add information only in new groups, fields, or `prompt`. Send all groups, `$defs`, and the overall prompt because `set` replaces rather than patches. Never write from scratch over existing content; if the user wants a fresh start, first say what will be lost.

## Reading the output

`get` returns the stored document under `Data.Schema` with original key casing, so it can be edited and sent straight back. `Data.HasDraft` reports an unsaved Studio Web edit; `Data.DraftIssueMessages` says what the editor found wrong with the draft.

`set` returns:

| Field | Means |
| --- | --- |
| `Groups`, `Fields`, `FieldTypes` | counts in the written taxonomy |
| `GroupIdsPreserved`, `FieldIdsPreserved` | entries retaining existing ids |
| `GroupIdsMinted`, `FieldIdsMinted` | new entries receiving ids |
| `BusinessChecksDropped` | checks attached to removed ids |
| `DraftDiscarded` | whether an unsaved draft was discarded |
| `ReplacedLegacyDocument` | superseded `{taxonomy, fieldTypes}` form was replaced, so no id was retained |
| `ProcessorKey` | processor through which the schema deploys |
| `ResourceFile` | processor file under the solution containing the deployable schema; this write creates or updates it, and it belongs in the same change as the `.flow` |
| `ResourcePending` | why a newly gained processor has no resource file; pass on what creates it |
| `ProcessorSync` | whether packing rebuilds that processor; it does not for a read-only mirror (`inputs.processorReadOnly`) or tenant-published processor (`inputs.processorFolderPath`), whose deployed schema this write does not reach |

On an edit, check `FieldIdsMinted` and `BusinessChecksDropped` before reporting success. A minted id where a rename was intended means the id was dropped: its annotations no longer point at the field, and its business checks are gone.

## When it refuses

| Exit | Message | What to do |
| --- | --- | --- |
| 3 | `Schema document failed validation` | Read `Data.Issues` for paths and problems. A missing parent is included: `Nested field group "<key>" has no parent group "<parent>"`. `Parent > Child` needs `Parent` in the same document; if an existing group was clearly meant as parent, rename one key to match—never add an empty parent. |
| 3 | `Invalid schema document` | Send `prompt` and `outputSchema`; the document is not a schema. |
| 3 | `Legacy schema document shape` | Send `{ prompt, outputSchema }`, not `{taxonomy, fieldTypes}`. An existing legacy node document is replaced and reports `ReplacedLegacyDocument: true`. |
| 1 | `Node "<id>" carries an unsaved Schema Editor draft` | Someone's unfinished editor session is on the node. Ask before passing `--discard-draft`; it throws their work away. Headless: stop and report. |
| 1 | `Invalid --schema JSON` | The argument did not parse; prefer `--schema @<file>` for sizeable JSON. |
| 1 | `Cannot read the schema file` | The `@` path is absent or unreadable; this is a path error, not malformed schema. |
| 1 | node not found, or wrong node type | Run `uip maestro flow nodes list <file>` for ids and types. Only Extract document nodes carry a taxonomy. |

On the SDK route, `check` reports the same content problems before compile, one code per rule, with the path and the problem in the message (SDK with builder-sdk#2055):

| Code | Rule it enforces |
| --- | --- |
| `EXTRACT_TAXONOMY_NESTING` | nesting by name: `A > B` needs a group `A`, and a top-level group names no parent ([Field groups](#field-groups)) |
| `EXTRACT_TAXONOMY_REF` | every field names a field type, and every `$ref` resolves inside `$defs` ([Field types](#field-types)) |
| `EXTRACT_TAXONOMY_LIMIT` | names within 64 characters, a nested group's whole composed key included; instructions within 4096 ([Names](#names), [Instructions](#instructions)) |
| `EXTRACT_TAXONOMY_DUPLICATE_ID` | no id on two groups or two fields ([What `set` does for you](#what-set-does-for-you)) |
| `EXTRACT_TAXONOMY_FIELD_TYPE` | a `$defs` key needs no escaping in a `$ref`; every field type has a title ([Field types](#field-types)) |
| `EXTRACT_TAXONOMY_STRUCTURE` | every group, field and container is the shape the Schema Editor reads |
| `EXTRACT_TAXONOMY_BARE`, `EXTRACT_TAXONOMY_LEGACY` (warnings) | a bare JSON Schema, or the `{taxonomy, fieldTypes}` form, in place of `{ prompt, outputSchema }`; `set` refuses both, so treat either as an error |

No code checks sibling-name uniqueness ([Names](#names)): each name is a property key, so JSON already makes siblings unique.

## Evidence boundary

Everything here is offline. `set` and `flow validate` prove schema shape, resolved references, and name/instruction limits—not extraction accuracy. Only running the node on real documents shows that; expect a round of tightening afterwards, mostly in the instructions.

When `Data.ResourceFile` is present, the write landed in both the `.flow` node and the processor copy; debug runs and deployed extraction read that copy, so carry it with the `.flow`. `Data.ResourcePending` means no second file was written. `Data.ProcessorSync` identifies cases where the schema never reaches deployed extraction. Report these values. Taking the node live remains the user's decision.
