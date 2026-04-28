# UI Patterns Reference

## Polling for Real-Time Updates

When a component needs to auto-refresh data (e.g., monitoring process instance status or variables), create `src/hooks/usePolling.ts`:

```typescript
import { useEffect, useRef, useCallback, useState } from 'react';

interface UsePollingOptions<T> {
  fetchFn: () => Promise<T>;
  interval?: number;       // ms, default 5000
  enabled?: boolean;       // toggle on/off
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  immediate?: boolean;     // fetch on mount, default true
  deps?: unknown[];        // Reset and refetch immediately when any dep changes (e.g., [instanceId])
}

interface UsePollingResult<T> {
  data: T | null;
  isLoading: boolean;      // True only during initial fetch (before first data arrives)
  error: Error | null;
  refetch: () => Promise<void>;
  start: () => void;
  stop: () => void;
  isActive: boolean;       // Whether the polling interval is running (use for "Live" indicator)
  lastUpdated: Date | null;
}

export function usePolling<T>({
  fetchFn, interval = 5000, enabled = true,
  onSuccess, onError, immediate = true, deps = [],
}: UsePollingOptions<T>): UsePollingResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [isActive, setIsActive] = useState(enabled);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => { setIsActive(enabled); }, [enabled]);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fetchFnRef = useRef(fetchFn);
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);
  const hasLoadedRef = useRef(false);

  useEffect(() => { fetchFnRef.current = fetchFn; }, [fetchFn]);
  useEffect(() => { onSuccessRef.current = onSuccess; }, [onSuccess]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);

  const prevJsonRef = useRef<string>('');

  const executeFetch = useCallback(async () => {
    try {
      const result = await fetchFnRef.current();
      // Only update state if data actually changed — prevents unnecessary re-renders
      const json = JSON.stringify(result);
      if (json !== prevJsonRef.current) {
        prevJsonRef.current = json;
        setData(result);
        setLastUpdated(new Date());
      }
      // Clear any previous error only if it was set (avoid no-op setState)
      setError(prev => prev === null ? prev : null);
      onSuccessRef.current?.(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      onErrorRef.current?.(error);
    } finally {
      // Only transition from loading → loaded once (on first successful or failed fetch)
      if (!hasLoadedRef.current) {
        hasLoadedRef.current = true;
        setIsLoading(false);
      }
    }
  }, []);

  const start = useCallback(() => setIsActive(true), []);
  const stop = useCallback(() => {
    setIsActive(false);
    if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
  }, []);
  const refetch = useCallback(async () => { await executeFetch(); }, [executeFetch]);

  // Serialize deps for comparison — when deps change, reset everything and refetch
  const depsKey = JSON.stringify(deps);
  const prevDepsKeyRef = useRef(depsKey);

  useEffect(() => {
    // Detect if deps changed (e.g., user selected a different instance)
    const depsChanged = depsKey !== prevDepsKeyRef.current;
    if (depsChanged) {
      prevDepsKeyRef.current = depsKey;
      // Full reset: clear old data, show loading, refetch immediately
      hasLoadedRef.current = false;
      prevJsonRef.current = '';
      setData(null);
      setIsLoading(true);
      setError(null);
    }

    if (!isActive || !enabled) {
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      return;
    }
    if (intervalRef.current) { clearInterval(intervalRef.current); }
    if (immediate || depsChanged) executeFetch();
    intervalRef.current = setInterval(executeFetch, interval);
    return () => { if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; } };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive, enabled, interval, immediate, executeFetch, depsKey]);

  return { data, isLoading, error, refetch, start, stop, isActive, lastUpdated };
}
```

### Usage with SDK services

```typescript
import { useMemo, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { usePolling } from '../hooks/usePolling';
import { ProcessInstances } from '@uipath/uipath-typescript/maestro-processes';

function InstanceMonitor({ instanceId, folderKey }: { instanceId: string; folderKey: string }) {
  const { sdk, isAuthenticated } = useAuth();
  const processInstances = useMemo(() => new ProcessInstances(sdk), [sdk]);

  const fetchVariables = useCallback(async () => {
    return processInstances.getVariables(instanceId, folderKey);
  }, [processInstances, instanceId, folderKey]);

  const { data: variables, isLoading, isActive, error } = usePolling({
    fetchFn: fetchVariables,
    interval: 5000,
    enabled: isAuthenticated && !!instanceId,
    immediate: true,
    deps: [instanceId],  // Reset and refetch when instance changes
  });

  // isLoading — true until first data arrives, AND resets to true on instance switch
  // isActive  — true while the polling interval is running (show "Live" indicator)
  // Render variables...
}
```

