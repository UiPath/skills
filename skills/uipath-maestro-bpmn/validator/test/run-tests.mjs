#!/usr/bin/env node
// Rule-coverage test harness. For each of the 19 PO.Frontend rules (+ the
// Maestro-original variable-existence check) it builds a minimal invalid BPMN
// that should trip exactly that rule, and asserts the rule's code is emitted.
// It also asserts a valid twin produces NO finding for that code.
//
// Run: node test/run-tests.mjs   (exit 0 = all rules fire correctly)
import BpmnModdle from "bpmn-moddle";
import descriptor from "../uipath-moddle.v1.json" with { type: "json" };
import { buildModel, collectKnownVariableIds, allNodes, allEdges } from "../model.mjs";
import { validateDiagram, validateVariableExistence } from "../rules.mjs";

const moddle = new BpmnModdle({ uipath: descriptor });

async function findingsFor(xml) {
  const { rootElement } = await moddle.fromXML(xml);
  const cs = buildModel(rootElement);
  const knownIds = collectKnownVariableIds(cs);
  const out = [];
  for (const d of Object.values(cs.diagramsById)) {
    out.push(...validateDiagram(d, cs, { enableMissingRootVariableValidation: true }));
  }
  out.push(...validateVariableExistence(allNodes(cs), allEdges(cs), knownIds));
  return out;
}

// ---- XML builders -------------------------------------------------------
const DEFS = (inner) =>
  `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:uipath="http://uipath.org/schema/bpmn" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Defs" targetNamespace="urn:test">
${inner}
</bpmn:definitions>`;
const PROC = (body, ext = "") => `  <bpmn:process id="P" name="P" isExecutable="true">${ext}\n${body}\n  </bpmn:process>`;
const COND = (s, t, expr) =>
  `    <bpmn:sequenceFlow id="${s}_${t}" sourceRef="${s}" targetRef="${t}"><bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">${expr}</bpmn:conditionExpression></bpmn:sequenceFlow>`;
const FLOW = (s, t, id) => `    <bpmn:sequenceFlow id="${id ?? s + "_" + t}" sourceRef="${s}" targetRef="${t}" />`;

// ---- Per-rule cases -----------------------------------------------------
const cases = [];
const add = (code, xml, note) => cases.push({ code, xml, note });

// 1 MISSING_CONDITION_EXPRESSION: XOR with 2 outgoing, no default, no conditions
add(
  "MISSING_CONDITION_EXPRESSION",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_G</bpmn:outgoing></bpmn:startEvent>
    <bpmn:exclusiveGateway id="G"><bpmn:incoming>S_G</bpmn:incoming><bpmn:outgoing>G_A</bpmn:outgoing><bpmn:outgoing>G_B</bpmn:outgoing></bpmn:exclusiveGateway>
    <bpmn:task id="A"><bpmn:incoming>G_A</bpmn:incoming></bpmn:task>
    <bpmn:task id="B"><bpmn:incoming>G_B</bpmn:incoming></bpmn:task>
${FLOW("S", "G", "S_G")}
${FLOW("G", "A", "G_A")}
${FLOW("G", "B", "G_B")}`,
    ),
  ),
);

// 2 INVALID_CONNECTION_TYPE: EndEvent -> Task
add(
  "INVALID_CONNECTION_TYPE",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_E</bpmn:outgoing></bpmn:startEvent>
    <bpmn:endEvent id="E"><bpmn:incoming>S_E</bpmn:incoming><bpmn:outgoing>E_T</bpmn:outgoing></bpmn:endEvent>
    <bpmn:task id="T"><bpmn:incoming>E_T</bpmn:incoming></bpmn:task>
${FLOW("S", "E", "S_E")}
${FLOW("E", "T", "E_T")}`,
    ),
  ),
);

