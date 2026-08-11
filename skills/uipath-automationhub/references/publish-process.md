# Publish a Process to Automation Hub

Creates one process in Automation Hub from a schema-driven payload and attaches its documents (PDD/SDD). Authenticates with the **user's cloud token** — the user does **not** need an admin-generated OpenAPI token.

> Auth, base/gateway URL, headers (and the header to **never** send), and every endpoint below are defined in [`api-endpoints.md`](api-endpoints.md). Resolve `$ACCESS_TOKEN` / `$BASE_URL` / `$ORG` / `$TENANT` via the shared **Authentication** section in [`../SKILL.md`](../SKILL.md) before starting.

## Step 1: Verify connectivity (and fetch the idea flows)

Verify the resolved token with a cheap call — this also fetches the idea flows you need next:

```bash
curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/idea-flows"
```

- **200** → save the `data` array (reused in Step 2) and tell the user "Connected to Automation Hub."
- **401** → token missing/expired: if it came from `~/.uipath/.auth`, ask the user to run `uip login` again; re-resolve and retry. **Never** add `x-ah-openapi-auth` to "fix" a 401 — that routes to the admin-token path and guarantees failure.
- **403** → the user is authenticated but lacks AH access on this tenant.
- **404 / network** → wrong URL or AH not enabled; confirm the org/tenant.

Do not proceed until you have a 200.

## Step 2: Pick the idea flow

From the saved `/idea-flows` `data` array:
1. Default to the entry whose `Idea flow name` contains "Business Process" (case-insensitive) and take its `Idea flow ID`.
2. If the caller specified a different flow, use that. If neither is found, list the available names + IDs and ask the user which to use. If none exist, tell the user Business Process flows may not be enabled and stop.

Store `idea_flow_id`.

## Step 3: Fetch the schema

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/idea-schema?idea_flow_id=$IDEA_FLOW_ID"
```

Parse `data.properties.schema.properties` for the field catalog (Assessment Type > Section > Question; note types, required flags, enum `answer_option` codes/labels) and keep `data.user_inputs` as the payload template. The process-name question (key contains `OVERVIEW_NAME`) is **required**.

## Step 4: Assemble the process payload

Gather the process fields — from the caller's supplied data (e.g. a Process Scribe hand-off object) or by asking the user. Then build `user_inputs` from the template:
- Place each value in its `AssessmentType > section > question` slot.
- Follow the template's wrapping per field: most are `{ "value": <v> }`; owner/submitter questions take a direct string.
- Convert enum labels to their `answer_option` codes; send integers as numbers.
- Include only sections that have at least one populated field.
- The `OVERVIEW_NAME` question **must** be present and non-empty.

Show the user a concise preview (name + key fields, and "show raw JSON" on request) and get a confirm before writing.

## Step 5: Create the process

```bash
curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/idea-from-schema"
```
where `$PAYLOAD` is `{ "idea_flow_id": <id>, "user_inputs": { … } }`.

- **201** → read `process_id` from the **top level** of the response (not nested in `data`). Keep it for Step 6.
- **400** → show the offending field/value; fix and retry (commonly a missing `OVERVIEW_NAME` or a bad enum code).
- **401** → re-authenticate. **409** → duplicate name; ask the user for a new name or stop.

## Step 6: Attach documents (PDD/SDD)

For each document the caller wants attached (link-based — an embed/link URL + metadata, per the reference):

```bash
curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$DOC_PAYLOAD" \
  "$BASE_URL/$ORG/$TENANT/automationhub_/api/v1/openapi/automations/$PROCESS_ID/documents"
```

Build `$DOC_PAYLOAD` per `ProcessDocumentValidator` (document name + `embed_link` + `document_type_id`; confirm required fields against `processDocumentRequest.schema.ts`). Record each returned `document_id`. On 400, surface the validation message and continue with the remaining documents.

> Raw file-byte upload is not supported here (the `media` endpoint is not usable yet). Attach documents by link/URL. If the caller only has bytes, host them first and pass the link.

## Step 7: Report

Summarize: the created `process_id`, the attached document ids (and any that failed), and a link to view it:

```
Published to Automation Hub:
  Process: <name>  (process_id: <id>)
  Documents: PDD ✓ (doc 12), SDD ✓ (doc 13)
  View: {baseUrl}/{org}/{tenant}/automationhub_/process-repository
```

## Notes

- **Cloud token only** — never send `x-ah-openapi-auth` / `x-ah-openapi-app-key`. Authorization is the user's real AH permissions.
- **Always** `POST /idea-from-schema` (not `/automations`) and **always** include `idea_flow_id`.
- The schema is fetched live, so the flow adapts automatically if fields change on the tenant.
- Idempotency: AH is the system of record for the *approved* process — publish once after approval. A duplicate name returns 409; decide up front whether to update-in-place (out of scope here) or treat as an error.
- To read a process back, use the [`get-process.md`](get-process.md) flow.
