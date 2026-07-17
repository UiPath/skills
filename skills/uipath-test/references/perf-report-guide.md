# Performance Report Generation Guide

Detailed instructions for turning a completed performance **scenario execution** into a
persona-organized report — as an in-chat text report, a downloadable **PDF**, or a
stakeholder-ready **HTML** page.

This guide is the authoring brain. The `uip tm perf-scenario …` commands only fetch data and
render your authored content; **all analysis, structure, and wording are your
responsibility** and come from the rules below.

## When to Use This Guide

- The user asks to "generate a performance report", "analyse this run", "give me a report",
  or "PDF / HTML report" for a performance scenario execution.
- The user asks about response times, HTTP/automation errors, throughput, CPU/RAM, or
  pass/fail for a scenario execution.

**Entry requirement: a scenario execution id.** Reports are generated for a specific,
completed execution — from the user directly, or from a scenario run earlier in the
conversation (see the resolution order in the Pipeline section). Without one, ask; don't hunt.

## Prerequisites

- Authenticated session (`uip login status --output json`).
- A Test Manager **project key**.
- A **completed** scenario execution (dry run or full run). Meaningful pass/fail appears on
  full executions; dry runs typically show per-group status `none`.
- CLI surface probed (see [/uipath:uipath-test § Critical Rules](../SKILL.md#critical-rules)). Always pass `--output json`; translate via the [Pre-rename fallbacks](../SKILL.md#pre-rename-fallbacks) table on a pre-rename CLI.

## Command surface (target `uip tm perf-scenario` commands)

All commands follow the repo's `<subject> <verb>` convention (like `report get`,
`requirements list`). The data maps one-to-one onto the former AgentHub tools. Two ids recur:
`--execution-id` = the **scenario execution** id; `--load-group-id` = a **load group's**
execution id (from `load-groups list`). Use `uip tm perf-scenario <cmd> --help --output json`
to confirm exact flags.

| Command | Fetches | Former tool |
|---|---|---|
| `uip tm perf-scenario executions list --project-key <key> [--scenario-id <uuid>] [--execution-type dryRun\|performanceTesting]` | scenario executions (filter dry vs full via `executionType`) | Get_Scenario_Executions |
| `uip tm perf-scenario load-groups list --project-key <key> --execution-id <uuid>` | per-load-group config + status; each group's id is the bridge id | Get_Load_Group_Logs |
| `uip tm perf-scenario http-errors list --execution-id <uuid> --load-group-id <uuid> --start-time-ms 0 --end-time-ms <durMs>` | HTTP errors grouped by request (URL, status, count) | Get_Http_Errors |
| `uip tm perf-scenario automation-errors list --execution-id <uuid> --load-group-id <uuid> --start-time-ms 0 --end-time-ms <durMs>` | automation-step failures (step, message, count) | Get_Automation_Errors |
| `uip tm perf-scenario results get --execution-id <uuid> --completed` | full data bundle: time-series, CPU/RAM, application logs | Get_Scenario_Execution_Data |
| `uip tm perf-scenario transaction-metrics list --load-group-id <uuid> --start-time-ms 0 --end-time-ms <durMs>` | per-transaction avg/P50/P90/P95/P99/max, throughput, error rate (**API SUTs only**) | Get_Transaction_Metrics |
| `uip tm perf-scenario report generate --execution-id <uuid> --format pdf\|html --report-file <path> --project-key <key>` | renders your authored markdown (pdf) / HTML (html); returns `{ViewUrl}` — the in-app report page when `--project-key` is passed | Generate_Report (unified) |
| `uip tm perf-scenario report compare --scenario-id <uuid> --execution-ids <uuid...> --report-file <path> --project-key <key>` | renders an authored comparison HTML across runs of one scenario (execution ids **oldest → newest**); returns `{ViewUrl}` | Generate_Comparison_Report_HTML |

> Always confirm real flags with `uip tm perf-scenario <cmd> --help --output json` before
> calling; if a listed name is missing, probe the group's `--help` for its current name.

---

## Pipeline — gather in this order

> **⛔ This workflow REQUIRES a scenario execution id.** Resolve it in this order:
> 1. The user provided one → use it, SKIP discovery (steps 1–2), go straight to step 3.
> 2. A scenario was executed **earlier in this conversation** → reuse that `ExecutionId`.
> 3. Neither → **STOP and ask the user for the execution id.** Offer two ways to get one:
>    copy it from the Test Manager UI, or — if they give you a `--project-key` — you can run
>    `executions list` to show them candidates **and let the user pick**. If no run exists
>    yet, point them to the scenario workflow
>    ([perf-scenario-guide.md](perf-scenario-guide.md)) to create and execute one first.
>    **Never select an execution yourself, never scan projects or tenants to find one.**
>
> **Two different load-group ids exist — don't mix them.** The load-group **execution** id
> (`--load-group-id` for metrics/errors commands) is the dashed `ExecutionId` inside
> `results get`'s `ExecutionsData` entries (also the `Id` field on `load-groups list` rows).
> The `LoadGroupId` field on those same rows is the **config** id — it works for
> `update-loadgroup` but returns nothing from metrics/errors endpoints.
>
> `load-groups list` is only for per-group config (thresholds, SUT type) that `results get`
> lacks — it's a Test Manager endpoint needing TM access on the active tenant.
> **If a Test Manager endpoint returns 403, do NOT hunt across projects or tenants** — mark
> the affected config fields "No data reported" and continue from the data bundle alone.
> **If you need a project key and the user didn't give one, ASK the user.**

> **⚠️ Load-group id format.** Always use the **dashed, lowercase GUID** from the
> `ExecutionId` field *inside* the `AggregatedData` entries (e.g.
> `a1b2c3d4-0000-0000-0000-000000000001`) as the `--load-group-id` and in chart markers.
> Do NOT use the `ExecutionsData` dictionary **key** — the CLI renders it un-dashed and
> re-cased (`B07b3d4a31000000…`), and the chart injector matches ids **dash-sensitively**,
> so markers built from the key produce "Chart unavailable — no data for this metric".

1. **(Discovery — only if the execution id is unknown.)** `executions list --project-key <key>`
   → find the scenario `--execution-id` and `duration` (ms). For a full report, confirm the
   scenario has a completed dry run (a full run with no prior dry run fails with "Dry run
   report not found").
2. **(Optional per-group config.)** `load-groups list --project-key <key> --execution-id <uuid>`
   → test case, SUT type, virtual users, ramp timing, thresholds, status.
3. **Full data bundle (start here when you have the id).** `results get --execution-id <uuid>
   --completed true` → time-series (load profile, response times, error rates, step durations),
   executing-robot CPU/RAM, application logs. One `ExecutionsData` entry per load group; take
   each group's id from its entries' **`ExecutionId` field (dashed)** — see the format warning
   above — and use it as `--load-group-id` below.
4. **Per load group errors.** `http-errors list` and `automation-errors list` (pass the
   scenario `--execution-id`, the group's `--load-group-id`, `--start-time-ms 0`,
   `--end-time-ms` = duration in ms).
5. **Per-transaction metrics.** `transaction-metrics list` per load group (`--load-group-id`
   = the load group id, `--start-time-ms 0`, `--end-time-ms` = duration in ms). **Only for
   API-type SUTs** — Browser/Desktop groups produce none.
6. **Render** (only if a file is requested) — `report generate --format pdf|html`.

### Working with the bundle (do NOT dump it)

The `results get` bundle is large (hundreds of KB — a datapoint every ~2 s per group). Never
print it whole; write it to a temp file once and extract with targeted `jq` passes:

1. **Structure probe:** top-level keys, `ExecutionsData` keys, entry count per group.
2. **Per group, one pass each:** the dashed `ExecutionId` (first `AggregatedData` entry);
   peaks (`max_by` on VUserCount / Cpu / Ram / ResponseTimeMs, keeping `MilliSeconds` so every
   spike has a timestamp + VU count); last-datapoint cumulative counts (workflows, errors);
   RAM first/last + monotonicity (leak check).
3. **Logs:** error/warning lines only (`select(.Level != "Information")`), plus the first and
   last few lines for run boundaries and threshold-violation messages.

Percentiles still come ONLY from `transaction-metrics list` — never from the bundle's
time-series. Aim for ≤ 6 extraction commands total; do not re-scan the file per metric.

---

## Data rules (most important — read before writing a single number)

- **Never fabricate.** Use only real values from the tool results — numbers, counts, URLs,
  thresholds, timings, status codes. Never invent endpoint URLs. Quote exact values verbatim.
- **Mark anything unavailable.** If a metric is missing write "No data reported". If
  transaction metrics 404 or the data bundle is empty, say so plainly — don't imply the
  tools are broken.
- **Percentiles have a single source.** Take avg / P50 / P90 / P95 / P99 / max from
  `transaction-metrics` (the per-transaction aggregate). **Do NOT recompute or average
  percentiles from the time-series datapoints** — averaging percentiles is statistically
  invalid.
- **Spikes / max.** Before describing a latency spike, find the actual maximum datapoint and
  report **both its timestamp and the virtual-user count at that moment**. Do not assume a
  spike is ramp-down/teardown — only call it teardown if it occurred during ramp-down; at
  full VU load it is load-related.
- **Extrapolation.** Separate MEASURED results from any capacity ESTIMATE. Never state a firm
  virtual-user ceiling as if measured; label projections as rough estimates needing an actual
  test, and note the **robot** (not the backend SUT) was the metered component.
- **SUT type mapping.** Never show the raw `systemUnderTestType` enum. Map:
  `windowsApplication` → **Desktop**; `chrome`/`edge`/`internetExplorer`/`safari`/`opera`/
  `firefox`/`netscape` → **Browser**; `api` → **API**; undefined/default → **Unknown**.
- **Rounding.** Response times 0–2 dp; percentages 1–2 dp; counts whole; durations as raw ms
  **and** human-readable (`985152 ms → 985,152 ms (approx 16 min 25 sec)`).
- **Empty error lists.** If the HTTP-errors source is empty, don't invent per-URL errors. If
  per-transaction aggregates show `httpErrorCount > 0`, report those totals and add one line:
  "URL-level error breakdown unavailable; counts sourced from per-transaction aggregates."
- **Generic transaction names.** If no transaction has a real URL (only `req1`/`req2` — common
  for Browser/Desktop), do NOT render a Host Reference / full-URL table; add one line:
  "Endpoint URLs not reported by the tools for this run (generic transaction names only)."
  Never repeat "not reported" row by row.
- **Every finding connects data → impact → action.** Don't report a number without saying
  what it means and what to do about it.
- **Impact legend** (use to reason from a symptom to a cause):
  - `404` → broken link / missing resource / routing
  - `500` → backend / server-side error
  - `502` / `504` → gateway / proxy / timeout / overload
  - element-not-found → selector flakiness
  - timeouts → slow backend / missing synchronization
  - `P99 ≫ P50` → tail latency
  - CPU or RAM `> ~90%` → infrastructure saturation
  - a slow HTTP `200` → successful request that still breached the response-time SLO

---

## Three output modes

| User asks for | What you do | Structure |
|---|---|---|
| "analyse this run" / "show me a report" (no file) | Author the report **in chat** — no `report generate` call. | 5-part linear (below) |
| "PDF" / "export as PDF" / "download as PDF" | Author markdown, call `report generate --format pdf`, return the download link. | Persona-organized (below) |
| "HTML report" / "web page" / ".html" | Author a self-contained HTML doc, call `report generate --format html`, return **both** view + download links. | Persona-organized (below) |

For PDF/HTML: the service returns a **single `ViewUrl`** — when `--project-key` was passed it
opens the **in-app report page** (renders charts inline, carries a Download button). Present
exactly ONE clickable link labelled `<execution name> report`; do NOT paste the report body
into chat and do NOT fabricate a separate download link. **Always pass `--project-key`** so
users land on the in-app page.

---

## In-chat report structure (5-part linear)

For a plain "analyse this run" with no file, answer directly in chat in EXACTLY these 5 parts:

1. **Title** — `Performance Test Report: <system / scenario name>`.
2. **Summary** — a `Test Context Overview` bullet list: test case, load (VU range + shape),
   duration, system under test, configured thresholds, plus any test type / labels / objectives.
3. **Key Metrics Across Views** — `Average`, `P50`, and `P95` subsections; each with response
   time (verdict vs threshold), HTTP error rate, automation error %, throughput.
4. **Analysis** — a numbered **Main Problems** list; each entry = heading + root-cause reasoning
   + exact `Count: <n>` with full URLs/identifiers + impact (use the Impact legend above). Then
   a **Recommendations** table with columns `Area | Action` (typical areas: Frontend, Test
   Scripts, Backend/APIs, Logs & Tracing, Infrastructure).
5. **Final Assessment** — did it survive the load and at what cost; production-readiness verdict;
   top-priority fixes in order; whether a re-test is recommended.

End with **2–3 suggested follow-up questions**.

---

## Report structure — PERSONA-ORGANIZED (PDF & HTML)

Each piece of analysis lives **once**, under the persona that needs it. Do NOT also emit a
separate linear "full report". Generate the personas in this order.

**Header (above the first persona):**
- Title as a level-1 heading: `# Performance Test Report: <scenario name>`
- `Overall Result: Passed / Failed / Partially Failed`
- A **Run Details** table (Field | Value): Project, Started, Finished, Duration, Load Groups,
  Peak Virtual Users, Execution Type.

**## Program Manager** (executive, non-technical)
- Release-readiness verdict per load group (Production-ready / Not ready / Needs
  investigation) + an overall verdict, each citing the one or two numbers that drove it.
- `### SLO Scorecard` table: Group | SLO | Limit | Observed | Result.
- `### What Went Wrong` — plain language, no jargon.
- `### Recommended Next Steps` — numbered list (who does what).
- No percentile tables or code-level detail here.

**## Developer** (code-level)
- `### HTTP Failures` table (4xx/5xx only): Endpoint/Transaction | Status | Count | Error Rate
  | Total Requests + an Interpretation line.
- `### Latency` table: Transaction | Avg | P50 | P95 | P99 | Max + Interpretation on tail
  latency (the P99-vs-Max gap).
- `### Slow Successful Responses` (slow HTTP 200s): Transaction | Max | P99 | SLO | Impact.
- `### Action Items` — prioritized P0/P1/P2, each citing a specific observed number.
- `### What Is Working` — short note.

**## InfraOps** (infrastructure)
- `### Resource Usage` — peak CPU (with timing), steady-state CPU, RAM trend, per group.
- CPU/RAM analysis citing evidence (value + timestamp); state whether infrastructure is the
  primary failure cause. **Flag monotonic RAM growth as a possible memory-leak signal.**
- `### Infrastructure Actions` — prioritized P0/P1/P2, limited to what the data supports.
- `### Host Reference` table: endpoint path → full URL. **Full URLs appear ONLY here.**

**## QA / Tester** (what to retest)
- `### Retest Scope` — which groups need a full retest, which don't, soak test yes/no.
- `### Retest Checklist` — pre-conditions & acceptance criteria, each citing the previous
  observed value vs the SLO (`[ ] <action> — <acceptance criterion>`).
- `### What to Monitor` during the retest.
- `### Soak Test` parameters table when a memory/resource trend warrants it.
- `### What Does NOT Need Retesting` — with reasons.
- `### Test Execution Reference` — scenario/group execution IDs, run window, error-onset
  timestamp if known.

Always keep all four personas even with a single load group; if a persona has no data, write
"No data reported" inside it.

---

## Markdown constraints (PDF mode — safe for a basic renderer)

Use ONLY: `#`/`##`/`###` headings; GitHub-style pipe tables with a `| --- |` separator row;
bullet lists; numbered lists; plain paragraphs. A heading line MUST start with `#`, `##`, or
`###` followed by a space — never a heading as plain text. Do NOT use HTML, emojis, mermaid,
very wide tables, deep nesting, or long unbroken strings (full URLs) inside main tables. Bold
`**` and inline `` `code` `` are stripped by the renderer — harmless but won't style. Keep
tables 4–6 columns; after every major metric table add a one/two-sentence `Interpretation:`
paragraph. Use plain-text status labels only ("Verdict: Passed"), never color/emoji/icons.

## HTML mode — persona TABS + chart placeholders

- One self-contained document: `<!DOCTYPE html>`, `<head>` with **only an inline `<style>`**,
  `<body>`. It must render offline and inside a CSP-restricted viewer: **no `<script>` / JS of
  any kind**, no external CSS/fonts/images, no remote src/href, no iframes.
- **Pinned visual style (use these exact tokens every run — reports must look identical
  across runs):** light theme; system font stack. `--bg:#f5f6f8; --card:#ffffff;
  --ink:#1c2331; --muted:#5b6472; --line:#e3e6ec; --pass:#1f9d55; --fail:#d64545;
  --warn:#c47f17; --accent:#2f6feb; --accentbg:#eaf1ff`. Status colors only for
  pass/fail/warn indicators; `--accent` for tabs and links. Do not invent a new palette or
  switch to a dark theme.
- Render a shared header (title, overall-result badge, key-stats row) **outside** the tabs.
- Then FOUR **CSS-only** switchable tabs (Program Manager, Developer, InfraOps, QA/Tester) —
  four radio `<input>`s first, then a `<nav>` of `<label>`s, then four `<section class="panel">`
  panels, all direct children of one container so `:checked ~ panel` selectors resolve. Hide
  radios; `.panel{display:none}`; reveal the checked panel; add
  `@media print{.panel{display:block!important}}` so a printed copy shows every persona.
- The personas MUST be switchable tabs — not side-by-side cards, not a linear report.
- **Charts = placeholders only.** Never draw/paste/recompute SVG. Where a chart belongs
  (Developer + InfraOps panels), emit exactly:
  `<figure style="margin:0"><figcaption>TITLE</figcaption><!--chart:GROUP_EXECUTION_ID:CHART_KEY--></figure>`
  where `GROUP_EXECUTION_ID` is the load group's **dashed, lowercase GUID** — the `ExecutionId`
  field from inside `AggregatedData` (e.g. `a1b2c3d4-0000-0000-0000-000000000001`), NEVER the
  un-dashed `ExecutionsData` dictionary key (dash mismatch → "Chart unavailable") — and
  `CHART_KEY` ∈ `responseTime`, `virtualUsers`, `httpErrorRate`, `automationErrorRate`,
  `throughput`, `systemUsage`. The service injects the real SVG on save and replaces no-data
  placeholders with a note. Group a load group's charts in a responsive 2-up grid. If the user
  asked for no charts, emit no markers.

---

## Comparison reports (several runs of ONE scenario)

Only when the user explicitly asks to COMPARE runs ("compare the last N runs", "what changed
between these executions"). Requires **2+ completed runs of a scenario that still exists**
(executions whose scenario was deleted carry no scenario id and cannot be compared).

### Workflow

1. Identify the runs (`executions list --project-key <key> --scenario-id <uuid>`; for
   "last N" pick the N most recent COMPLETED); order **oldest → newest**.
2. Gather EVERY run's data before authoring (slimming rules apply; per-run percentiles from
   `transaction-metrics list`).
3. Author ONE self-contained comparison HTML per the structure below.
4. Render: `report compare --scenario-id <uuid> --execution-ids <old>..<new> --report-file
   <html> --project-key <key>` → present the single returned `ViewUrl` as
   `<scenario name> comparison report`.

### Comparison data rules

Per-run stored values only — never recompute percentiles. A metric a run doesn't report →
"No data reported" in that cell; a transaction absent in a run → "Not present in this run".
Compare like-for-like (same transaction/load group across runs). Every trend states
**direction AND magnitude first→last** ("P95 +18% (regressed)", "error rate −2.1pp
(improved)", "stable"). Label capacity projections explicitly as estimates.

### Comparison structure (persona-organized — NOT a linear report)

**Shared header (above the tabs):** `# Performance Comparison: <scenario name>`; a
**Runs Compared** table (Run | Execution Id | Date | Duration | Overall Result, oldest→newest);
an overall **trend badge** (Improved / Regressed / Mixed / Stable) citing the driving metrics;
a **COMPARABILITY CHECK** — if runs differ in SLO thresholds, peak VUs, or load shape, list
each differing setting and state the verdict is directional, with a Confidence level (High if
configs match, Medium/Low otherwise); an **EXECUTIVE SUMMARY** (verdict; release-ready Yes/No;
one-line root cause; confidence; ONE plain-English business-risk sentence); and a
**What changed between runs** line/table (peak VUs, ramp/peak/ramp-down, both SLOs).

**FIVE CSS-only tabs** (same hidden-radio pattern as single-run reports; radios first, then
nav labels, then panels, all in one container; `@media print` shows all panels; keep all five
tabs even with sparse data):

- **Overview** — Run Overview table (one COLUMN per run: Started, Duration, Peak VUs, Groups
  Passed/Failed, Overall Result); Key Findings (3–5 bullets).
- **Tester** — SLO pass/fail matrix (Check | per-run threshold | per-run result | Pass/Fail);
  the comparability caveat; a recommended aligned-threshold retest (one fixed SLO set) plus a
  longer-ramp suggestion when a ramp-up spike appears.
- **Developer** — per-transaction Latency table (Transaction | per-run P95 & Max | Trend
  first→last with direction + magnitude) + tail-latency Interpretation; Reliability table
  (error rate/count per run + Trend); Tail-latency detail (Max per run + delta). ONLY IF the
  http-errors tool returned rows: status/endpoint breakdown + top failing endpoints; otherwise
  one line: "URL/status-level breakdown unavailable; using per-transaction aggregates".
- **Operations** — Infra table (peak CPU, steady-state CPU, RAM range/trend per run + Trend);
  Throughput (peak req/s per run + Trend); efficiency row (peak CPU ÷ peak req/s); a
  capacity-headroom ESTIMATE (labelled estimate); recommended infra actions.
- **Program Manager** — cards (Verdict, Release-ready, Open P0s, Confidence); a Regressions
  table in P0/P1/P2 priority (Metric | first→last | impact); an Improvements table;
  Recommended next steps BY TEAM.

### Comparison charts

Emit **bare markers only**: `<!--compare-chart:CHART_KEY-->` (chart key only — NO execution
id). The service overlays one line per compared run (legend Run 1..N oldest→newest). Missing
metric for ANY run → the service removes the marker **silently**: never caption a marker,
never assume a chart appears. Group markers in a responsive grid. Keys and placement:
`responseTime, throughput, httpErrorRate, automationErrorRate, virtualUsers` → **Developer**
panel; `cpu, ram` → **Operations** panel. Emit each key at most once.

### Comparison quality checklist

- [ ] 2+ runs, oldest→newest, with execution ids.
- [ ] Comparability check shown, confidence set.
- [ ] Executive summary includes the business-risk line.
- [ ] Five switchable persona tabs — not a linear report.
- [ ] Every cell = real value / "No data reported" / "Not present in this run".
- [ ] Every trend has direction + magnitude.
- [ ] Regressions and improvements separated, each citing numbers.
- [ ] Status/endpoint detail only when the errors tool returned rows.
- [ ] Capacity figures labelled estimates; no fabricated numbers/URLs.

## Analyse More

When the user asks for deeper detail after a report, loop:

1. **Explore** — `uip tm perf-scenario <cmd> --help --output json` to confirm the subcommand + flags.
2. **Execute** — run it with IDs from the previous response, always `--output json`.
3. **Validate** — if the result is empty or errors, diagnose before retrying (max 3 attempts).
4. **Repeat** — if the user wants more depth, identify the next command and repeat.

Stop when the user is satisfied, there is no more data, or 3 retries have failed.

## Output filename

Default `perf-report-<PERSONA-OR-all>-<YYYY-MM-DD>.<md|html>`. Ask where to save (default:
current directory) and confirm the name before writing.

## Quality checklist (verify before finalizing)

- [ ] Personas generated in order; each analysis lives once, under its persona.
- [ ] Every SLO breach shows observed value vs limit.
- [ ] Tail latency (P50 vs P99/Max) is explained.
- [ ] Monotonic RAM growth is flagged.
- [ ] HTTP 5xx separated from slow 200s.
- [ ] Retest checklist items have acceptance criteria.
- [ ] Full URLs appear only in the InfraOps Host Reference.
- [ ] Percentiles taken from transaction-metrics, not recomputed from time-series.
- [ ] No fabricated numbers or invented endpoint URLs; unavailable sections marked.
- [ ] (HTML) Personas are switchable tabs, not cards or a linear page.

## Anti-patterns

- **Do NOT** generate a report without gathering the data first — every number must trace to a
  tool result.
- **Do NOT** recompute percentiles from time-series datapoints.
- **Do NOT** invent endpoint URLs or per-URL error breakdowns.
- **Do NOT** show raw `systemUnderTestType` enums — map to Desktop / Browser / API / Unknown.
- **Do NOT** paste PDF/HTML report bodies into chat — return the link(s).
