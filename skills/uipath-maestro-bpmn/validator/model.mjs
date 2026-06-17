// Reconstruct the PO.Frontend Node[]/Edge[]/CanvasState model from a parsed
// bpmn-moddle tree. This is the integration layer (Phase 1). It mirrors
// PO.Frontend/src/services/serialization/bpmn-from-xml.ts closely enough that
// the ported rule engine in rules.mjs sees the same fields it sees on canvas.
//
// PHASE 2 NOTE: this file and validate-bpmn.mjs are the only integration glue.
// rules.mjs (the rule logic) is the swap target for the future npm package.

import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// Registry: required-field metadata (bpmn-spec.json). Bundled so RequiredFields
// runs fully offline. Maps serviceType -> Set<requiredFieldName>.
// ---------------------------------------------------------------------------
let _requiredFieldIndex;
function loadRequiredFieldIndex() {
  if (_requiredFieldIndex) return _requiredFieldIndex;
  const index = new Map();
  try {
    const spec = JSON.parse(readFileSync(join(__dirname, "bpmn-spec.json"), "utf8"));
    for (const [serviceType, def] of Object.entries(spec.extensionTypes ?? {})) {
      const names = new Set();
      for (const f of def.contextFields ?? []) {
        // Only fields the user can actually populate. Hidden fields with a
        // default are auto-filled by the designer and never empty in practice,
        // so requiring them offline would false-positive; skip hidden+defaulted.
        if (f.required && !(f.hidden && f.defaultValue !== null && f.defaultValue !== undefined)) {
          names.add(f.name);
        }
      }
      for (const f of def.inputFields ?? []) {
        if (f.required) names.add(f.name);
      }
      if (names.size) index.set(serviceType, names);
    }
  } catch {
    // Registry not bundled: RequiredFields degrades to a no-op (documented).
  }
  _requiredFieldIndex = index;
  return index;
}

// ---------------------------------------------------------------------------
// moddle helpers
// ---------------------------------------------------------------------------
const ext = (el) => el?.extensionElements?.values ?? [];
const findExt = (el, type) => ext(el).find((e) => e.$type === type);

function eventDefinitionOf(el) {
  const defs = el?.eventDefinitions;
  if (!defs || !defs.length) return undefined;
  const d = defs[0];
  const out = { type: d.$type, id: d.id };
  if (d.errorRef) out.errorRef = d.errorRef.id ?? d.errorRef;
  if (d.messageRef) out.messageRef = d.messageRef.id ?? d.messageRef;
  if (d.signalRef) out.signalRef = d.signalRef.id ?? d.signalRef;
  if (d.escalationRef) out.escalationRef = d.escalationRef.id ?? d.escalationRef;
  if (d.$type === "bpmn:TimerEventDefinition") {
    if (d.timeDuration) {
      out.timerType = "timeDuration";
      out.timeDuration = d.timeDuration.body ?? d.timeDuration;
    } else if (d.timeCycle) {
      out.timerType = "timeCycle";
      out.timeCycle = d.timeCycle.body ?? d.timeCycle;
    } else if (d.timeDate) {
      out.timerType = "timeDate";
      out.timeDate = d.timeDate.body ?? d.timeDate;
    }
  }
  return out;
}

// Map a uipath:Activity / uipath:Event extension element into the frontend
// `node.data.uipath` shape consumed by the rules.
function mapUiPathActivity(actEl) {
  const uipath = {};
  uipath.serviceType = actEl.type?.value ?? actEl.type ?? undefined;
  uipath.version = actEl.type?.version ?? actEl.version ?? "v1";

  const mapInput = (i) => ({ name: i.name, type: i.type, subType: i.subType, value: i.value, target: i.target, body: i.body });
  const mapOutput = (o) => ({
    name: o.name,
    type: o.type,
    subType: o.subType,
    source: o.source,
    var: o.var,
    body: o.body,
    custom: o.custom === "true" || o.custom === true,
    target: o.target,
  });

  uipath.context = (actEl.context?.input ?? []).map(mapInput);
  uipath.inputs = (actEl.input ?? []).map(mapInput);
  uipath.outputs = (actEl.output ?? []).map(mapOutput);
  return uipath;
}

