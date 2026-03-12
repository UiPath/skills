# Activities

Activities are pre-built actions available for each connector (e.g., "Send Message", "Create Issue"). They represent specific operations the connector supports.

> Full command syntax and options: [uipcli-commands.md — Integration Service](../uipcli-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

---

## List Activities

```bash
uipcli is activities list "<connector-key>" --format json
```

This lists **non-trigger activities only** (actions, not event listeners).

## Response Fields

| Field | Description |
|---|---|
| **`Name`** | Activity identifier |
| `DisplayName` | Human-readable name (e.g., "HTTP Request", "Send Message") |
| `Description` | What the activity does |
| `ObjectName` | The resource object this activity operates on |
| `MethodName` | HTTP method used (GET, POST, etc.) |
| `Operation` | Operation type (N/A for method-based activities) |
| `IsCurated` | Whether this is a curated/recommended activity |

---

## When to Use Activities vs Resources

- **Activities** = named actions (e.g., "Send Email"). Discovered via `is activities list`.
- **Resources** = data objects with CRUD (e.g., "Account"). Discovered via `is resources list`. Executed via `is resources execute <verb>`.

Some connectors have both. Always check both when discovering capabilities.

> After listing activities, present the available actions to the user. Activities provide context for what a connector can do — use this to guide which resource operations or workflow actions to pursue.
