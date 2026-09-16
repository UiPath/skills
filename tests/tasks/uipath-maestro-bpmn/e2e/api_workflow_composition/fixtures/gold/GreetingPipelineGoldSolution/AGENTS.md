# UiPath Solution Workspace

> **A `.uipx` file in this directory marks a UiPath solution. Drive every solution operation through the `uip` CLI — packing, publishing, deploying, and deployment configuration.** Do not hand-edit `.uipx`; manage projects via `uip solution projects ...` so the manifest stays internally consistent. Load the `uipath-solution` skill before running `uip solution` commands or editing `.uipx` (`uip skills install`).

This file is a static snapshot, scaffolded by the `uip` CLI version `1.203.0`. If the CLI version you have access to is different, there may be inconsistencies in the commands or options listed below. When you encounter one, look up the current form with `uip <group> --help` and **edit this file in place** — find and replace the stale command with the working one. Do the same for anything missing: if `--help` lists a command, subcommand, or option this file does not cover, add it to the table or section where it belongs.

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

The `uip ...` scaffolders (`agent init`, `maestro flow init`, `maestro bpmn init`, `maestro case init`, `api-workflow init`, `codedapp init`, and `function init` for Python functions only) **auto-register** the new project when run inside a solution directory — they walk up for the enclosing `.uipx` and add it to `Projects[]` automatically, so a separate `project add` is not needed. Pass `--skip-solution-registration` to scaffold standalone without registering; the output's `Data.SolutionRegistration.Status` is then `OptedOut`. The full set of `Status` values is: `Registered` / `AlreadyRegistered` (added in this run / already present), `NotInSolution` (no enclosing `.uipx` found), `OptedOut` (`--skip-solution-registration` passed), `Skipped` (a candidate solution was found but registration was not safe to attempt — e.g. multiple `.uipx` in one directory, or the project sits outside the solution dir), and `Failed` (manifest read/parse/write error).

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
| `BusinessRules` | Business rule — a single DMN decision. Ships as the `.dmn` file itself, not wrapped in a `.nupkg`, and the solution's `businessRule` resource points at it by file name. `restore` and `validate` are no-ops for this type. | no CLI scaffolding — authored in Studio Web | none |
| `Entity` | Data Fabric entity project — one folder per project, one `.entity` pointer file per entity; the schema itself lives in `resources/solution_folder/entity/native/<Name>.json`. Emits no package: the entity resources are the deployable payload, so `solution pack` validates the project instead of building it. | no CLI scaffolding — entity projects are modelled in the UiPath VS Code extension. Do not hand-write the `.entity` file or its resource: the pointer and the schema must stay in step, and `solution pack` fails if they do not. | `uipath-platform` (covers `uip df` entities, records and choice sets) |
| `Connector` | Integration Service connector | no CLI scaffolding — use `uip is connectors` to list / get / export existing connectors | `uipath-connector-builder` |
| `WebApp` | Legacy low-code UiPath App (the coded variant is `AppV2`) | no CLI scaffolding | none |

Install the skills with `uip skills install`. The general-purpose `uipath-platform` skill covers what isn't in a type-specific skill, and `uipath-solution` covers the solution lifecycle itself.

`BusinessRules`, `Library` and `Tests` projects declare no solution resources — `uip solution resources refresh` skips them instead of minting anything.

**`Library` is not a project type here.** A library is a reusable `.nupkg` consumed as a NuGet dependency, so `projects add` / `import` reject it and auto-registration returns `SolutionRegistration.Status: "Skipped"`. Publish it on its own (`uip rpa pack <project-dir> <output-path>`, then `uip or libraries upload --file <nupkg-path>`) and either reference it from a project's dependencies or attach it to this solution as a resource: `uip solution resources add --source remote --kind Library --name <library-name>`.

The type lives in either `project.uiproj` (top-level `ProjectType`) or `project.json` (`designOptions.outputType`, falling back to top-level `ProjectType` when `outputType` is absent — read or write either field). The `init` scaffolders above auto-register when run inside a solution directory (unless `--skip-solution-registration` is passed). For other scaffolders, register the project with the solution after scaffolding: use `uip solution projects add <project-path> [<solution-file>]` when the project already lives inside the solution directory (registers in place, no copy), or `uip solution projects import <path>` to copy a project from outside the solution dir into it and register it. If you pass an unknown type to those commands, they reject with the exhaustive accepted list — trust that error over this table.

## End-to-End Lifecycle

Run `uip login` first — most steps below need an authenticated session, including `solution pack` in some cases.

