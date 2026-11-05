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

<!--skill-flavor:diagram-snapshot:start-->
1. Before the first write, copy the file to `/tmp`:
   `cp "<FILE>" "/tmp/<FILE_NAME>.before.bpmn"`. Record that path as
   `<SNAPSHOT_PATH>`.
<!--skill-flavor:diagram-snapshot:end-->
<!--skill-flavor:diagram-preserved-check:start-->
7. After the last write, and before `validate`, compare `<SNAPSHOT_PATH>` with
   the edited file. Studio Web has no Python, so check by hand that, apart
   from the ids you deleted:
   - the `BPMNPlane` still targets the same `bpmnElement`;
   - every pool and lane still has its shape, and every lane keeps its
     `bpmn:flowNodeRef`s;
   - every annotation and group survives, with its shape;
   - every surviving shape and edge keeps its color attributes;
   - every surviving node shape keeps its size (only pools, lanes and
     expanded subprocesses may grow);
   - surviving node shapes either stay put or all move by one common offset;
   - every surviving flow still has its `BPMNEdge`.

   For each loss: if the user asked for that diagram change, keep it and name
   it in the summary; otherwise restore the entry from the snapshot. Re-check
   at most twice, then list any remaining losses in the summary.
<!--skill-flavor:diagram-preserved-check:end-->
