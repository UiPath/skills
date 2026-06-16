#!/usr/bin/env node
// Offline semantic validator for UiPath Maestro BPMN XML.
//
// Parses the BPMN with bpmn-moddle using the UiPath extension descriptor
// (same getModdle() pattern as PO.Frontend), then runs the canvas validation
// rule engine ported from PO.Frontend/src/services/validation/bpmn/rules/.
// Each rule below cites the frontend rule it is ported from. Prints `VALID`
// and exits 0 when no blocking errors are found; otherwise lists every error
// and exits non-zero. WARNING-severity findings are printed but do not gate.
//
// Usage: node validate-bpmn.mjs <bpmn-file> [resources]
//   resources: comma-separated release names, or a numeric folder ID, for the
//              optional solution-resource health check (requires uip CLI auth).
import BpmnModdle from "bpmn-moddle";
import descriptor from "./uipath-moddle.v1.json" with { type: "json" };
import { readFileSync, existsSync } from "fs";
import { execFileSync } from "child_process";

const SEVERITY = { ERROR: "ERROR", WARNING: "WARNING" };

// Built-in namespaces that look like variable references but are NOT user
// variables: loop iterators (`iterator.`), node metadata (`metadata.`), and the
// boundary-error context (`error.` / `vars.error`). The `vars.X` regex below
// only matches the `error` case (iterator./metadata. do not start with `vars.`),
// so it is listed here and skipped during variable-existence checks.
const BUILTIN_NON_VARIABLE_REFS = new Set(["error"]);

// --- IS connector types that must use the connector framework pattern ---
const IS_CONNECTOR_TYPES_LIST = [
  "Intsvc.ActivityExecution",
  "Intsvc.HttpExecution",
  "Intsvc.UnifiedHttpRequest",
  "Intsvc.WaitForEvent",
  "Intsvc.EventTrigger",
  "Intsvc.AsyncExecution",
  "Intsvc.SyncAgentExecution",
  "Intsvc.AsyncAgentExecution",
  "Intsvc.SyncWorkflowExecution",
  "Intsvc.AsyncWorkflowExecution",
];

// Service types that require a bound resource (release/process/agent/queue).
// Ported from PO.Frontend MissingResourceRule.ts SERVICE_TYPES_REQUIRING_RESOURCE.
// Node $types treated as activities / events for the FakeJoin rule.
const ACTIVITY_TYPES = new Set([
  "bpmn:Task",
  "bpmn:ServiceTask",
  "bpmn:UserTask",
  "bpmn:ScriptTask",
  "bpmn:SendTask",
  "bpmn:ReceiveTask",
  "bpmn:BusinessRuleTask",
  "bpmn:ManualTask",
  "bpmn:CallActivity",
  "bpmn:SubProcess",
]);
// Events that count as a FakeJoin target. EndEvent is intentionally excluded:
// converging multiple paths onto a single end event is idiomatic, valid BPMN
// (the frontend rule runs on canvas node types where a converging end is
// modeled as a gateway join, so it never sees a multi-incoming end event).
const EVENT_TYPES = new Set([
  "bpmn:IntermediateCatchEvent",
  "bpmn:IntermediateThrowEvent",
]);

const SERVICE_TYPES_REQUIRING_RESOURCE = new Set([
  "Orchestrator.StartAgentJob",
  "Orchestrator.StartJob",
  "Orchestrator.CreateQueueItem",
  "Orchestrator.CreateAndWaitForQueueItem",
  "Orchestrator.ExecuteApiWorkflow",
  "Actions.HITL",
  "UiPath.HumanInLoopTask",
  "Orchestrator.StartAgenticProcess",
  "Orchestrator.StartAgenticProcessAsync",
  "Orchestrator.StartCaseMgmtProcess",
  "Orchestrator.StartCaseMgmtProcessAsync",
]);

// --- uip CLI resolution (cached) ---
let _uipBinCache = undefined;
function resolveUipBin() {
  if (_uipBinCache !== undefined) return _uipBinCache;
  const homedir = process.env.HOME || process.env.USERPROFILE || "";
  const candidates = [
    "uip",
    `${homedir}/.bun/bin/uip`,
    `${homedir}/.local/bin/uip`,
    "/usr/local/bin/uip",
  ];
  for (const p of candidates) {
    try {
      if (p.startsWith("/") || p.startsWith(homedir)) {
        if (!existsSync(p)) continue;
      }
      execFileSync(p, ["--version"], { encoding: "utf8", timeout: 5000, stdio: "pipe" });
      _uipBinCache = p;
      return p;
    } catch {}
  }
  _uipBinCache = null;
  return null;
}

