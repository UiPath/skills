import React from 'react'
import MetricCard from '../components/MetricCard'
import { useInsights } from '../hooks/useInsights'

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>

  // Navigate the response using the path from insights-catalog.md Key response fields.
  // Examples:
  //   agents.getSummaryV2: String((data as any)?.data?.currentPeriodSummary?.successRate?.toFixed(1) + '%' ?? '—')
  //   agents.getAgents:    String((data as any)?.data?.agents?.length ?? '—')
  const value: string = <VALUE_EXPRESSION>

  return (
    <MetricCard
      title="<TITLE>"
      value={value}
      loading={loading}
      error={error?.message}
    />
  )
}