// 3 DUPLICATE_ERROR_EVENT_SUBPROCESS: two event subprocesses, same error code
add(
  "DUPLICATE_ERROR_EVENT_SUBPROCESS",
  DEFS(
    `  <bpmn:error id="Err1" name="E1" errorCode="CODE_X" />
${PROC(
  `    <bpmn:startEvent id="S"><bpmn:outgoing>S_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:task id="T"><bpmn:incoming>S_T</bpmn:incoming><bpmn:outgoing>T_E</bpmn:outgoing></bpmn:task>
    <bpmn:endEvent id="E"><bpmn:incoming>T_E</bpmn:incoming></bpmn:endEvent>
    <bpmn:subProcess id="SP1" triggeredByEvent="true">
      <bpmn:startEvent id="SP1S"><bpmn:errorEventDefinition id="ed1" errorRef="Err1" /></bpmn:startEvent>
    </bpmn:subProcess>
    <bpmn:subProcess id="SP2" triggeredByEvent="true">
      <bpmn:startEvent id="SP2S"><bpmn:errorEventDefinition id="ed2" errorRef="Err1" /></bpmn:startEvent>
    </bpmn:subProcess>
${FLOW("S", "T", "S_T")}
${FLOW("T", "E", "T_E")}`,
)}`,
  ),
);

// 4 START_EVENT_WITH_DEFINITION_IN_SUBPROCESS: regular subprocess start has timer def
add(
  "START_EVENT_WITH_DEFINITION_IN_SUBPROCESS",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_SP</bpmn:outgoing></bpmn:startEvent>
    <bpmn:subProcess id="SP"><bpmn:incoming>S_SP</bpmn:incoming><bpmn:outgoing>SP_E</bpmn:outgoing>
      <bpmn:startEvent id="SPS"><bpmn:timerEventDefinition id="t1"><bpmn:timeDuration>PT5M</bpmn:timeDuration></bpmn:timerEventDefinition></bpmn:startEvent>
    </bpmn:subProcess>
    <bpmn:endEvent id="E"><bpmn:incoming>SP_E</bpmn:incoming></bpmn:endEvent>
${FLOW("S", "SP", "S_SP")}
${FLOW("SP", "E", "SP_E")}`,
    ),
  ),
);

// 4b START_EVENT_WITHOUT_DEFINITION_IN_EVENT_SUBPROCESS
add(
  "START_EVENT_WITHOUT_DEFINITION_IN_EVENT_SUBPROCESS",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:task id="T"><bpmn:incoming>S_T</bpmn:incoming></bpmn:task>
    <bpmn:subProcess id="SP" triggeredByEvent="true">
      <bpmn:startEvent id="SPS" />
    </bpmn:subProcess>
${FLOW("S", "T", "S_T")}`,
    ),
  ),
);

// 5 ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE: boundary refs an Error with no errorCode
add(
  "ERROR_BOUNDARY_EVENT_REQUIRES_ERROR_CODE",
  DEFS(
    `  <bpmn:error id="ErrNoCode" name="NoCode" />
${PROC(
  `    <bpmn:startEvent id="S"><bpmn:outgoing>S_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:task id="T"><bpmn:incoming>S_T</bpmn:incoming></bpmn:task>
    <bpmn:boundaryEvent id="BE" attachedToRef="T"><bpmn:errorEventDefinition id="bed" errorRef="ErrNoCode" /></bpmn:boundaryEvent>
${FLOW("S", "T", "S_T")}`,
)}`,
  ),
);

// 5b MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK: two catch-all error boundaries on one task
add(
  "MULTIPLE_CATCH_ALL_BOUNDARY_EVENTS_ON_TASK",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:task id="T"><bpmn:incoming>S_T</bpmn:incoming></bpmn:task>
    <bpmn:boundaryEvent id="BE1" attachedToRef="T"><bpmn:errorEventDefinition id="bed1" /></bpmn:boundaryEvent>
    <bpmn:boundaryEvent id="BE2" attachedToRef="T"><bpmn:errorEventDefinition id="bed2" /></bpmn:boundaryEvent>
${FLOW("S", "T", "S_T")}`,
    ),
  ),
);

// 6 ERROR_END_EVENT_MISSING_EXCEPTION: error end event with no errorRef
add(
  "ERROR_END_EVENT_MISSING_EXCEPTION",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_E</bpmn:outgoing></bpmn:startEvent>
    <bpmn:endEvent id="E"><bpmn:incoming>S_E</bpmn:incoming><bpmn:errorEventDefinition id="eed" /></bpmn:endEvent>
${FLOW("S", "E", "S_E")}`,
    ),
  ),
);

