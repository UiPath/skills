# Incremental Editor

Handles ADD / REMOVE / CHANGE / REBUILD requests on existing dashboards.

## Trigger

Detects `.dashboard/state.json` at session start or after `BUILD_RESULT`. State schema: [state-file.md](state-file.md).

## edit-intent.json schema

Write to `<PROJECT_DIR>/edit-intent.json`:

```json
// ADD — full metric, same shape as an intent.json metric (fnBody required)
{ "op": "ADD", "projectDir": "/abs/path", "metric": { "name": "agent-health", "tier": "T1", "title": "Agent Health", "fnBody": "..." } }

// REMOVE — target is the widget component name from state.json
{ "op": "REMOVE", "projectDir": "/abs/path", "target": "AgentConsumption" }

// CHANGE — delta merges over the widget's persisted intentMetric
{ "op": "CHANGE", "projectDir": "/abs/path", "target": "MemoryCallsTrend", "delta": { "timeRange": "7d", "fnBody": "..." } }

// REBUILD — regenerate every widget from persisted intentMetric (e.g. after template updates)
{ "op": "REBUILD", "projectDir": "/abs/path" }
```

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

- `HAND_EDIT_DETECTED:{"widget":"X"}` — file was hand-edited. Warn user before overwriting.
- `TSC_PASS` — edit validated clean
- `TSC_FAIL:{"errors":"..."}` — surface to user
- `INCREMENTAL_READY:{"op":"ADD","widget":"X"}` — done; hot-reload fires automatically

## Rules

0. **Customized project?** If the user hand-edited files (or asks for look-and-feel changes), read [customization.md](customization.md) BEFORE running any edit-intent — the build regenerates `Dashboard.tsx` + `widgets/index.ts` on every op and would wipe their changes.
1. Only regenerate affected widget files — never the full scaffold.
2. Routing name never changes on edit.
3. After REMOVE or CHANGE: always regenerate Dashboard.tsx and widgets/index.ts (the build does this automatically).
4. Chart widgets get their detail view regenerated on ADD/CHANGE/REBUILD automatically — never hand-create views.
5. Do not touch .env.local unless user explicitly requests a config change.
