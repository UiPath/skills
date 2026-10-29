# Document classify and Dynamic Extract

*Exact signatures, fields, and defaults: `documentClassify()` and `dynamicExtract()`.*

Two document steps that need no published IxP project: classification
(`uipath.document.classify`) labels a document, and Dynamic Extract
(`uipath.ixp.extract-document-builder`, named Extract document) pulls fields
against a taxonomy you author INLINE. For a published project's trained fields,
use `ixpExtract` ([ixp.md](ixp.md)) instead.

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

Two routes author Dynamic Extract — see
[Two ways to author Dynamic Extract](#two-ways-to-author-dynamic-extract).

## Two ways to author Dynamic Extract

**The SDK factory**, `dynamicExtract()`, is the route above. It requires a
`model` with `modelName` and `folderKey` — copy them from the tenant, never
construct them. The node itself does not use them: it runs the taxonomy it
carries, and the runtime picks what to run from `inputs.processorKey`. The
requirement is the factory's, inherited from `ixpExtract`'s shape, so a user
with no published IxP project cannot call it at all.

**The CLI commands** author the same node with no model deployment. Use
[extract-document-node.md](extract-document-node.md) to establish the tenant has the node,
add it, and wire `fileRef`.

Both routes need the same taxonomy, and
[extract-document-taxonomy.md](extract-document-taxonomy.md) is where it is designed and
written. One difference matters when choosing: every field group and field in
the taxonomy must carry a stable id, and `nodes schema set` mints those for
you, while a `schema` passed to the factory is emitted verbatim and must
already have them or `flow validate` fails.

## Schema and outputs

`schema` is the extraction taxonomy: an object with `prompt` (the overall
instructions) and `outputSchema` (the field groups and the field types they
reference). It is emitted as the node's `schemaDocument`, and `flow validate`
rejects a node whose `schemaDocument` is any other shape, so a bare JSON-Schema
object with `properties` alone does not work here. The format, with a worked
example, is in [extract-document-taxonomy.md](extract-document-taxonomy.md).

Classification lands at `out('classify', ...)`. The extracted values land at
`out('extract')` under `result.output`, one property per taxonomy field; the
port itself carries the whole processed document, with the values' page
provenance alongside them under `result.attribution`. `ExtractionResult` is the
published-model node's output shape ([ixp.md](ixp.md)), not this one's.

## Evidence boundary

Both calls hit real document-understanding services — no local rung runs a
model. Offline `validate` proves the emitted shape (fileRef wiring, the
taxonomy, the classify `success` port); classification quality and extraction
values are platform evidence.
