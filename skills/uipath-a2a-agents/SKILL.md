---
name: uipath-a2a-agents
description: "UiPath Agent Gateway remote A2A agents (`uip agenthub remote-a2a-agent` / `remote-a2a-agent-user-connections`). Register an external A2A agent (Salesforce Agentforce, Microsoft Foundry, any agent with an agent card) from its card URL or card JSON; authenticate it with an OAuth Agent 2 Agent connection or with headers from Orchestrator assets; set users' own connections and Relay; update, refresh the card, list, get, delete. For calling an A2A agent from an agent→uipath-agents, from a flow→uipath-maestro-flow, from BPMN→uipath-maestro-bpmn. For MCP servers→uipath-mcp-servers."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Agent Gateway Remote A2A Agents

Agent Gateway is Orchestrator's hub for MCP servers and A2A agents: [about](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/about-agent-gateway). A **remote A2A agent** is an agent that runs elsewhere (a vendor's, another team's) registered in Agent Gateway so UiPath agents, flows and processes can call it. Agent Gateway stores its agent card, calls the endpoint the card names, and authenticates every call. The CLI group is `agenthub`: `uip agenthub remote-a2a-agent` manages agents, `uip agenthub remote-a2a-agent-user-connections` manages users' own connections on them.

## When to Use This Skill