const file = process.argv[2];
const resourceArg = process.argv[3];

if (!file) {
  console.error("Usage: node validate-bpmn.mjs <bpmn-file> [resources]");
  console.error("  resources: comma-separated release names for the solution-resource health check");
  console.error('    e.g. "Hello world JS,My Agent,My RPA Process"');
  console.error("  Or pass a numeric folder ID to auto-fetch via uip CLI (requires auth).");
  process.exit(1);
}

const xml = readFileSync(file, "utf8");
const moddle = new BpmnModdle({ uipath: descriptor });

// --- Step 1: Schema validation (getModdle + fromXML, PO.Frontend pattern) ---
let result;
try {
  result = await moddle.fromXML(xml);
} catch (e) {
  console.error("SCHEMA ERROR:", e.message);
  process.exit(1);
}

if (result.warnings?.length) {
  console.log("Schema warnings:", JSON.stringify(result.warnings, null, 2));
}

const definitions = result.rootElement;
const errors = [];

// --- Run ported semantic rules ---
errors.push(...validateConditionalFlows(definitions)); // ConditionalFlowRule.ts
errors.push(...validateVariableReferences(definitions)); // variable-reference checks
errors.push(...validateMissingRootVariables(definitions)); // MissingRootVariableRule.ts
errors.push(...validateFakeJoins(definitions)); // FakeJoinRule.ts
errors.push(...validateSuperfluousGateways(definitions)); // SuperfluousGatewayRule.ts
errors.push(...validateErrorEndEvents(definitions)); // ErrorEndEventRule.ts
errors.push(...validateErrorBoundaryEvents(definitions)); // ErrorBoundaryEventRule.ts
errors.push(...validateTimerDurations(definitions)); // TimerDurationRule.ts
errors.push(...validateSingleBlankStartEvent(definitions)); // SingleBlankStartEventRule.ts
errors.push(...validateMissingResource(definitions)); // MissingResourceRule.ts

// --- Maestro runtime / authoring extras (not 1:1 frontend canvas rules) ---
errors.push(...validateIsConnectorFramework(definitions));
errors.push(...validateConfigCompleteness(definitions));
errors.push(...(await validateConnectionHealth(definitions)));

// Optional: solution-resource health check (replicates SolutionResourceValidationUtils.ts)
if (resourceArg) {
  let releaseNames;
  if (/^\d+$/.test(resourceArg)) {
    try {
      releaseNames = fetchReleaseNames(resourceArg);
    } catch (e) {
      errors.push({
        code: "HEALTH_CHECK_FAILED",
        severity: SEVERITY.ERROR,
        message: `Cannot fetch releases for folder ${resourceArg}: ${e.message}`,
        description: "Pass release names directly as a comma-separated string instead of folder ID.",
      });
    }
  } else {
    releaseNames = resourceArg.split(",").map((s) => s.trim());
  }
  if (releaseNames) errors.push(...validateSolutionResources(definitions, releaseNames));
}

// --- Report ---
const blocking = errors.filter((e) => e.severity !== SEVERITY.WARNING);
const warnings = errors.filter((e) => e.severity === SEVERITY.WARNING);

if (warnings.length) {
  console.error("WARNINGS:");
  for (const w of warnings) {
    console.error(`  [${w.code}] ${w.message}`);
    console.error(`    ${w.description}`);
  }
}

if (blocking.length) {
  console.error("VALIDATION ERRORS:");
  for (const err of blocking) {
    console.error(`  [${err.code}] ${err.message}`);
    console.error(`    ${err.description}`);
  }
  process.exit(1);
} else {
  console.log("VALID");
}

// =====================================================================
// Tree helpers
// =====================================================================

function getProcesses(defs) {
  return (defs.rootElements || []).filter((el) => el.$type === "bpmn:Process");
}

// All flow elements across a process and nested (sub)processes, flattened.
function getAllFlowElements(process) {
  const elements = [];
  function collect(container) {
    for (const el of container.flowElements || []) {
      elements.push(el);
      if (el.flowElements) collect(el);
    }
  }
  collect(process);
  return elements;
}

// Resolve element.incoming / element.outgoing to SequenceFlow objects.
// bpmn-moddle resolves these references to the flow objects themselves, but
// fall back to id lookup when only an id string is present.
function resolveFlows(refs, flowById) {
  const out = [];
  for (const ref of refs || []) {
    if (typeof ref === "string") {
      const f = flowById.get(ref);
      if (f) out.push(f);
    } else if (ref && ref.$type === "bpmn:SequenceFlow") {
      out.push(ref);
    } else if (ref && ref.id && flowById.has(ref.id)) {
      out.push(flowById.get(ref.id));
    }
  }
  return out;
}