function mapErrorMapping(emEl) {
  return (emEl?.error ?? []).map((e) => ({
    id: e.id,
    errorRef: e.errorRef,
    priority: e.priority,
    condition: e.condition,
    detail: e.detail,
    retryable: e.retryable === "true" || e.retryable === true,
  }));
}

function mapVariables(varsEl) {
  if (!varsEl) return undefined;
  const map = (v) => ({
    id: v.id,
    name: v.name,
    type: v.type,
    subType: v.subType,
    canonicalId: v.canonicalId,
    elementId: v.elementId,
    default: v.default,
  });
  return {
    inputs: (varsEl.input ?? []).map(map),
    inputOutputs: (varsEl.inputOutput ?? []).map(map),
    outputs: (varsEl.output ?? []).map(map),
  };
}

// Populate node.data.uipath from a flow element's extensionElements.
// `requiredFieldIndex` supplies, per serviceType, the registry's required field
// names; matching serialized fields get `required: true` so RequiredFields can
// run offline with the same `field.required && isNilOrEmpty(value)` semantics
// the canvas uses.
function buildNodeUiPath(el, requiredFieldIndex) {
  // Script tasks / BPMN.Variables nodes carry their IO under uipath:Mapping,
  // which has the same { type, context, input, output } shape as
  // uipath:Activity / uipath:Event. Treat all three uniformly so node-output
  // variables (e.g. a script writing `var="x"`) are recovered.
  const act = findExt(el, "uipath:Activity") ?? findExt(el, "uipath:Event") ?? findExt(el, "uipath:Mapping");
  const em = findExt(el, "uipath:ErrorMapping");
  const vars = findExt(el, "uipath:Variables");
  let uipath;
  if (act) uipath = mapUiPathActivity(act);
  if (em) {
    uipath = uipath ?? {};
    uipath.errorMapping = mapErrorMapping(em);
  }
  if (vars) {
    uipath = uipath ?? {};
    uipath.variables = mapVariables(vars);
  }
  // Mark required fields from the registry onto serialized fields by name match,
  // and attach the full required-name set so RequiredFieldsRule can also detect
  // required fields that are entirely ABSENT from the serialized data (frontend
  // RequiredFieldsRule iterates every field in the node's data and fires on
  // `field.required && isNilOrEmpty(field.value)` — an unbound required field is
  // present-with-empty-value on canvas, which corresponds to absent-in-XML here).
  const st = uipath?.serviceType;
  const requiredNames = st ? requiredFieldIndex.get(st) : undefined;
  if (requiredNames) {
    for (const group of [uipath.context, uipath.inputs, uipath.outputs]) {
      if (!Array.isArray(group)) continue;
      for (const f of group) if (requiredNames.has(f.name)) f.required = true;
    }
    uipath.requiredFieldNames = [...requiredNames];
  }
  return uipath;
}

const ABSTRACT_ACTIVITY = new Set([
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
  "bpmn:AdHocSubProcess",
  "bpmn:Transaction",
]);
const ABSTRACT_EVENT = new Set([
  "bpmn:StartEvent",
  "bpmn:EndEvent",
  "bpmn:IntermediateCatchEvent",
  "bpmn:IntermediateThrowEvent",
  "bpmn:BoundaryEvent",
]);
function abstractTypeOf(type) {
  if (ABSTRACT_ACTIVITY.has(type)) return "bpmn:Activity";
  if (ABSTRACT_EVENT.has(type)) return "bpmn:Event";
  return undefined;
}

// ---------------------------------------------------------------------------
// Build a flat Node for one flow element. `parentId`/`parentElement` describe
// the containing Process or SubProcess.
// ---------------------------------------------------------------------------
function buildNode(el, parent, requiredFieldIndex) {
  const data = {};
  data.label = el.name ?? undefined;

  const ed = eventDefinitionOf(el);
  if (ed) data.eventDefinition = ed;

  if (el.$type === "bpmn:SubProcess") data.triggeredByEvent = el.triggeredByEvent === true;
  if (el.$type === "bpmn:BoundaryEvent" && el.attachedToRef) data.attachedToId = el.attachedToRef.id ?? el.attachedToRef;

  const uipath = buildNodeUiPath(el, requiredFieldIndex);
  if (uipath) data.uipath = uipath;

  if (parent) data.parentElement = { id: parent.id, type: parent.$type };

  return {
    id: el.id,
    type: el.$type,
    parentId: parent && parent.$type === "bpmn:SubProcess" ? parent.id : undefined,
    abstractType: abstractTypeOf(el.$type),
    data,
  };
}