### Key options

- `deps` — **CRITICAL for master-detail UIs.** Pass values that identify what you're polling (e.g., `[instanceId]`). When any dep changes, the hook resets `data` to `null`, sets `isLoading` to `true`, and immediately refetches. Without this, switching between items shows stale data with no loading indicator.
- `enabled` — tie to a condition (e.g., `!!selectedInstance`) so polling only runs when needed
- `immediate: false` — skip first fetch if the initial data is already loaded by another effect
- `interval` — default 5000ms; increase for less-critical data to reduce API load

### Master-detail pattern — MANDATORY for list + detail layouts

When the app has a list on the left and a detail panel on the right (e.g., instance list → instance details), **both** of the following are required:

**1. Always use `key` prop on the detail component:**

```typescript
// Parent component
{selectedInstance && (
  <InstanceDetail
    key={selectedInstance.id}  // Forces full remount on switch
    instanceId={selectedInstance.id}
    folderKey={selectedInstance.folderKey}
  />
)}
```

The `key` prop forces React to unmount the old component and mount a fresh one when the selected item changes. This resets all hooks (including `usePolling`), clears stale data, and shows the loading state naturally.

**2. Always pass `deps` to `usePolling` in detail components:**

```typescript
// Inside InstanceDetail component
const { data, isLoading, isActive } = usePolling({
  fetchFn: fetchInstanceData,
  interval: 5000,
  enabled: isAuthenticated && !!instanceId,
  deps: [instanceId],  // Resets data/loading when instance changes
});
```

Both are needed as defense-in-depth — `key` handles React component state, `deps` handles the polling hook's internal refs (`hasLoadedRef`, `prevJsonRef`).

**Why both?** The `key` prop alone works, but if a parent component refactors away the `key`, the `deps` mechanism still ensures correct behavior. The `deps` alone works for the hook, but doesn't reset other component state (e.g., local `useState` for tabs, expanded sections).

### Flicker-free updates — MANDATORY

Polling must NEVER cause visible UI flicker. Follow ALL three rules:

#### Rule 1: No per-cycle state changes in the hook

The hook does NOT use state for in-flight fetch status. **NEVER** add `setIsPolling(true)` / `setIsPolling(false)` or `setIsLoading(true)` / `setIsLoading(false)` around each fetch. This causes 2 re-renders per poll cycle, making every table row visibly flash.

- **`isLoading`** — only transitions once: `true` → `false` after the first fetch. NEVER set it back to `true`.
- **`isActive`** — only changes when polling starts/stops. Use for "Live" indicator.
- **`setError`** — functional update to avoid no-op state sets.

#### Rule 2: Accumulate variables and sort for stable rows

**THIS IS THE MOST IMPORTANT RULE.** The `getVariables()` API returns **different subsets of variables across polls** (as different activities execute, different variables become visible) and in **non-deterministic order**. This causes table rows to appear, disappear, and jump around between poll cycles — visible as flicker even when the hook doesn't re-render unnecessarily.

**Fix:** Accumulate all variables ever seen for an instance in a `Map` (keyed by `id`), update values when they reappear, and sort by name for stable row order. Same for elements. Reset all maps when switching instances.

```typescript
import type { GlobalVariableMetaData, ElementMetaData } from '@uipath/uipath-typescript/maestro-processes';

// Accumulated variables & elements — survive across polls, reset on instance switch
const accumulatedVarsRef = useRef<Map<string, GlobalVariableMetaData>>(new Map());
const accumulatedElementsRef = useRef<
  Map<string, { elementId: string; isMarker: boolean; inputs: Record<string, unknown>; outputs: Record<string, unknown> }>
>(new Map());

// Reset when switching instances
if (instanceId !== lastInstanceIdRef.current) {
  lastInstanceIdRef.current = instanceId;
  lastDataRef.current = null;
  accumulatedVarsRef.current = new Map();
  accumulatedElementsRef.current = new Map();
}

// Merge incoming data into accumulated maps (latest value wins)
if (displayData) {
  for (const v of displayData.variables.globalVariables) {
    accumulatedVarsRef.current.set(v.id, v);
  }
  for (const e of displayData.variables.elements) {
    if (Object.keys(e.inputs).length > 0 || Object.keys(e.outputs).length > 0) {
      accumulatedElementsRef.current.set(e.elementId, e);
    }
  }
}

// Stable sorted arrays — row order never jumps between polls
const displayVars = [...accumulatedVarsRef.current.values()].sort((a, b) =>
  a.name.localeCompare(b.name)
);
const displayElements = [...accumulatedElementsRef.current.values()].sort((a, b) =>
  a.elementId.localeCompare(b.elementId)
);

// Render using displayVars / displayElements — NOT displayData.variables directly
```

