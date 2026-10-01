# Registry workflow

Every `uipath:*` payload in a Maestro `.bpmn` comes from the registry — never
from prose, never hand-written. This file is the loop for turning user intent
into registry-backed XML.

Read the one file covering your step, not all of them:

- [registry-workflow-discover.md](registry-workflow-discover.md) — §1 sync and discover, §2 `registry get` fields, the 29 OOTB types, registry-evidence-only tasks
- [registry-workflow-connector-object.md](registry-workflow-connector-object.md) — §3 connector (`Intsvc.*`) enrichment: connection, then picking the object
- [registry-workflow-connector-inputs.md](registry-workflow-connector-inputs.md) — §3 connector inputs: the `target="body"` shape, `RequestFields`, required `Parameters`, `Reference` values
- [registry-workflow-bindings.md](registry-workflow-bindings.md) — §4 bindings from `bindingInfo`, Integration Service triggers, connectionless vs connector HTTP
- [registry-workflow-process-wrappers.md](registry-workflow-process-wrappers.md) — agent wrapper by `ProcessType`, API workflow invocation, the job-wrapper v1 `releaseKey` trap

## 5. Assemble

1. Build the document scaffold and process (see
   [structural-bpmn.md](structural-bpmn.md)).
2. Declare the process's variables (`<uipath:variables>`, each with an
   `elementId`) and the `<uipath:bindings>` block.
3. For each node, paste its `registry get` `xmlTemplate`, fill placeholders, and
   wire `{incomingEdge}`/`{outgoingEdge}` to your sequence flows.
4. Author the structural BPMN the registry does not emit: sequence flows,
   gateway conditions/defaults, event definitions, boundary events,
   subprocess/call-activity containers, multi-instance markers.
5. Generate the `bpmndi:BPMNDiagram`, after the final source edit:
   `uip maestro bpmn format <file.bpmn>`
6. Validate (see [structural-bpmn-validation.md#validation](structural-bpmn-validation.md#validation)).
   Re-run step 5 after any later source edit — `validate` errors on a node with
   no shape, so a stale diagram fails it.