// 7 FAKE_JOIN: task with two incoming flows
add(
  "FAKE_JOIN",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:task id="T0"><bpmn:outgoing>T0_T</bpmn:outgoing></bpmn:task>
    <bpmn:task id="T"><bpmn:incoming>S_T</bpmn:incoming><bpmn:incoming>T0_T</bpmn:incoming></bpmn:task>
${FLOW("S", "T", "S_T")}
${FLOW("T0", "T", "T0_T")}`,
    ),
  ),
);

// 8 SAME_POOL_MESSAGE_FLOW: message flow between two nodes in the same pool
add(
  "SAME_POOL_MESSAGE_FLOW",
  DEFS(
    `  <bpmn:collaboration id="C">
    <bpmn:participant id="Pool1" name="Pool 1" processRef="P" />
    <bpmn:messageFlow id="MF" sourceRef="T1" targetRef="T2" />
  </bpmn:collaboration>
  <bpmn:process id="P" isExecutable="true">
    <bpmn:task id="T1" />
    <bpmn:task id="T2" />
  </bpmn:process>`,
  ),
);

// 9 MISSING_RESOURCE: Orchestrator.StartJob with no resource binding (WARNING)
add(
  "MISSING_RESOURCE",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:serviceTask id="T" name="Start Job"><bpmn:incoming>S_T</bpmn:incoming>
      <bpmn:extensionElements><uipath:activity version="v1"><uipath:type value="Orchestrator.StartJob" version="v1" /></uipath:activity></bpmn:extensionElements>
    </bpmn:serviceTask>
${FLOW("S", "T", "S_T")}`,
    ),
  ),
);

// 10 MISSING_ROOT_VARIABLE: node output var not declared at root (WARNING)
add(
  "MISSING_ROOT_VARIABLE",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:serviceTask id="T" name="Job"><bpmn:incoming>S_T</bpmn:incoming>
      <bpmn:extensionElements><uipath:activity version="v1"><uipath:type value="Orchestrator.StartJob" version="v1" />
        <uipath:context><uipath:input name="name" value="X" /></uipath:context>
        <uipath:output name="JobState" type="string" var="Var_Undeclared" source="state" custom="true" />
      </uipath:activity></bpmn:extensionElements>
    </bpmn:serviceTask>
${FLOW("S", "T", "S_T")}`,
      `\n    <bpmn:extensionElements><uipath:variables version="v1"><uipath:input id="Var_Other" name="other" type="string" /></uipath:variables></bpmn:extensionElements>`,
    ),
  ),
);

// 11 ASSIGNMENT_NOT_ALLOWED: condition contains an assignment (WARNING)
add(
  "ASSIGNMENT_NOT_ALLOWED",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_G</bpmn:outgoing></bpmn:startEvent>
    <bpmn:exclusiveGateway id="G" default="G_B"><bpmn:incoming>S_G</bpmn:incoming><bpmn:outgoing>G_A</bpmn:outgoing><bpmn:outgoing>G_B</bpmn:outgoing></bpmn:exclusiveGateway>
    <bpmn:task id="A"><bpmn:incoming>G_A</bpmn:incoming></bpmn:task>
    <bpmn:task id="B"><bpmn:incoming>G_B</bpmn:incoming></bpmn:task>
${FLOW("S", "G", "S_G")}
${COND("G", "A", "=vars.x = 5")}
${FLOW("G", "B", "G_B")}`,
    ),
  ),
);

