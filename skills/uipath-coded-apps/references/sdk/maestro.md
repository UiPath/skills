# Maestro Reference

## Imports

```typescript
import { MaestroProcesses, ProcessInstances, ProcessIncidents } from '@uipath/uipath-typescript/maestro-processes';
import { Cases, CaseInstances } from '@uipath/uipath-typescript/cases';
```

## Scopes

- All Maestro operations: `PIMS`
- ProcessInstances.getBpmn: also requires `OR.Execution.Read`
- CaseInstances.getActionTasks: also requires `OR.Tasks` or `OR.Tasks.Read`

## Types to Import

```typescript
// Maestro Processes
import type {
  MaestroProcessGetAllResponse,
  RawMaestroProcessGetAllResponse,
  ProcessMethods,
} from '@uipath/uipath-typescript/maestro-processes';

// Process Instances
import type {
  ProcessInstanceGetResponse,
  RawProcessInstanceGetResponse,
  ProcessInstanceMethods,
  ProcessInstanceGetAllWithPaginationOptions,
  ProcessInstanceGetAllOptions,
  ProcessInstanceOperationOptions,
  ProcessInstanceOperationResponse,
  ProcessInstanceExecutionHistoryResponse,
  BpmnXmlString,
  ProcessInstanceGetVariablesResponse,
  ProcessInstanceGetVariablesOptions,
  ProcessInstanceRun,
} from '@uipath/uipath-typescript/maestro-processes';

// Process Incidents
import type {
  ProcessIncidentGetResponse,
  ProcessIncidentGetAllResponse,
} from '@uipath/uipath-typescript/maestro-processes';

// Cases
import type {
  CaseGetAllResponse,
} from '@uipath/uipath-typescript/cases';

// Case Instances
import type {
  CaseInstanceGetResponse,
  RawCaseInstanceGetResponse,
  CaseInstanceMethods,
  CaseInstanceGetAllWithPaginationOptions,
  CaseInstanceGetAllOptions,
  CaseInstanceOperationOptions,
  CaseInstanceOperationResponse,
  CaseInstanceReopenOptions,
  CaseGetStageResponse,
  CaseInstanceExecutionHistoryResponse,
  StageTask,
} from '@uipath/uipath-typescript/cases';
```

## Enums

```typescript
import {
  ProcessIncidentStatus,    // Open, Closed
  ProcessIncidentType,      // System, User, Deployment
  ProcessIncidentSeverity,  // Error, Warning
  DebugMode,                // None, Default, StepByStep, SingleStep
} from '@uipath/uipath-typescript/maestro-processes';

import {
  StageTaskType,               // external-agent, rpa, process, agent, action, api-workflow
  EscalationRecipientScope,    // user, usergroup
  EscalationActionType,        // notification
  EscalationTriggerType,       // sla-breached, at-risk
  SLADurationUnit,             // h, d, w, m
} from '@uipath/uipath-typescript/cases';
```

## MaestroProcesses Service

### getAll()

Returns `Promise<MaestroProcessGetAllResponse[]>`. Each process has: `processKey`, `packageId`, `name`, `folderKey`, `folderName`, `packageVersions`, `versionCount`, plus instance count fields (`runningCount`, `faultedCount`, `completedCount`, `pausedCount`, `cancelledCount`, `pendingCount`, `retryingCount`, `resumingCount`, `pausingCount`, `cancelingCount`). Each process has an attached `getIncidents()` method.

**NOTE:** Maestro responses include `folderKey` (GUID string) but NOT `folderId` (number). If you need to call an Orchestrator method that requires `folderId` (e.g., `Processes.start()`), you must bridge using `Processes.getAll()` — see "Bridging folderKey ↔ folderId" in [orchestrator.md](orchestrator.md). **NEVER use `parseInt(folderKey)`** — it returns `NaN`.

**CRITICAL — `name` is NOT `processKey`:** The human-readable process name (e.g., `"Loan.Origination.and.Review"`) is the `name` field. The `processKey` is a separate internal identifier (e.g., `"a1b2c3d4-..."`). When the user provides a process name, you MUST first call `MaestroProcesses.getAll()`, find the process where `name` matches, then extract its `processKey` and `folderKey` to use in subsequent calls like `ProcessInstances.getAll({ processKey })`. **NEVER use the process name as the processKey.**

