# Get a Process from Automation Hub

Fetches one process (by id or search) and its documents from Automation Hub, authenticating with the **user's cloud token** — no admin OpenAPI token required. Read-only: this flow never writes.

> Auth, base/gateway URL, headers (and the header to **never** send), and the read endpoints are defined in [`api-endpoints.md`](api-endpoints.md). Resolve `$ACCESS_TOKEN` / `$BASE_URL` / `$ORG` / `$TENANT` via the shared **Authentication** section in [`../SKILL.md`](../SKILL.md) before starting.

## Step 1: Resolve the process

- If the caller gives a **process id**, use it directly.
- Otherwise search by name:
  ```bash
  curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/automations?search=$QUERY&limit=20"
  ```
  If one clear match → use its `process_id`. If several → show a short list (name + id + owner) and ask the user to pick. If none → tell the user and stop.

## Step 2: Fetch the process

```bash
curl -s -w "\n%{http_code}" -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/automations/$PROCESS_ID"
```
- **200** → keep the record; project to the useful fields for display (name, status/phase, category, owner, description). The raw record is large — don't dump it all unless asked.
- **401** → re-authenticate. **403** → the user can't view this process. **404** → no such process.

## Step 3: Fetch the documents

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/automations/$PROCESS_ID/documents"
```
List each document (name, type, `FileId`/download reference). If the caller wants the bytes, follow the download reference; otherwise just list them. *(Optional: `/automations/$PROCESS_ID/components` for linked components.)*

## Step 4: Present

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
- Read-only: this flow never writes. To create/attach, use the [`publish-process.md`](publish-process.md) flow.
- **Open dependency:** in a hosted runtime (Process Scribe/Delegate) the cloud token is expected via the environment (see the shared Authentication section). Confirm the runtime provides it before relying on it in production.
