<!--skill-flavor:sdk-upgrade:start-->
  Needs `@uipath/maestro-builder-sdk` 6.73.0 or later. Studio Web ships its own SDK: when it refuses `{ name, folder }` or the key-less `prepare`, tell the user that this Studio Web build cannot author a folder entity yet.
<!--skill-flavor:sdk-upgrade:end-->

<!--skill-flavor:folder-entity-resources:start-->
  Run `uip maestro bpmn refresh .` after the merge: it turns the two bindings into the entity's row in `bindings_v2.json`. Do not run `uip solution resources refresh`: it fails in Studio Web. Check with `uip solution resources list --source local --output json` that the solution declares the entity; when it does not, tell the user.
<!--skill-flavor:folder-entity-resources:end-->
