import { useState, useEffect } from 'react'
import { useAuth } from './useAuth'
import { InsightsClient, type InsightsParams } from '../lib/insights-client'

type AgentsMethods     = keyof InsightsClient['agents']
type TraceviewMethods  = keyof InsightsClient['traceview']
type GovernanceMethods = keyof InsightsClient['governance']
type JobsMethods       = keyof InsightsClient['jobs']

export type InsightsKey =
  | `agents.${AgentsMethods}`
  | `traceview.${TraceviewMethods}`
  | `governance.${GovernanceMethods}`
  | `jobs.${JobsMethods}`

export function useInsights<T>(
  key: InsightsKey,
  params: Omit<InsightsParams, 'tenantId'>,
  deps: unknown[] = []
) {
  const { getToken, tenantId } = useAuth()
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    // VITE_UIPATH_CLOUD_URL = Data.BaseUrl from uip login (e.g. https://alpha.uipath.com)
    // VITE_UIPATH_BASE_URL  = API base with "api." subdomain (e.g. https://alpha.api.uipath.com)
    const cloudUrl = import.meta.env.VITE_UIPATH_CLOUD_URL as string
    const apiUrl   = import.meta.env.VITE_UIPATH_BASE_URL as string
    const org      = import.meta.env.VITE_UIPATH_ORG_NAME as string
    const tenant   = import.meta.env.VITE_UIPATH_TENANT_NAME as string
    const client = new InsightsClient(
      `${cloudUrl}/${org}/${tenant}/insightsrtm_`,  // Insights RTM: alpha.uipath.com/org/tenant/insightsrtm_
      `${apiUrl}/${org}/${tenant}`,                 // Jobs API: alpha.api.uipath.com/org/tenant
      getToken
    )

    const [ns, method] = key.split('.') as [
      'agents' | 'traceview' | 'governance' | 'jobs',
      string
    ]
    const fullParams = { ...params, tenantId } as InsightsParams
    const call = (client[ns] as Record<string, (p: InsightsParams) => Promise<T>>)[method]

    call(fullParams)
      .then((d) => { if (!cancelled) setData(d) })
      .catch((e: Error) => { if (!cancelled) setError(e) })
      .finally(() => { if (!cancelled) setLoading(false) })

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, error, loading }
}
