# Connector Implementation

Connector-backed BPMN elements are Integration Service elements. Use the
current Integration Service implementation guide for shared Flow/BPMN IS CLI
behavior, registry fallback, live metadata, connection-scoped references,
filters, custom fields, trigger metadata, and generated package resources:

- [../integration-service/impl.md](../integration-service/impl.md)

This file remains as a compatibility route for older references.

## Model-owned implementation

The model may edit:

- Standard BPMN wrapper elements around connector intent.
- Variables and mappings that consume connector outputs.
- Error, timeout, and fallback paths.
- Diagram geometry.

## CLI-owned implementation

The CLI or registry-backed tool must generate or enrich:

- `Intsvc.*` `uipath:activity` or `uipath:event` payloads.
- Connector key, operation/event, object, and version context.
- Connection binding expressions and `bindings_v2.json` resources.
- Dynamic input/output schemas and generated output metadata.
- Trigger property bindings for connector triggers.

Do not copy Flow node JSON or `uip maestro flow node configure` output into
BPMN. BPMN enrichment must emit BPMN XML plus generated package JSON using the
same Integration Service metadata contract.

## Validation expectations

- Every executable connector element has enriched context, inputs, outputs, and schemas.
- Binding expressions resolve.
- Required parameters and filters are present.
- No tenant URLs, connection IDs, folder keys, or copied exported metadata are committed.
