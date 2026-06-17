// Ported per-rule tests — a 1:1 translation of the PO.Frontend rule unit tests
// (PO.Frontend/src/services/validation/bpmn/rules/*.test.ts) against OUR rule
// engine (rules.mjs). Each case carries a `// FE:` comment mapping it to the
// originating frontend test (file + test name). The frontend tests construct
// synthetic Node[]/Edge[]/CanvasState graphs and call the rule directly; we do
// the same so the comparison is exact.
//
// Where our port intentionally diverges from a frontend test, the divergence is
// called out inline with a `// DRIFT:` comment and verified against the
// frontend's *actual observable behavior* (not just its unit test), per the
// drift-resolution policy. See README "Drift log".
//
// Returns { passed, failed, failures: [...] }.

import {
  buildValidationLookupMaps,
  validateConditionalSequenceFlow,
  validateConnections,
  validateDuplicateErrorEventSubprocess,
  validateEventSubProcessStart,
  validateErrorBoundaryEvents,
  validateDuplicateErrorBoundaryEvents,
  validateErrorEndEvents,
  validateFakeJoins,
  validateMessageFlowCrossPool,
  validateMissingResource,
  validateMissingRootVariables,
  validateNoAssignmentsInExpressions,
  validateRequiredFields,
  validateSequenceFlowPoolCrossing,
  validateSequenceFlowSubProcessCrossing,
  validateSingleBlankStartEvent,
  validateSingleStartEventInEventSubProcess,
  validateSuperfluousGateway,
  validateTaskTimerRange,
  validateTimerDuration,
  validateVariableExistence,
  validateVariableNotSet,
} from "../rules.mjs";
import { node, edge, canvasState, maps } from "./model-helpers.mjs";

const results = { passed: 0, failed: 0, failures: [], firedCodes: new Set() };
let currentSuite = "";
function suite(name) {
  currentSuite = name;
}
function check(name, condition, detail = "") {
  if (condition) {
    results.passed++;
  } else {
    results.failed++;
    results.failures.push(`[${currentSuite}] ${name}${detail ? " :: " + detail : ""}`);
  }
}
// assert exactly `n` findings of `code`
function expectCodeCount(name, findings, code, n) {
  const got = findings.filter((f) => f.code === code).length;
  if (n > 0 && got === n) results.firedCodes.add(code); // track positive coverage
  check(name, got === n, `expected ${n}x ${code}, got ${got} (all: [${findings.map((f) => f.code).join(",")}])`);
}
function expectNone(name, findings, code) {
  const got = findings.filter((f) => f.code === code).length;
  check(name, got === 0, `expected 0x ${code}, got ${got}`);
}
function expectEmpty(name, findings) {
  check(name, findings.length === 0, `expected [], got [${findings.map((f) => f.code).join(",")}]`);
}

// Convenience: run a graph-rule with freshly built lookup maps.
const run = (fn, nodes, edges) => fn(nodes, edges, buildValidationLookupMaps(nodes, edges));

// ===========================================================================
// 1. ConditionalFlowRule  (MISSING_CONDITION_EXPRESSION)
// ===========================================================================
suite("ConditionalFlowRule");
{
  // FE: "should return no errors for non-gateway nodes"
  expectEmpty("non-gateway node", run(validateConditionalSequenceFlow, [node("task1", "bpmn:Task")], []));

  // FE: "should return no errors for exclusive gateway with proper conditions"
  {
    const nodes = [node("gateway1", "bpmn:ExclusiveGateway"), node("task1", "bpmn:Task"), node("task2", "bpmn:Task")];
    const edges = [
      edge("flow1", "gateway1", "task1", { data: { conditionExpression: "x > 0" } }),
      edge("flow2", "gateway1", "task2", { data: { defaultFlow: true } }),
    ];
    expectEmpty("xor with conditions+default", run(validateConditionalSequenceFlow, nodes, edges));
  }

  // FE: "should detect missing conditions on exclusive gateway" (3 findings)
  {
    const nodes = [node("gateway1", "bpmn:ExclusiveGateway"), node("t1", "bpmn:Task"), node("t2", "bpmn:Task"), node("t3", "bpmn:Task")];
    const edges = [edge("flow1", "gateway1", "t1"), edge("flow2", "gateway1", "t2"), edge("flow3", "gateway1", "t3")];
    expectCodeCount("3 missing conditions", run(validateConditionalSequenceFlow, nodes, edges), "MISSING_CONDITION_EXPRESSION", 3);
  }

  // FE: "should not validate inclusive gateway flows anymore" (0 findings)
  {
    const nodes = [node("gateway1", "bpmn:InclusiveGateway"), node("t1", "bpmn:Task"), node("t2", "bpmn:Task"), node("t3", "bpmn:Task")];
    const edges = [edge("flow1", "gateway1", "t1"), edge("flow2", "gateway1", "t2"), edge("flow3", "gateway1", "t3")];
    expectEmpty("inclusive gateway not validated", run(validateConditionalSequenceFlow, nodes, edges));
  }

  // FE: "should validate condition type is conditionExpression not condition" — single outgoing → not a split
  {
    const nodes = [node("gateway1", "bpmn:ExclusiveGateway"), node("task1", "bpmn:Task")];
    const edges = [edge("flow1", "gateway1", "task1", { data: { conditionExpression: "x > 0" } })];
    expectEmpty("single outgoing not a split", run(validateConditionalSequenceFlow, nodes, edges));
  }

  // FE: "should flag exactly one flow without condition..." scenario 2 → 2 findings
  {
    const nodes = [node("gateway2", "bpmn:ExclusiveGateway"), node("t1", "bpmn:Task"), node("t2", "bpmn:Task"), node("t3", "bpmn:Task")];
    const edges = [
      edge("flow1", "gateway2", "t1", { data: { conditionExpression: "x > 0" } }),
      edge("flow2", "gateway2", "t2"),
      edge("flow3", "gateway2", "t3"),
    ];
    expectCodeCount("two flows missing condition", run(validateConditionalSequenceFlow, nodes, edges), "MISSING_CONDITION_EXPRESSION", 2);
  }

  // FE: "should handle text annotation" — only outgoing is an Association to a TextAnnotation → 0
  {
    const nodes = [node("g", "bpmn:ExclusiveGateway"), node("anno", "bpmn:TextAnnotation")];
    const edges = [edge("g_anno", "g", "anno", { type: "bpmn:Association" })];
    expectEmpty("text annotation target ignored", run(validateConditionalSequenceFlow, nodes, edges));
  }

  // FE: "should handle empty nodes and edges arrays"
  expectEmpty("empty graph", run(validateConditionalSequenceFlow, [], []));

  // FE chained: "should correctly validate an XOR gateway that splits..." — 2 findings, both from XOR_A
  {
    const nodes = [node("XOR_A", "bpmn:ExclusiveGateway"), node("XOR_B", "bpmn:ExclusiveGateway"), node("Task_C", "bpmn:Task"), node("Task_D", "bpmn:Task")];
    const edges = [edge("Flow1_A_to_B", "XOR_A", "XOR_B"), edge("Flow2_A_to_C", "XOR_A", "Task_C"), edge("Flow3_B_to_D", "XOR_B", "Task_D")];
    const f = run(validateConditionalSequenceFlow, nodes, edges);
    expectCodeCount("chained gateways: 2 findings", f, "MISSING_CONDITION_EXPRESSION", 2);
    check("chained gateways: both sourceId XOR_A", f.every((e) => e.sourceId === "XOR_A"), JSON.stringify(f.map((e) => e.sourceId)));
  }
}