function buildFlowIndex(flowElements) {
  const flowById = new Map();
  for (const el of flowElements) {
    if (el.$type === "bpmn:SequenceFlow") flowById.set(el.id, el);
  }
  return flowById;
}

function isSequenceFlow(el) {
  return el.$type === "bpmn:SequenceFlow";
}

function hasConditionExpression(flow) {
  return Boolean(flow.conditionExpression && flow.conditionExpression.body);
}

function targetRefId(flow) {
  const t = flow.targetRef;
  if (!t) return undefined;
  return typeof t === "string" ? t : t.id;
}

function sourceRefId(flow) {
  const s = flow.sourceRef;
  if (!s) return undefined;
  return typeof s === "string" ? s : s.id;
}

function nodeLabel(el) {
  return el.name || el.id || "unknown";
}

// First uipath:Activity / uipath:Event / uipath:Mapping extension on an element.
function getUiPathExtensions(element) {
  const out = [];
  for (const ext of element.extensionElements?.values || []) {
    if (
      ext.$type === "uipath:Activity" ||
      ext.$type === "uipath:Event" ||
      ext.$type === "uipath:Mapping"
    ) {
      out.push(ext);
    }
  }
  return out;
}

// =====================================================================
// Ported rule: ConditionalFlowRule.ts -> MISSING_CONDITION_EXPRESSION
// XOR-gateway outgoing flows must each have a condition or be the default.
// =====================================================================
function validateConditionalFlows(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    const flowElements = getAllFlowElements(process);
    const flowById = buildFlowIndex(flowElements);
    const nodeById = new Map(flowElements.map((e) => [e.id, e]));

    for (const node of flowElements) {
      if (node.$type !== "bpmn:ExclusiveGateway") continue;

      const outgoing = resolveFlows(node.outgoing, flowById);

      // Ignore flows whose target is a text annotation (matches frontend).
      const nonAnnotation = outgoing.filter((flow) => {
        const target = nodeById.get(targetRefId(flow));
        return target?.$type !== "bpmn:TextAnnotation";
      });

      if (nonAnnotation.length <= 1) continue;

      const defaultId =
        node.default && (typeof node.default === "string" ? node.default : node.default.id);

      const incomplete = nonAnnotation.filter(
        (flow) => !hasConditionExpression(flow) && flow.id !== defaultId
      );

      for (const flow of incomplete) {
        out.push({
          code: "MISSING_CONDITION_EXPRESSION",
          severity: SEVERITY.ERROR,
          message: `Flow "${nodeLabel(flow)}" from gateway "${nodeLabel(node)}" is missing a condition expression`,
          description:
            "Each non-default outgoing flow of an exclusive gateway must have a condition expression, or be marked as the gateway's default flow.",
          elementId: flow.id,
        });
      }
    }
  }
  return out;
}

// Shared helper used by the error-boundary checks below.
// (The EMPTY_REQUIRED_FIELD rule was removed: the moddle descriptor carries no
//  `required` attribute on inputs/outputs, so the rule could never fire.)
function isNilOrEmpty(v) {
  return v === undefined || v === null || String(v).trim() === "";
}

// =====================================================================
// Variable-reference checks -> VARIABLE_DOES_NOT_EXIST
// Every vars.X in an input body / output var / condition must be declared.
// =====================================================================
function validateVariableReferences(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    const declared = new Set();
    collectVariableIds(process, declared);

    const flowElements = getAllFlowElements(process);

    for (const element of flowElements) {
      for (const ext of getUiPathExtensions(element)) {
        for (const input of ext.input || []) {
          const text = input.body ?? input.value;
          if (text) checkVarsInText(text, declared, element, out);
        }
        for (const ctxInput of ext.context?.input || []) {
          const text = ctxInput.body ?? ctxInput.value;
          if (text) checkVarsInText(text, declared, element, out);
        }
        for (const output of ext.output || []) {
          if (output.var && !declared.has(output.var)) {
            out.push({
              code: "VARIABLE_DOES_NOT_EXIST",
              severity: SEVERITY.ERROR,
              message: `Output in "${nodeLabel(element)}" writes to undeclared variable "${output.var}"`,
              description: `Output "${output.name}" writes to variable id "${output.var}" which is not declared in <uipath:variables>.`,
              elementId: element.id,
            });
          }
        }
      }
    }

    for (const el of flowElements) {
      if (isSequenceFlow(el) && el.conditionExpression?.body) {
        checkVarsInText(el.conditionExpression.body, declared, el, out);
      }
    }
  }
  return out;
}

