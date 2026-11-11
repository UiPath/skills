# Updating Remote A2A Agents

Detail behind [Updating Agents](../SKILL.md#updating-agents). Read it before an `update` that changes the card, the headers or the connection, before an `update` with `--file` / `--body`, and whenever an update is refused.

## What an update keeps

| Flag | Effect | Left out |
|---|---|---|
| `--name` | Renames the agent. The slug never changes. | Kept. |
| `--description` | Replaces the description; `--description ""` clears it. | Kept: the CLI sends the stored one back. |
| `--header` (repeatable) | Replaces **every** stored header. | Kept. |
| `--agent-card-url` | Stores the new URL **without fetching it**: calls keep going to the endpoint in the stored card until `refresh-card` fetches the new card. | Kept. |
| `--agent-card-json` | Replaces the stored card; calls go to the new card's endpoint. | Kept. |
| `--connection-id` | Replaces the connection, without a card fetch, so a connection that is not OAuth shows only when calls fail ([why](troubleshooting-guide.md#connections-that-are-not-oauth)). | Kept. |
| `--clear-connection` | Removes the connection. Calls then use the headers alone. | Kept. |
| `--use-relay` / `--no-use-relay` | Turns Relay on or off. | Kept. |
| `--is-active false` / `true` | An inactive agent refuses calls (`Remote A2A agent '<SLUG>' is not active.`); it stays registered. | Kept. |

After `--agent-card-url`, run `uip agenthub remote-a2a-agent refresh-card <SLUG> --folder-path <FOLDER_PATH> --output json` and check the new `CachedAgentCard`.

To change the card itself, start from `CachedAgentCard` in `get`: it prints in the card's own camelCase, so it can go back as `--agent-card-json` once edited. Do not send the card, the headers or the connection again to change anything else (Critical Rule 6).

A header named twice is refused: `Header '<NAME>' is passed more than once.`

## Masked values

`get` shows secret header values as `****`. `--header "<NAME>=****"` keeps the stored value, but only under a name `get` shows with `****`, spelled exactly the same. The CLI refuses every other `****`, because the service would store `****` as the value:

- `Header '<NAME>' is stored unmasked, as \`remote-a2a-agent get\` shows it, so pass that value instead of "<NAME>=****".`: pass the value `get` shows, such as the `%ASSETS/<ASSET_NAME>%` reference.
- `Header '<NAME>' is stored as '<STORED_NAME>', …`: spell the name exactly as stored.
- `No stored header '<NAME>' has a masked value to keep, …`: there is nothing to keep under that name, so pass the real value or an asset reference.

An asset-backed header is kept by passing its `%ASSETS/<ASSET_NAME>%` value again.

## Moving an agent to another host

A new card URL, or a card whose endpoint is on another origin (scheme, host or port), moves the agent: its credentials would go to the new host. `update` refuses the move while it would send stored credentials there. Every refusal below also fires with `--dry-run`. A payload gets the same refusals, starting `The payload's agentCardUrl …` or `The payload's agentCardJson …`.

1. **Secret or asset-backed headers.** `--agent-card-url moves '<SLUG>' to another origin, <ORIGIN>, and without --header the update keeps the stored secret or asset-backed header '<NAME>' and sends it there.` Pass `--header` for every header to send to the new host. `"<NAME>=****"` or the same `%ASSETS/<ASSET_NAME>%` value keeps one, and the kept value then goes to the new host.
2. **The agent's own connection.** `… and the update keeps the stored Integration Service connection, so the service would send the connection's token there.` Add `--clear-connection`, or `--connection-id` with a connection made for the new host. Passing the stored id again is refused too.
3. **Users' per-user connections.** `… and the update keeps the per-user Integration Service connection of one user, …` (or `connections of <N> users`), naming each user and id. Ask the user whether to remove them. For each one they confirm, run `uip agenthub remote-a2a-agent-user-connections delete --agent <SLUG> --user-id <USER_ID> --folder-path <FOLDER_PATH> --yes --output json`. Then run the update again.

Example: `uip agenthub remote-a2a-agent update <SLUG> --agent-card-url <NEW_CARD_URL> --header "<NAME>=%ASSETS/<ASSET_NAME>%" --clear-connection --folder-path <FOLDER_PATH> --output json`, then `refresh-card`.

A new card URL must be an absolute `http` / `https` URL: `--agent-card-url '<URL>' is not an absolute http or https URL.`

Do not delete headers or connections to get past a refusal without the user's consent (Critical Rule 7).

## Connections

- `--connection-id and --clear-connection cannot be combined: one sets the agent's Integration Service connection, the other removes it.`: pass one of them.
- An `Authorization` header is not sent while the agent has a connection. After `--clear-connection`, a stored `Authorization` header is sent again.

## Payloads

`uip agenthub remote-a2a-agent update <SLUG> --folder-path <FOLDER_PATH> --print-schema --output json` (and `create --print-schema`) lists the fields, in camelCase. Pass a payload with `--file <PAYLOAD_FILE>` or `--body '<JSON>'`, not with scalar flags.

In an update payload:
- an omitted `name`, `agentCardUrl`, `agentCardJson`, `isActive`, `connectionId` or `useRelay` is kept;
- an omitted `description` is **cleared**;
- omitted `headers` are kept, and `"headers": ""` removes them all. `headers` is one string of `Name:Value` lines separated by newlines, and a `<NAME>:****` line keeps a masked value;
- `"clearConnectionId": true` removes the connection, and cannot go with `connectionId`.

A key that differs from its field only in case is refused: ``Payload keys differ from their fields only in case: `<KEY>` should be `<FIELD>`, … The CLI sends only the camelCase fields, so it would drop this one.`` Rename the key to the field name.
