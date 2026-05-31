# Managed HTTP Request - Concept + `http-request` Authoring Helper

This doc covers two things every agent authoring a Managed HTTP Request needs to know:
1. What Managed HTTP Request is, and the two modes it runs in.
2. How to use the `http-request` CLI command to fill in the values Managed HTTP Request needs.

Consumers: Maestro Flow, Maestro BPMN, API Workflows, Case Management, etc. Each consumer surfaces Managed HTTP Request differently (as a node, an activity, a tool call, …) and uses its own type identifier and configuration schema - the concept and the rules below are the same. For the exact node/activity type identifier and how to configure it, see your consumer's own authoring docs.

## What is Managed HTTP Request?

A built-in way to make an HTTP call from a UiPath automation. Runs in two modes - **connector mode** and **manual mode**:

| Mode | When | `url` | Auth |
|---|---|---|---|
| **Connector** | Connector exists for the vendor but the specific operation is not curated | **Relative** to the connection's vendor base URL | Applied automatically from the bound connection |
| **Manual** | No connector exists, or public API with no auth needed | **Full URL** | You supply all headers, including auth |

## Connector-Mode Rules

- `url` must be **relative**. Wrong: `"url": "https://example.atlassian.net/rest/api/2/issue"`. Right: `"url": "/issue"`.
- The connection's base URL is prepended automatically.
- The auth header is applied automatically - do not set `Authorization`.
- **`application/json` only - request and response.** No other content type is supported. If the operation requires or returns a non-JSON body, connector mode cannot call it - use a curated connector activity.
- Get the exact vendor base URL for a connection via (so you can compose the relative `url` correctly):

```bash
uip is connections base-url "<connection-id>" --output json
# → { "Data": { "BaseUrl": "https://api.atlassian.com/ex/jira/<site>/rest/api/2" } }
```

## Manual-Mode Rules

- `url` is the **fully qualified URL**.
- No connection is bound - you supply everything needed to make the call: URL, headers (including auth if needed), query params, and body.

## Authoring Helper: `http-request` command

Authoring a Managed HTTP Request payload requires concrete vendor values - IDs, field names, endpoint paths. Use `http-request` command to call any vendor API directly through the connection - same auth, same base URL the Managed HTTP Request will use at runtime.

### When the Agent Needs `http-request` command

Use `http-request` command to resolve any of the following before authoring the Managed HTTP Request payload:

- **Identifier lookups.** Resolve a human-friendly name to the vendor's internal ID. Examples: project key from a project name, channel ID from a channel name, user ID from email/name, custom-field IDs.
- **Required and optional fields** the vendor expects in the request body
- **Endpoint paths, query params, pagination tokens** before committing to a payload
- **Vendor error responses** for unsupported parameters or permissions

### Command

```bash
uip is resources run create "<connector-key>" http-request \
  --connection-id "<id>" \
  --body '{"method":"<method>","url":"<relative-path>"}' --output json
```

| `body` field | Required | Notes |
|---|---|---|
| `method` | Yes | Uppercase HTTP verb |
| `url` | Yes | **Relative** to the connection's vendor base URL (same convention as Managed HTTP Request connector mode) |
| `headers` | No | Extra headers. Do NOT set `Authorization`. |
| `body` | For POST/PUT/PATCH | **Stringified** JSON. Only `application/json` is supported today — no other content type. |

`http-request` command uses the same connection that Managed HTTP Request will use at runtime, so auth + base URL are applied automatically - same convention as Managed HTTP Request itself.

### Read-Only During Authoring

When using the `http-request` command, use `GET` method only, as `POST` / `PATCH` / `PUT` / `DELETE` mutate vendor state, often irreversibly.

Exception: the user asks you to actually run the operation now, not just author it.

## Worked Example: Jira Create Issue

User wants to create a Jira issue. Before composing the Managed HTTP Request payload, the agent needs the project key, issue type ID, and required custom fields. All resolved via `http-request` command GETs.

```bash
# 1. Resolve project key (user said "Engineering project").
uip is resources run create uipath-atlassian-jira http-request \
  --connection-id "<id>" \
  --body '{"method":"GET","url":"/project/search?query=Engineering"}' --output json
# → key "ENG"

# 2. For project ENG, get available issue types + required custom fields.
uip is resources run create uipath-atlassian-jira http-request \
  --connection-id "<id>" \
  --body '{"method":"GET","url":"/issue/createmeta?projectKeys=ENG&expand=projects.issuetypes.fields"}' \
  --output json
# → match "Task" → id "10001"; required custom field: customfield_10010 (Story Points)
```

3. (Optional) Confirm resolved values with the user.

4. Compose the Managed HTTP Request payload. The actual configuration command and schema are consumer-specific — the request body Managed HTTP Request will send to Jira at runtime looks like:

```json
{
  "method": "POST",
  "url": "/issue",
  "body": {
    "fields": {
      "project": { "key": "ENG" },
      "issuetype": { "id": "10001" },
      "summary": "Fix coder evals",
      "customfield_10010": 3
    }
  }
}
```

All steps 1-2 are GETs because we are in the authoring phase. The POST to `/issue` happens at runtime, performed by Managed HTTP Request - never by CLI during authoring.

## Critical Rules

1. **Do NOT set the `Authorization` header manually in connector mode.** Auth is applied automatically by the connection. Setting it yourself can leak or override the token.
2. **Do NOT use an absolute URL in connector-mode `url`.** Wrong: `"url": "https://example.atlassian.net/rest/api/2/project"`. Right: `"url": "/project"`.
3. **Do NOT issue writes via CLI during authoring.** See "Read-Only During Authoring" above.
4. **Do NOT guess the base URL.** Use `uip is connections base-url <connection-id>`.
5. **In connector mode, request and response bodies are `application/json` only.** No other content type is supported; do NOT set `Content-Type` to anything else. Same rule applies to the `http-request` helper command body (it runs through a connection). Manual mode has no such limit — you supply your own `Content-Type` and body.
