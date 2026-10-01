# Structural BPMN (what the registry does not emit)

The registry's `xmlTemplate`s give you the `uipath:*` payload for each node
(see [registry-workflow.md](registry-workflow.md)). Author everything holding
those nodes together from this file. Sections marked **REGISTRY GAP** have no
template at all; there the Studio Web canvas serializer is the contract.

Read the one section you need, not the file:

- [The document scaffold](structural-bpmn-skeleton.md#the-document-scaffold-registry-gap) — namespaces, `bpmn:definitions`/`bpmn:process` shell, the `uipath:type` child rule
- [A complete minimal file](structural-bpmn-skeleton.md#a-complete-minimal-file-author-from-this-not-from-examples) — the skeleton to author every new file from
- [Variables](structural-bpmn-variables.md#variables) — declaring them, `elementId`, reserved names, public input/output types, `entryPointId`
- [Script tasks](structural-bpmn-script-tasks.md#script-tasks--jint-authoring-contract) — `bpmn:scriptTask`, the Jint helpers, `args`, `scriptVersion`, return shape
- [Sequence flows](structural-bpmn-flow.md#sequence-flows-conditions-and-gateway-defaults-registry-gap) — `bpmn:sequenceFlow`, `conditionExpression`, gateway `default`
- [Gateways](structural-bpmn-flow.md#gateways) — which gateway type, and the rule each must satisfy
- [Events](structural-bpmn-flow.md#events-and-the-event-definition-matrix) — which event definition each event element may carry; timer, message, error payloads
- [Boundary events](structural-bpmn-flow.md#boundary-events-registry-gap-for-attachedtoref--cancelactivity) — `attachedToRef`, `cancelActivity`
- [Retry and error mapping](structural-bpmn-flow.md#retry-and-error-mapping-registry-gap) — `uipath:retry`, `uipath:errorMapping`
- [Choosing an error-handling construct](structural-bpmn-flow.md#choosing-an-error-handling-construct) — retry vs boundary event vs event subprocess
- [Subprocess, call activity, event subprocess](structural-bpmn-containers.md#subprocess-call-activity-event-subprocess-registry-gap-for-structure)
- [Multi-instance](structural-bpmn-containers.md#multi-instance--loop-characteristics-registry-gap--canvas-supports-it) — `multiInstanceLoopCharacteristics`, `inputCollection`, `inputElement`
- [Do not generate for new authoring](structural-bpmn-round-trip.md#do-not-generate-for-new-authoring-preserve-on-round-trip-only) — preserve-only structures and payloads
- [Diagram interchange](structural-bpmn-validation.md#diagram-interchange--bpmndi-registry-gap--always-generated) — `bpmndi` shapes, edges, waypoints
- [Editing operations](structural-bpmn-round-trip.md#editing-operations) — add, delete, or re-scope nodes on an existing file
- [Validation](structural-bpmn-validation.md#validation) — the XML parse gate, `validate`, and the manual checklist

Not in this file, do not grep for it here — connector (`Intsvc.*`) inputs,
`target="body"` and required `Parameters` are in
[registry-workflow-connector-inputs.md](registry-workflow-connector-inputs.md),
trigger payloads in
[registry-workflow-bindings.md](registry-workflow-bindings.md#integration-service-triggers), and
expression syntax with the `vars.` / `iterator.` / `bindings.` namespaces in
[expression-authoring.md](expression-authoring.md).

BPMN XML element names are case-sensitive. Use the exact lower-camel tag names
the serializer emits: `<bpmn:startEvent>`, `<bpmn:intermediateCatchEvent>`,
`<bpmn:scriptTask>`, `<bpmn:endEvent>`. Never PascalCase
(`<bpmn:IntermediateCatchEvent>`).
