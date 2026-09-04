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
- **401** → re-authenticate. **403** → the user can't view this process. **404** → no such process — *unless* the body says `not found in organization` (or the call 3xx-redirects to `portal_/unregistered`, or answers **422 tenant lookup**), which means AH itself is not available on this tenant: report the matching message from [`api-endpoints.md`](api-endpoints.md) (**Automation Hub not available on this tenant**) and stop.

## Step 3: Fetch the documents

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/automations/$PROCESS_ID/documents"
```

The list is under **`data.documents[]`** (standard envelope). Each entry carries `document_id`, `document_title`, `document_type_id`, and **either** a `file_id` (file-backed) **or** an `embed_link` (link-backed). *(Optional: `/automations/$PROCESS_ID/components` for linked components.)*

## Step 3b: Download a document (when the caller wants the bytes)

Only **file-backed** documents can be downloaded, and the endpoint takes the **`file_id`** — not the `document_id`:

```bash
curl -s -w "%{http_code}" -H "Authorization: Bearer $ACCESS_TOKEN" \
  -o "<destination-path>" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/download/file/$FILE_ID"
```

- The response body is the **raw file** (no JSON envelope) — always save with `-o`; pick the filename from `document_title` or ask the user.
- **200** → confirm the file exists and is non-empty before reporting success.
- A **link-backed** document (`file_id` absent) has nothing to download — present its `embed_link` to the user instead. Never invent a download URL for it.
- Do not guess other paths (`/documents/{id}/download`, `/files/{id}`, …) — `/download/file/{file_id}` is the only download route.

## Step 4: Present

```
Process: <name>  (process_id: <id>)
  Status:   <phase/status>
  Category: <category>
  Owner:    <owner>
  View:     {baseUrl}/{org}/{tenant}/automationhub_/automation-profile/{process_slug}/documentation
Documents:
  - PDD  (document_id 12, file_id 42 — downloadable)
  - SDD  (document_id 13, embed_link — link only)
```

Offer to return the raw JSON, download the documents, or fetch components if relevant.

## Notes

- **Cloud token only** — never send `x-ah-openapi-auth` / `x-ah-openapi-app-key`. You see exactly what the user's AH permissions allow.
- Read-only: this flow never writes. To create/attach, use the [`publish-process.md`](publish-process.md) flow.
- **Open dependency:** in a hosted runtime (Process Scribe/Delegate) the cloud token is expected via the environment (see the shared Authentication section). Confirm the runtime provides it before relying on it in production.
