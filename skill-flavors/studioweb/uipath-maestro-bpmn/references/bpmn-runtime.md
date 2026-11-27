<!--skill-flavor:sdk-upgrade:start-->
  Needs `@uipath/maestro-builder-sdk` 6.73.0 or later. Studio Web ships its own SDK: when it refuses `{ name, folder }` or the key-less `prepare`, tell the user that this Studio Web build cannot author a folder entity yet.
<!--skill-flavor:sdk-upgrade:end-->

<!--skill-flavor:folder-entity-resources:start-->
  Run `uip maestro bpmn refresh .` after the merge: it turns the two bindings into the entity's row in `bindings_v2.json`. Do not run `uip solution resources refresh`: it fails in Studio Web. Check with `uip solution resources list --source local --output json` that the solution declares the entity; when it does not, tell the user.
<!--skill-flavor:folder-entity-resources:end-->

<!--skill-flavor:sdk-df-folder-v2:start-->
  Needs `@uipath/maestro-builder-sdk` 6.122.0 or later. Studio Web ships its own SDK: when it writes `create`, `update`, `get` or `query` on a folder entity with a literal folder key as a V1 task (one `target="query"` row per parameter), the task still runs. Tell the user that this Studio Web build writes V1 Data Fabric tasks for folder entities; do not hand-convert its rows. A `delete`, or a folder key written as an `=`-expression, is a V1 task on every SDK: say nothing about it.
<!--skill-flavor:sdk-df-folder-v2:end-->

<!--skill-flavor:sdk-folder-key:start-->
  Studio Web ships its own `uip` and SDK: when `prepare` answers `unknown option '--folder-key'`, or says `--folder-key` needs a builder SDK release that supports it, name the folder by path with `{ name, folder }` instead, which needs no `--folder-key`.
<!--skill-flavor:sdk-folder-key:end-->

<!--skill-flavor:sdk-v2-connector:start-->
  Needs `@uipath/maestro-builder-sdk` 6.84.0 or later. Studio Web ships its own SDK: when it writes a new `.connector()` task with one `target="path"` / `target="query"` row per parameter and an `operation` context row, the task is V1 and still runs. Tell the user that this Studio Web build writes V1 connector tasks; do not hand-convert its rows.
<!--skill-flavor:sdk-v2-connector:end-->

<!--skill-flavor:sdk-inline-spec:start-->
  Needs `@uipath/maestro-builder-sdk` 6.85.7 or later. Studio Web ships its own SDK: when `decompile` refuses the type with `BPMN_TYPE_UNKNOWN`, tell the user that this Studio Web build cannot decompile that type yet.
<!--skill-flavor:sdk-inline-spec:end-->

<!--skill-flavor:sdk-palette-elements:start-->
  Needs `@uipath/maestro-builder-sdk` 6.88.1 or later. Studio Web ships its own SDK: when `decompile` refuses one of these elements with "has no builder equivalent", tell the user that this Studio Web build cannot edit that element yet.
<!--skill-flavor:sdk-palette-elements:end-->

<!--skill-flavor:sdk-no-message:start-->
  Needs `@uipath/maestro-builder-sdk` 6.122.5 or later. Studio Web ships its own SDK: when a decompiled source carries `message: ''` instead of `message: NO_MESSAGE`, this Studio Web build compiles it to one nameless `Message_1` that `validate` rejects; tell the user that this Studio Web build cannot round-trip a message event with no message chosen yet. Do not invent a message name or drop `message` to get past it: either changes what the event waits for.
<!--skill-flavor:sdk-no-message:end-->

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

<!--skill-flavor:brownfield-merge-form:start-->
  In Studio Web, merge through the round trip of the [Validation loop](../SKILL.md#validation-loop): it compiles the edit to `<Draft>/edited/` and merges that file, never the `.bpmn.ts`.
<!--skill-flavor:brownfield-merge-form:end-->

<!--skill-flavor:sibling-deploy:start-->
  3. With the user's go-ahead, publish the open solution as [Publish and deploy](operate.md#publish-and-deploy) says, and have the user confirm it in Publish history.
     A personal-workspace publish deploys itself: run no `deploy run`. A shared-location publish is deployed once with `uip solution deploy run`, as that section says.
<!--skill-flavor:sibling-deploy:end-->

<!--skill-flavor:sibling-redeploy:start-->
  Ship the finished process by publishing the open solution again to the same destination.
  A personal-workspace publish deploys itself. After a shared-location publish, with the user's go-ahead, move step 3's deployment to it with
  `uip solution deploy upgrade --name <DEPLOYMENT_NAME> --package-name <PACKAGE_NAME> --output json` (with no `--version`, it takes the newest published one).
  Never run a second `deploy run`: it deploys to a new folder, which the node does not name.
<!--skill-flavor:sibling-redeploy:end-->

<!--skill-flavor:business-rule-key:start-->
  `<decisionKey>` is the decision's `OutputArguments` property name (such as `decision1`), not its display name: a display name reads null. Studio Web cannot read a rule's output contract, so read `vars.<id>_businessRuleResponse.<decisionKey>.<column>` downstream, the whole result the builder already maps; ask the user for the decision's output name when a later node needs one column, and whether the rule is decision-keyed when that is not known.
<!--skill-flavor:business-rule-key:end-->

<!--skill-flavor:in-solution-debug:start-->
  Debug runs the open solution, so it starts the child project; before reporting that the pair
  works, read the child's returned values from the parent run (`debug-instances variables-all`).
<!--skill-flavor:in-solution-debug:end-->
