#!/usr/bin/env bash
# Seed for dashboard_eject_takeover: a minimal compiler-managed dashboard
# (state.json only — EJECT rewrites state and touches nothing else).
set -euo pipefail

mkdir -p ops-dash/.dashboard
cat > ops-dash/.dashboard/state.json << 'EOF'
{
  "schemaVersion": 2,
  "regime": "compiler-managed",
  "app": { "name": "Ops Dashboard", "routingName": "ops-dash-b7x1", "semver": "1.0.0" },
  "env": "alpha", "org": "codereval", "tenant": "DefaultTenant",
  "cloudUrl": "https://alpha.uipath.com", "timeRange": "30d",
  "widgets": {
    "JobFailures": { "hash": "0", "tier": "T1", "metric": "job-failures", "template": "data-table", "module": "metrics/job-failures.ts", "intentMetric": { "name": "job-failures", "tier": "T1", "title": "Faulted Jobs" } }
  },
  "deployment": { "systemName": null, "folderKey": null, "folderName": null, "appUrl": null, "deployVersion": null, "pinnedToGovernance": false, "lastDeployedAt": null },
  "buildStatus": "complete"
}
EOF
echo "seeded eject fixture"
