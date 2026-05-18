# Multi-Instance Implementation

This document defines the implementation boundary for multi-instance activities.

## Model-owned implementation

The model may edit:

- `bpmn:multiInstanceLoopCharacteristics`.
- Sequential or parallel marker attributes.
- `uipath:loopCharacteristics` extension metadata.
- Input collection, item variable, and output mappings.
- Boundary error paths and completion-condition expressions.

## Implementation rules

- Declare collection and item variables before referencing them.
- Use sequential execution when item order or resource limits matter.
- Keep per-item outputs distinct from aggregate outputs.
- Do not hide service-call retries inside loop metadata; model retry or boundary behavior explicitly.
- Choose the item binding pattern from the BPMN shape:
  - For a task with its own multi-instance marker, pass `iterator` into the task mapping and read the current item from `iterator.item`.
  - For a multi-instance subprocess, bind the subprocess loop element as `inputElement="iterator[0]"` and pass the current item to body activities with `=iterator[0].item`.
- Do not assume a bare item alias such as `=currentItem` is in scope inside a marker subprocess body unless the file already uses that alias successfully or a current runtime fixture confirms it.

## Generic marker subprocess pattern

Use this pattern when a subprocess body runs once per item and inner activities need the current item:

```xml
<bpmn:multiInstanceLoopCharacteristics id="Loop_ProcessItems" isSequential="true">
  <bpmn:extensionElements>
    <uipath:loopCharacteristics inputCollection="=vars.Var_Items" inputElement="iterator[0]" version="v1" />
  </bpmn:extensionElements>
</bpmn:multiInstanceLoopCharacteristics>

<!-- Inside the subprocess body -->
<uipath:input name="args" type="json" target="bodyField"><![CDATA[
{"item":"=iterator[0].item","vars":"=vars"}
]]></uipath:input>
```

## Validation expectations

- Input collection exists and is iterable.
- Item variable is scoped and referenced consistently.
- Completion conditions use readable variables and no assignments.
- Output aggregation target exists.
- Parallel execution does not conflict with known resource constraints.