function buildEdge(el, parent) {
  const data = {};
  if (el.name) data.label = el.name;
  if (el.conditionExpression) {
    // A FormalExpression moddle element carries its text in `.body`; an empty
    // `<conditionExpression/>` element has no `.body` (undefined). Only a real
    // string body is a condition — never fall back to the moddle object itself,
    // which would crash the string-based rules (matches frontend: an empty
    // conditionExpression element means "no condition expression").
    let body = el.conditionExpression.body ?? el.conditionExpression;
    if (typeof body === "string") {
      if (body && !body.startsWith("=")) body = `=${body}`;
      data.conditionExpression = body;
    }
  }
  // defaultFlow: source gateway's @default points to this flow.
  const source = el.sourceRef;
  if (source?.default && (source.default.id ?? source.default) === el.id) data.defaultFlow = true;
  if (parent) data.parentElement = { id: parent.id, type: parent.$type };
  return {
    id: el.id,
    type: el.$type,
    source: el.sourceRef?.id ?? el.sourceRef,
    target: el.targetRef?.id ?? el.targetRef,
    data,
  };
}

const FLOW_EDGE_TYPES = new Set(["bpmn:SequenceFlow", "bpmn:MessageFlow", "bpmn:Association"]);

// Recursively collect nodes & edges for one container (Process or SubProcess).
// `rootParentId` is the parentId assigned to the container's direct flow nodes:
//   undefined for a stand-alone process (frontend root scope), or the pool id
//   when the process is contained in a collaboration participant. Sub-process
//   children carry parentId = sub-process id (frontend behavior).
function collectContainer(container, requiredFieldIndex, nodesOut, edgesOut, rootParentId) {
  const flowElements = container.flowElements ?? [];
  for (const el of flowElements) {
    if (FLOW_EDGE_TYPES.has(el.$type)) {
      edgesOut.push(buildEdge(el, container));
      continue;
    }
    const node = buildNode(el, container, requiredFieldIndex);
    // Override parentId for direct children of a Process container.
    if (container.$type === "bpmn:Process") node.parentId = rootParentId;
    nodesOut.push(node);
    if (el.$type === "bpmn:SubProcess") {
      collectContainer(el, requiredFieldIndex, nodesOut, edgesOut, rootParentId);
    }
  }
}

function buildRootUiPath(processEl) {
  const vars = findExt(processEl, "uipath:Variables");
  if (!vars) return undefined;
  return { variables: mapVariables(vars) };
}