**Why this works:**
- **Accumulation** — variables that appeared in a previous poll but not the current one stay in the table. No rows disappear.
- **Latest value wins** — when a variable reappears, its value updates to the latest. The Map key is `v.id`, so the same variable always occupies the same entry.
- **Stable sort** — alphabetical by `name` (variables) or `elementId` (elements) ensures rows never shuffle between polls.
- **Reset on instance switch** — maps clear when the user selects a different instance, so stale data from the previous instance is never shown.

#### Rule 3: Components must NEVER tear down the data UI

Even with accumulation, the table can still flicker if the component conditionally removes and re-adds it. Use a `useRef` to preserve the last known raw data so the table DOM is never destroyed during polls:

```typescript
// Preserve raw data during polling, reset when switching items
const lastDataRef = useRef<InstanceData | null>(null);
const lastInstanceIdRef = useRef(instanceId);

if (instanceId !== lastInstanceIdRef.current) {
  lastInstanceIdRef.current = instanceId;
  lastDataRef.current = null;  // Reset — show loading for new instance
}
if (data) lastDataRef.current = data;
const displayData = lastDataRef.current;

// Show loading when no data yet (initial load OR after switching to a different item)
if (!displayData) return <LoadingSpinner />;
```

#### Complete flicker-free component pattern

```typescript
import { useCallback, useMemo, useRef } from 'react';
import type {
  ProcessInstanceGetVariablesResponse,
  GlobalVariableMetaData,
} from '@uipath/uipath-typescript/maestro-processes';

function InstanceDataPanel({ instanceId, folderKey }: Props) {
  const { sdk, isAuthenticated } = useAuth();
  const svc = useMemo(() => new ProcessInstances(sdk), [sdk]);

  const fetchFn = useCallback(
    () => svc.getVariables(instanceId, folderKey),
    [svc, instanceId, folderKey]
  );

  const { data, isLoading, isActive, error } = usePolling({
    fetchFn,
    interval: 5000,
    enabled: isAuthenticated && !!instanceId,
    deps: [instanceId],  // Reset and refetch when instance changes
  });

  // --- Flicker prevention refs ---
  const lastDataRef = useRef<ProcessInstanceGetVariablesResponse | null>(null);
  const lastInstanceIdRef = useRef(instanceId);
  const accumulatedVarsRef = useRef<Map<string, GlobalVariableMetaData>>(new Map());
  const accumulatedElementsRef = useRef<
    Map<string, { elementId: string; isMarker: boolean; inputs: Record<string, unknown>; outputs: Record<string, unknown> }>
  >(new Map());

  // Reset everything when switching instances
  if (instanceId !== lastInstanceIdRef.current) {
    lastInstanceIdRef.current = instanceId;
    lastDataRef.current = null;
    accumulatedVarsRef.current = new Map();
    accumulatedElementsRef.current = new Map();
  }
  if (data) lastDataRef.current = data;
  const displayData = lastDataRef.current;

  // Accumulate variables and elements into stable maps
  if (displayData) {
    for (const v of displayData.globalVariables) {
      accumulatedVarsRef.current.set(v.id, v);
    }
    for (const e of displayData.elements) {
      if (Object.keys(e.inputs).length > 0 || Object.keys(e.outputs).length > 0) {
        accumulatedElementsRef.current.set(e.elementId, e);
      }
    }
  }

  // Stable sorted arrays for rendering
  const displayVars = [...accumulatedVarsRef.current.values()].sort((a, b) =>
    a.name.localeCompare(b.name)
  );
  const displayElements = [...accumulatedElementsRef.current.values()].sort((a, b) =>
    a.elementId.localeCompare(b.elementId)
  );

  // Loading — only on initial load or instance switch
  if (!displayData) {
    if (error) return <div>Error: {error.message}</div>;
    return <div>Loading...</div>;
  }

  return (
    <div>
      {error && (
        <div className="text-sm text-red-600 p-2 bg-red-50 rounded mb-2">
          {error.message}
        </div>
      )}
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-sm font-semibold">Process Data</h3>
        {isActive && (
          <span className="flex items-center gap-1 text-xs text-gray-400">
            <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
            Live
          </span>
        )}
      </div>

      {/* Render from accumulated + sorted arrays — NOT raw displayData */}
      {displayVars.length > 0 && (
        <ProcessDataTable globalVariables={displayVars} />
      )}

      {displayElements.length > 0 && (
        <div className="mt-4 space-y-2">
          {displayElements.map(element => (
            <ElementCard key={element.elementId} element={element} />
          ))}
        </div>
      )}
    </div>
  );
}
```

