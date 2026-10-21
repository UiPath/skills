# UiPath Solution Workspace

> **A `.uipx` file in this directory marks a UiPath solution. Drive every solution operation through the `uip` CLI — packing, publishing, deploying, and deployment configuration.** Do not hand-edit `.uipx`; manage projects via `uip solution projects ...` so the manifest stays internally consistent. Load the `uipath-solution` skill before running `uip solution` commands or editing `.uipx` (`uip skills install`).

This file is a static snapshot, scaffolded by the `uip` CLI version `1.205.0`. If the CLI version you have access to is different, there may be inconsistencies in the commands or options listed below. When you encounter one, look up the current form with `uip <group> --help` and **edit this file in place** — find and replace the stale command with the working one. Do the same for anything missing: if `--help` lists a command, subcommand, or option this file does not cover, add it to the table or section where it belongs.

## The `.uipx` Manifest

`<solution>.uipx` is a JSON document at the solution root listing every project in the solution. Skeleton:

```json
{
    "DocVersion": "1.0.0",
    "StudioMinVersion": "2025.10.0",
    "SolutionId": "<uuid>",
    "Projects": [
        {
            "Type": "Process",
            "ProjectRelativePath": "MyProcess/project.json",
            "Id": "<uuid>"
        }
    ]
}
```

Typical layout:

```text
my-solution/
    my-solution.uipx          ← solution manifest
    AGENTS.md                 ← this file (Codex, Cursor, generic agents)
    CLAUDE.md                 ← identical copy (Claude Code)
    ProjectA/
        project.json
        bindings_v2.json      ← per-project resource declarations
        ...
    ProjectB/
        project.uiproj
        ...
```

You must manage membership via the CLI, never by editing the manifest. All these operations work entirely on local files (`.uipx` plus the solution-builder artefacts on disk) and do not require `uip login` — auth is only needed once you reach `pack` / `publish` / `deploy` / `upload`.

| Intent | Command |
|---|---|
| Create a solution | `uip solution init <name>` |
| Register an existing subfolder of the solution dir as a project (no copying — use after scaffolding *inside* the solution dir, e.g. `uip rpa create-project --location <solution-dir>`) | `uip solution projects add <project-path> [<solution-file>]` |
| Add a project from outside the solution — copies the folder at `<path>` into the solution dir and registers it (`<path>` is a local filesystem path) | `uip solution projects import <path>` |
| Unregister a project (does not delete the project files on disk) | `uip solution projects remove <project-path> [<solution-file>]` |
| List projects in the solution | `uip solution projects list` |

The `uip ...` scaffolders (`agent init`, `maestro flow init`, `maestro bpmn init`, `maestro case init`, `api-workflow init`, `codedapp init`, `rules init`, and `function init` for Python functions only) **auto-register** the new project when run inside a solution directory — they walk up for the enclosing `.uipx` and add it to `Projects[]` automatically, so a separate `project add` is not needed. Pass `--skip-solution-registration` to scaffold standalone without registering; the output's `Data.SolutionRegistration.Status` is then `OptedOut`. The full set of `Status` values is: `Registered` / `AlreadyRegistered` (added in this run / already present), `NotInSolution` (no enclosing `.uipx` found), `OptedOut` (`--skip-solution-registration` passed), `Skipped` (a candidate solution was found but registration was not safe to attempt — e.g. multiple `.uipx` in one directory, or the project sits outside the solution dir), and `Failed` (manifest read/parse/write error).

## Project Types

A solution can contain multiple projects of different types. The table below lists each project type and the `uip` command that scaffolds a fresh one (or marks the row when no scaffolding command exists).