// ---------------------------------------------------------------------------
// Public: build the full model (CanvasState-like) from a moddle definitions.
// ---------------------------------------------------------------------------
export function buildModel(definitions) {
  const requiredFieldIndex = loadRequiredFieldIndex();
  const rootElements = definitions.rootElements ?? [];

  // Global event objects (Errors/Messages/Signals/Escalations).
  const objects = { errors: [], messages: [], signals: [], escalations: [] };
  for (const el of rootElements) {
    if (el.$type === "bpmn:Error") objects.errors.push({ id: el.id, name: el.name, errorCode: el.errorCode });
    else if (el.$type === "bpmn:Message") objects.messages.push({ id: el.id, name: el.name });
    else if (el.$type === "bpmn:Signal") objects.signals.push({ id: el.id, name: el.name });
    else if (el.$type === "bpmn:Escalation") objects.escalations.push({ id: el.id, name: el.name, escalationCode: el.escalationCode });
  }

  const collaboration = rootElements.find((e) => e.$type === "bpmn:Collaboration");
  const processes = rootElements.filter((e) => e.$type === "bpmn:Process");
  const processById = new Map(processes.map((p) => [p.id, p]));

  const diagramsById = {};
  let rootDiagramId;
  let rootNode;

  const procContainerNode = (proc, parentId) => ({
    id: proc.id,
    type: "bpmn:Process",
    parentId,
    abstractType: undefined,
    data: { label: proc.name, uipath: buildRootUiPath(proc) },
  });

  if (collaboration) {
    // Single collaboration diagram: pools + every participant's process flow
    // nodes, with collaboration-level message flows. Pool lookup (walk parentId
    // up to bpmn:Participant) resolves because each process's flow nodes get
    // parentId = pool id, and the Process container node sits under the pool.
    const nodes = [];
    const edges = [];
    for (const p of collaboration.participants ?? []) {
      nodes.push({
        id: p.id,
        type: "bpmn:Participant",
        parentId: undefined,
        abstractType: undefined,
        data: { label: p.name, processRef: p.processRef?.id ?? p.processRef },
      });
      const proc = processById.get(p.processRef?.id ?? p.processRef);
      if (proc) {
        nodes.push(procContainerNode(proc, p.id));
        collectContainer(proc, requiredFieldIndex, nodes, edges, p.id);
        if (!rootNode) rootNode = procContainerNode(proc, undefined);
      }
    }
    for (const mf of collaboration.messageFlows ?? []) {
      edges.push(buildEdge(mf, collaboration));
    }
    rootDiagramId = collaboration.id;
    diagramsById[collaboration.id] = {
      diagramId: collaboration.id,
      root: { id: collaboration.id, type: collaboration.$type },
      nodes,
      edges,
    };
  } else {
    // Stand-alone process(es): one diagram each, root-scope flow nodes at
    // parentId undefined (frontend root scope). The Process container node is
    // included so container-scoped rules (SingleBlankStartEvent) can see it.
    for (const proc of processes) {
      const nodes = [procContainerNode(proc, undefined)];
      const edges = [];
      collectContainer(proc, requiredFieldIndex, nodes, edges, undefined);
      const diagramId = proc.id;
      diagramsById[diagramId] = {
        diagramId,
        root: { id: proc.id, type: proc.$type },
        nodes,
        edges,
      };
      if (!rootDiagramId) {
        rootDiagramId = diagramId;
        rootNode = procContainerNode(proc, undefined);
      }
    }
  }

  return {
    rootDiagramId,
    root: rootNode ?? { id: "root", type: "bpmn:Process", data: {} },
    diagramsById,
    objects,
  };
}

// Build the set of known variable identifiers for variable-existence checks:
// ids AND names AND canonicalIds, across root + every node scope.
export function collectKnownVariableIds(canvasState) {
  const ids = new Set();
  const add = (v) => {
    if (v?.id) ids.add(v.id);
    if (v?.name) ids.add(v.name);
    if (v?.canonicalId) ids.add(v.canonicalId);
  };
  const rv = canvasState.root?.data?.uipath?.variables;
  for (const v of rv?.inputs ?? []) add(v);
  for (const v of rv?.inputOutputs ?? []) add(v);
  for (const v of rv?.outputs ?? []) add(v);
  for (const d of Object.values(canvasState.diagramsById)) {
    for (const n of d.nodes) {
      const nv = n.data?.uipath?.variables;
      for (const v of nv?.inputs ?? []) add(v);
      for (const v of nv?.inputOutputs ?? []) add(v);
      for (const v of nv?.outputs ?? []) add(v);
      // A node's outputs each DECLARE a variable via their `var` attribute
      // (frontend mapNodeOutputsToVariables: `id: v.var`). These variables are
      // available to downstream nodes/edges, so they count as known. Without
      // this, a gateway condition reading a variable written by an upstream
      // script/task output false-positives as VARIABLE_DOES_NOT_EXIST.
      for (const o of n.data?.uipath?.outputs ?? []) {
        if (o.var) ids.add(o.var);
        if (o.name) ids.add(o.name);
        if (o.canonicalId) ids.add(o.canonicalId);
      }
    }
  }
  return ids;
}

// Convenience: all nodes / all edges across every diagram (for global checks).
export function allNodes(canvasState) {
  return Object.values(canvasState.diagramsById).flatMap((d) => d.nodes);
}
export function allEdges(canvasState) {
  return Object.values(canvasState.diagramsById).flatMap((d) => d.edges);
}