// 12 EMPTY_REQUIRED_FIELD: HttpExecution with required 'url' present but empty
add(
  "EMPTY_REQUIRED_FIELD",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:serviceTask id="T" name="HTTP"><bpmn:incoming>S_T</bpmn:incoming>
      <bpmn:extensionElements><uipath:activity version="v1"><uipath:type value="Intsvc.HttpExecution" version="v1" />
        <uipath:context><uipath:input name="method" value="GET" /><uipath:input name="url" value="" /></uipath:context>
      </uipath:activity></bpmn:extensionElements>
    </bpmn:serviceTask>
${FLOW("S", "T", "S_T")}`,
    ),
  ),
);

// 13 CROSSING_POOL_BOUNDARY: sequence flow between two pools (non-start target)
add(
  "CROSSING_POOL_BOUNDARY",
  DEFS(
    `  <bpmn:collaboration id="C">
    <bpmn:participant id="Pool1" name="P1" processRef="P" />
    <bpmn:participant id="Pool2" name="P2" processRef="P2" />
  </bpmn:collaboration>
  <bpmn:process id="P" isExecutable="true">
    <bpmn:task id="T1"><bpmn:outgoing>T1_T2</bpmn:outgoing></bpmn:task>
${FLOW("T1", "T2", "T1_T2")}
  </bpmn:process>
  <bpmn:process id="P2" isExecutable="true">
    <bpmn:task id="T2"><bpmn:incoming>T1_T2</bpmn:incoming></bpmn:task>
  </bpmn:process>`,
  ),
  "cross-pool",
);

// 14 CROSSING_SUBPROCESS_BOUNDARY: flow from outside into a subprocess child
add(
  "CROSSING_SUBPROCESS_BOUNDARY",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_C</bpmn:outgoing></bpmn:startEvent>
    <bpmn:subProcess id="SP">
      <bpmn:task id="C" />
    </bpmn:subProcess>
${FLOW("S", "C", "S_C")}`,
    ),
  ),
);

// 15 MULTIPLE_BLANK_START_EVENTS: process with two blank start events
add(
  "MULTIPLE_BLANK_START_EVENTS",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S1"><bpmn:outgoing>S1_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:startEvent id="S2"><bpmn:outgoing>S2_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:task id="T"><bpmn:incoming>S1_T</bpmn:incoming></bpmn:task>
    <bpmn:task id="T2"><bpmn:incoming>S2_T</bpmn:incoming></bpmn:task>
${FLOW("S1", "T", "S1_T")}
${FLOW("S2", "T2", "S2_T")}`,
    ),
  ),
);

// 16 MULTIPLE_START_EVENTS_IN_EVENT_SUBPROCESS
add(
  "MULTIPLE_START_EVENTS_IN_EVENT_SUBPROCESS",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:task id="T"><bpmn:incoming>S_T</bpmn:incoming></bpmn:task>
    <bpmn:subProcess id="SP" triggeredByEvent="true">
      <bpmn:startEvent id="SPS1"><bpmn:timerEventDefinition id="t1"><bpmn:timeDuration>PT5M</bpmn:timeDuration></bpmn:timerEventDefinition></bpmn:startEvent>
      <bpmn:startEvent id="SPS2"><bpmn:timerEventDefinition id="t2"><bpmn:timeDuration>PT5M</bpmn:timeDuration></bpmn:timerEventDefinition></bpmn:startEvent>
    </bpmn:subProcess>
${FLOW("S", "T", "S_T")}`,
    ),
  ),
);

// 17 SUPERFLUOUS_GATEWAY: gateway with exactly one in and one out
add(
  "SUPERFLUOUS_GATEWAY",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_G</bpmn:outgoing></bpmn:startEvent>
    <bpmn:exclusiveGateway id="G"><bpmn:incoming>S_G</bpmn:incoming><bpmn:outgoing>G_T</bpmn:outgoing></bpmn:exclusiveGateway>
    <bpmn:task id="T"><bpmn:incoming>G_T</bpmn:incoming></bpmn:task>
${FLOW("S", "G", "S_G")}
${FLOW("G", "T", "G_T")}`,
    ),
  ),
);

// 18 TASK_TIMER_OUT_OF_RANGE: actions task Timer below 15 minutes (WARNING)
add(
  "TASK_TIMER_OUT_OF_RANGE",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_T</bpmn:outgoing></bpmn:startEvent>
    <bpmn:userTask id="T" name="HITL"><bpmn:incoming>S_T</bpmn:incoming>
      <bpmn:extensionElements><uipath:activity version="v1"><uipath:type value="actions" version="v1" />
        <uipath:context><uipath:input name="Timer" value="5" /></uipath:context>
      </uipath:activity></bpmn:extensionElements>
    </bpmn:userTask>
${FLOW("S", "T", "S_T")}`,
    ),
  ),
);

