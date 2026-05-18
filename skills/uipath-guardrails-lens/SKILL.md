---
name: uipath-guardrails-lens
description: "Inspect UiPath guardrails-analysis results — list jobs, submit new analysis windows, list violating agents in a date range, drill into runs and prompts. Calls user-token endpoints under /api/execution/guardrails/user/ on the local Agents backend at http://localhost:5001. Violation categories are PII, HarmfulContent, UserPromptAttacks. For agent.json guardrail authoring→uipath-agents."
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# UiPath Guardrails Lens

Read-only + submit-only access to UiPath guardrails analysis data. The CLI/agent equivalent of the guardian-lens dashboard. Use when the user wants to know **which agents violated guardrails in a given date range**, see analysis-job status, or trigger a new analysis run.

> **Local-dev only (today).** Calls `http://localhost:5001` directly. When the API ships through the UiPath gateway, swap the base URL for the gateway path.

## Critical Rules

1. **Auth from `~/.uipath/.auth`.** Run `uip login` first if `UIPATH_ACCESS_TOKEN` isn't set. Never hard-code tokens.
2. **Always send three headers** on every request — `Authorization: Bearer …`, `X-UiPath-Internal-AccountId: $UIPATH_ORGANIZATION_ID`, `X-UiPath-Internal-TenantId: $UIPATH_TENANT_ID`. Direct-mode calls (no gateway) need both id headers explicitly.
3. **Use the `/user/...` endpoint family.** Never call `/api/execution/guardrails/analysis-jobs` without the `/user/` prefix from this skill — those are S2S-only and require a client-credential token.
4. **Dates are `YYYY-MM-DD`** (`.NET DateOnly`). No timestamps, no timezones.
5. **Never pass `orgId` or `tenantId` in body or query.** The backend resolves them from session headers; passing them in the wire payload is ignored at best, surprising at worst.
6. **Use `curl -sf`** for parseable output and non-zero exit on HTTP errors. Pipe through `jq` for filtering/projection.
7. **POST submit is idempotent.** Re-submitting an overlapping window returns existing jobs under `existingJobs` and does NOT re-evaluate. Don't poll-spam — the scheduler picks the next pending job every 500ms and a typical job finishes within seconds.
8. **Empty agents list ≠ "no violations".** It can also mean "no analysis job has been run for this window yet". Check `GET /user/analysis-jobs` first when the result is empty.
9. **`guardrail` is a comma-joined sorted list** (e.g. `"HarmfulContent,PiiDetection"`), not a single value. Use `jq contains("X")`, not exact-match.

## When to Use This Skill

Triggers on user asks like:
- "Which agents violated guardrails last week?"
- "Show me PII / harmful-content / prompt-injection issues for <date range>"
- "Submit a guardrails analysis for <date range>"
- "What's the status of analysis job <guid>?"
- "Show me the failing prompts for run <runId>"
- "List runs for agent <name> in the last 7 days"
- Slash command `/uipath:guardrails-lens`

Do NOT trigger when:
- User is authoring an agent's guardrail policies (`agent.json`) → use `uipath-agents` instead.
- User wants to call the live guardrail validators directly (e.g. `bulk-validate`, `validate`) → use existing routes in the `uipath-agents` skill.

## Setup

### 1. Authenticate

```bash
uip login --output json
```

This writes credentials to `~/.uipath/.auth`. Required vars: `UIPATH_ACCESS_TOKEN`, `UIPATH_ORGANIZATION_ID`, `UIPATH_TENANT_ID`.

### 2. Source the env

```bash
set -a
. "$HOME/.uipath/.auth"
set +a
export AGENTS_BASE="${AGENTS_BASE:-http://localhost:5001}"
```

### 3. Sanity-check connectivity

```bash
curl -sf \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UiPath-Internal-AccountId: $UIPATH_ORGANIZATION_ID" \
  -H "X-UiPath-Internal-TenantId: $UIPATH_TENANT_ID" \
  -H "Accept: application/json" \
  "$AGENTS_BASE/api/execution/guardrails/user/analysis-jobs" | jq
```

Should return `[]` or a list of recent jobs. `401` ⇒ token expired (`uip login` again). `404` ⇒ backend not running locally or `/user/` route not yet deployed.

## API Reference

All routes are user-token authenticated and resolve org/tenant from session.

