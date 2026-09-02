# The Standard resource (SR)

> Reached from
> [Author the min.json](../activity-generation.md#5-author-the-minjson) and
> [Compile the metadata](../activity-generation.md#6-compile-the-metadata) — both
> come **after the script has run**, because the response you observed is the only
> source for the output half. The contract below is the same one the platform
> enforces wherever the metadata is built.
>
> Paths in this file are relative to the skill root: the generator is
> `uip is activities metadata build`, the derivation rulebook
> [minimal-metadata-design.md](minimal-metadata-design.md), and the full field
> reference [standard-resource-contract.md](standard-resource-contract.md).

# Generate a Standard resource for an IS activity

## What this produces

One **Standard resource (SR)** for the **main activity**: the activity metadata
(authored as **JSON**) that the UiPath UI reads to render the activity and that
the platform uses to execute it. The action supplies the **call wiring** (HTTP
`method`, the vendor `path`, and the `scriptRef` base names via the
the script files); the **complete INPUT surface** — every parameter/field the vendor
accepts — comes from the **vendor API schema**, not the action's minimal
`Input`/`Output`. **Outputs stay minimal** — the record identifier(s) plus any
value that is the point of the operation, never the vendor's full response tree
(contract §4.2). DTL lookup actions do NOT get an SR (see below).

## The contract

**[standard-resource-contract.md](standard-resource-contract.md) is the
authoritative, self-contained contract — read it before authoring.** It documents
every field you may emit, the required fields, the closed value sets, the
`path` XOR `scriptRef` rule for lookups, and a worked example. You do NOT need the
source `.proto`; the reference is complete for the current scope.

**Current scope — full INPUT surface, minimal OUTPUT set, + DTL.** Enumerate
**every input the vendor operation expects** — all request parameters/fields,
required AND optional — sourced from the **vendor API schema**, not the action's
minimal `Input`/`Output`. For outputs, emit **only what a consumer needs**: the
record identifier(s), marked `primaryKey`, plus any value that is the purpose of
the operation. The response you observed is one sample, not the vendor's
contract — enumerating all of it claims more than you know.

Split per the contract: URL inputs (path/query) → `parameters[]`, request body →
`fields{}` (`request: true`), outputs → `fields{}` (`response: true`).
Include design-time lookups (DTL) via `reference` — this activity structure uses
`scriptRef` only (never `path`). **Emit ALL design items except
`generateSchema`** — the one exclusion, because a generateSchema-driven dynamic
schema is an api-type ObjectAction resolved at design time, not a static design
item (see `uip is resources describe -f/--field`).

The items whose derivation rules are written down: `design.position` on every
input (required → `primary`, optional → `secondary`; response fields get no
`design`); on **lookup** inputs also `design.displayPattern` (a `{token}` of the
most readable lookup field); on **flat** lookups `design.enableUserOverride:
true`; on inputs that semantically accept multiple entries
`design.isMultiSelect: true` — where a **true vendor array** gets a `[*]` name
and NO `delimiter`, while a **delimited-string list** (vendor packs the values
into one string, e.g. Slack `users` = comma-separated IDs) keeps its plain name,
`type: string`, and `design.delimiter` set explicitly to the vendor's separator
(never rely on the space default); and `design.component: "FolderPicker"` on
**hierarchical** (folder-tree) lookups — which OMIT `enableUserOverride`.
Contract §4.3 has the full rules.

**Emit only those five. Everything else is out** — other `component` values,
`isHidden`, `fieldActions`, `textBlocks`, widgets, object-level design,
`generateSchema`, triggers/events, curation, `compatibleProjectTypes`. There is no
rule to derive them from, so any value would be a UI claim you cannot support.
See the contract's "Deferred" section for the full list.

## One SR per MAIN activity — DTL lookup actions get NO SR

Step 5 emits a **main action file** for the activity and, for each
lookup field, a **DTL lookup action file**. Only the **main activity gets an
SR.** The DTL lookup actions get **no SR** — they are referenced from the main
SR by name only.

Both references use a `scriptRef` whose value is the **action file's base name
with the extension stripped** (`action.js` → `action`,
`listUserGroups.js` → `listUserGroups`) — never a path, never the extension:

- `metadata.method.<VERB>.scriptRef` = the **main action file's** base name (the
  script that executes the activity).
- each DTL field's `reference.scriptRef` = that lookup's **lookup action file's**
  base name.

Which action file serves the main activity, and which serves each DTL field, is
decided by step 5 and passed to
this step — do not guess the base names; use what the parent supplies (it
is the field → lookup-action mapping).

## Workflow — author the MINIMAL metadata, generate the SR with the script

The SR is NOT hand-authored. You author a small **minimal metadata file**
(`activity/<name>.min.json`) carrying only the irreducible facts, then run the
deterministic generator (`uip is activities metadata build`), which expands it into the
final SR and validates every contract rule. The min-file schema and the full
derivation rulebook live in [minimal-metadata-design.md](minimal-metadata-design.md) — read it
alongside the contract.

1. **Read [standard-resource-contract.md](standard-resource-contract.md)** (the
   target shape and rules) and
   **[minimal-metadata-design.md](minimal-metadata-design.md) §3–§5** (the min-file schema
   and what the script derives).
2. **Collect the names** — the main action's file base name and, for each lookup
   field, its lookup script's base name (step 3 produced those). Here the scripts
   already exist: the min.json is authored AFTER them (step 5 follows step 4), so
   you read the names off the files rather than committing to them. One metadata
   file for the main activity only.
3. **Author `activity/<activity_name>.min.json`** — in the working connector
   dir's `activity/` folder, next to where the SR will land (matching the
   scaffold's `uipath-salesforce-slack/activity/` layout). ALL judgment lives in
   this file, sourced from the **vendor API schema** (the same vendor source
   step 4 used, NOT the action's minimal `Input`/`Output`):
   - `activity` block: `name`, `description`, `elementKey`, `vendorPath`,
     `httpMethod` (the single verb — an SR is always one operation),
     `operation` override when the default mapping is wrong, and `scriptRef` =
     the main action file's base name,
   - `inputs[]`: EVERY vendor input, required AND optional, each with `in`
     (`path`|`query`|`body`), `required`, `description`, and where applicable:
     `isArray` (true vendor arrays only), `returned` (also in the response),
     `enum`, `defaultValue`, `lookup { scriptRef, value, display[] }`, and the
     **full `design` block, authored per the contract's §4.3 rules** — the
     script copies it into the SR VERBATIM (position from required/optional,
     `delimiter` for delimited-string lists, `displayPattern`/
     `enableUserOverride` on flat lookups, `component: "FolderPicker"` without
     override on folder-tree lookups; future design keys go here too, no script
     change needed),
   - `outputs[]`: **only the necessary** response fields — the identifier(s) with
     `primaryKey: true`, plus any value that is the point of the operation. Not the
     vendor's full response tree: what you observed is one sample, not a contract.
     For a LIST operation, one top-level entry — the records array
     (`isArray: true`) — with its element fields trimmed the same way.
4. **Run the generator:**
   ```
   uip is activities metadata build activity/<activity_name>.min.json
   # → writes activity/<activity_name>.json (the final SR)
   ```
   The script derives the mechanics (`[*]` naming, method/verb slot,
   `metadata.primaryKey`, `responseSchema`, enum→enhancedEnum routing), copies
   each input's authored `design` block into the SR **verbatim**, and
   **validates the contract rules** (including the design rules — position vs
   required, no delimiter on arrays, FolderPicker without override), refusing to
   write on any violation. On errors, fix the **min-file** and re-run — NEVER
   hand-edit the generated SR.
5. **Stamp the action script's type header** from the generated metadata:
   ```
   uip is activities metadata types activity/<activity_name>.json <ActivityName>.js
   ```
   The action is plain `.js` and nothing typechecks it, so this leading
   `/* … */` block is the only record of its shape. Deriving it from the metadata
   keeps the two from drifting; re-running replaces the block in place.
6. **Keep both files.** `activity/<name>.min.json` is the reviewable source of
   truth; `activity/<name>.json` is the generated artifact — regenerate it, and
   re-stamp the header, after any min-file change.
