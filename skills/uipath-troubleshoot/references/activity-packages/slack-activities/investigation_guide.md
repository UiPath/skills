# Slack Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity's class matches the reported failure (`UiPath.Slack.IntegrationService.Activities.SendMessage`, `...GetUserByEmail`). Do not confuse the Integration Service activities with the legacy `UiPath.Slack.Activities` (`SlackScope`/`SlackScopeActivity`) package — different code path, different exceptions.
- **Connection** — the Integration Service connection in evidence (its id / the Slack workspace it authenticates to) is the one the user is asking about. A different connection id = a different workspace = unrelated data.
- **Target** — for Send Message, the `Channel` argument; for Get User by Email, the email — match what the user reports.
- **Workflow file** — the error originates from the workflow the user references, not another `.xaml`/`.cs` that also calls Slack.
- **Timestamp** — the failure occurred in the reported window (load-bearing for a transient Slack/Integration-Service outage).

If the data doesn't match: discard it.

## Domain-Specific Data Gathering

1. **Classify by phase from the exception type — this is the primary routing decision.**
   - `System.AggregateException` → **connection resolution** (phase 1). Unwrap `InnerExceptions[0]`; it is a `UiPath.IntegrationCore.Utilities.ConnectionException` (or a transient `UiPath.CoreIpc.RemoteException` 503). The Slack request never ran — the cause is the connection, never the channel/email input.
   - `UiPath.BAF.Infrastructure.Exceptions.BusinessActivityExecutionException` → **Slack API rejection** (phase 2). The connection resolved; read the `Error Code`, `Message`, and `ProviderMessage` JSON — the Slack `error` code is the cause.
2. **Always unwrap `System.AggregateException`.** Its own text is just `One or more errors occurred. (<inner message>)`. Do not attribute the root cause to `AggregateException` itself.
3. **For `BusinessActivityExecutionException`, parse the `ProviderMessage`.** It is the raw Slack Web API response: `{"ok":false,"error":"<code>", ...}`. The `error` field (and any `response_metadata.messages`) name the exact Slack-side problem — match the fix to that code, not to the generic HTTP `Error Code`.
4. **Do not treat the connection id GUID as the cause.** `Unable to find a connection ... with the specified Id '<guid>'` means that id doesn't resolve for the running identity/folder — the fix is the connection binding, not the GUID value.

## Testing Prerequisites

1. **Activity identity** — confirm `SendMessage` / `GetUserByEmail` and capture the display name.
2. **Exception type + unwrapped detail** — `AggregateException` (with inner `ConnectionException` text) vs. `BusinessActivityExecutionException` (with `Error Code` / `Message` / `ProviderMessage`).
3. **Connection** — the Integration Service connection id and the Slack workspace it targets; whether the connection still exists, is enabled, and is in a folder the robot can use.
4. **Slack `error` code** — for phase-2 failures, the exact `error` string from `ProviderMessage`.
5. **Input arguments** — Send Message `Channel` (present and a valid channel id/name); Get User by Email email value.
6. **Package version** — `UiPath.Slack.IntegrationService.Activities` version.
