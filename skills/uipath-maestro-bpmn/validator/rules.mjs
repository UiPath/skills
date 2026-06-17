// Self-contained Maestro BPMN validation rule engine.
//
// This module is a faithful, offline port of the PO.Frontend canvas validation
// rule engine (PO.Frontend/src/services/validation/bpmn/). It operates on the
// reconstructed Node[]/Edge[]/CanvasState model (see model.mjs), which mirrors
// the frontend's `Node[]`/`Edge[]` derived from the same BPMN XML.
//
// PHASE 2 NOTE: this file is intentionally the *only* place rule logic lives.
// When the rules ship as a published npm package, this module is replaced by an
// import of that package with NO behavior change — model.mjs and
// validate-bpmn.mjs stay as the integration layer.
//
// Each rule cites the PO.Frontend source it is ported from.

import { Duration } from "luxon";

export const SEVERITY = { ERROR: "ERROR", WARNING: "WARNING" };

// ---------------------------------------------------------------------------
// Lookup maps — port of ValidateBpmnFlowUtils.buildValidationLookupMaps.
// ---------------------------------------------------------------------------
export function buildValidationLookupMaps(nodes, edges) {
  const nodeById = new Map();
  const nodesByParentId = new Map();
  const edgesBySource = new Map();
  const edgesByTarget = new Map();

  for (const node of nodes) {
    nodeById.set(node.id, node);
    const parentId = node.parentId;
    const siblings = nodesByParentId.get(parentId);
    if (siblings) siblings.push(node);
    else nodesByParentId.set(parentId, [node]);
  }
  for (const edge of edges) {
    const s = edgesBySource.get(edge.source);
    if (s) s.push(edge);
    else edgesBySource.set(edge.source, [edge]);
    const t = edgesByTarget.get(edge.target);
    if (t) t.push(edge);
    else edgesByTarget.set(edge.target, [edge]);
  }
  return { nodeById, nodesByParentId, edgesBySource, edgesByTarget };
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------
function dotGet(obj, prop, defaultValue) {
  const parts = String(prop).match(/[^.[\]]+|\[\d+\]/g) ?? [];
  let cur = obj;
  for (const raw of parts) {
    if (cur === null || typeof cur !== "object") return defaultValue;
    const key = /^\[\d+\]$/.test(raw) ? Number(raw.slice(1, -1)) : raw;
    cur = cur[key];
  }
  return cur === undefined ? defaultValue : cur;
}

// Port of EventObjectUtil.getEventObjectDetailsMapping (Errors branch only;
// the boundary-event rule only consults bpmn:ErrorEventDefinition).
function getEventObjectDetailsMapping(bpmnType) {
  if (bpmnType === "bpmn:ErrorEventDefinition") {
    return { type: "errors", accessor: "data.eventDefinition.errorRef", code: "errorCode" };
  }
  return undefined;
}

function isNilOrEmpty(value) {
  return value === undefined || value === null || (typeof value === "string" && value.trim() === "");
}

// ---------------------------------------------------------------------------
// Variable / expression helpers — port of VariableUtil.ts
// ---------------------------------------------------------------------------

// Captures the first segment after the prefix: e.g. "vars.response" / vars["response"].
const VAR_REFS_REGEX = /(^|\b)(vars|result)(?:\.([\w]+)|\["([^"]+)"\])/g;

// Special namespaces that are NOT user-declared variables. `iterator.` and
// `metadata.` never start with `vars.`, so they are excluded by the regex
// itself; `error` is the boundary-error context exposed as `vars.error`, which
// IS matched by the regex and therefore must be skipped explicitly here.
const BUILTIN_NON_VARIABLE_VARS_SEGMENTS = new Set(["error"]);

/**
 * Port of VariableUtil.validateNoAssignments. Returns true if the expression
 * contains an assignment operator (excluding comparison/arrow operators).
 */
export function expressionHasAssignment(expression) {
  if (!expression) return false;
  const offset = expression.startsWith("=") ? 1 : 0;
  const body = expression.slice(offset);
  if (!body.trim()) return false;
  const sanitized = body
    .replaceAll(/"(?:[^"\\]|\\.)*"/g, (m) => " ".repeat(m.length))
    .replaceAll(/'(?:[^'\\]|\\.)*'/g, (m) => " ".repeat(m.length))
    .replaceAll(/`(?:[^`\\]|\\.)*`/g, (m) => " ".repeat(m.length))
    .replaceAll(/\/(?:[^/\\]|\\.)*\/[gimsuy]*/g, (m) => " ".repeat(m.length));
  const assignmentRegex =
    /(\?\?=|&&=|\|\|=|>>>=|<<=|>>=|\*\*=|\+=|-=|\*=|\/=|%=|&=|\|=|\^=|(?<![!=<>+\-*/%.&|^?])=(?![=>]))/;
  return assignmentRegex.test(sanitized);
}

/**
 * Collect every `vars.X` / `result.X` reference in an expression that does NOT
 * resolve. Mirrors VariableUtil.getVariablesInExpression (the `nonExisting`
 * half) + the result-validity split in validateVariablesInExpression:758-782.
 *
 *  - `vars.X` resolves against `knownIds` (variable ids/names/canonicalIds,
 *    declared anywhere) — matches `existingIdsSet` semantics in the frontend.
 *  - `result.X` resolves ONLY against the referencing element's OWN output
 *    identifiers (`resultIds`); a `result.X` that names no output of this
 *    element is flagged, exactly like `isResultVariableValidForElement`
 *    (VariableUtil.ts:166-178) pushing it onto the non-existing set
 *    (VariableUtil.ts:263 treats the unresolved result ref as non-existing).
 *
 * `resultIds` defaults to an empty set: in contexts where result refs are not
 * element-local (e.g. edge conditions, which have no own outputs) every
 * `result.X` is unresolved, matching the frontend.
 */
export function findUnknownVariableRefs(expression, knownIds, resultIds = new Set()) {
  if (!expression) return [];
  const out = [];
  const resolvesAgainst = (seg, ids) => {
    if (ids.has(seg)) return true;
    // Nested-path tolerance: foo.bar resolves if `foo` is known.
    for (const id of ids) {
      if (seg === id || seg.startsWith(`${id}.`)) return true;
    }
    return false;
  };
  for (const match of expression.matchAll(VAR_REFS_REGEX)) {
    const prefix = match[2];
    const seg = match[3] ?? match[4];
    if (!seg) continue;
    if (prefix === "result") {
      // `result.X` is a node-local output alias; valid only if X names one of
      // this element's own outputs (frontend isResultVariableValidForElement).
      if (!resolvesAgainst(seg, resultIds)) out.push(match[0]);
      continue;
    }
    if (BUILTIN_NON_VARIABLE_VARS_SEGMENTS.has(seg)) continue;
    if (!resolvesAgainst(seg, knownIds)) out.push(match[0]);
  }
  return [...new Set(out)];
}

// ---------------------------------------------------------------------------
// Port of Tools.getAccessorFromType — selects which field of a custom output
// carries the user expression to validate.
function getAccessorFromType(type) {
  if (type === "json" || type === "jsonSchema" || type === "array") return "body";
  if (type === "file" || type === "octet-stream") return "target";
  return "source";
}

// ---------------------------------------------------------------------------
// ISO-8601 duration helpers — port of DateUtil.ts
// ---------------------------------------------------------------------------
function isValidIso8601(value) {
  return Duration.fromISO(value).isValid;
}
function hasIso8601WeekDesignator(value) {
  return /W/i.test(value);
}

// ===========================================================================
// RULE 1: ConditionalFlowRule
// ===========================================================================
export function validateConditionalSequenceFlow(nodes, _edges, lookupMaps) {
  const errors = [];
  const { edgesBySource, nodeById } = lookupMaps;
  for (const node of nodes) {
    if (node.type !== "bpmn:ExclusiveGateway") continue;
    const outgoing = edgesBySource.get(node.id) ?? [];
    const nonAnnotation = outgoing.filter((f) => nodeById.get(f.target)?.type !== "bpmn:TextAnnotation");
    if (nonAnnotation.length <= 1) continue;
    const hasDefault = nonAnnotation.some((f) => Boolean(f.data?.defaultFlow));
    const missing = nonAnnotation.filter((f) => !f.data?.conditionExpression && !f.data?.defaultFlow);
    if (missing.length === 0) continue;
    for (const flow of missing) {
      errors.push({
        code: "MISSING_CONDITION_EXPRESSION",
        message: "Sequence flow is missing condition expression",
        severity: SEVERITY.ERROR,
        sourceId: flow.source,
        targetId: flow.target,
        elementId: flow.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 2: ConnectionRule
// ===========================================================================
const baseAllowedTargets = new Set(["bpmn:TextAnnotation"]);
const commonAllowedTargets = new Set([
  ...baseAllowedTargets,
  "bpmn:IntermediateThrowEvent",
  "bpmn:IntermediateCatchEvent",
  "bpmn:EndEvent",
  "bpmn:ExclusiveGateway",
  "bpmn:ParallelGateway",
  "bpmn:InclusiveGateway",
  "bpmn:ComplexGateway",
  "bpmn:Task",
  "bpmn:UserTask",
  "bpmn:ServiceTask",
  "bpmn:SendTask",
  "bpmn:ReceiveTask",
  "bpmn:ManualTask",
  "bpmn:BusinessRuleTask",
  "bpmn:ScriptTask",
  "bpmn:CallActivity",
  "bpmn:SubProcess",
  "bpmn:AdHocSubProcess",
  "bpmn:Transaction",
]);
const activityAllowedTargets = new Set([
  ...commonAllowedTargets,
  "bpmn:EventBasedGateway",
  "bpmn:DataOutput",
  "bpmn:DataStoreReference",
  "bpmn:DataObjectReference",
]);
// Port of BPMNTypes.allowedTargetNodeTypesForSourceNodeType (concrete entries).
const allowedTargetNodeTypesForSourceNodeType = {
  "bpmn:StartEvent": commonAllowedTargets,
  "bpmn:IntermediateThrowEvent": commonAllowedTargets,
  "bpmn:IntermediateCatchEvent": commonAllowedTargets,
  "bpmn:BoundaryEvent": commonAllowedTargets,
  "bpmn:EndEvent": new Set(["bpmn:TextAnnotation"]),
  "bpmn:ExclusiveGateway": commonAllowedTargets,
  "bpmn:ParallelGateway": commonAllowedTargets,
  "bpmn:InclusiveGateway": commonAllowedTargets,
  "bpmn:ComplexGateway": commonAllowedTargets,
  "bpmn:EventBasedGateway": new Set(["bpmn:IntermediateCatchEvent", "bpmn:TextAnnotation"]),
  "bpmn:Task": activityAllowedTargets,
  "bpmn:UserTask": activityAllowedTargets,
  "bpmn:ServiceTask": activityAllowedTargets,
  "bpmn:SendTask": activityAllowedTargets,
  "bpmn:ReceiveTask": activityAllowedTargets,
  "bpmn:ManualTask": activityAllowedTargets,
  "bpmn:BusinessRuleTask": activityAllowedTargets,
  "bpmn:ScriptTask": activityAllowedTargets,
  "bpmn:CallActivity": activityAllowedTargets,
  "bpmn:SubProcess": activityAllowedTargets,
  "bpmn:AdHocSubProcess": activityAllowedTargets,
  "bpmn:Transaction": activityAllowedTargets,
  "bpmn:TextAnnotation": new Set(),
  "bpmn:Participant": baseAllowedTargets,
  "bpmn:Lane": baseAllowedTargets,
};

function canNodeTypesBeConnected(sourceNode, targetNode) {
  const s = sourceNode?.type;
  const t = targetNode?.type;
  if (!sourceNode || !s || !targetNode || !t) return false;
  const allowed = allowedTargetNodeTypesForSourceNodeType[s];
  // No matching rule for the source type → frontend `canNodeTypesBeConnected`
  // returns false (BPMNTypesUtils.ts:51-82: after the explicit-rule and
  // inherited-rule loops exhaust with no match it `return false`). The
  // abstract-type inheritance the frontend additionally walks is already folded
  // into our concrete allow-map (every concrete activity/event type has an
  // explicit entry above), so an unknown source type genuinely has no rule and
  // must be rejected as INVALID_CONNECTION_TYPE.
  if (!allowed) return false;
  return allowed.has(t);
}

export function validateConnections(nodes, edges, lookupMaps) {
  const { nodeById } = lookupMaps;
  const errors = [];
  for (const edge of edges) {
    // Only sequence flows participate in node-type connection rules; message
    // flows/associations have separate rules. Frontend `Edge[]` for a diagram
    // are predominantly sequence flows.
    if (edge.type && edge.type !== "bpmn:SequenceFlow") continue;
    const sourceNode = nodeById.get(edge.source);
    const targetNode = nodeById.get(edge.target);
    if (!sourceNode || !targetNode) {
      errors.push({
        code: "INVALID_CONNECTION",
        message: "Broken flow line: references an element that no longer exists.",
        severity: SEVERITY.WARNING,
        sourceId: edge.source,
        targetId: edge.target,
        elementId: edge.id,
      });
      continue;
    }
    if (sourceNode.id === targetNode.id) {
      errors.push({
        code: "INVALID_CONNECTION",
        message: "Invalid connection: source and target cannot be the same.",
        severity: SEVERITY.WARNING,
        sourceId: edge.source,
        targetId: edge.target,
        elementId: edge.id,
      });
      continue;
    }
    if (!canNodeTypesBeConnected(sourceNode, targetNode)) {
      errors.push({
        code: "INVALID_CONNECTION_TYPE",
        message: `${sourceNode.type} cannot connect to ${targetNode.type}.`,
        severity: SEVERITY.WARNING,
        sourceId: edge.source,
        targetId: edge.target,
        elementId: edge.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 3: DuplicateErrorEventSubprocessRule
// ===========================================================================
function getErrorObject(canvasState, errorRef) {
  const errorObjects = canvasState.objects?.errors ?? [];
  return errorObjects.find((o) => o.id === errorRef);
}

export function validateDuplicateErrorEventSubprocess(nodes, canvasState, lookupMaps) {
  const { nodesByParentId } = lookupMaps;
  const infos = [];
  const eventSubprocesses = nodes.filter((n) => n.type === "bpmn:SubProcess" && n.data?.triggeredByEvent === true);
  for (const sp of eventSubprocesses) {
    const children = nodesByParentId.get(sp.id) ?? [];
    const starts = children.filter((c) => c.type === "bpmn:StartEvent" && c.data?.eventDefinition?.type === "bpmn:ErrorEventDefinition");
    for (const se of starts) {
      const ed = se.data?.eventDefinition ?? {};
      infos.push({ node: sp, errorRef: ed.errorRef, errorCode: getErrorObject(canvasState, ed.errorRef)?.errorCode });
    }
  }
  const grouped = new Map();
  for (const i of infos) {
    const scope = i.node.parentId || "root";
    const arr = grouped.get(scope) ?? [];
    arr.push(i);
    grouped.set(scope, arr);
  }
  const errors = [];
  for (const [, scoped] of grouped) {
    const catchAll = scoped.filter((i) => i.errorRef === undefined);
    if (catchAll.length > 1) {
      for (const i of catchAll) {
        errors.push({
          code: "MULTIPLE_CATCH_ALL_ERROR_EVENT_SUBPROCESS",
          message: "Only one catch-all error event subprocess is allowed per scope.",
          severity: SEVERITY.ERROR,
          elementId: i.node.id,
        });
      }
    }
    const byCode = new Map();
    for (const i of scoped) {
      if (i.errorRef !== undefined && i.errorRef !== "" && i.errorCode) {
        const arr = byCode.get(i.errorCode) ?? [];
        arr.push(i);
        byCode.set(i.errorCode, arr);
      }
    }
    for (const [, same] of byCode) {
      if (same.length > 1) {
        for (const i of same) {
          errors.push({
            code: "DUPLICATE_ERROR_EVENT_SUBPROCESS",
            message: "Only one error event subprocess is allowed per error code per scope.",
            severity: SEVERITY.ERROR,
            elementId: i.node.id,
          });
        }
      }
    }
  }
  return errors;
}

// ===========================================================================
// RULE 4: EmptyStartEventDefinitionInSubProcessRule
// ===========================================================================
export function validateEventSubProcessStart(nodes, _edges, lookupMaps) {
  const { nodesByParentId } = lookupMaps;
  const errors = [];
  const allowed = [
    "bpmn:TimerEventDefinition",
    "bpmn:MessageEventDefinition",
    "bpmn:ErrorEventDefinition",
    "bpmn:SignalEventDefinition",
    "bpmn:EscalationEventDefinition",
  ];
  for (const node of nodes) {
    if (node.type !== "bpmn:SubProcess") continue;
    const isEventSubprocess = node.data?.triggeredByEvent === true;
    const children = nodesByParentId.get(node.id) ?? [];
    const starts = children.filter((c) => c.type === "bpmn:StartEvent");
    for (const se of starts) {
      const ed = se.data?.eventDefinition;
      if (isEventSubprocess) {
        if (!ed) {
          errors.push({
            code: "START_EVENT_WITHOUT_DEFINITION_IN_EVENT_SUBPROCESS",
            message: "Start event in an event sub-process must have an event definition.",
            severity: SEVERITY.ERROR,
            elementId: se.id,
            sourceId: node.id,
          });
        } else if (ed.type && !allowed.includes(ed.type)) {
          errors.push({
            code: "INVALID_EVENT_DEFINITION_IN_EVENT_SUBPROCESS",
            message: "Start event in an event sub-process must use Timer/Message/Error/Signal/Escalation.",
            severity: SEVERITY.ERROR,
            elementId: se.id,
            sourceId: node.id,
          });
        }
      } else if (ed) {
        errors.push({
          code: "START_EVENT_WITH_DEFINITION_IN_SUBPROCESS",
          message: "Start event in a regular sub-process must not have an event definition.",
          severity: SEVERITY.ERROR,
          elementId: se.id,
          sourceId: node.id,
        });
      }
    }
  }
  return errors;
}

// ===========================================================================
// RULE 5: ErrorBoundaryEventRule (validate + duplicate)
// ===========================================================================
export function validateErrorBoundaryEvents(nodes, canvasState) {
  const errors = [];
  for (const node of nodes) {
    if (node.type !== "bpmn:BoundaryEvent") continue;
    const ed = node.data?.eventDefinition;
    if (!ed || ed.type !== "bpmn:ErrorEventDefinition") continue;
    const details = getEventObjectDetailsMapping(ed.type);
    if (!details) continue;
    const errorRefId = dotGet(node, details.accessor);
    if (!errorRefId && ed.errorRef !== undefined) {
      errors.push({
        code: "ERROR_BOUNDARY_EVENT_EMPTY_ERROR_REF",
        message: "Error boundary event has an empty error reference.",
        severity: SEVERITY.ERROR,
        elementId: node.id,
      });
      continue;
    }
    if (errorRefId) {
      const errorObject = (canvasState.objects?.[details.type] ?? []).find((o) => o.id === errorRefId);
      if (errorObject && details.code && (!dotGet(errorObject, details.code) || String(dotGet(errorObject, details.code)).trim() === "")) {
        errors.push({
          code: "ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE",
          message: `Error '${errorObject.name || "Unknown"}' referenced by boundary event must have an error code.`,
          severity: SEVERITY.ERROR,
          elementId: node.id,
        });
      }
    }
  }
  return errors;
}

export function validateDuplicateErrorBoundaryEvents(nodes, canvasState) {
  const errors = [];
  const byTask = new Map();
  for (const node of nodes) {
    if (node.type !== "bpmn:BoundaryEvent") continue;
    const ed = node.data?.eventDefinition;
    if (!ed || ed.type !== "bpmn:ErrorEventDefinition") continue;
    const attachedToId = node.data?.attachedToId;
    if (!attachedToId) continue;
    const arr = byTask.get(attachedToId) ?? [];
    arr.push(node);
    byTask.set(attachedToId, arr);
  }
  for (const [, events] of byTask) {
    const catchAll = events.filter((n) => n.data?.eventDefinition?.errorRef === undefined);
    if (catchAll.length > 1) {
      for (const e of catchAll) {
        errors.push({
          code: "MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK",
          message: "Only one catch-all error boundary event is allowed per task.",
          severity: SEVERITY.ERROR,
          elementId: e.id,
        });
      }
    }
    const byCode = new Map();
    for (const n of events) {
      const ref = n.data?.eventDefinition?.errorRef;
      if (ref !== undefined && ref !== "") {
        const code = getErrorObject(canvasState, ref)?.errorCode;
        if (code) {
          const arr = byCode.get(code) ?? [];
          arr.push(n);
          byCode.set(code, arr);
        }
      }
    }
    for (const [, same] of byCode) {
      if (same.length > 1) {
        for (const n of same) {
          errors.push({
            code: "DUPLICATE_ERROR_BOUNDARY_EVENT_ON_TASK",
            message: "Only one error boundary event is allowed per error code per task.",
            severity: SEVERITY.ERROR,
            elementId: n.id,
          });
        }
      }
    }
  }
  return errors;
}

// ===========================================================================
// RULE 6: ErrorEndEventRule
// ===========================================================================
export function validateErrorEndEvents(nodes) {
  const errors = [];
  for (const node of nodes) {
    if (node.type !== "bpmn:EndEvent") continue;
    const ed = node.data?.eventDefinition;
    if (!ed || ed.type !== "bpmn:ErrorEventDefinition") continue;
    if (!ed.errorRef) {
      errors.push({
        code: "ERROR_END_EVENT_MISSING_EXCEPTION",
        message: "Error end event is missing a configured exception (errorRef).",
        severity: SEVERITY.ERROR,
        elementId: node.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 7: FakeJoinRule
// ===========================================================================
// FAITHFUL-PORT NOTE (drift resolved by matching the frontend's *actual*
// behavior — see validator/test/integration.test.mjs and README "FakeJoin"):
//
// The PO.Frontend FakeJoinRule fires only when `node.type === "bpmn:Activity"`
// or `node.type === "bpmn:Event"` — a LITERAL string equality against the
// abstract BPMN type names (FakeJoinRule.ts, isActivityOrEvent). However, on the
// real canvas every node carries its CONCRETE `$type` (`bpmn:Task`,
// `bpmn:EndEvent`, ...): bpmn-from-xml.ts sets `type: $type` and the validation
// layer compares concrete types everywhere (ValidateBpmnFlowUtils compares
// `=== "bpmn:StartEvent"`). The abstract names are never assigned to a real
// node, so on exported BPMN this frontend rule is effectively DORMANT — it never
// fires. The rule's own source carries a TODO admitting it must be rewritten to
// walk the inherited-type chain, which it does not yet do.
//
// Our model reconstructs CONCRETE types from the XML, mirroring the canvas.
// To match the frontend's observable behavior on real BPMN (and avoid the
// false positives an earlier hand-port produced on valid files), we apply the
// frontend's exact predicate: literal equality on `node.type`. This keeps the
// port faithful — same inputs, same outputs as the frontend — rather than
// inventing a stricter rule the frontend does not have.
function isFrontendFakeJoinType(type) {
  return type === "bpmn:Activity" || type === "bpmn:Event";
}
export function validateFakeJoins(nodes, edges, lookupMaps) {
  if (!nodes || !edges) return [];
  const errors = [];
  const { edgesByTarget } = lookupMaps;
  for (const node of nodes) {
    if (!isFrontendFakeJoinType(node.type)) continue;
    const incoming = (edgesByTarget.get(node.id) ?? []).filter((e) => !e.type || e.type === "bpmn:SequenceFlow");
    if (incoming.length > 1) {
      errors.push({
        code: "FAKE_JOIN",
        message: "Activities and events should not have multiple incoming flows.",
        severity: SEVERITY.ERROR,
        elementId: node.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 8: MessageFlowObjectsPoolRule
// ===========================================================================
function buildNodeToPoolMap(nodes, nodeById) {
  const map = new Map();
  for (const node of nodes) {
    let cur = node;
    while (cur) {
      if (cur.type === "bpmn:Participant") {
        map.set(node.id, cur.id);
        break;
      }
      if (!cur.parentId) break;
      const parent = nodeById.get(cur.parentId);
      if (!parent) break;
      cur = parent;
    }
  }
  return map;
}
export function validateMessageFlowCrossPool(nodes, edges, lookupMaps) {
  const errors = [];
  if (!nodes.some((n) => n.type === "bpmn:Participant")) return errors;
  const nodeToPool = buildNodeToPoolMap(nodes, lookupMaps.nodeById);
  for (const edge of edges) {
    if (edge.type !== "bpmn:MessageFlow") continue;
    const sp = nodeToPool.get(edge.source);
    const tp = nodeToPool.get(edge.target);
    if (sp && tp && sp === tp) {
      errors.push({
        code: "SAME_POOL_MESSAGE_FLOW",
        message: "Message flow cannot connect elements within the same pool.",
        severity: SEVERITY.ERROR,
        sourceId: edge.source,
        targetId: edge.target,
        elementId: edge.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 9: MissingResourceRule
// ===========================================================================
const SERVICE_TYPES_REQUIRING_RESOURCE = new Set([
  "Orchestrator.StartAgentJob",
  "Orchestrator.StartJob",
  "Orchestrator.CreateQueueItem",
  "Orchestrator.CreateAndWaitForQueueItem",
  "Orchestrator.ExecuteApiWorkflowAsync",
  "Actions.HITL",
  "Orchestrator.StartAgenticProcess",
  "Orchestrator.StartAgenticProcessAsync",
  "Orchestrator.StartCaseMgmtProcess",
  "Orchestrator.StartCaseMgmtProcessAsync",
]);
function hasResourceBinding(uipath) {
  if (!uipath?.context) return false;
  const releaseKey = uipath.context.find((c) => c.name === "releaseKey")?.value;
  if (releaseKey) return true;
  const name = uipath.context.find((c) => c.name === "name")?.value;
  return !!name;
}
export function validateMissingResource(nodes) {
  const errors = [];
  for (const node of nodes) {
    const uipath = node.data?.uipath;
    const serviceType = uipath?.serviceType;
    if (!serviceType || !SERVICE_TYPES_REQUIRING_RESOURCE.has(serviceType)) continue;
    if (hasResourceBinding(uipath)) continue;
    const label = node.data?.label || node.id;
    errors.push({
      code: "MISSING_RESOURCE",
      message: `Service task '${label}' has no bound resource.`,
      severity: SEVERITY.WARNING,
      elementId: node.id,
    });
  }
  return errors;
}

// ===========================================================================
// RULE 10: MissingRootVariableRule
// ===========================================================================
export function validateMissingRootVariables(nodes, canvasState) {
  const errors = [];
  const rootIds = new Set();
  const rv = canvasState.root?.data?.uipath?.variables;
  for (const v of rv?.inputOutputs ?? []) if (v.id) rootIds.add(v.id);
  for (const v of rv?.outputs ?? []) if (v.id) rootIds.add(v.id);

  const findNode = (id) => {
    for (const d of Object.values(canvasState.diagramsById)) {
      const n = d.nodes.find((x) => x.id === id);
      if (n) return n;
    }
    return undefined;
  };
  const collectNodeVarIds = (node) => {
    const ids = new Set();
    const nv = node.data?.uipath?.variables;
    for (const v of nv?.inputOutputs ?? []) if (v.id) ids.add(v.id);
    for (const v of nv?.outputs ?? []) if (v.id) ids.add(v.id);
    return ids;
  };
  const scopeIdsFor = (node) => {
    const result = new Set(rootIds);
    let cur = node;
    const visited = new Set();
    while (true) {
      const pe = cur?.data?.parentElement;
      if (pe?.type !== "bpmn:SubProcess" || visited.has(pe.id)) break;
      visited.add(pe.id);
      const spNode = findNode(pe.id);
      if (spNode) for (const id of collectNodeVarIds(spNode)) result.add(id);
      cur = spNode;
    }
    return result;
  };

  for (const node of nodes) {
    const outputs = node.data?.uipath?.outputs ?? [];
    if (!outputs.length) continue;
    const scopeIds = scopeIdsFor(node);
    const missing = outputs.some((o) => o.var && !scopeIds.has(o.var));
    if (missing) {
      errors.push({
        code: "MISSING_ROOT_VARIABLE",
        message: `Node '${node.data?.label ?? node.id}' references an output variable with no matching scope variable.`,
        severity: SEVERITY.WARNING,
        elementId: node.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 11: NoAssignmentsRule
// ===========================================================================
export function validateNoAssignmentsInExpressions(nodes, edges) {
  if (!nodes || !edges) return [];
  const errors = [];
  for (const edge of edges) {
    const expr = edge.data?.conditionExpression;
    if (expr && expressionHasAssignment(expr)) {
      errors.push({
        code: "ASSIGNMENT_NOT_ALLOWED",
        message: "Expression must not contain an assignment operator.",
        severity: SEVERITY.WARNING,
        elementId: edge.id,
        sourceId: edge.source,
        targetId: edge.target,
      });
    }
  }
  for (const node of nodes) {
    const mappings = node.data?.uipath?.errorMapping;
    if (!Array.isArray(mappings)) continue;
    for (const m of mappings) {
      if (m?.condition && expressionHasAssignment(m.condition)) {
        errors.push({
          code: "ASSIGNMENT_NOT_ALLOWED",
          message: "Error-mapping condition must not contain an assignment operator.",
          severity: SEVERITY.WARNING,
          elementId: node.id,
        });
      }
    }
  }
  return errors;
}

// ===========================================================================
// RULE 12: RequiredFieldsRule  (sourced from bpmn-spec.json registry metadata)
// ===========================================================================
// Faithful port of ValidateRequiredFieldsInData.findRequiredFieldErrorInData:
//   for each field in context, then inputs, then outputs (frontend order),
//   if (field.required && isNilOrEmpty(field.value)) → first error.
//
// On canvas, EVERY field a serviceType declares is present in the node data with
// its `required` flag set; an unbound required field is present-with-empty-value
// and the frontend fires on it. In exported BPMN an unbound required field is
// simply ABSENT. To reach parity, we treat an absent required field exactly as
// the frontend treats an unbound one: present with an empty value. The required-
// field names come from the bundled registry (bpmn-spec.json) per serviceType
// (model.mjs attaches them as `uipath.requiredFieldNames`).
//
// BOUNDARY: For dynamic IS-connector activity types whose required-ness is NOT
// in the static spec — it only materializes after a `registry get` enrichment —
// `requiredFieldNames` is undefined and absence cannot be judged offline, so we
// stay conservative (only present-but-empty fires). The frontend needs the same
// enrichment to know those fields are required, so this is shared, not a gap.
export function validateRequiredFields(nodes) {
  if (!nodes) return []; // frontend RequiredFieldsRule guards null inputs
  const errors = [];
  for (const node of nodes) {
    const uipath = node.data?.uipath;
    if (!uipath) continue;
    // First (frontend order): present fields flagged when required + empty value.
    const firstEmptyPresent = (fields) => {
      if (!Array.isArray(fields)) return undefined;
      for (const field of fields) {
        if (field.required && isNilOrEmpty(field.value)) return field;
      }
      return undefined;
    };
    let badName;
    const present = firstEmptyPresent(uipath.context) ?? firstEmptyPresent(uipath.inputs) ?? firstEmptyPresent(uipath.outputs);
    if (present) badName = present.name;
    else if (Array.isArray(uipath.requiredFieldNames)) {
      // No present-but-empty required field; check for an entirely ABSENT one
      // (treated by the frontend as present-with-empty, hence required+empty).
      const presentNames = new Set();
      for (const group of [uipath.context, uipath.inputs, uipath.outputs]) {
        if (!Array.isArray(group)) continue;
        for (const f of group) if (f.name) presentNames.add(f.name);
      }
      const absent = uipath.requiredFieldNames.find((name) => !presentNames.has(name));
      if (absent) badName = absent;
    }
    if (badName !== undefined) {
      const label = node.data?.label ?? node.id;
      errors.push({
        code: "EMPTY_REQUIRED_FIELD",
        message: `The field '${badName}' in node '${label}' is required but has no value.`,
        severity: SEVERITY.ERROR,
        elementId: node.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 13: SequenceFlowPoolCrossingRule
// ===========================================================================
export function validateSequenceFlowPoolCrossing(nodes, edges, lookupMaps) {
  const errors = [];
  if (!nodes.some((n) => n.type === "bpmn:Participant")) return errors;
  const nodeById = lookupMaps.nodeById;
  const nodeToPool = buildNodeToPoolMap(nodes, nodeById);
  for (const edge of edges) {
    if (edge.type !== "bpmn:SequenceFlow") continue;
    const sp = nodeToPool.get(edge.source);
    const tp = nodeToPool.get(edge.target);
    const targetNode = nodeById.get(edge.target);
    if (sp !== tp && targetNode?.type !== "bpmn:StartEvent") {
      errors.push({
        code: "CROSSING_POOL_BOUNDARY",
        message: "Sequence flow cannot cross pool boundaries.",
        severity: SEVERITY.ERROR,
        sourceId: edge.source,
        targetId: edge.target,
        elementId: edge.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 14: SequenceFlowSubProcessCrossingRule
// ===========================================================================
function getLogicalParent(node, nodeMap) {
  const actualParent = node.parentId ? nodeMap.get(node.parentId) : undefined;
  if (node.type === "bpmn:BoundaryEvent") {
    const attachedToId = node.data?.attachedToId;
    const attachedTo = attachedToId ? nodeMap.get(attachedToId) : undefined;
    if (attachedTo) return attachedTo.parentId ? nodeMap.get(attachedTo.parentId) : undefined;
  }
  return actualParent;
}
export function validateSequenceFlowSubProcessCrossing(_nodes, edges, lookupMaps) {
  const errors = [];
  const nodeMap = lookupMaps.nodeById;
  for (const edge of edges) {
    if (edge.type !== "bpmn:SequenceFlow") continue;
    const sourceNode = nodeMap.get(edge.source);
    const targetNode = nodeMap.get(edge.target);
    if (!sourceNode || !targetNode) continue;
    const sp = getLogicalParent(sourceNode, nodeMap);
    const tp = getLogicalParent(targetNode, nodeMap);
    if ((sp?.type === "bpmn:SubProcess" || tp?.type === "bpmn:SubProcess") && sp?.id !== tp?.id) {
      errors.push({
        code: "CROSSING_SUBPROCESS_BOUNDARY",
        message: "Sequence flow cannot cross sub-process boundaries.",
        severity: SEVERITY.ERROR,
        sourceId: edge.source,
        targetId: edge.target,
        elementId: edge.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 15: SingleBlankStartEventRule
// ===========================================================================
export function validateSingleBlankStartEvent(nodes, edges, lookupMaps) {
  if (!nodes || !edges) return [];
  const errors = [];
  const { nodesByParentId } = lookupMaps;
  const isBlankStart = (n) => n.type === "bpmn:StartEvent" && !n.data?.eventDefinition;
  const containers = nodes.filter((n) => n.type === "bpmn:Process" || n.type === "bpmn:SubProcess");
  for (const container of containers) {
    const scopeNodes = container.type === "bpmn:Process" ? (nodesByParentId.get(undefined) ?? []) : (nodesByParentId.get(container.id) ?? []);
    const blanks = scopeNodes.filter(isBlankStart);
    if (blanks.length > 1) {
      const type = container.type === "bpmn:SubProcess" ? "Sub-process" : "Process";
      errors.push({
        code: "MULTIPLE_BLANK_START_EVENTS",
        message: `${type} should have at most one blank start event.`,
        severity: SEVERITY.ERROR,
        elementId: container.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 16: SingleStartEventInEventSubProcessRule
// ===========================================================================
export function validateSingleStartEventInEventSubProcess(nodes, _edges, lookupMaps) {
  const errors = [];
  const { nodesByParentId } = lookupMaps;
  for (const node of nodes) {
    if (!(node.type === "bpmn:SubProcess" && node.data?.triggeredByEvent === true)) continue;
    const children = nodesByParentId.get(node.id) ?? [];
    const starts = children.filter((c) => c.type === "bpmn:StartEvent");
    if (starts.length > 1) {
      errors.push({
        code: "MULTIPLE_START_EVENTS_IN_EVENT_SUBPROCESS",
        message: "Event sub-process can have only one start event.",
        severity: SEVERITY.ERROR,
        elementId: node.id,
        sourceId: node.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 17: SuperfluousGatewayRule
// ===========================================================================
export function validateSuperfluousGateway(nodes, edges, lookupMaps) {
  if (!nodes || !edges) return [];
  const errors = [];
  const { edgesBySource, edgesByTarget } = lookupMaps;
  const isGateway = (t) => t === "bpmn:ExclusiveGateway" || t === "bpmn:ParallelGateway" || t === "bpmn:InclusiveGateway";
  for (const node of nodes) {
    if (!isGateway(node.type)) continue;
    const incoming = edgesByTarget.get(node.id) ?? [];
    const outgoing = edgesBySource.get(node.id) ?? [];
    if (incoming.length === 1 && outgoing.length === 1) {
      errors.push({
        code: "SUPERFLUOUS_GATEWAY",
        message: "Gateway should have at least two sources or targets.",
        severity: SEVERITY.ERROR,
        elementId: node.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 18: TaskTimerRule
// ===========================================================================
const MIN_TIMER_MINUTES = 15;
const MAX_TIMER_MINUTES = 90 * 24 * 60;
function isTimerValueOutOfRange(value) {
  if (value == null || value === "") return false;
  const str = String(value);
  if (str.startsWith("@") || str.startsWith("=")) return false;
  const minutes = Number(str);
  if (Number.isNaN(minutes)) return false;
  return minutes < MIN_TIMER_MINUTES || minutes > MAX_TIMER_MINUTES;
}
export function validateTaskTimerRange(nodes) {
  if (!nodes) return [];
  const errors = [];
  for (const node of nodes) {
    const uipath = node.data?.uipath;
    if (uipath?.serviceType !== "actions") continue;
    const timer = uipath.context?.find((c) => c.name === "Timer");
    if (timer?.value == null || timer.value === "") continue;
    if (isTimerValueOutOfRange(timer.value)) {
      errors.push({
        code: "TASK_TIMER_OUT_OF_RANGE",
        message: `Task timer for '${node.data?.label ?? node.id}' must be between 15 minutes and 90 days.`,
        severity: SEVERITY.WARNING,
        elementId: node.id,
      });
    }
  }
  return errors;
}

// ===========================================================================
// RULE 19: TimerDurationRule
// ===========================================================================
export function validateTimerDuration(nodes) {
  if (!nodes) return [];
  const errors = [];
  for (const node of nodes) {
    const ed = node.data?.eventDefinition;
    if (ed?.timerType !== "timeDuration") continue;
    const value = ed.timeDuration;
    if (!value) continue;
    if (value.startsWith("=") || value.startsWith("@")) continue;
    const label = node.data?.label ?? node.id;
    if (!isValidIso8601(value)) {
      errors.push({
        code: "TIMER_DURATION_INVALID",
        message: `Timer duration '${value}' on '${label}' is not a valid ISO 8601 duration.`,
        severity: SEVERITY.ERROR,
        elementId: node.id,
      });
      continue;
    }
    if (hasIso8601WeekDesignator(value)) {
      errors.push({
        code: "TIMER_DURATION_WEEK_UNSUPPORTED",
        message: `Timer duration '${value}' on '${label}' uses the unsupported week (W) designator.`,
        severity: SEVERITY.WARNING,
        elementId: node.id,
      });
    }
  }
  return errors;
}

// ---------------------------------------------------------------------------
// Variable-existence check across all nodes & edges of the whole model.
// Port of VariableUtil.validateVariablesInAllNodesAndEdges (the existence half).
// `knownIds` is built from variable ids AND names AND canonicalIds (model.mjs).
// ---------------------------------------------------------------------------
export function validateVariableExistence(allNodes, allEdges, knownIds) {
  const errors = [];
  const flag = (expr, elementId, resultIds, extra = {}) => {
    const unknown = findUnknownVariableRefs(expr, knownIds, resultIds);
    for (const ref of unknown) {
      errors.push({
        code: "VARIABLE_DOES_NOT_EXIST",
        message: `Variable reference '${ref}' does not resolve to a declared variable.`,
        severity: SEVERITY.ERROR,
        elementId,
        ...extra,
      });
    }
  };
  // Edge conditions have no element-local outputs → result.X never resolves.
  for (const edge of allEdges) {
    if (edge.data?.conditionExpression) {
      flag(edge.data.conditionExpression, edge.id, new Set(), { sourceId: edge.source, targetId: edge.target });
    }
  }
  for (const node of allNodes) {
    const uipath = node.data?.uipath;
    if (!uipath) continue;
    // result.X is validated against THIS element's own output identifiers
    // (var/name/canonicalId), per VariableUtil.isResultVariableValidForElement.
    const resultIds = new Set();
    for (const o of uipath.outputs ?? []) {
      if (o.var) resultIds.add(o.var);
      if (o.name) resultIds.add(o.name);
      if (o.canonicalId) resultIds.add(o.canonicalId);
    }
    const exprs = [];
    for (const c of uipath.context ?? []) {
      if (typeof c.value === "string") exprs.push(c.value);
      if (typeof c.body === "string") exprs.push(c.body);
    }
    for (const i of uipath.inputs ?? []) {
      if (typeof i.value === "string") exprs.push(i.value);
      if (typeof i.body === "string") exprs.push(i.body);
    }
    // Custom-output expressions: gate the field by accessor type, mirroring
    // VariableUtil.ts:952-968 (source only when accessor is `source`, body only
    // when accessor is `body`).
    for (const o of uipath.outputs ?? []) {
      if (!o.custom) continue;
      const accessor = getAccessorFromType(o.type);
      if (accessor === "source" && typeof o.source === "string") exprs.push(o.source);
      else if (accessor === "body" && typeof o.body === "string") exprs.push(o.body);
    }
    for (const m of uipath.errorMapping ?? []) {
      if (typeof m.condition === "string") exprs.push(m.condition);
    }
    for (const expr of exprs) flag(expr, node.id, resultIds);
  }
  return errors;
}

// ---------------------------------------------------------------------------
// VARIABLE_NOT_SET — port of the flow-reachability half of
// VariableUtil.validateVariablesInExpression (VariableUtil.ts:758-866).
//
// A variable can be DECLARED (exists in the known-id set) yet NOT SET at a given
// element because no flow path reaches that element from the node that produces
// it. The frontend computes, per element, the set of variables available via a
// backward walk over sequence-flow edges (+ scope/parent chain, boundary
// re-parenting, event-subprocess shared scope, subprocess EndEvent exposure),
// then warns on every referenced+declared variable not in that set.
//
// Faithful port of:
//   getSourceEdgeMappings              (VariableUtil.ts:121-130)
//   mapNodeOutputsToVariables          (VariableUtil.ts:539-579, uipath outputs)
//   getVariablesForSubProcess          (VariableUtil.ts:495-525)
//   getAvailableVariablesFromSourceNodes (VariableUtil.ts:303-389)
//   getAvailableVariablesForElement    (VariableUtil.ts:401-481)
// Skipped entirely for Case Management (VariableUtil.ts:826-828).
// ---------------------------------------------------------------------------

// A node output declares a variable whose identifier is `var` (falling back to
// `value` when shouldIdFallbackToValue, per the frontend mapNodeOutputsToVariables).
// Returns id + canonicalId + name. The frontend's availability match keys on
// id/canonicalId; this port additionally includes `name`, consistent with the
// rest of the port's variable resolution (collectKnownVariableIds /
// findUnknownVariableRefs resolve by id AND name AND canonicalId), because
// exported BPMN expressions may reference a variable by its serialized name.
function nodeOutputVariableIds(node, idFallbackToValue) {
  const ids = [];
  for (const o of node?.data?.uipath?.outputs ?? []) {
    const id = o.var ?? (idFallbackToValue ? (o.value ?? "") : "");
    if (id) ids.push(id);
    if (o.canonicalId) ids.push(o.canonicalId);
    if (o.name) ids.push(o.name);
  }
  return ids;
}

// Port of getVariablesForSubProcess: the variables a subprocess EXPOSES to a
// sibling selection (the subprocess node's own outputs + its EndEvent children's
// outputs). `isSelfSelected` is always false here (the selection is never the
// subprocess being traversed past), matching the edge-traversal path.
function subProcessExposedVarIds(subProcessId, nodes) {
  const ids = [];
  for (const node of nodes) {
    const outs = nodeOutputVariableIds(node, false);
    if (!outs.length) continue;
    if (node.id === subProcessId) {
      for (const i of outs) ids.push(i);
      continue;
    }
    if (node.parentId === subProcessId || node.data?.parentElement?.id === subProcessId) {
      if (node.type === "bpmn:EndEvent") for (const i of outs) ids.push(i);
    }
  }
  return ids;
}

// Backward BFS over sequence-flow edges from `selectionElementId`, collecting
// every available variable id. Port of getAvailableVariablesFromSourceNodes.
function availableVarIdsFromSourceNodes(selectionElementId, selectionElementType, nodes, edges, rootVarIds, nodeById) {
  const edgeToSource = new Map();
  const sourceToEdges = new Map();
  for (const edge of edges) {
    edgeToSource.set(edge.id, edge.source);
    const arr = sourceToEdges.get(edge.target) ?? [];
    arr.push(edge.id);
    sourceToEdges.set(edge.target, arr);
  }

  const available = new Set(rootVarIds); // root variables are globally available
  const visitedEdges = new Set();

  // The selected element's own outputs are available.
  const selected = nodeById.get(selectionElementId);
  if (selected) for (const i of nodeOutputVariableIds(selected, true)) available.add(i);

  const edgesToVisit = [];
  let currentEdgeId = selectionElementId;
  if (selectionElementType === "node") {
    edgesToVisit.push(...(sourceToEdges.get(selectionElementId) ?? []));
    currentEdgeId = edgesToVisit.shift();
  }

  while (currentEdgeId) {
    let sourceNode = nodeById.get(edgeToSource.get(currentEdgeId) ?? "");
    // Boundary events have no incoming edge; re-parent to their host.
    if (sourceNode?.type === "bpmn:BoundaryEvent" && sourceNode?.id) {
      const parentId = sourceNode.parentId;
      sourceNode = parentId ? nodeById.get(parentId) : undefined;
    }
    if (sourceNode?.type !== "bpmn:SubProcess" && sourceNode?.id) {
      for (const i of nodeOutputVariableIds(sourceNode, true)) available.add(i);
    }
    if (sourceNode?.type === "bpmn:SubProcess" && sourceNode?.id) {
      for (const i of subProcessExposedVarIds(sourceNode.id, nodes)) available.add(i);
    }
    visitedEdges.add(currentEdgeId);

    let nextEdge = sourceToEdges.get(sourceNode?.id ?? "");
    if (!nextEdge && sourceNode?.parentId) {
      const sourceParent = nodeById.get(sourceNode.parentId);
      if (sourceParent?.type === "bpmn:SubProcess") nextEdge = sourceToEdges.get(sourceParent.id);
    }
    edgesToVisit.push(...(nextEdge ?? []).filter((e) => !visitedEdges.has(e)));
    currentEdgeId = edgesToVisit.shift();
  }
  return available;
}

// Port of getAvailableVariablesForElement: source-node BFS + subprocess scope +
// parent chain (with event-subprocess shared-scope handling).
function availableVarIdsForElement(selectionElementId, selectionElementType, nodes, edges, rootVarIds, nodeById) {
  const available = availableVarIdsFromSourceNodes(selectionElementId, selectionElementType, nodes, edges, rootVarIds, nodeById);

  const selected = nodeById.get(selectionElementId);
  if (selected?.type === "bpmn:SubProcess") {
    // Self-selected: expose all child variables.
    for (const node of nodes) {
      if (node.parentId === selectionElementId || node.data?.parentElement?.id === selectionElementId) {
        for (const i of nodeOutputVariableIds(node, false)) available.add(i);
      }
    }
  }

  let parentElementId = selected?.data?.parentElement?.id;
  if (!parentElementId) return available;

  const visitedParentIds = new Set();
  while (parentElementId && !visitedParentIds.has(parentElementId)) {
    visitedParentIds.add(parentElementId);
    const parentNode = nodeById.get(parentElementId);
    if (!parentNode) break;

    const isParentEventSubprocess = parentNode.type === "bpmn:SubProcess" && parentNode.data?.triggeredByEvent === true;
    if (isParentEventSubprocess) {
      const grandparentNodeId = parentNode.data?.parentElement?.id;
      if (!grandparentNodeId) break;
      for (const node of nodes) {
        const nodeScope = node.data?.parentElement?.id;
        if (nodeScope === grandparentNodeId && node.id !== parentElementId) {
          if (node.type === "bpmn:SubProcess") {
            for (const i of subProcessExposedVarIds(node.id, nodes)) available.add(i);
          } else {
            for (const i of nodeOutputVariableIds(node, true)) available.add(i);
          }
        }
      }
      parentElementId = grandparentNodeId;
      continue;
    }

    for (const i of availableVarIdsFromSourceNodes(parentElementId, "node", nodes, edges, rootVarIds, nodeById)) available.add(i);
    parentElementId = parentNode.data?.parentElement?.id;
  }
  return available;
}

// Collect the `vars.X` identifiers in an expression that are DECLARED (resolve
// against the model's known ids) — these are the candidates for VARIABLE_NOT_SET.
function declaredVarRefsInExpression(expression, knownIds) {
  if (!expression) return [];
  const out = new Set();
  for (const match of expression.matchAll(VAR_REFS_REGEX)) {
    const prefix = match[2];
    if (prefix !== "vars") continue;
    const seg = match[3] ?? match[4];
    if (!seg || BUILTIN_NON_VARIABLE_VARS_SEGMENTS.has(seg)) continue;
    let resolvedId;
    if (knownIds.has(seg)) resolvedId = seg;
    else {
      for (const id of knownIds) {
        if (seg.startsWith(`${id}.`)) {
          resolvedId = id;
          break;
        }
      }
    }
    if (resolvedId) out.add(resolvedId);
  }
  return [...out];
}

// `varExpressionsForElement` mirrors getInputExpressions + the output accessor
// gate used by the frontend node loop (VariableUtil.ts:949-971).
function varExpressionsForNode(uipath) {
  const exprs = [];
  for (const c of uipath.context ?? []) {
    if (typeof c.value === "string") exprs.push(c.value);
    if (typeof c.body === "string") exprs.push(c.body);
  }
  for (const i of uipath.inputs ?? []) {
    if (typeof i.value === "string") exprs.push(i.value);
    if (typeof i.body === "string") exprs.push(i.body);
  }
  for (const o of uipath.outputs ?? []) {
    if (!o.custom) continue;
    const accessor = getAccessorFromType(o.type);
    if (accessor === "source" && typeof o.source === "string") exprs.push(o.source);
    else if (accessor === "body" && typeof o.body === "string") exprs.push(o.body);
  }
  return exprs;
}

// Emit VARIABLE_NOT_SET (WARNING) for declared variables referenced at an
// element that are not reachable in flow order. Skipped for Case Management.
export function validateVariableNotSet(allNodes, allEdges, knownIds, canvasState, options = {}) {
  if (options.isCaseManagement) return []; // frontend skips (VariableUtil.ts:826-828)
  const errors = [];
  const nodeById = new Map(allNodes.map((n) => [n.id, n]));

  // Root variable identifiers (id + canonicalId + name) — globally available.
  // `name` included for the same port-consistency reason as nodeOutputVariableIds.
  const rootVarIds = [];
  const rv = canvasState?.root?.data?.uipath?.variables;
  for (const v of [...(rv?.inputs ?? []), ...(rv?.inputOutputs ?? [])]) {
    if (v.id) rootVarIds.push(v.id);
    if (v.canonicalId) rootVarIds.push(v.canonicalId);
    if (v.name) rootVarIds.push(v.name);
  }

  const check = (elementId, elementType, expression) => {
    const declared = declaredVarRefsInExpression(expression, knownIds);
    if (!declared.length) return;
    const available = availableVarIdsForElement(elementId, elementType, allNodes, allEdges, rootVarIds, nodeById);
    for (const ref of declared) {
      if (!available.has(ref)) {
        errors.push({
          code: "VARIABLE_NOT_SET",
          message: `Variable '${ref}' is not set at this point in the flow.`,
          severity: SEVERITY.WARNING,
          elementId,
        });
      }
    }
  };

  for (const edge of allEdges) {
    if (typeof edge.data?.conditionExpression === "string") check(edge.id, "edge", edge.data.conditionExpression);
  }
  for (const node of allNodes) {
    const uipath = node.data?.uipath;
    if (!uipath) continue;
    const expr = varExpressionsForNode(uipath).join(" ; ");
    if (expr) check(node.id, "node", expr);
  }
  return errors;
}

// ---------------------------------------------------------------------------
// Orchestrator: run every rule against one diagram's CanvasState. Mirrors the
// per-diagram loop in ValidateBpmnFlowUtils.validateBpmnFlow.
// ---------------------------------------------------------------------------
export function validateDiagram(diagram, canvasState, options = {}) {
  const nodes = diagram.nodes;
  const edges = diagram.edges;
  const lm = buildValidationLookupMaps(nodes, edges);
  const errors = [];
  errors.push(...validateConnections(nodes, edges, lm));
  errors.push(...validateMessageFlowCrossPool(nodes, edges, lm));
  errors.push(...validateSequenceFlowSubProcessCrossing(nodes, edges, lm));
  errors.push(...validateSequenceFlowPoolCrossing(nodes, edges, lm));
  errors.push(...validateConditionalSequenceFlow(nodes, edges, lm));
  errors.push(...validateSuperfluousGateway(nodes, edges, lm));
  errors.push(...validateFakeJoins(nodes, edges, lm));
  errors.push(...validateSingleBlankStartEvent(nodes, edges, lm));
  errors.push(...validateEventSubProcessStart(nodes, edges, lm));
  errors.push(...validateSingleStartEventInEventSubProcess(nodes, edges, lm));
  errors.push(...validateErrorBoundaryEvents(nodes, canvasState));
  errors.push(...validateDuplicateErrorBoundaryEvents(nodes, canvasState));
  errors.push(...validateErrorEndEvents(nodes));
  errors.push(...validateDuplicateErrorEventSubprocess(nodes, canvasState, lm));
  errors.push(...validateRequiredFields(nodes));
  errors.push(...validateMissingResource(nodes));
  errors.push(...validateNoAssignmentsInExpressions(nodes, edges));
  if (options.enableMissingRootVariableValidation) {
    errors.push(...validateMissingRootVariables(nodes, canvasState));
  }
  errors.push(...validateTaskTimerRange(nodes));
  errors.push(...validateTimerDuration(nodes));
  return errors;
}

export const RULE_CODES = [
  "MISSING_CONDITION_EXPRESSION",
  "INVALID_CONNECTION",
  "INVALID_CONNECTION_TYPE",
  "DUPLICATE_ERROR_EVENT_SUBPROCESS",
  "MULTIPLE_CATCH_ALL_ERROR_EVENT_SUBPROCESS",
  "START_EVENT_WITHOUT_DEFINITION_IN_EVENT_SUBPROCESS",
  "INVALID_EVENT_DEFINITION_IN_EVENT_SUBPROCESS",
  "START_EVENT_WITH_DEFINITION_IN_SUBPROCESS",
  "ERROR_BOUNDARY_EVENT_EMPTY_ERROR_REF",
  "ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE",
  "MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK",
  "DUPLICATE_ERROR_BOUNDARY_EVENT_ON_TASK",
  "ERROR_END_EVENT_MISSING_EXCEPTION",
  "FAKE_JOIN",
  "SAME_POOL_MESSAGE_FLOW",
  "MISSING_RESOURCE",
  "MISSING_ROOT_VARIABLE",
  "ASSIGNMENT_NOT_ALLOWED",
  "EMPTY_REQUIRED_FIELD",
  "CROSSING_POOL_BOUNDARY",
  "CROSSING_SUBPROCESS_BOUNDARY",
  "MULTIPLE_BLANK_START_EVENTS",
  "MULTIPLE_START_EVENTS_IN_EVENT_SUBPROCESS",
  "SUPERFLUOUS_GATEWAY",
  "TASK_TIMER_OUT_OF_RANGE",
  "TIMER_DURATION_INVALID",
  "TIMER_DURATION_WEEK_UNSUPPORTED",
  "VARIABLE_DOES_NOT_EXIST",
  "VARIABLE_NOT_SET",
];
