# Integration Service Implementation

This document defines the implementation boundary for Integration Service BPMN elements.

## Model-owned implementation

The model may edit:

- Standard BPMN wrapper element: service task, start event, intermediate event, boundary event, or receive/wait pattern.
- Stable element ID and public-safe display name.
- Sequence flows and diagram geometry.
- Variables and mappings that consume the eventual output.
- Error handling and retry intent, when specified by the user.

The model must keep any Integration Service service payload as draft intent unless CLI enrichment has supplied the concrete metadata.

## CLI-owned implementation

The CLI or registry-backed tool must generate or enrich:

- `uipath:activity` or `uipath:event` contents for `Intsvc.*` service types.
- `uipath:type` service type and version from supported metadata.
- `uipath:context` fields for connector key, operation, object, connection binding, event name, folder fields, and trigger properties.
- `uipath:input` bodies for request parameters and filter expressions.
- `uipath:output` mappings and dynamic output schemas.
- `uipath:inputSchema` payloads.
- Root `uipath:bindings` entries that point to generated binding resources.
- `bindings_v2.json` resource entries.

## Safe placeholder shape

When enrichment is unavailable, keep the BPMN element structurally visible and mark it as draft in planning notes rather than inventing executable XML. The project should remain in Author state until enrichment completes.

Use synthetic names only, for example `Task_CreateTicket` or `Start_WhenRecordCreated`. Do not use real connection IDs, tenant URLs, folder keys, account-specific resource IDs, or copied metadata from another project.

## Validation expectations

Before Operate, confirm that:

- Every executable Integration Service element has CLI-enriched context, inputs, outputs, and schemas.
- Root binding references resolve.
- Generated package resources exist and are deduped.
- Required filters and parameters are present.
- Trigger property bindings are generated for trigger elements.
- No private IDs are present in files intended for commit.
