# Plan Generation + Approval Gate

## Plan Format

The plan is the first thing the user sees. It must be human-readable — no API method names,
no [Insights]/[SDK] routing labels, no chart-type jargon. Write it as a product manager
describing the dashboard to a stakeholder, not as a developer listing implementation details.

**Structure:**
1. Opening line: `Here's your **[Dashboard Name]** — [N] widgets. Confirm to build, or tell me what to change.`
2. Group widgets by theme when there are 4+ (e.g., **Overview** / **Trends** / **Detail**)
3. Each widget: `• **Widget Name (time range)** — plain-English sentence describing what it shows and why it's useful`
4. Closing "What you can do" block with 3–4 concrete examples

**Example output (use as the template):**

```
Here's your **Agent Health Dashboard** — 6 widgets. Confirm to build, or tell me what to change.

**Overview**
• **Active Agents** — How many agents are registered in your fleet right now
• **Overall Success Rate (30 days)** — Fleet-wide job success percentage over the past month
• **Average Run Duration (30 days)** — Typical time agents take to complete a job — useful for SLA planning

**Activity**
• **Invocation Volume (24h)** — Hourly chart of how busy your agents were today — spot load patterns
• **Error Rate Trend (7 days)** — Day-by-day error count across all agents — catch spikes early

**Usage**
• **Top Agents by Consumption (30 days)** — Which agents are using the most resources — useful for cost and capacity reviews

---
Say **"go ahead"** to build, or try:
• _"add governance violations for the last 30 days"_
• _"remove invocation volume"_
• _"change error trend to 14 days"_
• _"replace the table with a bar chart"_
```

**Rules for widget descriptions:**
- Focus on the business insight, not the data source
- Include the time range in the name when it's not "live"
- Use "spot", "track", "identify", "compare" — action verbs that explain why this widget matters
- Never mention: getAgents, getSummaryV2, Insights API, useInsights, KPI card, area chart, donut

## Approval Gate Rules
- ANY positive response → proceed to scaffold
  (yes, looks good, do it, go ahead, 👍, confirmed, ship it, build it)
- Widget edit request → update that widget line only, re-show ONLY the changed line, re-ask
- "Remove X" → remove from list, re-show updated plan, re-ask
- "Add X" → derive the right data source internally (never mention it), append with plain description, re-ask
- Rejection without edit → ask: "What would you like to change?"
- Never re-show the full plan after partial edits — show diffs only

## Standard Time Constants
**Both `startTime` AND `endTime` are required for all Insights API calls — omitting `endTime` causes 500 errors.**

Use these constants — do not compute date arithmetic inline:
```typescript
const NOW             = new Date().toISOString()                            // always required as endTime
const ONE_DAY_AGO     = new Date(Date.now() -    86_400_000).toISOString() // 24 hours
const SEVEN_DAYS_AGO  = new Date(Date.now() -   604_800_000).toISOString() // 7 days
const THIRTY_DAYS_AGO = new Date(Date.now() - 2_592_000_000).toISOString() // 30 days
const NINETY_DAYS_AGO = new Date(Date.now() - 7_776_000_000).toISOString() // 90 days
```

Every `useInsights` call must pass both:
```typescript
useInsights('agents.getErrors', { startTime: SEVEN_DAYS_AGO, endTime: NOW })
```

In the plan, map time frames to natural language: ONE_DAY_AGO → "today" or "24h",
SEVEN_DAYS_AGO → "last 7 days", THIRTY_DAYS_AGO → "last 30 days".

## Four-Axis Metric Decomposition (internal only — never shown to user)
For each metric, derive internally and use to build the description:
- **Shape**: `line | bar | area | donut | kpi | table`
- **Time frame**: `realtime | hourly | daily | weekly | monthly`
- **Aggregation**: `count | sum | avg | p50 | p95 | p99`
- **Service**: `SDK` or `Insights` (resolve via data-router.md)

## Anti-patterns
- Do NOT show [Insights] or [SDK] labels in the plan
- Do NOT mention API method names (getAgents, getSummaryV2, etc.)
- Do NOT mention chart types (KPI card, area chart) in the plan — describe the insight instead
- Do NOT start scaffolding before explicit approval
- Do NOT infer approval from silence or a question ("which folder?")
- Do NOT re-derive the entire plan if only one widget changes
- Do NOT show code, file paths, or technical terms in the plan
