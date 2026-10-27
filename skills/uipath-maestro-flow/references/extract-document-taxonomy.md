# Extract document taxonomy

*Commands: `uip maestro flow nodes schema get` and `uip maestro flow nodes schema set`.*

An Extract document node (`uipath.ixp.extract-document-builder`) decides what to pull out of a document from a taxonomy it carries inline, at `inputs.schemaDocument` in the `.flow` file. The taxonomy names the field groups, the fields under them, each field's data type, and the instructions the model reads. The taxonomy is the extraction model's brief. Writing a good one is most of the work of making the node useful, and these two commands are how it is read and replaced.

```bash
uip maestro flow nodes schema get <file> --node-id <id> --output json
uip maestro flow nodes schema set <file> --node-id <id> --file <taxonomy.json> --output json
```

Both edit the `.flow` on disk and need no login. `--schema '<json>'` takes the document inline instead of `--file`.

Because they edit the `.flow`, they do not survive a project that generates it from TypeScript source: if the project has a `.flow-sdk/` directory, the next compile overwrites the taxonomy. See [extract-document-node.md](extract-document-node.md) for which authoring mode to pick.

For the node itself — checking the tenant has it, adding it, wiring `fileRef`, choosing it over a published IXP model — see [extract-document-node.md](extract-document-node.md). This guide assumes the node already exists.

## Starting from a flow in Studio Web

Users can start off with a flow in Studio Web, and ask you to continue working on it. You should then work on a local copy: pull it down, edit it, push it back.

Pulling it down requires the flow's solution id, and where that comes from depends on what the user has already said.

The user may provide either the URL of the flow in Studio Web - which contains the `solutionId` query parameter, or the solution id on its own. Either is enough to identify the solution to download.

If the user has not provided either of these and they are referring to a flow in Studio Web, ask them for either the URL or the solution id before proceeding.

If the user has not mentioned Studio Web at all, but no local `.flow` turns up, clarify with the user whether the flow lives in Studio Web.

**When in doubt, ask, rather than working it out.** Nothing enumerates what is in Studio Web: `uip solution` downloads, uploads and deletes by id, and the ids it prints come from solutions already to hand. So there is no listing to find, and the places that look like a way around it — the platform's search endpoint, the CLI's stored credentials — are not paths to take. Ask for a link or an id, say that either works, and carry on once it arrives.

Then pull it down:

```bash
uip login status --output json
uip solution download <solution-id>
```

The download writes a directory named after the id, with the flow project inside it, and every command in this guide runs against the `.flow` in that project. Where login has expired, say so and ask the user log in with: `uip login`.

Push the finished taxonomy back with `uip solution upload` from the downloaded solution's root, so the flow they opened in Studio Web is updated with the changes, and tell them where to find it.

### The documents uploaded to the node

Sample documents a user uploaded through Studio Web come down with the solution, under the flow project:

```
<Project>/evals/<dataset-id>/eval-files/
```

The dataset directory is a GUID, so list `evals/` rather than guessing it. These are the documents to design the taxonomy from, and reading them needs one step first.

**They are not the files their names claim.** Each keeps its original extension but holds text in a wrapper:

```
BINARY_FILE:application/pdf:2073
---BASE64---
JVBERi0xLjMKJe…
```

A header line gives the media type and the byte count, then a separator, then the payload. Reading one directly returns that text instead of a document, and decoding the whole file fails because of the first two lines. Drop them, then decode:

```bash
for f in <Project>/evals/*/eval-files/*; do
  tail -n +3 "$f" | base64 -d > "decoded/$(basename "$f")"
done
```

Read the decoded copies.

## At a glance

Read the user's sample documents, design the taxonomy from what is on the page, write it, and fix whatever the write rejects.

```bash
uip maestro flow nodes schema get Flow/Flow.flow --node-id extractDocument1 --output json   # what is there now
uip maestro flow nodes schema set Flow/Flow.flow --node-id extractDocument1 --file taxonomy.json --output json
uip maestro flow validate Flow/Flow.flow --output json
```

`set` replaces the whole document, mints a stable id for every new entry and keeps the ids already there, rebuilds the model-settings copy, and refuses a document that breaks a limit with one `Data.Issues` entry per problem. Read the documents before designing: a taxonomy written from the user's sentence alone misses the fields that are actually on the page, and invents ones that are not.

## The loop

