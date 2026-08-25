# Document classify and Dynamic Extract

*Exact signatures, fields, and defaults: [`documentClassify()`](api.md#documentclassify-function) and [`dynamicExtract()`](api.md#dynamicextract-function).*

Two document steps that need no published IxP project: classification
(`uipath.document.classify`) labels a document, and Dynamic Extract
(`uipath.ixp.extract-document-builder`) pulls fields against a schema you
author INLINE. For a published project's trained fields, use `ixpExtract`
([ixp.md](ixp.md)) instead.

Signatures: `documentClassify({ fileRef, pageRange?, splitPages?, modelConfig? })`;
`dynamicExtract({ fileRef, schema, model, pageRange?, modelConfig? })`.

```ts
.input({ file: types.file })
.step('classify', documentClassify({ fileRef: input('file'), splitPages: true }))
.step('extract', dynamicExtract({
  fileRef: input('file'),
  schema: { type: 'object', properties: {
    invoiceTotal: { type: 'string', description: 'Grand total' } } },
  model: { modelName: 'invoiceixp-cef0d447-ixp',
    folderKey: 'c4359cde-55f0-4f0e-9322-c6cdce74ab4c' },
}))
.step('total', script({ code: 'return $vars.extract.output.ExtractionResult;' }))
```

## The model identity

Dynamic Extract authors its SCHEMA inline, but execution still runs against a
model deployment: `model.modelName` and `model.folderKey` are REQUIRED (the
platform validator rejects the node without them), with optional `projectId`,
`projectName`, `folderName`, and `versionTag`. Copy them from the tenant —
never construct them.

## Schema and outputs

`schema` is a JSON-Schema object (`type: 'object'` with `properties`, each
usually carrying a `description` the model reads). It is emitted as the node's
`schemaDocument`. Classification lands at `out('classify', ...)`; extraction
results at `out('extract', 'ExtractionResult')`.

## Evidence boundary

Both calls hit real document-understanding services — no local rung runs a
model. Offline `validate` proves the emitted shape (fileRef wiring, schema,
model identity, the classify `success` port); classification quality and
extraction values are platform evidence.
