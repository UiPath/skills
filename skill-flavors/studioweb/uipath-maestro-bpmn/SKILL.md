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
