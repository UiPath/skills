import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { <ICON> } from 'lucide-react'
import { <SDK_SERVICE> } from '<SDK_IMPORT>'
import { useAuth } from '@/hooks/useAuth'
import { DeltaBadge, ViewAllLink, LoadingState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

export function <COMPONENT_NAME>() {
  const navigate = useNavigate()
  const { sdk, isAuthenticated } = useAuth()
  const [value, setValue] = useState<string>('—')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return
    let cancelled = false
    setLoading(true)
    const svc = new <SDK_SERVICE>(sdk as never)
    svc.<SDK_CALL>
      .then((r: <SDK_RESULT_TYPE>) => { if (!cancelled) setValue(<VALUE_EXPRESSION>) })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e : new Error(String(e))) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [sdk, isAuthenticated])

  if (loading) return <LoadingState height="h-32" />

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
            <CardDescription><DESCRIPTION></CardDescription>
          </div>
        </div>
        <ViewAllLink to="<DETAIL_ROUTE>" />
      </CardHeader>
      <div className="px-6 pb-4 flex items-baseline gap-3">
        <span className="text-3xl font-semibold tabular-nums">{error ? '—' : value}</span>
        <DeltaBadge direction="<DELTA_DIR>" text="<DELTA_TEXT>" />
      </div>
    </Card>
  )
}