// ===========================================================================
// 2. ConnectionRule  (INVALID_CONNECTION / INVALID_CONNECTION_TYPE)
// FE asserts by message substring; we assert the equivalent code.
// ===========================================================================
suite("ConnectionRule");
{
  // FE: "should validate empty graph without errors"
  expectEmpty("empty graph", run(validateConnections, [], []));

  // FE: "should allow valid connections between nodes" — StartEvent -> Task
  {
    const nodes = [node("1", "bpmn:StartEvent"), node("2", "bpmn:Task")];
    expectEmpty("start->task allowed", run(validateConnections, nodes, [edge("e1", "1", "2")]));
  }

  // FE: "should detect edges with missing nodes" — Broken flow line
  {
    const nodes = [node("1", "bpmn:StartEvent")];
    const f = run(validateConnections, nodes, [edge("e1", "1", "nonexistent")]);
    expectCodeCount("broken flow line -> INVALID_CONNECTION", f, "INVALID_CONNECTION", 1);
  }

  // FE: "should not allow a connection to have the same source and target"
  {
    const nodes = [node("1", "bpmn:StartEvent")];
    const f = run(validateConnections, nodes, [edge("e1", "1", "1")]);
    expectCodeCount("self loop -> INVALID_CONNECTION", f, "INVALID_CONNECTION", 1);
  }

  // FE: "should validate node type compatibility" — verbatim frontend input:
  // unknown source type "output" → unknown target "input". canNodeTypesBeConnected
  // (BPMNTypesUtils.ts:51-82) finds no matching rule and returns false, so the
  // edge is INVALID_CONNECTION_TYPE. (Restored from a prior doctored EndEvent->Task
  // substitute; matches ConnectionRule.test.ts:33-43.)
  {
    const nodes = [node("1", "output"), node("2", "input")];
    const f = run(validateConnections, nodes, [edge("e1", "1", "2")]);
    expectCodeCount("unknown output->input -> INVALID_CONNECTION_TYPE", f, "INVALID_CONNECTION_TYPE", 1);
  }
}

// ===========================================================================
// 3. DuplicateErrorEventSubprocessRule
// ===========================================================================
suite("DuplicateErrorEventSubprocessRule");
{
  const esp = (id, parentId) => node(id, "bpmn:SubProcess", { triggeredByEvent: true }, { parentId });
  const errStart = (id, parentId, errorRef) =>
    node(id, "bpmn:StartEvent", { eventDefinition: { type: "bpmn:ErrorEventDefinition", ...(errorRef ? { errorRef } : {}) } }, { parentId });

  // FE: "multiple catch-all error event subprocesses at same scope" — 2 findings
  {
    const nodes = [esp("sp1", undefined), errStart("s1", "sp1"), esp("sp2", undefined), errStart("s2", "sp2")];
    const cs = canvasState({ errors: [] });
    const f = validateDuplicateErrorEventSubprocess(nodes, cs, maps(nodes, []));
    expectCodeCount("2 catch-all ESP", f, "MULTIPLE_CATCH_ALL_ERROR_EVENT_SUBPROCESS", 2);
  }

  // FE: "multiple error event subprocesses with same error code at same scope" — 2 findings
  {
    const nodes = [esp("sp1", undefined), errStart("s1", "sp1", "error1"), esp("sp2", undefined), errStart("s2", "sp2", "error2")];
    const cs = canvasState({ errors: [{ id: "error1", errorCode: "501" }, { id: "error2", errorCode: "501" }] });
    const f = validateDuplicateErrorEventSubprocess(nodes, cs, maps(nodes, []));
    expectCodeCount("same error code ESP", f, "DUPLICATE_ERROR_EVENT_SUBPROCESS", 2);
  }

  // FE: "different error codes at same scope" — []
  {
    const nodes = [esp("sp1", undefined), errStart("s1", "sp1", "error1"), esp("sp2", undefined), errStart("s2", "sp2", "error2")];
    const cs = canvasState({ errors: [{ id: "error1", errorCode: "501" }, { id: "error2", errorCode: "502" }] });
    expectEmpty("different error codes ESP", validateDuplicateErrorEventSubprocess(nodes, cs, maps(nodes, [])));
  }

  // FE: "same error code at different scopes" — []
  {
    const nodes = [esp("sp1", "scope1"), errStart("s1", "sp1", "error1"), esp("sp2", "scope2"), errStart("s2", "sp2", "error1")];
    const cs = canvasState({ errors: [{ id: "error1", errorCode: "501" }] });
    expectEmpty("same code different scope ESP", validateDuplicateErrorEventSubprocess(nodes, cs, maps(nodes, [])));
  }

  // FE: "catch-all error event subprocesses at different scopes" — []
  {
    const nodes = [esp("sp1", "scope1"), errStart("s1", "sp1"), esp("sp2", "scope2"), errStart("s2", "sp2")];
    expectEmpty("catch-all different scope ESP", validateDuplicateErrorEventSubprocess(nodes, canvasState(), maps(nodes, [])));
  }
}

// ===========================================================================
// 4. EmptyStartEventDefinitionInSubProcessRule
// ===========================================================================
suite("EmptyStartEventDefinitionInSubProcessRule");
{
  const sp = (id, triggeredByEvent) => node(id, "bpmn:SubProcess", triggeredByEvent ? { triggeredByEvent: true } : {});
  const start = (id, parentId, ed) => node(id, "bpmn:StartEvent", ed ? { eventDefinition: ed } : {}, { parentId });

  // FE: "should allow blank start event in subprocess" (regular)
  {
    const nodes = [sp("subprocess1", false), start("start1", "subprocess1")];
    expectEmpty("blank start in regular subprocess", run(validateEventSubProcessStart, nodes, []));
  }
  // FE: "should detect start event with event definition in regular subprocess"
  {
    const nodes = [sp("subprocess1", false), start("start1", "subprocess1", { id: "timer1", type: "bpmn:TimerEventDefinition" })];
    expectCodeCount("def in regular subprocess", run(validateEventSubProcessStart, nodes, []), "START_EVENT_WITH_DEFINITION_IN_SUBPROCESS", 1);
  }
  // FE: "should allow start event with timer event definition in event subprocess"
  {
    const nodes = [sp("subprocess1", true), start("start1", "subprocess1", { type: "bpmn:TimerEventDefinition" })];
    expectEmpty("timer def in event subprocess", run(validateEventSubProcessStart, nodes, []));
  }
  // FE: "should allow start event with message event definition in event subprocess"
  {
    const nodes = [sp("subprocess1", true), start("start1", "subprocess1", { type: "bpmn:MessageEventDefinition" })];
    expectEmpty("message def in event subprocess", run(validateEventSubProcessStart, nodes, []));
  }
  // FE: "should detect start event without event definition in event subprocess"
  {
    const nodes = [sp("subprocess1", true), start("start1", "subprocess1")];
    expectCodeCount("no def in event subprocess", run(validateEventSubProcessStart, nodes, []), "START_EVENT_WITHOUT_DEFINITION_IN_EVENT_SUBPROCESS", 1);
  }
  // FE: "should detect start event with invalid event definition in event subprocess"
  {
    const nodes = [sp("subprocess1", true), start("start1", "subprocess1", { type: "bpmn:ConditionalEventDefinition" })];
    expectCodeCount("invalid def in event subprocess", run(validateEventSubProcessStart, nodes, []), "INVALID_EVENT_DEFINITION_IN_EVENT_SUBPROCESS", 1);
  }
}

