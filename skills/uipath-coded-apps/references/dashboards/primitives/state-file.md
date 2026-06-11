# State File — .dashboard/state.json

Per-project metadata. Read at every build start. Written by build script on success.

## Schema

```json
{
  "schemaVersion": 1,
  "app": {
    "name": "Operations Health Dashboard",
    "routingName": "operations-health-x7k2",
    "semver": "1.0.0"
  },
  "env": "alpha",
  "org": "appsdev",
  "tenant": "appsdevDefault",
  "cloudUrl": "https://alpha.uipath.com",
  "timeRange": "30d",
  "widgets": {
    "MemoryCallsTrend": { "hash": "a3f7b2c1", "tier": "T1", "metric": "memory-calls-trend", "template": "area-chart", "intentMetric": { "name": "memory-calls-trend", "tier": "T1", "title": "Memory Calls", "fnBody": "..." } },
    "AgentHealth": { "hash": "c9e1d4f2", "tier": "T1", "metric": "agent-health", "template": "ranked-table", "intentMetric": { "name": "agent-health", "tier": "T1", "title": "Agent Health", "fnBody": "..." } }
  },
  "deployment": {
    "systemName": null,
    "folderKey": null,
    "folderName": null,
    "appUrl": null,
    "deployVersion": null,
    "pinnedToGovernance": false,
    "lastDeployedAt": null
  },
  "buildStatus": "complete"
}
```

## Key rules

1. Every state.json starts at `schemaVersion: 1`.
2. `widgets` is a map of `{ hash, tier, metric, template, intentMetric }` — not a string array. `intentMetric` is the widget's full intent entry (fnBody, title, hints), persisted so CHANGE/REBUILD can regenerate without the original intent.json.
3. `routingName` never changes once set. Not even on upgrades.
4. `hash` used for hand-edit detection — compare to current file before CHANGE/REMOVE.
5. `deployment.systemName` set by deploy plugin on first deploy.
6. `buildStatus` is `"in-progress"` from early in the build (so deploy can find app metadata even after a failed build) and `"complete"` on success.
7. `timeRange` is the dashboard default window — incremental edits fall back to it when a CHANGE delta has no `timeRange`.
