<!-- when: adding a HITL node to a Maestro BPMN (.bpmn) process -->
# HITL on Maestro BPMN — Node Reference

QuickForm and coded-action-app HITL nodes are both supported on Maestro BPMN processes. `uipath.human-in-the-loop.quick-form` and `uipath.human-in-the-loop.coded-action-app` are registered as **registry shortcut names** in the BPMN validator ([bpmn-spec.json](../uipath-maestro-bpmn/validator/bpmn-spec.json)) — these are palette/discovery identifiers, not literal XML to write. There is no dedicated CLI subcommand for Maestro (unlike Flow's `uip maestro flow hitl add`) — write the node directly into the `.bpmn` XML.

Design the schema per Step 4b — never block waiting on the user, per Critical Rule 1 — then validate frequently (`uip maestro bpmn validate <file>.bpmn --output json`) while wiring the node so any shape mistakes surface immediately rather than at deploy time. In Maestro, field names in `outputs`/`inOuts` must exactly match declared process variable names and types.

**Confirmed node shape (verified by direct reproduction against a real Studio Web BPMN process with a working, editable QuickForm task):**

```xml
<bpmn:task id="Activity_InvoiceApproval" name="Invoice Approval">
  <bpmn:extensionElements>
    <uipath:activity version="v1">
      <uipath:type value="Actions.HITL" version="v2" />
      <uipath:context>
        <uipath:input name="hitlType" type="string" value="quick" />
        <uipath:input name="taskTitle" type="string" value="Please review this invoice and approve or reject" />
        <uipath:input name="labels" type="string" />
        <uipath:input name="priority" type="string" value="Medium" />
        <uipath:input name="actionCatalogName" type="string" />
        <uipath:input name="enableActionableNotifications" type="boolean" value="false" />
        <uipath:input name="assignmentCriteria" type="string" />
        <uipath:input name="recipient" type="json" />
        <uipath:input name="_schemaFileId" type="string" value="<see file-id callout below>" />
        <uipath:input name="hitlSchemaId" type="string" value="<matches schemaId in the .hitl.json sidecar>" />
        <uipath:inputSchema type="jsonSchema"><![CDATA[{"$schema":"http://json-schema.org/draft-07/schema#","type":"object","properties":{"invoiceid":{"type":"string","title":"Invoice ID"},"amount":{"type":"number","title":"Amount"}},"required":[]}]]></uipath:inputSchema>
      </uipath:context>
      <uipath:input name="HitlTaskArguments" type="json" target="bodyField"><![CDATA[{"invoiceid":"INV-1001","amount":500}]]></uipath:input>
      <uipath:output name="Action" type="string" source="=Action" var="invoiceDecision" options="[{&#34;value&#34;:&#34;Approve&#34;,&#34;label&#34;:&#34;Approve&#34;},{&#34;value&#34;:&#34;Reject&#34;,&#34;label&#34;:&#34;Reject&#34;}]" />
    </uipath:activity>
  </bpmn:extensionElements>
  <bpmn:incoming>edge_into_task</bpmn:incoming>
  <bpmn:outgoing>edge_out_of_task</bpmn:outgoing>
</bpmn:task>
```

Notes on what's easy to get wrong:
- **Element is `bpmn:task`, not `bpmn:UserTask`.** `bpmn-spec.json`'s generic `Actions.HITL` XML template uses `bpmn:UserTask` and `version="v1"` — that template is for the app-based/coded-action-app path (its `context` fields are `appId`, `appVersion`, `actions`, `key`, `taskTitle`). A real QuickForm task exported from Studio Web is a plain `bpmn:task` with `uipath:type value="Actions.HITL" version="v2"`. Use the shape above for QuickForm; the spec's template for app-based.
- **`<uipath:inputSchema>` (last child of `<uipath:context>`) and `<uipath:input name="HitlTaskArguments">` (sibling of `<uipath:context>`, not inside it) are both required.** Without them the "Edit Schema" canvas in Studio Web doesn't open at all — confirmed by direct reproduction. This mirrors the Case surface's `data.inputSchema`/`data.inputs[]` requirement — see [hitl-casetask-action.md § Step 3](hitl-casetask-action.md) for the parallel Case shape and full field-by-field rationale.
- **The `Action` output requires a matching process-level variable declaration** — add `<uipath:inputOutput id="<varId>" name="Action" type="string" elementId="<taskId>" />` inside the process's top-level `<uipath:variables version="v1">` block.
- **A separate `<TaskLabel>.hitl.json` sidecar file is required**, same shape as the Case surface's (`title`, `fields[]` with `direction`/optional `colSpan`/`binding` or `variable`, `outcomes[]` with **no** `action` key, `schemaId`) — see [hitl-casetask-action.md § Step 2](hitl-casetask-action.md) for the exact shape; it's identical across both surfaces.
- **`_schemaFileId` cannot be authored blind — it is a server-assigned foreign key, not a UUID you invent.** A placeholder value makes "Edit Schema" fail silently (a `404` on Studio Web's internal `FileOperations/File/Rename` call, confirmed by direct reproduction). There is no `uip` CLI command that resolves this today. **Never block on this.** Write a fresh placeholder UUID v4, finish the rest of the node, validate, and move on — do not attempt the live reconciliation yourself and do not stop to ask about it. State plainly in the final report: "This task's schema was written with a placeholder `_schemaFileId`, so Studio Web's 'Edit Schema' canvas won't open for it yet. Making it editable requires resolving the real file ID Studio Web assigns to the `.hitl.json` after upload (`GET /api/Project/{projectId}/FileOperations/Structure`) and pushing it back with a targeted single-file update (`PUT /api/Project/{projectId}/FileOperations/File/{fileId}`) — not another whole-project `uip solution upload`, which re-pushes every file and mints a fresh random file ID for each one, undoing the fix. Ask me to do this reconciliation if you want the schema editable in Studio Web." This is a real product/tooling gap the user can act on later, not something to resolve mid-task.
- **Diagram-interchange edges are required for the connector lines to render, even though the logical `bpmn:sequenceFlow`s already exist.** Every `bpmn:sequenceFlow` needs a matching `bpmndi:BPMNEdge` (with two `di:waypoint` points, aligned to the source/target shapes' connecting edges) in the `bpmndi:BPMNPlane` — omitting it leaves the nodes logically connected but visually disconnected in the canvas. Confirmed by direct reproduction.
