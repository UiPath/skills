# Batch Transform

*Exact signatures, fields, and defaults: [`batchTransform()`](api.md#batchtransform-function).*

Adds AI-generated columns to a CSV and returns a new file attachment.

Signature: `batchTransform({ attachment, prompt, outputColumns, enableWebSearchGrounding? })`

```ts
 .step('categorizeRows',
   batchTransform({
     attachment: out('start', 'csvFile'),
     prompt: 'Classify each row by category and write a one-line summary.',
     outputColumns: [
       { name: 'Category', description: 'One of: Utility, Software, Travel, Other' },
       { name: 'Summary',  description: 'Plain-English one-line summary of the row' },
     ],
   }))
```

## General

- Error **460005** can be transient; retry it once before classifying the failure
