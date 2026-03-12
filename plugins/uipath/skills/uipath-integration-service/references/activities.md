# Activities

Activities are pre-built actions available for each connector (e.g., "Send Message", "Create Issue"). They represent specific operations the connector supports.

**Important:** Activities are discoverable via CLI but are executed within UiPath Studio workflows, not directly from `uipcli`. For CLI-executable operations, use [resources](resources.md).

---

## List Activities

```bash
uipcli is activities list "<connector-key>" --format json
```

> Run `uipcli is activities list --help` for all flags.

This lists **non-trigger activities only** (actions, not event listeners).

### Response Fields

| Field | Description |
|---|---|
| `Name` | Activity identifier |
| `DisplayName` | Human-readable name (e.g., "HTTP Request", "Send Message") |
| `Description` | What the activity does |
| `ObjectName` | The resource object this activity operates on |
| `MethodName` | HTTP method used (GET, POST, etc.) |
| `Operation` | Operation type (N/A for method-based activities) |
| `IsCurated` | Whether this is a curated/recommended activity |

---

## When to Use Activities vs Resources

- **Activities** = named actions (e.g., "Send Email"). Discovered via `is activities list`. Executed in Studio workflows.
- **Resources** = data objects with CRUD (e.g., "Account"). Discovered via `is resources list`. Executed via `is resources execute <verb>`.

Some connectors have both. Always check both when discovering capabilities:

```bash
uipcli is activities list "<connector-key>" --format json
uipcli is resources list "<connector-key>" --format json
```

For HTTP connector activities, see [connectors.md — HTTP Connector Fallback](connectors.md#http-connector-fallback).
