export interface InsightsParams {
  tenantId: string
  startTime: string  // required — omitting causes 500 errors
  endTime: string    // required — omitting causes 500 errors, use new Date().toISOString()
  limit?: number
  [key: string]: unknown
}

export class InsightsClient {
  constructor(
    private rtmBase: string,
    private jobsBase: string,
    private getToken: () => Promise<string>
  ) {}

  private async post<T>(base: string, path: string, body: InsightsParams): Promise<T> {
    const token = await this.getToken()
    const res = await fetch(`${base}/${path}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })
    if (res.status === 401) throw new Error('INSIGHTS_AUTH_EXPIRED')
    if (!res.ok) throw new Error(`Insights ${res.status}: ${path}`)
    return res.json() as Promise<T>
  }

  agents = {
    getSummaryV2:            (p: InsightsParams) => this.post(this.rtmBase, 'Agents/summaryV2', p),
    getErrors:               (p: InsightsParams) => this.post(this.rtmBase, 'Agents/errors', p),
    getTopErroredAgents:     (p: InsightsParams) => this.post(this.rtmBase, 'Agents/topErroredAgents', p),
    getIncidents:            (p: InsightsParams) => this.post(this.rtmBase, 'Agents/incidents', p),
    getIncidentDistribution: (p: InsightsParams) => this.post(this.rtmBase, 'Agents/incidentDistribution', p),
    getConsumption:          (p: InsightsParams) => this.post(this.rtmBase, 'Agents/consumption', p),
    getConsumptionTimeline:  (p: InsightsParams) => this.post(this.rtmBase, 'Agents/consumptionTimeline', p),
    getLatencyTimeline:      (p: InsightsParams) => this.post(this.rtmBase, 'Agents/latencyTimeline', p),
    getAgents:               (p: InsightsParams) => this.post(this.rtmBase, 'Agents/agents', p),
    getUnitConsumption:      (p: InsightsParams) => this.post(this.rtmBase, 'Agents/summary/unit-consumption', p),
    getNames:                (p: InsightsParams) => this.post(this.rtmBase, 'Agents/names', p),
  }

  traceview = {
    getLatencyTimeline:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/latencyTimeline', p),
    getErrorsTimeline:      (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/errorsTimeline', p),
    getMemoryTimeline:      (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/memoryTimeline', p),
    getMemoryCallsTimeline: (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/memoryCallsTimeline', p),
    getTopMemorySpaces:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/topMemorySpaces', p),
    getUnitConsumption:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/unitConsumption', p),
  }

  governance = {
    getPolicySummary:     (p: InsightsParams & { policy: string }) =>
                            this.post(this.rtmBase, 'Governance/policy/summary', p),
    getPolicyTraces:      (p: InsightsParams) => this.post(this.rtmBase, 'Governance/policy/traces', p),
    getOperationSummary:  (p: InsightsParams) => this.post(this.rtmBase, 'Governance/operation/summary', p),
  }

  jobs = {
    getSummary:             (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/summary', p),
    getCompletedTimeline:   (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/completed-timeline', p),
    getUncompletedTimeline: (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/uncompleted-timeline', p),
    getTopFailures:         (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/top-failures', p),
    getFailuresByReason:    (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/failures-by-reason', p),
    getProcessDetails:      (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/process-details', p),
    getFailureDetails:      (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/failure-details', p),
  }
}