// ===========================================================================
// 5. ErrorBoundaryEventRule (validate + duplicate)
// ===========================================================================
suite("ErrorBoundaryEventRule");
{
  const be = (id, ed, attachedToId = "task1") => node(id, "bpmn:BoundaryEvent", { eventDefinition: ed, attachedToId });

  // FE: "should not report errors when there are no boundary events"
  expectEmpty("no boundary events", validateErrorBoundaryEvents([], canvasState()));
  // FE: "should not report errors for boundary events without error definitions"
  expectEmpty("non-error boundary def", validateErrorBoundaryEvents([be("boundary1", { type: "bpmn:SignalEventDefinition" })], canvasState()));
  // FE: "should detect empty error reference in boundary event" (errorRef:"")
  {
    const f = validateErrorBoundaryEvents([be("boundary1", { type: "bpmn:ErrorEventDefinition", errorRef: "" })], canvasState());
    expectCodeCount("empty error ref", f, "ERROR_BOUNDARY_EVENT_EMPTY_ERROR_REF", 1);
  }
  // FE: "should detect missing error code when referencing an error"
  {
    const cs = canvasState({ errors: [{ id: "error1", name: "CustomerError", errorCode: "" }] });
    const f = validateErrorBoundaryEvents([be("boundary1", { type: "bpmn:ErrorEventDefinition", errorRef: "error1" })], cs);
    expectCodeCount("missing error code", f, "ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE", 1);
  }
  // FE: "should not report errors when error has valid error code"
  {
    const cs = canvasState({ errors: [{ id: "error1", name: "CustomerError", errorCode: "ERR-001" }] });
    expectEmpty("valid error code", validateErrorBoundaryEvents([be("boundary1", { type: "bpmn:ErrorEventDefinition", errorRef: "error1" })], cs));
  }
  // FE: "multiple catch-all boundary events on same task" — 2 findings
  {
    const nodes = [be("b1", { type: "bpmn:ErrorEventDefinition" }, "task1"), be("b2", { type: "bpmn:ErrorEventDefinition" }, "task1")];
    expectCodeCount("2 catch-all on task", validateDuplicateErrorBoundaryEvents(nodes, canvasState()), "MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK", 2);
  }
  // FE: "multiple boundary events with same error code on same task" — 2 findings
  {
    const nodes = [be("b1", { type: "bpmn:ErrorEventDefinition", errorRef: "error1" }, "task1"), be("b2", { type: "bpmn:ErrorEventDefinition", errorRef: "error2" }, "task1")];
    const cs = canvasState({ errors: [{ id: "error1", errorCode: "501" }, { id: "error2", errorCode: "501" }] });
    expectCodeCount("same code on task", validateDuplicateErrorBoundaryEvents(nodes, cs), "DUPLICATE_ERROR_BOUNDARY_EVENT_ON_TASK", 2);
  }
  // FE: "different error codes on same task" — []
  {
    const nodes = [be("b1", { type: "bpmn:ErrorEventDefinition", errorRef: "error1" }, "task1"), be("b2", { type: "bpmn:ErrorEventDefinition", errorRef: "error2" }, "task1")];
    const cs = canvasState({ errors: [{ id: "error1", errorCode: "501" }, { id: "error2", errorCode: "502" }] });
    expectEmpty("different codes on task", validateDuplicateErrorBoundaryEvents(nodes, cs));
  }
  // FE: "same error code on different tasks" — []
  {
    const nodes = [be("b1", { type: "bpmn:ErrorEventDefinition", errorRef: "error1" }, "task1"), be("b2", { type: "bpmn:ErrorEventDefinition", errorRef: "error1" }, "task2")];
    const cs = canvasState({ errors: [{ id: "error1", errorCode: "501" }] });
    expectEmpty("same code different tasks", validateDuplicateErrorBoundaryEvents(nodes, cs));
  }
  // FE: "catch-all boundary events on different tasks" — []
  {
    const nodes = [be("b1", { type: "bpmn:ErrorEventDefinition" }, "task1"), be("b2", { type: "bpmn:ErrorEventDefinition" }, "task2")];
    expectEmpty("catch-all different tasks", validateDuplicateErrorBoundaryEvents(nodes, canvasState()));
  }
}

// ===========================================================================
// 6. ErrorEndEventRule
// ===========================================================================
suite("ErrorEndEventRule");
{
  const end = (id, ed) => node(id, "bpmn:EndEvent", ed ? { eventDefinition: ed } : {});
  expectEmpty("no end events", validateErrorEndEvents([]));
  expectEmpty("end without def", validateErrorEndEvents([end("end1")]));
  expectEmpty("end with signal def", validateErrorEndEvents([end("end1", { type: "bpmn:SignalEventDefinition" })]));
  // FE: "should report error when error end event has no errorRef"
  expectCodeCount("error end no errorRef", validateErrorEndEvents([end("end1", { type: "bpmn:ErrorEventDefinition" })]), "ERROR_END_EVENT_MISSING_EXCEPTION", 1);
  // FE: "should report error when error end event has empty errorRef"
  expectCodeCount("error end empty errorRef", validateErrorEndEvents([end("end1", { type: "bpmn:ErrorEventDefinition", errorRef: "" })]), "ERROR_END_EVENT_MISSING_EXCEPTION", 1);
  // FE: "should not report error when error end event has a valid errorRef"
  expectEmpty("error end valid errorRef", validateErrorEndEvents([end("end1", { type: "bpmn:ErrorEventDefinition", errorRef: "error1" })]));
  // FE: "multiple error end events missing errorRef" — 2 findings (end1, end3)
  {
    const nodes = [end("end1", { type: "bpmn:ErrorEventDefinition" }), end("end2", { type: "bpmn:ErrorEventDefinition", errorRef: "error1" }), end("end3", { type: "bpmn:ErrorEventDefinition" })];
    const f = validateErrorEndEvents(nodes);
    expectCodeCount("2 error ends missing ref", f, "ERROR_END_EVENT_MISSING_EXCEPTION", 2);
    check("error ends are end1,end3", f.map((e) => e.elementId).join(",") === "end1,end3", f.map((e) => e.elementId).join(","));
  }
  // FE: "should ignore non-end-event nodes"
  expectEmpty("ignore boundary error event", validateErrorEndEvents([node("boundary1", "bpmn:BoundaryEvent", { eventDefinition: { type: "bpmn:ErrorEventDefinition" } })]));
}

// ===========================================================================
// 7. FakeJoinRule
// DRIFT (resolved by matching the frontend's *actual* behavior): the frontend
// rule matches only literal "bpmn:Activity"/"bpmn:Event" node types. On the real
// canvas every node carries its CONCRETE type (bpmn:Task, bpmn:EndEvent, ...),
// so the rule is dormant on exported BPMN. Our port mirrors that exactly. The
// FE unit tests below feed literal abstract types — we reproduce them verbatim,
// AND add concrete-type cases proving we do NOT over-fire on real BPMN (which an
// earlier hand-port did). See README "Drift log #2".
// ===========================================================================
suite("FakeJoinRule");
{
  // FE: "should return empty array for null or undefined inputs"
  expectEmpty("null nodes", validateFakeJoins(null, [], maps([], [])));
  expectEmpty("null edges", validateFakeJoins([], null, maps([], [])));
  expectEmpty("undefined both", validateFakeJoins(undefined, undefined, maps([], [])));
  // FE: "should return empty array when no fake joins exist"
  {
    const nodes = [node("1", "bpmn:Activity"), node("2", "bpmn:Event")];
    expectEmpty("no fake joins", run(validateFakeJoins, nodes, [edge("e1", "1", "2")]));
  }
  // FE: "should detect fake joins in activities" (literal bpmn:Activity, 2 incoming)
  {
    const nodes = [node("1", "bpmn:Activity"), node("2", "bpmn:Activity"), node("3", "bpmn:Activity")];
    const edges = [edge("e1", "1", "3"), edge("e2", "2", "3")];
    expectCodeCount("fake join in activity", run(validateFakeJoins, nodes, edges), "FAKE_JOIN", 1);
  }
  // FE: "should detect fake joins in events" (literal bpmn:Event)
  {
    const nodes = [node("1", "bpmn:Activity"), node("2", "bpmn:Activity"), node("3", "bpmn:Event")];
    const edges = [edge("e1", "1", "3"), edge("e2", "2", "3")];
    expectCodeCount("fake join in event", run(validateFakeJoins, nodes, edges), "FAKE_JOIN", 1);
  }
  // FE: "should ignore non-activity/event nodes" (gateway with multiple incoming)
  {
    const nodes = [node("1", "bpmn:Activity"), node("2", "bpmn:Activity"), node("3", "bpmn:Gateway")];
    const edges = [edge("e1", "1", "3"), edge("e2", "2", "3")];
    expectEmpty("gateway multiple incoming allowed", run(validateFakeJoins, nodes, edges));
  }
  // PORT PARITY: concrete-typed task with 2 incoming must NOT fire (matches the
  // frontend's dormant-on-real-BPMN behavior; an earlier hand-port over-fired).
  {
    const nodes = [node("a", "bpmn:Task"), node("b", "bpmn:Task"), node("c", "bpmn:Task")];
    const edges = [edge("e1", "a", "c"), edge("e2", "b", "c")];
    expectNone("concrete task join does not over-fire", run(validateFakeJoins, nodes, edges), "FAKE_JOIN");
  }
}

