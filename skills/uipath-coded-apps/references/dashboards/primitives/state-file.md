# State File — .dashboard/state.json

Per-project metadata. Read at every build start. Written by build script on success.

## Schema

```json
{
  "schemaVersion": 2,
  "versions": { "skill": "2.0.0", "scaffold": "1.0.0", "intentSchema": 2, "sdk": "1.4.1" },
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
    "MemoryCallsTrend": {
      "hash": "a3f7b2c1",
      "tier": "T1",
      "metric": "memory-calls-trend",
      "template": "area-chart",
      "module": "metrics/memory-calls-trend.ts",
      "intentMetric": { "name": "memory-calls-trend", "tier": "T1", "title": "Memory Calls" }
    },
    "AgentHealth": {
      "hash": "c9e1d4f2",
      "tier": "T1",
      "metric": "agent-health",
      "template": "ranked-table",
      "module": "metrics/agent-health.ts",
      "intentMetric": { "name": "agent-health", "tier": "T1", "title": "Agent Health" }
    }
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

1. `schemaVersion` is `2`. The `versions` block (`skill`/`scaffold`/`intentSchema`/`sdk`) records what the dashboard was built against; a `scaffold` mismatch with the shipped version drives the offer-on-detect upgrade.
2. `widgets` is a map of `{ hash, tier, metric, template, module, intentMetric }` — not a string array.
   - `intentMetric` is pure metadata (no `fnBody`) — title, display hints, tier, name. Used by CHANGE/REBUILD to regenerate without the original `intent.json`.
   - `module` is the relative path to the durable data-fetch code (e.g. `"metrics/agent-health.ts"`). The live source lives at `src/metrics/<name>.ts` in the project.
3. `routingName` never changes once set. Not even on upgrades.
4. `hash` used for hand-edit detection — compare to current file before CHANGE/REMOVE.
5. `deployment.systemName` set by deploy plugin on first deploy.
6. `buildStatus` is `"in-progress"` from early in the build (so deploy can find app metadata even after a failed build) and `"complete"` on success.
7. `timeRange` is the dashboard default window — incremental edits fall back to it when a CHANGE delta has no `timeRange`.
