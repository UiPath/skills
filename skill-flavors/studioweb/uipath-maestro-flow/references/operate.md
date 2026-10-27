<!--skill-flavor:operate-auth:start-->
Everything that touches the cloud: publish, deploy, debug, trigger, inspect,
and instance lifecycle. Studio Web signs you in to the tenant of the user, so
there is no login step.
<!--skill-flavor:operate-auth:end-->

<!--skill-flavor:operate-format:start-->
**Never run `format` on a merged file.** In Studio Web almost every write is a
merge into the canvas of the user. The `layout` of the original holds the
positions of the user, and `merge` keeps them and places each added node.
`format` lays out every node again and discards them.

A new `.flow` that `compile` wrote straight, with no merge, is different.
`compile` writes a placeholder `ui.position` on each node, all on one flat row,
and no top-level `layout` block. So run `format` once on such a file, before
the user opens it, unless its source sets `.layout()` (below):

```bash
uip maestro flow format <Name>.flow --output json
```
<!--skill-flavor:operate-format:end-->

<!--skill-flavor:layout-sdk-version:start-->
5. **`at` and `dim` need `@uipath/maestro-builder-sdk` 6.36.0 or later** — check that `dist/api-index.md` of the SDK that Studio Web ships lists them. If not, write the entry long-hand, `{ position: { x, y } }` with an optional `size: { width, height }`.
<!--skill-flavor:layout-sdk-version:end-->

<!--skill-flavor:operate-publish:start-->
"Publish" means the open solution, with `uip solution publish`. Studio Web
packages the solution and signs in, so there is no pack or upload step:

```bash
uip solution publish --output json
uip solution publish --location "<key or name>" --output json
uip solution publish --personal-workspace --output json
```

With no destination flag and one destination, it publishes there. With
several destinations, it publishes nothing and lists them: ask the user, then
run it again with `--location`. Offer exactly the choices the command returned.
Publish is asynchronous: tell the user to check the result in the Publish
history of Studio Web. A personal-workspace publish deploys itself. A
shared-location publish does not: deploy it with `uip solution deploy run`
(the `uipath-solution` skill has the contract).
<!--skill-flavor:operate-publish:end-->

<!--skill-flavor:operate-debug:start-->
```bash
uip flow debug <Project>
```

`<Project>` is a project name in the open solution, not a path; it defaults to
the open project. In Studio Web the verb is `uip flow debug`:
`uip maestro flow debug` fails here with `FlowDebugService is not a
constructor`. Debug runs the saved project, so there is no pack or upload step.

`flow debug` executes the flow for real: it sends the emails, posts the
messages, calls the APIs. It is not a validation step — `validate` is. Run it
when the request is for a flow that works; ask when the request stops at build
or validate; and with nobody to ask, report the flow as unverified rather than
letting a passing `validate` stand as the result. The reply is plain text:
[CLI-LOOP.md — Reading the reply](CLI-LOOP.md#reading-the-reply).
<!--skill-flavor:operate-debug:end-->

<!--skill-flavor:operate-debug-wait:start-->
- **The reply waits up to 120 s.** Pass `--timeout <seconds>` to change it,
  from 10 to 150.
- **`TimedOut after <N>s` is not a failure.** The run continues in the host.
  The reply has no instance id: when it gives a `Trace ID`, read the result
  later with `uip traces spans get <Trace ID>`; otherwise tell the user to
  check the run in the designer.
- **Never start a second debug while one is running,** a timed-out one
  included. It executes the flow again.
- **Re-run only after changing the flow.** Never to re-read the reply the
  completed run already returned.
<!--skill-flavor:operate-debug-wait:end-->

<!--skill-flavor:operate-debug-scratch-copy:start-->
- **Every process and connection node must resolve.** A node bound to a
  resource the tenant lacks (a placeholder key awaiting the real process, a stub
  connection) fails provisioning and starts no run, though `check` and
  `validate` pass it. Each connection must also be
  in the solution ([SKILL.md](../SKILL.md#the-connector-loop-in-studio-web),
  step 7). Name the blocking node to the user. Do not debug a copy of the
  project: Studio Web cannot delete the copy afterwards.
<!--skill-flavor:operate-debug-scratch-copy:end-->

<!--skill-flavor:operate-debug-inputs:start-->
```bash
uip flow debug <Project> --inputs '{"numberA": 5, "numberB": 7}'
```
<!--skill-flavor:operate-debug-inputs:end-->

<!--skill-flavor:operate-debug-attachment:start-->
`uip flow debug` in Studio Web cannot pass a file: it ignores `--attachment`.
To run a flow with a `types.file` input, ask the user to run it from the
designer.
<!--skill-flavor:operate-debug-attachment:end-->

<!--skill-flavor:operate-debug-entry-point:start-->
**A flow with more than one root starts at the default root.** That is the
trigger marked `isDefaultEntryPoint`, else the first trigger. To run another
root, pass its path exactly as the `entry-points.json` of the project lists it.
For a flow that is `content/<file>.bpmn#<triggerNodeId>`; the `content/` prefix
is optional:

```bash
uip flow debug <Project> --entry-point "content/<file>.bpmn#<triggerNodeId>"
```

A wrong value fails and lists the valid paths. A bare trigger node id is not a
valid value here.
<!--skill-flavor:operate-debug-entry-point:end-->

<!--skill-flavor:operate-debug-report:start-->
Report the status line first, then the `Trace ID` when the reply has one. The
reply has no Studio Web URL and no instance id: do not invent them.

`Faulted` means the cause is already in that same reply. Find the faulted
element and its message in `Execution trace`. For more detail, run
`uip traces spans get <Trace ID>`. Do not re-run the flow. When you expect a
long reply, redirect it to a file as you start the run, then search the file:
<!--skill-flavor:operate-debug-report:end-->

<!--skill-flavor:operate-debug-redirect:start-->
```bash
cd /solution/<Project>
uip flow debug <Project> > .flow-sdk/flow-debug.txt
```
<!--skill-flavor:operate-debug-redirect:end-->

<!--skill-flavor:operate-instance-id:start-->
Every `instance` command needs `--folder-key` (`-f`) or it is rejected before
reaching the API. Get one from `uip or folders list --output json`, or from the
job or process context. The instance id comes from a `job status` response or
`instance list`. A `uip flow debug` reply in Studio Web has none.
<!--skill-flavor:operate-instance-id:end-->

<!--skill-flavor:refresh-command:start-->
```bash
uip solution resources list --source local --output json
uip solution resources add --source remote --kind connection --cloud-key <ConnectionId> --output json
```
<!--skill-flavor:refresh-command:end-->

<!--skill-flavor:refresh-when:start-->
Do not run `uip solution resources refresh` in Studio Web. The solution has no
local `.uipx`, so the command fails with "no .uipx manifest found". Before
`uip solution publish` or `uip flow debug`, list the solution's local
resources. Add each connection the flow uses that is not in the list. A
connection that is not in the solution fails at run time with a binding error.
<!--skill-flavor:refresh-when:end-->

<!--skill-flavor:debug-shared-resources:start-->
  Shared resources reach the run through the connections of the open solution
  (`uip solution resources add`), not through the debug folder.
<!--skill-flavor:debug-shared-resources:end-->
