# Insights HTTP Client

Temporary HTTP client until Insights lands in `@uipath/uipath-typescript`.
When SDK ships: replace `InsightsClient` with the SDK class in `sdk-client.ts`.
No widget files, no hook call sites change on migration.

## Client Implementation (generated into every dashboard as `src/lib/insights-client.ts`)

```typescript
// All RTM endpoints (Agents, Traceview, Governance): base = …/insightsrtm_
// Jobs endpoints: base = …/<ORG>/<TENANT>  path = /api/v1.0/InsightsJobs/…

export interface InsightsParams {
  tenantId: string;        // UUID from VITE_INSIGHTS_TENANT_ID — never the tenant name string
  startTime: string;       // ISO 8601 — required, use startTime constants from build-plan.md, e.g. "2025-01-01T00:00:00Z"
  endTime: string;         // ISO 8601 — required, always pass endTime: NOW
  limit?: number;
  [key: string]: unknown;
}

export class InsightsClient {
  constructor(
    private rtmBase: string,   // ${VITE_UIPATH_BASE_URL}/${ORG}/${TENANT}/insightsrtm_
    private jobsBase: string,  // ${VITE_UIPATH_BASE_URL}/${ORG}/${TENANT}
    private getToken: () => Promise<string>
  ) {}

  private async post<T>(base: string, path: string, body: InsightsParams): Promise<T> {
    const token = await this.getToken();
    const res = await fetch(`${base}/${path}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (res.status === 401) throw new Error('INSIGHTS_AUTH_EXPIRED');
    if (!res.ok) throw new Error(`Insights ${res.status}: ${base}/${path}`);
    return res.json() as Promise<T>;
  }

  agents = {
    getSummaryV2:             (p: InsightsParams) => this.post(this.rtmBase, 'Agents/summaryV2', p),
    getErrors:                (p: InsightsParams) => this.post(this.rtmBase, 'Agents/errors', p),
    getTopErroredAgents:      (p: InsightsParams) => this.post(this.rtmBase, 'Agents/topErroredAgents', p),
    getIncidents:             (p: InsightsParams) => this.post(this.rtmBase, 'Agents/incidents', p),
    getIncidentDistribution:  (p: InsightsParams) => this.post(this.rtmBase, 'Agents/incidentDistribution', p),
    getConsumption:           (p: InsightsParams) => this.post(this.rtmBase, 'Agents/consumption', p),
    getConsumptionTimeline:   (p: InsightsParams) => this.post(this.rtmBase, 'Agents/consumptionTimeline', p),
    getLatencyTimeline:       (p: InsightsParams) => this.post(this.rtmBase, 'Agents/latencyTimeline', p),
    getAgents:                (p: InsightsParams) => this.post(this.rtmBase, 'Agents/agents', p),
    getUnitConsumption:       (p: InsightsParams) => this.post(this.rtmBase, 'Agents/summary/unit-consumption', p),
    getNames:                 (p: InsightsParams) => this.post(this.rtmBase, 'Agents/names', p),
  };

  traceview = {
    getLatencyTimeline:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/latencyTimeline', p),
    getErrorsTimeline:      (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/errorsTimeline', p),
    getMemoryTimeline:      (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/memoryTimeline', p),
    getMemoryCallsTimeline: (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/memoryCallsTimeline', p),
    getTopMemorySpaces:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/topMemorySpaces', p),
    getUnitConsumption:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/unitConsumption', p),
  };

  governance = {
    getPolicySummary:    (p: InsightsParams & { policy: string }) =>
                           this.post(this.rtmBase, 'Governance/policy/summary', p),
    getPolicyTraces:     (p: InsightsParams) => this.post(this.rtmBase, 'Governance/policy/traces', p),
    getOperationSummary: (p: InsightsParams) => this.post(this.rtmBase, 'Governance/operation/summary', p),
  };

  jobs = {
    getSummary:            (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/summary', p),
    getCompletedTimeline:  (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/completed-timeline', p),
    getUncompletedTimeline:(p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/uncompleted-timeline', p),
    getTopFailures:        (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/top-failures', p),
    getFailuresByReason:   (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/failures-by-reason', p),
    getProcessDetails:     (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/process-details', p),
    getFailureDetails:     (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/failure-details', p),
  };
}
```

## Initialization in sdk-client.ts

```typescript
import { InsightsClient } from './insights-client';

// VITE_UIPATH_CLOUD_URL = Data.BaseUrl from uip login (e.g. https://alpha.uipath.com)
// VITE_UIPATH_BASE_URL  = API base with "api." subdomain (e.g. https://alpha.api.uipath.com)
const cloudUrl = import.meta.env.VITE_UIPATH_CLOUD_URL;
const apiUrl   = import.meta.env.VITE_UIPATH_BASE_URL;
const org      = import.meta.env.VITE_UIPATH_ORG_NAME;
const tenant   = import.meta.env.VITE_UIPATH_TENANT_NAME;

export function createInsightsClient(getToken: () => Promise<string>): InsightsClient {
  return new InsightsClient(
    `${cloudUrl}/${org}/${tenant}/insightsrtm_`,  // Insights RTM: uses cloud URL, not api. subdomain
    `${apiUrl}/${org}/${tenant}`,                 // Jobs API: uses api. subdomain
    getToken
  );
}
```

## useInsights hook — namespace-qualified key

```typescript
// Key format: 'namespace.method'
// Examples: 'agents.getSummaryV2' | 'traceview.getLatencyTimeline' | 'governance.getPolicySummary'
// tenantId is injected automatically from useAuth() — callers only pass startTime/endTime/etc.
const { data, loading, error } = useInsights(
  'agents.getSummaryV2',
  { startTime: '2025-01-01T00:00:00Z' }
);
```

## SDK Migration Steps (when @uipath/uipath-typescript/insights ships)
1. In `sdk-client.ts`: replace `createInsightsClient(...)` with SDK Insights service init
2. Update `useInsights.ts` to use the SDK namespace calls
3. Delete `src/lib/insights-client.ts` from the scaffold template
4. Update `insights-catalog.md`: remove "HTTP client" note
No widget files change on migration — hook interface is stable.
