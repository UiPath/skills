# API Workflow Review Checklist

Quality checklist for UiPath API Workflow projects — serverless JSON workflows (`Workflow.json`, Serverless Workflow DSL: top-level `document` with `dsl` version + `do[]` activity array).

> **Unit of Work:** Before the technical checks below, complete Step 3a (Unit of Work Discovery) from SKILL.md. Declared unit: the request input schema. Actual unit: external calls per request. One request fanning out to N vendor writes over a sub-collection of the input is one-to-many — assess per Step 3a.

> **Read-only:** fixes route to `uipath-api-workflow`.

## 1. Structural Validation

### Project Markers

| Check | Severity | How to Verify |
|---|---|---|
| `project.uiproj` exists with `"ProjectType": "Api"` | Critical | Read project.uiproj |
| Legacy `project.json`-only layout (no `.uiproj`) | Warning | Packs and runs but Studio Web rejects it (`invalid_project_folder`) — flag, route to `uipath-api-workflow` for conversion |
| `Workflow.json` is valid JSON with `document.dsl` and `do[]` | Critical | Read Workflow.json |
| `entry-points.json` present | Warning | `ls entry-points.json` |
| `bindings_v2.json` present (if connector activities used) | Warning | `ls bindings_v2.json` |

### CLI Validation

```bash
uip api-workflow validate "<WORKFLOW_JSON>" --output json
```

Offline static validation — no auth, no network, no side effects (safe for review). Catches: malformed JSON, unknown `activityType` values, per-activity required keys, missing `metadata.activityType`/`displayName`, duplicate or empty-named variables, empty task lists.

- `Result: "Success"`, `Data.Status: "Valid"` — report any `Data.Warnings`.
- `Result: "Failure"` — report each semantic error with its JSON path. Focus on semantic-tail errors (`Unknown activityType 'X'`, missing required keys) — AJV `oneOf` fanout duplicates are noise, not separate findings.

> **Do NOT run `uip api-workflow run`.** It executes the workflow — Integration Service vendor calls cause real side effects (emails sent, tickets created, files uploaded). Runtime verification is an operator task — route to `uipath-api-workflow`.

> If the CLI reports an unknown command for `api-workflow validate` (older CLI), record it under "Rules Skipped" and run the manual checks below.

## 2. Design Quality

| Check | Severity | How to Verify |
|---|---|---|
| Input validation before business logic (required-field / type checks first) | Warning | Inspect first activities in `do[]` |
| Structured error responses (Response activity with 4xx for bad input, not deep null failures) | Warning | Check Response activities |
| TryCatch wraps vendor / HTTP calls | Warning | Check for TryCatch around connector and HTTP activities |
| No inline secrets (tokens, API keys in headers or configuration) | Critical | Grep Workflow.json for `token`, `apiKey`, `secret`, `password`, `Bearer ` |
| Connector activities reference connections by ID — no hardcoded credentials | Critical | Check connector `metadata.configuration` |
| Long-running logic not synchronous (hard timeout ~10 minutes; 5 min CPU for serverless) | Warning | Bulk processing / chained calls → flag; recommend async pattern |
| Variables have non-empty names and types; no duplicates | Warning | Covered by `validate` — carry its findings verbatim |

## Common Issues

### No Input Schema Enforcement

**Symptom:** API workflow has input schema defined, but the first steps do not validate required inputs. Callers can send malformed payloads and the workflow tries to process them.

**Impact:** NullReferenceException deep in the logic instead of a clear 400 Bad Request. Consumers get unhelpful errors.

**Detection:** Inspect API workflow's initial activities. Check for explicit validation (required-field checks, type validation) before business logic begins.

**Fix:** Add input validation as the first step. Return structured 400 responses with field-specific error messages.

**Severity:** Warning

### Synchronous Long-Running API Workflow

**Symptom:** API workflow performing long-running logic (DB migrations, bulk processing, chained API calls) synchronously. Hard timeout: 10 minutes (5 min CPU for serverless).

**Impact:** Request times out with no result, no recovery path. Caller sees timeout error. Work may be partially complete with no rollback.

**Detection:** Long-running logic visible in `do[]` (bulk loops over external calls, chained vendor requests).

**Fix:** Convert to async pattern — accept request, return job ID, process in background (via queue), let caller poll. Or use `Wait for Event and Resume` for suspend/resume.

**Severity:** Warning