// ===========================================================================
// 8. MessageFlowObjectsPoolRule
// ===========================================================================
suite("MessageFlowObjectsPoolRule");
{
  const part = (id) => node(id, "bpmn:Participant");
  const inPool = (id, parentId) => node(id, "bpmn:Task", {}, { parentId });
  const mf = (id, s, t) => edge(id, s, t, { type: "bpmn:MessageFlow" });

  // FE: "should return empty array when no pools exist"
  expectEmpty("no pools", run(validateMessageFlowCrossPool, [inPool("task1"), inPool("task2")], [mf("flow1", "task1", "task2")]));
  // FE: "should allow message flow between different pools"
  {
    const nodes = [part("pool1"), part("pool2"), inPool("task1", "pool1"), inPool("task2", "pool2")];
    expectEmpty("cross-pool mf allowed", run(validateMessageFlowCrossPool, nodes, [mf("flow1", "task1", "task2")]));
  }
  // FE: "should detect message flow within the same pool" — 1 finding
  {
    const nodes = [part("pool1"), inPool("task1", "pool1"), inPool("task2", "pool1")];
    expectCodeCount("same-pool mf", run(validateMessageFlowCrossPool, nodes, [mf("flow1", "task1", "task2")]), "SAME_POOL_MESSAGE_FLOW", 1);
  }
  // FE: "should handle nested elements in pools"
  {
    const nodes = [part("pool1"), node("subprocess1", "bpmn:SubProcess", {}, { parentId: "pool1" }), inPool("task1", "subprocess1"), inPool("task2", "subprocess1")];
    expectCodeCount("nested same-pool mf", run(validateMessageFlowCrossPool, nodes, [mf("flow1", "task1", "task2")]), "SAME_POOL_MESSAGE_FLOW", 1);
  }
  // FE: "should ignore non-message flows"
  {
    const nodes = [part("pool1"), inPool("task1", "pool1"), inPool("task2", "pool1")];
    expectEmpty("sequence flow ignored by mf rule", run(validateMessageFlowCrossPool, nodes, [edge("flow1", "task1", "task2", { type: "bpmn:SequenceFlow" })]));
  }
  // FE: "should handle multiple message flows" — 1 finding (only same-pool flow1)
  {
    const nodes = [part("pool1"), part("pool2"), inPool("task1", "pool1"), inPool("task2", "pool1"), inPool("task3", "pool2")];
    const edges = [mf("flow1", "task1", "task2"), mf("flow2", "task1", "task3")];
    expectCodeCount("multiple mf, one same-pool", run(validateMessageFlowCrossPool, nodes, edges), "SAME_POOL_MESSAGE_FLOW", 1);
  }
  // FE: "should handle elements in deeply nested subprocesses"
  {
    const nodes = [
      part("pool1"),
      node("subprocess1", "bpmn:SubProcess", {}, { parentId: "pool1" }),
      node("subprocess2", "bpmn:SubProcess", {}, { parentId: "subprocess1" }),
      inPool("task1", "subprocess2"),
      inPool("task2", "subprocess2"),
    ];
    expectCodeCount("deeply nested same-pool mf", run(validateMessageFlowCrossPool, nodes, [mf("flow1", "task1", "task2")]), "SAME_POOL_MESSAGE_FLOW", 1);
  }
}

// ===========================================================================
// 9. MissingResourceRule (WARNING)
// ===========================================================================
suite("MissingResourceRule");
{
  const svc = (id, uipath, label = "Task", type = "bpmn:ServiceTask") => node(id, type, { label, uipath });

  // FE: "ignores nodes without a uipath service type"
  expectEmpty("no service type", run(validateMissingResource, [svc("1", {})], []));
  // FE: "ignores service types that do not require a bound resource" (ScriptTask)
  expectEmpty("scriptTask ignored", run(validateMissingResource, [svc("1", { serviceType: "BPMN.ScriptTask" })], []));
  // FE: "flags an agent task when no resource is bound"
  expectCodeCount("agent no binding", run(validateMissingResource, [svc("agent-1", { serviceType: "Orchestrator.StartAgentJob", version: "v2" }, "Agent (placeholder)")], []), "MISSING_RESOURCE", 1);
  // FE: "does not flag an agent task with a v1 releaseKey binding"
  expectEmpty("agent releaseKey binding", run(validateMissingResource, [svc("agent-1", { serviceType: "Orchestrator.StartAgentJob", context: [{ name: "releaseKey", type: "string", value: "binding-id" }] })], []));
  // FE: "does not flag a v2 task with a name binding"
  expectEmpty("v2 name binding", run(validateMissingResource, [svc("queue-1", { serviceType: "Orchestrator.CreateAndWaitForQueueItem", version: "v2", context: [{ name: "name", value: "MyQueue" }, { name: "folderPath", value: "Shared" }] })], []));
  // FE: "flags when context exists but has no releaseKey or name"
  expectCodeCount("hitl no binding fields", run(validateMissingResource, [svc("hitl-1", { serviceType: "Actions.HITL", context: [{ name: "taskTitle", type: "string", value: "Approve" }] })], []), "MISSING_RESOURCE", 1);
  // FE: "returns one warning per unbound task across multiple nodes" (script-1 not checked)
  {
    const nodes = [svc("agent-1", { serviceType: "Orchestrator.StartAgentJob" }), svc("queue-1", { serviceType: "Orchestrator.CreateQueueItem" }), svc("script-1", { serviceType: "BPMN.ScriptTask" })];
    const f = run(validateMissingResource, nodes, []);
    check("one warning per unbound task", f.map((e) => e.elementId).sort().join(",") === "agent-1,queue-1", f.map((e) => e.elementId).join(","));
  }
  // FE: "flags an unbound call activity action %s" (4 case manager / agentic types)
  for (const st of ["Orchestrator.StartAgenticProcess", "Orchestrator.StartAgenticProcessAsync", "Orchestrator.StartCaseMgmtProcess", "Orchestrator.StartCaseMgmtProcessAsync"]) {
    expectCodeCount(`call activity ${st}`, run(validateMissingResource, [svc("call-1", { serviceType: st, version: "v2" }, "Call activity", "bpmn:CallActivity")], []), "MISSING_RESOURCE", 1);
  }
}

