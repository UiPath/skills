# http-request task — Implementation

> **Phase split.** Written in Phase 2 by `uip maestro case sdd convert`. Phase 3 binds connector mode's connection into the solution. See [`../../../phased-execution.md`](../../../phased-execution.md).

## Convert writes this task

`sdd convert` emits every `http-request` task in the shape the Case Designer saves: `type: "http-request"`, `data.serviceType: "Intsvc.UnifiedHttpRequest"`, a `context` naming the generic HTTP connector's activity (`uipath-uipath-http`, `objectName: "http-request"`, the Designer's `metadata`), and the request in the `body` input: `authentication`, `method`, `headers`, `query`, and `url` plus `requestBodyType: "raw"` for a body in manual mode, or `path` only and no `requestBodyType` in connector mode.

1. **Never hand-write the `context` or `metadata`.** They are a copy of the Designer's activity configuration; a hand-typed copy drifts from it. Fix the SDD line and re-run convert instead.
2. **When convert cannot write the task, write a [placeholder](../../../placeholder-tasks.md).** That is a CLI whose `uip maestro case task-types list --output json` does not list `http-request` under `Authorable`, and every brownfield add, which runs no convert. Tell the user to configure the request in Studio Web, or to upgrade the CLI and rebuild; never improvise the shape.
3. **Work the `Data.Unresolved[]` entries for the task** — a missing or unsupported method, headers that are not a JSON object, a body that is neither JSON nor an `=` expression, a body on `GET`/`HEAD`/`OPTIONS`/`DELETE`, an Outputs row other than `code`/`headers`/`body`/`Error`, a connector with no connection, and connector mode's FolderKey — by fixing the SDD and re-running convert. Report any left to the user in `build-issues.md`.

## Connector mode

`body.authentication` is `"connector"` and `body.targetConnector` names the connector. The task carries a `Connection` binding for `ConnectionId` and one for `folderKey`, mirrored at the root. Manual mode has `authentication: "manual"`, no task binding, and one root `Connection` binding with `resourceKey: "ImplicitConnection"`; `bindings sync` writes no sidecar resource for it, as the Designer's save does not.

The build's normal steps bind it: the Step 9 `uip maestro case bindings sync` files the connection under its `targetConnector`, where the Designer files it, and the `uip solution resources refresh` before every upload or debug (SKILL.md Rule 15) reads that entry to add the connection to the solution. Never skip either for a case with a connector-mode task.


## Post-Write Verification

- `type: "http-request"`, `data.serviceType: "Intsvc.UnifiedHttpRequest"`.
- `uip maestro case validate` reports no `CASE_MGMT_CONNECTOR_ACTIVITY_UNRESOLVED` or `CASE_MGMT_CONNECTOR_INPUTS_EMPTY` for the task, and `--strict` no `STRICT_CONNECTOR_CONTEXT_INCOMPLETE`. If one fires, regenerate the task with `uip maestro case sdd convert`; never run `case spec` or `case splice` for it, since neither writes this type.
- `data.outputs` is `code`, `headers`, `body` and `Error`, with `var` numbered apart from other tasks' outputs and from the case's own variable names (`code`, `code2`, …), so a case variable named `body` is never overwritten. An arrow row naming that variable (`Body -> body`) binds to it instead.
- No header in the `body` input carries a credential ([planning.md § Rules](planning.md#rules), first item).
- Connector mode: two `Connection` bindings on the task and at the root, and the connection listed in the solution after `resources refresh`.

<!-- END: impl-json.md -->
