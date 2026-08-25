# Integration Service Presentation Rules

When a connection resource file is available (see "Connection Resource File" in [overview.md](./overview.md) for field reference):

- **Connections** — display as `resource.name` + `spec.connectorName`. Format: "**{resource.name}** ({spec.connectorName})". Show `resource.key` (connection ID) only when needed for commands.
- **Connectors** — use `spec.connectorName`, never `spec.connectorKey` or activity package names
- **Connection owner** — use `resource.name`
- **Connection type** — use `spec.authenticationType` when describing how the user needs to authenticate

When no connection resource file is available, resolve from the connections API (`uip is connections list`).

General rules:
- **Do NOT infer connector names from activity package names** — they differ. Always resolve from the connection resource file or the connections API.
- **Activities** — use the activity display name from the connector, not the internal operation ID