// ===========================================================================
// 10. MissingRootVariableRule (WARNING)
// Uses validateMissingRootVariables(nodes, canvasState). Our port reads
// canvasState.root.data.uipath.variables (inputOutputs+outputs), resolves a
// node output's `var` against root + enclosing-subprocess scope via
// node.data.parentElement chain & canvasState.diagramsById.
// ===========================================================================
suite("MissingRootVariableRule");
{
  const task = (id, outputs, parentElement) => node(id, "bpmn:Task", { label: id, uipath: { outputs }, ...(parentElement ? { parentElement } : {}) });
  const subp = (id, variables, parentElement) => node(id, "bpmn:SubProcess", { isExpanded: true, uipath: { variables }, ...(parentElement ? { parentElement } : {}) });
  // Build a canvasState whose diagram contains the given nodes and whose root has the given vars.
  const cs = (rootInputOutputs = [], rootOutputs = [], diagramNodes = []) =>
    canvasState({ rootVariables: { inputs: [], inputOutputs: rootInputOutputs, outputs: rootOutputs }, diagramNodes });

  // FE root 1: missing from root
  {
    const t = task("Task_1", [{ name: "response", type: "any", var: "var_missing" }]);
    expectCodeCount("root: missing var", validateMissingRootVariables([t], cs([], [], [t])), "MISSING_ROOT_VARIABLE", 1);
  }
  // FE root 2: exists in root inputOutputs
  {
    const t = task("Task_1", [{ var: "var_1" }]);
    expectEmpty("root: var exists", validateMissingRootVariables([t], cs([{ id: "var_1", name: "response", type: "any" }], [], [t])));
  }
  // FE root 3: one warning per node even if multiple outputs missing
  {
    const t = task("Task_1", [{ var: "var_a" }, { var: "var_b" }, { var: "var_c" }]);
    expectCodeCount("root: one per node", validateMissingRootVariables([t], cs([], [], [t])), "MISSING_ROOT_VARIABLE", 1);
  }
  // FE root 4: only the unhealthy node flagged
  {
    const t1 = task("Task_1", [{ var: "var_1" }]);
    const t2 = task("Task_2", [{ var: "var_missing" }]);
    const f = validateMissingRootVariables([t1, t2], cs([{ id: "var_1" }], [], [t1, t2]));
    expectCodeCount("root: only unhealthy", f, "MISSING_ROOT_VARIABLE", 1);
    check("root: flagged node is Task_2", f[0]?.elementId === "Task_2", f[0]?.elementId);
  }
  // FE root 5: root outputs also count
  {
    const e = task("EndEvent_1", [{ var: "var_out" }]);
    expectEmpty("root: outputs count", validateMissingRootVariables([e], cs([], [{ id: "var_out", name: "out", type: "string" }], [e])));
  }
  // FE subprocess 1: task in subprocess references root-scoped var
  {
    const sp = subp("SubProcess_1", { inputOutputs: [{ id: "var_sub" }] });
    const t = task("Task_1", [{ var: "var_root_only" }], { id: "SubProcess_1", type: "bpmn:SubProcess" });
    expectEmpty("sub: resolves at root", validateMissingRootVariables([sp, t], cs([{ id: "var_root_only" }], [], [sp, t])));
  }
  // FE subprocess 2: missing from all scopes
  {
    const sp = subp("SubProcess_1", { inputOutputs: [{ id: "var_sub" }] });
    const t = task("Task_1", [{ var: "var_nowhere" }], { id: "SubProcess_1", type: "bpmn:SubProcess" });
    expectCodeCount("sub: missing everywhere", validateMissingRootVariables([sp, t], cs([], [], [sp, t])), "MISSING_ROOT_VARIABLE", 1);
  }
  // FE subprocess 3: resolves at subprocess scope
  {
    const sp = subp("SubProcess_1", { inputOutputs: [{ id: "var_sub" }] });
    const t = task("Task_1", [{ var: "var_sub" }], { id: "SubProcess_1", type: "bpmn:SubProcess" });
    expectEmpty("sub: resolves at subprocess", validateMissingRootVariables([sp, t], cs([], [], [sp, t])));
  }
  // FE nested 2: resolves at intermediate subprocess scope
  {
    const outer = subp("SubProcess_outer", { inputOutputs: [{ id: "var_outer" }] });
    const inner = subp("SubProcess_inner", { inputOutputs: [] }, { id: "SubProcess_outer", type: "bpmn:SubProcess" });
    const t = task("Task_1", [{ var: "var_outer" }], { id: "SubProcess_inner", type: "bpmn:SubProcess" });
    expectEmpty("nested: resolves at outer", validateMissingRootVariables([outer, inner, t], cs([], [], [outer, inner, t])));
  }
  // FE nested 3: missing from all scopes
  {
    const outer = subp("SubProcess_outer", { inputOutputs: [{ id: "var_outer" }] });
    const inner = subp("SubProcess_inner", { inputOutputs: [{ id: "var_inner" }] }, { id: "SubProcess_outer", type: "bpmn:SubProcess" });
    const t = task("Task_1", [{ var: "var_nowhere" }], { id: "SubProcess_inner", type: "bpmn:SubProcess" });
    expectCodeCount("nested: missing everywhere", validateMissingRootVariables([outer, inner, t], cs([], [], [outer, inner, t])), "MISSING_ROOT_VARIABLE", 1);
  }
}

// ===========================================================================
// 11. NoAssignmentsRule (WARNING)
// ===========================================================================
suite("NoAssignmentsRule");
{
  const en = (cond) => edge("edge-1", "node-1", "node-2", { data: { conditionExpression: cond } });
  const nm = (errorMapping) => node("node-1", "bpmn:Activity", { uipath: { errorMapping } });

  expectEmpty("null nodes", validateNoAssignmentsInExpressions(null, []));
  expectEmpty("null edges", validateNoAssignmentsInExpressions([], null));
  expectEmpty("empty", validateNoAssignmentsInExpressions([], []));
  // FE: "should detect assignment in edge condition expression"
  expectCodeCount("edge assignment", validateNoAssignmentsInExpressions([], [en("=x = 5")]), "ASSIGNMENT_NOT_ALLOWED", 1);
  // FE: "should skip edges with no condition expression"
  expectEmpty("edge no cond", validateNoAssignmentsInExpressions([], [edge("edge-1", "node-1", "node-2", { data: {} })]));
  // FE: "should not flag comparison operators in edge expressions"
  expectEmpty("edge comparison", validateNoAssignmentsInExpressions([], [en("=x === y && z >= 10")]));
  // FE: "should detect compound assignment operators (??=)"
  expectCodeCount("edge compound assign", validateNoAssignmentsInExpressions([], [en("=x ??= 5")]), "ASSIGNMENT_NOT_ALLOWED", 1);
  // FE: "should detect errors across multiple edges"
  expectCodeCount("multiple edge assigns", validateNoAssignmentsInExpressions([], [edge("edge-1", "a", "b", { data: { conditionExpression: "=a = 1" } }), edge("edge-2", "c", "d", { data: { conditionExpression: "=b = 2" } })]), "ASSIGNMENT_NOT_ALLOWED", 2);
  // FE: "should not check node inputs for assignments"
  expectEmpty("node inputs not checked", validateNoAssignmentsInExpressions([node("node-1", "bpmn:Activity", { uipath: { inputs: [{ name: "myInput", var: "var-1", value: "=x = 5", type: "string" }] } })], []));
  // FE: "should not check node outputs for assignments"
  expectEmpty("node outputs not checked", validateNoAssignmentsInExpressions([node("node-1", "bpmn:Activity", { uipath: { outputs: [{ name: "myOutput", var: "out-1", source: "=x = 5", type: "string" }] } })], []));
  // FE: "should produce no errors for clean edge expressions" (arrow fn)
  expectEmpty("arrow fn not assignment", validateNoAssignmentsInExpressions([], [en("=() => x + 1")]));
  // FE: "should detect assignment in error mapping condition"
  expectCodeCount("error mapping assign", validateNoAssignmentsInExpressions([nm([{ id: "ErrorMapping_1", condition: "=x = 5" }])], []), "ASSIGNMENT_NOT_ALLOWED", 1);
  // FE: "should skip error mappings with no condition"
  expectEmpty("error mapping no cond", validateNoAssignmentsInExpressions([nm([{ id: "ErrorMapping_1" }])], []));
  // FE: "should not flag comparison operators in error mapping conditions"
  expectEmpty("error mapping comparison", validateNoAssignmentsInExpressions([nm([{ condition: "=x === y" }])], []));
  // FE: "should detect assignments across multiple error mappings"
  expectCodeCount("multiple error mapping assigns", validateNoAssignmentsInExpressions([nm([{ condition: "=a = 1" }, { condition: "=b = 2" }])], []), "ASSIGNMENT_NOT_ALLOWED", 2);
  // FE: "should detect assignments in both edges and error mappings"
  expectCodeCount("edge + error mapping assigns", validateNoAssignmentsInExpressions([nm([{ condition: "=x = 1" }])], [en("=y = 2")]), "ASSIGNMENT_NOT_ALLOWED", 2);
}