**Key properties of this pattern:**
- **No rows appear/disappear during polling** — accumulated Map keeps all variables ever seen
- **No row reordering** — stable alphabetical sort on every render
- **Values update in-place** — Map overwrites existing entries with latest values
- **Clean reset on instance switch** — maps clear, loading spinner shows, fresh data loads
- **Table DOM never torn down** — `lastDataRef` prevents conditional removal during polls
- `isActive` drives a pure CSS animation (no state toggle, no re-render)

## BPMN Diagram Rendering

To visualize Maestro process diagrams, use `bpmn-js` (from bpmn.io) with the BPMN XML returned by `ProcessInstances.getBpmn()`.

### Setup

```bash
npm install bpmn-js
```

Add CSS imports in `src/index.css` (or the component file):

```css
@import 'bpmn-js/dist/assets/diagram-js.css';
@import 'bpmn-js/dist/assets/bpmn-font/css/bpmn-embedded.css';

/* Hide bpmn.io watermark */
.bjs-powered-by { display: none !important; }
```

### BPMN Viewer component

```typescript
import { useEffect, useRef } from 'react';
import BpmnViewer from 'bpmn-js/lib/Viewer';

interface BpmnDiagramProps {
  bpmnXml: string;
}

export const BpmnDiagram = ({ bpmnXml }: BpmnDiagramProps) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !bpmnXml) return;

    const viewer = new BpmnViewer({ container: containerRef.current });

    (async () => {
      try {
        await viewer.importXML(bpmnXml);
        viewer.get('canvas').zoom('fit-viewport');
      } catch (err) {
        console.error('Error rendering BPMN:', err);
      }
    })();

    return () => { viewer.destroy(); };
  }, [bpmnXml]);

  return <div ref={containerRef} style={{ width: '100%', height: '500px' }} />;
};
```

### Fetching BPMN XML

```typescript
// Via service method
const bpmnXml = await processInstances.getBpmn(instanceId, folderKey);

// Or via bound method on an instance object
const instance = await processInstances.getById(instanceId, folderKey);
const bpmnXml = await instance.getBpmn();
```

Then render: `<BpmnDiagram bpmnXml={bpmnXml} />`

## Rendering Process Instance Data (Variables & Elements)

When displaying process instance variables (`getVariables()` response), **NEVER dump raw JSON**. The response contains deeply nested objects that are unreadable as raw text. Always parse and render structured UI.

### Naming convention

The tab/section label should fit the context:
- If the app is focused on a **single specific process** (e.g., "Loan Origination Dashboard"), use a domain-specific name like **"Loan Details"**, **"Application Data"**, or **"Extraction Results"** — whatever describes what those variables actually represent.
- If the app is a **generic process monitor** listing multiple processes, use **"Process Data"** as the tab/section name. Avoid "Variables" — it's a developer concept that means nothing to end users.

### Rendering `globalVariables`

Display as a clean key-value table. Format values by type.

```typescript
import type { GlobalVariableMetaData } from '@uipath/uipath-typescript/maestro-processes';

interface ProcessDataTableProps {
  globalVariables: GlobalVariableMetaData[];
}

function ProcessDataTable({ globalVariables }: ProcessDataTableProps) {
  if (globalVariables.length === 0) {
    return <p className="text-sm text-gray-500 p-4">No data available</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {globalVariables.map((v) => (
            <tr key={v.id}>
              <td className="px-4 py-3 text-sm font-medium text-gray-900 whitespace-nowrap">{v.name}</td>
              <td className="px-4 py-3 text-sm text-gray-700 max-w-md">
                <FormattedValue value={v.value} type={v.type} />
              </td>
              <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">{v.type}</span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">{v.source}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Rendering `elements` (activity step data)

Each element represents an executed activity with inputs and outputs. Render as collapsible cards — show the element name (derived from `elementId`) as the header, then inputs and outputs as structured sections inside.

```typescript
import { useState } from 'react';
import type { ElementMetaData } from '@uipath/uipath-typescript/maestro-processes';

interface ElementCardProps {
  element: ElementMetaData;
}

