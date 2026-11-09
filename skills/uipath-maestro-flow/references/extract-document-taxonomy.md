# Extract document taxonomy

*Commands: `uip maestro flow nodes schema get` and `uip maestro flow nodes schema set`.*

An Extract document node (`uipath.ixp.extract-document-builder`) stores its taxonomy at `inputs.schemaDocument` in the `.flow`: field groups, fields, types, and model instructions. Read or replace it:

```bash
uip maestro flow nodes schema get <file> --node-id <id> --output json
uip maestro flow nodes schema set <file> --node-id <id> --schema @<taxonomy.json> --output json
```

Both commands edit the `.flow` on disk without login. `--schema` accepts JSON or a file prefixed with `@`. These commands are new: an older CLI returns `error: unknown command 'schema'` with `"Result": "ValidationError"`; tell the user to update `uip`.

This guide assumes the node exists. Adding it, wiring `fileRef`, published IXP-model behavior, and `.flow-sdk/` overwrite behavior are in [extract-document-node.md](extract-document-node.md).

## Starting from a flow in Studio Web

<!--skill-flavor:extract-brownfield:start-->
For a Studio Web flow, work on a local copy: download, edit, and upload it. Identify it from the URL's `solutionId` query parameter or the solution id; if neither was provided, ask for one. If Studio Web was not mentioned but no local `.flow` exists, ask whether the flow lives there.

**When in doubt, ask, rather than working it out.** Nothing lists Studio Web contents: `uip solution` downloads, uploads, and deletes by id, and printed ids come only from solutions already at hand. Do not use the platform search endpoint or CLI stored credentials to find one. Ask for the URL or id, explain either works, and continue when supplied.

Then run:

```bash
uip login status --output json
uip solution download <solution-id>
```

The download creates a directory named for the id containing the project; run this guide's commands against its `.flow`. If login expired, say so and ask the user to log in with `uip login`.

After editing, run `uip solution upload` from the downloaded solution root, then tell the user where to find the updated Studio Web flow.
<!--skill-flavor:extract-brownfield:end-->

### The documents uploaded to the node

<!--skill-flavor:extract-eval-files-path:start-->
Studio Web sample documents are under:

```
<Project>/evals/<dataset-id>/eval-files/
```
<!--skill-flavor:extract-eval-files-path:end-->

The dataset directory is a GUID; list `evals/` rather than guessing it. Each file retains its original extension and contains:

```
BINARY_FILE:application/pdf:2073
---BASE64---
JVBERi0xLjMKJe…
```

Drop the first two lines before decoding, or the wrapper is read as document text and whole-file decoding fails:

```bash
mkdir -p decoded
for f in <Project>/evals/*/eval-files/*; do
  tail -n +3 "$f" | base64 -d > "decoded/$(basename "$f")"
done
```

If multiple datasets contain the same filename, decode separately per dataset directory to prevent overwrites. Read the decoded copies.

## At a glance

Read the samples, design from their contents, write the taxonomy, fix rejected issues, and validate:

```bash
uip maestro flow nodes schema get Flow/Flow.flow --node-id extractDocument1 --output json   # what is there now
uip maestro flow nodes schema set Flow/Flow.flow --node-id extractDocument1 --schema @taxonomy.json --output json
uip maestro flow validate Flow/Flow.flow --output json
```

