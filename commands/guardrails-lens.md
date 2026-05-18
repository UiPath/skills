---
description: List UiPath agents that violated guardrails in a date range. Optionally submits a new analysis job and polls until completion.
---

# Show guardrails violations for a date range

Help the user answer the question: **which agents violated UiPath guardrails (PII / HarmfulContent / UserPromptAttacks) in a given date range?**

This command activates the `uipath-guardrails-lens` skill end-to-end. The full reference (curl recipes, jq filters, response shapes, anti-patterns) lives in `skills/uipath-guardrails-lens/SKILL.md`.

## Steps

1. **Resolve the date range.** Default to the last 7 days. If the user already gave a range in the conversation (e.g. "last week", "May 1–7", "yesterday"), use that directly — do not re-ask. Otherwise prompt with `AskUserQuestion` for the range in `YYYY-MM-DD` form (`from`, `to`).

2. **Verify auth.** If `~/.uipath/.auth` is missing or `UIPATH_ACCESS_TOKEN` is unset, tell the user to run `uip login` and stop. Source the auth file once and export `AGENTS_BASE="${AGENTS_BASE:-http://localhost:5001}"`.

3. **Check coverage.** `GET /user/analysis-jobs`. Filter to jobs whose `[fromDate..toDate]` overlaps the user's window.
   - **Covered + Completed** → go to step 5.
   - **Covered but Pending/Running** → tell the user to wait, optionally poll the specific id every 5 s for up to ~1 min. Do not exceed 20 polls.
   - **Not covered** → step 4.

4. **Offer to submit a new analysis job.** `AskUserQuestion`-confirm before submitting. On yes: `POST /user/analysis-jobs` with `{from, to}`. Poll each new job id until `Completed` (sleep 3 s, max 20 retries). On `Failed`, surface the `error` field.

5. **Query violating agents.** `GET /user/analysis/agents?from=&to=` — filter `violatingRuns > 0`, sort descending, present as a small table:

   ```
   AGENT                                       VIOLATING / TOTAL    HAD FAILED RUN?
   Converter.agent.ConverterAgent                3 / 12             no
   Echo.agent.EchoAgent                          1 / 4              yes
   ```

   If empty with `Completed` jobs in the window: tell the user "no agents violated guardrails in this window" — clean signal, not an error.

6. **Offer drill-down.** Ask which agent (if any) to inspect. On selection:
   - `GET /user/analysis/agents/{agentId}/runs?from=&to=&pageSize=50` → show runs with `violatingPromptCount > 0` (id, startedAt, status, violationTypes).
   - Ask which run to inspect. On selection: `GET /user/analysis/runs/{runId}` → show each failing prompt with `guardrail` and a 200-char preview of `text`.

## Notes

- **Local-dev only today.** This command talks directly to `http://localhost:5001`. When the API ships through the UiPath gateway, the skill author will update the base URL.
- **POST is idempotent.** Re-submitting an overlapping window returns existing jobs under `existingJobs` — no double-evaluation.
- **`guardrail` is a comma-joined sorted list** (e.g. `"HarmfulContent,PiiDetection"`); use `contains("...")` rather than exact match when filtering.
- **Never include `orgId` or `tenantId` in body or query** — the user endpoints resolve them server-side from the auth headers.