// 19 TIMER_DURATION_INVALID: timer intermediate event with bad ISO duration
add(
  "TIMER_DURATION_INVALID",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_I</bpmn:outgoing></bpmn:startEvent>
    <bpmn:intermediateCatchEvent id="I"><bpmn:incoming>S_I</bpmn:incoming><bpmn:outgoing>I_E</bpmn:outgoing>
      <bpmn:timerEventDefinition id="td"><bpmn:timeDuration>NOT_A_DURATION</bpmn:timeDuration></bpmn:timerEventDefinition>
    </bpmn:intermediateCatchEvent>
    <bpmn:endEvent id="E"><bpmn:incoming>I_E</bpmn:incoming></bpmn:endEvent>
${FLOW("S", "I", "S_I")}
${FLOW("I", "E", "I_E")}`,
    ),
  ),
);

// 19b TIMER_DURATION_WEEK_UNSUPPORTED: valid ISO with week designator (WARNING)
add(
  "TIMER_DURATION_WEEK_UNSUPPORTED",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_I</bpmn:outgoing></bpmn:startEvent>
    <bpmn:intermediateCatchEvent id="I"><bpmn:incoming>S_I</bpmn:incoming><bpmn:outgoing>I_E</bpmn:outgoing>
      <bpmn:timerEventDefinition id="td"><bpmn:timeDuration>P1W</bpmn:timeDuration></bpmn:timerEventDefinition>
    </bpmn:intermediateCatchEvent>
    <bpmn:endEvent id="E"><bpmn:incoming>I_E</bpmn:incoming></bpmn:endEvent>
${FLOW("S", "I", "S_I")}
${FLOW("I", "E", "I_E")}`,
    ),
  ),
);

// 20 VARIABLE_DOES_NOT_EXIST: condition references undeclared vars.X (Maestro-original)
add(
  "VARIABLE_DOES_NOT_EXIST",
  DEFS(
    PROC(
      `    <bpmn:startEvent id="S"><bpmn:outgoing>S_G</bpmn:outgoing></bpmn:startEvent>
    <bpmn:exclusiveGateway id="G" default="G_B"><bpmn:incoming>S_G</bpmn:incoming><bpmn:outgoing>G_A</bpmn:outgoing><bpmn:outgoing>G_B</bpmn:outgoing></bpmn:exclusiveGateway>
    <bpmn:task id="A"><bpmn:incoming>G_A</bpmn:incoming></bpmn:task>
    <bpmn:task id="B"><bpmn:incoming>G_B</bpmn:incoming></bpmn:task>
${FLOW("S", "G", "S_G")}
${COND("G", "A", '=vars.DoesNotExist == "x"')}
${FLOW("G", "B", "G_B")}`,
    ),
  ),
);

// ---- Run ----------------------------------------------------------------
let failures = 0;
const fired = new Set();
for (const c of cases) {
  const findings = await findingsFor(c.xml);
  const codes = findings.map((f) => f.code);
  const ok = codes.includes(c.code);
  if (ok) fired.add(c.code);
  const tag = ok ? "PASS" : "FAIL";
  if (!ok) failures++;
  console.log(`${tag}  ${c.code}${c.note ? " (" + c.note + ")" : ""}  -> [${[...new Set(codes)].join(", ") || "none"}]`);
}

console.log(`\n${cases.length} cases, ${cases.length - failures} passed, ${failures} failed.`);
console.log(`distinct rule codes fired: ${fired.size}`);
process.exit(failures === 0 ? 0 : 1);