`set` replaces the whole document rather than patching it ([What `set` does for you](#what-set-does-for-you)). Read documents before designing: relying only on the user's sentence misses actual fields and invents absent ones.

## The loop

1. **Collect samples.** Use decoded Studio Web files ([The documents uploaded to the node](#the-documents-uploaded-to-the-node)); otherwise ask which documents are representative. Prefer varied layouts to duplicates.
2. **Read them.** Perform one full `Read` per decoded document; it returns text and image for digital and scanned files, so no PDF tooling is needed.
3. **Design** the taxonomy under the rules below and save it as JSON.
4. **Write it:** run `uip maestro flow nodes schema set <file> --node-id <id> --schema @<path> --output json`.
5. **Fix rejection.** Exit 3 means the document violates a schema rule; correct each path in `Data.Issues` and rerun the same command.
6. **Validate:** run `uip maestro flow validate <file> --output json`; it must return `Valid`.
7. **Report** what was created, pass on any processor warning, and say that taking the node live is the user's Studio Web step.

## The document

The document has two members that matter:

- `prompt`: overall extraction instructions.
- `outputSchema`: OpenAI structured-outputs JSON Schema; top-level `properties` are groups and `$defs` are field types.

Leave out `config`: `set` rebuilds it from `inputs.modelConfig`, so a supplied copy is discarded.

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

Each `outputSchema.properties` entry is a group: single-occurrence groups use `"type": ["object", "null"]` with fields under `properties`; repeating groups use `"type": "array"` with fields under `items.properties`. Model repeating tables as arrays.

Encode nesting in the key: `Invoice > Line Items` is a child of `Invoice`; both remain top-level properties, using a space-greater-than-space separator. `set` derives the stored parent-id back-reference; do not write it. Start with one document-type group and place each table or section beneath it.

### Field types

Fields use `$ref` entries in `outputSchema.$defs`; they do not carry types themselves. Preserve the entire existing `$defs` block unchanged: `set` replaces the document, missing entries remove types, and every `$ref` must resolve in that block; one that names a key you did not include is refused — `$ref "#/$defs/ft-date" does not name a field type in outputSchema.$defs`.

The six predefined entries are:

| Use it for | `$defs` key | Returns |
| --- | --- | --- |
| copied exactly as printed | `ft-exact-text` | verbatim text |
| derived, summarized, or uncertain strict type | `ft-inferred-text` | text |
| date | `ft-date` | calendar date |
| non-money count or quantity | `ft-number` | decimal, preserving printed scale |
| currency amount | `ft-monetary-quantity` | amount with currency |
| yes/no | `ft-boolean` | true or false |

Use a stricter type only when certain; otherwise use `ft-inferred-text`, since a wrong strict type can lose a value.

A Choice is the only type to add. Use it only for a small, fixed, evident set of allowed values—not an open description—and key it with `ft-` plus a URL-safe suffix. Its shape is:

```json
"ft-payment-status": { "title": "Payment Status", "type": ["string", "null"], "enum": ["Paid", "Unpaid", "Partially paid"] }
```

Never infer the allowed values from what happens to appear in the samples — a value the documents did not show still extracts, and an enum that omits it loses it. For large or open sets, use `ft-inferred-text` and name likely values in the field instructions.

### Names

A group key, field key, and field-type `title` must be **64 characters or fewer**, counting spaces.

For a nested group, keep the **whole composed key** within 64 — `Invoice > Line Items` counts as 20, separator included. Keeping the composed key inside the limit satisfies every reader of the document.

Names must be nonempty, not start with punctuation, a symbol, or a space, and be unique among siblings. Prefer concise wording from the document, such as its column header or row label.

### Instructions

Write instructions for every group, every field and the document as a whole: `description` on each group and field, `prompt` on the document. Each is **4096 characters or fewer**. Types specify value shape; instructions identify the correct value on the page, not merely repeat its name. User instructions about a field outrank sample-based inferences.

### Size

These limits are not CLI-enforced but improve extraction: keep groups to a readable number of fields (25 is a reasonable ceiling, matching the IXP taxonomy quota this node does not share); keep distinct field types few (every Choice with a different set of values is another type); and treat a Choice with many values as text.

## What `set` does for you

- **Stable ids:** Groups and fields carry `x-uipath-field-group-id` and `x-uipath-field-id`, used by annotations, evaluator settings, and taxonomy history. First writes mint ids; later writes preserve submitted ids and assign a missing id from the same-named replaced entry.
- **Model settings:** It rebuilds them from `inputs.modelConfig`.
- **Validation:** It validates before writing. A non-schema or limit violation returns exit 3 and changes nothing on disk.
- **Draft protection:** If Studio Web has an editing draft, `set` stops. Run `--discard-draft` only on the user's say-so; it proceeds by throwing the draft away.

## Editing a taxonomy that already exists

Always run `get` first, modify only what is needed, and send the whole document back. Preserve every returned id, including across renames; without it, annotations and evaluator settings can be reassigned by position. Since `set` replaces rather than patches, send all groups, the `$defs` catalogue, and the overall prompt. Never write a replacement from scratch over a taxonomy that already has content. If the user wants a fresh start, say what will be lost first.

## Reading the output

`get` returns the stored document as `Data.Schema`, preserving key casing. `Data.HasDraft` reports an unsaved Studio Web edit; `Data.DraftIssueMessages` reports editor problems.

`set` returns:

| Field | Means |
| --- | --- |
| `Groups`, `Fields`, `FieldTypes` | contents of the written taxonomy |
| `GroupIdsPreserved`, `FieldIdsPreserved` | entries retaining their existing ids |
| `GroupIdsMinted`, `FieldIdsMinted` | new entries assigned ids |
| `BusinessChecksDropped` | checks attached to ids removed from the document |
| `DraftDiscarded` | an unsaved draft was discarded |
| `ReplacedLegacyDocument` | superseded `{taxonomy, fieldTypes}` form was replaced; no id was preserved |
| `Warnings` | a tenant-side processor still has the previous schema |

On edits, inspect `FieldIdsMinted` and `BusinessChecksDropped` before reporting success. An unexpected minted id means a dropped rename id; its annotations and business checks no longer follow the field.

## When it refuses

| Exit | Message | What to do |
| --- | --- | --- |
| 3 | `Schema document failed validation` | Read `Data.Issues` for paths and problems. A missing parent is included: `Nested field group "<key>" has no parent group "<parent>"`. `Parent > Child` requires `Parent` in the same document; if an existing group was intended as parent, rename one key to match—never add an empty parent. |
| 3 | `Invalid schema document` | Supply `prompt` and `outputSchema`; the document is not a schema. |
| 3 | `Legacy schema document shape` | Send `{ prompt, outputSchema }`, not `{taxonomy, fieldTypes}`. An existing legacy node document is replaced and reports `ReplacedLegacyDocument: true`. |
| 1 | `Node "<id>" carries an unsaved Schema Editor draft` | Ask before running `--discard-draft`; it discards unfinished work. |
| 1 | `Invalid --schema JSON` | The argument did not parse; prefer `--schema @<file>` for sizeable JSON because shells mangle inline JSON. |
| 1 | `Cannot read the schema file` | The `@` path is missing or unreadable; this is a path error, not malformed schema JSON. |
| 1 | node not found, or wrong node type | Run `uip maestro flow nodes list <file>` for ids and types. Only Extract document nodes carry taxonomies. |

## Evidence boundary

This process is offline. `set` and `flow validate` prove only that the taxonomy is well formed, references resolve, and names and instructions fit—not extraction accuracy. Run the node against real documents to assess values; instructions usually need tightening.

It does not update the tenant-side processor used by a Studio Web-created node. A solution published before the flow is next saved there extracts with the previous taxonomy; `set`'s warning identifies this. It also does not take anything live; that remains the user's Studio Web decision.