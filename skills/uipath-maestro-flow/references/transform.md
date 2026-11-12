# Transform

*Exact signatures, fields, and defaults: `transform()`.*

Transform applies `filter`, `map`, or `group-by` to an array without custom JavaScript.

Signature:
`transform({ collection, operations, variant?: 'filter' | 'map' | 'group-by' })`.
Operations are the SDK's `filter`, `map`, and `groupBy` discriminated shapes.

```ts
.step('active', transform({ variant: 'filter', collection: input('rows'),
  operations: [{ type: 'filter', filters: [
    { field: 'status', condition: 'equals', value: 'active' },
  ] }] }))
```

## At a glance

Use a named variant for one operation, generic Transform for a chain, and Script when the calculation does not fit these operations.

## Choosing the shape

Prefer a named variant for one standard operation so the canvas communicates intent: set `variant: 'map' | 'filter' | 'group-by'` with exactly one `operations` entry. Omit `variant` for the generic node.

## Data-dependent review

Operations run in order. A map may remove fields needed by a later filter or group, and a misspelled field on untyped input may yield empty rows without structural failure. Review chains against representative items and assert resulting values, not merely that the node ran.