// ===========================================================================
// 12. RequiredFieldsRule
// FE marks fields `required:true` inline. Our model recovers `required` from
// the registry by field-name match; here we set it directly (same shape the
// rule consumes) to reproduce the FE scenarios 1:1.
// ===========================================================================
suite("RequiredFieldsRule");
{
  const n = (id, uipath, label = "Test Activity") => node(id, "bpmn:ServiceTask", { label, uipath });
  expectEmpty("null nodes", validateRequiredFields(null));
  // FE: "no required fields empty"
  expectEmpty("no empty required", validateRequiredFields([n("1", { context: [{ required: true, name: "field1", value: "value1" }], inputs: [{ required: true, name: "input1", value: "value2" }], outputs: [{ name: "output1", value: "" }] })]));
  // FE: "empty required field in context" (2 nodes) → 2 findings
  {
    const nodes = [n("1", { context: [{ required: true, name: "field1", value: "" }, { required: false, name: "field2", value: "" }] }), n("2", { context: [{ required: true, name: "field1", value: "" }, { required: false, name: "field2", value: "" }] })];
    expectCodeCount("context empty required", validateRequiredFields(nodes), "EMPTY_REQUIRED_FIELD", 2);
  }
  // FE: "empty required field in inputs"
  expectCodeCount("inputs empty required", validateRequiredFields([n("1", { inputs: [{ required: true, name: "input1", value: null }, { required: false, name: "input2", value: "" }] })]), "EMPTY_REQUIRED_FIELD", 1);
  // FE: "empty required field in outputs"
  expectCodeCount("outputs empty required", validateRequiredFields([n("1", { outputs: [{ required: true, name: "output1", value: undefined }, { required: false, name: "output2", value: "" }] })]), "EMPTY_REQUIRED_FIELD", 1);
  // FE: "handle nodes without uipath data"
  expectEmpty("no uipath", validateRequiredFields([node("1", "bpmn:ServiceTask", {})]));
  // FE: "multiple empty required fields in different sections" → 1 finding (per-node)
  {
    const f = validateRequiredFields([n("1", { context: [{ required: true, name: "field1", value: "" }], inputs: [{ required: true, name: "input1", value: null }], outputs: [{ required: true, name: "output1", value: undefined }] })]);
    expectCodeCount("per-node single finding", f, "EMPTY_REQUIRED_FIELD", 1);
  }
  // PORT PARITY (absent required field): On canvas, every required field exists
  // in node data, so an unbound one is present-with-empty-value and the frontend
  // fires `field.required && isNilOrEmpty(field.value)` (ValidateRequiredFieldsInData.ts:15-16).
  // Offline, an unbound required field is ABSENT from the serialized data; the
  // model attaches the serviceType's required-field names as `requiredFieldNames`
  // so the rule treats an absent name as present-with-empty (same observable result).
  {
    // 'method' required by registry but not serialized at all → fires.
    const node1 = n("1", { context: [{ name: "url", value: "https://x" }], requiredFieldNames: ["method", "url"] });
    expectCodeCount("absent required field fires", validateRequiredFields([node1]), "EMPTY_REQUIRED_FIELD", 1);
  }
  {
    // All registry-required names present and non-empty → no finding.
    const node1 = n("1", { context: [{ name: "method", value: "GET" }, { name: "url", value: "https://x" }], requiredFieldNames: ["method", "url"] });
    expectEmpty("all required present", validateRequiredFields([node1]));
  }
  {
    // No requiredFieldNames (dynamic IS-connector type, required-ness only known
    // after registry enrichment) → conservative: absence not flagged (frontend
    // shares this — it also needs the enrichment to know the field is required).
    const node1 = n("1", { context: [{ name: "someField", value: "v" }] });
    expectEmpty("no requiredFieldNames → conservative", validateRequiredFields([node1]));
  }
}

// ===========================================================================
// 13. SequenceFlowPoolCrossingRule
// ===========================================================================
suite("SequenceFlowPoolCrossingRule");
{
  const part = (id) => node(id, "bpmn:Participant");
  const inPool = (id, parentId, type = "bpmn:Task") => node(id, type, {}, { parentId });
  const sf = (id, s, t) => edge(id, s, t, { type: "bpmn:SequenceFlow" });

  // FE: "should allow sequence flow within same pool"
  {
    const nodes = [part("pool1"), inPool("task1", "pool1"), inPool("task2", "pool1")];
    expectEmpty("same pool sf", run(validateSequenceFlowPoolCrossing, nodes, [sf("flow1", "task1", "task2")]));
  }
  // FE: "should detect sequence flow crossing pool boundaries"
  {
    const nodes = [part("pool1"), part("pool2"), inPool("task1", "pool1"), inPool("task2", "pool2")];
    expectCodeCount("cross pool sf", run(validateSequenceFlowPoolCrossing, nodes, [sf("flow1", "task1", "task2")]), "CROSSING_POOL_BOUNDARY", 1);
  }
  // FE: "should handle nested elements in pools"
  {
    const nodes = [part("pool1"), part("pool2"), inPool("subprocess1", "pool1", "bpmn:SubProcess"), inPool("subprocess2", "pool2", "bpmn:SubProcess"), inPool("task1", "subprocess1"), inPool("task2", "subprocess2")];
    expectCodeCount("nested cross pool sf", run(validateSequenceFlowPoolCrossing, nodes, [sf("flow1", "task1", "task2")]), "CROSSING_POOL_BOUNDARY", 1);
  }
}

// ===========================================================================
// 14. SequenceFlowSubProcessCrossingRule
// ===========================================================================
suite("SequenceFlowSubProcessCrossingRule");
{
  const sp = (id) => node(id, "bpmn:SubProcess");
  const inSp = (id, parentId) => node(id, "bpmn:Task", {}, { parentId });
  // FE helper: boundary node has parentId = attachedTo AND data.attachedToId = attachedTo
  const boundary = (id, attachedTo) => node(id, "bpmn:BoundaryEvent", { attachedToId: attachedTo }, { parentId: attachedTo });
  const sf = (id, s, t) => edge(id, s, t, { type: "bpmn:SequenceFlow" });

  // FE: "should allow sequence flow within same scope"
  {
    const nodes = [sp("subprocess1"), inSp("task1", "subprocess1"), inSp("task2", "subprocess1")];
    expectEmpty("same scope sf", run(validateSequenceFlowSubProcessCrossing, nodes, [sf("flow1", "task1", "task2")]));
  }
  // FE: "should detect sequence flow crossing subprocess boundary"
  {
    const nodes = [sp("subprocess1"), sp("subprocess2"), inSp("task1", "subprocess1"), inSp("task2", "subprocess2")];
    expectCodeCount("cross subprocess sf", run(validateSequenceFlowSubProcessCrossing, nodes, [sf("flow1", "task1", "task2")]), "CROSSING_SUBPROCESS_BOUNDARY", 1);
  }
  // FE: "should ignore non-sequence flows"
  {
    const nodes = [sp("subprocess1"), sp("subprocess2"), inSp("task1", "subprocess1"), inSp("task2", "subprocess2")];
    expectEmpty("association ignored", run(validateSequenceFlowSubProcessCrossing, nodes, [edge("association1", "task1", "task2", { type: "bpmn:Association" })]));
  }
  // FE: "boundary attached to child node connected within same subprocess" — allowed
  {
    const nodes = [sp("subprocess1"), boundary("boundaryEvent", "task1"), inSp("task1", "subprocess1"), inSp("task2", "subprocess1")];
    expectEmpty("boundary on child, same subprocess", run(validateSequenceFlowSubProcessCrossing, nodes, [sf("flow1", "boundaryEvent", "task2")]));
  }
  // FE: "subprocess-attached boundary connected into the subprocess" — crossing
  {
    const nodes = [sp("subprocess1"), boundary("boundaryEvent", "subprocess1"), inSp("task1", "subprocess1")];
    expectCodeCount("boundary on subprocess into child", run(validateSequenceFlowSubProcessCrossing, nodes, [sf("flow1", "boundaryEvent", "task1")]), "CROSSING_SUBPROCESS_BOUNDARY", 1);
  }
  // FE: "subprocess-attached boundary connected into a different subprocess" — crossing
  {
    const nodes = [sp("subprocess1"), boundary("boundaryEvent", "subprocess1"), sp("subprocess2"), inSp("task1", "subprocess2")];
    expectCodeCount("boundary on subprocess into other subprocess", run(validateSequenceFlowSubProcessCrossing, nodes, [sf("flow1", "boundaryEvent", "task1")]), "CROSSING_SUBPROCESS_BOUNDARY", 1);
  }
}

// ===========================================================================
// 15. SingleBlankStartEventRule
// Our port keys scopes off bpmn:Process / bpmn:SubProcess container nodes and
// groups start events by parentId. We add a container Process node (the FE tests
// include one via createNode("process1","bpmn:Process")).
// ===========================================================================
suite("SingleBlankStartEventRule");
{
  const proc = node("process1", "bpmn:Process");
  const start = (id, parentId, ed) => node(id, "bpmn:StartEvent", ed ? { eventDefinition: ed } : {}, { parentId });
  const sp = (id) => node(id, "bpmn:SubProcess");

  expectEmpty("null/empty", run(validateSingleBlankStartEvent, [], []));
  // FE: "single blank start in root process"
  expectEmpty("single blank root", run(validateSingleBlankStartEvent, [proc, start("start1")], []));
  // FE: "multiple blank start events in root process" — 1 finding on process1
  {
    const f = run(validateSingleBlankStartEvent, [proc, start("start1"), start("start2")], []);
    expectCodeCount("multiple blank root", f, "MULTIPLE_BLANK_START_EVENTS", 1);
    check("blank root elementId process1", f[0]?.elementId === "process1", f[0]?.elementId);
  }
  // FE: "single blank start in subprocess"
  expectEmpty("single blank subprocess", run(validateSingleBlankStartEvent, [proc, sp("subprocess1"), start("start1", "subprocess1")], []));
  // FE: "multiple blank start events in subprocess" — 1 finding on subprocess1
  {
    const f = run(validateSingleBlankStartEvent, [proc, sp("subprocess1"), start("start1", "subprocess1"), start("start2", "subprocess1")], []);
    expectCodeCount("multiple blank subprocess", f, "MULTIPLE_BLANK_START_EVENTS", 1);
    check("blank subprocess elementId subprocess1", f[0]?.elementId === "subprocess1", f[0]?.elementId);
  }
  // FE: "should not count non-blank start events"
  expectEmpty("non-blank not counted", run(validateSingleBlankStartEvent, [proc, start("start1"), start("start2", undefined, { id: "timer1", type: "bpmn:TimerEventDefinition" })], []));
  // FE: "independent scopes"
  {
    const nodes = [proc, sp("subprocess1"), sp("subprocess2"), start("start1"), start("start2", "subprocess1"), start("start3", "subprocess2")];
    expectEmpty("independent scopes one blank each", run(validateSingleBlankStartEvent, nodes, []));
  }
}

