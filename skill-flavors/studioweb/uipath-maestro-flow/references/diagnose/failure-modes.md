<!--skill-flavor:project-creation-recovery-index:start-->
| [`=js:` prefix missing](#js-prefix-missing) | Activity input bound to literal string `"vars.X.output.Y"` | Missing `=js:` prefix on a `$vars` reference. `flow validate` catches this — validate after every edit. |
| [`variables.nodes[]` missing](#variablesnodes-missing--varsxoutput-resolves-to-undefined) | `Cannot read property 'output' of undefined` on a downstream node | Direct-authored `.flow` skipped `variables.nodes[]`; `flow validate` accepts it but the BPMN has no process-level variable declaration for the upstream node. |
| [Misshapen nodes in Studio Web](#misshapen-rectangle-nodes-in-studio-web) | Nodes render at the wrong size for their shape in the designer | `flow format` not run after the last edit |
| [HITL `completed` port unwired](#hitl-completed-port-unwired) | Flow hangs indefinitely after a HITL node | No outgoing edge from the node's `completed` source port |
| [Run reports `Successful`, work not done](#run-reports-completed-but-the-work-never-happened) | Run finishes `Successful` / `Completed`, but the API call / node it depended on failed | `inputs.errorHandlingEnabled: true` on a node with no handler, or an `error` edge routed back into the happy path |
| [Reused reference ID](#reused-reference-id--cross-connection-id-leakage) | Connector node faults silently at runtime | Reference ID copied from a prior flow's connection |
| [Missing `bindings[]` on resource node](#missing-bindings-on-resource-node) | `Folder does not exist or the user does not have access to the folder` | Top-level `bindings[]` entries not added for a `uipath.core.*` resource node |
| [`flow validate` passes, `flow debug` faults](#flow-validate-passes-flow-debug-faults) | Local validation green, cloud run red | Multiple causes — narrower than before (the missing-`=js:` validator + expression-ref linting now catch a large slice statically). See entry for the residual triage path. |
<!--skill-flavor:project-creation-recovery-index:end-->

<!--skill-flavor:js-prefix-validator-note:start-->
`flow validate` flags this as an error (cli-side `expression-prefix-validator`, emitted with a remediation hint pointing at the `=js:`-prefixed form), so the symptom should be caught before `uip flow debug` — validate after every edit.
<!--skill-flavor:js-prefix-validator-note:end-->

<!--skill-flavor:variables-nodes-fix-command:start-->
Run `uip maestro flow format /solution/<ProjectName>/new.flow --output json`. Format regenerates `variables.nodes[]` from `nodes[]` + `definitions[]` (matching `node add` and canvas behavior). If entries are still missing afterwards, add them manually:
<!--skill-flavor:variables-nodes-fix-command:end-->

<!--skill-flavor:misshapen-nodes-body:start-->
The designer renders the saved `/solution/<ProjectName>/new.flow` live: nodes appear at the wrong dimensions for their shape — a square/circle node stretched into an oblong (e.g., 200×80), or an inline agent squashed to a 96×96 square instead of its 288×96 rectangle. Layout looks visually broken even though the flow runs correctly.

### Cause

`uip maestro flow format` was not run after the last edit. Hand-written or stale `layout` data with dimensions that don't match each node's shape remains in the `.flow` file and the designer renders it as-is.

### Fix

Run format after every edit (there is no publish or upload step in between — the designer shows the file as saved):

```bash
uip maestro flow format /solution/<ProjectName>/new.flow --output json
```
<!--skill-flavor:misshapen-nodes-body:end-->

<!--skill-flavor:completed-but-no-work-symptom:start-->
The run ends with status `Successful` (`uip flow debug`) or `Completed` (deployed job) and no incident is raised, yet the flow's real effect is missing — the record was never created, the message never sent, the downstream node ran on empty or stale data. The flow "always looks successful," including on runs where a dependency was demonstrably down. Nothing shows up in `instance incidents` because, as far as the engine is concerned, nothing failed.
<!--skill-flavor:completed-but-no-work-symptom:end-->

<!--skill-flavor:error-handling-audit-script:start-->
Write this script to `/tmp/audit.js` with the file-write tool (no heredoc — multi-line shell input gets collapsed), then run it with `node`:

```js
// /tmp/audit.js
const fs = require("fs");
const d = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const E = d.edges || [];
const N = Object.fromEntries((d.nodes || []).map((n) => [n.id, n]));
const END = new Set(["core.control.end", "core.logic.terminate"]);

const targets = (nid, port, exclude) =>
  E.filter((e) => e.sourceNodeId === nid &&
    (port === undefined || e.sourcePort === port) &&
    (exclude === undefined || e.sourcePort !== exclude)).map((e) => e.targetNodeId);

const terminals = (start, seen = new Set()) => {
  if (seen.has(start)) return new Set();
  seen.add(start);
  if (END.has((N[start] || {}).type)) return new Set([start]);
  const out = new Set();
  for (const t of targets(start)) for (const x of terminals(t, seen)) out.add(x);
  return out;
};
const union = (sets) => new Set(sets.flatMap((s) => [...s]));
const subset = (a, b) => [...a].every((x) => b.has(x));
const sorted = (s) => JSON.stringify([...s].sort());

for (const [nid, n] of Object.entries(N)) {
  if ((n.inputs || {}).errorHandlingEnabled !== true) continue;
  const err = targets(nid, "error"), ok = targets(nid, undefined, "error");
  if (err.length === 0) { console.log(`${nid}: flag set, NO error edge`); continue; }
  const okTerm = union(ok.map((t) => terminals(t)));
  for (const t of err) {
    const term = terminals(t);
    if (ok.includes(t)) console.log(`${nid}: error -> ${t} REJOINS the happy path`);
    else if (term.size > 0 && subset(term, okTerm)) console.log(`${nid}: error -> ${t} shares success terminal(s) ${sorted(term)}`);
    else console.log(`${nid}: error -> ${t} distinct terminal(s) ${sorted(term)} - ok`);
  }
}
```

```bash
node /tmp/audit.js /solution/<ProjectName>/new.flow
```
<!--skill-flavor:error-handling-audit-script:end-->

<!--skill-flavor:project-creation-recovery:start-->
<!--skill-flavor:project-creation-recovery:end-->

<!--skill-flavor:missing-bindings-symptom-intro:start-->
`uip maestro flow validate` passes locally. At `uip flow debug` (or in deployed runs), the resource node faults with:
<!--skill-flavor:missing-bindings-symptom-intro:end-->

<!--skill-flavor:validate-passes-debug-faults-symptom:start-->
Local `uip maestro flow validate` returns `Result: Success`. The same flow fails at `uip flow debug` with a runtime error (`Faulted` on the first output line, cause in `Run logs:`).
<!--skill-flavor:validate-passes-debug-faults-symptom:end-->