function collectVariableIds(process, ids) {
  const varsEl = (process.extensionElements?.values || []).find(
    (el) => el.$type === "uipath:Variables"
  );
  if (varsEl) {
    for (const v of [
      ...(varsEl.inputOutput || []),
      ...(varsEl.input || []),
      ...(varsEl.output || []),
    ]) {
      // Real BPMN expressions reference variables by either id or name
      // (e.g. `vars.requestType` while id is `Var_RequestType`), so accept both.
      if (v.id) ids.add(v.id);
      if (v.name) ids.add(v.name);
    }
  }
  for (const el of process.flowElements || []) {
    if (el.$type === "bpmn:SubProcess" && el.extensionElements) {
      collectVariableIds(el, ids);
    }
  }
}

function checkVarsInText(text, declared, element, out) {
  const refs = String(text).match(/vars\.([a-zA-Z0-9_]+)/g);
  if (!refs) return;
  for (const ref of refs) {
    const varId = ref.substring(5);
    // `iterator.` and `metadata.` never start with `vars.`, so they are not
    // matched here; the error context (`vars.error`) is matched and skipped.
    if (BUILTIN_NON_VARIABLE_REFS.has(varId)) continue;
    if (!declared.has(varId)) {
      out.push({
        code: "VARIABLE_DOES_NOT_EXIST",
        severity: SEVERITY.ERROR,
        message: `Variable "${varId}" referenced in "${nodeLabel(element)}" does not exist`,
        description: `Expression references "vars.${varId}" but no variable with id="${varId}" is declared.`,
        elementId: element.id,
      });
    }
  }
}

// =====================================================================
// Ported rule: MissingRootVariableRule.ts -> MISSING_ROOT_VARIABLE (WARNING)
// A node output's `var` must resolve to a variable declared at the node's own
// scope, an ancestor subprocess, or the root process. Missing entries signal
// data corruption.
// =====================================================================
function validateMissingRootVariables(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    const rootIds = new Set();
    collectScopeVariableIds(process, rootIds);

    // Walk subprocess tree, accumulating in-scope variable ids per node.
    function walk(container, inheritedIds) {
      const scopeIds = new Set(inheritedIds);
      collectScopeVariableIds(container, scopeIds);

      for (const el of container.flowElements || []) {
        if (el.$type === "bpmn:SubProcess") {
          walk(el, scopeIds);
          continue;
        }
        for (const ext of getUiPathExtensions(el)) {
          const outputs = ext.output || [];
          const missing = outputs.some((o) => o.var && !scopeIds.has(o.var));
          if (missing) {
            out.push({
              code: "MISSING_ROOT_VARIABLE",
              severity: SEVERITY.WARNING,
              message: `Node "${nodeLabel(el)}" has an output bound to a variable missing from its scope`,
              description:
                "An output writes to a variable id that is not declared at this node's scope, any ancestor subprocess, or the root process. This usually indicates corrupted variable metadata.",
              elementId: el.id,
            });
            break;
          }
        }
      }
    }
    walk(process, rootIds);
  }
  return out;
}

function collectScopeVariableIds(container, ids) {
  const varsEl = (container.extensionElements?.values || []).find(
    (el) => el.$type === "uipath:Variables"
  );
  if (!varsEl) return;
  for (const v of [
    ...(varsEl.inputOutput || []),
    ...(varsEl.input || []),
    ...(varsEl.output || []),
  ]) {
    if (v.id) ids.add(v.id);
  }
}

// =====================================================================
// Ported rule: FakeJoinRule.ts -> FAKE_JOIN
// Activities and events must not have more than one incoming sequence flow.
// =====================================================================
function validateFakeJoins(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    const flowElements = getAllFlowElements(process);
    const incomingCount = new Map();
    for (const el of flowElements) {
      if (!isSequenceFlow(el)) continue;
      const t = targetRefId(el);
      if (t) incomingCount.set(t, (incomingCount.get(t) || 0) + 1);
    }
    for (const node of flowElements) {
      if (!isActivityOrEvent(node)) continue;
      if ((incomingCount.get(node.id) || 0) > 1) {
        out.push({
          code: "FAKE_JOIN",
          severity: SEVERITY.ERROR,
          message: `Node "${nodeLabel(node)}" has multiple incoming flows`,
          description:
            "Activities and events must not have multiple incoming sequence flows. Use a gateway to join paths.",
          elementId: node.id,
        });
      }
    }
  }
  return out;
}

function isActivityOrEvent(node) {
  return ACTIVITY_TYPES.has(node.$type) || EVENT_TYPES.has(node.$type);
}

