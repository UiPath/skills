# The pipeline, and the values it needs

Read this in phase 1 or 3, or when working out what a run has to be given.

Nothing here is a coordinate for one tenant. The scripts have no account, tenant, folder or
solution path baked in, and refuse to run without the ones they need, so a wrong scope is a loud
failure rather than a silent write into somebody else's environment. What follows is the shape of
each value; the caller supplies the actual one.

## What is deployed where

```
Solution package     $SOLUTION_NAME      one package carries every coded-action job for one
                                         ontology; defaults to the solution directory's name
Solution source      $SOLUTION_SRC       the solution directory phase 1 created, holding the
                                         .uipx, one directory per function project, and the
                                         resources/solution_folder/** descriptors
Deployment           $DEPLOY_NAME        created by `deploy`, one per version
Orchestrator folder                      created by `deploy` under $PARENT_FOLDER_PATH;
                                         `uip or folders get` returns both its Key (GUID) and
                                         its numeric Id (the OrganizationUnitId)
Release shape                            ProcessType=Function,
                                         ProcessKey=$SOLUTION_NAME.Function.<ProjectName>,
                                         TargetFramework=Portable
                                         (Orchestrator computes the key itself; the CLI omits
                                         spec.packageName and nothing should hand-write it)
CLI binary           $UIP_CLI            defaults to `uip` on PATH
```

Every project in the Solution moves onto one version line together, which is why publishing is
gated and why the source tree must stay complete. Packing a subset publishes a package missing the
rest, and deploying it drops them.

Version is not part of release matching: a release is looked up by `Name` or `ProcessKey` only.
That is why republishing needs no `ont:process` change, and why only the folder id moves.

## Where the Solution source comes from

Phase 1 creates it. There are two routes and the same output shape.

**Scaffold first.** `uip solution init` creates the directory and the `.uipx`, which is also where
the fresh `SolutionId` comes from. `uip functions new --empty` creates each Function project, one
per coded action. Whether that command also registers the project in the `.uipx` `Projects` array
is version-dependent, so read the manifest and run `uip solution projects add` only for what is
missing — SKILL.md Phase 1 has the check and the exact reason.

**No `.npmrc` is written, at any point.** The `@uipath` scope does resolve from GitHub Packages
rather than npmjs, but nothing in this pipeline needs the SDK installed, and `stage_jobs.py` strips
any `.npmrc` from the staged copy on purpose: it would reach the runtime carrying an unexpanded
`${GH_NPM_REGISTRY_TOKEN}`. The npmjs 404 during `uip functions new` is expected and harmless.

**Verified live.** A CLI-scaffolded solution deploys a real job-capable release
(`ProcessType=Function`), with `projects add` generating the
`resources/solution_folder/process/function/**` descriptors itself. It emits no
`SolutionStorage.json` and needs none: the staging step reads the `.uipx` `Projects` array.
`uip or processes list` reports the release version as `ProcessVersion`.

**There is no template fallback, and the CLI scaffold is the only route.** An earlier revision
shipped a known-good Studio Web export's manifests to copy from; it is gone. `uip solution init`
plus `uip functions new --empty` is verified to produce the same shape, and the export carried a
`SolutionId` that was not ours to reuse.

### The manifest is authoritative, not the directory listing

Which projects the package contains comes from `SolutionStorage.json` when it exists, and from the
`.uipx` `Projects` array when it does not. Listing directories would silently include a stray
folder, or miss a project the manifest still references.

### Staging

No function project has a committed job source. Its source is the job that lives beside the action
TTL that invokes it, and `jobs.map.json` in the solution directory records the mapping:

```json
{ "projects": { "<ProjectName>": "../jobs/<job>.ts" } }
```

Relative paths resolve against that file's own directory, so a job beside its action is written
relative and one outside the tree is written absolute.

`stage_jobs.py` copies the tree to a temp staging dir, writes each mapped source in as that
project's `main.ts`, derives that project's `entry-points.json` from the job's interfaces, and
packs the copy. `main.ts` at the project root is the layout the verified Studio Web export shipped
and what `uipath.json`'s functions map (`main: main.ts:default`) and the manifest's
`filePath: content/main.ts` both name. The source tree is never mutated, and a job is edited in
exactly one place. The consequence: **the source tree is not directly packable**, so always go
through the script.