| Op | Method + Path | Body / Query | Returns |
|---|---|---|---|
| Submit job | `POST /api/execution/guardrails/user/analysis-jobs` | `{ "from": "YYYY-MM-DD", "to": "YYYY-MM-DD" }` | `{ newJobs[], existingJobs[] }` |
| Get job | `GET /api/execution/guardrails/user/analysis-jobs/{jobId}` | — | `GuardrailsAnalysisJobDto` |
| List jobs | `GET /api/execution/guardrails/user/analysis-jobs` | — | `GuardrailsAnalysisJobDto[]` |
| List agents | `GET /api/execution/guardrails/user/analysis/agents` | `?from=&to=` | `AgentSummaryDto[]` |
| List agent runs | `GET /api/execution/guardrails/user/analysis/agents/{agentId}/runs` | `?from=&to=&page=&pageSize=` | `PagedRunsResponse` |
| Get run detail | `GET /api/execution/guardrails/user/analysis/runs/{runId}` | — | `AgentRunDetailDto` |

## Primary Workflow — "Which agents violated guardrails in this interval?"

### Step 1 — Parse the interval

If the user says "last week", "yesterday", "May 1–7", etc., resolve to two `YYYY-MM-DD` dates (`FROM`, `TO`). Use the system clock for relative phrasing.

```bash
FROM="2026-05-01"
TO="2026-05-13"
```

### Step 2 — Confirm there's analysis data for the window

```bash
curl -sf \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UiPath-Internal-AccountId: $UIPATH_ORGANIZATION_ID" \
  -H "X-UiPath-Internal-TenantId: $UIPATH_TENANT_ID" \
  -H "Accept: application/json" \
  "$AGENTS_BASE/api/execution/guardrails/user/analysis-jobs" \
| jq --arg from "$FROM" --arg to "$TO" '
    [ .[] | select(.fromDate <= $to and .toDate >= $from) ]
    | map({ id, fromDate, toDate, status })'
```

- Empty array → no analysis run for this window. Offer Step 2a (submit) before continuing.
- Any item `status: "Pending"` or `"Running"` → wait. Optionally poll the specific id every 3-5 s.
- Any item `status: "Completed"` whose window covers `[FROM..TO]` → go to Step 3.

### Step 2a — (optional) Submit a new analysis job

```bash
curl -sf -X POST \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UiPath-Internal-AccountId: $UIPATH_ORGANIZATION_ID" \
  -H "X-UiPath-Internal-TenantId: $UIPATH_TENANT_ID" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{ \"from\": \"$FROM\", \"to\": \"$TO\" }" \
  "$AGENTS_BASE/api/execution/guardrails/user/analysis-jobs" | jq
```

The response splits into `newJobs[]` (just created) and `existingJobs[]` (already-covered sub-intervals; not re-evaluated). Poll any new job until `status: "Completed"`:

```bash
JOB_ID="<from response>"
curl -sf \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UiPath-Internal-AccountId: $UIPATH_ORGANIZATION_ID" \
  -H "X-UiPath-Internal-TenantId: $UIPATH_TENANT_ID" \
  -H "Accept: application/json" \
  "$AGENTS_BASE/api/execution/guardrails/user/analysis-jobs/$JOB_ID" | jq '.status'
```

If a poll loop is needed, sleep ≥ 3 s between calls and stop after ~20 iterations with a clear "still running, try again later".

### Step 3 — Query violating agents

```bash
curl -sf -G \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UiPath-Internal-AccountId: $UIPATH_ORGANIZATION_ID" \
  -H "X-UiPath-Internal-TenantId: $UIPATH_TENANT_ID" \
  -H "Accept: application/json" \
  --data-urlencode "from=$FROM" \
  --data-urlencode "to=$TO" \
  "$AGENTS_BASE/api/execution/guardrails/user/analysis/agents" \
| jq '[.[] | select(.violatingRuns > 0)]
      | sort_by(-.violatingRuns)
      | .[] | { agentName, violatingRuns, totalRuns, hasFailedRun }'
```

Empty result with `Completed` jobs in the window ⇒ no agents violated anything. Empty result with no jobs ⇒ go back to Step 2a.

### Step 4 — Drill into a specific agent's runs

```bash
AGENT_ID="<from step 3>"
curl -sf -G \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UiPath-Internal-AccountId: $UIPATH_ORGANIZATION_ID" \
  -H "X-UiPath-Internal-TenantId: $UIPATH_TENANT_ID" \
  -H "Accept: application/json" \
  --data-urlencode "from=$FROM" \
  --data-urlencode "to=$TO" \
  --data-urlencode "pageSize=50" \
  "$AGENTS_BASE/api/execution/guardrails/user/analysis/agents/$AGENT_ID/runs" \
| jq '.items[] | select(.violatingPromptCount > 0)
                | { id, startedAt, status, durationMs, violatingPromptCount, violationTypes }'
```

