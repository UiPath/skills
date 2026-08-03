# uipath-ixp taxonomy-serving mock

Overlay for smoke tasks whose correct path **starts with a read**. Overlays the
base [`mock_template`](../mock_template/README.md) — list it SECOND so its
`mocks/uip` wins:

```yaml
sandbox:
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
    - {type: template_dir, path: ../_shared/mock_template_taxonomy}
```

## Why it exists

The base mock fails every invocation. That is right for a task whose graded
commands are independent, and wrong for one that reads before it writes:

- **A value carried from the taxonomy is unobtainable.** If grading requires
  `fields add --type … --instructions …` with the field's existing type and
  instructions, a failing `get-taxonomy` leaves the agent nothing to carry. An
  agent that declines to invent them stops — the correct call, graded as a fail.
- **A mutation gated on an earlier mutation is wrong to issue.** The skill
  teaches add-before-delete so a failed `fields add` leaves the field where it
  was. If the add fails, withholding the `fields delete` is correct behavior.

Serving the reads makes the graded shape reachable, and lets criteria assert the
carried-over *values* rather than just flag presence.

## Fixture

Project `my_invoices-f1afa9ef-ixp` (`Title` `My_Invoices`):

| Field group      | Fields                                        |
|------------------|-----------------------------------------------|
| `Invoice Header` | Invoice Number, Invoice Date, Total Amount    |
| `Line Items`     | Description                                   |

`Total Amount` is `Monetary Quantity`. Its `moon_form` entry's `field_id` is the
field's own identity and matches no `entity_def` — the type resolves through
`field_type_id`, the distinction the move-a-field recipe calls out.

Served: `projects list`, `projects get`, `projects get-taxonomy`, `fields add`,
`fields delete`. Everything else falls through to the base mock's offline
failure, so a task can still guard against unwanted verbs.

## get-taxonomy is stateful

An agent that re-reads the taxonomy to verify a move sees its own writes, not
stale canned state it would then try to re-apply:

| After | `Invoice Header` | `Line Items` |
|-------|------------------|--------------|
| — | Total Amount | — |
| `fields add` | Total Amount | Total Amount (**new** `field_id`) |
| `fields delete` | — | Total Amount |

The intermediate both-groups state is what the real backend does between add and
delete, and the new `field_id` is why a move drops the field's confirmed labels.
State lives in dot-prefixed marker files beside `calls.log`, so it stays out of
graded globs and CI artifact uploads.

## Constraints

Logging matches the base mock exactly — same `uip ` prefix, same newline
normalization — so anchored `^uip\s+ixp …` criteria keep matching. Change one
and change both. `mocks/uip` must stay mode `755`.
