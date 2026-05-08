# Connector Implementation

This document defines the implementation boundary for connector-backed BPMN elements.

## Model-owned implementation

The model may edit:

- Standard BPMN wrapper elements around connector intent.
- Variables and mappings that consume connector outputs.
- Error, timeout, and fallback paths.
- Diagram geometry.

## CLI-owned implementation

The CLI or registry-backed tool must generate:

- `Intsvc.*` `uipath:activity` or `uipath:event` payloads.
- Connector key, operation/event, object, and version context.
- Connection binding expressions and `bindings_v2.json` resources.
- Dynamic input/output schemas and generated output metadata.
- Trigger property bindings for connector triggers.

## Validation expectations

- Every executable connector element has enriched context, inputs, outputs, and schemas.
- Binding expressions resolve.
- Required parameters and filters are present.
- No tenant URLs, connection IDs, folder keys, or copied exported metadata are committed.
