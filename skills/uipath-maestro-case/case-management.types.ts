/**
 * TypeScript types for the Case Management JSON Schema (V23).
 *
 * V23 keeps the V20 flat top-level shape: no `root` wrapper, case-specific
 * fields under `metadata`, and a semver version string (`"23.0.0"`). It shares
 * V20's node/edge/task composition; the version bump tracks intermediate
 * schema revisions (V21–V23) that did not change the structural layout.
 *
 * V23 composition: top=V23 (flat), nodes=V13, edges=V12, rules=V12, tasks=V13.
 *
 * Hand-flattened from `src/case-mgmt-zod` (the zod source of truth). Regenerate
 * from there when the schemas change.
 */

// ─── UiPath Primitives ────────────────────────────────────────────────────────

export interface UiPathVariable {
    name: string;
    type: string;
    id?: string;
    canonicalId?: string;
    camelizedId?: string;
    displayName?: string;
    subType?: string;
    elementId?: string;
    default?: unknown;
    value?: unknown;
    var?: string;
    source?: unknown;
    target?: string;
    custom?: boolean;
    required?: boolean;
    internal?: boolean;
    body?: unknown;
    _jsonSchema?: unknown;
}

export interface UiPathBinding {
    id: string;
    name: string;
    type: string;
    resource: string;
    resourceKey: string;
    propertyAttribute: string;
    resourceSubType?: string;
    default?: string;
}

export interface UiPathAllVariables {
    inputs?: UiPathVariable[];
    outputs?: UiPathVariable[];
    inputOutputs?: UiPathVariable[];
}

// ─── SLA & Escalation ────────────────────────────────────────────────────────

export interface EscalationRuleRecipient {
    scope: "User" | "UserGroup";
    target: string;
    value: string;
}

export interface EscalationRule {
    id: string;
    displayName?: string;
    action?: {
        type: "notification";
        recipients: EscalationRuleRecipient[];
    };
    triggerInfo?: {
        type: "at-risk" | "sla-breached";
        atRiskPercentage?: number;
    };
}

export interface SlaSchema {
    count?: number;
    unit?: "min" | "h" | "d" | "w" | "m";
    escalationRule?: EscalationRule[];
}

export interface SlaRuleEntry {
    expression: string;
    count?: number;
    unit?: "min" | "h" | "d" | "w" | "m";
    escalationRule?: EscalationRule[];
}

// ─── Rules (V12: DNF — OR of AND-clauses) ───────────────────────────────────
// V12 rules exclude deprecated condition, stage-complete, and timer rules.

export interface WaitForConnectorRule {
    rule: "wait-for-connector";
    id?: string;
    conditionExpression?: string;
    uipath?: {
        serviceType?: string;
        context?: UiPathVariable[];
        inputs?: UiPathVariable[];
        outputs?: UiPathVariable[];
        bindings?: UiPathBinding[];
    };
}

export interface CaseEnteredRule {
    rule: "case-entered";
    id?: string;
    conditionExpression?: string;
}

export interface SelectedStageCompletedRule {
    rule: "selected-stage-completed";
    id?: string;
    selectedStageId?: string;
    conditionExpression?: string;
}

export interface SelectedStageExitedRule {
    rule: "selected-stage-exited";
    id?: string;
    selectedStageId?: string;
    conditionExpression?: string;
}

export interface SelectedTasksCompletedRule {
    rule: "selected-tasks-completed";
    id?: string;
    selectedTasksIds?: string[];
    conditionExpression?: string;
}

export interface CurrentStageEnteredRule {
    rule: "current-stage-entered";
    id?: string;
    conditionExpression?: string;
}

export interface AdhocRule {
    rule: "adhoc";
    id?: string;
    conditionExpression?: string;
}

export interface RequiredStagesCompletedRule {
    rule: "required-stages-completed";
    id?: string;
    conditionExpression?: string;
}

export interface RequiredTasksCompletedRule {
    rule: "required-tasks-completed";
    id?: string;
    conditionExpression?: string;
}

export interface UserSelectedStageRule {
    rule: "user-selected-stage";
    id?: string;
    conditionExpression?: string;
}

