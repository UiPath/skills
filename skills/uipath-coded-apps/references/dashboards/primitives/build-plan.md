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

## External Client Question (append to plan, before approval)

After the plan example, append this block verbatim before asking for approval:

---

**One more thing before I build:**

Your dashboard needs an OAuth app to let users sign in securely.

Do you have an existing non-confidential external app in UiPath?
- **Yes** — reply with the Client ID and I'll use it
- **No** — reply "create one" and I'll create one now before building (adds ~30 seconds)

---

This is part of the approval gate interaction. After the user responds to the plan edits AND provides the client ID decision, the agent proceeds. Both responses count as a single "approval."

- If user replies with a Client ID → extract it and proceed to Phase 6 with `clientId` set
- If user replies "create one" → proceed to Phase 5.5 (external client creation) before Phase 6

**Rules for widget descriptions:**
- Focus on the business insight, not the data source
- Include the time range in the name when it's not "live"
- Use "spot", "track", "identify", "compare" — action verbs that explain why this widget matters
- Never mention: getAgents, getSummaryV2, Insights API, useInsights, KPI card, area chart, donut

## Graceful Degradation — When a Metric Can't Be Built Exactly

When the user's requested metric has no direct API match, use a proxy and say so.
**Always disclose approximations in the plan — never silently substitute.**

### Wording patterns

| Situation | How to phrase it in the plan |
|---|---|
| Using a proxy metric | "• **[Title]** — I'll show [proxy] as an approximation for [requested]; [brief reason why]" |
| Metric doesn't exist at all | Omit it and explain: "I wasn't able to include [metric] — [brief reason]. I've replaced it with [alternative] which shows [value]." |
| Derived calculation approximated | "• **[Title]** — [what's shown]; note this is [count/volume], not a [%/rate] — divide by total runs for the percentage" |
| Time comparison requested | Use two separate KPI cards: "• **[Title] — This Month** and **[Title] — Last Month** (side by side for comparison)" |

### Examples

```
Here's your Dashboard — 4 widgets. One approximation noted below.

**Overview**
• **Agent Productivity (30 days)** — How busy your agents have been;
  I'm using invocation volume as a proxy since a direct productivity
  score isn't in the analytics API yet
• **Job Success Rate (today)** — Percentage of today's jobs that completed
  successfully vs failed; note this reflects completed jobs only

**What you can do:**
• "Replace productivity with error count instead" — I'll swap it
• "That's fine, go ahead" — I'll build it with the approximation noted
```

### When to omit entirely

If a user asks for something the API genuinely cannot provide (e.g., "real-time agent CPU usage",
"agent cost in dollars", "per-user agent attribution"), omit the widget and explain clearly:

```
⚠ I couldn't include "agent cost in dollars" — UiPath tracks consumption in
AGU/PLTU units, not currency. I've added an AGU Consumption widget instead,
which shows the same underlying usage in platform units.
```

Never generate a widget for a non-existent endpoint. An empty/broken chart is worse than
a clear explanation.

## Approval Gate Rules
- ANY positive response → proceed to scaffold
  (yes, looks good, do it, go ahead, 👍, confirmed, ship it, build it)
- Widget edit request → update that widget line only, re-show ONLY the changed line, re-ask
- "Remove X" → remove from list, re-show updated plan, re-ask
- "Add X" → derive the right data source internally (never mention it), append with plain description, re-ask
- Rejection without edit → ask: "What would you like to change?"
- Never re-show the full plan after partial edits — show diffs only
- **Client ID question must be answered before Phase 6.** If the user approves the widget list but does not answer the client ID question, re-ask specifically: "One more thing — do you have an existing non-confidential external app Client ID, or should I create one?" Do not proceed to Phase 6 until both the plan and the client ID question are answered.

## Standard Time Constants

See canonical definitions in `sdk-capabilities.md` (Standard Time Constants section).

`build-dashboard.mjs` injects these automatically into every generated widget file.
Use `SEVEN_DAYS_AGO`, `NOW`, etc. directly in `dataHook` expressions without re-declaring them.

**Both `startTime` AND `endTime` are required for all Insights calls.** Omitting `endTime` causes 500 errors.

In the plan, map time frames to natural language: `ONE_DAY_AGO` → "today/24h",
`SEVEN_DAYS_AGO` → "last 7 days", `THIRTY_DAYS_AGO` → "last 30 days".

## Four-Axis Metric Decomposition (internal only — never shown to user)
For each metric, derive internally and use to build the description:
- **Shape**: `line | bar | area | donut | kpi | table`
- **Time frame**: `realtime | hourly | daily | weekly | monthly`
- **Aggregation**: `count | sum | avg | p50 | p95 | p99`
- **Service**: `SDK` or `Insights` (resolve via sdk-capabilities.md)

## Anti-patterns
- Do NOT show [Insights] or [SDK] labels in the plan
- Do NOT mention API method names (getAgents, getSummaryV2, etc.)
- Do NOT mention chart types (KPI card, area chart) in the plan — describe the insight instead
- Do NOT start scaffolding before explicit approval
- Do NOT infer approval from silence or a question ("which folder?")
- Do NOT re-derive the entire plan if only one widget changes
- Do NOT show code, file paths, or technical terms in the plan
