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
                                         `folder-id "Shared/<name>"` resolves its numeric Id
Release shape                            ProcessType=Function,
                                         ProcessKey=$SOLUTION_NAME.Function.<ProjectName>,
                                         TargetFramework=Portable
                                         (Orchestrator computes the key itself; the CLI omits
                                         spec.packageName and nothing should hand-write it)
uip binary           $UIP_CLI            defaults to `uip` on PATH
```

Every project in the Solution moves onto one version line together, which is why publishing is
gated and why the source tree must stay complete. Packing a subset publishes a package missing the
rest, and deploying it drops them.

Version is not part of release matching: a release is looked up by `Name` or `ProcessKey` only.
That is why republishing needs no `ont:process` change, and why only the folder id moves.

## Where the Solution source comes from

Phase 1 creates it. There are two routes and the same output shape.

**Scaffold first.** `uip solution init` creates the directory and the `.uipx`, which is also where
the fresh `SolutionId` comes from. `uip functions new --empty` creates each Function project, and
`uip solution projects add` registers it in the manifest. One project per coded action. The
scaffold also writes each project's `.npmrc`: the `@uipath` scope resolves from GitHub Packages,
not npmjs, via `${GH_NPM_REGISTRY_TOKEN}`, and the CLI's own scaffolding writes no `.npmrc`.

**Verified live.** A CLI-scaffolded solution deploys a real job-capable release
(`ProcessType=Function`), with `projects add` generating the
`resources/solution_folder/process/function/**` descriptors itself. It emits no
`SolutionStorage.json` and needs none: the staging step reads the `.uipx` `Projects` array.
`uip or processes list` reports the release version as `ProcessVersion`.

**Template fallback.** `assets/solution-skeleton` is a known-good Studio Web export's manifests,
instantiated by `solution_scaffold.py --template`. Its `.uipx` carries the exported `SolutionId`
rather than a fresh one, which matters only if the solution ever has to reach Studio Web.
`assets/NOTES.md` lists every renamed occurrence.

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

`solution_release.py` copies the tree to a temp staging dir, writes each mapped source in as that
project's `functions/<actionName>.ts`, and packs the copy. Into `functions/`, never the project
root: `uip functions pack` rebuilds the `uipath.json` functions map from a directory scan of
`functions/*.ts` on every run and silently discards hand-written entries, so a root-level source
is invisible and packs to nothing. The source tree is never mutated, and a job is edited in
exactly one place. The consequence: **the source tree is not directly packable**, so always go
through the script.

At pack time the script runs `uip functions pack` inside every staged project before
`uip solution pack`: only the functions pass generates `entry-points.json`, and solution pack
without it fails with `entry-points.json not found. Run 'uipath-functions pack' to generate it.`
(the error names a binary that does not exist; the working command is `uip functions pack`).

A project listed in `jobs.map.json` must not also have a committed `functions/*.ts`: the staged
copy supplies it, and a committed one would be a second copy free to drift.

## Publish and deploy

Pack from the solution directory and upload the `.zip`. No cloud project, no Studio Web,
no `uip functions push`.

```bash
scripts/solution_release.py version                               # {current, next}
scripts/solution_release.py stage                                 # build + validate, temp only
scripts/solution_release.py pack    1.0.3 /tmp/pk                 # local .zip, no tenant writes
scripts/solution_release.py publish 1.0.3                         # prints the steps
scripts/solution_release.py publish 1.0.3 --execute               # pack, then upload to the feed
scripts/solution_release.py deploy  1.0.3 support-jobs-1-0-3 --execute
scripts/solution_release.py folder-id "Shared/support-jobs-1-0-3" # -> ont:processFolderId
scripts/solution_release.py await TagOverdueTicketProcess 1.0.3 --folder-path "Shared/support-jobs-1-0-3"
```

**Never reuse a version number.** Publishing the same version is a silent no-op everywhere:
publish succeeds, deploy reports Successful, nothing changes, and no output distinguishes it from
a real release. `version` computes `next = current + 1` from the live deployment, filtering
tombstones, precisely so nobody has to remember what was last shipped.

**`publish` is asynchronous.** `--wait` polls until the package is Ready. Deploying before it
finishes fails with a package-not-found error that says nothing about publishing.

**A new version means a new deployment, not an upgrade.** `publish` uploads a package version to
the feed; the deployment then has to run on it. `uip solution deploy run` does not upgrade. It
creates a deployment plus a new Orchestrator folder (`-n` required, fresh `DeploymentKey`). Treat
the folder as moving on every release and repoint the TTL in phase 5.

The old deployment is left alone, still serving its old version, which makes rollback trivial: put
the previous folder id back in the TTL.

**SPIKE-PENDING.** `uip solution deploy upgrade` exists in the CLI help as an in-place upgrade of
an existing deployment, but no verified run has used it: test whether upgrading a live deployment
to a new package version keeps the same Orchestrator folder id, which would remove phase 5 from
the repeat path and nothing else. Until then, assume folder-per-version and repoint the TTL every
release.

So folders accumulate one per release. Deploy the new version, repoint the TTL, confirm with
`await`, and only then consider retiring the previous deployment. Uninstalling deletes the folder,
so doing it before the TTL is repointed destroys the folder the live action still names. Name the
folder after the version so which is which stays obvious.

**The new folder MUST be created under `Shared`.** A solution folder created at the ROOT gets no
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

### Repointing the action at the new folder

`deploy --execute` prints the new folder id; `folder-id <path>` resolves it separately, because
`deploy run` reports only a FolderPath and the TTL needs the numeric Id. The one place the CLI
exposes that Id is `OrganizationUnitId` in `uip or processes get --all-fields`: `uip or folders
get` takes only a GUID or key, never a path, and `uip or processes list` returns only the GUID
`FolderKey`. `folder-id` therefore lists the folder's processes by path and reads the numeric id
off one of them.

```bash
scripts/ttl_patch.py {workdir}/{name}-{action}.ttl --folder-id <id> --execute
```

`ont:process` does not change: the release Name and ProcessKey are identical in the new folder, and
only the folder differs.

### Await

`await` polls for up to ten minutes and distinguishes three outcomes: `ready`, `stale` (keeps
polling), and `missing` (fails immediately, listing what the folder does contain). Nothing may
invoke before `ready`: a stale Release is indistinguishable from a fresh one at the API surface,
and invoking against one is what produced three consecutive `JsCodedFunction.ValidationFailed`
faults.

`stage` writes only to a temp directory and is the fastest proof that a job change reaches the
staging tree; `pack` also only writes there, but runs `uip functions pack` per project, which
installs dependencies and so needs the network and `GH_NPM_REGISTRY_TOKEN`. Check the nupkg if in
doubt. A correct pack contains `<SolutionName>.Function.<ProjectName>.<version>.nupkg` with the
job at `content/functions/<actionName>.ts`, which is what `entry-points.json`'s `filePath` refers
to.

### Two dead ends, so nobody re-walks them

**`uip solution projects publish --project-name <name>` does not work.** That publishes an existing
*cloud* solution project, and `--project-name` wants a Studio Web project name, and the name you
know is the name of the deployment and of the package, a different namespace. It fails
`HTTP 400: Project with name '<name>' not found` (`projectName`, error 2003, `RetryWillNotFix`).
Nor can the CLI enumerate cloud project names: `uip solution projects list` reads only the on-disk
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