```typescript
const maestroProcesses = new MaestroProcesses(sdk);
const allProcesses = await maestroProcesses.getAll();
const target = allProcesses.find(p => p.name === 'Loan.Origination.and.Review');
if (!target) throw new Error('Process not found');
// Now use target.processKey and target.folderKey for instance queries
const instances = await processInstances.getAll({ processKey: target.processKey, pageSize: 20 });
```

### getIncidents(processKey: string, folderKey: string)

Returns `Promise<ProcessIncidentGetResponse[]>`. Each incident has: `instanceId`, `elementId`, `folderKey`, `processKey`, `incidentId`, `incidentStatus`, `incidentType`, `errorCode`, `errorMessage`, `errorTime`, `errorDetails`, `debugMode`, `incidentSeverity`, `incidentElementActivityType`, `incidentElementActivityName`.

## Process-Attached Methods (ProcessMethods)

Returned by `getAll()` on each `MaestroProcessGetAllResponse`:

- `process.getIncidents()` -> `Promise<ProcessIncidentGetResponse[]>`

## ProcessIncidents Service

Standalone service exported from `@uipath/uipath-typescript/maestro-processes` (same subpath as `MaestroProcesses` and `ProcessInstances`). Use it when you need incidents across **all folders** without first resolving a specific `processKey` or `instanceId`.

### getAll()

Returns `Promise<ProcessIncidentGetAllResponse[]>`. Each summary has aggregated fields like `processKey`, `errorMessage`, `count`, `firstOccuranceTime`.

```typescript
import { ProcessIncidents } from '@uipath/uipath-typescript/maestro-processes';

const processIncidents = new ProcessIncidents(sdk);
const incidents = await processIncidents.getAll();
for (const incident of incidents) {
  console.log(`${incident.processKey}: ${incident.errorMessage} (count: ${incident.count})`);
}
```

### When to use which incident accessor

| Scope | Use |
|---|---|
| All incidents across all folders (summary rollup) | `new ProcessIncidents(sdk).getAll()` — returns `ProcessIncidentGetAllResponse[]` |
| All incidents for one process | `MaestroProcesses.getIncidents(processKey, folderKey)` or `process.getIncidents()` — returns `ProcessIncidentGetResponse[]` |
| Incidents on a single instance | `ProcessInstances.getIncidents(instanceId, folderKey)` or `instance.getIncidents()` — returns `ProcessIncidentGetResponse[]` |

Note that `ProcessIncidentGetAllResponse` (summary) and `ProcessIncidentGetResponse` (per-incident detail) are different shapes.

## ProcessInstanceGetResponse Fields

`instanceId: string`, `packageKey: string`, `packageId: string`, `packageVersion: string`, `latestRunId: string`, `latestRunStatus: string`, `processKey: string`, `folderKey: string`, `userId: number`, `instanceDisplayName: string`, `startedByUser: string`, `source: string`, `creatorUserKey: string`, `startedTime: string`, `completedTime: string | null`, `instanceRuns: ProcessInstanceRun[]`. Plus all `ProcessInstanceMethods`.

## ProcessInstances Service

### getAll(options?: ProcessInstanceGetAllWithPaginationOptions)

Returns `NonPaginatedResponse<ProcessInstanceGetResponse>` or `PaginatedResponse<ProcessInstanceGetResponse>`. Token-based pagination. Filter options: `processKey`, `packageId`, `packageVersion`, `errorCode`.

### getById(id: string, folderKey: string)

Returns `Promise<ProcessInstanceGetResponse>` with attached methods.

### cancel(instanceId: string, folderKey: string, options?: ProcessInstanceOperationOptions)

Returns `Promise<OperationResponse<ProcessInstanceOperationResponse>>`. Options: `{ comment?: string }`.

### pause(instanceId: string, folderKey: string, options?: ProcessInstanceOperationOptions)

Same signature and return type as cancel.