function ElementCard({ element }: ElementCardProps) {
  const [expanded, setExpanded] = useState(false);

  const hasInputs = Object.keys(element.inputs).length > 0;
  const hasOutputs = Object.keys(element.outputs).length > 0;

  if (!hasInputs && !hasOutputs) return null; // Skip empty elements

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 text-left"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900">{element.elementId}</span>
          {element.isMarker && (
            <span className="text-xs px-1.5 py-0.5 bg-yellow-100 text-yellow-700 rounded">Marker</span>
          )}
        </div>
        <span className="text-gray-400 text-sm">{expanded ? '−' : '+'}</span>
      </button>
      {expanded && (
        <div className="p-4 space-y-4">
          {hasInputs && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Inputs</h4>
              <KeyValueRenderer data={element.inputs} />
            </div>
          )}
          {hasOutputs && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Outputs</h4>
              <KeyValueRenderer data={element.outputs} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### Value formatting helpers

Use these to render any value cleanly — primitives as text, objects/arrays as structured UI.

```typescript
/** Renders a typed value from globalVariables */
function FormattedValue({ value, type }: { value: any; type: string }) {
  if (value === null || value === undefined) {
    return <span className="text-gray-400 italic">—</span>;
  }
  if (typeof value === 'boolean') {
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        value ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
      }`}>
        {value ? 'True' : 'False'}
      </span>
    );
  }
  if (typeof value === 'number') {
    return <span className="font-mono text-sm">{value.toLocaleString()}</span>;
  }
  if (typeof value === 'string') {
    // Detect JSON strings that were double-serialized
    if (value.startsWith('{') || value.startsWith('[')) {
      try {
        const parsed = JSON.parse(value);
        return <KeyValueRenderer data={parsed} />;
      } catch {
        // Not JSON, render as string
      }
    }
    return <span className="text-sm">{value}</span>;
  }
  if (Array.isArray(value)) {
    return <KeyValueRenderer data={value} />;
  }
  if (typeof value === 'object') {
    return <KeyValueRenderer data={value} />;
  }
  return <span className="text-sm">{String(value)}</span>;
}

