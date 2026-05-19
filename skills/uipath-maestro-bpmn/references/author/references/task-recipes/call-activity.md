# Call Activity Recipe

The current supported implementation wrapper for confirmed process calls
exposed through Orchestrator process-orchestration resource types is
`bpmn:callActivity`.

Supported shells:

- `Orchestrator.StartAgenticProcess`
- `Orchestrator.StartAgenticProcessAsync`
- `Orchestrator.StartCaseMgmtProcess`
- `Orchestrator.StartCaseMgmtProcessAsync`

The model may draft:

- Call activity wrapper, mappings, boundary events, and BPMN DI.
- Placeholder-safe called-resource intent when a documented contract exists.
- Synchronous versus asynchronous routing as explicit process behavior.

CLI or operator must resolve:

- Called process identity, package/resource binding, and generated package metadata.
- Dynamic input/output schemas.
- Case-management details unless a dedicated case-management contract is available.

Use subprocesses for inline local process structure. Use call activities when execution leaves the local BPMN scope.
