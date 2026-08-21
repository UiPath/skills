# UiPath Solution Workspace

> **A `.uipx` file in this directory marks a UiPath solution. Drive every solution operation through the `uip` CLI — packing, publishing, deploying, and deployment configuration.** Do not hand-edit `.uipx`; manage projects via `uip solution project ...` so the manifest stays internally consistent.

This file is a static snapshot, scaffolded by the `uip` CLI version `1.197.0`. If the CLI version you have access to is different, there may be inconsistencies in the commands or options listed below. When you encounter one, look up the current form with `uip <group> --help` and **edit this file in place** — find and replace the stale command with the working one.

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
| Register an existing subfolder of the solution dir as a project (no copying — use after scaffolding *inside* the solution dir, e.g. `uip rpa create-project --location <solution-dir>`) | `uip solution project add <project-path> [<solution-file>]` |
| Add a project from outside the solution — copies the folder at `<path>` into the solution dir and registers it (`<path>` is a local filesystem path) | `uip solution project import <path>` |
| Unregister a project (does not delete the project files on disk) | `uip solution project remove <project-path> [<solution-file>]` |
| List projects in the solution | `uip solution project list` |

The `uip ... init` scaffolders (`agent init`, `maestro flow init`, `maestro bpmn init`, `maestro case init`, `api-workflow init`) **auto-register** the new project when run inside a solution directory — they walk up for the enclosing `.uipx` and add it to `Projects[]` automatically, so a separate `project add` is not needed. Pass `--skip-solution-registration` to scaffold standalone without registering; the output's `Data.SolutionRegistration.Status` is then `OptedOut`. The full set of `Status` values is: `Registered` / `AlreadyRegistered` (added in this run / already present), `NotInSolution` (no enclosing `.uipx` found), `OptedOut` (`--skip-solution-registration` passed), `Skipped` (a candidate solution was found but registration was not safe to attempt — e.g. multiple `.uipx` in one directory, or the project sits outside the solution dir), and `Failed` (manifest read/parse/write error).

## Project Types

A solution can contain multiple projects of different types. The table below lists each project type and the `uip` command that scaffolds a fresh one (or marks the row when no scaffolding command exists).

| Type | Description | Scaffold with | Skill |
|---|---|---|---|
| `Process` | RPA process — Studio workflow (XAML, Coded C#, or Hybrid) | `uip rpa create-project --name <name>` | `uipath-rpa` |
| `Library` | Reusable RPA library | `uip rpa create-project --template-id LibraryProcessTemplate --name <name>` | `uipath-rpa` |
| `Tests` | Test Automation project | `uip rpa create-project --template-id TestAutomationProjectTemplate --name <name>` | `uipath-rpa` |
| `Flow` | Maestro Flow — long-running orchestrated workflow | `uip maestro flow init <name>` | `uipath-maestro-flow` |
| `CaseManagement` | Maestro Case — stateful business process (SLA, approvals, HITL) | `uip maestro case init <name>` | `uipath-maestro-case` |
| `ProcessOrchestration` | Maestro BPMN — long-running orchestrated process | `uip maestro bpmn init <name>` | `uipath-maestro-bpmn` |
| `Agent` | LLM agent project — **low-code** (configured via `agent.json`; no Python) or **coded** (Python: LangGraph / LlamaIndex / OpenAI Agents). Both subtypes share `ProjectType: "Agent"`; the discriminator is `agent.json#type`. | `uip agent init <path>` (low-code) · `uip codedagent new [name]` (coded — see the `uipath-agents` skill for the full flow) | `uipath-agents` |
| `AppV2` | Coded App — web application | `uip codedapp init <path>` | `uipath-coded-apps` |
| `Function` | UiPath Function (JS / TS / Python) | `uip functions new [name]` | none |
| `Api` | API Workflow project | `uip api-workflow init <name>` | none |
| `Connector` | Integration Service connector | no CLI scaffolding — use `uip is connectors` to list / get / export existing connectors | none |
| `WebApp` | Legacy low-code UiPath App (the coded variant is `AppV2`) | no CLI scaffolding | none |

All skill should be installed by running the command: `uip skills install`. The general-purpose `uipath-platform` skill covers what isn't in a type-specific skill.

The type lives in either `project.uiproj` (top-level `ProjectType`) or `project.json` (`designOptions.outputType`, falling back to top-level `ProjectType` when `outputType` is absent — read or write either field). The `init` scaffolders above auto-register when run inside a solution directory (unless `--skip-solution-registration` is passed). For other scaffolders, register the project with the solution after scaffolding: use `uip solution project add <project-path> [<solution-file>]` when the project already lives inside the solution directory (registers in place, no copy), or `uip solution project import <path>` to copy a project from outside the solution dir into it and register it. If you pass an unknown type to those commands, they reject with the exhaustive accepted list — trust that error over this table.

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
#     Useful in CI: login -> restore -> pack. Takes <solutionPath> only; it
#     does not produce a package. Pack also restores internally, so this is an
#     optimization, not a requirement.
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

**Activation lifecycle.** `deploy run` activates by default. To split the steps:

```bash
uip solution deploy run --skip-activate ...                      # leaves "Inactive (Ready to activate)"
uip solution deploy activate <deployment-name>     # activate later
uip solution deploy uninstall <deployment-name> --yes   # remove the deployment + its resources (--yes required; the CLI never prompts)
```

`uninstall` and `activate` take the deployment name as a **positional** argument (no `--name` flag). `status` takes the **pipeline deployment ID** (the GUID returned by `deploy run`), also positional.

## Package Signing

`solution pack` can sign each packed project `.nupkg` with a code-signing certificate. Signing is opt-in: add `--signing-certificate-path <cert.pfx>` to the pack command. The certificate password (`--signing-certificate-password`) is optional — passing it as `env.VAR` (e.g. `env.SIGNING_PASSWORD`) is recommended, though an inline value also works. An optional timestamp server is set with `--signing-timestamp-server <url>`.

## Studio Web (Browser Editing)

Studio Web is a separate target from the Orchestrator deploy chain — it hosts a browser-based collaborative editor for solutions. The `solution upload` command pushes the local solution there and returns a `DesignerUrl` to open the solution in a browser; this is independent of `pack` / `publish` / `deploy` and does *not* produce a runtime-deployable artifact.

```bash
uip solution upload .                      # upload solution dir to Studio Web as a new solution; returns DesignerUrl
uip solution upload . --force              # force-replace the existing Studio Web solution referenced by .uipx (destroys cloud version history)
uip solution download <solution-id>        # round-trip a Studio Web solution back to disk
uip solution delete <solution-id> --yes    # remove a solution from Studio Web (--yes required; the CLI never prompts)
```

`upload` accepts a solution directory, a `.uipx` file, or a `.uis` file. It probes Studio Web for the bundled `SolutionId` first: if the cloud has no solution with that id, the upload imports as new; if a solution with that id already exists, the upload is refused unless `--force` is passed. Forcing replaces the cloud project in place and **wipes its Studio Web version history**, so use `--force` deliberately. To upload a copy as an unrelated cloud solution instead of overwriting, scaffold a fresh solution with `uip solution init` (or remove the `SolutionId` from the local `.uipx`) and re-run upload.

## Per-Project Bindings (`bindings_v2.json`)

Each project declares the resources it needs (assets, queues, buckets, processes, …) in a `bindings_v2.json` file at the project root. These declarations drive the solution's resource inventory.

After editing a project's bindings, or after `solution project import` (which doesn't auto-sync resources), reconcile the solution-level inventory:

```bash
uip solution resources refresh     # re-scan every project, sync new / removed resources
```

`solution resources refresh` creates new resources for bindings not yet in the solution and imports from Orchestrator when a matching resource already exists.

Inspect the current solution inventory:

```bash
uip solution resources list        # everything declared in this solution
```

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
2. **Use `--output-filter <jmespath>`** to extract specific fields rather than piping JSON through external tools. The expression is applied to the `Data` array — start with `[]`, not with `Data[]`. Example: `uip solution packages list --output-filter "[].name"`.

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
| `uip functions` | UiPath Functions |
| `uip tm` | Test Manager (test projects, sets, executions) |
| `uip is` | Integration Service (connectors, connections) |
| `uip tools` | Manage CLI tool extensions |

## Troubleshooting Quick Map

| Symptom | First thing to check |
|---|---|
| `Not authenticated` / 401 | `uip login`, then re-run |
| Command targets the wrong tenant | `uip login tenant set <tenant>`; verify with `uip login status` |
| Pack succeeds but publish 409s | Version conflict — bump the version (`uip solution pack . ./out -v <new-version>`) or delete the colliding version with `uip solution packages delete <package-name> <version> --yes` (only if intentional; `--yes` required) |
| `deploy run` fails on a resource conflict | `uip solution deploy config link config.json <resource> --name <existing> --folder-path <path>` to map to the existing one, or change `conflictFixingAction` via `config set` |
| `Resource not found` after deploy | `uip solution resources refresh` to re-sync from each project's `bindings_v2.json`; if still missing, the resource was never declared in any project |
| Output looks empty | You may have redirected stderr — confirmations and errors go there. Re-run without `2>` |

---

For deeper detail, consult:

- The official Solutions Management guide: <https://docs.uipath.com/solutions-management/automation-cloud/latest>
- The `uipath-platform` skill — auth, Orchestrator (folders, assets, queues, buckets, robots, packages, processes), solution lifecycle (pack / publish / deploy), Integration Service, and the `uip` CLI.
- The `uipath-solution-design` skill — turn a Process Design Document (PDD) into an implementation-ready Solution Design Document (SDD) and pick scope (single product vs. multi-project Solution composing RPA / Flow / Case / Agents / Apps / API Workflows).
