---
name: uipath-ah-get-process
description: "Fetch a business process and its documents (PDD/SDD) from UiPath Automation Hub via the Open API, using the user's cloud login — no admin OpenAPI token needed. Use to read back a process by id or search, and to retrieve its attached documents (e.g. for Process Scribe dedup / related-idea lookups). To create/attach instead→uipath-ah-publish-process."
allowed-tools: Bash, Read, AskUserQuestion
user-invocable: true
---

# Get a Process from Automation Hub

Fetches one process (by id or search) and its documents from Automation Hub, authenticating with the **user's cloud token** — no admin OpenAPI token required.

## Step 0: Read the API reference

Read `references/api-endpoints.md` first — cloud-token auth, base URL, headers (and the header to **never** send), and the read endpoints.

## Step 1: Authenticate (cloud token)

Resolve the cloud token + base URL + org + tenant in priority order: **runtime env-auth** (`UIPATH_CLI_AUTH_TOKEN` + `UIPATH_CLI_ORGANIZATION_NAME`/`UIPATH_CLI_TENANT_NAME` — how UiPath Delegate provides it; or `UIPATH_ACCESS_TOKEN`/`UIPATH_URL`) → `~/.uipath/.auth` (after `uip login`) → ask the user to paste a token + org + tenant. Never fall back to an admin OpenAPI token, and never send `x-ah-openapi-auth`.

## Step 2: Resolve the process

- If the caller gives a **process id**, use it directly.
- Otherwise search by name:
  ```bash
  curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/automations?search=$QUERY&limit=20"
  ```
  If one clear match → use its `process_id`. If several → show a short list (name + id + owner) and ask the user to pick. If none → tell the user and stop.

## Step 3: Fetch the process

```bash
curl -s -w "\n%{http_code}" -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/automations/$PROCESS_ID"
```
- **200** → keep the record; project to the useful fields for display (name, status/phase, category, owner, description). The raw record is large — don't dump it all unless asked.
- **401** → re-authenticate (Step 1). **403** → the user can't view this process. **404** → no such process.

## Step 4: Fetch the documents

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/automations/$PROCESS_ID/documents"
```
List each document (name, type, `FileId`/download reference). If the caller wants the bytes, follow the download reference; otherwise just list them. *(Optional: `/automations/$PROCESS_ID/components` for linked components.)*

## Step 5: Present

```
Process: <name>  (process_id: <id>)
  Status:   <phase/status>
  Category: <category>
  Owner:    <owner>
Documents:
  - PDD  (FileId: 12)
  - SDD  (FileId: 13)
```

Offer to return the raw JSON, download the documents, or fetch components if relevant.

## Notes

- **Cloud token only** — never send `x-ah-openapi-auth` / `x-ah-openapi-app-key`. You see exactly what the user's AH permissions allow.
- Read-only: this skill never writes. To create/attach, use `uipath-ah-publish-process`.
- **Open dependency:** in a hosted runtime (Process Scribe/Delegate) the cloud token is expected via the environment (Step 1). Confirm the runtime provides it before relying on it in production.