// =====================================================================
// Ported rule: SuperfluousGatewayRule.ts -> SUPERFLUOUS_GATEWAY
// A gateway with exactly one incoming and one outgoing flow is superfluous.
// =====================================================================
function validateSuperfluousGateways(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    const flowElements = getAllFlowElements(process);
    const incoming = new Map();
    const outgoing = new Map();
    for (const el of flowElements) {
      if (!isSequenceFlow(el)) continue;
      const t = targetRefId(el);
      const s = sourceRefId(el);
      if (t) incoming.set(t, (incoming.get(t) || 0) + 1);
      if (s) outgoing.set(s, (outgoing.get(s) || 0) + 1);
    }
    for (const node of flowElements) {
      if (!isGateway(node)) continue;
      if ((incoming.get(node.id) || 0) === 1 && (outgoing.get(node.id) || 0) === 1) {
        out.push({
          code: "SUPERFLUOUS_GATEWAY",
          severity: SEVERITY.ERROR,
          message: `Gateway "${nodeLabel(node)}" is superfluous`,
          description:
            "A gateway should have at least two incoming or two outgoing flows. Remove it or merge the surrounding flows.",
          elementId: node.id,
        });
      }
    }
  }
  return out;
}

function isGateway(node) {
  return (
    node.$type === "bpmn:ExclusiveGateway" ||
    node.$type === "bpmn:ParallelGateway" ||
    node.$type === "bpmn:InclusiveGateway"
  );
}

// =====================================================================
// Ported rule: ErrorEndEventRule.ts -> ERROR_END_EVENT_MISSING_EXCEPTION
// An error end event must reference an error (errorRef); otherwise it fails at
// runtime with "Failed to parse BPMN XML".
// =====================================================================
function validateErrorEndEvents(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    for (const node of getAllFlowElements(process)) {
      if (node.$type !== "bpmn:EndEvent") continue;
      const errorDef = (node.eventDefinitions || []).find(
        (d) => d.$type === "bpmn:ErrorEventDefinition"
      );
      if (!errorDef) continue;
      if (!refId(errorDef.errorRef)) {
        out.push({
          code: "ERROR_END_EVENT_MISSING_EXCEPTION",
          severity: SEVERITY.ERROR,
          message: `Error end event "${nodeLabel(node)}" has no error reference`,
          description:
            "An error end event must reference a declared <bpmn:error>. Without it the process fails to parse at runtime.",
          elementId: node.id,
        });
      }
    }
  }
  return out;
}

// =====================================================================
// Ported rule: ErrorBoundaryEventRule.ts
//   -> ERROR_BOUNDARY_EVENT_EMPTY_ERROR_REF
//   -> ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE
//   -> MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK
//   -> DUPLICATE_ERROR_BOUNDARY_EVENT_ON_TASK
// =====================================================================
function validateErrorBoundaryEvents(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    // Index declared <bpmn:error> by id (definitions-level root elements).
    const errorById = new Map();
    for (const el of defs.rootElements || []) {
      if (el.$type === "bpmn:Error") errorById.set(el.id, el);
    }

    const flowElements = getAllFlowElements(process);
    const byTask = new Map();

    for (const node of flowElements) {
      if (node.$type !== "bpmn:BoundaryEvent") continue;
      const errorDef = (node.eventDefinitions || []).find(
        (d) => d.$type === "bpmn:ErrorEventDefinition"
      );
      if (!errorDef) continue;

      const attachedTo = refId(node.attachedToRef);
      if (attachedTo) {
        if (!byTask.has(attachedTo)) byTask.set(attachedTo, []);
        byTask.get(attachedTo).push({ node, errorDef });
      }

      const errorRefId = refId(errorDef.errorRef);

      // errorRef attribute present in XML but resolving to nothing -> empty ref.
      if (!errorRefId && hasOwn(errorDef, "errorRef")) {
        out.push({
          code: "ERROR_BOUNDARY_EVENT_EMPTY_ERROR_REF",
          severity: SEVERITY.ERROR,
          message: `Boundary event "${nodeLabel(node)}" has an empty error reference`,
          description:
            "Select a specific error with an error code, or remove the error reference entirely (catch-all).",
          elementId: node.id,
        });
        continue;
      }

      if (errorRefId) {
        const errorObj = errorById.get(errorRefId);
        if (errorObj && isNilOrEmpty(errorObj.errorCode)) {
          out.push({
            code: "ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE",
            severity: SEVERITY.ERROR,
            message: `Error "${errorObj.name || errorRefId}" referenced by boundary event "${nodeLabel(node)}" has no error code`,
            description: "An error referenced by a boundary event must declare an errorCode.",
            elementId: node.id,
          });
        }
      }
    }

    // Per-task duplicate / multiple catch-all detection.
    for (const [, events] of byTask) {
      const catchAll = events.filter((e) => !hasOwn(e.errorDef, "errorRef"));
      if (catchAll.length > 1) {
        for (const e of catchAll) {
          out.push({
            code: "MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK",
            severity: SEVERITY.ERROR,
            message: `Multiple catch-all error boundary events on "${nodeLabel(e.node)}"`,
            description: "Only one catch-all error boundary event is allowed per task.",
            elementId: e.node.id,
          });
        }
      }

      const byCode = new Map();
      for (const e of events) {
        const errorRefId = refId(e.errorDef.errorRef);
        if (!errorRefId) continue;
        const code = errorById.get(errorRefId)?.errorCode;
        if (!code) continue;
        if (!byCode.has(code)) byCode.set(code, []);
        byCode.get(code).push(e);
      }
      for (const [, sameCode] of byCode) {
        if (sameCode.length > 1) {
          for (const e of sameCode) {
            out.push({
              code: "DUPLICATE_ERROR_BOUNDARY_EVENT_ON_TASK",
              severity: SEVERITY.ERROR,
              message: `Duplicate error boundary event on "${nodeLabel(e.node)}"`,
              description: "Only one error boundary event is allowed per error code per task.",
              elementId: e.node.id,
            });
          }
        }
      }
    }
  }
  return out;
}

