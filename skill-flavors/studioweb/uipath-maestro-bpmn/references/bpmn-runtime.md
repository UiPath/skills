<!--skill-flavor:sdk-upgrade:start-->
  Needs `@uipath/maestro-builder-sdk` 6.73.0 or later. Studio Web ships its own SDK: when it refuses `{ name, folder }` or the key-less `prepare`, tell the user that this Studio Web build cannot author a folder entity yet.
<!--skill-flavor:sdk-upgrade:end-->

<!--skill-flavor:folder-entity-resources:start-->
  Run `uip maestro bpmn refresh .` after the merge: it turns the two bindings into the entity's row in `bindings_v2.json`. Do not run `uip solution resources refresh`: it fails in Studio Web. Check with `uip solution resources list --source local --output json` that the solution declares the entity; when it does not, tell the user.
<!--skill-flavor:folder-entity-resources:end-->

<!--skill-flavor:sdk-v2-connector:start-->
  Needs `@uipath/maestro-builder-sdk` 6.84.0 or later. Studio Web ships its own SDK: when it writes a new `.connector()` task with one `target="path"` / `target="query"` row per parameter and an `operation` context row, the task is V1 and still runs. Tell the user that this Studio Web build writes V1 connector tasks; do not hand-convert its rows.
<!--skill-flavor:sdk-v2-connector:end-->

<!--skill-flavor:sdk-inline-spec:start-->
  Needs `@uipath/maestro-builder-sdk` 6.85.7 or later. Studio Web ships its own SDK: when `decompile` refuses the type with `BPMN_TYPE_UNKNOWN`, tell the user that this Studio Web build cannot decompile that type yet.
<!--skill-flavor:sdk-inline-spec:end-->

<!--skill-flavor:sdk-palette-elements:start-->
  Needs `@uipath/maestro-builder-sdk` 6.88.1 or later. Studio Web ships its own SDK: when `decompile` refuses one of these elements with "has no builder equivalent", tell the user that this Studio Web build cannot edit that element yet.
<!--skill-flavor:sdk-palette-elements:end-->

<!--skill-flavor:sdk-script-result:start-->
  Needs `@uipath/maestro-builder-sdk` 6.93.7 or later. Studio Web ships its own SDK, and an older `check` does not report it: read `=result.response` yourself.
<!--skill-flavor:sdk-script-result:end-->

<!--skill-flavor:sdk-script-type:start-->
  Needs `@uipath/maestro-builder-sdk` 6.93.8 or later. Studio Web ships its own SDK, and an older one writes whatever `type` says: never pass `type`.
<!--skill-flavor:sdk-script-type:end-->

<!--skill-flavor:sdk-http-manual:start-->
  Needs `@uipath/maestro-builder-sdk` 6.93.9 or later. Studio Web ships its own SDK: when `compile` writes the old manual form (`mode="manual"` with the request as context rows), the run faults, so tell the user that this Studio Web build cannot write a plain HTTP call yet.
  From 6.93.9, `outputVar` is the body, so read `vars.<id>_response.x`, not `vars.<id>_response.body.x`, which read the old form's whole response.
<!--skill-flavor:sdk-http-manual:end-->

<!--skill-flavor:sdk-check-baseline:start-->
  Needs `@uipath/maestro-builder-sdk` 6.97.0 or later. Studio Web ships its own SDK: when `check` refuses `--baseline` (`needs a @uipath/maestro-builder-sdk release that supports it`, or `unknown option '--baseline'`), this Studio Web build does not have it yet. Run `check --source` without `--baseline` and fix only the errors on elements you changed.
<!--skill-flavor:sdk-check-baseline:end-->
