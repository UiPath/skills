# Slack — Connector Overrides

**Connector key:** `uipath-salesforce-slack`

## Connection Selection Override

### When this override applies

Slack webhook trigger node types — explicit allow-list (not a blanket `.trigger.*` wildcard):

- `uipath.connector.trigger.uipath-salesforce-slack.message-received-in-slack`
- `uipath.connector.trigger.uipath-salesforce-slack.channel-message-posted`
- `uipath.connector.trigger.uipath-salesforce-slack.chat-message-posted`
- `uipath.connector.trigger.uipath-salesforce-slack.chat-message-updated`
- `uipath.connector.trigger.uipath-salesforce-slack.reaction-added-in-slack`
- `uipath.connector.trigger.uipath-salesforce-slack.member-joined-a-slack-channel`
- `uipath.connector.trigger.uipath-salesforce-slack.channel-created-in-slack`
- `uipath.connector.trigger.uipath-salesforce-slack.webhook-event-received-real-time-`

**Override exceptions:**

- `uipath.connector.trigger.uipath-salesforce-slack.button-clicked` — the BYOA requirement depends on the app/configuration. Follow the default native-connector flow, then the existing BYOA detection via `triggers objects` ([../connections.md — For BYOA Connections](../connections.md#for-byoa-connections-webhook-triggers)) handles it.
- Non-trigger Slack activities (`send-message-to-channel`, `create-channel`, etc.) follow the default auto-select rule.

### Why

Slack webhook triggers require a Bring-Your-Own-App (BYOA) connection — backed by a Slack app the customer registered with their own OAuth credentials. The personal-workspace default connection is not guaranteed to be BYOA, so silent auto-select can bind a non-BYOA connection that the runtime rejects when the trigger fires.

### Behavior

- **Auto-select:** disabled — always present connections to the user.
- **List filter:** `--byoa` from the start. Do not call `triggers objects` first to discover the BYOA requirement — every Slack trigger needs BYOA.

  ```bash
  uip is connections list "uipath-salesforce-slack" --byoa --all-folders --output json
  ```

- **Post-selection verification:** ping the chosen connection.
- **Recovery on empty:** follow the BYOA empty-list recovery in [../connections.md — For BYOA Connections](../connections.md#for-byoa-connections-webhook-triggers) (`--byoa --all-folders --refresh`, then prompt to create a BYOA connection).

### User-facing presentation

Prefix the connection list with: "Slack triggers require a **BYOA** (Bring-Your-Own-App) connection — one backed by a Slack app you registered yourself. Listing only BYOA connections. Pick one, or create a new BYOA connection if none exist."
