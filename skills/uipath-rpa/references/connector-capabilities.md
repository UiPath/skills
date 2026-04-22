# Discover Connector Capabilities (For IS/Connector Workflows)

When a workflow involves an Integration Service connector (Salesforce, Jira, ServiceNow, Slack, etc.), explore the connector before writing XAML. For the full end-to-end authoring flow, see [is-connector-xaml-guide.md](is-connector-xaml-guide.md).

## Prerequisite: `uip login`

All `uip is *` commands require an authenticated session. They fail silently (with a generic "Not logged in" error) otherwise.

```bash
uip login                                                       # production (cloud.uipath.com)
uip login --authority https://alpha.uipath.com/identity_        # alpha
uip login --authority https://staging.uipath.com/identity_      # staging
```

If you need the user to authenticate, ask them to type `! uip login` so the token lands in the current session.

## Discovery Commands

```bash
# List connectors available to the tenant (find the connector key):
uip is connectors list --output json

# What activities does a specific connector offer? (get activity names + method + operation)
uip is activities list <connector-key> --output json

# What data objects/resources does it expose?
uip is resources list <connector-key> --output json

# Describe a specific operation's schema (fields, types, required flags, enum values):
uip is resources describe <connector-key> <operation-name> --operation Create --output json
```

`resources describe` is the authoritative field schema — **never guess field names**. The response includes a `metadataFile` path like `~/.uipath/cache/integrationservice/<connector>/_static/<operation>.Create.json`. Read that JSON directly for the full `parameters` / `requestFields` / `responseFields` list.

Note: it's `resources describe` (not `activities describe`). The `activities` subcommand only has `list`.

## Finding an Activity's Type ID (for XAML generation)

For hand-authored XAML, the IS `ConnectorActivity` element needs a `UiPathActivityTypeId` GUID. Get it via `find-activities`:

```bash
uip rpa find-activities --query "<search terms>" --project-dir "<PROJECT_DIR>" --output json
```

In the response, each result's `activityTypeId` field is the GUID to pass to:

```bash
uip rpa get-default-activity-xaml \
    --activity-type-id "<TYPE_ID>" \
    --connection-id "<CONN_ID>" \
    --project-dir "<PROJECT_DIR>" --output json
```

**`--activity-type-id` is mandatory for IS dynamic activities** — without it, the default XAML comes back empty (`Configuration={x:Null}`, no fields) and isn't runnable.

## Connection Management

**Check if a connection exists:**
```bash
uip is connections list <connector-key> --output json
```

**If no connection exists**, options:
1. **Create one** (opens an OAuth browser flow for the user): `uip is connections create <connector-key>`
2. **Placeholder** — drop the XAML with a placeholder `ConnectionId="00000000-0000-0000-0000-000000000000"` and tell the user to configure the connection in Studio before running.

**Verify a connection is active:**
```bash
uip is connections ping <connection-id>
```

If the ping fails, offer to re-authenticate: `uip is connections edit <connection-id>`.

## Next: Generate the XAML

Once you have `connector-key`, `activityTypeId`, `connection-id`, and the field schema, follow [is-connector-xaml-guide.md](is-connector-xaml-guide.md) for the complete authoring flow with a worked example.