`uip solution pack` requires each project's `entry-points.json` and never produces one; without it
pack fails with `entry-points.json not found. Run 'uipath-functions pack' to generate it.` (an
error naming a binary that does not exist). The command that would generate it, `uip functions
pack`, **cannot lower the `type<T>()` contract idiom** on any SDK version, so the script derives
the manifest itself with `tools/entry_points.py`. That deriver reproduces byte-for-byte what
Studio Web's own packer produced for both verified jobs, which is the only evidence of what the
platform accepts. `uip solution pack` reads no TypeScript and only zips the tree, so a manifest
supplied alongside `main.ts` is all it needs.

Deriving on every stage is what keeps the interfaces and the manifest from drifting. A contract
the deriver cannot read is refused rather than approximated, because a wrong manifest faults the
job before its handler runs.

A project listed in `jobs.map.json` must not also have a committed `main.ts`: the staged copy
supplies it, and a committed one would be a second copy free to drift.

## Publish and deploy

Pack from the solution directory and upload the `.zip`. No cloud project, no Studio Web,
no `uip functions push`.

```bash
python3 <SKILL_DIR>/scripts/publish_package.py 1.0.3                         # dry run: current, next, target
python3 <SKILL_DIR>/scripts/stage_jobs.py                                 # build + validate, temp only
uip solution pack <staging> /tmp/pk -n support-jobs -v 1.0.3  # local .zip, no tenant writes
python3 <SKILL_DIR>/scripts/publish_package.py 1.0.3                         # prints the steps
python3 <SKILL_DIR>/scripts/publish_package.py 1.0.3 --execute               # pack, then upload to the feed
python3 <SKILL_DIR>/scripts/deploy_release.py  1.0.3 <deployment-name> --execute   # creates the folder, or upgrades in place
uip or folders get "<PARENT>/<deployment-name>"          # -> Key and numeric Id, in one call
python3 <SKILL_DIR>/scripts/await_release.py <ProcessName> 1.0.3 --folder-path "<PARENT>/<deployment-name>"
```

**Never reuse a version number.** Publishing the same version is a silent no-op everywhere:
publish succeeds, deploy reports Successful, nothing changes, and no output distinguishes it from
a real release. `publish_package.py` computes `next = current + 1` from the live deployment,
filtering tombstones, and refuses any other version unless `--force-version` is passed.

**`publish` is asynchronous.** `--wait` polls until the package is Ready. Deploying before it
finishes fails with a package-not-found error that says nothing about publishing.

**The first deploy creates the folder. Every later one upgrades it in place.** `publish` uploads a
package version to the feed; the deployment then has to run on it. `deploy run` with the **same
deployment name** and a new `--package-version` upgrades that deployment: one folder throughout,
the same folder key, no duplicate processes, `ActivationStatus: SuccessfulActivate` each time.
Verified across three consecutive versions.

There is no `uip solution deploy upgrade`. The subcommands are activate, config, list, run, status <!-- uip-check-skip -->
and uninstall. `deploy run` *is* the upgrade path, so nothing here is pending a spike.

**A deployment cannot target an existing folder.** `--folder-name` is documented as the name *for
the new folder created for this deployment*, and the other folder flags name only a parent. Given a
name that already exists, the deploy creates `<name> 1` and puts the processes there, leaving
anything bound to the original folder pointing at zero processes -- which surfaces at invoke as
`No Orchestrator process named '...' in Orchestrator folder N`. This is why the deployment goes
first and everything else follows the folder it made.

**Never uninstall to re-release.** `uninstall` removes all provisioned resources *and the solution
folder*, and the ontology's Data Fabric entities live in that folder. Uninstalling to get a clean
deploy destroys the author's data. Reusing the deployment name is the correct path.

**The folder MUST be created under `Shared`.** A solution folder created at the ROOT gets no
user with unattended robot permissions, so the service cannot start the job in it:

```
HTTP 409  errorCode 1671
"Couldn't find any user with unattended robot permissions in the current folder."
```

and the invoke surfaces that only as a bare `"Unexpected error"` on the `Running job` step, with
zero jobs created in the folder, which is a misleading pair. A folder created under `Shared` inherits its
assignments and runs the job. `PARENT_FOLDER_PATH` defaults to `Shared` for exactly this reason;
point it at a different parent only if that parent has robot permissions to inherit.

`deploy list` is how you tell publish from deploy. `CurrentPackageVersion` is what is running;
`NewPackageVersionAvailable` is a published package the deployment has not taken. Seeing `1.0.2` /
`1.0.3` there means publish succeeded and only the deploy is outstanding.

### Binding the ontology to the folder

Nothing is patched into an artifact. The action names its release with `ont:process` and says
nothing about where that release is deployed, so a re-release changes no file.

What the caller needs from this phase is the folder itself, and one call returns both
representations:

```bash
uip or folders get "<PARENT>/<deployment-name>"   # -> Key (GUID) and Id (numeric OrganizationUnitId)
```

The **Key** is what the ontology is created against (`uip ont create --folder-key`) and what the
Data Fabric entities are created in. The numeric **Id** is what Orchestrator's
`X-UIPATH-OrganizationUnitId` header wants. They are two representations of one folder, returned
together, so neither has to be derived from the other.

`ont:process` does not change across releases either: the release Name and ProcessKey are identical
after an in-place upgrade.

### Await

`await` polls for up to ten minutes and distinguishes three outcomes: `ready`, `stale` (keeps
polling), and `missing` (fails immediately, listing what the folder does contain). Nothing may
invoke before `ready`: a stale Release is indistinguishable from a fresh one at the API surface,
and invoking against one is what produced three consecutive `JsCodedFunction.ValidationFailed`
faults.

`stage` writes only to a temp directory and is the fastest proof that a job change reaches the
staging tree and that its contract lowers to a manifest; `pack` also only writes there, and runs
no installer, so it needs neither the network nor `GH_NPM_REGISTRY_TOKEN`. Check the nupkg if in
doubt. A correct pack contains `<SolutionName>.Function.<ProjectName>.<version>.nupkg` with the
job at `content/main.ts`, which is what `entry-points.json`'s `filePath` refers to.

### Two dead ends, so nobody re-walks them

**`uip solution projects publish --project-name <name>` does not work.** That publishes an existing <!-- uip-check-skip -->
*cloud* solution project, and `--project-name` wants a Studio Web project name, and the name you
know is the name of the deployment and of the package, a different namespace. It fails
`HTTP 400: Project with name '<name>' not found` (`projectName`, error 2003, `RetryWillNotFix`).
Nor can the CLI enumerate cloud project names: `uip solution projects list` reads only the on-disk <!-- uip-check-skip -->
manifest. Packing from source needs none of it.

**`uip functions publish` is not a substitute.** The `uipath-functions` skill states JS/TS
functions have no job semantics (HTTP endpoint only, no `StartJobs`), yet these demonstrably run
as Orchestrator jobs with `ProcessType=Function`. The difference is the route: `functions publish`
targets a package feed and likely produces the HTTP-only flavour. Use the Solution route.

## What the caller must supply

Required. No default, and the script exits rather than guessing.

| Variable | Shape | Needed by |
|---|---|---|
| `SOLUTION_SRC` | path to the solution directory | `stage`, `pack`, `publish` |

Optional, defaulted to a convention rather than to anyone's tenant.

| Variable | Default | Why this default is safe |
|---|---|---|
| `SOLUTION_NAME` | the solution directory's name | the package name follows the directory phase 1 named |
| `DEPLOY_NAME` | `SOLUTION_NAME` | a name this skill creates, not one it discovers |
| `PARENT_FOLDER_PATH` | `Shared` | the Orchestrator folder that carries robot permissions |
| `UIP_CLI` | `uip` | the binary on PATH |

Org and tenant are not variables here. They come from the authenticated session that `uip` already
holds, and `uip login status` is the only thing allowed to report them.
