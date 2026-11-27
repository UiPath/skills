# Microsoft Teams — Connector Overrides

**Connector key:** `uipath-microsoft-teams`

## Connection Selection Override

### When this override applies

Send-bot-* activity node types:

- `uipath.connector.uipath-microsoft-teams.send-bot-channel-message`
- `uipath.connector.uipath-microsoft-teams.send-bot-direct-message`

Non-bot Teams activities (`send-channel-message`, `send-individual-chat-message`, `create-channel`, etc.) follow the default auto-select rule.

### Why

Send-bot-* activities post messages from a Teams bot identity, not from the user. The connection must be authorized with the Teams bot scope. The personal-workspace default connection is typically authorized without that scope, so silent auto-select binds a connection that fails at runtime with a 403. Asking the user up front lets them pick a bot-scoped connection (or re-authorize the default).

### Behavior

- **Auto-select:** disabled — always present connections to the user.
- **List filter:** none. Use the standard `uip is connections list "uipath-microsoft-teams" --all-folders --output json`.
- **Post-selection verification:** ping. No CLI flag exposes bot-scope state at bind time — verification is deferred to runtime (a 403 surfaces missing scope, then the [Scope-Related Errors](../connections.md#scope-related-errors) recovery applies).
- **Recovery on empty:** standard native-connector recovery (`--refresh`, then prompt to create via `uip is connections create "uipath-microsoft-teams"` — user must consent to the Teams bot scope during OAuth).

### User-facing presentation

Prefix the connection list with: "These activities post messages from a Teams **bot** identity, so the connection needs the bot scope authorized. Pick a connection that has it. If none does, re-authorize via `uip is connections edit <id>` and grant the bot scope during OAuth."