export interface TaskRunsSequentiallyRule {
    rule: "runs-sequentially";
    id?: string;
    conditionExpression?: string;
}

export type Rule =
    | WaitForConnectorRule
    | CaseEnteredRule
    | SelectedStageCompletedRule
    | SelectedStageExitedRule
    | SelectedTasksCompletedRule
    | CurrentStageEnteredRule
    | AdhocRule
    | RequiredStagesCompletedRule
    | RequiredTasksCompletedRule
    | UserSelectedStageRule
    | TaskRunsSequentiallyRule;

/** Rules in Disjunctive Normal Form: outer array = OR groups, inner = AND conditions */
export type Rules = Rule[][];

// ─── Deprecated Rules ────────────────────────────────────────────────────────
// These rule types are excluded from V12 rules but still referenced by
// the deprecated TaskCondition type (which uses the legacy rules schema).

/** @deprecated Removed in V12 rules */
export interface ConditionRule {
    rule: "condition";
    id?: string;
    conditionExpression?: string;
}

/** @deprecated Removed in V12 rules */
export interface StageCompleteRule {
    rule: "stage-complete";
    id?: string;
}

/** @deprecated Removed in V12 rules */
export interface TimerRule {
    rule: "timer";
    id?: string;
    timer?: {
        timerType: "timeCycle" | "timeDate" | "timeDuration";
        timeDuration?: string;
        timeDate?: string;
        repeat?: string;
        every?: string;
        at?: string;
        timeCycle?: string;
    };
}

/** @deprecated Union including legacy rule types; used only by deprecated TaskCondition */
export type LegacyRule = Rule | ConditionRule | StageCompleteRule | TimerRule;

/** @deprecated Legacy rules in DNF form; used only by deprecated TaskCondition */
export type LegacyRules = LegacyRule[][];

// ─── Tasks ───────────────────────────────────────────────────────────────────

/** @deprecated Use TaskEntryCondition instead */
export interface TaskCondition {
    id?: string;
    displayName?: string;
    actionType: "skip" | "run";
    rules: LegacyRules;
}

export interface TaskEntryCondition {
    id?: string;
    displayName?: string;
    rules?: Rules;
}

interface BaseTask {
    id?: string;
    elementId?: string;
    /** @deprecated Use shouldRunOnlyOnce instead */
    shouldRunOnReEntry?: boolean;
    shouldRunOnlyOnce?: boolean;
    displayName?: string;
    skipCondition?: string;
    /** @deprecated Use entryConditions instead */
    conditions?: TaskCondition[];
    entryConditions?: TaskEntryCondition[];
    isRequired?: boolean;
    description?: string;
}

interface ProcessTaskData {
    name?: string;
    folderPath?: string;
    inputs?: UiPathVariable[];
    outputs?: UiPathVariable[];
    context?: UiPathVariable[];
}

export interface ActionTaskAssignee extends ProcessTaskData {
    Type: 0 | 1 | 2 | 3;
    Value: string;
    originalEntry?: unknown;
}

export interface ProcessTask extends BaseTask {
    type: "process";
    data?: ProcessTaskData;
}

export interface ActionTask extends BaseTask {
    type: "action";
    data?: ProcessTaskData & {
        taskTitle?: string;
        labels?: string;
        priority?: string;
        actionCatalogName?: string;
        recipient?: string | ActionTaskAssignee;
        startCriteria?: string | number;
        endCriteria?: string | number;
        timer?: string | number;
        actionDataOutcome?: string | number;
        actionData?: string;
    };
}

export interface AgentTask extends BaseTask {
    type: "agent";
    data?: ProcessTaskData;
}

export interface ApiWorkflowTask extends BaseTask {
    type: "api-workflow";
    data?: ProcessTaskData;
}

export interface RpaTask extends BaseTask {
    type: "rpa";
    data?: ProcessTaskData;
}

export interface ExternalAgentTask extends BaseTask {
    type: "external-agent";
    data?: ProcessTaskData & {
        serviceType?: string;
        bindings?: UiPathBinding[];
    };
}

