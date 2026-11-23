import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const CHECKER = fileURLToPath(new URL("../../skills/uipath-planner/scripts/check-sdd.mjs", import.meta.url));

function run(text, ...flags) {
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "check-sdd-")), "sdd.md");
  fs.writeFileSync(file, text);
  const result = spawnSync(process.execPath, [CHECKER, file, ...flags], { encoding: "utf8" });
  return { status: result.status, out: result.stdout + result.stderr, written: fs.readFileSync(file, "utf8") };
}

/** A Maestro BPMN SDD in the PDD-aligned layout: steps in §2, failures in §7, the wiring in §11. */
function bpmnSdd({ flowTarget = "`check`", failureThen = "`alert`" } = {}) {
  return `# Solution Design Document — Demo

## Planner Handoff

| Field | Value |
|---|---|
| **Status** | draft |
| **Template validation** | passed |

<!-- planner-sdd-body:v1 -->
## 2. Solution Flow

### Steps

| # | Node Key | Step Kind | Description | Inputs | Outputs | Integrated Component | Notes |
|---|---|---|---|---|---|---|---|
| 1 | \`start\` | Start | Start | — | — | — | — |
| 2 | \`read\` | Call | Read the records | — | records | connector | — |
| 3 | \`check\` | Compute | Check the records | records | ok | — | — |
| 4 | \`alert\` | Call | Tell the owner | — | — | connector | — |
| 5 | \`done\` | End | End | — | — | — | — |

## 7. Exceptions and Error Handling

| Failing Node | Trigger | Attempts | Caught By | Then |
|---|---|---|---|---|
| \`read\` | source unavailable | — | \`readFailed\` | ${failureThen} |

## 11. Build Specification

### Gateways

| Gateway Key | Type | Incoming | Outgoing | Default Flow | Purpose |
|---|---|---|---|---|---|

### Sequence Flows

| Flow Key | Source | Target | Condition | Notes |
|---|---|---|---|---|
| \`f1\` | \`start\` | \`read\` | — | — |
| \`f2\` | \`read\` | ${flowTarget} | — | — |
| \`f3\` | \`check\` | \`done\` | — | — |
| \`f4\` | \`alert\` | \`done\` | — | — |

### Events

| Event Key | Event Kind | Definition | Attached To (boundary) | Interrupting? | Timer / Message / Error detail |
|---|---|---|---|---|---|
| \`readFailed\` | boundary | error | \`read\` | yes | source unavailable |
`;
}

test("a consistent BPMN SDD in the PDD-aligned layout passes and --ready sets it ready", () => {
  const { status, out, written } = run(bpmnSdd(), "--ready");
  assert.equal(status, 0, out);
  assert.match(out, /OK: the SDD's tables agree/);
  assert.match(written, /\| \*\*Status\*\* \| ready \|/);
});

test("a sequence flow to a node no table declares fails and keeps the SDD at draft", () => {
  const { status, out, written } = run(bpmnSdd({ flowTarget: "`missing`" }), "--ready");
  assert.equal(status, 1);
  assert.match(out, /FAIL: \[unknown-node\] a flow names `missing`/);
  assert.match(written, /\| \*\*Status\*\* \| draft \|/);
});

test("a failure row under Exceptions and Error Handling is checked against the steps", () => {
  const { status, out } = run(bpmnSdd({ failureThen: "`nowhere`" }));
  assert.equal(status, 1);
  assert.match(out, /FAIL: \[error-catch\] after a failure of `read` the run continues at `nowhere`/);
});

test("a BPMN SDD in the earlier layout is still checked", () => {
  const earlier = bpmnSdd({ flowTarget: "`missing`" })
    .replace("## 2. Solution Flow\n\n### Steps", "## 4. Activities Inventory")
    .replace("## 7. Exceptions and Error Handling", "## 10. Error Handling & Retry")
    .replace("## 11. Build Specification\n\n### Gateways", "## 5. Gateways & Sequence Flows\n\n### Gateways")
    .replace("### Events", "## 6. Events");
  const { status, out } = run(earlier);
  assert.equal(status, 1);
  assert.match(out, /FAIL: \[unknown-node\] a flow names `missing`/);
});
