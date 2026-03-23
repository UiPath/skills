# Activities

Activities are pre-built actions available for each connector (e.g., "Send Message", "Create Issue"). They represent specific operations the connector supports. Activities include both **actions** (non-trigger) and **triggers** (event listeners).

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

---

## List Activities (Non-Trigger)

```bash
uip is activities list "<connector-key>" --format json
```

This lists **non-trigger activities only** (actions, not event listeners).

## List Trigger Activities

```bash
uip is activities list "<connector-key>" --triggers --format json
```

The `--triggers` flag filters to **trigger activities only** (`isTrigger=true`). These represent events the connector can fire (e.g., "Record Created", "Record Updated").

The **Operation** field on trigger activities indicates the trigger type:
- **CREATED** / **UPDATED** / **DELETED** — CRUD event triggers (require an intermediate "objects" step to discover which objects support the operation)
- Other values — custom event triggers (skip directly to metadata)

> When a trigger activity is selected, proceed to [triggers.md](triggers.md) for the trigger metadata workflow.

## Response Fields

| Field | Description |
|---|---|
| **`Name`** | Activity identifier |
| `DisplayName` | Human-readable name (e.g., "HTTP Request", "Send Message") |
| `Description` | What the activity does |
| **`ObjectName`** | The resource object this activity operates on (use as `<object-name>` in trigger describe for non-CRUD triggers) |
| `MethodName` | HTTP method used (GET, POST, etc.) |
| **`Operation`** | Operation type — for triggers, this is the event type (CREATED, UPDATED, DELETED, or custom) |
| `IsCurated` | Whether this is a curated/recommended activity |

---

## When to Use Activities vs Resources vs Triggers

- **Activities** = named actions (e.g., "Send Email"). Discovered via `is activities list`.
- **Triggers** = event listeners (e.g., "Record Created"). Discovered via `is activities list --triggers`. Metadata via `is triggers objects` / `is triggers describe`. See [triggers.md](triggers.md).
- **Resources** = data objects with CRUD (e.g., "Account"). Discovered via `is resources list`. Executed via `is resources execute <verb>`.

> After listing activities, present the available actions to the user. Activities provide context for what a connector can do — use this to guide which resource operations, triggers, or workflow actions to pursue.