// =====================================================================
// Ported rule: TimerDurationRule.ts
//   -> TIMER_DURATION_INVALID (ERROR)
//   -> TIMER_DURATION_WEEK_UNSUPPORTED (WARNING)
// Static ISO-8601 durations on timer event definitions must be valid; week
// designators (PnW) are unsupported. Expression-mode values (=, @) are skipped.
// =====================================================================
function validateTimerDurations(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    for (const node of getAllFlowElements(process)) {
      const timerDef = (node.eventDefinitions || []).find(
        (d) => d.$type === "bpmn:TimerEventDefinition"
      );
      if (!timerDef) continue;
      const value = timerDef.timeDuration?.body;
      if (!value) continue;
      if (value.startsWith("=") || value.startsWith("@")) continue;

      if (!isValidIso8601Duration(value)) {
        out.push({
          code: "TIMER_DURATION_INVALID",
          severity: SEVERITY.ERROR,
          message: `Timer "${nodeLabel(node)}" has an invalid duration "${value}"`,
          description: "Timer durations must be valid ISO-8601 durations, e.g. PT30S, PT15M, P1D.",
          elementId: node.id,
        });
        continue;
      }
      if (/\d+W/.test(value)) {
        out.push({
          code: "TIMER_DURATION_WEEK_UNSUPPORTED",
          severity: SEVERITY.WARNING,
          message: `Timer "${nodeLabel(node)}" uses an unsupported week designator "${value}"`,
          description: "ISO-8601 week durations (PnW) are not supported; express the duration in days.",
          elementId: node.id,
        });
      }
    }
  }
  return out;
}

// ISO-8601 duration: PnYnMnDTnHnMnS or PnW. Must contain at least one component.
function isValidIso8601Duration(value) {
  if (typeof value !== "string") return false;
  const re = /^P(?!$)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?!$)(\d+H)?(\d+M)?(\d+(?:\.\d+)?S)?)?$/;
  if (!re.test(value)) return false;
  // Reject a bare "P" or "PT" with no actual component.
  return /\d/.test(value);
}

// =====================================================================
// Ported rule: SingleBlankStartEventRule.ts -> MULTIPLE_BLANK_START_EVENTS
// Each scope (process / subprocess) may have at most one blank start event
// (a StartEvent with no event definition).
// =====================================================================
function validateSingleBlankStartEvent(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    checkScopeBlankStarts(process, out);
    for (const el of getAllFlowElements(process)) {
      if (el.$type === "bpmn:SubProcess") checkScopeBlankStarts(el, out);
    }
  }
  return out;
}

function checkScopeBlankStarts(container, out) {
  const blanks = (container.flowElements || []).filter(
    (el) => el.$type === "bpmn:StartEvent" && (el.eventDefinitions || []).length === 0
  );
  if (blanks.length > 1) {
    const kind = container.$type === "bpmn:SubProcess" ? "Sub-process" : "Process";
    out.push({
      code: "MULTIPLE_BLANK_START_EVENTS",
      severity: SEVERITY.ERROR,
      message: `${kind} "${nodeLabel(container)}" has ${blanks.length} blank start events`,
      description: `A ${kind.toLowerCase()} may have at most one blank (untyped) start event.`,
      elementId: container.id,
    });
  }
}

