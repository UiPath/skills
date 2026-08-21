// Test helpers that mirror the PO.Frontend rule-test builders
// (createNode / createEdge / createMockCanvasState etc.). The frontend rule
// tests operate directly on synthetic Node[]/Edge[]/CanvasState graphs and call
// the rule functions; we reproduce that exact harness so the ported per-rule
// tests are a true 1:1 translation of the frontend tests against OUR rule
// engine (rules.mjs), with no XML round-trip in the way for the synthetic cases.
//
// Node/Edge shapes match what rules.mjs consumes (see model.mjs): a Node carries
// { id, type, parentId?, abstractType?, data:{...} }; an Edge carries
// { id, type?, source, target, data:{...} }.

import { buildValidationLookupMaps } from "../rules.mjs";

export function node(id, type, data = {}, extra = {}) {
  return { id, type, data, ...extra };
}

export function edge(id, source, target, { type = "bpmn:SequenceFlow", data = {} } = {}) {
  return { id, type, source, target, data };
}

// A minimal CanvasState compatible with rules that consult canvasState.objects
// (errors/messages/...) and canvasState.diagramsById / root.
export function canvasState({ errors = [], rootVariables = undefined, diagramNodes = [], diagramEdges = [] } = {}) {
  const diagramId = "diagram1";
  return {
    rootDiagramId: diagramId,
    root: {
      id: "root",
      type: "bpmn:Process",
      data: rootVariables ? { uipath: { variables: rootVariables } } : {},
    },
    diagramsById: {
      [diagramId]: { diagramId, root: { id: "root", type: "bpmn:Process" }, nodes: diagramNodes, edges: diagramEdges },
    },
    objects: { errors, messages: [], signals: [], escalations: [] },
  };
}

export function maps(nodes, edges) {
  return buildValidationLookupMaps(nodes ?? [], edges ?? []);
}
