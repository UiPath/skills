# Summarize

*Exact signatures, fields, and defaults: `summarize()`.*

Reads an attachment and produces a summary given a prompt.

Signature: `summarize({ attachment, prompt, returnCitations? })`

`attachment` and `prompt` are both required. `check` reports a missing or blank one as
`PATTERN_NO_ATTACHMENT` / `PATTERN_NO_PROMPT`, and `flow validate` refuses the node (`REQUIRED_FIELD`).

```ts
.step('digest',
  summarize({
    attachment: out('previousNode', 'document'),
    prompt: 'Summarize decisions and owners.',
    returnCitations: true
  }))
```

## At a glance

Summarize reads a document; Batch transform ([batch-transform.md](batch-transform.md)) enriches a CSV into a new file.

```ts
.step('digest', summarize({ attachment: out('start', 'document'),
  prompt: 'Summarize the decisions and owners.',
  returnCitations: true }))
```

Request citations only when the scenario needs them.

## General

- Error **460005** can be transient; retry it once before classifying the failure