1. **Collect the samples.** "The files uploaded to the node" are the ones that come down with the solution, under `<Project>/evals/<dataset-id>/eval-files/`, and they need decoding first — pull the flow down if it is not already local ([Starting from a flow in Studio Web](#starting-from-a-flow-in-studio-web)). Otherwise ask which documents are representative if the user has not said. Prefer variety over volume — a handful covering the layouts that differ tells you more than twenty of the same one.
2. **Read them.** One full `Read` per document returns text and image for both digital and scanned files, so no PDF tooling is needed — provided the file really is one. A document that came down with a solution is wrapped and reads as text until it is decoded.
3. **Design the taxonomy** against the rules below and write it to a JSON file.
4. **Write it:** `uip maestro flow nodes schema set <file> --node-id <id> --file <path> --output json`.
5. **Fix what it rejects.** Exit 3 means the document is a schema but breaks a rule; `Data.Issues` lists each problem with the path it is at. Correct those and run the same command again.
6. **Validate the flow:** `uip maestro flow validate <file> --output json` must come back `Valid`.
7. **Report** what was created, pass on the processor warning if the output carries one, and say that taking the node live is the user's step in Studio Web.

## The document

`set` takes the whole document, not a patch. It has two members that matter:

- `prompt` — the overall extraction instructions, applying to everything.
- `outputSchema` — an OpenAI structured-outputs JSON Schema. Its top-level `properties` are the field groups; its `$defs` are the field types.

`config` is a copy of the node's model settings. Leave it out of anything you write: `set` rebuilds it from `inputs.modelConfig`, so a `config` you send is discarded.

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

Each entry of `outputSchema.properties` is a field group, and its shape says how often it occurs.

A group that occurs **once** per document — a header, a summary block — is `"type": ["object", "null"]` and holds its fields directly under `properties`. A group that **repeats** — line items, transactions, payments — is `"type": "array"` and holds its fields under `items.properties`. Getting this wrong costs accuracy: a repeating table modelled as a single group returns only one row.

**Nesting is by name.** A group keyed `Invoice > Line Items` is a child of the group keyed `Invoice`. Both sit at the top level of `properties`; the hierarchy lives in the key, separated by a space-greater-than-space. The stored document also carries a back-reference to the parent's id, but you do not write it — `set` derives it from the key and fills it in.

Start with one group named for the document type, and put each table or section under it as a child. That mirrors how the document reads and gives the model a frame for where to look.

### Field types

A field does not carry its data type. It points at an entry in `outputSchema.$defs` with a `$ref`, and the entry says what the value looks like. A node arrives with six entries already defined:

| Use it for | `$defs` key | Returns |
| --- | --- | --- |
| A value copied off the page exactly as printed | `ft-exact-text` | the text, verbatim |
| A value that is derived, summarised, or where plain text is right but a stricter type is not certain | `ft-inferred-text` | text |
| A date | `ft-date` | a calendar date |
| A count or other quantity that is not money | `ft-number` | a decimal, keeping the printed scale |
| A currency amount | `ft-monetary-quantity` | the amount with its currency |
| A yes/no | `ft-boolean` | true or false |

**Carry the whole `$defs` block through unchanged.** `set` replaces the document, so a write that drops an entry removes that field type from the node even if nothing used it. Every `$ref` is checked against the block in the same document, wherever it sits, and one that names a key you did not include is refused — `$ref "#/$defs/ft-date" does not name a field type in outputSchema.$defs`.

**Prefer a stricter type only when you are sure.** `ft-inferred-text` is the right answer for anything ambiguous; a wrong strict type fails to extract a value that a text field would have returned.

**A Choice is the one type you add yourself.** Use it only where the complete set of allowed values is small, fixed, and evident from the documents or from what the user told you — a status column with four states, not a description column. Add an entry keyed with the same `ft-` prefix and a URL-safe suffix:

```json
"ft-payment-status": { "title": "Payment Status", "type": ["string", "null"], "enum": ["Paid", "Unpaid", "Partially paid"] }
```

Never infer the allowed values from what happens to appear in the samples — a value the documents did not show still extracts, and an enum that omits it loses it. Where the set is large or open, use `ft-inferred-text` and name the likely values in the field's instructions instead.

### Names

A group's name is its property key, a field's name is its property key, and a field type's name is its `title`. Each must be **64 characters or fewer**, counted exactly as written, including any surrounding spaces.

For a nested group, keep the **whole composed key** within 64 — `Invoice > Line Items` counts as 20, separator included. Keeping the composed key inside the limit satisfies every reader of the document.

Beyond the limit: never empty; never starting with punctuation, a symbol or a space; unique among siblings. Prefer the document's own wording — a field's name is usually its column header or row label — and keep it short enough to read in the editor.

### Instructions

Every group, every field and the document as a whole takes instructions: `description` on the group or field, `prompt` on the document. Each is **4096 characters or fewer**.

Write them for all three. The data type says what a value looks like; the instructions say which value on the page is the right one, which is what the model actually needs. `"The date the invoice was issued, not the due date"` earns its place. `"The invoice date"` does not — it repeats the field name and tells the model nothing.

Anything the user said about a particular field outranks what you inferred from the documents. If they said the reference number excludes a branch prefix, write that down even if every sample includes one.

### Size

Nothing here is enforced by the CLI, but a taxonomy that ignores it tends to extract badly:

- Keep a group to a readable number of fields. The IXP taxonomy quota, which this node does not share, caps a group at 25, and that is a reasonable ceiling to design against.
- Keep the number of distinct field types small. Every Choice with a different set of values is another type.
- A Choice with a long list of values is usually a text field in disguise.

## What `set` does for you

**It keeps stable ids.** Every group and field carries an id (`x-uipath-field-group-id`, `x-uipath-field-id`). Annotations, per-field evaluator settings and taxonomy history are all stored against those ids. On a first write there are none, and `set` mints one per entry. On a later write it keeps every id you sent, and gives an entry that has none the id of the same-named entry it replaces.

**It rebuilds the model-settings copy** from the node's `inputs.modelConfig`, so the document can never disagree with the settings the extraction actually runs under.

**It checks the document before writing anything.** A document that is not a schema at all, or that breaks a limit, is refused with exit 3 and changes nothing on disk.

**It refuses to destroy an unsaved draft.** When someone left an editing session open in Studio Web, the node carries that draft and `set` stops rather than overwriting it. `--discard-draft` proceeds and throws the draft away — only on the user's say-so.

## Editing a taxonomy that already exists

`get` first, always. Then change what needs changing and send the whole document back, under two rules.

**Keep the ids.** Every id that came back from `get` stays on its entry, including through a rename — an id is what connects a field to the annotations and evaluator settings recorded against it, and the readers fall back to matching by position when one is missing. A rename that drops the id quietly re-points stored annotations at whatever field now sits in that place.

**Send everything back.** `set` replaces the document rather than patching it, so anything you leave out is gone: other field groups, the `$defs` catalogue, the overall prompt.

Never write a replacement from scratch over a taxonomy that already has content. If the user wants a fresh start, say what will be lost first.

## Reading the output

`get` returns the stored document under `Data.Schema`, with its own key casing intact so it can be edited and sent straight back. `Data.HasDraft` says whether an unsaved Studio Web edit is parked on the node, and `Data.DraftIssueMessages` says what the editor thought was wrong with it.

`set` returns counts and what happened to the ids:

| Field | Means |
| --- | --- |
| `Groups`, `Fields`, `FieldTypes` | what the written taxonomy now holds |
| `GroupIdsPreserved`, `FieldIdsPreserved` | entries that kept the id they already had |
| `GroupIdsMinted`, `FieldIdsMinted` | entries that were new and got one |
| `DraftDiscarded` | an unsaved editor draft was thrown away |
| `Warnings` | the node names a tenant-side processor that still holds the previous schema |

On an edit, `FieldIdsMinted` above zero where you expected a rename is the signal that an id was dropped — check before reporting success.

## When it refuses

| Exit | Message | What to do |
| --- | --- | --- |
| 3 | `Schema document failed validation` | Read `Data.Issues`: each one names the path and the problem. Fix and resend. |
| 3 | `Invalid schema document` | The document is not a schema — it needs `prompt` and `outputSchema`. |
| 3 | `Legacy schema document shape` | The node still carries the superseded `{taxonomy, fieldTypes}` form. Opening the flow once in Studio Web converts it. |
| 3 | `Nested field group "<key>" has no parent group "<parent>"` | A group named `Parent > Child` needs `Parent` to be a group of its own in the same document. Add it, or flatten the name. |
| 1 | `Node "<id>" carries an unsaved Schema Editor draft` | Someone's unfinished editor session is on the node. Ask before passing `--discard-draft`; it throws their work away. |
| 1 | `Invalid --schema JSON` | The argument did not parse. Prefer `--file` for anything sizeable; shells mangle inline JSON. |
| 1 | `Cannot read --file` | The path does not exist or could not be read. This is a wrong path, not a malformed schema. |
| 1 | node not found, or wrong node type | `uip maestro flow nodes list <file>` gives the ids and types. Only Extract document nodes carry a taxonomy. |

## Evidence boundary

Everything here is offline. `set` and `flow validate` prove the taxonomy is well formed, that its references resolve and that its names and instructions fit — not that it extracts the right values. Only running the node against real documents shows that, and the taxonomy usually needs a round of tightening afterwards, mostly in the instructions.

Two things this does not do. It does not update the tenant-side processor a node created in Studio Web points at, so a solution published before that flow is next saved there extracts with the previous taxonomy — the warning in `set`'s output says when this applies. And it does not take anything live: that stays a decision for the user, in Studio Web.
