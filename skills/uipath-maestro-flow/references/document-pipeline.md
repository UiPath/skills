# Document classify and Extract document

*Exact signatures, fields, and defaults: `documentClassify()` and `dynamicExtract()`.*

Two document steps that need no trained IxP fields: classification
(`uipath.document.classify`) labels a document, and the Extract document node
(`uipath.ixp.extract-document-builder`) pulls fields against a taxonomy you
author INLINE — though the `dynamicExtract()` factory still needs a published
model's identity ([Two ways to author it](#two-ways-to-author-it)). For a
published project's trained fields, use `ixpExtract` ([ixp.md](ixp.md)) instead.

Signatures: `documentClassify({ fileRef, pageRange?, splitPages?, modelConfig? })`;
`dynamicExtract({ fileRef, schema, model, pageRange?, modelConfig? })`.

```ts
.input({ file: types.file })
.step('classify', documentClassify({ fileRef: input('file'), splitPages: true }))
.step('extract', dynamicExtract({
  fileRef: input('file'),
  schema: invoiceTaxonomy,
  model: { modelName: 'invoiceixp-cef0d447-ixp',
    folderKey: 'c4359cde-55f0-4f0e-9322-c6cdce74ab4c' },
}))
.step('total', script({ code: 'return $vars.extract.output.result.output;' }))
```

## At a glance

Classify a document (`uipath.document.classify`), or extract fields against an
INLINE taxonomy (`uipath.ixp.extract-document-builder`) instead of a published
IxP project's trained fields.
Signatures: `documentClassify({ fileRef, pageRange?, splitPages?, modelConfig? })`;
`dynamicExtract({ fileRef, schema, model: { modelName, folderKey, ... }, pageRange? })`.

```ts
.step('classify', documentClassify({ fileRef: input('file'), splitPages: true }))
.step('extract', dynamicExtract({ fileRef: input('file'), schema: invoiceTaxonomy,
  model: { modelName: 'invoiceixp-cef0d447-ixp', folderKey: '<folder-guid>' } }))
```

## Two ways to author it

**The SDK factory**, `dynamicExtract()`, is the call above, and it carries
limits the node itself does not have. It requires a `model` with a published
deployment's `modelName` and `folderKey` — copy them from the tenant, never
construct them — although the node never reads them: it runs the taxonomy it
carries, through `inputs.processorKey`, which exists only after the flow is
saved once in Studio Web ([Making it actually extract](extract-document-node.md#making-it-actually-extract)).
Decompiling a flow that holds this node and compiling it back also throws on
the missing `model`. So the factory is usable only where a flow must stay in
TypeScript source and a published model's identity is to hand; everywhere else,
use the CLI.

**The CLI commands** author the same node with no model deployment, and are the
route the router row and both guides point at: add it and wire `fileRef` per
[extract-document-node.md](extract-document-node.md).

Both routes need the same taxonomy, and
[extract-document-taxonomy.md](extract-document-taxonomy.md) is where it is designed and
written. One difference decides between them: every field group and field must
carry a stable id, and `nodes schema set` mints those for you, while a `schema`
passed to the factory is emitted verbatim — `flow validate` warns about each
missing id, and the remedy its warning names, `nodes schema set`, is overwritten
by the next compile. On this route the ids have to be written into the source,
which the taxonomy guide warns against because hand-managed ids are how
annotations detach from fields.

## Schema and outputs

`schema` is the extraction taxonomy: an object with `prompt` (the overall
instructions) and `outputSchema` (the field groups and the field types they
reference). It is emitted as the node's `schemaDocument`. `flow validate` only
warns about any other shape, so it will not catch a bare JSON-Schema object
with `properties` alone for you — the format, with a worked example, is in
[extract-document-taxonomy.md](extract-document-taxonomy.md).

Classification lands at `out('classify', ...)`. What the node emits at run time
is a processed document, with the extracted values at `result.output`, one
property per taxonomy field, and their page provenance under
`result.attribution` ([Reading what it extracts](extract-document-node.md#reading-what-it-extracts)).
The two routes embed different typings for it, though: `nodes create` embeds
that current shape, while the SDK factory still embeds the older
`ExtractionResult` shape — so on a factory-built flow, a read of
`result.output` validates with an `EXPRESSION_DIAGNOSTIC` warning until the SDK
catches up. `ExtractionResult` as a runtime shape belongs to the
published-model node ([ixp.md](ixp.md)), not this one.

## Evidence boundary

Both calls hit real document-understanding services — no local rung runs a
model. Offline `validate` proves the emitted shape (fileRef wiring, the
taxonomy, the classify `success` port); classification quality and extraction
values are platform evidence.
