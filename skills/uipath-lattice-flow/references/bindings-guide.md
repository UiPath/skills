# Bindings Guide

The `bindings_v2.json` file is a project-level file that maps connector nodes to their Integration Service connections at runtime.

---

## OOTB-Only Flows

For flows that use only OOTB nodes (triggers, scripts, HTTP, logic, etc.), the bindings file is empty:

```json
{
  "bindings": []
}
```

Most flows built with this skill will use this empty format.

---

## When Bindings Are Needed

- **Connector nodes** (`uipath.connector.*`) require binding entries to resolve their Integration Service connections at runtime
- **Resource nodes** (RPA workflow, agent, API workflow) do NOT use `bindings_v2.json` -- they resolve connections via `model.bindings` in the node instance

---

## Binding Entry Format

Each binding entry maps a connection property to a value:

```json
{
  "id": "bXk9mNpQr",
  "resourceKey": "<CONNECTION_KEY>",
  "propertyAttribute": "<PROPERTY_NAME>",
  "value": "<VALUE>"
}
```

| Field | Description |
|-------|-------------|
| `id` | `b` + 8 random alphanumeric characters |
| `resourceKey` | The connection identifier from the connector's schema |
| `propertyAttribute` | The property on the connection to bind |
| `value` | The resolved value for that property |

---

## Deduplication

Bindings are deduplicated by the `resourceKey` + `propertyAttribute` pair. Do not add multiple entries with the same combination.
