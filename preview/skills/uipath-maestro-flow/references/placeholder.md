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

## Unknown node types

`mock()` is a deliberate placeholder — a node that stands in for work not yet
decided. It is NOT the way to carry a node the SDK has no factory for: it
compiles to `core.logic.mock`, so the original type is gone.

For that, use `rawNode({ nodeType, version, manifest, inputs? })`. It carries
the definition the platform serves for that `nodeType@version`, so the node
keeps its identity and its inputs:

```ts
.step('exotic', rawNode({
  nodeType: 'uipath.exotic.thing', version: '2.1',
  manifest: exoticManifest,        // verbatim from `registry get`
  inputs: { where: input('scope') },
}))
```

Two rules. **The manifest must be real** — an exact copy of what
`uip maestro flow registry get <nodeType>` returns (after
`registry pull --force`, since registry reads are cached). A hand-written
manifest validates locally and fails on the tenant, which resolves the node
against its own catalog. **Prefer a typed factory** whenever one exists: it
carries the family's check rules, its defaults and its output contract, none of
which a raw node can know.

**Never for a connector.** A `uipath.connector.*` node type is refused by
`check` (`RAW_NODE_CONNECTOR`) and by `compile`. A raw node keeps its inputs
verbatim, so the emitted connector node has no `inputs.detail` and no
connection binding: `uip maestro flow validate` only warns ("Connector is not
configured") and the run can never reach Integration Service. Measured on the
eval archive, every Data Fabric flow authored this way failed its checker. The
situation that tempts it — `compile` refusing a body field as `unknown input`
because the static library does not carry it — is what
`npx flow-sdk registry prepare <key> <action>` exists for (add
`-f entityName=<Entity>` for a Data Service operation); see the
[parent-field loop](connector-params.md#schema-dynamic-operations-the-parent-field-loop).

`decompile` emits `rawNode(...)` for any node type it cannot name, hoisting the
manifest to a `const` beside the flow. So `mock()` in decompiled source means
the flow really contains a placeholder.
