# Connector capabilities

Read this file when: you are working with Integration Service connectors (Salesforce, Jira, ServiceNow, etc.) and need to discover activities, resources, or manage connections.

## Discover connector capabilities

```bash
# List activities for a connector:
uip is activities list <connector-key> --format json

# List data objects/resources:
uip is resources list <connector-key> --format json

# Describe fields of a specific resource:
uip is resources describe <connector-key> <object-name> --format json
```

## Connection management

```bash
# Check if a connection exists:
uip is connections list <connector-key> --format json

# Verify a connection is active:
uip is connections ping <connection-id>

# Create a new connection (opens OAuth flow):
uip is connections create <connector-key>

# Re-authenticate an expired connection:
uip is connections edit <connection-id>
```

If no connection exists and you cannot create one interactively, use a placeholder GUID (`00000000-0000-0000-0000-000000000000`) and inform the user to configure the connection in Studio.
