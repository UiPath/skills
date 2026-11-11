<!--skill-flavor:preflight-target:start-->
1. Confirm the target: a Studio Web debug run, or a publish of the open
   solution. **"Publish" means `uip solution publish`** of the open solution,
   to the destination the user chooses.
<!--skill-flavor:preflight-target:end-->

<!--skill-flavor:preflight-host:start-->
4. Make sure each connection is in the solution. Do not run
   `uip solution resources refresh` in Studio Web: the solution has no local
   `.uipx`, so it fails. Read each `connection` row in `bindings_v2.json`. For
   each one that the list does not show, add it:

   ```bash
   uip solution resources list --source local --output json
   uip solution resources add --source remote --kind connection --cloud-key <ConnectionId> --output json
   ```

   A connection that is not in the solution fails at run time with a binding
   error.
5. You are already signed in to the tenant of the user. Never run `uip login`
   or `uip login status`.
<!--skill-flavor:preflight-host:end-->

<!--skill-flavor:ship:start-->
## Publish and deploy

Studio Web owns the solution and packages it, so there is no `bpmn pack`, no
`uip solution pack` and no `uip solution upload` here. The canvas already shows
the open solution's files.

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

There is no standalone process publish here: `uip maestro bpmn process publish`
packs the project locally, and Studio Web owns packaging. Publish the solution.
<!--skill-flavor:ship:end-->

<!--skill-flavor:debug-run:start-->
A debug run is two steps: run it, then read its values.

1. **Run it.**

   ```bash
   uip maestro bpmn debug "<Project>" --inputs '{}'
   uip maestro bpmn debug "<Project>" --inputs '{"orderId": "O-1"}'
   uip maestro bpmn debug "<Project>" --inputs '{}' --entry-point "/content/<File>.bpmn#<StartEventId>"
   ```

2. **Read its values with the `Trace ID` it prints.** The `Trace ID` is the
   debug instance id. The trace lists each element's **status**, never a
   variable's **value**, so read the values right after the run. Report a value
   from this read, never from the process logic.

   ```bash
   uip maestro bpmn debug-instances variables <TRACE_ID> --output json
   uip maestro bpmn debug-instances variables-all <TRACE_ID> --output json
   uip maestro bpmn debug-instances incidents <TRACE_ID> --output json
   ```

`<Project>` is a project name in the open solution, not a path; it defaults to
the open project. Debug runs the saved copy of the process open in the
designer, so there is no pack or upload step.

**Always pass `--inputs`:** the input values as inline JSON, or `'{}'` when the
process takes none. `@file` is not supported. Without `--inputs`, Studio Web
opens its Debug configuration dialog, and the run waits for the user to click
**Save & Debug**. Confirm the values first, and redact secrets from the
summary. `--entry-point` takes the `filePath` exactly as `entry-points.json`
spells it. `--timeout <seconds>` defaults to `120`, clamped to `10`–`150`.
Pass no other flags.

**The output is plain text, not JSON:** the status, `Trace ID: <id>` when one
was found, the run logs and the execution trace. Exit 1 means `Faulted` or
`Failed`. `TimedOut after <N>s` also exits 1, but the run is still going in
Studio Web: do not troubleshoot it, and do not run it again. Tell the user to
follow the run in Studio Web.
<!--skill-flavor:debug-run:end-->

<!--skill-flavor:publish-default:start-->
- **Never deploy to Orchestrator because the user said "publish".** Publish the open solution with `uip solution publish`.
<!--skill-flavor:publish-default:end-->

<!--skill-flavor:offline-checks:start-->
Never use `debug` as validation. `check` and `validate` are the offline checks;
`debug` executes against real services.
<!--skill-flavor:offline-checks:end-->

<!--skill-flavor:fix-and-ship:start-->
When the action reveals a modeling or binding problem, the fix is in the
`.bpmn.ts`: run the [Validation loop](../SKILL.md#validation-loop) again, then
debug or publish again.
<!--skill-flavor:fix-and-ship:end-->

<!--skill-flavor:operate-scope:start-->
Everything past `validate` that touches the cloud: package metadata, Studio Web
publish, debug and deployed runs, job and instance inspection, and instance
lifecycle. These actions may contact UiPath services and external systems. You
are already signed in to the tenant of the user, so there is no `uip login`.
<!--skill-flavor:operate-scope:end-->
