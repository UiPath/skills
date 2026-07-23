// Integration suite over REAL .bpmn files — the strongest defense against drift
// in the hand-port. Every file here is a real, externally-validated artifact:
//   - Backend BpmnParser/Worker/Athena/V2-E2E TestData (parsed & executed by the
//     .NET engine in PO.BpmnEngine tests).
//   - PO.Frontend editor mock fixtures (PO.Frontend/mocks/files).
// They are bundled under test/fixtures/ so this suite is self-contained and runs
// in CI without any sibling checkout.
//
// Each file is run through the full pipeline (bpmn-moddle parse -> model.mjs ->
// rules.mjs):
//   - test/fixtures/known-good/*       : must produce ZERO ERROR-severity findings
//                                        (warnings allowed). Complete, execution-
//                                        validated workflows + clean editor mocks.
//   - test/fixtures/expected-findings/*: genuinely violate a rule the frontend
//                                        would also flag (verified by reading the
//                                        file); assert the exact ERROR codes fire.
//
// Optionally, set MAESTRO_BPMN_TESTDATA / MAESTRO_BPMN_FRONTEND_MOCKS to also
// sweep a live corpus (used during development; absent in CI).

import { readFileSync, existsSync, readdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import BpmnModdle from "bpmn-moddle";
import descriptor from "../uipath-moddle.v1.json" with { type: "json" };
import { buildModel, collectKnownVariableIds, allNodes, allEdges } from "../model.mjs";
import { validateDiagram, validateVariableExistence, validateVariableNotSet } from "../rules.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const moddle = new BpmnModdle({ uipath: descriptor });

async function errorCodesFor(xml) {
  const { rootElement } = await moddle.fromXML(xml);
  const cs = buildModel(rootElement);
  const knownIds = collectKnownVariableIds(cs);
  const out = [];
  for (const d of Object.values(cs.diagramsById)) out.push(...validateDiagram(d, cs, { enableMissingRootVariableValidation: true }));
  out.push(...validateVariableExistence(allNodes(cs), allEdges(cs), knownIds));
  // VARIABLE_NOT_SET is WARNING-only; included so its topology walk runs on real
  // files (filtered out of the ERROR set below, so it can't break known-good).
  out.push(...validateVariableNotSet(allNodes(cs), allEdges(cs), knownIds, cs));
  return [...new Set(out.filter((f) => f.severity === "ERROR").map((f) => f.code))].sort();
}

// ---- Expected ERROR codes for the bundled expected-findings fixtures -------
// Verified by inspecting each file; the frontend rule would flag the same issue.
const EXPECTED_ERROR_CODES = {
  "ExclusiveGatewayDefaultFlow.bpmn": ["SUPERFLUOUS_GATEWAY"], // XOR with a single in + single out
  "StartGatewayEnd.bpmn": ["SUPERFLUOUS_GATEWAY"], // gateway 1-in/1-out
  "InclusiveJoinRouteAwayBranch.bpmn": ["MISSING_CONDITION_EXPRESSION"], // branch lacks condition
  "Parse_SubProcess_With_Multiple_Element_Types.bpmn": ["MISSING_CONDITION_EXPRESSION"],
  "Can_Parse_Complex_Process_With_Task_Gateway_BoundaryEvent_etc.bpmn": ["MISSING_CONDITION_EXPRESSION", "TIMER_DURATION_INVALID"],
  // Dangling vars.* references (runtime-injected, not declared in-file):
  "Parse_AsyncExecution_And_Create_CorrectModel.bpmn": ["VARIABLE_DOES_NOT_EXIST"],
  "Parse_IXP_Extraction_FileUpload_And_Create_CorrectModel.bpmn": ["VARIABLE_DOES_NOT_EXIST"],
  "Parse_IXP_Extraction_JobAttachment_And_Create_CorrectModel.bpmn": ["VARIABLE_DOES_NOT_EXIST"],
  "Parse_IXP_ExtractionValidation_And_Create_CorrectModel.bpmn": ["VARIABLE_DOES_NOT_EXIST"],
  "ExternalAgentWorkflow.bpmn": ["VARIABLE_DOES_NOT_EXIST"],
  "StartEventWithOutputs.bpmn": ["VARIABLE_DOES_NOT_EXIST"],
  // Frontend editor mocks (work-in-progress; same issues the FE validator shows):
  "A.2.0.bpmn": ["MISSING_CONDITION_EXPRESSION"],
  "A.2.1.bpmn": ["MISSING_CONDITION_EXPRESSION"],
  "all_sequence_flow_types.bpmn": ["MISSING_CONDITION_EXPRESSION"],
  "all elements.bpmn": ["ERROR_END_EVENT_MISSING_EXCEPTION"],
  "B.1.0.bpmn": ["MISSING_CONDITION_EXPRESSION"],
  "B.2.0.bpmn": ["ERROR_END_EVENT_MISSING_EXCEPTION", "MISSING_CONDITION_EXPRESSION"],
  "C.2.0.bpmn": ["ERROR_END_EVENT_MISSING_EXCEPTION", "MISSING_CONDITION_EXPRESSION"],
  "C.3.0.bpmn": ["MISSING_CONDITION_EXPRESSION"],
  "C.4.0.bpmn": ["MISSING_CONDITION_EXPRESSION"],
  "C.5.0.bpmn": ["MISSING_CONDITION_EXPRESSION"],
  "C.6.0.bpmn": ["INVALID_EVENT_DEFINITION_IN_EVENT_SUBPROCESS"], // compensate-def start in event subprocess
  "C.7.0.bpmn": ["MISSING_CONDITION_EXPRESSION"],
  "demo.bpmn": ["MISSING_CONDITION_EXPRESSION"],
  "Golden_Scenario.initial.bpmn": ["MISSING_CONDITION_EXPRESSION"],
  "subprocess-example-001-collapsed.bpmn": ["SUPERFLUOUS_GATEWAY"],
  "subprocess-example-001-expanded.bpmn": ["SUPERFLUOUS_GATEWAY"],
  "subprocess-example-003-collapsed_deeply-nested.bpmn": ["SUPERFLUOUS_GATEWAY"],
};

function listBpmn(dir) {
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((n) => n.endsWith(".bpmn"))
    .map((n) => ({ name: n, path: join(dir, n) }));
}

const arrEq = (a, b) => a.length === b.length && a.every((x, i) => x === b[i]);

export default async function runIntegration({ verbose = false } = {}) {
  const results = { passed: 0, failed: 0, failures: [], ranFiles: 0, knownGood: 0, expected: 0 };

  const knownGood = listBpmn(join(__dirname, "fixtures", "known-good"));
  const expected = listBpmn(join(__dirname, "fixtures", "expected-findings"));

  if (knownGood.length === 0 && expected.length === 0) {
    console.log("  (integration: no bundled fixtures found — skipped)");
    return results;
  }

  for (const { name, path } of knownGood) {
    results.ranFiles++;
    results.knownGood++;
    let codes;
    try {
      codes = await errorCodesFor(readFileSync(path, "utf8"));
    } catch (e) {
      results.failed++;
      results.failures.push(`[integration] known-good ${name} threw: ${String(e.message).split("\n")[0]}`);
      continue;
    }
    if (codes.length === 0) results.passed++;
    else {
      results.failed++;
      results.failures.push(`[integration] KNOWN-GOOD ${name} produced ERROR findings [${codes.join(",")}] (drift or new genuine issue)`);
    }
    if (verbose && codes.length) console.log(`  FAIL (known-good) ${name} -> [${codes.join(",")}]`);
  }

  for (const { name, path } of expected) {
    results.ranFiles++;
    results.expected++;
    const want = EXPECTED_ERROR_CODES[name];
    if (!want) {
      results.failed++;
      results.failures.push(`[integration] expected-findings ${name} has no EXPECTED_ERROR_CODES entry`);
      continue;
    }
    let codes;
    try {
      codes = await errorCodesFor(readFileSync(path, "utf8"));
    } catch (e) {
      results.failed++;
      results.failures.push(`[integration] expected ${name} threw: ${String(e.message).split("\n")[0]}`);
      continue;
    }
    const wantSorted = [...want].sort();
    if (arrEq(wantSorted, codes)) results.passed++;
    else {
      results.failed++;
      results.failures.push(`[integration] ${name}: expected ERROR [${wantSorted.join(",")}], got [${codes.join(",")}]`);
    }
    if (verbose) console.log(`  ${arrEq(wantSorted, codes) ? "ok " : "FAIL"} (expected) ${name} -> [${codes.join(",")}]`);
  }

  return results;
}
