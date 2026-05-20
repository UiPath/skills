# Connector Planning

Connector-backed activities and triggers are Integration Service-owned. Use
the current Integration Service planning guide for discovery, registry refresh,
connection checks, object/activity metadata, trigger metadata, and fallback
rules:

- [../integration-service/planning.md](../integration-service/planning.md)
- [../integration-service/impl.md](../integration-service/impl.md)

This file is only a compatibility route for older references.

## When to use

- Connector activities.
- Connector triggers.
- Connector-backed waits.
- Unified HTTP or authenticated HTTP through Integration Service.
- Dynamic connector schemas.

## Planning steps

1. Identify connector, operation or event, object, filters, inputs, outputs, and failure behavior.
2. Decide if the connector is a start trigger, intermediate wait, service task, or boundary behavior.
3. Follow the Integration Service planning guide linked above for registry
   fallback, connection verification, activity/object selection, required-field
   discovery, and trigger metadata.
4. Plan surrounding BPMN structure and variables.
5. Record required operator choices: connection, folder scope, operation, filters, and output variable names.
6. Leave enrichment to the CLI before validation for upload/run.

## Model may draft

- Placeholder BPMN wrappers with stable IDs and public-safe labels.
- Surrounding flows, gateways, variables, and error paths.
- Draft notes that describe connector intent.

## CLI must provide

- Connector metadata, operation/event metadata, connection binding, trigger properties, schemas, and generated binding resources.

## Stop conditions

Stop before Operate if the connector element is not CLI-enriched or if copied private connection metadata appears in the source.