| Type | Description | Scaffold with | Skill |
|---|---|---|---|
| `Process` | RPA process — Studio workflow (XAML, Coded C#, or Hybrid) | `uip rpa create-project --name <name>` | `uipath-rpa` |
| `Tests` | Test Automation project | `uip rpa create-project --template-id TestAutomationProjectTemplate --name <name>` | `uipath-rpa` |
| `Flow` | Maestro Flow — long-running orchestrated workflow | `uip maestro flow init <name>` | `uipath-maestro-flow` |
| `CaseManagement` | Maestro Case — stateful business process (SLA, approvals, HITL) | `uip maestro case init <name>` | `uipath-maestro-case` |
| `ProcessOrchestration` | Maestro BPMN — long-running orchestrated process | `uip maestro bpmn init <name>` | `uipath-maestro-bpmn` |
| `Agent` | LLM agent project — **low-code** (configured via `agent.json`; no Python) or **coded** (Python: LangGraph / LlamaIndex / OpenAI Agents). Both subtypes share `ProjectType: "Agent"`; the discriminator is `agent.json#type`. | `uip agent init <path>` (low-code) · `uip codedagent new [name]` (coded — see the `uipath-agents` skill for the full flow) | `uipath-agents` |
| `AppV2` | Coded App — web application | `uip codedapp init <path>` | `uipath-coded-apps` |
| `Function` | UiPath Function (JS / TS / Python) | `uip function new [name]` | `uipath-functions` |
| `Api` | API Workflow project | `uip api-workflow init <name>` | `uipath-api-workflow` |
| `BusinessRules` | Business rule — one or more DMN decisions. Packs to a `.uirule` (its `.dmn` files plus `entry-points.json`), not a `.nupkg` | `uip rules init <name>` | `uipath-rules` |
| `Entity` | Data Fabric entity project — one folder per project, one `.entity` pointer file per entity; the schema itself lives in `resources/solution_folder/entity/native/<Name>.json`. Emits no package: the entity resources are the deployable payload, so `solution pack` validates the project instead of building it. | `uip df entities create <Name> --local` — scaffolds the project when it does not exist (named after the entity unless `--project-name` says otherwise), and adds a further entity when it does; `entities list`/`get`/`update`/`validate`/`delete` with `--local` work on them afterwards. Prefer these to hand-writing the `.entity` file or its resource — the pointer and the schema must stay in step, and `solution pack` fails if they do not. Entities are also modelled in the UiPath VS Code extension. | `uipath-platform` (covers `uip df` entities, records and choice sets) |
| `Connector` | Integration Service connector | no CLI scaffolding — use `uip is connectors` to list / get / export existing connectors | `uipath-connector-builder` |
| `WebApp` | Legacy low-code UiPath App (the coded variant is `AppV2`) | no CLI scaffolding | none |

Install the skills with `uip skills install`. The general-purpose `uipath-platform` skill covers what isn't in a type-specific skill, and `uipath-solution` covers the solution lifecycle itself.

A `BusinessRules` project gets its `businessRule` resource when it is added to the solution, and `uip solution resources refresh` regenerates it if it goes missing. `Library` and `Tests` projects declare no solution resources, and refresh skips them.

**`Library` is not a project type here.** A library is a reusable `.nupkg` consumed as a NuGet dependency, so `projects add` / `import` reject it and auto-registration returns `SolutionRegistration.Status: "Skipped"`. Publish it on its own (`uip rpa pack <project-dir> <output-path>`, then `uip or libraries upload --file <nupkg-path>`) and either reference it from a project's dependencies or attach it to this solution as a resource: `uip solution resources add --source remote --kind Library --name <library-name>`.

The type lives in either `project.uiproj` (top-level `ProjectType`) or `project.json` (`designOptions.outputType`, falling back to top-level `ProjectType` when `outputType` is absent — read or write either field). A third form exists but is narrow: `uipath.json` is read as a project manifest **only** for a code-first Functions project, which is recognised by a `functions` map inside it. Other project kinds keep a `uipath.json` for their own config — a coded app stores its SDK settings there — and that file is not what registers them: a coded app is registered from the `project.uiproj` that `uip codedapp init <path>` writes. Pointing a solution at a coded app's `uipath.json` (or at its `package.json`) fails, because neither carries a `ProjectType`.

The `init` scaffolders above auto-register when run inside a solution directory (unless `--skip-solution-registration` is passed). For other scaffolders, register the project with the solution after scaffolding: use `uip solution projects add <project-path> [<solution-file>]` when the project already lives inside the solution directory (registers in place, no copy), or `uip solution projects import <path>` to copy a project from outside the solution dir into it and register it. If you pass an unknown type to those commands, they reject with the exhaustive accepted list — trust that error over this table. `uip solution pack` rejects the same way: a `Projects[]` entry whose `Type` no packager handles fails with `ErrorCode: invalid_argument`, naming the project, the accepted types, and how to drop the entry, rather than attempting the pack.

`projects add` and `projects remove` take **either** the project folder or its manifest file: `uip solution projects remove my-app` and `uip solution projects remove my-app/project.uiproj` do the same thing. That matters because the `.uipx` records a project by its manifest file (`ProjectRelativePath: "my-app/project.uiproj"`), so the path `pack` quotes back when it refuses an entry can be pasted straight into `remove`. `projects import` is the exception — its argument is an external folder to copy, so give it a directory.

**Member package ids come from folder names, and pack refuses the ones a feed cannot store.** Each member is published under `<solution>.<project-type>.<member-folder>` — the solution's own `.uipx` name, the short type (`Rpa`, `Case`, `Flow`, …) and the member's folder inside the solution. The name a project declares for itself is not used, and `--name` renames the archive only. Two limits ride on that, both checked before anything is packed and both reported as `ErrorCode: invalid_argument` / `Retry: RetryWillNotFix`:

- **Unique.** Two members whose folders compose the same id fail the pack, naming the shared id and every folder that produced it. Spaces and dots both collapse to a single dot and NuGet ids are case-insensitive, so `collide me`, `collide.me` and `Collide.Me` are one id.
- **100 characters.** A composed id longer than that fails the pack, naming the member folder that blew the limit.

The fix for either is a rename — the member folder, or the `.uipx`. A whole-solution pack takes no `--package-id`; only a single-project pack (`--project`, below) can override the id.

## End-to-End Lifecycle

Run `uip login` first — most steps below need an authenticated session, including `solution pack` in some cases.

```bash
# 1. Authenticate
#    Interactive (browser OAuth):
uip login
#    Non-interactive (CI / CD) with client credentials — read the values from
#    environment variables so the secret stays out of shell history:
uip login --client-id env.UIPATH_CLIENT_ID --client-secret env.UIPATH_CLIENT_SECRET --tenant <TENANT>

# 1a. (Optional) Restore project dependencies before packing. Resolves NuGet
#     deps (including authenticated Orchestrator feeds) so pack can compile.
#     Useful in CI: login -> restore -> pack. Takes <solutionPath> as its only
#     positional arg and does not produce a package. Pack also restores
#     internally, so this is an optimization, not a requirement.
uip solution restore .

# 2. Pack the solution into a .zip. Two positional args:
#    <solutionPath>  — solution dir (containing .uipx) or a .uis file
#    <output-path>   — directory where the .zip is written (required unless --dry-run)
uip solution pack . ./out

# 2a. (Optional) Validate the solution against the strict deploy-time
#     pipeline without producing a package — useful as a CI gate.
uip solution pack . --dry-run

# 2b. (Optional) Pack ONE project into its own .nupkg instead of the .zip.
#     It packs as a stand-alone project: no solution resources go into it, so
#     a project that uses one is published without it.
#     --project takes the project's Id from the .uipx or its path relative to
#     the solution folder. The package id defaults to the one the solution
#     pack gives the project; --package-id (only with --project) overrides
#     it, and --name is refused with it. Data.Packages is the absolute path of
#     the .nupkg. An unknown --project fails with invalid_argument and lists
#     the valid Ids and paths.
uip solution pack . ./out --project <project-id-or-path> [--package-id <id>]

# 3. Publish the packed .zip to Orchestrator
uip solution publish ./out/<package>.zip

# 4. Fetch the default deployment configuration for the published package
uip solution deploy config get <package-name> --destination config.json

# 5. (Optional) Customize the config — see "Deployment Configuration" below

# 6. Deploy. By default this also activates; pass --skip-activate to defer.
uip solution deploy run \
    --name <deployment-name> \
    --package-name <package-name> \
    --package-version <version> \
    --folder-name <new-folder> \
    --parent-folder-path Shared \
    --config-file config.json

# 7. The deploy returns a pipeline deployment ID — track it:
uip solution deploy status <pipeline-deployment-id>    # that run's progress and errors; a deployment name or key gives the record's state instead

# 8. List every deployment in the active tenant
uip solution deploy list
```

`deploy run` also takes `--parent-folder-key <key>` in place of `--parent-folder-path`, and `--personal-workspace` to deploy into your Personal Workspace instead of the tenant.

**Listing one folder's deployments.** `uip solution deploy list --folder-path <path>` (or `--folder-key <key>`) lists the deployments installed into that folder. The Solutions search does the filtering, so `--limit`, `--offset` and `Pagination.Total` all count matching deployments: page with `--offset <previous Offset + Returned>` while `Pagination.HasMore` is true. The match is on the folder's **full path** (`Shared/Finance`, not `Finance`), exact and not case-sensitive, and deployments in its subfolders are **not** included — list each subfolder with its own call. `FolderPath` is the folder the deployment was installed *into*; a row's `FolderKey` is the deployment's own solution folder one level below it, so passing that key to `--folder-key` matches no deployment — use the key of the `FolderPath` folder instead.

**Every deploy waits, and validates first.** `deploy run` — tenant, `--personal-workspace` or `--feed` — goes through the Pipelines install, which validates the package against the target *before* it schedules the install, then polls the run to a terminal state and reports `Status: "DeploymentSucceeded"` with `DeploymentKey`, `PipelineDeploymentId` and `InstanceId`. A validation failure ends in `Status: ValidationFailed` with the per-resource errors in `Instructions`, and nothing is installed. `--timeout <seconds>` (default 360) bounds each polling phase; running out exits `2` with `ErrorCode: timeout` and `Retry: RetryLater` — "may still be running", so check `uip solution deploy status <pipeline-deployment-id>` rather than treating it as a failed install. `--wait` is accepted for backwards compatibility and does nothing. Deploying into a Personal Workspace or a folder feed needs a **user session**: under an external app's client-credentials token, `--personal-workspace` is refused before anything is requested and `--feed` is refused once it resolves to a feed other than the tenant feed (`ErrorCode: permission_denied`), because the server ignores the feed header on that token type and the install would otherwise land on the tenant feed under the requested name. A `--feed` that names the tenant feed is fine from CI/CD, as is omitting the flag. Reading a feed is the same: `deploy list` and `deploy status` with `--personal-workspace` or a folder-feed `--feed` refuse an external app (`ErrorCode: permission_denied`) instead of showing the tenant feed's records under that feed's name. A session whose kind cannot be read from its token is refused the same way; `uip login` records an interactive login as a user session.

**Upgrading in place.** `uip solution deploy upgrade <deployment-key>` (the `Key` from `deploy list`) or `uip solution deploy upgrade --name <deployment-name> --package-name <pkg>` moves an existing deployment to another published version of its package (newest by default, or `--version <version>`) and keeps the values already set on it. Both forms work from a CI/CD pipeline signed in as an external app. With a key, the deployment's name, package and feed are read from the server, so no `--package-name` or `--personal-workspace` is needed, and the result also carries `FromVersion` and `InstallDeploymentKey` — the key that stays the same across upgrades, so store that one rather than `DeploymentKey`, which changes with every upgrade. It uses the same Pipelines install, so it validates before it installs: on success it reports `Status: "DeploymentSucceeded"`, `Operation`, `DeploymentStatus`, `Actions`, `ToVersion`, `PipelineDeploymentId` and `DeploymentKey`; on a validation failure it reports the errors and the deployment stays on its current version. `--no-wait` returns `Status: "Accepted"` as soon as the install is queued. An external app can only upgrade tenant-feed deployments: the server ignores the feed header on client-credentials requests, so a Personal Workspace or folder-feed deployment is refused and needs a user session.

**Key or name — how the two forms differ.** The key form makes one extra Pipelines call, the deployment lookup, and needs nothing else: it works on any server that has that lookup. On a server without it, a user session reads the key through the Solutions API instead (tenant feed, or your Personal Workspace with `--personal-workspace`; a folder-feed deployment needs the name form) and the result carries no `FromVersion`; an external app gets `ErrorCode: not_found`, and the message points at the name form. The name form needs `--package-name` because the install route is addressed by name and nothing name-keyed in Pipelines reports a deployment's package; with `--version` as well it makes no version lookup. It does check the name exists first (the same route would otherwise treat an unknown name as a fresh install and create a deployment), so a typo fails with `ErrorCode: not_found` instead of deploying. A name whose deployment was *uninstalled* is caught the same way — the CLI checks the deployment search, which an external app can read only on servers that serve the Pipelines search — so from CI/CD on an older server address such a deployment by key, which reads its status. Find the key, the name and the package with `uip solution deploy list`.

**`Operation` tells you what actually happened.** The endpoint is unified, so asking for the version already deployed is a *configuration change*, not a version move. `Operation: "VersionChange"` means the version moved; `"ConfigurationChange"` means it did not. Check it rather than assuming `DeploymentSucceeded` implies a new version. `DeploymentStatus` says whether the new version runs: `SuccessfulActivate` means it does; `SuccessfulInstall` with `SetupActivation` in `Actions` means it is installed but the previous version keeps running until activation is set up (`uip solution deploy activate`, or Setup activation in Orchestrator).

**A rejected attempt leaves a pending draft.** When a `deploy run` or `deploy upgrade` stops at `ValidationFailed` (or a conflict or scheduling error), nothing is installed and the live version keeps running, but the attempt stays behind as a *draft* — its key is the `deploymentKey` in the failure's `Instructions`. While the draft exists it owns the deployment, as in the Orchestrator UI (which offers only "continue editing" and "delete draft"): re-running the same `deploy run` with a corrected `--config-file` and the **draft's** version re-validates it with the new file (settings and resource links the file does not name keep the rejected values). Any other version is refused before anything is sent (`ErrorCode: invalid_argument`) — including the version that is live now, which the server would otherwise answer by installing the draft's version instead. Under an external app that check only warns and the deploy goes ahead — and the server then runs the draft, installing the draft's version — so from CI/CD ask only for the draft's version, or discard the draft first. `deploy upgrade` sends no configuration, so it refuses a deployment with a pending draft (`ErrorCode: invalid_argument`, naming the draft's key and version) rather than re-run the rejected attempt; once the cause is fixed, `uip solution deploy upgrade <draft-or-deployment-key> --discard-draft` deletes the draft and upgrades the live version with its own configuration, and reports the deleted key as `DiscardedDraftKey`. Address the deployment by key for this from CI/CD — on an older server the name form can only find the draft with a user session. A draft still being validated cannot be discarded yet (`Retry: RetryLater`). A Setup activation started in Orchestrator and left unfinished is a draft too, of the live version: both commands refuse while it exists and name it as such — finish it in Orchestrator, or discard it the same way. A deployment whose *first* install never completed has nothing to upgrade: fix and re-run its `deploy run`, or delete the draft in Orchestrator.

