# Agent Workflow

Follow these steps in order when the user asks to interact with an external service.

## Step 1: Find the Connector

```bash
uipcli is connectors list --filter "<vendor>" --format json
```

| Outcome | Action |
|---|---|
| Native connector found | Use its connector key. Proceed to Step 2. |
| Not found | Fall back to HTTP connector (`uipath-uipath-http`). See [connectors.md](connectors.md). |

---

## Step 2: Find a Connection

```bash
uipcli is connections list "<connector-key>" --format json
```

- **Native**: Pick default enabled connection (`IsDefault: Yes`, `State: Enabled`).
- **HTTP fallback**: Match connection by vendor **Name** (case-insensitive substring).
- **Multiple**: Present options to the user.
- **None**: Ask user to create via `is connections create "<connector-key>"`.

See [connections.md](connections.md) for full selection logic and lifecycle.

---

## Step 3: Ping the Connection

```bash
uipcli is connections ping "<connection-id>" --format json
```

| Result | Action |
|---|---|
| `Enabled` | Healthy. Proceed to Step 4. |
| Fails | Run `is connections edit <id>` to re-authenticate, then ping again. If still fails, ask user to choose another or create new. |

---

## Step 4: Discover Capabilities

```bash
uipcli is activities list "<connector-key>" --format json
```

For resource-based CRUD, also explore resources — **always pass `--connection-id` and `--operation`**:

```bash
uipcli is resources list "<connector-key>" \
  --connection-id "<id>" --operation <Create|List|Retrieve|Update|Delete|Replace> --format json

uipcli is resources describe "<connector-key>" "<object>" \
  --connection-id "<id>" --operation Create --format json
```

See [activities.md](activities.md) and [resources.md](resources.md) for details.

---

## Step 5: Resolve Reference Fields

Check describe output for `referenceFields`. **If none exist, skip to Step 6.**

For each reference field: list the referenced object, collect valid IDs, and present options to the user.

See [resources.md — Reference Fields](resources.md#reference-fields-critical) for the resolution workflow and examples.

---

## Step 6: Execute

```bash
uipcli is resources execute <verb> "<connector-key>" "<object>" \
  --connection-id "<id>" --body '{"field": "value"}' --format json
```

See [resources.md — Execute Operations](resources.md#execute-operations) for the verb table and options.
