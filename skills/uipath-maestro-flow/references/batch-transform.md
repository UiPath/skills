# Batch Transform

*Exact signatures, fields, and defaults: `batchTransform()`.*

`batchTransform({ attachment, prompt, outputColumns, enableWebSearchGrounding? })` adds AI-generated columns to a CSV and returns a new file attachment.

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

Use Summarize ([summarize.md](summarize.md)) for documents; request web grounding only when needed.

## General

- **460005** may be transient; retry once before classifying the failure.