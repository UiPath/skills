# Authenticating Remote A2A Agents

Detail behind [Authentication](../SKILL.md#authentication). Read it before choosing how a new agent authenticates, and before an `update` with `--connection-id` or `--header`.

## What Agent Gateway sends

Every call to the agent, and every card fetch (`create` from `--agent-card-url`, `refresh-card`), authenticates with the first that applies:

1. **The caller's per-user connection** on the agent, when the caller is a user who has one.
2. **The agent's connection** (`--connection-id`). Agent Gateway asks Integration Service for the connection's OAuth token on each call and sends `Authorization: Bearer <TOKEN>`. A stored `Authorization` header is then not sent; the other headers are.
3. **The agent's headers** alone.

Header values can come from Orchestrator assets, as [Critical Rule 4](../SKILL.md#critical-rules) says. Use a Secret or Text asset; a Credential asset gives its password. Creating assets → `uipath-platform`.

`get` shows a raw header value as `****` only when a part of its name, between hyphens, ends in `Token`, `Secret`, `Password`, `Auth`, `Credentials` or `Session`, is `Authorization`, or the name has `Api-Key`, `Access-Key`, `Private-Key`, `Secret-Key` or `Session-Key`: `X-Api-Key` is masked, `Ocp-Apim-Subscription-Key` and `X-Authorize` are not. Under any other name the value prints in clear. Asset references always print as written.

Every call also carries the caller's `Accountid` and `Tenantid` headers and the trace headers (`Traceparent`, `Request-Id`, `Request-Context`).

## Choosing from the card

Read the card's `securitySchemes`: from `CachedAgentCard` in `get`, or from the provider. Then confirm with the user what credential they have.

| Scheme in the card | Set on the agent |
|---|---|
| `oauth2`, any flow | `--connection-id` of an Agent 2 Agent connection that uses an OAuth 2.0 grant ([below](#oauth-connections)). |
| `apiKey`, `in: header` | `--header "<NAME>=%ASSETS/<ASSET_NAME>%"`, with `<NAME>` the scheme's `name` and the asset holding the key. |
| `apiKey`, `in: query` | Not supported: Agent Gateway sends headers, not query parameters. Ask the provider for a header or OAuth option. |
| `http`, `scheme: basic` | `--header "Authorization=%ASSETS/<ASSET_NAME>%"`, the asset holding `Basic <BASE64>` (`<BASE64>` encodes `<USER>:<PASSWORD>`). |
| `http`, `scheme: bearer`, a token that does not expire | `--header "Authorization=%ASSETS/<ASSET_NAME>%"`, the asset holding `Bearer <TOKEN>`. |
| `http`, `scheme: bearer`, a token from an OAuth server | An OAuth connection, as for `oauth2`. A copied token stops working when it expires. |
| No `securitySchemes` | Nothing, or what the provider documents. |

A raw value (`--header "<NAME>=<VALUE>"`) works too, but use it only when the user cannot store an asset (Critical Rule 4).

## OAuth connections

The connector is **Agent 2 Agent**, connector key `uipath-google-agent2agent`. `uip is connections list <CONNECTOR_KEY> --all-folders --refresh --output json`, with that key, lists its connections with their ids and folders. Always pass `--refresh`: without it the CLI answers from its cache. Creating one → `uipath-platform`, or the user in Integration Service.

The connector offers seven authentication types. Only the ones that use an OAuth 2.0 grant, such as client credentials, work in Agent Gateway, because it asks Integration Service for the connection's OAuth token. Personal Access Token, API Key and Basic do not ([why](troubleshooting-guide.md#connections-that-are-not-oauth)), although the connector's documentation lists them.

The CLI cannot show a connection's type: `is connections list` has no column for it. Before passing `--connection-id`, ask the user which type the connection uses.

## Example: Microsoft Foundry

An example of the rules above, from Microsoft's [Enable incoming A2A on a Foundry agent](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/enable-agent-to-agent-endpoint):

- Foundry accepts only Microsoft Entra ID tokens, on every A2A URL, the card included.
- Use an Agent 2 Agent connection with OAuth 2.0 client credentials: token URL `https://login.microsoftonline.com/<ENTRA_TENANT_ID>/oauth2/v2.0/token`, the client id and secret of an Entra app registration, scope `https://ai.azure.com/.default`. Pass it on `create` with `--connection-id`: it also authenticates the card fetch.
- Give the app's service principal the **Foundry Agent Consumer** role on the Foundry project, or on that agent.
- The card is at the agent's A2A path followed by `/agentCard/v1.0`, or `/agentCard/v0.3` for A2A v0.3: `https://<ACCOUNT>.services.ai.azure.com/api/projects/<PROJECT>/agents/<AGENT>/endpoint/protocols/a2a/agentCard/v1.0`. Not `/.well-known/agent-card.json`.
- Do not paste an Entra token as a static `Authorization` header: it expires.