- Register, update, delete, list or get a remote A2A agent, or fetch its card again (`refresh-card`).
- Choose and set how Agent Gateway authenticates to it: an Integration Service connection, or headers ([Authentication](#authentication)).
- List, set or delete a user's own connection on an agent ([Per-User Connections](#per-user-connections)).
- Reach an agent inside a private network through Relay ([Relay](#relay)).
- Get the `A2aUrl` UiPath callers use for the agent.

**Not this skill:** calling a remote A2A agent from an agent → `uipath-agents`, from a flow → `uipath-maestro-flow`, from BPMN → `uipath-maestro-bpmn`; MCP servers → `uipath-mcp-servers`; creating the Integration Service connection itself → `uipath-platform`. No skill covers exposing a UiPath agent to other platforms over A2A.

## Critical Rules

1. **Give every command the agent's folder.** Pass `--folder-path <FOLDER_PATH>` or `--folder-key <FOLDER_KEY>` (never both) on every `remote-a2a-agent` and `remote-a2a-agent-user-connections` command except `--print-schema` on `create`. Slugs are unique per folder: the same slug can name different agents in two folders. Find folders with `uip or folders list --output json`; a personal workspace resolves only by `--folder-key`.

2. **Use the slug, exactly as `list` prints it.** Always pass `--slug` on `create`. Never pass a display name or a GUID where a slug goes.

3. **Only OAuth connections work.** Agent Gateway asks Integration Service for a connection's OAuth token on every call and on every card fetch. An Agent 2 Agent connection of type Personal Access Token, API Key or Basic has no OAuth token: `create` and `refresh-card` with it fail with `server_error` "HTTP 502: Received HTML instead of the expected JSON response.", whatever the `Instructions` say about retrying, and calls fail the same way. The CLI cannot show a connection's type: before you pass `--connection-id`, confirm with the user that the connection uses an OAuth 2.0 grant; when you cannot ask, do not pass it, and tell the user which connection you left out and why. For an API key, Basic credentials or a fixed bearer token, use `--header` instead ([Authentication](#authentication)).

4. **Keep secrets in Orchestrator assets.** A header value of exactly `%ASSETS/<ASSET_NAME>%` is replaced, on every call, by that asset's value from the agent's folder. The asset holds the whole value (`Bearer <TOKEN>`, `Basic <BASE64>`), so nothing goes before or after the reference: `Authorization=%ASSETS/<ASSET_NAME>%`. `Bearer %ASSETS/<ASSET_NAME>%` is not replaced: the agent gets that text as is. Never put a raw secret in `--header` when the user can store it in an asset, and never print one back.

5. **Dry-run every write first.** `create`, `update`, `delete`, `refresh-card` and the per-user `set` / `delete` take `--dry-run`: it runs the CLI's checks and prints the plan (`Code: DryRun`) without the call. The service's own checks (the card fetch, asset reads, name and slug conflicts) run only on the real call, so a clean plan does not promise a clean write. The plan shows header values in clear: do not paste it to the user when a header holds a raw secret.

6. **An update changes only what the user asked.** Scalar flags keep every stored field you do not pass. Do not re-send the card, the headers or the connection to change something else ([Updating Agents](#updating-agents)).

7. **Never route stored credentials around a refusal.** `update` refuses to move an agent with a secret or asset-backed header to another origin, and refuses `****` under a header stored unmasked. Follow the refusal's `Instructions`; do not delete headers or the connection to get past it without the user's consent.

8. **Ask before acting for another user.** Setting or deleting someone else's per-user connection changes how their calls authenticate: confirm with the user first, unless they asked for exactly that user.

9. **Deletes need `--yes`, after the user confirms.** `remote-a2a-agent delete` and the per-user `delete` refuse without `--yes` (`ErrorCode: confirmation_required`) and never prompt. Show the slug and `Name`, get the user's confirmation, then pass `--yes`. A delete's `--dry-run` needs `--yes` too and deletes nothing, so `delete <SLUG> --dry-run --yes` is fine before the user confirms; only the real delete waits for them.

10. **`not_supported` is final.** `ErrorCode: not_supported` ("Remote A2A agent management isn't supported on the connected environment.") means Agent Gateway there does not offer remote A2A agents ([Automation Suite](#automation-suite)). Another attempt, folder or flag gets the same answer; tell the user.

## Registering an Agent

`uip agenthub remote-a2a-agent create --name <NAME> --slug <SLUG> --agent-card-url <CARD_URL> --folder-path <FOLDER_PATH> --output json`, plus the agent's auth: `--connection-id <CONNECTION_ID>` or `--header <NAME>=<VALUE>` (repeatable), and `--use-relay` for a private network.

- **Picking the connection.** List the Agent 2 Agent connections ([OAuth connections](references/authentication-guide.md#oauth-connections)), then ask the user which one uses OAuth 2.0, naming each by its `Name` and `Id`. The list does not show a connection's type: do not infer it from the name, the order or `IsDefault`. Pass the `Id` of the row whose `Name` the user gives (Critical Rule 3).
- **`--agent-card-url`** may be any URL that serves the card, not only `/.well-known/agent-card.json` (Foundry serves it at `…/a2a/agentCard/v1.0`; see the [Foundry example](references/authentication-guide.md#example-microsoft-foundry)). Agent Gateway fetches it on `create` and `refresh-card` with the agent's own auth (connection or headers), through Relay when it is on. A card behind auth is fine when that auth is set on the agent.
- **`--agent-card-json '<JSON>'`** stores a card you pass, without fetching: use it only when Agent Gateway cannot fetch the card at all. `refresh-card` then has nothing to fetch.
- Every call goes to the JSON-RPC endpoint the card names: its `url` in a v0.3 card, or its `supportedInterfaces` URL in a v1.0 card. Check it is the agent's real endpoint before creating.
- From a CLI login, a `%ASSETS/<ASSET_NAME>%` header makes `create` from a card URL, and `refresh-card`, fail with `Forbidden (403)`: Orchestrator does not give asset values to a CLI login. Create without that header and add it with `update <SLUG> --folder-path <FOLDER_PATH> --header "<HEADER>=%ASSETS/<ASSET_NAME>%"`, the value exactly the reference: for a bearer token stored as `Bearer <TOKEN>`, `--header "Authorization=%ASSETS/<ASSET_NAME>%"`, never `Authorization=Bearer %ASSETS/…%` (Rule 4). Or create from `--agent-card-json` ([details](references/troubleshooting-guide.md#asset-backed-headers-from-the-cli)).
- `create --print-schema --output json` describes a `--file` / `--body` payload, in camelCase.
- The result is the stored agent: `Slug`, `A2aUrl`, `AgentCardUrl`, `CachedAgentCard`, `Headers` (secrets as `****`), `UseRelay`, `IsActive`, and `ConnectionId` when it has one. Confirm the create from it.

## Authentication

Agent Gateway authenticates every call to the agent, and every card fetch, with the caller's own per-user connection if they have one ([Per-User Connections](#per-user-connections)), else the agent's connection, else the agent's headers. Pick from the `securitySchemes` in the agent's card: OAuth 2.0 → an OAuth Agent 2 Agent connection (`--connection-id`, Rule 3); an API key in a header, HTTP Basic or a fixed bearer token → `--header`, with the value in an asset (Rule 4). The table for each scheme, what goes in the asset, OAuth connections and a Microsoft Foundry example: [references/authentication-guide.md](references/authentication-guide.md).

## Updating Agents

`uip agenthub remote-a2a-agent update <SLUG> --folder-path <FOLDER_PATH> --output json`, with only the flags for what changes (Rule 6). What each flag keeps or replaces, masked values, moving an agent to another host and payloads: [references/updating-agents-guide.md](references/updating-agents-guide.md).

## Per-User Connections

An agent calls with its own connection, except for a user who has a per-user connection on it: calls made with that user's identity use their own. Calls made with any other identity (another user, an external application) use the agent's connection. Use them when each user has their own account at the agent's provider.

- `uip agenthub remote-a2a-agent-user-connections list --agent <SLUG> --folder-path <FOLDER_PATH> --output json` — one row per user: `UserId`, `UserName`, `ConnectionId`, `ConnectionName`, `Status`. Needs McpServers.Edit.
- `uip agenthub remote-a2a-agent-user-connections set --agent <SLUG> --me --connection-id <CONNECTION_ID> --folder-path <FOLDER_PATH> --output json` — sets or replaces one. The user: `--me`, `--user-email <EMAIL>` or `--user-id <USER_ID>`; the connection: `--connection-id` or `--connection-name "<NAME>"`, exactly one of each. Needs Connections.Edit. The connection must be an OAuth Agent 2 Agent connection (Rule 3) made for the endpoint in the agent's card. For a v0.3 card, the CLI refuses a connection made for another URL; it does not check a v1.0 card.
- **Another user's connection in their personal workspace** is one you see only while you explore that workspace. Until then, `set` for them answers `You can see no connection of the Agent 2 Agent connector named '<NAME>'.`, and its id gets a 403. Exploring gives you the Personal Workspace Administrator role on everything in it, and Orchestrator notifies the owner and audits it: ask the user before you explore (Rule 8). Then:
  1. `uip or folders explore --owner <USER_EMAIL> --output json`, with the email you pass to `set --user-email` (`--owner` also takes the `--user-id`). `Data.Status` is `Exploring` or `Already exploring`. It needs a user login, not an external application, and Folders.Edit, Users.View and Roles.View on the tenant.
  2. `set` again, as above.
  3. `uip or folders stop-exploring --owner <USER_EMAIL> --output json`, unless the user wants to keep exploring. The per-user connection stays set.
- `uip agenthub remote-a2a-agent-user-connections delete --agent <SLUG> --me --folder-path <FOLDER_PATH> --yes --output json` — removes one, so that user's calls use the agent's connection again (Rule 9).
- `Status`: `Active` — the connection is enabled. Any other status: [troubleshooting](references/troubleshooting-guide.md#per-user-connections).
- `Per-user connections are not enabled on this tenant.` — they aren't available on this tenant: every user calls with the agent's connection, which `update --connection-id` changes.

## Relay

`--use-relay` routes the card fetch and every call through UiPath Relay, for an agent the cloud cannot reach (inside a company network). The Relay client must be running where the agent is reachable. `update --no-use-relay` turns it off; an update without either keeps the setting. Without Relay, Agent Gateway refuses private hosts.

## Automation Suite

Agent Gateway on Automation Suite does not have remote A2A agents: every `uip agenthub remote-a2a-agent` and `remote-a2a-agent-user-connections` command fails with `not_supported` (Rule 10).

## Troubleshooting

Every `uip agenthub` message about remote A2A agents, with its cause and fix: [references/troubleshooting-guide.md](references/troubleshooting-guide.md). The most common: an HTTP 502 on `create` or `refresh-card` means Agent Gateway could not fetch the card, usually because of a non-OAuth connection (Rule 3); running the same command again gets the same 502.

## Reference Navigation

- [references/authentication-guide.md](references/authentication-guide.md) — what Agent Gateway sends, the table for each scheme, OAuth connections, a Microsoft Foundry example.
- [references/updating-agents-guide.md](references/updating-agents-guide.md) — what an update keeps or replaces, masked values, moving an agent, payloads.
- [references/troubleshooting-guide.md](references/troubleshooting-guide.md) — errors with their cause and fix, connections that are not OAuth, asset-backed headers from the CLI.

## What NOT to Do

- Do NOT attach a Personal Access Token, API Key or Basic connection; do NOT retry the 502 it causes (Rule 3).
- Do NOT write `Bearer %ASSETS/<ASSET_NAME>%`: the asset holds the whole value (Rule 4).
- Do NOT put a raw secret in `--header` when it can live in an asset (Rule 4).
- Do NOT re-send the card or headers to change something else (Rule 6).
- Do NOT run a delete with `--yes` before the user confirms; a `--dry-run --yes` is fine (Rule 9).
- Do NOT retry a `not_supported` failure (Rule 10).
