# document-extraction task — Planning

Runs a deployed IXP (Document Understanding) model on one file and returns the extraction result. Built-in type: `uip maestro case sdd convert` writes it from the SDD block; the deployment is not in the registry cache.

## When to Use

Pick this plugin when the sdd.md labels a task `document-extraction`: fields read from a semi-structured document (invoice, form, contract) by an IXP deployment.

Distinguish from:

- **Reasoning over the text** (classify, summarize, draft) → [agent](../agent/planning.md).
- **No deployment yet** → still `document-extraction`; the model is built and deployed with `uipath-ixp` before the build, and the task resolves once it exists.

## Required Fields from sdd.md

| Line | Required | Notes |
|---|---|---|
| `**IXP Deployment:**` | Yes | The deployment's title, as the solution lists it (`DeploymentTitle`). Becomes the `ixpDeployment` binding's `default` and `modelDisplayName`. |
| `**Model Name:**` | Yes | The deployment's `DeploymentName` (`<title-slug>-<hash>-ixp`), never the IXP project's name. |
| `**Folder Path:**` | Yes | The folder the deployment is deployed to. |
| `**Deployment Key:**` | Yes | The deployment's solution resource `Key`. |
| `**Folder Key:**` | Yes | The deployment's `FolderKey`. |

Inputs rows: `fileRef` (File, required) reads the document, e.g. `=vars.invoiceFile`; `pageRange` (Page range) is optional. Any other Inputs row is reported in `Data.Unresolved[]` and not written.

`isRequired`, `runOnlyOnce`, activation mode and entry rule come from the SDD task envelope, as for every task.

## Resolution

No registry cache lookup and no `tasks/registry-resolved.json` entry. When a line is `<UNRESOLVED>` or missing, fill it from two read-only lookups and update the SDD with the user's permission (Rule 2):

```bash
uip solution resources list --kind IxpDeployment --source remote --output json   # Name, Key, Folder, FolderKey
uip ixp projects list --output json                                               # the IXP project names
uip ixp deployments list "<IXP_PROJECT_NAME>" --output json                       # DeploymentName (Model Name) for the row whose DeploymentTitle is the Name
```

`Name` is `**IXP Deployment:**`, `Key` is `**Deployment Key:**`, `Folder` is `**Folder Path:**`, `FolderKey` is `**Folder Key:**`. Two remote deployments with the same `Name` in different folders are ambiguous: ask, never pick one by position. No deployment at all → the Rule 18 gate with `Force pull and re-resolve` and `Use placeholders for all` only; never `Create missing resources inline`. Training or deploying a model is `uipath-ixp`'s, not this skill's.

## Rules

1. **Outputs are fixed.** The task's outputs are `output` (the IXP result: `ExtractionResult` and `Taxonomy`) and `error`, matched case-insensitively. Read the result downstream per Rule 11 as `"Stage"."Task".output`. An arrow row (`| output | -> extraction |`) needs a `jsonSchema` case variable with a body schema. An Outputs row naming anything else is reported in `Data.Unresolved[]` as `output-type`.
2. **The file must reach `fileRef` at run time.** `uip maestro case debug` passes no case inputs, so a `fileRef` reading an In argument is empty in a debug run and the task faults `[430002] Invalid input on document extraction operation`. To debug, wire `fileRef` to an upstream task output that carries a file, or start the case through a trigger that does.

<!-- END: planning.md -->