// ===========================================================================
// 16. SingleStartEventInEventSubProcessRule
// ===========================================================================
suite("SingleStartEventInEventSubProcessRule");
{
  const sp = (id, triggeredByEvent) => node(id, "bpmn:SubProcess", triggeredByEvent ? { triggeredByEvent: true } : {});
  const start = (id, parentId, ed) => node(id, "bpmn:StartEvent", ed ? { eventDefinition: ed } : {}, { parentId });

  // FE: "should allow event subprocess with one start event"
  expectEmpty("one start in event subprocess", run(validateSingleStartEventInEventSubProcess, [sp("subprocess1", true), start("start1", "subprocess1", { type: "bpmn:TimerEventDefinition" })], []));
  // FE: "should allow regular subprocess with multiple start events"
  expectEmpty("regular subprocess multiple starts", run(validateSingleStartEventInEventSubProcess, [sp("subprocess1", false), start("start1", "subprocess1"), start("start2", "subprocess1")], []));
  // FE: "should detect multiple start events in event subprocess"
  {
    const nodes = [sp("subprocess1", true), start("start1", "subprocess1", { type: "bpmn:TimerEventDefinition" }), start("start2", "subprocess1", { type: "bpmn:MessageEventDefinition" })];
    expectCodeCount("two starts event subprocess", run(validateSingleStartEventInEventSubProcess, nodes, []), "MULTIPLE_START_EVENTS_IN_EVENT_SUBPROCESS", 1);
  }
  // FE: "...with three start events"
  {
    const nodes = [sp("subprocess1", true), start("s1", "subprocess1", { type: "bpmn:TimerEventDefinition" }), start("s2", "subprocess1", { type: "bpmn:MessageEventDefinition" }), start("s3", "subprocess1", { type: "bpmn:ErrorEventDefinition" })];
    expectCodeCount("three starts event subprocess", run(validateSingleStartEventInEventSubProcess, nodes, []), "MULTIPLE_START_EVENTS_IN_EVENT_SUBPROCESS", 1);
  }
  // FE: "should not flag event subprocess with no start events"
  expectEmpty("no starts event subprocess", run(validateSingleStartEventInEventSubProcess, [sp("subprocess1", true)], []));
}

// ===========================================================================
// 17. SuperfluousGatewayRule
// ===========================================================================
suite("SuperfluousGatewayRule");
{
  expectEmpty("null nodes", validateSuperfluousGateway(null, [], maps([], [])));
  expectEmpty("null edges", validateSuperfluousGateway([], null, maps([], [])));
  // FE: "should return empty array when no gateways present"
  expectEmpty("no gateways", run(validateSuperfluousGateway, [node("1", "bpmn:Task")], []));
  // FE: "should detect superfluous gateway with exactly one input and output"
  {
    const nodes = [node("gateway1", "bpmn:ExclusiveGateway")];
    const edges = [edge("e1", "start", "gateway1"), edge("e2", "gateway1", "end")];
    expectCodeCount("superfluous 1in1out", run(validateSuperfluousGateway, nodes, edges), "SUPERFLUOUS_GATEWAY", 1);
  }
  // FE: "should not flag gateway with multiple inputs"
  {
    const nodes = [node("gateway1", "bpmn:ParallelGateway")];
    const edges = [edge("e1", "start1", "gateway1"), edge("e2", "start2", "gateway1"), edge("e3", "gateway1", "end")];
    expectEmpty("multiple inputs", run(validateSuperfluousGateway, nodes, edges));
  }
  // FE: "should not flag gateway with multiple outputs"
  {
    const nodes = [node("gateway1", "bpmn:InclusiveGateway")];
    const edges = [edge("e1", "start", "gateway1"), edge("e2", "gateway1", "end1"), edge("e3", "gateway1", "end2")];
    expectEmpty("multiple outputs", run(validateSuperfluousGateway, nodes, edges));
  }
  // FE: "should handle multiple gateways correctly"
  {
    const nodes = [node("gateway1", "bpmn:ExclusiveGateway"), node("gateway2", "bpmn:ParallelGateway")];
    const edges = [edge("e1", "start", "gateway1"), edge("e2", "gateway1", "gateway2"), edge("e3", "x", "gateway2"), edge("e4", "gateway2", "end1"), edge("e5", "gateway2", "end2")];
    // gateway1: 1 in (e1), 1 out (e2) -> superfluous. gateway2: 2 in (e2,e3), 2 out -> fine.
    const f = run(validateSuperfluousGateway, nodes, edges);
    expectCodeCount("multiple gateways", f, "SUPERFLUOUS_GATEWAY", 1);
    check("superfluous is gateway1", f[0]?.elementId === "gateway1", f[0]?.elementId);
  }
}

// ===========================================================================
// 18. TaskTimerRule (WARNING)
// ===========================================================================
suite("TaskTimerRule");
{
  const action = (timerValue, label = "My Action", id = "node-1") =>
    node(id, "bpmn:ServiceTask", { label, uipath: { serviceType: "actions", context: timerValue !== undefined ? [{ name: "Timer", value: String(timerValue), type: "number" }] : [] } });

  expectEmpty("null nodes", validateTaskTimerRange(null));
  expectEmpty("empty nodes", validateTaskTimerRange([]));
  // FE: "ignores nodes that are not action service tasks"
  expectEmpty("non-action service task", validateTaskTimerRange([node("node-1", "bpmn:ServiceTask", { uipath: { serviceType: "automation", context: [{ name: "Timer", value: "5", type: "number" }] } })]));
  // FE: "ignores action nodes with no Timer context entry"
  expectEmpty("no Timer entry", validateTaskTimerRange([action(undefined)]));
  // FE: "ignores empty Timer value"
  expectEmpty("empty Timer", validateTaskTimerRange([action("")]));
  // FE: "ignores Timer set to a variable reference (@)"
  expectEmpty("@ Timer", validateTaskTimerRange([action("@in_timerMinutes")]));
  // FE: "ignores Timer set to an expression (=)"
  expectEmpty("= Timer", validateTaskTimerRange([action("=someExpression")]));
  // FE: min/max/in-range valid
  expectEmpty("min 15", validateTaskTimerRange([action(15)]));
  expectEmpty("max 129600", validateTaskTimerRange([action(129600)]));
  expectEmpty("in range 60", validateTaskTimerRange([action(60)]));
  expectEmpty("numeric string 1440", validateTaskTimerRange([action("1440")]));
  // FE: out-of-range warnings
  expectCodeCount("below min 14", validateTaskTimerRange([action(14)]), "TASK_TIMER_OUT_OF_RANGE", 1);
  expectCodeCount("zero", validateTaskTimerRange([action(0)]), "TASK_TIMER_OUT_OF_RANGE", 1);
  expectCodeCount("above max 129601", validateTaskTimerRange([action(129601)]), "TASK_TIMER_OUT_OF_RANGE", 1);
  // FE: "only warns on out-of-range action nodes, not valid ones"
  expectCodeCount("mixed only out-of-range", validateTaskTimerRange([action(5, "a", "n1"), action(60, "b", "n2"), action(129601, "c", "n3")]), "TASK_TIMER_OUT_OF_RANGE", 2);
  // FE: "ignores non-numeric Timer values"
  expectEmpty("non-numeric", validateTaskTimerRange([action("not-a-number")]));
}

