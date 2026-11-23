# Document classify and Extract document

*Exact signatures, fields, and defaults: `documentClassify()` and `dynamicExtract()`.*

Two document steps that need no trained IxP fields: classification
(`uipath.document.classify`) labels a document, and the Extract document node
(`uipath.ixp.extract-document-builder`) pulls fields against a taxonomy you
author INLINE ([Two ways to author it](#two-ways-to-author-it)). It is
opt-in: add it only when the user names the Extract document node. Any other
extraction request, one with no trained model included, goes to a published
IXP model or an IXP project ([ixp.md](ixp.md)), never to this node.

Signatures: `documentClassify({ fileRef, pageRange?, splitPages?, modelConfig? })`;
`dynamicExtract({ fileRef, schema?, pageRange?, modelConfig? })`.

```ts
.input({ file: types.file })
.step('classify', documentClassify({ fileRef: input('file'), splitPages: true }))
.step('extract', dynamicExtract({ fileRef: input('file'), schema: invoiceTaxonomy }),
  { label: 'Extract invoice' })
.step('total', script({ code: 'return $vars.extract.output.result.output;' }))
```

## At a glance

Classify a document (`uipath.document.classify`), or extract fields against an
INLINE taxonomy (`uipath.ixp.extract-document-builder`) instead of a published
IxP project's trained fields.
Signatures: `documentClassify({ fileRef, pageRange?, splitPages?, modelConfig? })`;
`dynamicExtract({ fileRef, schema?, pageRange?, modelConfig? })`.

```ts
.step('classify', documentClassify({ fileRef: input('file'), splitPages: true }))
.step('extract', dynamicExtract({ fileRef: input('file'), schema: invoiceTaxonomy }),
  { label: 'Extract invoice' })
```

## Two ways to author it

**The SDK factory**, `dynamicExtract()`, takes no `model` argument. Compile
gives each step its processor, as `uip maestro flow nodes create` does:

- it writes `inputs.processorKey`, one per step, the same on every recompile;
- when it compiles the project's main flow inside a local solution (a folder
  whose `.uipx` lists the project), it writes the processor's resource file
  (`resources/solution_folder/idpProcessor/extraction/<Label>.json`), keeps
  it in step with the node on every compile, and declares it in
  `bindings_v2.json`. A compile with no `.uipx` above it, such as Studio
  Web's candidates under `/tmp`, writes no file: the designer creates it.

So validate and packing pass with no CLI step after compile, and
decompile -> compile keeps the node and its key. Give the
step a `label` that says what it extracts: the processor is named after it.

```ts
.step('extract', dynamicExtract({ fileRef: input('invoice'), schema: invoiceTaxonomy }),
  { label: 'Extract invoice' })
```

Needs `@uipath/maestro-builder-sdk` 6.118.0 or later. An older SDK requires
`model` (compile fails reading `modelName` without it) and writes no
`inputs.processorKey`.
<!--skill-flavor:extract-sdk-floor:start-->
Upgrade the copy in use: `npm install @uipath/maestro-builder-sdk@latest` in a
workspace that has its own `node_modules` copy, else
`npm install -g @uipath/maestro-builder-sdk@latest`. Where that is not
possible, use the CLI.
<!--skill-flavor:extract-sdk-floor:end-->

**The CLI commands** author the same node in a flow that has no TypeScript
source: add it and wire `fileRef` per
[extract-document-node.md](extract-document-node.md). Never mix the two on
one flow: the next compile overwrites what the commands wrote.

Both routes need the same taxonomy, and
[extract-document-taxonomy.md](extract-document-taxonomy.md) is where it is designed and
written. Write it without ids on either route: every field group and field
must carry a stable id, and both `nodes schema set` and compile mint them.
Compile keeps an id the source carries. For an entry with none it takes the
id the `.flow` it overwrites has for the same name (a group by its key, a field
by its name within that group), else mints one from that name, so a recompile
or an unrelated edit keeps it. It prints what it kept and minted:

```text
compile: "extract" taxonomy ids: 1 group and 2 field id(s) kept, 0 group and 1 field id(s) minted
```

Matching is by name, so a rename mints a new id and detaches what is stored
against the old one. Before a rename, copy the entry's `x-uipath-field-id`
(or `x-uipath-field-group-id`) from the compiled `.flow` onto the renamed entry
in the source; decompile prints them, so a decompiled source already has them.
Treat a minted count after a rename as a dropped id, as `set`'s
`FieldIdsMinted` ([Reading the output](extract-document-taxonomy.md#reading-the-output)):
restore the id and recompile. On an SDK
without builder-sdk#2054, the factory emits the `schema` verbatim and `flow
validate` warns about every missing id; author with the CLI there.

## Schema and outputs

`schema` is the extraction taxonomy: an object with `prompt` (the overall
instructions) and `outputSchema` (the field groups and the field types they
reference). It is emitted as the node's `schemaDocument`. `check` refuses the
content problems `nodes schema set` refuses, each under its own code. A bare
JSON-Schema object (`properties` alone) or the legacy `{taxonomy, fieldTypes}`
form is only a warning there (`EXTRACT_TAXONOMY_BARE`, `_LEGACY`), as in `flow
validate`, but `set` refuses both and the processor gets no fields: fix either
warning before compiling. The codes are in
[When it refuses](extract-document-taxonomy.md#when-it-refuses). When `check`
reports none of these for a broken taxonomy, the SDK is older (no
builder-sdk#2055) and `flow validate` only warns about a wrong shape. The format, with a worked example, is
in [extract-document-taxonomy.md](extract-document-taxonomy.md).

Classification lands at `out('classify', ...)`. What the node emits at run time
is a processed document, with the extracted values at `result.output`, one
property per field group holding its fields, and their page provenance under
`result.attribution` ([Reading what it extracts](extract-document-node.md#reading-what-it-extracts)).
Read a value with `out('extract', 'result.output.<group>.<field>')`. `check`
verifies the processed document's fixed keys (`version`, `type`, `result`,
`taxonomy`, `metadata` and the keys under them): a read of a key the document
does not have is `EXTRACT_READ_UNKNOWN_FIELD`, with the spelling to use.
`ExtractionResult` is one of those keys: it is the published-model node's
shape ([ixp.md](ixp.md)), not this one. Group and field names under
`result.output` are not checked against the taxonomy, so a misspelt one
(`result.output.Invoice.Totl`) still passes `check`. Copy them from the
taxonomy.

## Evidence boundary

Both calls hit real document-understanding services — no local rung runs a
model. Offline `validate` proves the emitted shape (fileRef wiring, the
taxonomy, the classify `success` port); classification quality and extraction
values are platform evidence.
