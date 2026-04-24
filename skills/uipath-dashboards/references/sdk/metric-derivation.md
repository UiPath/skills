# Metric derivation — reasoning framework

**This skill is a dashboard expert, not a phrase-book.** When a user asks for a metric — whether it's in `intent-map.md` or not — the generator's job is to **reason** about how to compute it from SDK primitives, not look it up.

`intent-map.md` is a catalog of worked examples, not an exhaustive list. When a requested metric isn't in the catalog, the agent derives it from this framework.

## The four-axis decomposition

Every metric resolves on four axes. Classify the intent on all four, then the SDK call + aggregation falls out mechanically.

### Axis 1 — Shape

What does the metric *look like* once computed?

| Shape | Examples | Determines |
|---|---|---|
| **scalar** | "active agents", "total cost MTD", "avg response time" | KPI widget with single-number body |
| **scalar-with-delta** | "invocations today (+8% vs yesterday)" | KPI with delta badge; requires a second SDK query for the comparison period |
| **time-series** | "invocations per hour last 24h", "compliance rate per week" | Bar/line/area chart; requires bucketing + zero-fill |
| **categorical** | "jobs by state", "tasks by priority" | Bar chart (≤6 categories) or horizontal bar (>6) |
| **ranked** | "top agents by invocation" | Ranked-table (multi-column) or horizontal bar (single metric) |
| **parts-of-whole** | "cost by model", "tasks by status" | Donut (≤5 slices) or progress-bar-list (>5) |
| **distribution** | "job duration distribution" | Histogram or box plot |
| **flow / funnel** | "case stages", "Maestro process path" | Sankey, funnel, or BPMN overlay |

### Axis 2 — Time framing

Does the metric care about time, and if so how?

| Framing | Implication |
|---|---|
| **snapshot** | "current state" — no time filter, just a live read. Example: "how many queues are defined". |
| **point-in-time count** | "jobs today", "errors this week" — filter on `CreationTime gt <iso>`. Single count. |
| **bucketed series** | "jobs per hour over 24h" — fetch window, client-side group into N buckets, zero-fill. |
| **trend vs prior period** | "invocations today vs yesterday" — TWO queries, current and prior, compute delta. |
| **rolling window** | "error rate over last 7 rolling days" — query enough history to compute a sliding window. |

### Axis 3 — Aggregation

How do you collapse many rows into the metric?

| Aggregation | Formula / SDK hint |
|---|---|
| **count** | `resp.totalCount` from first page if narrow filter; else sum `.items.length` across paginated pages |
| **distinct count** | paginate → `new Set(rows.map(r => r.<field>)).size` |
| **sum** | paginate → `rows.reduce((s, r) => s + r.<field>, 0)` |
| **mean** | paginate → sum / count; drop rows with null/zero for the measured field |
| **median / percentile (p50, p95, p99)** | paginate → sort → index. For p95 over N rows: `sorted[Math.floor(N * 0.95)]`. |
| **ratio** | two counts → numerator / denominator. Example: error rate = faulted / total. |
| **rate-of-change** | `(current - prior) / prior` — requires two windowed queries |
| **top-N** | paginate → group-by → sort desc → slice first N |
| **group-by + aggregate** | paginate → `Map<groupKey, accumulator>` → materialize as rows |

### Axis 4 — Service

Which SDK class/service owns the primary entity for this metric?

See [service-semantics.md](service-semantics.md) for the full model. Key question: "what's the canonical **row** behind this metric?"

- "active agents" → row is a distinct `processName` within `Jobs` (no `Agents` service; agent activity = job filter `ProcessType eq 'Agent'`)
- "error rate" → row is a `Job` (needs faulted count + total count)
- "open cases" → row is a `CaseInstance`
- "conversation volume" → row is an `Exchange`

## Worked derivation — "P95 response time over last 7 days"

Suppose this isn't in the intent-map. Derivation:

1. **Shape** → scalar (single number) potentially with delta vs previous 7d.
2. **Time framing** → point-in-time count over 7d window; second query for 7d-prior-window if delta requested.
3. **Aggregation** → percentile p95.
4. **Service** → Jobs (job duration = `endTime - startTime`).

Synthesized call:
```ts
const since = isoDaysAgo(7);
const jobs = await fetchAllJobs(jobsService(sdk), `CreationTime gt ${since}`);
const durations = jobs
  .filter((j) => j.startTime && j.endTime)
  .map((j) => new Date(j.endTime).getTime() - new Date(j.startTime).getTime())
  .sort((a, b) => a - b);
const p95 = durations[Math.floor(durations.length * 0.95)];
```

The agent didn't need an intent-map entry for "P95 response time" — it reasoned from axes + primitives.

## Worked derivation — "Compliance drift week-over-week"

1. **Shape** → time-series (rolling pass rate) + delta (this week vs last week).
2. **Framing** → bucketed series (daily) + rate-of-change across window.
3. **Aggregation** → per-day ratio (pass / total), then compare current 7d mean vs prior 7d mean.
4. **Service** → ProcessIncidents (if governance/compliance is exposed there) OR the governance CLI (v2+; for v1 this probably isn't in SDK — agent says so and suggests what IS queryable).

When the agent can't reach the data in v1's SDK-only scope, it says so and points at `intent-map.md § "Pattern: data the user wants isn't in the SDK"` — it doesn't fabricate.

## Primitives the agent composes

Think of these as Lego blocks. Any metric is a composition.

| Primitive | Signature | Used for |
|---|---|---|
| `fetchAllWithFilter(service, filter)` | paginates through all pages with cursor | any count, any group-by, any window |
| `zeroFill(rows, keyField, buckets, defaults)` | fills missing buckets with defaults | every time-series |
| `isoHoursAgo(n)` / `isoDaysAgo(n)` | ISO timestamp N units ago | windowed filters |
| `hourBucket(date)` / `dayBucket(date)` | bucket key for a timestamp | time-series aggregation |
| `groupBy(rows, keyFn)` | `Map<string, T[]>` | top-N, breakdown-by, per-group metrics |
| `dedupById(rows)` | set-based dedup | paginated overlap protection (see invariants.md §5) |
| `percentile(sortedNumbers, p)` | indexed lookup | p50/p95/p99 |
| `delta(current, prior)` | `{value, direction, formatted}` | trend badges |

All of these ship in `src/lib/utils.ts` and `src/lib/queries/_shared.ts` in the scaffold. The generator composes them; it does not reinvent.

## When to halt vs synthesize

**Synthesize when:**
- The four axes classify cleanly
- The service owning the data is in SDK coverage
- The aggregation decomposes into the primitives above
- The invariants in `invariants.md` still apply

**Halt and ask when:**
- The metric implies a service NOT in SDK coverage (e.g., "queue-item throughput" — queue items aren't in the SDK)
- The metric is ambiguous (e.g., "agent health" — what are the dimensions?)
- The time framing requires historical data older than the SDK can fetch efficiently
- The calculation is genuinely novel and might warrant a different service

Halting is honest. Fabricating is worse than halting. The user would rather hear "I can't derive this from Jobs/Processes/Tasks — here's what I CAN query that's adjacent" than get a dashboard that silently shows wrong numbers.

## Anti-patterns

- **Treating `intent-map.md` as exhaustive.** It's illustrative. Always consider whether a requested metric matches the axes framework before searching the table.
- **Falling back to client-side `jobs.getAll()` without a filter.** Paginating the entire tenant's job history is wasteful; the axes framework always produces a filter first.
- **Epoch-fallback for missing dates.** Rule 4 of `invariants.md` — drop the row with `console.warn`, don't mis-bucket it into 1970.
- **Hardcoding column lists in detail views.** Columns are derived from `service-semantics.md` — "what's the semantic shape of this service's row?"
- **Reinventing aggregation.** Use the primitives; don't write a new `.reduce()` for every metric.
