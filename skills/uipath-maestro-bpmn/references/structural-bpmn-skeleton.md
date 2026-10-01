# Structural BPMN: document skeleton

## The document scaffold (REGISTRY GAP)

The registry emits no `<bpmn:definitions>` / `<bpmn:process>` root and no
namespace declarations. Author this shell yourself. The canvas import detector
(`exporter.ts`) requires: a root `<…:definitions>` carrying a BPMN-spec
namespace, at least one `<bpmn:process>`, and (to render) a
`<bpmndi:BPMNDiagram>`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:uipath="http://uipath.org/schema/bpmn"
    id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn"
    exporter="UiPath Maestro (https://uipath.com)">
  <bpmn:process id="Process_1">
    <!-- variables, flow nodes, sequence flows -->
  </bpmn:process>
  <bpmndi:BPMNDiagram id="Diagram_1">
    <bpmndi:BPMNPlane id="Plane_1" bpmnElement="Process_1">
      <!-- one BPMNShape per node, one BPMNEdge per flow -->
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
```

The `uipath:` namespace URI is exactly `http://uipath.org/schema/bpmn`. All
`uipath:*` tags inside `extensionElements` are lower-camelCase
(`uipath:activity`, `uipath:variables`, `uipath:loopCharacteristics`, …).

Every `uipath:activity` / `uipath:event` / `uipath:mapping` carries its node
type as a **child** element — `<uipath:type value="<Type>" version="v1" />` —
never as a `type=` attribute on the wrapper. This holds both for templated nodes
and for any shell you author or preserve by hand.

XML comments must not contain `--` (double-hyphen): it is invalid XML and the
file will fail to parse. Never paste CLI commands or flags
(`--output`, `--connection-id`) into `<!-- … -->`. Keep comments minimal.

## A complete minimal file (author from this, not from examples)

This is a minimal CLI-compatible authoring scaffold with a runnable entry-point
contract: one public input, mutable process variables, one registry-derived
`BPMN.Variables` task, one public output, and complete diagram interchange.
Preserve the initializer's `isExecutable` shape — omitted, or `"false"` if
already present. Never force `"true"`. `init` and `format` write
`exporterVersion`; leave it to them rather than pinning a release into hand-
authored source. Author structural nodes from this skeleton and replace the
middle task with retrieved templates for the nodes the process needs. **Do not
reverse-engineer the pattern from full example BPMN files** — it is the main
reason authoring runs out of time.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    xmlns:uipath="http://uipath.org/schema/bpmn"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn"
    exporter="UiPath Maestro (https://uipath.com)">
  <bpmn:process id="Process_1">
    <bpmn:extensionElements>
      <uipath:variables version="v1">
        <uipath:input id="input_Var_Amount" name="Amount" type="number" elementId="Start_1" />
        <uipath:inputOutput id="Var_Amount" name="Amount" type="double" elementId="Process_1" />
        <uipath:output id="output_Var_Echo" name="Echo" type="number" elementId="End_1" />
        <uipath:inputOutput id="Var_Echo" name="Echo" type="double" elementId="Process_1" />
      </uipath:variables>
      <uipath:bindings version="v1" />
    </bpmn:extensionElements>
    <bpmn:startEvent id="Start_1" name="Start">
      <bpmn:extensionElements>
        <uipath:entryPointId value="00000000-0000-4000-8000-000000000001" />
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:output name="Amount" type="double" var="Var_Amount" source="=vars.input_Var_Amount" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:task id="Task_Copy" name="Copy amount">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:output name="Echo" type="double" var="Var_Echo" source="=vars.Var_Amount" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:task>
    <bpmn:endEvent id="End_1" name="Complete">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:output name="Echo" type="double" var="output_Var_Echo" source="=vars.Var_Echo" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_2</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="Task_Copy" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Copy" targetRef="End_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="Diagram_1">
    <bpmndi:BPMNPlane id="Plane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="S_Start" bpmnElement="Start_1"><dc:Bounds x="160" y="100" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_Task" bpmnElement="Task_Copy"><dc:Bounds x="250" y="78" width="100" height="80" /></bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_End" bpmnElement="End_1"><dc:Bounds x="430" y="100" width="36" height="36" /></bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="E_1" bpmnElement="Flow_1"><di:waypoint x="196" y="118" /><di:waypoint x="250" y="118" /></bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E_2" bpmnElement="Flow_2"><di:waypoint x="350" y="118" /><di:waypoint x="430" y="118" /></bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
```
