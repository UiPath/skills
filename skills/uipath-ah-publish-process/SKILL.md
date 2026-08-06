---
name: uipath-ah-publish-process
description: "Publish an approved business process (and its PDD/SDD documents) to UiPath Automation Hub via the Open API, using the user's cloud login — no admin OpenAPI token needed. Use when a process has been captured/approved (e.g. by Process Scribe) and needs to be written to Automation Hub as the system of record. To read a process back→uipath-ah-get-process."
allowed-tools: Bash, Read, AskUserQuestion
user-invocable: true
---

# Publish a Process to Automation Hub

Creates one process in Automation Hub from a schema-driven payload and attaches its documents (PDD/SDD). Authenticates with the **user's cloud token** — the user does **not** need an admin-generated OpenAPI token.

## Step 0: Read the API reference

Read `references/api-endpoints.md` first. It defines the cloud-token auth model, the base URL, the exact headers (and which header to **never** send), and every endpoint below.

## Step 1: Authenticate (cloud token)

Resolve the cloud token + base URL + org + tenant using the priority order in the reference:
1. **Runtime env-auth** — `UIPATH_CLI_AUTH_TOKEN` + `UIPATH_CLI_ORGANIZATION_NAME`/`UIPATH_CLI_TENANT_NAME` (how UiPath Delegate provides it; or `UIPATH_ACCESS_TOKEN`/`UIPATH_URL` from a parent `uip`), else
2. `~/.uipath/.auth` (after `uip login`), else
3. ask the user to paste a cloud token + org + tenant.

Use whichever token you resolved as `$ACCESS_TOKEN` below.

Then verify connectivity with a cheap call (this also fetches the idea flows you need next):

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
- **401** → re-authenticate (Step 1). **409** → duplicate name; ask the user for a new name or stop.

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
- The schema is fetched live, so the skill adapts automatically if fields change on the tenant.
- Idempotency: AH is the system of record for the *approved* process — publish once after approval. A duplicate name returns 409; decide up front whether to update-in-place (out of scope here) or treat as an error.
- **Open dependency:** in a hosted runtime (e.g. Process Scribe/Delegate) the cloud token is expected to be injected via the environment (Step 1, option 1). Confirm the runtime provides `UIPATH_ACCESS_TOKEN` (or an equivalent) before relying on it in production.
