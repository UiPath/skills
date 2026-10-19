# document-extraction task — Implementation

> **Phase split.** Written in Phase 2 by `uip maestro case sdd convert`. Phase 3 adds the deployment to the solution and syncs its sidecar entry. See [`../../../phased-execution.md`](../../../phased-execution.md).

## Convert writes this task

`sdd convert` emits every `document-extraction` task in the shape the Case Designer saves: `type: "document-extraction"`, `data.name: "Document extraction"`, `data.serviceType: "IXP.Extraction"`, `data.version: "v2"`, and a `context` of seven entries in this order: `solutionResourceKey` (Deployment Key), `name` (`=bindings.<id>`), `folderKey`, `folderName`, `modelName`, `modelDisplayName` (IXP Deployment) and `digitizationMode: "fileUpload"`. Inputs are `fileRef` and `pageRange`; outputs are `output` (`=result`) and `error` (`=Error`), with `var` numbered apart across tasks (`output2`, …).

One root binding names the deployment: `resource: "ixpDeployment"`, `resourceKey` the Deployment Key, `default` the IXP Deployment, `propertyAttribute: "name"`. There is no folder binding; the folder is a literal key in `context`. Two tasks on the same deployment share the binding.

1. **Never hand-write the `context`, the binding or the outputs.** Fix the SDD line and re-run convert instead.
2. **When convert cannot write the task, write a [placeholder](../../../placeholder-tasks.md).** That is a CLI whose `uip maestro case task-types list --output json` does not list `document-extraction` under `Authorable`, and every brownfield add, which runs no convert. Tell the user to configure the task in Studio Web, or to upgrade the CLI and rebuild; never improvise the shape.
3. **Work the `Data.Unresolved[]` entries for the task** — a missing deployment line, an empty `fileRef`, an Inputs row other than `fileRef`/`pageRange`, an Outputs row other than `output`/`error` — by fixing the SDD per [planning.md § Resolution](planning.md#resolution) and re-running convert. Report any left to the user in `build-issues.md`.

## Add the deployment to the solution

After `uip solution init` and before the Step 9 `bindings sync`, import the deployment once per IXP Deployment:

```bash
uip solution resources add --source remote --kind IxpDeployment --name "<IXP_DEPLOYMENT>" --output json
```

It is idempotent, returns the same `Key` as `**Deployment Key:**`, and writes the solution's debug overwrite for the deployment. Without it, Studio Web shows the task red ("No debug overwrite configured") and `case debug` cannot resolve the model. A returned `Key` that differs from the SDD's Deployment Key means the SDD names a different deployment: stop and ask.

Then `uip maestro case bindings sync` writes the deployment's sidecar entry (`resource: "ixpDeployment"`, keyed by the Deployment Key, `ActivityName` the task's name), as the Designer regenerates it (SKILL.md Rule 15).

## Post-Write Verification

- `type: "document-extraction"`, `data.serviceType: "IXP.Extraction"`, `data.version: "v2"`, and the seven `context` entries with no `null` value.
- One `ixpDeployment` root binding per deployment, its `resourceKey` equal to `context[solutionResourceKey]`; no `CASE_MGMT_BINDING_PAIR_INCOMPLETE` from `uip maestro case validate`.
- `fileRef` is not empty, and `data.outputs` is `output` and `error`.
- `bindings_v2.json` has the `ixpDeployment` entry after `bindings sync`, and the solution lists the deployment after `resources add`.

<!-- END: impl-json.md -->
