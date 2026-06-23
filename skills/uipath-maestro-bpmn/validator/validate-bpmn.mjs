#!/usr/bin/env node
// Offline semantic validator for UiPath Maestro BPMN XML.
//
// Pipeline:
//   1. Parse the BPMN with bpmn-moddle using the UiPath extension descriptor
//      (same getModdle() + fromXML() pattern as PO.Frontend).
//   2. Reconstruct the PO.Frontend Node[]/Edge[]/CanvasState model (model.mjs).
//   3. Run ALL 19 PO.Frontend validation rules (rules.mjs) per diagram, plus a
//      whole-model variable-existence check.
//   4. (Optional) Run the Maestro-original connection-liveness ping via uip CLI.
//
// Prints `VALID` and exits 0 when there are no ERROR-severity findings.
// Otherwise lists every finding (rule code + message) and exits non-zero.
// WARNING-severity findings are printed but do not gate.
//
// Usage: node validate-bpmn.mjs <bpmn-file> [resources]
//   resources: comma-separated release names, or a numeric folder ID, for the
//              optional solution-resource liveness ping (requires uip CLI auth).
import BpmnModdle from "bpmn-moddle";
import descriptor from "./uipath-moddle.v1.json" with { type: "json" };
import { readFileSync, existsSync } from "fs";
import { execFileSync } from "child_process";
import { buildModel, collectKnownVariableIds, allNodes, allEdges } from "./model.mjs";
import { validateDiagram, validateVariableExistence, validateVariableNotSet, SEVERITY } from "./rules.mjs";

// --- uip CLI resolution (cached) — used only for the liveness-ping extra. ---
let _uipBin;
function resolveUipBin() {
  if (_uipBin !== undefined) return _uipBin;
  const home = process.env.HOME || process.env.USERPROFILE || "";
  const candidates = ["uip", `${home}/.bun/bin/uip`, `${home}/.local/bin/uip`, "/usr/local/bin/uip"];
  for (const p of candidates) {
    try {
      if ((p.startsWith("/") || p.startsWith(home)) && !existsSync(p)) continue;
      execFileSync(p, ["--version"], { encoding: "utf8", timeout: 5000, stdio: "pipe" });
      _uipBin = p;
      return p;
    } catch {
      /* keep trying */
    }
  }
  _uipBin = null;
  return null;
}

function pingConnections(resourceArg) {
  // Maestro-original extra: liveness-check bound IS connections. Best-effort;
  // a missing/unauthenticated CLI is reported as a NOTE, never a hard failure.
  const bin = resolveUipBin();
  if (!bin) return { note: "uip CLI not found; skipped connection liveness ping." };
  try {
    const args = ["is", "connections", "ping", "--output", "json"];
    if (/^\d+$/.test(resourceArg)) args.push("--folder", resourceArg);
    const out = execFileSync(bin, args, { encoding: "utf8", timeout: 30000, stdio: "pipe" });
    return { ok: true, raw: out.trim() };
  } catch (e) {
    return { note: `connection liveness ping unavailable: ${String(e.message || e).split("\n")[0]}` };
  }
}

const file = process.argv[2];
const resourceArg = process.argv[3];
if (!file) {
  console.error("Usage: node validate-bpmn.mjs <bpmn-file> [resources]");
  process.exit(1);
}

const xml = readFileSync(file, "utf8");
const moddle = new BpmnModdle({ uipath: descriptor });

let definitions;
try {
  const result = await moddle.fromXML(xml);
  definitions = result.rootElement;
  if (result.warnings?.length) {
    for (const w of result.warnings) console.error(`PARSE WARNING: ${w.message ?? w}`);
  }
} catch (e) {
  console.error(`SCHEMA ERROR: failed to parse BPMN XML: ${e.message ?? e}`);
  process.exit(2);
}

// Build the model and run all rules.
const canvasState = buildModel(definitions);
const knownIds = collectKnownVariableIds(canvasState);

const findings = [];
for (const diagram of Object.values(canvasState.diagramsById)) {
  // Skip the trivial root-only "single blank start, no edges" diagram, mirroring
  // ValidateBpmnFlowUtils.validateBpmnFlow.
  const realNodes = diagram.nodes.filter((n) => n.type !== "bpmn:Participant");
  if (
    diagram.diagramId === canvasState.rootDiagramId &&
    realNodes.length === 1 &&
    realNodes[0].type === "bpmn:StartEvent" &&
    diagram.edges.length === 0
  ) {
    continue;
  }
  findings.push(...validateDiagram(diagram, canvasState, { enableMissingRootVariableValidation: true }));
}
findings.push(...validateVariableExistence(allNodes(canvasState), allEdges(canvasState), knownIds));
findings.push(...validateVariableNotSet(allNodes(canvasState), allEdges(canvasState), knownIds, canvasState));

// Optional connection liveness ping (Maestro-original extra).
if (resourceArg) {
  const ping = pingConnections(resourceArg);
  if (ping.note) console.error(`NOTE: ${ping.note}`);
  else if (ping.ok) console.error(`connection liveness ping ok`);
}

const errors = findings.filter((f) => f.severity === SEVERITY.ERROR);
const warnings = findings.filter((f) => f.severity === SEVERITY.WARNING);

const fmt = (f) => `  [${f.severity}] ${f.code}: ${f.message}${f.elementId ? ` (element: ${f.elementId})` : ""}`;

if (warnings.length) {
  console.error("WARNINGS:");
  for (const w of warnings) console.error(fmt(w));
}

if (errors.length === 0) {
  console.log("VALID");
  process.exit(0);
}

console.error("ERRORS:");
for (const e of errors) console.error(fmt(e));
console.error(`\n${errors.length} blocking error(s), ${warnings.length} warning(s).`);
process.exit(1);
