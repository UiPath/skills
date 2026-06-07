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
  "widgets": {
    "ErrorRateTrend": { "hash": "a3f7b2c1", "tier": "T1", "metric": "agent-errors", "template": "line-chart" },
    "InvocationVolume": { "hash": "c9e1d4f2", "tier": "T1", "metric": "invocation-volume", "template": "area-chart" },
    "HighFailureQueues": { "hash": "f2a8c6d3", "tier": "T2", "metric": "queue-failure-threshold", "template": "ranked-table" }
  },
  "deployment": {
    "systemName": null,
    "folderKey": null,
    "appUrl": null,
    "lastDeployedAt": null
  }
}
```

## Key rules

1. Every state.json starts at `schemaVersion: 1`.
2. `widgets` is a map of `{ hash, tier, metric }` — not a string array.
3. `routingName` never changes once set. Not even on upgrades.
4. `hash` used for hand-edit detection — compare to current file before CHANGE/REMOVE.
5. `deployment.systemName` set by deploy plugin on first deploy.
