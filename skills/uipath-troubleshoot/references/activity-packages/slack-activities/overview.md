# Slack Activities (Integration Service)

Activities from the `UiPath.Slack.IntegrationService.Activities` package for automating Slack through an Integration Service connection — e.g. **Send Message** (`SendMessage`) and **Get User by Email** (`GetUserByEmail`). These are Business Activity Framework (BAF) connector activities: they resolve an Integration Service connection to a Slack workspace, then call the Slack Web API.

## How These Activities Work

Each activity runs in two phases:

1. **Connection resolution.** `BAFAsyncCodeActivity → ConnectionService.Connect(...)` resolves the configured Integration Service connection (by connection id) and obtains the Slack OAuth token. This happens before any Slack call.
2. **Slack Web API call.** The activity issues the Slack Web API request (e.g. `chat.postMessage` for Send Message, `users.lookupByEmail` for Get User by Email) and maps the JSON response back, or throws on a Slack-side error.

The phase that fails determines the exception type and the fix — this is the key diagnostic split:

- A failure in **phase 1** surfaces as `System.AggregateException` wrapping a `UiPath.IntegrationCore.Utilities.ConnectionException` (or a transient IPC error). The Slack request never ran; the problem is the connection, not the message/user input.
- A failure in **phase 2** surfaces as `UiPath.BAF.Infrastructure.Exceptions.BusinessActivityExecutionException` carrying the Slack API's own error (`Error Code`, `Message`, and a raw `ProviderMessage` JSON with the Slack `error` code). The connection was fine; Slack rejected the request.

## Key Activities

- **Send Message** (`UiPath.Slack.IntegrationService.Activities.SendMessage`) — post a message to a channel/user (`chat.postMessage`). Requires a valid `Channel`.
- **Get User by Email** (`UiPath.Slack.IntegrationService.Activities.GetUserByEmail`) — look up a workspace user by email (`users.lookupByEmail`).

## Common Failure Patterns

- **Connection resolution failure** — the activity faults at phase 1 with `System.AggregateException`. Inner `ConnectionException` is one of: `Unable to find a connection of type  with the specified Id '<guid>'.` (connection deleted / wrong id / not in scope) or `The selected connection is no longer valid. Please use another connection or create a new one.` (connection revoked/invalidated). A transient `503 (Service Unavailable)` during service discovery also surfaces this way. See [connection-resolution-failure.md](./playbooks/connection-resolution-failure.md).
- **Slack API rejected the request** — the activity faults at phase 2 with `BusinessActivityExecutionException` (`Error Code: [<http>]`, `Message: <slack_error>`, `ProviderMessage: {"ok":false,"error":"<slack_error>",...}`). The Slack `error` code (e.g. `invalid_arguments` / missing `channel`, `channel_not_found`, `not_in_channel`, `invalid_auth`) is the real cause. See [slack-api-error.md](./playbooks/slack-api-error.md).

## Package

NuGet: `UiPath.Slack.IntegrationService.Activities`