### resume(instanceId: string, folderKey: string, options?: ProcessInstanceOperationOptions)

Same signature and return type as cancel.

### getExecutionHistory(instanceId: string)

Returns `Promise<ProcessInstanceExecutionHistoryResponse[]>`. Each span has: `id`, `traceId`, `parentId`, `name`, `startedTime`, `endTime`, `attributes`, `createdTime`, `updatedTime?`, `expiredTime`.

### getBpmn(instanceId: string, folderKey: string)

Returns `Promise<BpmnXmlString>` (a string of BPMN XML).

### getVariables(instanceId: string, folderKey: string, options?: ProcessInstanceGetVariablesOptions)

Returns `Promise<ProcessInstanceGetVariablesResponse>` with `{ elements, globalVariables, instanceId, parentElementId }`. Options: `{ parentElementId?: string }`.

**Response structure:**

- `globalVariables: GlobalVariableMetaData[]` — Named variables with types. Each has:
  - `id: string` — unique identifier
  - `name: string` — human-readable variable name (e.g., `"loanAmount"`, `"applicantName"`)
  - `type: string` — value type (`"integer"`, `"string"`, `"boolean"`, or custom types)
  - `value: any` — the current value (can be primitive, object, or array)
  - `source: string` — name of the BPMN element that set/owns this variable
  - `elementId: string` — BPMN element ID
- `elements: ElementMetaData[]` — Per-element execution data (activity steps). Each has:
  - `elementId: string` — BPMN element ID (e.g., `"Activity_XYRXSH"`)
  - `elementRunId: string` — unique run identifier
  - `isMarker: boolean` — whether this is a marker element
  - `inputs: Record<string, any>` — input arguments passed to the element (can be deeply nested objects)
  - `inputDefinitions: Record<string, any>` — schema/definitions for inputs
  - `outputs: Record<string, any>` — output values produced by the element (can be deeply nested objects)

**UI rendering — MANDATORY:** See [../patterns.md](../patterns.md) section "Rendering Process Instance Data" for how to display variables and element data properly. **NEVER dump raw JSON** — always parse and render structured UI.

### getIncidents(instanceId: string, folderKey: string)

Returns `Promise<ProcessIncidentGetResponse[]>`.

## ProcessInstance-Attached Methods (ProcessInstanceMethods)

Returned by `getAll()` and `getById()` on each `ProcessInstanceGetResponse`:

- `instance.cancel(options?)` -> `Promise<OperationResponse<ProcessInstanceOperationResponse>>`
- `instance.pause(options?)` -> `Promise<OperationResponse<ProcessInstanceOperationResponse>>`
- `instance.resume(options?)` -> `Promise<OperationResponse<ProcessInstanceOperationResponse>>`
- `instance.getIncidents()` -> `Promise<ProcessIncidentGetResponse[]>`
- `instance.getExecutionHistory()` -> `Promise<ProcessInstanceExecutionHistoryResponse[]>`
- `instance.getBpmn()` -> `Promise<BpmnXmlString>`
- `instance.getVariables(options?)` -> `Promise<ProcessInstanceGetVariablesResponse>`

## Cases Service

### getAll()

Returns `Promise<CaseGetAllResponse[]>`. Each case has: `processKey`, `packageId`, `name`, `folderKey`, `folderName`, `packageVersions`, `versionCount`, plus instance count fields (same as MaestroProcesses).

## CaseInstanceGetResponse Fields

`instanceId: string`, `packageKey: string`, `packageId: string`, `packageVersion: string`, `latestRunId: string`, `latestRunStatus: string`, `processKey: string`, `folderKey: string`, `userId: number`, `instanceDisplayName: string`, `startedByUser: string`, `source: string`, `creatorUserKey: string`, `startedTime: string`, `completedTime: string`, `instanceRuns: CaseInstanceRun[]`, `caseAppConfig?: CaseAppConfig`, `caseType?: string`, `caseTitle?: string`. Plus all `CaseInstanceMethods`.

## CaseInstanceExecutionHistoryResponse Fields

