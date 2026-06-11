# Incremental Editor

Handles ADD / REMOVE / CHANGE / REBUILD requests on existing dashboards.

## Trigger

Detects `.dashboard/state.json` at session start or after `BUILD_RESULT`. State schema: [state-file.md](state-file.md).

## edit-intent.json schema

Write to `<PROJECT_DIR>/edit-intent.json`. **Multiple changes = ONE `ops` batch — never run the script once per change.** The whole batch is validated up front (nothing is written if any op would fail), applied in order, and Dashboard.tsx/index.ts + tsc run once at the end.

```json
{
  "projectDir": "/abs/path",
  "ops": [
    { "op": "CHANGE", "target": "MemoryCallsTrend", "delta": { "displayAs": "bar-chart", "fnBody": "..." } },
    { "op": "REMOVE", "target": "AgentConsumption" },
    { "op": "ADD", "metric": { "name": "agent-health", "tier": "T1", "title": "Agent Health", "fnBody": "..." } }
  ]
}
```

Op shapes:
- **ADD** — `metric` is a full intent.json metric (fnBody required)
- **REMOVE** — `target` is the widget component name from state.json
- **CHANGE** — `delta` merges over the widget's persisted `intentMetric`
- **REBUILD** — no fields; regenerates every widget from persisted `intentMetric` (e.g. after template updates)

A single-op shorthand (`{ "op": "ADD", "projectDir": "...", "metric": ... }`) is also accepted.

## Run command

```bash
node "${SKILL_BASE_DIR}/assets/scripts/build-dashboard.mjs" "${EDIT_INTENT_PATH}"
```

## CHANGE semantics

Each widget's full intent metric (`intentMetric` — fnBody, title, display hints) is persisted in state.json at build time. CHANGE merges your `delta` over it, so a delta only needs the fields that change.

1. **Changing the time window requires a new `fnBody`.** The fnBody references time constants by name (e.g. `THIRTY_DAYS_AGO`) — a `timeRange` delta alone updates the subtitle but not the query window. Always pair `"timeRange"` with an updated `"fnBody"` using the matching constant (`SEVEN_DAYS_AGO` for 7d, etc.).
2. Changing `displayAs` between chart ↔ table/kpi is supported — the build regenerates or removes the detail view accordingly.
3. **Legacy dashboards** (built before intent persistence) have no stored `intentMetric` — the build fails with a clear message; include the full metric (fnBody, title) in `delta`, or re-run a fresh build.

## Events to watch

- `HAND_EDIT_DETECTED:{"widget":"X"}` — file was hand-edited; the whole batch is rejected before any write. Ask the user (see [customization.md](customization.md)).
- `TSC_PASS` — edit validated clean
- `TSC_FAIL:{"errors":"..."}` — surface to user
- `INCREMENTAL_READY:{"count":N,"ops":[{"op":"ADD","widget":"X"},…]}` — done; hot-reload fires automatically

## Rules

0. **Customized project?** If the user hand-edited files (or asks for look-and-feel changes), read [customization.md](customization.md) BEFORE running any edit-intent — the build regenerates `Dashboard.tsx` + `widgets/index.ts` on every op and would wipe their changes.
1. Only regenerate affected widget files — never the full scaffold.
1b. **Batch every multi-widget request into one `ops` array** ("convert everything to charts" = one run with N CHANGE ops, not N runs). One layout regen, one tsc.
2. Routing name never changes on edit.
3. After REMOVE or CHANGE: always regenerate Dashboard.tsx and widgets/index.ts (the build does this automatically).
4. Chart widgets get their detail view regenerated on ADD/CHANGE/REBUILD automatically — never hand-create views.
5. Do not touch .env.local unless user explicitly requests a config change.