// ===========================================================================
// 19. TimerDurationRule
// ===========================================================================
suite("TimerDurationRule");
{
  const timer = (timeDuration, id = "node-1", timerType = "timeDuration") =>
    node(id, "bpmn:IntermediateCatchEvent", { label: "My Timer", eventDefinition: { timerType, timeDuration } });

  expectEmpty("null nodes", validateTimerDuration(null));
  expectEmpty("empty nodes", validateTimerDuration([]));
  // FE: "ignores nodes without an eventDefinition"
  expectEmpty("no eventDefinition", validateTimerDuration([node("n1", "bpmn:Task", { label: "Task" })]));
  // FE: "ignores timer events whose timerType is not timeDuration"
  expectEmpty("non-timeDuration timerType", validateTimerDuration([timer("P5W", "n1", "timeDate")]));
  // FE: "ignores an empty duration value"
  expectEmpty("empty duration", validateTimerDuration([timer("")]));
  // FE: "ignores = and @ prefixed"
  expectEmpty("= duration", validateTimerDuration([timer("=myVar")]));
  expectEmpty("@ duration", validateTimerDuration([timer("@in_duration")]));
  // FE: "valid ISO 8601 duration"
  expectEmpty("valid PT15M", validateTimerDuration([timer("PT15M")]));
  // FE: "malformed -> TIMER_DURATION_INVALID (ERROR)"
  expectCodeCount("malformed P5X", validateTimerDuration([timer("P5X")]), "TIMER_DURATION_INVALID", 1);
  // FE: "week designator -> TIMER_DURATION_WEEK_UNSUPPORTED (WARNING)"
  expectCodeCount("week P5W", validateTimerDuration([timer("P5W")]), "TIMER_DURATION_WEEK_UNSUPPORTED", 1);
}

// ===========================================================================
// 20. Variable existence — result.X element-local validity
// (VariableUtil.isResultVariableValidForElement:166-178; the non-existing split
//  at :758-782; getVariablesInExpression treating an unresolved result ref as
//  non-existing at :263). result.X is valid ONLY if X names one of the
//  referencing element's OWN outputs; otherwise VARIABLE_DOES_NOT_EXIST fires.
// ===========================================================================
suite("ResultVariableExistence");
{
  // FE: "should not return a validation error for result namespace when it matches current element outputs"
  // node1 declares output var "outputVar" → result.outputVar is valid.
  {
    const n1 = node("node1", "bpmn:ServiceTask", { uipath: { outputs: [{ name: "outputVar", var: "outputVar", custom: true, source: "=result.outputVar", type: "string" }] } });
    const f = validateVariableExistence([n1], [], new Set());
    expectNone("result.X matches own output → no DOES_NOT_EXIST", f, "VARIABLE_DOES_NOT_EXIST");
  }
  // FE: "should return a validation error for result namespace when it does not match current element outputs"
  // node1 has output "outputVar" but references result.missingVar → invalid.
  {
    const n1 = node("node1", "bpmn:ServiceTask", { uipath: { inputs: [{ name: "i", value: "=result.missingVar" }], outputs: [{ name: "outputVar", var: "outputVar" }] } });
    const f = validateVariableExistence([n1], [], new Set());
    expectCodeCount("result.X not an output → DOES_NOT_EXIST", f, "VARIABLE_DOES_NOT_EXIST", 1);
  }
  // FE: getVariablesInExpression "should return the correct result variable in the expression"
  // An edge condition has no element-local outputs → result.myVar is non-existing.
  {
    const e1 = edge("edge1", "a", "b", { data: { conditionExpression: "=result.myVar" } });
    const f = validateVariableExistence([], [e1], new Set());
    expectCodeCount("edge result.X → DOES_NOT_EXIST", f, "VARIABLE_DOES_NOT_EXIST", 1);
  }
}

// ===========================================================================
// 21. VARIABLE_NOT_SET — flow-order reachability (WARNING)
// Port of validateVariablesInExpression:758-866 (the reachability half). A
// DECLARED variable referenced where no flow path reaches its producer fires
// VARIABLE_NOT_SET. Tested at the model level (allNodes/allEdges/knownIds/cs),
// mirroring validateVariablesInAllNodesAndEdges.
// ===========================================================================
suite("VariableNotSet");
{
  // Helper: canvasState with given root vars + diagram nodes/edges.
  const csFor = (rootInputOutputs, nodes, edges) => canvasState({ rootVariables: { inputs: [], inputOutputs: rootInputOutputs, outputs: [] }, diagramNodes: nodes, diagramEdges: edges });

  // FE: "should return a validation error if a variable is used before it is set"
  // edge node1->node2 references vars.myVar; myVar is declared (known) but not
  // produced on any path reaching the edge → exactly 1 VARIABLE_NOT_SET.
  {
    const n1 = node("node1", "bpmn:Task", {});
    const n2 = node("node2", "bpmn:Task", {});
    const e1 = edge("edge1", "node1", "node2", { data: { conditionExpression: "=vars.myVar" } });
    const known = new Set(["myVar"]); // declared somewhere, but not reachable here
    const cs = csFor([], [n1, n2], [e1]);
    const f = validateVariableNotSet([n1, n2], [e1], known, cs);
    expectCodeCount("used before set → NOT_SET", f, "VARIABLE_NOT_SET", 1);
  }
  // FE: "should not return a validation error if a variable used is a root variable"
  // Same graph but myVar is a ROOT variable → globally available → no NOT_SET.
  {
    const n1 = node("node1", "bpmn:Task", {});
    const n2 = node("node2", "bpmn:Task", {});
    const e1 = edge("edge1", "node1", "node2", { data: { conditionExpression: "=vars.myVar" } });
    const known = new Set(["myVar"]);
    const cs = csFor([{ id: "myVar", name: "myVarName", type: "string" }], [n1, n2], [e1]);
    const f = validateVariableNotSet([n1, n2], [e1], known, cs);
    expectNone("root variable → no NOT_SET", f, "VARIABLE_NOT_SET");
  }
  // Reachable producer → no NOT_SET: node A produces var, node B (downstream)
  // references it; B's backward walk reaches A.
  {
    const a = node("A", "bpmn:ServiceTask", { uipath: { outputs: [{ name: "o", var: "produced", custom: true, source: "x", type: "string" }] } });
    const b = node("B", "bpmn:ServiceTask", { uipath: { inputs: [{ name: "i", value: "=vars.produced" }] } });
    const e1 = edge("A_B", "A", "B", { data: {} });
    const known = new Set(["produced"]);
    const cs = csFor([], [a, b], [e1]);
    const f = validateVariableNotSet([a, b], [e1], known, cs);
    expectNone("reachable producer → no NOT_SET", f, "VARIABLE_NOT_SET");
  }
  // Producer downstream → NOT_SET: node A (upstream) references a var produced by
  // node B (downstream), unreachable at A.
  {
    const a = node("A", "bpmn:ServiceTask", { uipath: { inputs: [{ name: "i", value: "=vars.fromB" }] } });
    const b = node("B", "bpmn:ServiceTask", { uipath: { outputs: [{ name: "o", var: "fromB", custom: true, source: "x", type: "string" }] } });
    const e1 = edge("A_B", "A", "B", { data: {} });
    const known = new Set(["fromB"]);
    const cs = csFor([], [a, b], [e1]);
    const f = validateVariableNotSet([a, b], [e1], known, cs);
    expectCodeCount("downstream producer → NOT_SET at A", f, "VARIABLE_NOT_SET", 1);
  }
  // Case Management is skipped entirely (VariableUtil.ts:826-828).
  {
    const n1 = node("node1", "bpmn:Task", {});
    const n2 = node("node2", "bpmn:Task", {});
    const e1 = edge("edge1", "node1", "node2", { data: { conditionExpression: "=vars.myVar" } });
    const cs = csFor([], [n1, n2], [e1]);
    const f = validateVariableNotSet([n1, n2], [e1], new Set(["myVar"]), cs, { isCaseManagement: true });
    expectEmpty("case management skipped", f);
  }
}

export default results;