`creationUserKey: string | null`, `folderKey: string`, `instanceDisplayName: string`, `instanceId: string`, `packageId: string`, `packageKey: string`, `packageVersion: string`, `processKey: string`, `source: string`, `status: string`, `startedTime: string`, `completedTime: string | null`, `elementExecutions: ElementExecutionMetadata[]`.

## CaseGetStageResponse Fields

`id: string`, `name: string`, `sla?: StageSLA`, `status: string`, `tasks: StageTask[][]`.

## StageTask Fields

`id: string`, `name: string`, `completedTime: string`, `startedTime: string`, `status: string`, `type: StageTaskType`.

## CaseInstances Service

### getAll(options?: CaseInstanceGetAllWithPaginationOptions)

Returns `NonPaginatedResponse<CaseInstanceGetResponse>` or `PaginatedResponse<CaseInstanceGetResponse>`. Filter options: `processKey`, `packageId`, `packageVersion`, `errorCode`.

### getById(instanceId: string, folderKey: string)

Returns `Promise<CaseInstanceGetResponse>` with attached methods.

### close(instanceId: string, folderKey: string, options?: CaseInstanceOperationOptions)

Returns `Promise<OperationResponse<CaseInstanceOperationResponse>>`. Options: `{ comment?: string }`.

### pause / resume

Same signature pattern as close.

### reopen(instanceId: string, folderKey: string, options: CaseInstanceReopenOptions)

Options: `{ stageId: string, comment?: string }`. The `stageId` is required - get it from `getStages()`.

### getStages(caseInstanceId: string, folderKey: string)

Returns `Promise<CaseGetStageResponse[]>`. Each stage has: `id`, `name`, `sla`, `status`, `tasks: StageTask[][]`.

### getExecutionHistory(instanceId: string, folderKey: string)

Returns `Promise<CaseInstanceExecutionHistoryResponse>` with `{ elementExecutions, instanceId, status, startedTime, completedTime, ... }`.

### getActionTasks(caseInstanceId: string, options?: TaskGetAllOptions)

Returns `NonPaginatedResponse<TaskGetResponse>` or `PaginatedResponse<TaskGetResponse>`. Requires `OR.Tasks` scope.

## CaseInstance-Attached Methods (CaseInstanceMethods)

- `instance.close(options?)` -> `Promise<OperationResponse<CaseInstanceOperationResponse>>`
- `instance.pause(options?)` -> `Promise<OperationResponse<CaseInstanceOperationResponse>>`
- `instance.resume(options?)` -> `Promise<OperationResponse<CaseInstanceOperationResponse>>`
- `instance.reopen(options)` -> `Promise<OperationResponse<CaseInstanceOperationResponse>>`
- `instance.getExecutionHistory()` -> `Promise<CaseInstanceExecutionHistoryResponse>`
- `instance.getStages()` -> `Promise<CaseGetStageResponse[]>`
- `instance.getActionTasks(options?)` -> pagination-aware, returns tasks

## Usage Example

```typescript
import { useMemo, useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { ProcessInstances } from '@uipath/uipath-typescript/maestro-processes';
import type { ProcessInstanceGetResponse } from '@uipath/uipath-typescript/maestro-processes';

function InstanceDashboard() {
  const { sdk } = useAuth();
  const processInstances = useMemo(() => new ProcessInstances(sdk), [sdk]);
  const [instances, setInstances] = useState<ProcessInstanceGetResponse[]>([]);

  useEffect(() => {
    const load = async () => {
      const result = await processInstances.getAll({ pageSize: 20 });
      setInstances(result.items);
    };
    load();
  }, [processInstances]);

  const handleCancel = async (instance: ProcessInstanceGetResponse) => {
    const result = await instance.cancel({ comment: 'Cancelled from dashboard' });
    if (result.success) {
      // Refresh list
    }
  };

  return (
    <div>
      {instances.map(inst => (
        <div key={inst.instanceId}>
          <span>{inst.instanceDisplayName} - {inst.latestRunStatus}</span>
          <button onClick={() => handleCancel(inst)}>Cancel</button>
        </div>
      ))}
    </div>
  );
}
```