**One deployment per package.** `deploy run` always creates a *new* deployment in a *new* Orchestrator folder — it never updates an existing one, and it cannot deploy into a folder that already exists (Orchestrator renames the folder instead, `MySolution` -> `MySolution 1`). So if the package is already deployed, the command stops and lists the existing deployments rather than quietly adding another folder. That check is best-effort, not a guarantee: a failed lookup only logs a warning, and a CI job signed in with an application (client-credentials) account is never stopped by it — an existing deployment is reported as a warning and the deploy goes ahead (on servers without the Pipelines deployment search the check is skipped, with a warning). In automation, track what you have already deployed instead of relying on the stop. To ship a new version, upgrade the existing deployment in place with `uip solution deploy upgrade <deployment-key>`; to start over, `deploy uninstall`, then `deploy delete` to clear the record it leaves in `deploy list` (that record does not block a redeploy — `blocksRedeploy` lets an uninstalled deployment through — so the delete is housekeeping, not a prerequisite). Pass `--yes` only when you really do want a second, independent copy, and give it a different `--name`: the install is keyed on the deployment name, so re-using an existing one updates that deployment in place instead. While you are still iterating, validate locally (`solution pack --dry-run`) instead of deploying each attempt.

**Activation lifecycle.** `deploy run` activates by default. To split the steps:

```bash
uip solution deploy run --skip-activate ...                      # leaves "Inactive (Ready to activate)"
uip solution deploy activate <deployment-name>     # activate later
uip solution deploy uninstall <deployment-name> --yes   # remove the deployment + its resources (--yes required; the CLI never prompts)
uip solution deploy delete <deployment-name> --yes      # remove what uninstall leaves behind (--yes required)
```

`deploy run` reports `ActivationStatus: SuccessfulActivate` when the deployment runs. When the install landed but a resource needs "Setup activation" in Orchestrator first, it is still `Result: Success`, with `ActivationStatus: NeedsSetupToActivate`, `PendingResources` and `NextSteps` — the deployment exists, so do **not** run the deploy again; complete the setup, then `deploy activate`. `ReadyToActivate` in the same place means the install landed and the command could not activate it: run `deploy activate`.

