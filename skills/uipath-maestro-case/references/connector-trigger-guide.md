# Connector Trigger Resolution Guide

Read this file only for connector-backed case-start triggers, in-stage
`wait-for-connector` tasks, or connector condition rules. It converts the
normalized SDD connector intent into a verified spec input. JSON lowering lives
in [connector-trigger-impl.md](connector-trigger-impl.md).

All three targets share the trigger TypeCache, connection resolution, one
read-only spec call, reference resolution, and required-parameter gate.

## Resolution Pipeline

### 1. Find the trigger in TypeCache

Pull the registry once if
`~/.uip/case-resources/typecache-triggers-index.json` is absent. Match the SDD
by exact display name, connector key, or event operation and retain
`uiPathActivityTypeId`. A missing cache after pull or zero exact matches is an
unresolved resource handled by the single batched gate in
[registry-discovery.md](registry-discovery.md).

Never fuzzy-select a connector definition. A placeholder is allowed only after
the user chooses the grouped fallback.

### 2. Resolve the connection

```bash
uip maestro case registry get-connection \
  --type typecache-triggers \
  --activity-type-id "<uiPathActivityTypeId>" \
  --output json
```

If the SDD provides a concrete connection identity/name, require an exact
match. Otherwise ask the user to select an available connection or create one;
do not auto-select even a singleton. Connection creation follows
[connector-integration.md](connector-integration.md).

For entity-typed Curated triggers, resolve the placeholder object through
`uip is triggers objects`. For GenericTrigger definitions, discover objects
through `uip is resources list/describe`. In both cases pass the concrete
`--object-name`; omission can surface only as an opaque spec-fetch error.

### 3. Discover the trigger contract

```bash
uip maestro case spec --type trigger \
  --activity-type-id "<uiPathActivityTypeId>" \
  --connection-id "<connection-id>" \
  --object-name "<object-when-required>" \
  --skip-case-shape \
  --output json
```

Retain:

- `inputs.eventParameters[]`, including `required`, defaults, enum, and
  reference metadata;
- `outputs.responseFields[]`;
- `operation.eventMode`;
- filter capability and `filter.fields[]`;
- `references[]` and their emitted discovery commands;
- diagnostics/fallbacks that affect correctness.

### 4. Resolve reference fields

Run each spec-provided `discoverCommand` exactly, using the selected connection.
Match the SDD display value and retain its lookup value. Reference IDs are
connection-scoped: never reuse one from a different connection. Follow
pagination until found or exhausted. Ambiguous/no matches require user input;
never guess.

### 5. Validate required event parameters (hard gate)

Every required event parameter must have a literal, a freshly resolved
reference ID, or an explicit default. Ask for all missing values in one grouped
question. Do not lower a connector target with a missing required parameter.

### 6. Map SDD input intent

- A name in `eventParameters[]` configures what the trigger monitors and must
  be resolved before lowering.
- A name in `filter.fields[]` narrows which events fire and may be a literal or
  runtime variable expression.
- A name in neither contract is a mismatch; return it to Planner or ask for a
  disambiguation instead of inventing a mapping.

### 7. Build the spec input

```json
{
  "eventParameters": {
    "parentFolderId": "<resolved-id>"
  },
  "filter": {
    "groupOperator": "And",
    "filters": [
      {
        "id": "subject",
        "operator": "Contains",
        "value": {
          "isLiteral": true,
          "rawString": "\"urgent\"",
          "value": "urgent"
        }
      }
    ]
  }
}
```

Omit absent blocks. Only use filter field IDs and operators returned by the
spec. The CLI automatically ANDs required event parameters into its mandatory
filter; never duplicate those clauses in the user filter.

## Runtime-variable filters

The FilterTree compiler accepts literal clauses. For a runtime value such as
`=vars.urgentKeyword`:

1. retain the non-literal clause in normalized resolution evidence;
2. omit it from the CLI FilterTree payload;
3. let the CLI compile literals and the mandatory parameter filter;
4. after spec generation, append the dynamic clause to both compiled filter
   sinks using the canonical template-literal form.

String operand:

```text
=js:`(<mandatory>) && (contains(subject, '${vars.urgentKeyword}'))`
```

Numeric operand:

```text
=js:`(<mandatory>) && (amount > ${vars.minimumAmount})`
```

Preserve the mandatory prefix. String substitutions require quotes; numeric and
boolean substitutions do not.

## Trigger filter sinks

The full `case spec --input-details` call populates three coordinated sinks:

| Sink | Content |
|---|---|
| `essentialConfiguration.filter` in metadata configuration | Design-time user FilterTree |
| `activityPropertyConfiguration.filterExpression` | Compiled mandatory + user expression |
| `body.filters.expression` | Same compiled runtime expression |

When dynamic clauses require a post-spec rewrite, keep the two compiled
expression sinks identical.

## Normalized resolution evidence

The entry in `case-build/registry-resolved.json` must retain:

```json
{
  "taskType": "wait-for-connector",
  "activityTypeId": "<id>",
  "connectionId": "<id>",
  "connectorKey": "<key>",
  "objectName": "<object-or-null>",
  "eventOperation": "<operation>",
  "eventMode": "polling|webhooks",
  "inputValues": { "eventParameters": {} },
  "filter": null,
  "outputs": [],
  "status": "resolved"
}
```

Do not put credentials or tenant dumps in this evidence. Continue immediately
to [connector-trigger-impl.md](connector-trigger-impl.md); resolution alone does
not produce a runnable connector node.

<!-- END: connector-trigger-guide.md -->