export interface ExternalWorkflowTask extends BaseTask {
    type: "external-workflow";
    data?: ProcessTaskData & {
        serviceType?: string;
        bindings?: UiPathBinding[];
    };
}

export interface DocumentExtractionTask extends BaseTask {
    type: "document-extraction";
    data?: ProcessTaskData & {
        serviceType?: string;
    };
}

export interface WaitForTimerTask extends BaseTask {
    type: "wait-for-timer";
    data?: {
        timer?: "timeCycle" | "timeDate" | "timeDuration";
        timeDuration?: string;
        timeDate?: string;
        timeCycle?: string;
        repeat?: string;
        every?: string;
        at?: string;
    };
}

export interface WaitForConnectorTask extends BaseTask {
    type: "wait-for-connector";
    data?: ProcessTaskData & {
        serviceType?: string;
        bindings?: UiPathBinding[];
    };
}

export interface ExecuteConnectorActivityTask extends BaseTask {
    type: "execute-connector-activity";
    data?: ProcessTaskData & {
        serviceType?: string;
        bindings?: UiPathBinding[];
    };
}

export interface CaseManagementSubTask extends BaseTask {
    type: "case-management";
    data?: ProcessTaskData;
}

export interface FlowProcessTask extends BaseTask {
    type: "flow-process";
    data?: ProcessTaskData;
}

export type Task =
    | ProcessTask
    | ActionTask
    | AgentTask
    | ApiWorkflowTask
    | RpaTask
    | ExternalAgentTask
    | ExternalWorkflowTask
    | DocumentExtractionTask
    | WaitForTimerTask
    | WaitForConnectorTask
    | ExecuteConnectorActivityTask
    | CaseManagementSubTask
    | FlowProcessTask;

// ─── Nodes ────────────────────────────────────────────────────────────────────

interface BaseNode {
    id: string;
    position?: unknown;
    style?: unknown;
    measured?: unknown;
    dragging?: boolean;
    selected?: boolean;
    zIndex?: number;
    width?: number;
    height?: number;
    extent?: string;
}

export interface TriggerNode extends BaseNode {
    type: "case-management:Trigger";
    data: {
        label?: string;
        parentElement?: unknown;
        description?: string;
        uipath?: {
            serviceType?:
                | "None"
                | "Intsvc.EventTrigger"
                | "Intsvc.TimerTrigger"
                | null;
            context?: UiPathVariable[];
            inputs?: UiPathVariable[];
            outputs?: UiPathVariable[];
            bindings?: UiPathBinding[];
            timerType?: string | null;
            timeCycle?: string;
        };
    };
}

export interface EntryCondition {
    id?: string;
    displayName?: string;
    rules?: Rules;
    isInterrupting?: boolean;
}

export interface ExitCondition {
    id?: string;
    displayName?: string;
    rules?: Rules;
    type?: "exit-only" | "wait-for-user" | "return-to-origin";
    exitToStageId?: string;
    marksStageComplete?: boolean;
}

export interface StageNodeData {
    label?: string;
    parentElement?: unknown;
    isInvalidDropTarget?: boolean;
    isPendingParent?: boolean;
    instanceIdPrefix?: string;
    /** 2D array: outer = parallel lanes, inner = sequential tasks per lane */
    tasks?: Task[][];
    sla?: SlaSchema;
    entryConditions?: EntryCondition[];
    exitConditions?: ExitCondition[];
    isRequired?: boolean;
    description?: string;
}

export interface StageNode extends BaseNode {
    type: "case-management:Stage";
    data: StageNodeData;
}

export interface ExceptionStageNodeData {
    label?: string;
    parentElement?: unknown;
    instanceIdPrefix?: string;
    /** 2D array: outer = parallel lanes, inner = sequential tasks per lane */
    tasks?: Task[][];
    sla?: SlaSchema;
    entryConditions?: EntryCondition[];
    exitConditions?: ExitCondition[];
    slaRules?: SlaRuleEntry[];
    isRequired?: boolean;
    description?: string;
}

export interface ExceptionStageNode extends BaseNode {
    type: "case-management:ExceptionStage";
    data: ExceptionStageNodeData;
}

