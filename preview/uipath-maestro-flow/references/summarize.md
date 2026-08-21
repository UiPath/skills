# Summarize

*Behavior and worked examples. Exact signatures, fields, and defaults: [`summarize()`](api.md#summarize-function).*

Reads an attachment and produces a summary given a prompt.

Signature: `summarize({ attachment, prompt, returnCitations? })`

```ts
.step('digest',
  summarize({
    attachment: out('previousNode', 'document'),
    prompt: 'Summarize decisions and owners.',
    returnCitations: true
  }))
```

## General

- Error **460005** can be transient; retry it once before classifying the failure