### Step 5 — Show the failing prompts for a run

```bash
RUN_ID="<from step 4 .id (== traceId)>"
curl -sf \
  -H "Authorization: Bearer $UIPATH_ACCESS_TOKEN" \
  -H "X-UiPath-Internal-AccountId: $UIPATH_ORGANIZATION_ID" \
  -H "X-UiPath-Internal-TenantId: $UIPATH_TENANT_ID" \
  -H "Accept: application/json" \
  "$AGENTS_BASE/api/execution/guardrails/user/analysis/runs/$RUN_ID" \
| jq '.prompts[] | select(.violation != null)
                  | { index, guardrail, violation, textPreview: (.text[0:200]) }'
```

## Response Shapes

### `AgentSummaryDto` — list-agents

```jsonc
{
  "agentId": "<guid>",
  "agentName": "Converter.agent.ConverterAgent",
  "totalRuns": 12,
  "violatingRuns": 3,
  "hasFailedRun": false,
  "hasViolation": true
}
```

### `AgentRunSummaryDto` — items of list-agent-runs

```jsonc
{
  "id": "<traceId>",
  "agentId": "<guid>",
  "agentName": "...",
  "startedAt": "2026-05-13T14:00:00Z",
  "durationMs": 1240,
  "status": "Success" | "Failed" | "Cancelled" | "Running" | "Unknown",
  "promptCount": 3,
  "violatingPromptCount": 1,
  "violationTypes": ["HarmfulContent", "PiiDetection"]
}
```

### `AgentRunDetailDto` — get-run

```jsonc
{
  "id": "<traceId>",
  "agentId": "<guid>",
  "agentName": "...",
  "startedAt": "...",
  "durationMs": 1240,
  "status": "Success",
  "prompts": [
    {
      "id": "<spanId>",
      "index": 0,
      "text": "Convert the input string ...",
      "offsetMs": 0,
      "durationMs": 0,
      "violation": "Failed",
      "guardrail": "HarmfulContent,PiiDetection"
    }
  ]
}
```

### `GuardrailsAnalysisJobDto`

```jsonc
{
  "id": "<guid>",
  "fromDate": "2026-05-01",
  "toDate": "2026-05-13",
  "status": "Pending" | "Running" | "Completed" | "Failed",
  "submittedAt": "...",
  "startedAt": null,
  "completedAt": null,
  "error": null
}
```

## What NOT to Do

- **Don't call S2S routes.** `/api/execution/guardrails/analysis-jobs` (without `/user/`) requires `[Authorize(Policy = Policies.S2S)]`. Trying it with a user token returns `403`.
- **Don't pass `orgId` / `tenantId` in body or query.** The user-token endpoints have no such parameters; the backend reads the session populated from the auth headers.
- **Don't exact-match on `prompt.guardrail`.** Multiple failed guardrails are comma-joined alphabetically (e.g. `"HarmfulContent,PiiDetection"`). Use `jq 'select(.guardrail | contains("PiiDetection"))'`.
- **Don't map run status numerically.** The API projects status to a string (`Success`/`Failed`/`Cancelled`/`Running`/`Unknown`).
- **Don't expect retroactive backfill.** Re-submitting a window that overlaps an existing job returns the existing job under `existingJobs`. To re-evaluate, the existing job must be deleted (no public endpoint today — manual SQL).
- **Don't conflate `hasFailedRun` with `hasViolation`.** They're independent: a run can succeed (status `Success`) and still have violating prompts; conversely a `Failed` run can carry zero violations (the run failed for non-guardrail reasons).
- **Don't poll a job faster than every 3 s.** The scheduler claims one job at a time; polling tighter doesn't speed anything up.

## Quick `jq` recipes

```bash
# Top 5 violating agents in window
curl ... agents?from=&to= | jq -r '
  sort_by(-.violatingRuns) | .[0:5]
  | .[] | "\(.agentName)\t\(.violatingRuns)/\(.totalRuns)"'

# Count violations by guardrail type across an agent's runs
curl ... agents/$AGENT_ID/runs?... | jq '
  [.items[].violationTypes // []] | flatten
  | group_by(.) | map({ type: .[0], count: length })'

# Prompts that failed PII specifically
curl ... runs/$RUN_ID | jq '
  .prompts[] | select(.guardrail // "" | contains("PiiDetection"))'

# Latest 10 jobs with status
curl ... analysis-jobs | jq '
  sort_by(.submittedAt) | reverse | .[0:10]
  | .[] | { id, fromDate, toDate, status, submittedAt }'
```
