# Integration Service Planning

Integration Service activities and triggers are CLI-owned or CLI-enriched. The model may plan the node and surrounding BPMN structure, but it must not invent connector metadata, connection identifiers, dynamic schemas, or binding resources.

## When to use

Use this plugin reference when a BPMN process needs:

- A connector activity.
- A connector trigger.
- A wait-for-event shape backed by Integration Service.
- Unified HTTP or connector-authenticated HTTP behavior.
- Dynamic input/output schemas from connector metadata.

For plain connectionless HTTP calls where the workflow owns the URL, method,
payload, and parsing, record the intent during pass 1 and read
[task-recipes/http-request.md](../../task-recipes/http-request.md) after the
skeleton is chosen, before deciding whether the node is executable or only
draft intent.

## Planning steps

1. Identify the connector, operation/event, object, and user-visible intent.
2. Determine whether the element is a trigger, wait event, connector activity, connector-authenticated HTTP call, or plain connectionless HTTP call.
3. Check whether the process can proceed with a draft placeholder or must stop until enrichment is available.
4. Record required user decisions: connector, connection, folder/resource scope, operation, filters, required parameters, and output variables.
5. Keep the surrounding BPMN structure model-authored: start/event/task placement, sequence flows, gateways, error handling, and diagrams.
6. Hand the Integration Service element to CLI enrichment before validation for upload/debug/publish.

## Live enrichment expectation

Executable Integration Service nodes require live registry-backed enrichment for the target tenant. Static examples and sanitized fixtures demonstrate shape only; they are not reusable connector metadata.

- Use current CLI/registry data for connector keys, operation/event names, object metadata, connection availability, trigger properties, filters, parameter schemas, and generated output schemas.
- Treat stale exported metadata, copied tenant identifiers, or fixture values as non-authoritative.
- If live enrichment is unavailable, keep the node as draft intent and stop before Operate. A draft may include a canonical `uipath:type value="Intsvc.<Variant>"` shell with placeholder strings, but not real connector metadata, connection bindings, dynamic schemas, or generated resource references.

## Model may draft

- A placeholder service task, start event, or intermediate event with a stable element ID.
- A draft `uipath:activity` or `uipath:event` shell carrying `uipath:type value="Intsvc.<Variant>"` and placeholder string `uipath:input` values. See [impl.md](impl.md#safe-placeholder-shape) and [../../../../shared/wrapper-shells.md](../../../../shared/wrapper-shells.md).
- Public-safe display naming.
- Surrounding sequence flows, gateways, boundary errors, and variable mappings.
- A `README.md` (or `notes.md`) inside the project that lists the
  CLI-owned blockers verbatim. The list must contain at minimum these
  exact phrases: `connection binding`, `dynamic schemas`,
  `bindings_v2.json`, and `package metadata`. See
  [impl.md](impl.md#draft-handoff-notes) for the full template.

## CLI must provide

- Connector key and operation/event metadata.
- Connection binding and resource metadata.
- Context fields such as object name, activity, operation, filter expression, and trigger properties.
- Dynamic schemas and generated output metadata.
- `bindings_v2.json` entries and resource metadata.
- Validation that the selected connection and operation are available.

## Stop conditions

Stop before real run/upload if:

- No selected connection exists.
- The connector operation is unknown.
- Required parameters are not resolved.
- Generated schemas are missing for an executable element.
- The element contains pasted private connection or tenant identifiers.
