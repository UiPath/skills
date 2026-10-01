# Structural BPMN: diagram and validation

## Diagram interchange — `bpmndi` (REGISTRY GAP — always generated)

The registry emits no diagram. Import is **diagram-driven**: the canvas builds
nodes from `BPMNShape`s and edges from `BPMNEdge`s, not by walking
`flowElements`. **A node with no shape is invisible; a flow with no edge is
dropped.** Generate the full `BPMNDiagram` with `uip maestro bpmn format <file.bpmn>`.

- One `<bpmndi:BPMNShape id="S_<nodeId>" bpmnElement="<nodeId>">` per node, with
  `<dc:Bounds x= y= width= height= />`. SubProcess shapes carry `isExpanded`.
- One `<bpmndi:BPMNEdge id="BPMNEdge_<flowId>" bpmnElement="<flowId>">` per
  sequence flow, with `<di:waypoint x= y= />` points.
- Lay nodes out left-to-right with non-overlapping bounds. Typical sizes: tasks
  100×80, events 36×36, gateways 50×50.

Example:

```xml
<bpmndi:BPMNShape id="S_StartEvent_1" bpmnElement="StartEvent_1">
  <dc:Bounds x="160" y="100" width="36" height="36" />
</bpmndi:BPMNShape>
<bpmndi:BPMNEdge id="BPMNEdge_Flow_1" bpmnElement="Flow_1">
  <di:waypoint x="196" y="118" />
  <di:waypoint x="260" y="118" />
</bpmndi:BPMNEdge>
```

## Validation

Validate with the CLI — it runs the full PO.Frontend canvas rule set offline
(the same Node/Edge/CanvasState reconstruction and every canvas rule), plus the
deploy-readiness checks:

```bash
uip maestro bpmn validate <file.bpmn> --output json
```

Exit 0 means the document passes every rule the CLI enforces, which is not
the same as every rule in the contract: `FAKE_JOIN` is registered but never
reported (see [Gateways](structural-bpmn-flow.md#gateways)), so a clean exit is not proof of the
hand-checked invariant in item 5 below. Exit 1 lists the blocking errors,
each with its rule code (gateway/condition, superfluous-gateway,
error end/boundary event, timer-duration/required-field, single-blank-start,
single-conditional-outgoing-flow, variable-reference, method-parentheses,
input-type, event-object, and IS-connector checks). Warnings are reported but do
not block. Triage them by code: on pass they are in `Data.Warnings` (one
string), on failure in `Instructions` with the errors.

- **`VARIABLE_DOES_NOT_EXIST`** — a reference with no matching declaration.
  Always a defect; fix it.
- **`VARIABLE_NOT_SET`** on the node reading a caller-supplied input —
  **expected by construction, not a defect**, whenever that input is correctly
  scoped to the start event (see [Variables](structural-bpmn-variables.md#variables)). Canvas availability
  recognizes only process-scoped variables and upstream nodes'
  `uipath:output` mappings; a start-event input is neither, so any process
  whose node consumes a caller value carries this warning. Scoping the input
  to the process instead silences the warning by emptying the published input
  contract (`entry-points.json`'s `input` becomes `[]`) — nothing can then
  invoke the process with that value, and a `debug --inputs` run still
  succeeds, which is exactly what hides the break. Judge correctness by the
  published contract (`entry-points.json` declares the input and every
  output), not by whether the warning is gone.

If `validate` is unknown or runs only deploy-readiness checks, update
the CLI — see [cli-conventions.md](cli-conventions.md#discovery-commands-read-only-authoring-safe).

Run the well-formed-XML parse before `validate` every time; the validator's
tokenizer does not report an unbound namespace prefix:

```bash
python3 -c "import sys, xml.etree.ElementTree as ET; ET.parse(sys.argv[1])" <file.bpmn>
```

If the CLI is unavailable, also walk the structural checklist below; it mirrors
the same blocking rules:

1. Root is `<…:definitions>` with the BPMN + `uipath` namespaces.
2. Exactly one `<bpmndi:BPMNDiagram>` with a shape per node and an edge per flow.
3. Every `sourceRef`/`targetRef`/`attachedToRef`/`*Ref` resolves to a declared id.
4. Each XOR gateway: non-default flows have conditions; exactly one default.
5. No activity/event has more than one incoming flow. The CLI never reports
   this one (see [Gateways](structural-bpmn-flow.md#gateways)), so check it by hand whether or not
   `validate` is available. One open exception: an end event that converges
   the normal routes returning one shared public result, which
   [Variables](structural-bpmn-variables.md#variables) prescribes. Leave those as prescribed rather than
   rebuilding them behind a gateway.
6. Each event subprocess has exactly one start event, and it carries an event
   definition (with `isInterrupting`).
7. Every `vars.<id>` reference resolves to a declared variable.
8. Each `uipath:*` payload was produced from a `registry get` template, not
   hand-written.
