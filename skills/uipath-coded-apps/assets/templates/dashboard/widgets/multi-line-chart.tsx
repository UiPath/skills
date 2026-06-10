import React from 'react'
import { useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { <ICON> } from 'lucide-react'
<HOOK_IMPORT>
<RESPONSE_TYPE_IMPORT>
<SDK_IMPORT_LINE>
import { ViewAllLink, LoadingState, EmptyState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

// SERIES: define which fields to plot as separate lines
// e.g. [{ key: 'P50', color: 'hsl(var(--chart-1))' }, { key: 'P95', color: 'hsl(var(--chart-2))' }]
const SERIES: { key: string; color: string; label?: string }[] = <SERIES>

export function <COMPONENT_NAME>() {
  const navigate = useNavigate()
  const { data, loading, error } = <DATA_HOOK>

  if (loading) return <LoadingState />
  if (error) return <EmptyState message={error.message} />

  // For multi-series from a flat array (e.g. [{name:'P50',value:6,date:'...'},{name:'P95',...}])
  // pivot into [{date, P50: 6, P95: 12}, ...] before passing to LineChart
  const rawData = <DATA_SELECTOR>
  const chartData: Record<string, unknown>[] = <PIVOT_EXPRESSION>
  // PIVOT_EXPRESSION example for {name,value,date} arrays:
  // rawData.reduce((acc, row) => { const d=acc.find(r=>r.date===row.date)||{date:row.date}; d[row.name]=row.value; if(!acc.find(r=>r.date===row.date)) acc.push(d); return acc; }, [])

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => navigate('<DETAIL_ROUTE>')}
    >
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-muted p-2">
            <<ICON> className="w-4 h-4 text-muted-foreground" />
          </div>
          <div>
            <CardTitle className="text-base"><TITLE></CardTitle>
            <CardDescription><SUBTITLE></CardDescription>
          </div>
        </div>
        <ViewAllLink to="<DETAIL_ROUTE>" />
      </CardHeader>
      <CardContent className="pt-0">
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <XAxis
              dataKey="<X_KEY>"
              tick={{ fontSize: 11 }}
              tickFormatter={(v: string | number) => {
                const d = new Date(String(v))
                return isNaN(d.getTime()) ? String(v) : d.toLocaleDateString([], { month: 'short', day: 'numeric' })
              }}
            />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            {SERIES.map(s => (
              <Line key={s.key} dataKey={s.key} name={s.label ?? s.key} stroke={s.color} dot={false} strokeWidth={2} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
