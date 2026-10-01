# Structural BPMN: containers and multi-instance

## Subprocess, call activity, event subprocess (REGISTRY GAP for structure)

- **SubProcess** (`bpmn:subProcess`): a container with its own nested
  `flowElements` (start event, nodes, end event) and its own scoped
  `<uipath:variables>`. Variants: `collapsed`, `expanded`, `eventSubprocess`.
  The shape carries `isExpanded` for the collapsed/expanded distinction.
- **Event subprocess**: a `bpmn:subProcess` with `triggeredByEvent="true"`. It
  must have **exactly one** start event, and that start event **must carry an
  event definition** (with `isInterrupting`) — a blank start event is invalid for
  an event subprocess.
- **Call activity** (`bpmn:callActivity`): invokes a *separate* Maestro
  instance. The registry provides the `uipath:activity` payload for the
  Orchestrator agentic/case-management call-activity types
  (`Orchestrator.StartAgenticProcess[Async]`, `…CaseMgmtProcess[Async]`). A
  plain BPMN `calledElement` round-trips but is not specially authored by the
  canvas layer.
- Each scope (process or sub-process) may have at most one blank (untyped) start
  event (`MULTIPLE_BLANK_START_EVENTS`).

> SubProcess scopes operations *within the same instance*; CallActivity invokes
> a *separate* Maestro instance. Do not conflate them.

## Multi-instance / loop characteristics (REGISTRY GAP — canvas supports it)

The registry spec enumerates **no** multi-instance or loop markers
(`grep` for `multiInstance`/`loopCharacteristics` in `bpmn-spec.json` returns
nothing). This is a genuine registry gap. The Studio Web canvas, however, **does**
serialize them (`elements/nodes.ts`), so author them from the canvas contract:

```xml
<bpmn:multiInstanceLoopCharacteristics isSequential="true">
  <bpmn:completionCondition xsi:type="bpmn:tFormalExpression">=vars.Var_Done</bpmn:completionCondition>
  <bpmn:extensionElements>
    <uipath:loopCharacteristics
        inputCollection="=vars.Var_Items" inputElement="item" />
  </bpmn:extensionElements>
</bpmn:multiInstanceLoopCharacteristics>
```

- `isSequential="true"` = one at a time; `false` = parallel.
- The collection/item binding lives in the `uipath:loopCharacteristics`
  extension (`inputCollection`, `inputElement`), **not** in `loopCardinality`
  (the canvas never reads `loopCardinality`).
- The loop element **must declare `inputElement`** — do not rely on reading a
  bare `iterator`/`iterator.item` downstream without it. For a multi-instance
  **subprocess** body, bind `inputElement="iterator[0]"` on
  `uipath:loopCharacteristics` and pass the current item into body activities
  with `=iterator[0].item`. Do not assume a bare alias such as `=currentItem` is
  in scope inside a marker subprocess body unless the file already uses it.
- Inside the body, read the current item with the `iterator` namespace — see
  [expression-authoring.md](expression-authoring.md).
- `bpmn:standardLoopCharacteristics` is also recognized (no uipath extension).
