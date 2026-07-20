---
confidence: high
---

# Jira Scope — Response Was Not Recognized As JSON / HTTP 500

## Context

What this looks like:
- A child Jira activity (Get Issue, Search Issues, Create Issue) faults with:
  - `Response was not recognized as JSON`, or
  - an HTTP `500 (Internal Server Error)` / `Response status code does not indicate success: 500`.
- Authentication **succeeded** — the scope opened; the failure is on the REST call, not the credential. (If the fault is `Authentication information is invalid` at scope open, use the authentication playbook instead.)
- The REST client received HTML or an unexpected body where it expected a JSON document, so deserialization failed.

What can cause it:
- **R1 — `Server URL` points past the root instance.** The classic pack expects the bare instance root (`https://<domain>.atlassian.net`) and builds `/rest/api/...` paths onto it. A `Server URL` that ends in `/secure/Dashboard.jspa`, a project key, or a `/browse/<KEY>` link routes the REST call to an HTML page; the response is HTML, not JSON, → `Response was not recognized as JSON`.
- **R2 — on-premises Server / Data Center instance.** The classic `UiPath.Jira.Activities` pack is built and tested natively for Jira **Cloud**. Against an on-premises **Server / Data Center** host, default endpoints / context paths can diverge (e.g. a `/jira` context path, different REST routing), returning structural `5xx` errors or non-JSON bodies the pack cannot parse.

What to look for:
- The trailing segment of `Server URL`: does it end in `.atlassian.net` (root) or carry an appended `/secure/...`, `/browse/...`, or project path?
- The host shape: `*.atlassian.net` (Cloud) vs a custom corporate host / IP with a context path (likely Server / Data Center).

## Investigation

1. Read the error from job evidence. Confirm it is `Response was not recognized as JSON` or an HTTP `5xx` on a **child** Jira activity, and that the scope itself opened (no auth fault). This separates it from the authentication family.
2. Read the `Jira Scope` `Server URL` from the `.xaml`. Inspect the literal for an appended path beyond the instance root.
3. Classify the host: `*.atlassian.net` → Jira Cloud; a custom host / on-prem hostname with a context path → likely Server / Data Center.
4. Decide R1 vs R2:
   - Root host is correct but a dashboard/project path is appended → **R1**.
   - Host is an on-premises Server / Data Center instance → **R2**.

## Resolution

- **R1 — URL truncation:** set `Server URL` to the bare instance root only. Example: change `https://acme.atlassian.net/secure/Dashboard.jspa` → `https://acme.atlassian.net`. Let the activities append their own `/rest/api/...` paths; do not include dashboard, project, or `/browse/...` segments.
- **R2 — on-premises instance:** the classic pack targets Jira Cloud and is not guaranteed against Server / Data Center.
  - If a Cloud instance is available, point `Server URL` at it.
  - If the workflow must stay on-premises, do not rely on the classic pack's default endpoints; move the Jira calls to the **Integration Service** Jira connector (where supported) or to direct REST via the HTTP activities against the documented Server / Data Center REST paths.

After the fix, re-run; a child activity returning a parsed JSON result (issues, fields) confirms the routing is correct.

This is a high-confidence routing diagnosis when `Server URL` carries an appended path (R1). For R2, confirm the deployment type with the user before concluding — the same symptom can come from either an appended path or an unsupported on-prem endpoint.