```bash
# 1. Authenticate
#    Interactive (browser OAuth):
uip login
#    Non-interactive (CI / CD) with client credentials:
uip login --client-id <ID> --client-secret <SECRET> --tenant <TENANT>

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
uip solution deploy status <pipeline-deployment-id>

# 8. List every deployment in the active tenant
uip solution deploy list
```

`deploy run` also takes `--parent-folder-key <key>` in place of `--parent-folder-path`, and `--personal-workspace` to deploy into your Personal Workspace instead of the tenant.

**A Personal Workspace deploy does not wait.** A tenant deploy polls until the install reaches a terminal state and reports `Status: "DeploymentSucceeded"`. `--personal-workspace` goes through a different endpoint that answers as soon as the install is accepted, so it reports `Status: "DeploymentStarted"` plus a `NextSteps` line and returns while the install is still running. Anything you do to that deployment next — `deploy uninstall`, `deploy activate`, an upgrade — is refused with `HTTP 400 … cannot be uninstalled` (or the equivalent) for as long as the operation is in progress.

Add `--wait` when the next step needs the deployment settled:

```bash
uip solution deploy run ... --personal-workspace --wait --timeout 300
```

With `--wait` the command polls the deployment to a terminal state inside `--timeout`, reports `Status: "DeploymentSucceeded"` and drops `NextSteps` (there is nothing left to check). A terminal failure exits `1` and names the operation status; still running when the timeout expires exits `2` with `ErrorCode: timeout` and `Retry: RetryLater` — "may still be running", so retry or check `deploy list` rather than treating it as a failed install. Without `--wait` nothing changes, so poll `uip solution deploy list` yourself if you skip it.

**One deployment per package.** `deploy run` always creates a *new* deployment in a *new* Orchestrator folder — it never updates an existing one, and it cannot deploy into a folder that already exists (Orchestrator renames the folder instead, `MySolution` -> `MySolution 1`). So if the package is already deployed, the command stops and lists the existing deployments rather than quietly adding another folder. That check is best-effort, not a guarantee: it reads the Solutions search, which needs a user session, so a CI job signed in with an application (client-credentials) account deploys without it, and a failed lookup only logs a warning. In automation, track what you have already deployed instead of relying on the stop. To ship a new version, upgrade the existing deployment in place with `uip solution deploy upgrade <deployment-key>`; to start over, `deploy uninstall` first. Pass `--yes` only when you really do want a second, independent copy. While you are still iterating, validate locally (`solution pack --dry-run`) instead of deploying each attempt.

**Activation lifecycle.** `deploy run` activates by default. To split the steps:

```bash
uip solution deploy run --skip-activate ...                      # leaves "Inactive (Ready to activate)"
uip solution deploy activate <deployment-name>     # activate later
uip solution deploy uninstall <deployment-name> --yes   # remove the deployment + its resources (--yes required; the CLI never prompts)
```

`uninstall` and `activate` take the deployment name as a **positional** argument (no `--name` flag). `status` takes the **pipeline deployment ID** (the GUID returned by `deploy run`), also positional.

`uninstall` waits out an operation that blocks it: when Orchestrator refuses because the deployment still has something running, the CLI polls until that finishes and then sends the request again, all inside `--timeout` (which covers the whole command, the status poll included). If it is still busy when the timeout expires you get exit `2` with `ErrorCode: timeout` and `Retry: RetryLater` — retry later, do not treat it as permanent. A refusal for any other reason (superseded, inactive, unknown name) still fails immediately with exit `1`.

Neither `uninstall` nor `activate` takes a feed flag, and neither needs one: they find the deployment themselves — tenant feed first, then your Personal Workspace, then the folder feeds you can reach — and scope their requests to whatever feed holds it. So the `deploy activate <name>` that `--skip-activate` points you at works the same on a `--personal-workspace` or `--feed` deployment as on a tenant one. The cost is one extra lookup per call, and a name that exists in no feed you can see is reported as not found rather than as a blocked uninstall.

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

`solution pack` runs the workflow analyzer over every RPA project. Two things control it:

```bash
uip solution pack . ./out --skip-analyze                             # don't run the analyzer at all
uip solution pack . ./out --governance-file-path ./policy.json       # analyze against a local policy file
uip solution pack . ./out --automation-ops-profile StudioWeb         # analyze against the tenant policy
```

`--skip-analyze` turns off only the analyzer rules — the compiler still restores, compiles, and validates, so a broken project still fails the pack.

