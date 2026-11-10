# Operate — package, ship, run and manage a BPMN process

Everything past `validate` that prepares a project for the cloud or touches the
cloud: package metadata, `.nupkg` packaging, Studio Web upload, Orchestrator
publish, debug and deployed runs, job and instance inspection, and instance
lifecycle. These actions may contact UiPath services and external systems, and
all but the reads need `uip login`.

> **Ask before every cloud-side mutation.** Upload, publish, deploy, debug,
> process run, pause, resume, cancel, retry, migrate and cursor movement each
> need the user's clear decision for that action. Consent to validate or package
> is not consent to run. A debug run is a REAL run: it calls connectors, starts
> child processes, creates Action Center work, mutates queues and sends messages.
>
> **Where you came from.** The project is authored in `<Name>.bpmn.ts`, compiled into `<Project>/<Name>.bpmn`, formatted and validated (SKILL.md).
> A failed or stuck run is investigated in [diagnose.md](diagnose.md), and the fix goes back into the `.bpmn.ts`.

<!--skill-flavor:upload-consent:start-->
The one exception is the Studio Web upload of a project this run created: a request to build or draft the process authorizes the upload that shows it ([Studio Web upload](#studio-web-upload)).
<!--skill-flavor:upload-consent:end-->

## Pre-flight, before any cloud action

<!--skill-flavor:preflight-target:start-->
1. Confirm the target: package only, Studio Web upload, or Orchestrator
   deployment. **"Publish" means Studio Web upload** unless the user names
   Orchestrator.
<!--skill-flavor:preflight-target:end-->
2. Confirm the compiled `.bpmn` has been formatted and passes
   `uip maestro bpmn validate`, and that every connector node has been through the
   CLI's Integration Service enrichment — a draft with unresolved enrichment is
   not executable.
3. Regenerate the package metadata from the compiled BPMN:

   ```bash
   uip maestro bpmn refresh <project-path> --output json
   ```

   `refresh` needs the project's `project.uiproj` (`bpmn init` wrote it) and
   rewrites the four derived files — `bindings_v2.json`, `entry-points.json`,
   `operate.json`, `package-descriptor.json`; `Data.WrittenFiles` names the ones
   that were stale, which is the drift report. Never hand-edit those files and
   never use the deprecated `update-metadata`: it does not materialize `Intsvc.*`
   connection bindings, so a package it wrote validates and faults at run time.
<!--skill-flavor:preflight-host:start-->
4. Refresh the solution's declared resources when the project sits in the
   solution `bpmn init` scaffolded (it does unless `--skip-solution-registration`
   was passed), so generated resource files and debug metadata are current:

   ```bash
   uip solution resources refresh --solution-folder <SolutionDir> --output json
   ```

5. Confirm login:

   ```bash
   uip login status --output json
   ```
<!--skill-flavor:preflight-host:end-->

6. Check the generated files for public-safety before committing or sharing:
   no tenant URLs, folder keys, connection ids, user data, payloads or local paths.

**Always include folder context on the runtime commands that require it**:
`process list`, `get` and `run` require `--folder-key`, and every
`instance` subcommand and `incident get` take `--folder-key` or `-f`.

<!--skill-flavor:ship:start-->
## Package

```bash
uip maestro bpmn pack <project-path> <OutputDir> --output json
```

Pass `--name` and `--version` only for a public-safe identity the user gives.
Report the package path and identity the CLI returns. `pack` consumes the
refreshed files; if they changed, that was the `refresh`, not the pack.

## Studio Web upload

```bash
uip solution upload <SolutionDir> --output json
```

The project's solution directory is what `bpmn init` scaffolded around it
(`<Name>Solution/`), or the solution it was initialized inside.
A project initialized with `--skip-solution-registration` has no solution, and upload and deploy both require one.
Create one beside it with `uip solution init <SolutionName> --output json`, `cd <SolutionName>`, run `uip solution projects import <project-path> --output json` with `<project-path>` relative to that folder (for example `../A/B`), and upload the solution.
Ask before doing this when the user named the project's path, because the uploaded copy lives in the new solution folder, not at that path.
When the solution declares resource dependencies, refresh them with the solution tooling the installed CLI offers (check `uip solution --help` rather than inventing a verb) and confirm the generated resource files match.
Report the Studio Web URL (`Data.DesignerUrl`) or solution id; when the CLI returns none, write `Studio Web URL: <not returned by CLI>` rather than omitting it.

**Consent.** Unless the request forbids upload, a request to build or draft the process authorizes the upload that shows it, so upload without asking when this run's `bpmn init` scaffolded the solution.
Confirm first when it did not — the project went into a solution that already existed, or an existing project was edited in place — because `upload` overwrites the cloud solution that matches the `SolutionId` in the local `.uipx`.
Ask once, before the first upload, and say in the question that the upload replaces the Studio Web copy.

**Each later upload overwrites the same solution.**
The first upload writes the cloud solution id back into the local `.uipx`, so each upload after it reports `Data.Action: "Overwritten"` with the same `SolutionId` and `DesignerUrl`.
`"Imported"` on a later upload means that id was lost and a second cloud solution was just created: stop and fix that before continuing.

### Check the cloud copy before editing

An upload replaces the cloud copy with the local one, so it would erase edits made in Studio Web.
Check the cloud copy before you start editing a project in a solution this run did not scaffold, so you build on the current copy, and again before each edit after this run's own first upload: the user may have changed the canvas between turns.
Download the solution by the `SolutionId` in its `.uipx`, into a fresh directory outside the workspace:

```bash
uip solution download <SOLUTION_ID> --extract -d "$(mktemp -d)" --output json
```

- A failure whose `Instructions` say "Studio Web API returned 404" means there is no cloud copy yet (`init` writes a `SolutionId` before any upload): upload.
- A failure for another reason (offline, not logged in, a timeout): the cloud copy is unchecked, and an upload would replace whatever is there.
  You may keep working on the local files, but do not upload until a download and comparison succeed, or until the user, told that the check failed and that the upload would replace the Studio Web copy unseen, says to replace it.
  Retry the download before the upload; when it still fails, ask, and say in the reply that nothing was uploaded.
- Otherwise compare each project's `.bpmn` in the download with the local one.
  Studio Web reformats the `.uipx` and `project.uiproj` and adds `SolutionStorage.json`, so only the `.bpmn` files tell real edits apart.
  When they match, carry on.

When they differ, ask which copy to keep, unless the user is answering a draft gate this run showed: then they edited the outline you uploaded, so build on their copy without asking, and say so in the reply.
To build on the Studio Web copy, treat it as the original of a [brownfield edit](bpmn-runtime.md#brownfield-editing): copy its `.bpmn` over `<Project>/<Name>.bpmn`, seed `<Name>.bpmn.ts` from it with `uip maestro bpmn decompile --style nested`, compile that source as the baseline before editing, and merge the compiled edit back with `uip maestro bpmn merge <edited.bpmn> --original <Project>/<Name>.bpmn --baseline <baseline.bpmn> -o <Project>/<Name>.bpmn`, so the user's layout and the elements you did not touch stay as they drew them.
Compile the baseline and the edit into a `mktemp -d` directory outside the workspace, as the download above does, so the workspace keeps exactly one `<Name>.bpmn`: a scratch folder elsewhere in the workspace leaves a second `.bpmn` for the next reader, and tools that search the workspace for `*.bpmn` find it.

## Orchestrator deployment

Only when the user explicitly asks for a deployed process.
Confirm the package identity, the target folder and the feed first.
A project with no solution needs one first; see [Studio Web upload](#studio-web-upload).

```bash
uip maestro bpmn pack <project-path> <OutputDir> --output json
uip solution pack <SolutionDir> <OutputDir> --output json
uip solution publish <PackageZip> --output json
```

Activation and the `uip solution deploy` steps that follow are the platform
skill's; this skill stops at the BPMN project and package boundary.
<!--skill-flavor:ship:end-->

## Debug — a controlled Studio Web run

<!--skill-flavor:debug-run:start-->
```bash
uip maestro bpmn debug <project-path> --output json
uip maestro bpmn debug <project-path> --inputs @inputs.json --output json
uip maestro bpmn debug <project-path> --folder-id <FOLDER_ID> --output json
```

Confirm the input values and the target folder first, and redact secrets from
the summary. Parse and report `Data.jobKey`, `Data.instanceId`, `Data.runId`,
`Data.solutionId` and `Data.finalStatus`; match keys case-insensitively, the
casing varies by CLI version.

The debug output lists each element's **status**, never a variable's **value**.
A `Completed` run with every element green proves the process ran, not that any
output holds the expected value. Read the values in the same session, right
after the run — a debug instance is ephemeral:

```bash
uip maestro bpmn debug-instance variables-all <INSTANCE_ID> --output json
uip maestro bpmn debug-instance variables <INSTANCE_ID> --output json
uip maestro bpmn debug-instance incidents <INSTANCE_ID> --output json
```
<!--skill-flavor:debug-run:end-->

<!--skill-flavor:offline-checks:start-->
Never use `debug` as validation. `check`, `validate` and the local engine
(`flow-debug`, which runs the compiled `.bpmn` on this machine with every
service mocked) are the offline checks; `debug` executes against real services.
<!--skill-flavor:offline-checks:end-->

## Run a deployed process

```bash
uip maestro bpmn process list --folder-key <FOLDER_KEY> --output json
uip maestro bpmn process get <PROCESS_KEY> --feed-id <FEED_ID> --folder-key <FOLDER_KEY> --output json
uip maestro bpmn process run <PROCESS_KEY> --folder-key <FOLDER_KEY> --release-key <RELEASE_KEY> --inputs @inputs.json --output json
```

`get` also requires `--feed-id`; `run` requires `--release-key`.
Take `<FOLDER_KEY>` from the user, or the `Key` of `uip or folders list --output json`.
From the `process list` entry take `<RELEASE_KEY>` (`releaseKey`) and `<FEED_ID>` (`feedId`).
`<PROCESS_KEY>` is `<processKey>:<processVersion>` from that entry, for example `MyProcess:1.0.0`.
Add `--feed-id` or `--robot-ids` to `process run` only when the user supplies them or the list entry identifies them.

## Inspect a job or instance

Status first, then incidents and variables when the status is faulted or
ambiguous, traces last. Every `instance` command needs `-f <FOLDER_KEY>`.

```bash
uip maestro bpmn job status <JOB_KEY> --folder-key <FOLDER_KEY> --output json
uip maestro bpmn instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn job traces <JOB_KEY> --output json
```

When a run starts, report the Studio Web URL if returned, the process key, job
key, run id, solution id or instance id, the folder, the input summary with
secrets redacted, the final status if the command waited, and the next
inspection command. When the user cares about a business result, the final
status is not enough: report the output variable and the value the API returns,
and say so when the debug API returns a root output as `null`.

## Manage a running instance

Each of these is a cloud-side mutation and needs the user's decision for that
specific action on that specific instance. For retry, migrate and cursor
movement, diagnose first ([diagnose.md](diagnose.md)) and correlate the deployed
asset.

```bash
uip maestro bpmn instance list --output json
uip maestro bpmn instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance pause <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance resume <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance cancel <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance retry <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance migrate <INSTANCE_ID> <NEW_VERSION> -f <FOLDER_KEY> --output json
uip maestro bpmn instance goto <INSTANCE_ID> '[{"sourceElementId":"A","targetElementId":"B"}]' -f <FOLDER_KEY> --output json
```

| Action | When |
| --- | --- |
| `pause` / `resume` | halt a running instance keeping its state, and continue it |
| `cancel` | the instance must stop and not continue from where it is |
| `retry` | the root cause is understood and the same definition is expected to succeed |
| `migrate` | the user chooses a different package version for this instance |
| `goto` | the user names the source and target element ids to move the cursor between |

After every lifecycle command, fetch the instance again and report its status.
<!--skill-flavor:fix-and-ship:start-->
When the action reveals a modeling or binding problem, the fix is in the
`.bpmn.ts`: recompile, format, validate, `refresh`, and ship again.
<!--skill-flavor:fix-and-ship:end-->

## Anti-patterns

- **Never debug or run without the user's explicit consent for that run.**
<!--skill-flavor:publish-default:start-->
- **Never deploy to Orchestrator because the user said "publish".** Studio Web upload is the default.
<!--skill-flavor:publish-default:end-->
- **Never upload an executable process with unresolved Integration Service enrichment.**
- **Never fix a packaging error by editing the generated JSON.** Fix the source, recompile, `refresh`.
- **Never treat package generation as authoring** — the four files are derived from the compiled BPMN.
- **Never retry a faulted instance before reading its incidents and deployed asset.**
- **Never omit the folder key** on `process list`/`get`/`run`, `instance …` and `incident get`.
- **Never put tenant, folder, feed, connection or payload values in examples or summaries.**
