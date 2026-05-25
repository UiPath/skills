import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { useInsights } from '../hooks/useInsights'

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>

  // Most Insights responses wrap the array in a nested object.
  // Extract with the path from insights-catalog.md Key response fields.
  // Example for topErroredAgents: const chartData = (data as any)?.data ?? []
  const chartData: Record<string, unknown>[] = <DATA_SELECTOR>

  if (loading) return <div className="h-64 animate-pulse rounded-lg bg-muted" />
  if (error) return <div className="rounded-lg border bg-card p-4 text-sm text-destructive">{error.message}</div>

  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="mb-3 text-sm font-medium text-muted-foreground"><TITLE></h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={chartData}>
          <XAxis dataKey="<X_KEY>" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="<Y_KEY>" fill="hsl(var(--primary))" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