// =====================================================================
// Ported rule: MissingResourceRule.ts -> MISSING_RESOURCE (WARNING)
// Resource-backed service types must bind a resource: V1 `releaseKey` context
// input, or V2 `name` binding.
// =====================================================================
function validateMissingResource(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    for (const element of getAllFlowElements(process)) {
      for (const ext of getUiPathExtensions(element)) {
        const serviceType = ext.type?.value;
        if (!serviceType || !SERVICE_TYPES_REQUIRING_RESOURCE.has(serviceType)) continue;

        const ctxInputs = ext.context?.input || [];
        const releaseKey = ctxInputs.find((c) => c.name === "releaseKey")?.value;
        const name =
          ctxInputs.find((c) => c.name === "name")?.value ||
          ctxInputs.find((c) => c.name === "process")?.value;

        if (!releaseKey && !name) {
          out.push({
            code: "MISSING_RESOURCE",
            severity: SEVERITY.WARNING,
            message: `Node "${nodeLabel(element)}" (${serviceType}) has no bound resource`,
            description:
              "Resource-backed service types must bind a resource via a releaseKey/process/name context input. Enrich the binding before Operate.",
            elementId: element.id,
          });
        }
      }
    }
  }
  return out;
}

// =====================================================================
// Maestro runtime extra: IS connector framework completeness.
// =====================================================================
function validateIsConnectorFramework(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    for (const element of getAllFlowElements(process)) {
      for (const ext of element.extensionElements?.values || []) {
        if (ext.$type !== "uipath:Activity" && ext.$type !== "uipath:Event") continue;
        const typeValue = ext.type?.value;
        if (!typeValue || !IS_CONNECTOR_TYPES_LIST.includes(typeValue)) continue;

        const ctxNames = new Set((ext.context?.input || []).map((i) => i.name));
        if (!ctxNames.has("connectorKey")) {
          out.push({
            code: "MISSING_IS_CONNECTOR_FIELD",
            severity: SEVERITY.WARNING,
            message: `"${nodeLabel(element)}" (${typeValue}) is missing "connectorKey" in context`,
            description: "IS connector activities must carry connectorKey in context.",
            elementId: element.id,
          });
        }
        if (!ctxNames.has("objectName")) {
          out.push({
            code: "MISSING_IS_CONNECTOR_FIELD",
            severity: SEVERITY.WARNING,
            message: `"${nodeLabel(element)}" (${typeValue}) is missing "objectName" in context`,
            description: "IS connector activities must carry objectName in context.",
            elementId: element.id,
          });
        }
        const hasBody = (ext.input || []).some((i) => i.target === "body");
        if (!hasBody) {
          out.push({
            code: "MISSING_IS_BODY_INPUT",
            severity: SEVERITY.WARNING,
            message: `"${nodeLabel(element)}" (${typeValue}) is missing a body input (target="body")`,
            description: 'IS connector activities must have a <uipath:input target="body"> request payload.',
            elementId: element.id,
          });
        }
      }
    }
  }
  return out;
}

// =====================================================================
// Maestro runtime extra: email trigger config completeness.
// =====================================================================
function validateConfigCompleteness(defs) {
  const out = [];
  for (const process of getProcesses(defs)) {
    for (const element of getAllFlowElements(process)) {
      for (const ext of element.extensionElements?.values || []) {
        if (ext.$type === "uipath:Event" && ext.type?.value === "Intsvc.EventTrigger") {
          validateEventTriggerConfig(element, ext, out);
        }
      }
    }
  }
  return out;
}

function validateEventTriggerConfig(element, eventExt, out) {
  const label = nodeLabel(element);
  const ctxInputs = eventExt.context?.input || [];
  const operation = ctxInputs.find((i) => i.name === "operation")?.value;
  if (operation !== "EMAIL_RECEIVED") return;

  const bodyInput = (eventExt.input || []).find(
    (i) => i.$type === "uipath:Input" && i.name === "body"
  );
  if (bodyInput?.body) {
    try {
      const bodyData = JSON.parse(bodyInput.body);
      const folderId = bodyData.queryParams?.parentFolderId;
      if (!folderId) {
        out.push({
          code: "INCOMPLETE_TRIGGER_CONFIG",
          severity: SEVERITY.WARNING,
          message: `Email trigger "${label}" is missing the email folder (parentFolderId)`,
          description:
            'Discover folder IDs with "uip is resources execute list uipath-microsoft-outlook365 MailFolder --connection-id <id> --output json", or ask the user.',
          elementId: element.id,
        });
      } else if (!folderId.startsWith("AAMk")) {
        out.push({
          code: "INVALID_TRIGGER_CONFIG",
          severity: SEVERITY.WARNING,
          message: `Email trigger "${label}" has an invalid parentFolderId`,
          description: 'parentFolderId must be an Exchange folder ID (starts with "AAMk...").',
          elementId: element.id,
        });
      }
    } catch {}
  }
}