`uninstall`, `delete`, `activate` and `status` take the deployment **name** as a positional argument (no `--name` flag). `status` also accepts a **deployment key** (from `deploy list` or `deploy upgrade` — the form that diagnoses a stale key) or the **pipeline deployment ID** from `deploy run` (that run's progress and errors, `Code: SolutionDeployStatus`); by name or key it answers `Code: SolutionDeployment` and reports the record's `Operation`, `OperationStatus`, `ActivationStatus`, `Actions`, and `NextSteps` when it is not live. A name is found across feeds; a key outside the tenant feed needs `--personal-workspace` or `--feed <name-or-key>`, as with `deploy list`. `Superseded: null` means the CLI could not tell — the chain search failed or holds no row for the key — and the fields are the requested record's own; take the current key from `deploy list`.

**Two status axes.** `OperationStatus: Successful` means the last operation's content landed. `ActivationStatus: Active` means the deployment runs. An upgrade can land `Successful` *and* `NeedsSetupToActivate`: the new version is installed but does not run until "Setup activation" is completed in Orchestrator (Tenant > Solutions > Deployments); the previous version keeps running meanwhile. The UI words the same states differently: `NeedsSetupToActivate` shows as **Inactive (Needs setup)**, `Operation: VersionChange` as **Change version**, `Operation: ActivationSetup` as **Activation setup** — and the UI lists every record of a deployment, where `deploy list` shows only the newest. `deploy upgrade` reports both axes; when not `Active` it adds `PendingResources` (the resources the service flags as needing configuration — Integration Service connections, typically — each with the `Reason` the activation validation gives, such as a connection that needs authenticating) and `NextSteps`. "Setup activation" has no CLI command **on an existing deployment**: `deploy config link` maps a resource to an existing one only in the config file a new `deploy run` consumes, `deploy upgrade` takes no config file, and the `resource`/`resources` verbs edit the solution project, not a deployment. `deploy activate` is refused (`4007 … cannot be activated`) until the setup is done in Orchestrator.

**A key is one record, not the deployment.** Every operation creates a new deployment record with its own key: `deploy run` the Install record, `deploy upgrade` a VersionChange one (`DeploymentKey` in its output; `InstallDeploymentKey` is the one that never changes). `deploy list` shows the newest per deployment. A key from before an upgrade is *superseded*: the Solutions record still answers as it was — old version, `Active`, `Upgrade` offered — but `deploy upgrade <key>` resolves it to the deployment's current generation through the Pipelines lookup and upgrades that, and `deploy status <key>` reports `Superseded: true` with `CurrentDeploymentKey`. Store `InstallDeploymentKey`, or take the current key from `deploy list`.

**`uninstall` and `delete` are never both available.** The service offers one action per state, and `deploy list` tells you which:

| Deployment state | `Actions` | What removes it |
|---|---|---|
| Installed | `SetupActivation, Uninstall, Upgrade` | `deploy uninstall` |
| Uninstalled | `Delete` | `deploy delete` |
| Never installed (`Draft`, e.g. a failed install) | `Install, Delete` | `deploy delete` |

So a full clean-up of a live deployment is two commands: `uninstall` removes its resources and folder, `delete` then removes the deployment itself. `delete` reads the action list first, and when the record lists actions but not `Delete` it says so and names the command to run instead — it never sends a request the state forbids. A record that lists **no** actions is the exception: nothing is known about it, so the request goes out and the server answers.

`uninstall` waits out an operation that blocks it: when Orchestrator refuses because the deployment still has something running, the CLI polls until that finishes and then sends the request again, all inside `--timeout` (which covers the whole command, the status poll included). If it is still busy when the timeout expires you get exit `2` with `ErrorCode: timeout` and `Retry: RetryLater` — retry later, do not treat it as permanent. A refusal for any other reason (superseded, inactive, unknown name) still fails immediately with exit `1`.

`uninstall` and `activate` do not need a feed flag: without one they find the deployment themselves — tenant feed first, then your Personal Workspace, then the folder feeds you can reach — and scope their requests to whatever feed holds it. So the `deploy activate <name>` that `--skip-activate` points you at works the same on a `--personal-workspace` or `--feed` deployment as on a tenant one. The cost is a lookup per feed until the name is found, and a name that exists in no feed you can see is reported as not found rather than as a blocked uninstall. When you know the feed, pass it: `uninstall`, `activate` and `delete` take `--personal-workspace` or `--feed <name-or-key>` and then search that feed alone. The commands the CLI prints as next steps already carry the flag for the feed the deployment was found in. With either flag, an external-app (client-credentials) login is refused for any feed but the tenant's, because the server ignores the feed header for it.

`deploy delete` and `deploy status <name>` (without a feed flag) find a name the same way. All four say "not found" only when every feed answered — with one exception: under an external-app login, `deploy status <guid>` for a GUID that is no deployment key still says "not found" when only the feeds after the tenant could not be searched, or when the tenant search refused the login (401/403), because an app login cannot read those feeds at all. When a feed cannot be searched — the feed service is down or refuses the session, the list of feeds cannot be read or gives a feed no key, or the tenant search itself fails — and no other feed has the name, they fail with a message that names the feeds they could not search instead of calling the name unknown. `ErrorCode` then comes from that failure (`server_error`, `network_error`, `authentication_required`, `permission_denied`, …, or `unknown_error` when it has no known class) and is never `not_found`; `Retry` follows it — `RetryLater` for an outage, `RetryWillNotFix` for a 401 or 403, and also `RetryWillNotFix` when every feed that could not be searched is one the list gives no key, since a retry gets the same list. Do not treat the name as wrong: do what `Instructions` say (log in again, fix the session's access, or retry later). To check one feed yourself, pass `--personal-workspace` or `--feed <name-or-key>` to `deploy status` or `deploy list`, or to the `activate`, `uninstall` or `delete` you meant to run — but `--feed` is resolved through the same list of feeds, so when that list is what failed only `--personal-workspace` helps, and `--feed` cannot pick a feed the list gives no key. When the tenant feed refuses an `activate` or `uninstall` for its own reason (401, 403, 409, 422, 429, a 5xx), that failure is reported as it is.

## Dependency Feeds

Packing an RPA project restores its NuGet dependencies first, so `pack` and `restore` both need to know which feeds to resolve against. So does `cleanup`: deciding that a dependency is *unused* means resolving the dependency graph, so it reads the same feeds. All three take the same three options.

```bash
uip solution pack . ./out --feed-folder Shared/Production        # resolve from one folder's library feed
uip solution pack . ./out --nuget-sources-config-path ./NuGet.config
uip solution pack . ./out --exclude-configured-sources           # resolve from nothing else
```

By default dependencies resolve against every tenant feed the session can see, plus the feeds the WorkflowCompiler adds on its own: nuget.org, UiPath-Official, Connect (`gallery.uipath.com`) and the UiPath internal feed.

- `--feed-folder <name>` narrows the Orchestrator side to a single folder's library feed — a folder name or a fully qualified path. It fails closed: naming a folder with no authenticated session is an error, not a silent fall back to other sources.
- `--nuget-sources-config-path <path>` points at your own `NuGet.config`. Its sources are added to the ones above.
- `--exclude-configured-sources` drops the WorkflowCompiler's built-in feeds, so resolution uses only the tenant feeds (or `--feed-folder`) and `--nuget-sources-config-path`. Use it when a build must resolve from an approved set only.

That last flag is strict on purpose, and that is what makes it easy to get wrong: with the built-ins gone, the official activity packages (`UiPath.System.Activities`, `UiPath.UIAutomation.Activities`, …) have to be reachable on the feeds you named. Most tenant library feeds do not mirror UiPath-Official, so on a typical solution a bare `--exclude-configured-sources` fails the restore. Pair it with a `NuGet.config` pointing at your own mirror.

## Package Signing

`solution pack` can sign each packed project `.nupkg` with a code-signing certificate. Signing is opt-in: add `--signing-certificate-path <cert.pfx>` to the pack command. The certificate password (`--signing-certificate-password`) is optional — passing it as `env.VAR` (e.g. `env.SIGNING_PASSWORD`) is recommended, though an inline value also works. An optional timestamp server is set with `--signing-timestamp-server <url>`.

## Workflow Analyzer and Governance

`solution pack` runs the workflow analyzer over every RPA project. These flags control it:

```bash
uip solution pack . ./out --skip-analyze                             # don't run the analyzer at all
uip solution pack . ./out --ignored-rules ST-USG-034,ST-MRD-002      # run it, but drop these rules' findings
uip solution pack . ./out --governance-file-path ./policy.json       # analyze against a local policy file
uip solution pack . ./out --governance-product StudioWeb             # analyze against the tenant policy
```

`--skip-analyze` turns off only the analyzer rules — the compiler still restores, compiles, and validates, so a broken project still fails the pack.

`--ignored-rules` keeps the analyzer on but drops the findings of the rules it names, for every RPA project in the solution: they are not reported and cannot fail the pack. It is the per-run escape hatch the legacy `uipcli --ignoredRules` was — use it for violations a pipeline has deliberately accepted, rather than editing a policy other people share. The value is a comma-separated list of rule IDs; repeat the flag to add more; IDs are trimmed and matched case-insensitively. Which rules it can lift depends on where the rules come from:

- **The signed-in tenant publishes an AutomationOps policy.** The list is not applied, even with a `--governance-file-path`: the organisation's policy stays enforced in full, and a warning names the rules that were not ignored. The pack does not fail because of the flag.
- **A `--governance-file-path` is used** (the tenant publishes nothing, could not be asked, or there is no signed-in tenant). The list applies on top of the file, even to rules the file raises to `Error`.
- **No policy at all.** The list applies on top of the rules shipped with the WorkflowCompiler.

A failed pack says which project broke and where. Alongside `Message`, the envelope carries `Data.Projects` — one entry per member project with `Path` (its directory relative to the solution, `.` at the root), `Type`, `Result`, `Message` and `Findings`; each finding carries `Source` (`Analyzer`, `Validator`, `Compiler`, `Other`), `ErrorCode`, `Description`, `FilePath` and `ActivityIdRef` where the compiler reported one. Read `Data.Projects` rather than parsing `Message` — the message flattens every failed project into one sentence and names no file. A failure that belongs to no project at all (not logged in, no packager for a `Type`) has no `Data.Projects`.

The analyzer rule configuration comes from whichever governance flag you use. `--governance-file-path` reads a local policy file — pass an AutomationOps policy **exactly as exported**, envelope and all: the analyzer reads the whole export, so handing it just the inner `data` object is rejected with a message telling you to pass the export instead. A file that cannot be read, or that is not JSON, fails the pack rather than falling back — you asked for a policy, so packing without one would be a silent pass. `--governance-product` downloads the policy published in AutomationOps for the signed-in tenant; its value is the product to fetch (`StudioWeb`, `Development`, `Business`, …). With neither flag the analyzer uses the rules shipped with the WorkflowCompiler. Pass `--governance-file-path` or `--ignored-rules` without `--governance-product` and the tenant is still asked, about `StudioWeb`, so a governed tenant's policy can win over them — those are the only cases with a product default.

`--automation-ops-profile` is the old name for `--governance-product`. It still works and still parses, but it is hidden from help and warns; passing both is rejected rather than resolved. Use `--governance-product` in anything new.

Whenever you are signed in as a user, the tenant is asked first — including when you pass `--governance-file-path`. There are three possible answers and each does something different:

- **The tenant publishes a policy.** That policy is what the analyzer uses, whatever else you passed. A `--governance-file-path` alongside it is not used, and `--ignored-rules` is not applied; each gets a warning and the pack carries on — a flag in your own pipeline does not lift the organisation's policy.
- **The tenant publishes nothing.** The analyzer uses your `--governance-file-path` if you passed one, otherwise the rules shipped with the WorkflowCompiler.
- **The question could not be answered** (expired token, no route, the service is down). The pack still succeeds and nothing fails: you get a warning naming the reason (`unauthorized`, `notFound`, `serverError`, `timedOut`, …), shown only at `--log-level warn` or lower (see below), and the analyzer uses your `--governance-file-path` if you passed one, otherwise the shipped rules. Not knowing whether you are governed is not a reason to break a build.

With no signed-in tenant there is nothing to ask, so a `--governance-file-path` is simply used and an offline pack keeps working.

When you are signed in as an external application, the tenant is not asked: AutomationOps does not accept external-application tokens yet. The pack behaves as when the question could not be answered — your `--governance-file-path` if you passed one, otherwise the shipped rules — and the warning names the reason `applicationLogin`.

Note what this means for CI: a pack that could not reach AutomationOps still returns `Result: Success` and exit `0`, so a stage using `--governance-product` as a governance gate goes green while having enforced the shipped defaults. The warning in the log is what tells you which happened — `uip solution pack` reports on governance, it does not enforce it. That warning is a `warn`-level log line, and the default `--log-level` is `error`, which hides it. A stage that needs to know passes `--log-level warn` and reads stderr. To read it from a file instead, pass `--log-file <path>` together with `--log-level warn`: the level filter runs before a line is sent to the file, so `--log-file` alone still drops the warning. Strict, fail-closed behaviour belongs to design-time hosts, not to this command.

## Dependency Feeds

Packing an RPA project restores its NuGet dependencies first, so `pack` and `restore` both need to know which feeds to resolve against. So does `cleanup`: deciding that a dependency is *unused* means resolving the dependency graph, so it reads the same feeds.

```bash
uip solution pack . ./out --feed-folder Shared/Production      # resolve from one folder's library feed
uip solution pack . ./out --nuget-sources-config-path ./NuGet.config
```

By default dependencies resolve against every tenant feed the session can see.

- `--feed-folder <name>` narrows that to a single Orchestrator folder's library feed — a folder name or a fully qualified path. Accepted by `pack`, `restore` and `cleanup`. It fails closed: naming a folder with no authenticated session is an error, not a silent fall back to other sources.
- `--nuget-sources-config-path <path>` points at your own `NuGet.config`. Accepted by `pack` and `restore` only — `cleanup` does not take it, so a solution that packs against custom sources may clean up against different ones.

`pack` also takes `-n, --name <name>` to override the package name (it defaults to the solution folder or `.uis` file name) and `-v, --version <version>` (defaults to `1.0.0`).

`--name` names the **solution archive only**. Each member project keeps its own NuGet id, anchored on the solution's `.uipx` name, so packing one solution twice under two names produces two archives holding members with the same ids — which is what lets an upgrade land on the same feed entries. Renaming the solution *directory* does not move member ids either; the `.uipx` travels with a checkout.

`--author` and `--description` apply to every member that declares neither. A project that declares its own `Description` / `Author` in its project file keeps them, so per-project provenance survives a solution pack; only when nothing declares either do the `UiPath` / `Created by UiPath` defaults apply.

`publish` goes to the tenant feed by default:

```bash
uip solution publish ./out/<package>.zip --personal-workspace   # publish to your Personal Workspace instead
uip solution publish ./out/<package>.zip --wait                 # block until the package is Ready or Active
```

`publish` also accepts `--package-name` / `--package-version`, but those rewrite `solutionMetadata.json` inside the `.zip`, so they only work on a package produced by `uip solution pack`. Prefer packing with the name and version you want.

Published packages live on the tenant feed:

```bash
uip solution packages list --limit 100                              # what's published
uip solution packages download <package-name> [package-version]     # pull a .zip back (latest if version omitted; -d for the destination)
uip solution packages delete <package-name> <package-version> --yes # remove a version (--yes required)
```

## Solution Cleanup

`uip solution cleanup` removes unused items from every project in the solution. For a solution directory it **modifies the project sources in place**, so check what it would do first:

```bash
uip solution cleanup . --dry-run     # only detect unused items, change nothing
uip solution cleanup .               # apply
uip solution cleanup . --skip-imports  # apply, but leave now-unused references in project files alone
```

There is **no confirmation prompt and no `--yes` flag** — unlike `deploy uninstall` and `packages delete`, which both refuse to run without `--yes`. The bare command mutates the working tree, so run `--dry-run` first and have the tree committed.

Cleanup decides what is unused by resolving dependencies, and it always consults whatever NuGet sources the user and machine config already define — there is no flag to turn that off. A source configured outside the solution can therefore influence what gets deleted from the project tree.

## Studio Web (Browser Editing)

Studio Web is a separate target from the Orchestrator deploy chain — it hosts a browser-based collaborative editor for solutions. The `solution upload` command pushes the local solution there and returns a `DesignerUrl` to open the solution in a browser; this is independent of `pack` / `publish` / `deploy` and does *not* produce a runtime-deployable artifact.

```bash
uip solution upload .                      # push solution dir to Studio Web; imports it or updates it in place; returns DesignerUrl
uip solution upload . --no-snapshot        # same, but skip recording a restorable pre-overwrite version
uip solution download <solution-id>                      # round-trip a Studio Web solution back to disk as ./<solution-id>.uis
uip solution download <solution-id> -d ./out --extract   # same, plus unzip it into ./out/<solution-id>/
uip solution download <solution-id> -n my-solution       # name the output my-solution.uis (and my-solution/ with --extract)
uip solution delete <solution-id> --yes    # remove a solution from Studio Web (--yes required; the CLI never prompts)
```

`upload` accepts a solution directory, a `.uipx` file, or a `.uis` file. It checks Studio Web for the bundled `SolutionId` and picks the operation itself, so the same command works for the first upload and every one after it:

- **cloud has no solution with that id** — imported as new. Studio Web assigns its own `SolutionId` (it never honors the one in the archive), and the CLI writes that id into the local `.uipx`. That link is what makes your next upload an update instead of a second solution, and it is reported under `Data.LocalSolutionIdUpdated`.
- **cloud already has it** — contents replaced in place under the same id. Existing Studio Web version history is **kept**, and the contents being replaced are first recorded as a restorable version. Pass `--no-snapshot` to skip that recording in a tight iteration loop — then anything changed in Studio Web since your last upload is lost (the local solution files are never affected).

`Data.Action` is `Imported` or `Overwritten`, so you can tell which ran. `--force` skips the existence check and overwrites directly; it is not normally needed, it fails rather than importing if that solution is gone, and it has no effect when no `SolutionId` is bundled (the upload imports as new). To upload a copy as an unrelated cloud solution instead of updating, scaffold a fresh solution with `uip solution init`, or replace the `SolutionId` in the local `.uipx` with a fresh GUID and re-run upload (removing the field entirely fails `.uipx` validation).

The bundle `upload` sends leaves out `.venv`, `node_modules`, `__pycache__`, `.git`, `.local` and `.flow-sdk` folders and `.env` / `.env.*` files on its own. To leave more out, add a `.uipignore` file at the solution root (or inside a project, where its patterns apply to that project only) using `.gitignore` syntax — `dist/`, `*.log`, `!keep.log`, `MyAgent/generated/`; a line-leading `#` is a comment. A pattern that would drop a project the `.uipx` lists is refused — remove the project with `uip solution projects remove` instead. `uip codedapp push` honors the same file (its older `.uipathignore` is deprecated — use `.uipignore`). `solution pack` does not read it.

If Studio Web refuses the upload with 401 or 403, do **not** re-run `uip login` — the CLI checks the session and its token expiry before it calls, so the token was valid and re-authenticating produces the same one. The failure is about what the acting identity may do in Studio Web (for a CI pipeline: the external application's `StudioWebS2S` grants) or about the tenant the bundled `SolutionId` belongs to. The envelope's `Instructions` name both, and an application 401 is reported as `ErrorCode: permission_denied` rather than `authentication_required`.

`download` writes the `.uis` archive and nothing else — extraction is opt-in. Pass `--extract` to also unzip it into a sibling directory named after the archive; that directory is a working solution tree, with the `.uipx` manifest at its root. `--extract` also drops `AGENTS.md` and `CLAUDE.md` there so an agent picking the solution up has the same briefing `uip solution init` writes. It only fills gaps: a file the archive already carried is left alone, and the paths actually written come back in `Data.BriefingFiles`. Without `--extract` you get the zip only, and no briefing files — there is no solution directory to put them in.

Two more verbs act on a **cloud** solution project rather than the local tree — do not confuse them with the local `projects add` / `import` / `remove` / `list` membership commands above:

```bash
# Publish a cloud solution project straight to a solution package (no local pack)
uip solution projects publish \
    --project-name <cloud-project-name> \
    --package-name <package-name> \
    --package-version <version>

# Sync a cloud solution project, or reset it
uip solution projects resync <cloud-project-name>
uip solution projects resync <cloud-project-name> --sync-option Reset
```

`projects publish` requires all three of `--project-name`, `--package-name` and `--package-version`, and optionally takes `--folder-name`, `--description` and `--release-notes`. `projects resync` accepts the project name positionally or as `--project-name`, and `--sync-option` is `Sync` (default) or `Reset`. Both wait for the operation to finish.

## Per-Project Bindings (`bindings_v2.json`)

Each project declares the resources it needs (assets, queues, buckets, processes, …) in a `bindings_v2.json` file at the project root. These declarations drive the solution's resource inventory.

`projects add` and `projects import` do not always create the project's resources. Some project types (a coded app, for example) pick their resource template from a file only their own tool can read, so these commands register the project and stop. They report `Data.ResourcesPending: true` and warn when that happens, naming the tool to install (`uip tools install codedapp` for a coded app) — the resources arrive at the next `resources refresh`, `pack` or `upload`.

After editing a project's bindings, or after `solution projects import` (which doesn't auto-sync resources), reconcile the solution-level inventory:

```bash
uip solution resources refresh     # re-scan every project, sync new / removed resources
```

`solution resources refresh` creates new resources for bindings not yet in the solution and imports from Orchestrator when a matching resource already exists.

It also generates or regenerates each project's own resources (its `package` and `process`, for example) — on the first run, and again after a project rename or type change. The output counts these apart from the binding counts: `Data.Created`, `Data.Imported` and `Data.Skipped` count bindings only, and `Data.ProjectResourcesCreated` counts the project resources this run generated or regenerated; resources the regeneration removes are not counted. A rerun with nothing new reports `0`. `Status` names this count too (`, N project resources generated`) when it is above `0`.

**Refresh is import-only for cloud resources. It never overwrites an imported resource** — that is what keeps your local edits (a renamed resource, a patched retry count) from being wiped on every re-scan. So if you change an entity, queue or asset **in the cloud** after importing it, `refresh` will not pick the change up: it reports the resource under `Skipped` and leaves it alone. To pull the new cloud definition, use `resources edit --source remote` (below).

**A failed Resource Catalog call is not a "not found".** `resources refresh`, `pack`, `upload`, `projects add` and `projects import` look each binding up in the Resource Catalog. When that lookup fails — the catalog refuses the login with 401/403, it is unreachable, or (for `pack`, which runs without a login) there is no login — nothing is created for the binding, because a local stub would deploy as a new, empty resource instead of the one in the cloud. The same goes for a resource the catalog found but whose import was refused. A binding the solution already holds keeps that resource as it is. Refresh reports what it could not check in `Data.Warnings` and exits `0`; `projects add` / `import` log it as a warning. `pack` and `upload` fail when a binding the solution does **not** hold could not be resolved: `ErrorCode: permission_denied` for a refused login (`Retry: RetryWillNotFix`), `server_error` or `rate_limited` (`Retry: RetryLater`) when the catalog is down or throttling, and — `pack` only — `authentication_required` with no login. `resources refresh` and `upload` check the login before they start, so with no login they fail on that check instead, as before. After no login or a 401/403 the rest of the bindings are not looked up. From CI/CD, run `uip solution resources refresh` under a login the catalog accepts (a user login), commit the solution's resources, and the pipeline's `pack` then uses them as they are. An import that fails for any other reason still falls back to a local resource, and says so in the warnings.

Each project's own tool also reports what its authored files add to the solution
resources — for a Coded Action app, its `action-schema.json` lands on the app
resource's `spec.actionSchema`. Two things follow:

- `uip solution resources refresh` reports `Data.ReconciledSpecs` — how many
  resource specs it rewrote from the projects' authored files. Problems that
  `pack` would fail on show up in `Data.Warnings` here; refresh still exits `0`.
- `uip solution pack` and `uip solution upload` both fail when a project
  reports a problem with its own authored files — a coded app whose
  `webAppManifest.json` does not parse, or a Coded Action project whose
  `action-schema.json` is missing or does not parse, for example. The message
  names the file and the project, and the envelope carries
  `ErrorCode: invalid_argument`.
  Nothing is written before that check passes, so fix the file and re-run the command.

For project types whose resources do not depend on a tool contribution, refresh
does not warn when the installed tool has nothing to contribute. Use
`--log-level debug` to see that diagnostic. An `AppV2` coded app does require its
tool's contribution: if it is missing, refresh warns and pack/upload fail with
`contribution_unavailable`. Run `uip tools install codedapp`, then try again.

An `action-schema.json` edited without a following `refresh` or `pack` still
shows the previous schema in `uip solution resources get`; the next pack or
refresh rewrites it, so the packed solution is never stale.

`uip codedapp init <path> --type Action` writes a valid starter
`action-schema.json`, so a freshly scaffolded Coded Action packs without being
edited first. It is never overwritten on a re-run — your own schema is the one
that matters.

### A coded app's build output

A coded app's packed payload is a **folder that is already built**: nothing in
`uip solution pack` runs the app's build, so a CI pipeline has to run its
`npm run build` (or equivalent) first. Which folder gets packed is
`config.bundlePath` in the app's `webAppManifest.json`, relative to the project
directory — `source/dist` for an app `uip codedapp init` scaffolded inside a
solution, `dist` for a standalone one.

Pack **fails** when that folder holds no HTML entry point (`index.html`,
`main.html` or `app.html`, unless `config.mainFile` selects another HTML file),
naming the path and both ways out. That used to
succeed and ship an app that could not start, so if you see this failure the
answer is to build the app or repoint `config.bundlePath` — not to retry.

Coded app entry points declared in `config.mainFile` must be HTML files inside
the bundle; absolute paths and parent segments are refused by the shared packager.
When adopting an app with `codedapp init --force`, `config.bundlePath` must name
a child build folder, never the project root or a parent. Standalone
`codedapp pack <dist>` uses that selected folder for preview and packaging,
and preserves the project identity written by the packager. Its bundle and entry
selection stays in memory and in the package. Only a missing project ID is
persisted to the project manifest. `config.mainFile`, when present, must be a string.
When a coded app has an authored `entry-points.json`, pack updates its primary
entry's `filePath` in the archive to match the selected HTML file, preserving
the other metadata and leaving the project file unchanged.
Child bundle paths are checked after aliases resolve during adoption and again
at pack time. They cannot point to the project root or outside it. An explicitly
selected external positional folder in `codedapp pack` remains supported.

### Bringing an app you already have into a solution

To register a web app that already exists — one with its own sources and build
at the project root, not the `source/` layout `init` writes — run
`uip codedapp init <path> --force` on it. With an app already there (an
`index.html`, or a `package.json` declaring a build script), init **adopts** it
instead of writing a starter: it writes only `project.uiproj` and
`webAppManifest.json`, leaves every other file alone, and sets
`config.bundlePath` to the app's own build output. The result's
`Data.AdoptedApp` reports the path it chose and where it came from —
`build-output` (a folder it found), `existing-manifest` (a value already
declared, which wins) or `default` (nothing is built yet, so the value is a
guess and `NextSteps` says so — check it before you pack; for an app with no
build script it also says the folder will not appear on its own, so set
`config.bundlePath` yourself).

One exception to a declared value winning: if an earlier `init --force` on
an older CLI wrote a starter into `source/` over your app and pointed
`config.bundlePath` at it, that value is ignored and the probe runs instead,
with `NextSteps` saying so. It is recognised by the starter page's own
markup, so an app that genuinely builds into `source/dist` — or one where
you have since built over the starter — keeps its declared path. Without it the solution would keep packing
`Result: Success` while shipping the starter, because the starter has an
`index.html` of its own. Delete the leftover `source/` once a pack looks
right.

Re-running `init` over a project that already has a `webAppManifest.json`
merges into it rather than rewriting it: `config.bundlePath` is applied and
everything else — including the `projectId` a pack writes to keep the
packaged app's identity stable — is carried through. Omitting `--type` on a
re-run means "leave the variant alone": an existing Coded Action stays one,
schema and artefact subtype included. Passing `--type Action` over a plain
coded app still upgrades it.

### Adding a resource by hand

A resource is either **virtual** — declared locally now, provisioned when the solution deploys — or **imported**, pointing at something that already exists in Orchestrator. `--source` picks which:

```bash
uip solution resources add --source local  --kind Queue   --name InvoiceQueue
uip solution resources add --source local  --kind Asset   --type Credential --name ApiLogin
uip solution resources add --source remote --kind Process --name Existing --folder-path Shared
```

`--type` picks the subtype for kinds that have one. For assets it takes the Orchestrator name (`Text`, `Integer`, `Bool`, `Credential`, `Secret`) or the solution name (`stringAsset`, `integerAsset`, `booleanAsset`, `credentialAsset`, `secretAsset`), case-insensitive. A subtype the kind does not have fails with `ErrorCode: invalid_argument`, and `Instructions` lists the valid ones. A kind with no subtypes (a queue) refuses `--type`; a connection's connector type passes through. An empty `--type ""` is refused for every kind; leave the option out instead. With `--source local`, adding a name that already exists with a different `--type` fails instead of returning the existing one. With `--source remote`, `--type` must match the resource's own type: it narrows same-name matches and never changes what gets imported.

`--name` is checked before anything is written, because a local resource becomes a file under `resources/solution_folder/<kind>/<name>.json`: a blank or whitespace-only name, a name over 256 characters, or one containing path separators, control characters or any of `: * ? " < > |` fails with `Result: Failure` and a `Message` that names the option (`--name must not be blank`, `--name contains unsafe characters`). `uip agent memory add` runs the same check on `--memory-space` when it declares a memory space in the solution.

**Not every kind can be virtual.** Queues, assets and buckets can — the solution creates them on deploy. Kinds that must already exist somewhere (processes, connections, apps, indexes, entities) cannot be conjured from a local declaration; they need `--source remote`, or a `deploy config link` onto an existing resource at deploy time.

`--source local` does **not** enforce that. It succeeds for any kind, prints `Result: Success`, and writes a stub — the check that would catch it is not on this code path. The failure surfaces later, at deploy. Two ways to catch it early:

- `uip solution resources refresh` does check, and warns per resource: `Link it before deploy: uip solution deploy config link <file> "<name>" --name <existing-name>`. If you see that warning, the resource cannot be virtual.
- `uip solution resources list --source remote --kind <kind>` — if the kind is one Orchestrator owns, confirm the target is really there before declaring it locally.

`--folder-path` is rejected with `--source local`: a virtual always lands in `solution_folder`.

Inspect the current solution inventory:

```bash
uip solution resources list        # everything declared in this solution
uip solution resources list --source remote --kind app --include-version
                                   # classic Apps in Orchestrator, with the version deployed per folder
uip solution resources list --search <term>    # filter by name
uip solution resources list --limit 20 --next-page <cursor>   # the 20 rows after the previous page
```

A listing returns at most 50 rows unless you pass `--limit`. Check `Pagination.HasMore` before treating the rows as complete. The resource catalog pages by cursor, so `--offset` accepts only `0`: to get the next page, pass the previous response's `Pagination.NextPage` to `--next-page` with the same filters. If the catalog call fails, the command fails; use `--source local` to list only the solution's own resources.

`--include-version` reads the live `version` of the kinds that carry one (`app`,
`appVersion`, `package`, `process`). It costs one extra call per resource, so it
is off by default.

Every command below takes the resource **key** from `resources list`. `--solution-folder <path>` overrides the solution root (defaults to the current directory) on all of them.

```bash
# Read one resource's full spec, locks and metadata
uip solution resources get <resource-key>
uip solution resources get <resource-key> --include-dependencies

# Patch spec properties — the JSON is merged into the existing spec
uip solution resources edit <resource-key> --patch '{"retentionPeriod":14}'
uip solution resources edit <resource-key> --patch -          # read the JSON from stdin

# Pull the cloud definition over the local one (imported resources only)
uip solution resources edit <resource-key> --source remote           # report what would change, write nothing
uip solution resources edit <resource-key> --source remote --force   # apply it

# Drop a resource from the solution (local only, leaves bindings_v2.json alone)
uip solution resources remove <resource-key>
```

### Picking up a cloud change: `edit --source remote`

Use this when the resource changed **in Orchestrator or Data Fabric** after you imported it — a new field on an entity, a changed queue setting — and `refresh` reported it under `Skipped`.

Without `--force` it writes nothing: it lists the spec properties that differ and exits `1` with `ErrorCode: invalid_argument`. That exit code is deliberate — a script that forgot `--force` must not read "nothing was written" as "done". Re-run with `--force` to apply.

```bash
uip solution resources edit <resource-key> --source remote --output json
# Failure, invalid_argument: "2 properties differ from the cloud definition: description, fields"

uip solution resources edit <resource-key> --source remote --force --output json
# Success, ResourceEdited: Data.Applied true, Data.Changed ["description","fields"]
```

**`--force` is destructive.** It replaces the local spec with the cloud one, so any local edit to a listed property is lost — including a rename you made before deployment. Run it once without `--force` first and read the `Changed` list.

Three things it will not do:

- `--patch` and `--source remote` cannot be combined (two sources for the same spec would race), and `--force` is rejected without `--source remote`.
- A resource with no recorded cloud reference fails with `Resource has no cloud definition to sync from` rather than silently doing nothing. Two causes: it genuinely has no cloud counterpart (a `--source local` stub, or a project's own artefact resource), **or** the reference belongs to someone else. The reference is stored per user and per tenant in `userProfile/<your-user-id>/debug_overwrites.json`, so if a teammate imported the resource — or you imported it against another tenant — you have no reference for it. Re-import it with `uip solution resources add --source remote` to record one for yourself.
- If the cloud definition cannot be read for the comparison, it fails with `Could not read the cloud definition to compare against` instead of reporting no drift. Check the resource still exists in the cloud, or pass `--force` to overwrite with whatever the cloud returns.

`get` and `edit` use the same shape — **copy the casing `get` returns** (`Value`, not `value`). A patch key whose case does not match is treated as unknown.

Both of `edit`'s failure modes are silent and still report `Result: Success`:

- A key the SDK marks as reference, read-only or unknown is ignored rather than rejected.
- A mis-cased key is ignored the same way.

So `Result: Success` from `edit` does not mean the value changed. Read it back with `resources get` before relying on it. No CLI verb sets a *reference* property, so a virtual process cannot be pointed at a package this way — link it at deploy time with `deploy config link` instead.

Keys are GUIDs for imported cloud resources and compound strings such as `MyFunction.api.MyFunction.1:1.0.0` for package resources; pass the `Key` value `uip solution resources list` prints.

## Deployment Configuration

The deploy config is a JSON file fetched from Orchestrator that lists every resource the solution will provision (or reuse) and every property you can override. It is **separate from `bindings_v2.json`** — bindings declare *what a project needs*, the deploy config decides *how that maps to Orchestrator at deploy time*.

```bash
# Fetch the default config to a file
uip solution deploy config get <package-name> --destination config.json

# Set a property on a single resource
uip solution deploy config set config.json <resource-name> <property> <value>
# e.g. set config.json MyQueue maxNumberOfRetries 5

# Set a property on every resource (limited; supports e.g. conflictFixingAction)
uip solution deploy config set config.json --all <property> <value>

# Link a resource slot to an existing Orchestrator resource (instead of creating a new one)
uip solution deploy config link config.json <resource-name> \
    --name <existing-resource-name> \
    --folder-path Shared/Production

# Remove a link — the resource will be created at deploy time again
uip solution deploy config unlink config.json <resource-name>

# Apply the customized config:
uip solution deploy run ... --config-file config.json
```

If a deploy fails on a configuration issue, the CLI prints the offending resource and an `Instructions` field. Read those before retrying — most failures are an `existing-resource-name` typo, a wrong `--folder-path`, or a property that the resource type does not accept.

## Resource Types in Orchestrator

The CLI talks about the same resource types Orchestrator does:

- **Assets** — key-value configuration. Asset value types: `Text`, `Bool`, `Integer`, `Credential`, `Secret`.
- **Queues** & **Queue Items** — work-item queues for distributed transactional processing; queue items are the rows.
- **Storage Buckets** & **Bucket Files** — file storage for automation data.
- **Connections** — Integration Service connections to external systems (Salesforce, ServiceNow, …).
- **Processes / Releases** — published packages bound to a folder.
- **Triggers** & **Webhooks** — event-, time-, or queue-based job firing; outbound HTTP notifications.
- **Entities** — Data Service tables. Add or bind with kind `Entity`.
- **ChoiceSets** — enumerations used by entity fields. Add with kind `ChoiceSet`.

Resources outside a solution are managed under the orchestrator tool, which exposes per-type subgroups (`uip or assets …`, `uip or queues …`, `uip or buckets …`, `uip or bucket-files …`, `uip or libraries …`, `uip or queue-items …`, `uip or triggers …`, `uip or webhooks …`). Run `uip or --help` for the live list. Example:

```bash
uip or assets list          # list assets in the active folder
uip or assets create        # create an asset (see --help)
```

## Output Conventions for Agents

Three rules make automation reliable:

1. **Never redirect or drop stderr.** Errors and confirmations go to stderr — `2>/dev/null` will silently hide failures and produce false retries.
2. **Use `--output-filter <jmespath>`** to extract specific fields rather than piping JSON through external tools. The expression is applied to the `Data` array — start with `[]`, not with `Data[]`. On list commands with a default `--limit`, an explicit `--limit` is required with `--output-filter` (the filter only sees the records fetched). Example: `uip solution packages list --limit 100 --output-filter "[].Name"`.
3. **Match the key casing of the unfiltered output.** Filter keys are case-sensitive and most commands print `Data` keys in PascalCase, so write `[].Name`, not `[].name` — the wrong casing matches nothing and returns `Data: []`. A few commands pass their keys through verbatim (`uip maestro flow registry get` is one, where `Node.inputDefinition.fields` is correct). If you are unsure, run the command once without `--output-filter` and read the keys off the output.

A filter that selects nothing still returns `Result: "Success"` with `Data: []` and exit 0 — that is a valid empty answer, not a failure. Check the `Warning` field and stderr. They say which it was: a field name that does not exist (fix the expression), no record matched or the expression resolved to no value (the answer really is empty), or a name that reads below the top level (`Items[].Name` reads `Name` off an `Items` entry, so only `Items` was checked — an empty `Items` is the usual cause, not a bad name).

Standard success shape: `{ "Result": "Success", "Code": "<CommandCode>", "Data": ... }`.
Standard failure shape: `{ "Result": "Failure", "Message": "<short>", "Instructions": "<actionable>" }`.

List commands always return `Data: []` on empty results — never a message object — so consumers can rely on a consistent array shape.

## Discovering Commands

This file is a starting map, not a reference. The live source of truth is the CLI itself:

```bash
uip --help                       # top-level groups
uip solution --help              # every solution verb
uip solution deploy --help       # the deploy subgroup
uip <command> --help             # full options for any command
```

For concept or API documentation beyond CLI usage, fetch `https://docs.uipath.com/llms.txt` for the product index, then the relevant `.md` page (e.g. `https://docs.uipath.com/orchestrator/automation-cloud/latest/api-guide/assets-requests.md`).

Adjacent groups commonly used alongside solutions:

| Group | Purpose |
|---|---|
| `uip login`, `uip login tenant` | Authenticate, switch tenants |
| `uip or folders` | Manage Orchestrator folders |
| `uip or assets`, `uip or queues`, `uip or buckets`, `uip or bucket-files`, `uip or libraries`, `uip or queue-items`, `uip or triggers`, `uip or webhooks` | Manage Orchestrator resources directly |
| `uip rpa` | RPA workflow lifecycle (compile, validate, execute, scaffold) |
| `uip maestro` | Maestro Flow / Case / BPMN scaffolding |
| `uip agent`, `uip codedagent` | Coded agent lifecycle |
| `uip codedapp` | Coded Apps lifecycle |
| `uip function` | UiPath Functions |
| `uip df` | Data Fabric entities, records and choice sets (the service behind `Entity` projects) |
| `uip tm` | Test Manager (test projects, sets, executions) |
| `uip is` | Integration Service (connectors, connections) |
| `uip tools` | Manage CLI tool extensions |
| `uip skills` | Install the UiPath agent skills referenced above |

## Troubleshooting Quick Map

| Symptom | First thing to check |
|---|---|
| `Not authenticated` / 401 | `uip login`, then re-run |
| `upload` fails with 401/403 and `ErrorCode: permission_denied` | Not a login problem — the token was valid when the call went out, so `uip login` mints the same one. Read `Instructions`: for a session on an external application, check that the app has the Studio Web (`StudioWebS2S`) grants, not only the Orchestrator and Solutions ones; for a user, check Studio Web access in the tenant. Then confirm the `SolutionId` in the `.uipx` belongs to the tenant you are logged into — one from another tenant is refused, not reported missing |
| `packages list` or `deploy list` fails with `ErrorCode: permission_denied` from a CI/CD pipeline | `packages list` reads the Solutions search, which accepts user sessions only, so an external app's client-credentials token is refused (the message says so). `deploy list` reads the deployment search, which accepts an external app on servers that serve `POST /v1/pipelines/deployments/search`; it is refused only on an older server, or with `--personal-workspace` or a folder `--feed`, whose feed the server ignores for an app. `uip login` with the same app mints the same kind of token; run the listing under a user session. The same goes for `--personal-workspace` on any command: an external app has no Personal Workspace. |
| `pack` or `upload` fails with `ErrorCode: permission_denied` (or `pack` with `authentication_required`) and a message naming the Resource Catalog | The catalog refused the login (or there was none), so bindings the solution does not hold yet could not be resolved, and the command will not pack them as empty stubs. Run `uip solution resources refresh` under a user login, commit the solution's resources, then re-run. Bindings already in the solution are fine as they are |
| Command targets the wrong tenant | `uip login tenant set <tenant>`; verify with `uip login status` |
| Pack succeeds but publish 409s | Version conflict — bump the version (`uip solution pack . ./out -v <new-version>`) or delete the colliding version with `uip solution packages delete <package-name> <version> --yes` (only if intentional; `--yes` required) |
| `deploy run` stops because the package is already deployed | Upgrade it in place with `uip solution deploy upgrade <deployment-key>` (running `deploy run` again does not upgrade it), or `uip solution deploy uninstall <name> --yes` then `uip solution deploy delete <name> --yes` first, or pass `--yes` with a different `--name` to create a second, separate deployment (re-using the name updates the existing one in place) |
| `HTTP 400 … cannot be uninstalled` (error `4007`) | The deployment is not uninstallable in its state — superseded, already uninstalled, or left by a failed install. Read `Instructions`: when its `Actions` list offers `Delete`, remove the record with `uip solution deploy delete <name> --yes`. An operation still running is the other cause, and that one clears by itself (`Retry: RetryLater`) |
| `deploy upgrade` reported `Status: DeploymentSucceeded` but the old version still runs | Read `DeploymentStatus` and `ActivationStatus` in the same output. `SuccessfulInstall` / `NeedsSetupToActivate` means the new version is installed and waits for "Setup activation" in Orchestrator; `PendingResources` names what needs configuring and why (`Reason`, from the activation validation, e.g. `[CNS1072] You will need to authenticate this connection before proceeding further`) and `NextSteps` the step. `ReadyToActivate` means `uip solution deploy activate <name>` is all that is left. Do not run the upgrade again — the content is already there |
| `Another upgrade has already started for this deployment` (error `4005`) | The key you passed is superseded by a later record; nothing is running. The CLI names the current record — use that key (`uip solution deploy list` shows it). If the current record is already at the version you want, there is nothing to upgrade |
| `deploy run` succeeded with `ActivationStatus: NeedsSetupToActivate` and the deployment does not run | Expected: the install landed, and a resource needs "Setup activation" in Orchestrator before activation. `PendingResources` names what needs configuring and why (`Reason`, from the activation validation, e.g. `[CNS1072] You will need to authenticate this connection before proceeding further`) and `NextSteps` the step. `Status` may read `ValidationFailed` there: that is the pipeline's word for the activation validation it ran after the install, and `NextSteps` open with its errors. Do not deploy again (the deployment exists); complete the setup, then `uip solution deploy activate <name>` |
| `deploy activate` refused with `cannot be activated` (error `4007`) on an installed deployment | The deployment needs "Setup activation" first (`ActivationStatus: NeedsSetupToActivate`); `Instructions` list the resources that need configuration. Complete the setup in Orchestrator, then activate. `deploy status <key>` shows the same state |
| `deploy run` fails on a resource conflict | `uip solution deploy config link config.json <resource> --name <existing> --folder-path <path>` to map to the existing one, or change `conflictFixingAction` via `config set` |
| The deployment is stuck in `Draft` and `deploy activate` won't take it | Read `Operation` first. `ActivationSetup` + `Draft` is a "Setup activation" someone started in Orchestrator and did not finish — complete it there (the UI lists it as `Activation setup · Draft`); `deploy status <key>` names the resources it waits for. To discard it instead, `uip solution deploy delete <name> --yes` removes the draft alone and the deployment returns to its previous record (still needing setup). `VersionChange` + `Draft` is an upgrade queued and never installed. An `Install` `Draft` is a deploy whose install never completed — validation rejected something. It never advances on its own (a deployment passes through `Draft` for a moment right after you fire the command, but not once the command has returned). The reasons are in the failure's `Instructions` (`Validation:` / `Conflicts:`) on every feed, next to the draft's key; fix them with `uip solution deploy config set` / `deploy config link`, then run your original `uip solution deploy run …` again with `--config-file config.json` added and the **same** `--name` and `--package-version` — it still needs `--package-name` and `--folder-name`. A `Draft` left by an install does not block that rerun; one left by an update of a live deployment needs `--yes`, because the package is already deployed. While a draft exists any other version is refused, `deploy upgrade` included — to drop it instead, run `uip solution deploy upgrade <draft-key> --discard-draft`, or Delete draft in Orchestrator. To look at it, `uip solution deploy list` needs the same `--personal-workspace` / `--feed <name-or-key>` flag the deploy used — plain `deploy list` is tenant-scoped and shows no row for those deployments at all |
| `Resource not found` after deploy | `uip solution resources refresh` to re-sync from each project's `bindings_v2.json`; if still missing, the resource was never declared in any project |
| A cloud change (new entity field, changed queue setting) never reaches the solution | Expected: `refresh` is import-only and reports the resource under `Skipped`. Pull it with `uip solution resources edit <resource-key> --source remote --force` |
| Output looks empty | You may have redirected stderr — confirmations and errors go there. Re-run without `2>` |

---

For deeper detail, consult:

- The official Solutions Management guide: <https://docs.uipath.com/solutions-management/automation-cloud/latest>
- The `uipath-platform` skill — auth, Orchestrator (folders, assets, queues, buckets, robots, packages, processes), solution lifecycle (pack / publish / deploy), Integration Service, and the `uip` CLI.
- The `uipath-solution` skill — the `uip solution` lifecycle itself: pack, publish, deploy, resources, and `.uipx` membership.
- The `uipath-planner` skill — turn a Process Design Document (PDD) into an implementation-ready Solution Design Document (SDD) and pick scope (single product vs. multi-project Solution composing RPA / Flow / Case / Agents / Apps / API Workflows).
