---
confidence: medium
---

# Slack — API rejected the request

## Context

A Slack Integration Service activity (`SendMessage`, `GetUserByEmail`, …) faults **after the connection resolved** — the Slack Web API was called and returned an error. The connection is fine; the request itself (its arguments, the bot's channel membership, or its token scopes) is the problem.

What this looks like — `UiPath.BAF.Infrastructure.Exceptions.BusinessActivityExecutionException` whose body carries the Slack API error verbatim:

```
UiPath.BAF.Infrastructure.Exceptions.BusinessActivityExecutionException: BusinessActivityExecutionException:
Error Code: [400]
Message: invalid_arguments
RequestId: <id>
ProviderMessage: {"ok":false,"error":"invalid_arguments","warning":"missing_charset","response_metadata":{"messages":["[ERROR] missing required field: channel"],"warnings":["missing_charset"]}}
```

The `Error Code` is the HTTP status; `Message` and the `ProviderMessage` JSON `error` field are the **Slack** error code — that is the real cause. Common `error` values:

- `invalid_arguments` with `response_metadata.messages: ["[ERROR] missing required field: channel"]` — Send Message ran without a resolved `Channel` (the `Channel` argument was empty/null, or an upstream variable produced no value). The dominant `SendMessage` API failure in telemetry.
- `channel_not_found` — the `Channel` value doesn't match a channel in the workspace (wrong id/name, or a channel from a different workspace than the connection).
- `not_in_channel` — the channel exists but the Slack app/bot isn't a member of it, so it can't post.
- `users_not_found` — Get User by Email: no workspace user has that email (wrong/typo email, or a user outside this workspace).
- `invalid_auth` / `account_inactive` / `token_revoked` — the Slack token is rejected/inactive (re-auth needed). May also surface through the BAF layer as `Unauthorized - An invalid connection id, and/or Bearer token provided.`
- `missing_scope` — the connection's token lacks the OAuth scope the call needs (e.g. `chat:write` for Send Message, `users:read.email` for Get User by Email).
- `ratelimited` (HTTP 429) — Slack throttled the request; transient.

What can cause it:
- **Missing/empty required argument** (`invalid_arguments`, missing `channel`): the `Channel` (or other required input) wasn't supplied. Fix is in the workflow inputs.
- **Wrong target** (`channel_not_found`, `users_not_found`): the channel/email doesn't exist in this workspace.
- **App not in channel** (`not_in_channel`): the bot must be invited to the channel before it can post.
- **Token rejected** (`invalid_auth` / `Unauthorized ...`): the connection's Slack token is invalid/revoked — re-authorize.
- **Missing scope** (`missing_scope`): the Slack app's token doesn't include the required scope.
- **Rate limited** (`ratelimited`): transient throttling — retry with backoff.

What to look for:
- The exception **type is `BusinessActivityExecutionException`** and a `ProviderMessage` JSON is present — this is the marker that the connection resolved and Slack rejected the call. The `error` field, not the HTTP `Error Code`, drives the fix.

> **Different cause — do not apply this playbook:**
> - `System.AggregateException` wrapping a `ConnectionException` (`Unable to find a connection ...` / `The selected connection is no longer valid ...`) means the failure was at connection resolution, before the Slack call → use [connection-resolution-failure.md](./connection-resolution-failure.md).
> - This is the Integration Service package, not the legacy `UiPath.Slack.Activities` (`SlackScope`).

## Investigation

1. **Confirm the exception type** is `BusinessActivityExecutionException` and **parse the `ProviderMessage` JSON.** Read the `error` field and any `response_metadata.messages` — they name the exact Slack-side problem.
2. **Map the `error` code to its cause** (table above). Do not stop at the generic HTTP `Error Code` (`[400]`/`[429]`) — the Slack `error` string is the discriminator.
3. **For `invalid_arguments` / missing field:** capture the activity's argument values from the workflow source — confirm `Channel` (or the named missing field) actually resolves to a non-empty value at runtime.
4. **For `channel_not_found` / `users_not_found`:** confirm the channel/email exists in the workspace the connection authenticates to.
5. **For `not_in_channel`:** confirm whether the app/bot is a member of the target channel.
6. **For `invalid_auth` / `missing_scope`:** capture the connection and the scopes its Slack token was granted.

## Resolution

- **If `invalid_arguments` / `missing required field: channel`:** set a valid `Channel` on the Send Message activity (channel id or name); fix the upstream expression if `Channel` was coming from an empty variable.
- **If `channel_not_found`:** correct the `Channel` value to a channel that exists in the connection's workspace.
- **If `not_in_channel`:** invite the Slack app/bot to the target channel (`/invite @<app>`), then re-run.
- **If `users_not_found`:** correct the email to a user that exists in the workspace.
- **If `invalid_auth` / `account_inactive` / `token_revoked` / `Unauthorized - An invalid connection id, and/or Bearer token provided.`:** re-authorize the Slack connection in Integration Service (or recreate it).
- **If `missing_scope`:** re-authorize the connection with the required Slack OAuth scope (e.g. `chat:write`, `users:read.email`) for the operation.
- **If `ratelimited` (429):** retry with backoff; add a Retry Scope around the activity. Reduce call frequency if it recurs.

If the argument is valid, the target exists in the workspace, the app is in the channel, and the token authorizes with the right scopes yet Slack still rejects the call, capture the full `ProviderMessage` and escalate with the Slack `error` code.
