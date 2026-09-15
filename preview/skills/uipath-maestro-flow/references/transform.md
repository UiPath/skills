# Transform

*Exact signatures, fields, and defaults: [`transform()`](api.md#transform-function).*

Transform applies filter, map, or group-by operations to an array.

Signature:
`transform({ collection, operations, variant?: 'filter' | 'map' | 'group-by' })`.
Operations are the SDK's `filter`, `map`, and `groupBy` discriminated shapes.

```ts
.step('active', transform({ variant: 'filter', collection: input('rows'),
  operations: [{ type: 'filter', filters: [
    { field: 'status', condition: 'equals', value: 'active' },
  ] }] }))
```

## Choosing the shape

Prefer a named variant for one standard operation so the canvas communicates
intent. Use generic Transform for a chain; use Script when the requested
calculation does not fit the transform operations.

## Data-dependent review

Operations run in order. A map can remove a field that a later filter or group
expects, and a plausible misspelled field on untyped input can yield empty
rows without a structural failure. Review the chain against representative
items and assert the resulting values, not merely that the node ran.

Omit `variant` for the generic node. Set `variant: 'map' | 'filter' | 'group-by'`
for a single-purpose node; `operations` must then contain exactly one entry.
