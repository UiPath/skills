#!/usr/bin/env bash
# Seed for dashboard_upgrade_scaffold: a complete compiler-managed dashboard
# stamped with an OLD scaffold version (2.0.0) so the shipped kit registers as
# drift → UPGRADE_AVAILABLE. Kit extracted via stdin tar (drive-colon-proof).
set -euo pipefail

mkdir -p ops-dash/metrics ops-dash/src/metrics ops-dash/.dashboard
tar -xz -C ops-dash -f - < "$SKILLS_REPO_PATH/skills/uipath-coded-apps/assets/fixtures/governance-dashboard-starter-kit.tar.gz"

cat > ops-dash/intent.json << 'EOF'
{
  "schemaVersion": 2,
  "dashboardName": "Ops Dashboard",
  "timeRange": "7d",
  "projectDir": ".",
  "routingName": "ops-dash-b7x1",
  "orgName": "codereval", "tenantName": "DefaultTenant",
  "cloudUrl": "https://alpha.uipath.com", "apiUrl": "https://alpha.api.uipath.com",
  "clientId": "",
  "metrics": [ { "name": "job-failures", "tier": "T1", "title": "Faulted Jobs" } ]
}
EOF

cat > ops-dash/metrics/job-failures.ts << 'EOF'
import type { MetricFn } from '@/lib/metric-contract'

export const fetchData: MetricFn = async (sdk) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  return ((await new Jobs(sdk).getAll({ filter: "State eq 'Faulted'" }))?.items ?? []).map(x => ({ ...x }))
}
EOF
cp ops-dash/metrics/job-failures.ts ops-dash/src/metrics/job-failures.ts

cat > ops-dash/.dashboard/state.json << 'EOF'
{
  "schemaVersion": 2,
  "versions": { "skill": "2.0.0", "scaffold": "2.0.0", "intentSchema": 2, "sdk": "1.5.0" },
  "regime": "compiler-managed",
  "app": { "name": "Ops Dashboard", "routingName": "ops-dash-b7x1", "semver": "1.0.0" },
  "env": "alpha", "org": "codereval", "tenant": "DefaultTenant",
  "cloudUrl": "https://alpha.uipath.com", "timeRange": "7d",
  "widgets": {
    "JobFailures": { "hash": "0", "tier": "T1", "metric": "job-failures", "template": "data-table", "module": "metrics/job-failures.ts", "intentMetric": { "name": "job-failures", "tier": "T1", "title": "Faulted Jobs" } }
  },
  "deployment": { "systemName": null, "folderKey": null, "folderName": null, "appUrl": null, "deployVersion": null, "pinnedToGovernance": false, "lastDeployedAt": null },
  "buildStatus": "complete"
}
EOF
echo "seeded upgrade fixture (scaffold stamped 2.0.0)"