export interface StickyNoteNode extends BaseNode {
    type: "case-management:StickyNote";
    data: {
        label?: string;
        parentElement?: unknown;
        color?: string;
        content?: string;
    };
}

export type CaseManagementNode =
    | TriggerNode
    | StageNode
    | ExceptionStageNode
    | StickyNoteNode;

// ─── Edges ───────────────────────────────────────────────────────────────────

interface BaseEdge {
    id: string;
    source: string;
    target: string;
    sourceHandle?: string;
    targetHandle?: string;
    style?: unknown;
    dragging?: boolean;
    selected?: boolean;
    zIndex?: number;
    extent?: string;
}

interface EdgeData {
    label?: string;
    parentElement?: unknown;
    waypoints?: unknown[];
}

export interface TriggerEdge extends BaseEdge {
    type: "case-management:TriggerEdge";
    data: EdgeData;
}

export interface CaseManagementEdge extends BaseEdge {
    type: "case-management:Edge";
    data: EdgeData & { isReEntry?: boolean | null };
}

export type CaseManagementEdgeType = TriggerEdge | CaseManagementEdge;

// ─── Case App Config ──────────────────────────────────────────────────────────

export interface CaseAppConfigSection {
    id: string;
    title: string;
    details: string;
    error?: string;
    titleError?: string;
}

export interface CaseAppConfig {
    caseSummary: string;
    sections: CaseAppConfigSection[];
}

// ─── Case Manager ─────────────────────────────────────────────────────────────

export interface CaseManagerGlobalEvent {
    entryPointId?: string;
    /** 2D array: outer = parallel lanes, inner = sequential tasks per lane */
    tasks?: Task[][];
}

export interface CaseManager {
    id: string;
    enabled: boolean;
    globalEvents?: CaseManagerGlobalEvent[];
    /** Array of task grids (each entry is the 2D lane/sequence layout) */
    tasks?: Task[][][];
}

// ─── Metadata ─────────────────────────────────────────────────────────────────

/** Renamed from V19 `caseExitConditions`. Same shape. */
export interface CaseExitRule {
    id?: string;
    displayName?: string;
    rules?: Rules;
    marksCaseComplete?: boolean;
}

/**
 * Case-specific fields that lived on `root` in V19 and earlier. From V20 on they
 * live under `metadata` so the top level matches the generic flow-workbench
 * workflow file format.
 */
export interface CaseManagementMetadata {
    caseIdentifier?: string;
    caseIdentifierType?: "constant" | "external";
    caseAppEnabled?: boolean;
    allowAdhocOptionalStageTasks?: boolean;
    publishVersion?: number;
    caseExecutionIncludesDebugVariables?: boolean;
    caseExecutionUsesSyncCaseTasks?: boolean;
    caseDirectlyPassTaskOutputs?: boolean;
    caseBpmnUseNewGlobalVariables?: boolean;
    caseUnifiedSchemaEnabled?: boolean;
    caseAppConfig?: CaseAppConfig;
    /**
     * Node-connector object set up on the root when a "wait for human"
     * select-next-stage connector is configured. Preserved as-is across the
     * roundtrip — there is no zod schema for its shape.
     */
    waitForHumanSelectNextStageDFConnector?: unknown;
    slaRules?: SlaRuleEntry[];
    caseExitRules?: CaseExitRule[];
    caseManagerAgentProjectId?: string;
    intsvcActivityConfig?: string;
    caseManagerData?: CaseManager;
}

// ─── Top-level Schema (V23) ──────────────────────────────────────────────────
//
// V23 carries forward the V20 flat shape: the case identifier, name, version
// and bindings/variables live at the top level, and the remaining case-specific
// fields live under `metadata`.

export interface CaseManagementJsonSchema {
    id: string;
    /** Semver-style version string. V23 is exactly "23.0.0". */
    version: string;
    name: string;
    description?: string;
    metadata?: CaseManagementMetadata;
    bindings?: UiPathBinding[];
    variables?: UiPathAllVariables;
    nodes: CaseManagementNode[];
    edges: CaseManagementEdgeType[];
}
