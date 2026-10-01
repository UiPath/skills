# Registry workflow: process wrappers

## Agent wrapper selection — pick by `ProcessType`, not the label

When a node invokes an agent, choose the wrapper by the resource's
**`ProcessType`**, not its display label. The default
`uip or processes list --folder-path <path> --output json` row has no
`ProcessType`; add `--all-fields` to the same call and read `ProcessType`,
`Key`, and `FolderKey` from that one response — same PascalCase as the
default list; `--all-fields` only adds fields, it does not change casing.

- Coded Python agents publish as `ProcessType: "Function"` — use the
  `Orchestrator.StartJob` process contract, **not** `StartAgentJob`.
- Agent Builder (low-code) publishes as `ProcessType: "Agent"` →
  `Orchestrator.StartAgentJob`.
- External A2A agent addressed by URL / skillId → `A2A.AgentExecution`.
- Integration Service external agent → `Intsvc.*AgentExecution`.

Gotcha: `A2A.AgentExecution` renders as an external A2A node and **disables the
Action dropdown** in Studio Web. Do not use it for a folder-deployed agent — the
canvas treats the task as misconfigured. Use `StartAgentJob`/`StartJob` for
folder-deployed resources.

## API workflow invocation — `ExecuteApiWorkflowAsync` waits, despite the name

There is one registry type for invoking a published API workflow from a
`bpmn:serviceTask`: `Orchestrator.ExecuteApiWorkflowAsync`. Its display label —
`Start and wait for API workflow` — is the accurate behavior: it **waits** for
completion and the result is available to later nodes. There is no separate
fire-and-forget API-workflow wrapper; do not model one. Resolve the invoked
workflow's release key and folder key, plus its request/response schemas,
before the node is runnable — the served template is broken as-is; see the
next section for the fix.

## Job-wrapper v1 trap — `releaseKey` templates are unrunnable

`Orchestrator.StartJob`, `Orchestrator.ExecuteApiWorkflowAsync`,
`Orchestrator.BusinessRules`, and `Orchestrator.StartAgenticProcess[Async]` /
`StartCaseMgmtProcess[Async]` all serve the same **v1** `xmlTemplate`:
`<uipath:activity version="v1">` with a hidden, unbound `releaseKey` /
`folderId` / `folderPath` / `name` context (`binding: false` on every field
except `releaseKey`, which carries `bindingInfo` — `resource: "process"`,
`propertyAttribute: "Key"` — in `validator/bpmn-spec.json`). Pasted with the
template's blank placeholders it passes `validate` and packs clean, then
faults at runtime because nothing ever resolves `releaseKey`
(`ExecuteApiWorkflowAsync`: `170009 Could not get value for key:ReleaseKey
from context in input`).

**The fix is not to drop `releaseKey` — it is to resolve it, and to correct
the template's second bug.** Verified end-to-end for
`Orchestrator.ExecuteApiWorkflowAsync` against a live deployed API workflow:

1. **Bind `releaseKey`** via the resource-binding mechanism this field's
   `bindingInfo` already documents (see [§4
   Bindings](registry-workflow-bindings.md#4-bindings--from-bindinginfo-never-invented)): a
   process-kind `<uipath:binding resource="process" propertyAttribute="Key"
   default="<resolved-key>" />`, referenced from the context as
   `=bindings.<id>`. Resolve `<resolved-key>` from `uip or processes list
   --folder-path <path> --output json` → the deployed resource's
   `Key` — never leave the template's `{releaseKey}` placeholder unresolved.
2. **The template's `folderId` context field is misnamed — the runtime reads
   `folderKey`, not `folderId` or `folderPath`.** Populating `releaseKey`
   alone still faults with `Could not get value for key:FolderKey from
   context in input`. Add a context field literally named `folderKey` holding
   the target folder's `FolderKey` GUID (the same `or processes list`
   response carries it as `FolderKey`) — a plain literal value, not a binding.
   Re-read it after every deploy: `deploy run` creates a new folder.
3. With both fields correct — `releaseKey` bound to the resource's real `Key`,
   `folderKey` literal to the folder's real `FolderKey` — the node runs to
   completion. For `Orchestrator.ExecuteApiWorkflowAsync`, drop the
   template's own `folderId`/`folderPath`/`name` context fields.

For the other types in the list, apply step 1 only. Apply step 2 after a
live run faults with `key:FolderKey`; without a run, report the node
unverified.

When the caller asks for API workflow invocation/status/result fields, map those
fields as `uipath:output` rows on the API workflow `bpmn:serviceTask` itself
using the discovered output names/types and `source` expressions, for example
`source="=invocation"`, `source="=status"`, and `source="=result"` (or the exact
schema fields returned by discovery). For a `=result.<key>` source, use the key
a debug run showed when one ran (SKILL.md rule 17 step 5); otherwise use the
schema field name and report the mapping as unverified. Do not add a downstream script task solely
to split the API workflow service-task result into variables; that hides the
requested service-task output contract from the model.
