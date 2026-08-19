# Placeholder

*Exact signatures, fields, and defaults: [`mock()`](api.md#mock-function).*

A placeholder says that a real capability belongs at this point in the graph
but does not exist yet.

Signature: `mock()`.

```ts
.step('extractInvoice', mock())
.step('continueWithInput', script({
  code: 'return $vars.assumedInvoiceId;' }))
```

Use a real script when downstream work needs temporary fixed data; that script
has the same behavior locally and after deployment. Use a placeholder only to
make a missing capability visible. Do not use it merely to disable a step or as
the only work in a finished Flow.