// =====================================================================
// Maestro runtime extra: connection-liveness ping via uip CLI.
// =====================================================================
async function validateConnectionHealth(defs) {
  const out = [];
  const uipBin = resolveUipBin();
  if (!uipBin) return out;

  for (const process of getProcesses(defs)) {
    const bindingsEl = (process.extensionElements?.values || []).find(
      (el) => el.$type === "uipath:Bindings"
    );
    const bindings = bindingsEl?.binding || [];
    const connectionBindings = bindings.filter(
      (b) => b.resource === "Connection" && b.propertyAttribute === "ConnectionId"
    );

    const seen = new Set();
    for (const binding of connectionBindings) {
      const connId = binding.default;
      if (!connId || seen.has(connId)) continue;
      seen.add(connId);
      try {
        // execFileSync with an argument array — no shell, so connId (from the
        // BPMN binding) cannot inject shell metacharacters.
        const output = execFileSync(
          uipBin,
          ["is", "connections", "ping", connId, "--output", "json"],
          { encoding: "utf8", timeout: 15000, stdio: "pipe" }
        );
        const r = JSON.parse(output);
        if (r.Result !== "Success" || r.Data?.Status !== "Enabled") {
          out.push({
            code: "UNHEALTHY_CONNECTION",
            severity: SEVERITY.ERROR,
            message: `Connection "${connId}" is not healthy (${r.Data?.Status || r.Message || "unknown"})`,
            description: `Fix the connection with: uip is connections edit ${connId}`,
          });
        }
      } catch (e) {
        out.push({
          code: "UNHEALTHY_CONNECTION",
          severity: SEVERITY.ERROR,
          message: `Connection "${connId}" could not be reached`,
          description: `Ping failed: ${e.message?.split("\n")[0]}. Fix with: uip is connections edit ${connId}`,
        });
      }
    }
  }
  return out;
}

// =====================================================================
// Optional: solution-resource validation (SolutionResourceValidationUtils.ts)
// =====================================================================
function validateSolutionResources(defs, releaseNames) {
  const out = [];
  for (const process of getProcesses(defs)) {
    const bindingsEl = (process.extensionElements?.values || []).find(
      (el) => el.$type === "uipath:Bindings"
    );
    const bindings = bindingsEl?.binding || [];
    const nameBindings = bindings.filter((b) => b.name === "name");
    if (!nameBindings.length) continue;

    for (const element of getAllFlowElements(process)) {
      const ctxInputs = [];
      for (const ext of getUiPathExtensions(element)) {
        for (const i of ext.context?.input || []) {
          if (i.$type === "uipath:Input" && i.value) ctxInputs.push(i);
        }
      }
      if (!ctxInputs.length) continue;

      for (const binding of nameBindings) {
        const usedByElement = ctxInputs.some((i) => i.value === `=bindings.${binding.id}`);
        if (usedByElement) {
          const resourceName = binding.default;
          if (resourceName && !releaseNames.includes(resourceName)) {
            out.push({
              code: "MISSING_SOLUTION_RESOURCE",
              severity: SEVERITY.ERROR,
              message: `Resource "${resourceName}" used by "${nodeLabel(element)}" is not found in the solution`,
              description: `The resource "${resourceName}" is not among the provided release names.`,
              elementId: element.id,
            });
          }
        }
      }
    }
  }
  return out;
}

function fetchReleaseNames(folderId) {
  const uipBin = resolveUipBin();
  if (!uipBin) throw new Error("uip CLI not found");
  const output = execFileSync(
    uipBin,
    ["or", "releases", "list", folderId, "--output", "json"],
    { encoding: "utf8", timeout: 30000 }
  );
  const parsed = JSON.parse(output);
  if (parsed.Result !== "Success") throw new Error(parsed.Message || "Failed to list releases");
  return (parsed.Data || []).map((r) => r.Name);
}

// =====================================================================
// Small utilities
// =====================================================================
function refId(ref) {
  if (!ref) return undefined;
  return typeof ref === "string" ? ref : ref.id;
}

function hasOwn(obj, key) {
  return Object.prototype.hasOwnProperty.call(obj, key) && obj[key] !== undefined;
}
