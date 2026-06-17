# SlackMessageReader

Reads the latest message from a Slack channel using the UiPath Integration Services Slack connector.

## What Was Fixed

### Problem 1 — `Invalid GUID string` (HTTP 400)
**Root cause:** `connectionId` was passed as a prefixed binding key instead of a bare UUID, and query parameters were appended as a query string to `relativeUrl` instead of passed as a `queryParameters` object.

**Fix applied:**
```json
// WRONG
"inputs": {
  "detail": {
    "relativeUrl": "conversations.history?channel=C074M703U8G&limit=1",
    "httpMethod": "GET"
  }
}

// CORRECT
"inputs": {
  "detail": {
    "connectionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "relativeUrl": "conversations.history",
    "httpMethod": "GET",
    "queryParameters": {
      "channel": "C074M703U8G",
      "limit": "1"
    }
  }
}
```

### Problem 2 — `not_authed` with `core.action.http`
**Root cause:** `core.action.http` is a generic HTTP node and does NOT inject IS OAuth tokens regardless of `mode: "connector"` or `authenticationType: "connector"` settings.

**Fix:** Removed `core.action.http` approach entirely. Always use the typed `slack-http-request` connector node for IS-authenticated Slack calls.

## Setup

1. Replace `${CONNECTION_ID}` in both `SlackMessageReader.flow` and `bindings_v2.json` with your actual Slack connection UUID from UiPath Integration Service:
   - Go to Integration Service → Connections → Slack → copy the bare UUID from the connection URL

2. Replace the channel ID `C074M703U8G` in `SlackMessageReader.flow` with your target Slack channel ID if needed.

3. Deploy using the CLI:
```bash
uipath flow deploy SlackMessageReader
```

4. Run and verify the output contains `"ok": true` and a `messages` array with the latest message.