The analyzer rule configuration comes from whichever governance flag you use. `--governance-file-path` reads a local policy file. `--automation-ops-profile` downloads the policy published in AutomationOps for the signed-in tenant; its value is the product to fetch (`StudioWeb`, `Development`, `Business`, …). With neither flag the analyzer uses the rules shipped with the WorkflowCompiler. The two are mutually exclusive. If the tenant policy can't be fetched — no session, or nothing published — the pack falls back to the shipped rules instead of failing. Note what that means for CI: the pack still returns `Result: Success` and exit `0`, so a stage using `--automation-ops-profile` as a governance gate goes green while having enforced the shipped defaults, not the tenant policy. Check the logs if the distinction matters.

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

After editing a project's bindings, or after `solution projects import` (which doesn't auto-sync resources), reconcile the solution-level inventory:

```bash
uip solution resources refresh     # re-scan every project, sync new / removed resources
```

`solution resources refresh` creates new resources for bindings not yet in the solution and imports from Orchestrator when a matching resource already exists.

### Adding a resource by hand

A resource is either **virtual** — declared locally now, provisioned when the solution deploys — or **imported**, pointing at something that already exists in Orchestrator. `--source` picks which:

```bash
uip solution resources add --source local  --kind Queue   --name InvoiceQueue
uip solution resources add --source remote --kind Process --name Existing --folder-path Shared
```

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
```

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

# Drop a resource from the solution (local only, leaves bindings_v2.json alone)
uip solution resources remove <resource-key>
```

`get` and `edit` use the same shape — **copy the casing `get` returns** (`Value`, not `value`). A patch key whose case does not match is treated as unknown.

Both of `edit`'s failure modes are silent and still report `Result: Success`:

- A key the SDK marks as reference, read-only or unknown is ignored rather than rejected.
- A mis-cased key is ignored the same way.

So `Result: Success` from `edit` does not mean the value changed. Read it back with `resources get` before relying on it. No CLI verb sets a *reference* property, so a virtual process cannot be pointed at a package this way — link it at deploy time with `deploy config link` instead.

A package resource key can be a composite like `TestRPA.process.TestRPA:1.0.0`; `edit` and `remove` want a plain GUID.

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

Two rules make automation reliable:

1. **Never redirect or drop stderr.** Errors and confirmations go to stderr — `2>/dev/null` will silently hide failures and produce false retries.
2. **Use `--output-filter <jmespath>`** to extract specific fields rather than piping JSON through external tools. The expression is applied to the `Data` array — start with `[]`, not with `Data[]`. On list commands with a default `--limit`, an explicit `--limit` is required with `--output-filter` (the filter only sees the records fetched). Example: `uip solution packages list --limit 100 --output-filter "[].name"`.

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
| Command targets the wrong tenant | `uip login tenant set <tenant>`; verify with `uip login status` |
| Pack succeeds but publish 409s | Version conflict — bump the version (`uip solution pack . ./out -v <new-version>`) or delete the colliding version with `uip solution packages delete <package-name> <version> --yes` (only if intentional; `--yes` required) |
| `deploy run` stops because the package is already deployed | Upgrade it in place with `uip solution deploy upgrade <deployment-key>` (running `deploy run` again does not upgrade it), or `uip solution deploy uninstall <name> --yes` first, or pass `--yes` to create a second, separate deployment |
| `deploy run` fails on a resource conflict | `uip solution deploy config link config.json <resource> --name <existing> --folder-path <path>` to map to the existing one, or change `conflictFixingAction` via `config set` |
| `Resource not found` after deploy | `uip solution resources refresh` to re-sync from each project's `bindings_v2.json`; if still missing, the resource was never declared in any project |
| Output looks empty | You may have redirected stderr — confirmations and errors go there. Re-run without `2>` |

---

For deeper detail, consult:

- The official Solutions Management guide: <https://docs.uipath.com/solutions-management/automation-cloud/latest>
- The `uipath-platform` skill — auth, Orchestrator (folders, assets, queues, buckets, robots, packages, processes), solution lifecycle (pack / publish / deploy), Integration Service, and the `uip` CLI.
- The `uipath-solution` skill — the `uip solution` lifecycle itself: pack, publish, deploy, resources, and `.uipx` membership.
- The `uipath-planner` skill — turn a Process Design Document (PDD) into an implementation-ready Solution Design Document (SDD) and pick scope (single product vs. multi-project Solution composing RPA / Flow / Case / Agents / Apps / API Workflows).
