#!/usr/bin/env bash
# Seed for dashboard_semantic_wrong_field: a dashboard whose metric module
# COMPILES but filters on sourceType (the trigger origin) instead of the raw
# ProcessType field — the compiles-green-returns-wrong-rows trap Phase 3.5
# exists to catch. The module deliberately carries no hint comment; the agent
# must find the cause in the SDK docs.
set -euo pipefail

mkdir -p agent-runs-dash/metrics
tar -xz -C agent-runs-dash -f - < "$SKILLS_REPO_PATH/skills/uipath-coded-apps/assets/fixtures/governance-dashboard-starter-kit.tar.gz"

cat > agent-runs-dash/intent.json << 'EOF'
{
  "schemaVersion": 2,
  "dashboardName": "Agent Runs",
  "timeRange": "7d",
  "projectDir": ".",
  "routingName": "agent-runs-dash",
  "orgName": "codereval", "tenantName": "DefaultTenant",
  "cloudUrl": "https://alpha.uipath.com", "apiUrl": "https://alpha.api.uipath.com",
  "clientId": "",
  "metrics": [
    {
      "name": "agent-runs", "tier": "T3", "title": "Agent Runs",
      "displayAs": "data-table",
      "columnDefs": [
        { "key": "processName", "label": "Agent" },
        { "key": "state", "label": "State" },
        { "key": "creationTime", "label": "Started", "format": "timeAgo" }
      ]
    }
  ]
}
EOF

cat > agent-runs-dash/metrics/agent-runs.ts << 'EOF'
import type { MetricFn } from '@/lib/metric-contract'

export const fetchData: MetricFn = async (sdk) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  return ((await new Jobs(sdk).getAll({ filter: "SourceType eq 'Agent'" }))?.items ?? []).map(x => ({ ...x }))
}
EOF
echo "seeded semantic fixture (compiling wrong-field filter)"
