# Remote A2A Agent Troubleshooting

Text `uip agenthub remote-a2a-agent` and `remote-a2a-agent-user-connections` print in a failure's `Message`, `Instructions` or `Errors`, with its cause and fix. Every failure also carries `Instructions`: when no row here matches, follow them, except a `Retry: RetryLater` on a 502 from `create` or `refresh-card` ([below](#registering-and-the-card)).

## Registering and the card

| Text | Cause and fix |
|---|---|
| `HTTP 502: Received HTML instead of the expected JSON response.` (`server_error`) on `create` or `refresh-card` | Agent Gateway could not fetch the card. It reports every cause the same way, so a retry fails again. Check, in this order: **1.** With a connection: it must use an OAuth grant. A Personal Access Token, API Key or Basic connection always fails ([why](#connections-that-are-not-oauth)); ask the user its type. An OAuth one may need its owner to sign in again: `uip is connections ping <CONNECTION_ID> --force-refresh --output json`. **2.** The card URL must answer with the card, with the agent's auth: check the path with the user (Foundry's ends `…/a2a/agentCard/v1.0`). **3.** A host only reachable from a private network needs `--use-relay`. When Agent Gateway cannot fetch the card at all, create with `--agent-card-json`. `create` stores nothing on failure. |
| `URL blocked for security reasons: DNS resolution failed for host: <HOST>` (in `Errors.AgentCardUrl`) | The host does not resolve from the cloud. Check its spelling; for a host inside a private network, pass `--use-relay`. |
| `URL blocked for security reasons: Private network address detected: <IP>` (in `Errors.AgentCardUrl`) | A private host without Relay: pass `--use-relay`. A Relay client must reach the host. |
| `Forbidden (403). …` with `Context.ErrorCode: "10400"`, on `create` from a card URL or `refresh-card` of an agent with a `%ASSETS/<ASSET_NAME>%` header | Orchestrator refused to give the asset's value to a CLI login: [asset-backed headers from the CLI](#asset-backed-headers-from-the-cli). Token scopes are not the cause. |
| `HTTP 409: Business Conflict: Remote A2A agent with slug '<SLUG>' already exists in this folder` | Pick another `--slug`, or update the existing agent. |
| `HTTP 409: Business Conflict: Remote A2A agent with name '<NAME>' already exists in this folder` | Pick another `--name`. |
| `HTTP 500: Server error: Cannot refresh agent card: no AgentCardUrl configured. …` | The agent was created from `--agent-card-json`, so `refresh-card` has nothing to fetch. Do not retry. Pass a new card with `update --agent-card-json`, or set `--agent-card-url` and then refresh. |

## Connections that are not OAuth

[Critical Rule 3](../SKILL.md#critical-rules) gives the symptom. The cause: Integration Service answers the token request for a Personal Access Token, API Key or Basic connection with `400 CNS1021` "access token is not supported", which Agent Gateway turns into the 502. `create` stores nothing. `update --connection-id` stores the connection without fetching the card, so the update succeeds and every later call fails with a 502.

Fix: put the same credential in `--header`, with an asset ([Choosing from the card](authentication-guide.md#choosing-from-the-card)). For an agent that already has the connection: `uip agenthub remote-a2a-agent update <SLUG> --clear-connection --header "<NAME>=%ASSETS/<ASSET_NAME>%" --folder-path <FOLDER_PATH> --output json`.

## Asset-backed headers from the CLI

From a CLI login, `create` from `--agent-card-url` and `refresh-card` on an agent with a `%ASSETS/<ASSET_NAME>%` header fail with `ErrorCode: permission_denied`, `Forbidden (403). …`, and `Context.ErrorCode: "10400"`. Orchestrator refuses to give the asset's value to a CLI login. Token scopes are not the cause, and `create` stores nothing. As with MCP servers, Agent Gateway in the portal can read the asset.

- **The card needs no auth:** create the agent without the asset header, then add it with `update --header "<NAME>=%ASSETS/<ASSET_NAME>%"`. `update` does not fetch the card.
- **The card needs the header:** create with `--agent-card-json '<CARD_JSON>'` and the header. `--agent-card-json` stores the card without fetching it. The user can get the card from the provider.
- **To refresh the card later,** ask the user to refresh it in Agent Gateway.

## Calls to the agent

A UiPath agent, flow or process that calls the remote agent gets these statuses back from Agent Gateway.

| Status | Cause and fix |
|---|---|
| 502 | Agent Gateway got no OAuth token from the connection: usually a Personal Access Token, API Key or Basic connection set with `update --connection-id` ([why](#connections-that-are-not-oauth)). A 502 `Error proxying A2A request: …` means the endpoint in the card is unreachable: check the card's `url` and Relay. |
| 401 with `WWW-Authenticate: Bearer error="invalid_token", error_description="Integration Service rejected the access token …"`, or a 403 | Integration Service refused the connection's token: its owner signs in to it again. When the caller has a per-user connection on the agent, that connection is the one to fix ([below](#per-user-connections)). |
| 401 or 403 without that `error_description` | The remote agent refused the credential Agent Gateway sent. Its body passes through unchanged. Check the header value or the asset behind it, and the scopes or roles the provider requires. |
| 400 `Remote A2A agent '<SLUG>' is not active.` | `update <SLUG> --is-active true`, if the user wants it back on. |
| 504 `Request timeout` | The remote agent did not answer in time. |

## Folders, slugs and deletes

| Text | Cause and fix |
|---|---|
| `'<NAME>' resolves to the remote A2A agent '<SLUG>', not to an agent with that slug: …` | A display name was passed where the slug goes: pass `<SLUG>`. |
| `HTTP 404: Not Found` on `get`, `update`, `delete` or `refresh-card` | Wrong folder, or not the slug: `uip agenthub remote-a2a-agent list --folder-path <FOLDER_PATH> --output json` shows the slugs. |
| `Confirmation required: this will delete remote A2A agent '<SLUG>' and cannot be undone.` | Show the user the slug and `Name`, confirm, then add `--yes`. On a `--dry-run`, add `--yes` to see the plan: a dry-run deletes nothing. |
| `Remote A2A agent management isn't supported on the connected environment.` (`not_supported`) | Agent Gateway there has no remote A2A agents (Automation Suite 26.10). Final: tell the user. |
| `Forbidden (403). …` without `Context.ErrorCode: "10400"` | A missing folder permission: `get` needs McpServers.View, `create` McpServers.Create, `update` and `refresh-card` McpServers.Edit, `delete` McpServers.Delete. |

## Updates

| Text | Cause and fix |
|---|---|
| `Header '<NAME>' is stored unmasked, …` / `Header '<NAME>' is stored as '<STORED_NAME>', …` / `No stored header '<NAME>' has a masked value to keep, …` | `****` works only under a name `get` shows as `****`: [masked values](updating-agents-guide.md#masked-values). |
| `--agent-card-url moves '<SLUG>' to another origin, <ORIGIN>, …` / `--agent-card-json moves …` / `The payload's agentCardUrl moves …` | The update would send stored credentials to a new host: [moving an agent](updating-agents-guide.md#moving-an-agent-to-another-host). |
| `--connection-id and --clear-connection cannot be combined: …` | Pass one of the two. |
| `--agent-card-url '<URL>' is not an absolute http or https URL.` | Pass the URL with its scheme and host. |

## Per-user connections

| Text | Cause and fix |
|---|---|
| `Per-user connections are not enabled on this tenant.` (`not_found`) | They aren't available on this tenant: every user calls with the agent's own connection. Tell the user; change that connection (`update <SLUG> --connection-id <CONNECTION_ID>`) only if they ask, since it changes it for every user. |
| `Connection '<CONNECTION_ID>' is for '<BASE_URL>', and '<SLUG>' calls '<ENDPOINT>'.` / `Connection '<CONNECTION_ID>' names no base URL, …` | A per-user connection's token goes to the endpoint in the agent's card. Set an Agent 2 Agent connection made for `<ENDPOINT>`. |
| `Connection '<CONNECTION_ID>' is in the personal workspace '<FOLDER>', which is not yours.` (or `not the user's own`) | A personal-workspace connection can be set only for that workspace's owner. Pass one from a shared folder, or from the user's own personal workspace. |
| `Forbidden (403). …` on `set`, with `Instructions` naming Connections.Edit and McpServers.Edit | Your own per-user connection needs Connections.Edit in the agent's folder; another user's also needs McpServers.Edit. The same 403 comes back for a connection that is not Enabled or that you cannot see: `uip is connections ping <CONNECTION_ID> --force-refresh --output json`. |
| `Forbidden (403). …` on `list` | `list` needs McpServers.Edit in the agent's folder. |
| `You can see no connection of the Agent 2 Agent connector named '<NAME>'.` | `uip is connections list <CONNECTOR_KEY> --all-folders --refresh --output json`, with `<CONNECTOR_KEY>` `uipath-google-agent2agent`, lists the ones you can see. A connection in another user's personal workspace is among them only while you explore that workspace; until then its id with `--connection-id` gets a 403 too. Explore it as [Per-User Connections](../SKILL.md#per-user-connections) says, after asking the user, or have that user run `set --me`. Otherwise pass the exact name, or `--connection-id`. |
| `Error exploring personal workspace` / `Error stopping exploring personal workspace` with `ErrorCode: permission_denied` | Exploring takes a user login and Folders.Edit, Users.View and Roles.View on the tenant; Orchestrator refuses it to an external application or a personal access token whatever they are granted. Tell the user; have that user run `set --me`, or an admin explore the workspace. |
| `You own this Personal Workspace, and an owner cannot explore their own. …` | The connection is your own: `set --me`, or `--user-email` with your email, needs no exploring. |
| `No Personal Workspace is owned by '<OWNER>'. …` / `Personal Workspace '<NAME>' not found. …` | Check the email or name: `uip or folders list --all --type personal --name <TEXT> --output json` lists the workspaces with their `OwnerName`. When the user has none on this tenant (it is created the first time they open Orchestrator there), their connection is in another folder: ask them which, or have them run `set --me`. |
| `<N> connections of the Agent 2 Agent connector are named '<NAME>'.` / `<N> users in the organization have the email '<EMAIL>'.` | `Instructions` lists each id: show them to the user, ask which one, and pass it as `--connection-id` / `--user-id`. |
| `No user in the organization has the email '<EMAIL>'.` | Check the email with the user; `uip admin users list --search <TEXT> --output json` lists users with their emails. |
| `Looking a user up by email needs permission to read the organization's users. …` | Ask for the user's id and pass `--user-id`. |
| `--me needs a user's login, and this session has no user of its own.` | The login is an external application's: pass `--user-email` or `--user-id`. |
| `'<SLUG>' has no per-user connection for user <USER>.` | Nothing to delete: `list` shows the users who have one. |
| `Confirmation required: this will remove a per-user connection from remote A2A agent '<SLUG>' and cannot be undone.` | Confirm with the user (Critical Rule 8 for another user's), then add `--yes`. |

`Status` in `list`:
- `Active`: the connection is enabled.
- `RequiresAuth`: the connection is gone, expired or failing. The user signs in to it again, or sets another.
- `Inactive`: the connection is disabled, or the agent is inactive.
- `Unavailable`: Agent Gateway could not read the connections' state. List again later.

`set` does not check the connection's type: a Personal Access Token, API Key or Basic connection is stored, and that user's calls then fail with a 502 (Critical Rule 3).

## Input and payloads

| Text | Cause and fix |
|---|---|
| `HTTP 400: One or more validation errors occurred.` with `Errors` | Fix the fields `Errors` lists. Without `Errors`, re-run with `--dry-run` to see the body. |
| ``Payload keys differ from their fields only in case: `<KEY>` should be `<FIELD>`, …`` | Rename each key as listed; `--print-schema` lists the fields. |
| `Use exactly one of --file, --body, or scalar options.` | Pass flags, `--file` or `--body`, not a mix. |
| `No input provided. Pass scalar options, --file <path>, or --body <json>.` | Pass the fields. |
| `Header '<NAME>' is passed more than once.` | Pass each header once. |
