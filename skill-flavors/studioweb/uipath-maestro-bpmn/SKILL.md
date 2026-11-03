<!--skill-flavor:named-solution-init:start-->
   A named solution is the one Studio Web already has open as the workspace
   root. Never create another; run `init` from that root. A
   `Data.AutoCreatedSolution` in the response means `init` ran outside it:
   re-run it from the root and report the stray directory.
<!--skill-flavor:named-solution-init:end-->
<!--skill-flavor:delegated-resource-solution-first:start-->
   (1) Studio Web already has one open solution as the workspace root.
   Never create a new one. Create the resource's project inside it the way
   its owning skill's Studio Web flavor says: an API workflow through the
   `CreateProjects` host tool, an RPA project with `uip rpa init`.
<!--skill-flavor:delegated-resource-solution-first:end-->
<!--skill-flavor:delegated-resource-author-deploy:start-->
   (2) Delegate authoring to the resource's owning skill (e.g.
   `uipath-api-workflow`) with an explicit argument contract: declared inputs
   and outputs, not an unauthored scaffold. RPA authoring is not supported in
   Studio Web: stop at the `uip rpa init` scaffold and hand the workflow to
   the user. (3) After explicit user approval, publish the open solution with
   host-intercepted `uip solution publish` **before** binding the resource
   into the BPMN node; its release key and folder key exist only once
   deployed. There is no `pack`. Publishing to the personal workspace
   auto-deploys; a shared location needs `uip solution deploy run`. Follow
   `uipath-solution` for destinations and redeploys.
<!--skill-flavor:delegated-resource-author-deploy:end-->

<!--skill-flavor:v2-solution-resources-refresh:start-->
   Studio Web keeps the open solution's resources in sync after
   `bpmn refresh`: skip the `uip solution resources refresh` step that
   `Data.V2.Instructions` ends with. It is Node-CLI-only and is not run here.
<!--skill-flavor:v2-solution-resources-refresh:end-->

<!--skill-flavor:debug-node-output:start-->
   (5) Unless the task forbids
   live runs or asks for a draft or handoff, run the process
   (`uip maestro bpmn debug "<ProjectName>"`) and read the node's output in the
   execution trace it prints. Map `=result.<key>` to the key that output
   used; a scalar can surface under a generic key instead of the schema
   property name. Without a run, use the schema name and report the mapping
   as unverified. A business rule maps its whole result as one `output` from
   `=result`, never one output per decision or column.
<!--skill-flavor:debug-node-output:end-->

<!--skill-flavor:login-status-check:start-->
- **1a Read the toolbox kinds.** The sandbox supplies login and denies
  `uip login status`: never run it, and treat the session as logged in.
  Chain 1a in the same Bash call as 1b's scan, not a turn of its own.
<!--skill-flavor:login-status-check:end-->

<!--skill-flavor:wellformed-check:start-->
   The sandbox has no `python3`, so `validate` is the parse check: a
   `ParseError` or `XML_NOT_WELL_FORMED` finding is a source defect to fix
   before anything else. Run the CLI validator, which runs the full
   PO.Frontend canvas rule set (structural rules plus variable, method-call,
   input-type, and event-object checks) offline, plus deploy-readiness checks:

   ```bash
   ! grep -nE '</?bpmn:[A-Z]' <file.bpmn> &&
     uip maestro bpmn validate <file.bpmn> --output json
   ```
<!--skill-flavor:wellformed-check:end-->

<!--skill-flavor:final-path-line:start-->
  The process is on the canvas
<!--skill-flavor:final-path-line:end-->