/** Recursively renders a Record or array as a structured key-value list */
function KeyValueRenderer({ data }: { data: Record<string, any> | any[] }) {
  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-gray-400 text-sm italic">Empty list</span>;
    return (
      <div className="space-y-2">
        {data.map((item, i) => (
          <div key={i} className="pl-3 border-l-2 border-gray-200">
            <span className="text-xs text-gray-400 mb-1 block">#{i + 1}</span>
            {typeof item === 'object' && item !== null
              ? <KeyValueRenderer data={item} />
              : <span className="text-sm text-gray-700">{String(item)}</span>
            }
          </div>
        ))}
      </div>
    );
  }

  const entries = Object.entries(data);
  if (entries.length === 0) return <span className="text-gray-400 text-sm italic">Empty</span>;

  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
      {entries.map(([key, val]) => (
        <div key={key} className="contents">
          <dt className="text-xs text-gray-500 py-1 whitespace-nowrap">{formatKey(key)}</dt>
          <dd className="text-sm text-gray-700 py-1 min-w-0 break-words">
            {val === null || val === undefined ? (
              <span className="text-gray-400 italic">—</span>
            ) : typeof val === 'object' ? (
              <KeyValueRenderer data={val} />
            ) : typeof val === 'boolean' ? (
              <span className={val ? 'text-green-600' : 'text-red-600'}>{String(val)}</span>
            ) : (
              String(val)
            )}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** Converts camelCase/snake_case keys to readable labels */
function formatKey(key: string): string {
  return key
    .replace(/([a-z])([A-Z])/g, '$1 $2')  // camelCase → camel Case
    .replace(/_/g, ' ')                     // snake_case → snake case
    .replace(/\b\w/g, c => c.toUpperCase()); // Capitalize words
}
```

### Complete usage — Process Instance detail panel

See the "Complete flicker-free component pattern" in the Flicker-free updates section above. That example includes all required patterns: `usePolling`, `lastDataRef` preservation, variable accumulation via `Map`, stable sort, and instance-switch reset.

### Rules for rendering process data

1. **NEVER render raw JSON.** Always parse objects and render structured UI (tables, key-value grids, collapsible cards).
2. **Handle double-serialized JSON strings.** Values from process variables are sometimes JSON-serialized strings (e.g., `"{\"key\": \"value\"}"`). Always try `JSON.parse()` on string values that start with `{` or `[`.
3. **Format keys for readability.** Convert `camelCase` and `snake_case` to title-cased words with spaces.
4. **Skip empty data.** Don't show elements with empty inputs AND empty outputs. Don't show sections with zero items.
5. **Use appropriate labels.** "Process Data" for the global variables section, "Activity Details" for element data. Adapt naming to the specific domain when possible.
6. **Show type badges** on global variables — helps users understand what kind of data each variable holds.
7. **Make element cards collapsible** — elements can have very large nested input/output structures; don't expand all by default.
8. **Poll for updates** when the process is still running — variables change during execution.
9. **NEVER render raw `getVariables()` arrays directly in polled components.** The API returns different variable subsets and in non-deterministic order across polls — rows will appear, disappear, and shuffle. Instead, accumulate all variables into a `Map<id, variable>` ref (latest value wins) and sort by name before rendering. Same for elements — accumulate in a `Map<elementId, element>` and sort by elementId. Reset both maps when switching instances. Also use `lastDataRef` to preserve raw data during polls so the table DOM is never torn down. See "Flicker-free updates" Rules 2 and 3 for the complete pattern.

## HITL Detection (Human-in-the-Loop)

To determine whether a running process instance is currently waiting on a human task, use `getVariables()` + `getBpmn()`. This avoids calling `getExecutionHistory()`.

### How it works

1. **`getVariables()`** returns an `elements` array — the last element is the currently active BPMN element.
2. **`getBpmn()`** returns the BPMN XML. Parse it to find the element type for that `elementId`.
3. If the BPMN element is `<bpmn:userTask>`, the instance is pending on a human task.

**IMPORTANT:** `latestRunStatus` on the instance is NOT useful for HITL detection — a process waiting on a human task still shows as `"Running"`.

### HITL detection helper

```typescript
import { ProcessInstances } from '@uipath/uipath-typescript/maestro-processes';
import type { BpmnXmlString, ProcessInstanceGetVariablesResponse } from '@uipath/uipath-typescript/maestro-processes';

interface HitlStatus {
  isUserTask: boolean;
  activityType: string;  // e.g., "user task", "service task", "script task"
  elementId: string | null;
}

/**
 * Detects whether a process instance is currently waiting on a human task.
 * Uses getVariables() to find the active element, then getBpmn() to check its type.
 */
export async function detectHitlStatus(
  processInstances: ProcessInstances,
  instanceId: string,
  folderKey: string,
  // Optional: pass pre-fetched data to avoid redundant calls
  prefetchedVariables?: ProcessInstanceGetVariablesResponse,
  prefetchedBpmn?: BpmnXmlString,
): Promise<HitlStatus> {
  // 1. Get the last active element from variables
  const variables = prefetchedVariables ?? await processInstances.getVariables(instanceId, folderKey);
  const lastElement = variables.elements[variables.elements.length - 1];
  const elementId = lastElement?.elementId ?? null;

  if (!elementId) {
    return { isUserTask: false, activityType: 'Unknown', elementId: null };
  }

  // 2. Parse BPMN XML to find the element type
  const bpmnXml = prefetchedBpmn ?? await processInstances.getBpmn(instanceId, folderKey);
  const match = bpmnXml.match(new RegExp(`<bpmn:(\\w+)\\s+id="${elementId}"`));

  if (!match?.[1]) {
    return { isUserTask: false, activityType: 'Unknown', elementId };
  }

  // Convert camelCase BPMN type to readable form: "userTask" → "user task"
  const activityType = match[1].replace(/([A-Z])/g, ' $1').trim().toLowerCase();
  return {
    isUserTask: activityType === 'user task',
    activityType,
    elementId,
  };
}
```

### Usage in a component

```typescript
import { useMemo, useCallback, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import { usePolling } from '../hooks/usePolling';
import { ProcessInstances } from '@uipath/uipath-typescript/maestro-processes';
import type { GlobalVariableMetaData } from '@uipath/uipath-typescript/maestro-processes';
import { detectHitlStatus } from '../utils/hitl';

interface InstanceData {
  variables: ProcessInstanceGetVariablesResponse;
  bpmnXml: BpmnXmlString;
  hitl: HitlStatus;
}

function InstancePanel({ instanceId, folderKey }: { instanceId: string; folderKey: string }) {
  const { sdk, isAuthenticated } = useAuth();
  const processInstances = useMemo(() => new ProcessInstances(sdk), [sdk]);

  const fetchInstanceData = useCallback(async () => {
    const [variables, bpmnXml] = await Promise.all([
      processInstances.getVariables(instanceId, folderKey),
      processInstances.getBpmn(instanceId, folderKey),
    ]);
    const hitl = await detectHitlStatus(processInstances, instanceId, folderKey, variables, bpmnXml);
    return { variables, bpmnXml, hitl };
  }, [processInstances, instanceId, folderKey]);

  const { data, isLoading, isActive } = usePolling<InstanceData>({
    fetchFn: fetchInstanceData,
    interval: 5000,
    enabled: isAuthenticated && !!instanceId,
    deps: [instanceId],  // Reset and refetch when instance changes
  });

  // Flicker prevention — see "Flicker-free updates" for full explanation
  const lastDataRef = useRef<InstanceData | null>(null);
  const lastInstanceIdRef = useRef(instanceId);
  const accumulatedVarsRef = useRef<Map<string, GlobalVariableMetaData>>(new Map());

  if (instanceId !== lastInstanceIdRef.current) {
    lastInstanceIdRef.current = instanceId;
    lastDataRef.current = null;
    accumulatedVarsRef.current = new Map();
  }
  if (data) lastDataRef.current = data;
  const displayData = lastDataRef.current;

  // Accumulate + sort variables
  if (displayData) {
    for (const v of displayData.variables.globalVariables) {
      accumulatedVarsRef.current.set(v.id, v);
    }
  }
  const displayVars = [...accumulatedVarsRef.current.values()].sort((a, b) =>
    a.name.localeCompare(b.name)
  );

  if (!displayData) return <div>Loading...</div>;

  // Render using displayVars (accumulated + sorted) and displayData.hitl
  // displayData.hitl.isUserTask → show "Active User Task" UI
  // displayData.hitl.activityType → show the current activity type
  // displayVars → render process data table (stable rows)
  // displayData.bpmnXml → render BPMN diagram
}
```

### Getting the task for the instance

When HITL is detected via BPMN, you may also want to open the task in Action Center. Use the `CreatorJobKey` OData filter to find the task — the instance ID is the `CreatorJobKey`:

```typescript
import { Tasks } from '@uipath/uipath-typescript/tasks';
import { buildTaskUrl, getEmbedTaskUrl } from '../utils/formatters';

// Filter tasks by CreatorJobKey — the instanceId IS the CreatorJobKey
const result = await tasks.getAll({
  filter: `CreatorJobKey eq ${instanceId}`,
  pageSize: 10,
});

const pendingTask = result.items.find(t => !t.isCompleted) ?? null;

// Build the embed URL from the task ID
if (pendingTask) {
  const taskLink = buildTaskUrl(pendingTask.id);
  const embedUrl = getEmbedTaskUrl(taskLink);
  // Open in iframe...
}
```

### Rendering HITL status in the UI

```typescript
{data?.hitl.isUserTask ? (
  <div className="flex items-center gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
    <div className="p-2 bg-amber-100 rounded-lg">
      <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    </div>
    <div>
      <h4 className="font-semibold text-amber-900">Waiting on Human Review</h4>
      <p className="text-sm text-amber-700">This instance requires human input to continue</p>
    </div>
    {/* Add "Open Task" button if task link is available */}
  </div>
) : (
  <div className="flex items-center gap-3 p-4 bg-gray-50 border border-gray-200 rounded-lg">
    <div className="p-2 bg-gray-100 rounded-lg">
      <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
    <div>
      <h4 className="font-semibold text-gray-900">Automated Process</h4>
      <p className="text-sm text-gray-600">Current step: {data?.hitl.activityType}</p>
    </div>
  </div>
)}
```

## Embedding Action Center Tasks (HITL)

When a user needs to view or complete an Action Center task (human-in-the-loop task, action app, or escalation) inside the app, embed it via iframe using UiPath's embed URL format.

### Embed URL format

The standard Action Center URL looks like:
```
https://cloud.uipath.com/{orgName}/{tenantName}/actions_/current-task/tasks/{taskId}
```

The **embed** URL inserts `embed_/` after the origin:
```
https://cloud.uipath.com/embed_/{orgName}/{tenantName}/actions_/current-task/tasks/{taskId}
```

### API-to-Cloud URL mapping

**CRITICAL:** The API base URL (`VITE_UIPATH_BASE_URL`) and the cloud UI URL use different hostnames. You must map correctly when constructing task URLs:

| API URL | Cloud UI URL |
|---------|-------------|
| `https://api.uipath.com` | `https://cloud.uipath.com` |
| `https://staging.api.uipath.com` | `https://staging.uipath.com` |
| `https://alpha.api.uipath.com` | `https://alpha.uipath.com` |

**NEVER use naive string replacement** like `baseUrl.replace('api.', 'cloud.')` — this breaks for staging/alpha (produces `staging.cloud.uipath.com` which is wrong).

Add this helper to `src/utils/formatters.ts`:

```typescript
/** Maps an API base URL to the corresponding cloud UI URL */
export function apiToCloudUrl(apiBaseUrl: string): string {
  try {
    const url = new URL(apiBaseUrl);
    // "api.uipath.com" → "cloud.uipath.com"
    // "staging.api.uipath.com" → "staging.uipath.com"
    // "alpha.api.uipath.com" → "alpha.uipath.com"
    let cloudHost = url.hostname.replace('api.uipath.com', 'uipath.com');
    if (cloudHost === 'uipath.com') cloudHost = 'cloud.uipath.com';
    return `${url.protocol}//${cloudHost}`;
  } catch {
    return apiBaseUrl;
  }
}
```

### URL helper functions

Create `src/utils/formatters.ts` (or add to existing):

```typescript
/** Converts a standard Action Center URL to an embeddable iframe URL */
export const getEmbedTaskUrl = (taskUrl: string): string => {
  try {
    const url = new URL(taskUrl);
    const parts = url.pathname.split('/');
    const orgId = parts[1];
    const tenantId = parts[2];
    const taskId = parts[parts.length - 1];
    return `${url.origin}/embed_/${orgId}/${tenantId}/actions_/current-task/tasks/${taskId}`;
  } catch (e) {
    console.error('Error parsing task URL:', e);
    return taskUrl;
  }
};

/** Constructs a standard Action Center task URL from components */
export function buildTaskUrl(taskId: number | string): string {
  const baseUrl = import.meta.env.VITE_UIPATH_BASE_URL || '';
  const org = import.meta.env.VITE_UIPATH_ORG_NAME || '';
  const tenant = import.meta.env.VITE_UIPATH_TENANT_NAME || '';
  const cloudHost = apiToCloudUrl(baseUrl);
  return `${cloudHost}/${org}/${tenant}/actions_/current-task/tasks/${taskId}`;
}
```

### Getting the task link

To get an embeddable task URL, use the `CreatorJobKey` OData filter to find the task for the instance, then construct the URL with `buildTaskUrl()`:

```typescript
import { Tasks } from '@uipath/uipath-typescript/tasks';

// Filter tasks by CreatorJobKey — the instanceId IS the CreatorJobKey
const result = await tasks.getAll({
  filter: `CreatorJobKey eq ${instanceId}`,
  pageSize: 10,
});

const pendingTask = result.items.find(t => !t.isCompleted) ?? null;

// Build the embed URL
if (pendingTask) {
  const taskLink = buildTaskUrl(pendingTask.id);
  const embedUrl = getEmbedTaskUrl(taskLink);
  // Open in iframe...
}
```

**Do NOT construct the URL manually** — always use the `apiToCloudUrl` + `buildTaskUrl` helpers to ensure correct environment mapping across cloud/staging/alpha.

### iframe component

```typescript
import { getEmbedTaskUrl } from '../utils/formatters';

interface TaskEmbedProps {
  taskLink: string;
  onClose: () => void;
}

export const TaskEmbed = ({ taskLink, onClose }: TaskEmbedProps) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg shadow-xl w-[90vw] h-[90vh] flex flex-col">
      <div className="flex justify-between items-center p-4 border-b">
        <h3 className="text-lg font-medium text-gray-900">Task Details</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
      </div>
      <div className="flex-1 p-1">
        <iframe
          src={getEmbedTaskUrl(taskLink)}
          className="w-full h-full rounded border-0"
          title="Action Center Task"
        />
      </div>
    </div>
  </div>
);
```

### Key points

- **No extra auth needed**: The iframe loads from the same UiPath domain, so the user's existing browser session handles authentication automatically.
- **`embed_/` prefix is required**: Without it, the action center page renders with full navigation chrome. The embed URL gives a clean, frameable view.
- **Task link source**: Use `tasks.getAll({ filter: "CreatorJobKey eq ${instanceId}" })` to find the task, then build the URL with `buildTaskUrl(taskId)`.
- **HITL detection**: Use `getVariables()` + `getBpmn()` to detect if the current element is a user task (see "HITL Detection" section above). Do NOT rely on `latestRunStatus`.
- **Use `apiToCloudUrl()`** — never manually convert API URLs to cloud URLs with string replacement.
- **Use a modal overlay**: Render the iframe in a modal (like the example above) so the user can close it and return to the app.
