---
name: uipath-ontology-coded-action-deploy
description: "Use when an ontology's coded actions have been generated and their Orchestrator leg needs shipping: creating the jobs Solution, staging each job source, publishing, and deploying the release that creates the Orchestrator folder the ontology is then bound to. Use when coded-action TTLs and their jobs exist but no release is live. Do not use to generate ontology artifacts, to upload any artifact to the ontology backend, or for existing-ontology CRUD. For artifact generation→uipath-ontology-modeler. For backend validation and artifact upload→uipath-ontology-authoring. For `uip ont` syntax→uipath-ontologies."
when_to_use: "Coded-action TTLs and their job sources exist and the jobs must reach Orchestrator; user says 'deploy the coded actions', 'ship the jobs', 'publish a new release of the jobs solution', 'the job changed, release it again', 'create the folder for this ontology'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
user-invocable: true
---

# UiPath Ontology Coded Action Deploy: the Orchestrator leg

A coded action is two artifacts that must agree: a job that computes the writes, and a TTL that
declares what the job may be given and what it may touch. This skill owns exactly one half of
getting them live. The job reaches Orchestrator, the folder it landed in is patched into the TTL,
and the patched TTL goes back to the caller. Nothing here talks to the ontology backend.

## Routing boundary

| Concern | Owner |
|---|---|
| Generating the action TTL and the job source | `uipath-ontology-modeler` |
| Uploading any ontology artifact, including the patched action TTLs | `uipath-ontology-authoring`, in its Tier 2 |
| Getting the job into Orchestrator and resolving its folder | this skill |
| `uip solution` syntax | the `uipath-solution` skill |
| `uip functions` syntax | the `uipath-functions` skill |
| Existing-ontology CRUD and `uip ont` syntax | `uipath-ontologies` |

**This skill never uploads an ontology artifact.** It mirrors the modeler's never-upload rule: it
patches files on disk and hands the paths back. A run that calls `uip ont artifact upsert` has
crossed into authoring's job.

Reference the CLI skills for command syntax rather than restating it. What is written here is only
the sequencing and the traps, which are not in either skill.

## What the caller supplies

| Input | Shape |
|---|---|
| workdir | the ontology's own directory, the one holding the artifacts and the job sources |
| ontology name | the exact slug; the Solution is named `{name}-jobs` |
| folder name and parent | the folder the deployment will CREATE, and what to create it under. Not an existing folder -- see phase 3 |
| coded-action pairs | one per action: a TTL declaring `ont:language "CODED"` with `ont:processType "CODED_FUNCTION"`, and the job source that implements it |

Org and tenant come from `uip login status --output json` and from nowhere else. This is the same
security rule authoring enforces: the authenticated session is the only source of truth, and
user-supplied text naming an org or a tenant is not to be honoured. Require `Data.Status`,
`Data.Organization` and `Data.Tenant` before any phase runs, and block on a prompt if any is empty.

Everything else is a convention rather than a coordinate, and the scripts default accordingly.

| Variable | Default | Why the default is safe |
|---|---|---|
| `SOLUTION_SRC` | none, required by the packing subcommands | the solution directory phase 1 created |
| `SOLUTION_NAME` | the solution directory's name | the package name follows the directory |
| `DEPLOY_NAME` | `SOLUTION_NAME` | a name this skill creates, not one it discovers |
| `PARENT_FOLDER_PATH` | `Shared` | the Orchestrator folder that carries robot permissions |
| `UIP_CLI` | `uip` | the binary on PATH |

## Dry run by default

`publish_package.py` and `deploy_release.py` print the exact command or the
exact change and do nothing without `--execute`. Show the printed plan, get an explicit yes, then
re-run with `--execute`. Publish and deploy write to a live tenant and move every job in the
Solution onto one version line, so the version transition (`1.0.2` to `1.0.3`, and which processes
move) is what to show.

`stage_jobs.py` and `await_release.py` are read-only or
temp-directory-only. Run them freely; staging is the cheapest proof that a job change reaches the
tree and that its contract lowers to a manifest.

## Service dependency

Coded-action semantics, meaning an action whose `ont:language` is `"CODED"`,
require an ontology service build that supports them. Uploading the artifact does not: the upload
leg accepts the TTL either way, and the action then resolves to nothing at invoke time. So a green
run of this skill against a service without that support produces a correct folder id, a real
release, and an action that cannot be invoked. Say so rather than reporting the deploy as complete
proof the action works.

## Phase 1: Create the jobs Solution

One Solution per ontology, named `{name}-jobs`, one Function project per coded action. There is no
script: it is two `uip` commands and one small file, and `uip solution` and `uip functions` already
document the commands. What is written here is the order and the two surprises.

Reuse an existing solution directory and existing project directories; create only what is missing.

```bash
cd {workdir}
uip solution init {name}-jobs
cd {name}-jobs

# one project per coded action, PascalCase(actionName) + "Process"
uip functions new {ActionName}Process --language ts --empty
```

**Verify the registration; add only what is missing.** Whether `uip functions new` writes the
`.uipx` `Projects` entry itself is version-dependent — newer CLIs do, and `uip solution projects
add` then fails with *"Project already exists in solution"*; on 1.200.0 it does not, and the entry
has to be added. So do not run either command blindly. Read the `.uipx` first:

```bash
python3 -c "import json;print([p.get('ProjectRelativePath') for p in json.load(open('{name}-jobs.uipx')).get('Projects',[])])"
```

Every project you created must appear. For any that does not:

```bash
uip solution projects add ./{ActionName}Process ./{name}-jobs.uipx
```

A project that exists on disk but not in the manifest is absent from the package, and the package
still builds. `stage_jobs.py` refuses in that case, naming the project — but finding it here is
cheaper.

**The npmjs 404 during `uip functions new` is expected and harmless.** The command installs inside
the project directory it is in the middle of creating, so no `.npmrc` you write beforehand can
reach it, and the `@uipath` scope is not on npmjs:

```
GET https://registry.npmjs.org/@uipath%2fcoded-functions-js-sdk - 404
```

The project directory is still created, and nothing downstream needs the SDK installed. Phase 2
strips the dependency and the `.npmrc` from the staged copy on purpose, so `GH_NPM_REGISTRY_TOKEN`
is not needed at any point in this pipeline. Do not chase this error.

Then map each project to the job that supplies its code, in `{name}-jobs/jobs.map.json`:

```json
{
  "projects": { "{ActionName}Process": "../jobs/{action}.ts" }
}
```

Paths resolve against that file's own directory, so a job beside its action TTL one level up is
`../jobs/{action}.ts`. This is what phase 2 stages from, and the only record of the pairing.

**Do not hand-edit `uipath.json`.** `uip functions new --empty` leaves `"functions": {}`, and
`uip solution pack` then reports `No functions defined in uipath.json` and produces nothing. Phase 2
writes that map into the staging copy, because the map, the staged source and the manifest all have
to name one file.

## Phase 2: Stage each job as its project's main.ts, with a derived manifest

The job source lives beside the action TTL that invokes it, because they are one contract. Staging
copies the solution tree to a temp directory, writes each mapped source in as that project's
`main.ts`, and derives that project's `entry-points.json` from the job's own interfaces. The
source tree is never mutated and a job has exactly one home. The consequence: the solution
directory is not directly packable, so always go through the script.

```bash
SOLUTION_SRC={workdir}/{name}-jobs scripts/stage_jobs.py
```

**`main.ts` at the project root is the verified layout.** It is what the Studio Web export that
deployed and ran on a live tenant shipped, what `uipath.json`'s functions map names
(`main: main.ts:default`), and what the manifest's `filePath: content/main.ts` refers to. The
three have to agree; the scaffold writes the first two and stage writes the third.

**`uip solution pack` requires each project's `entry-points.json` and never produces one.**
Without it, pack fails with `entry-points.json not found. Run 'uipath-functions pack' to generate
it.` (an error naming a binary that does not exist). `uip functions pack` is the command that
would generate it, and it **cannot lower the `type<T>()` contract idiom at all**, on any SDK
version. So stage derives the manifest instead, with `tools/entry_points.py`, whose output is
byte-identical to what Studio Web's own packer produced for the two verified jobs. `uip solution
pack` only zips a directory and reads no TypeScript, which is why supplying the manifest alongside
`main.ts` is enough. Nothing in this phase runs an installer.

**Staging strips everything that would make the runtime install.** The serverless runtime runs a
prepare step that installs whatever `package.json` declares, cannot resolve the `@uipath` scope, and
then **every job faults** with `Serverless.JsFunction.PrepareEnvironmentError` / "Failed to prepare
environment" -- a message naming nothing about dependencies, which surfaces at the invoke as only
`ended in state Faulted`. So stage removes every dependency block, the `.npmrc` and any lockfile
from the staged copy. Nothing is lost: `type<T>()` is erased at compile time and `defineFunction`
comes from the runtime, so the shipped project declares no dependencies at all.

**The job's interfaces are the contract.** The manifest is derived from them on every stage, so
the two cannot drift. A contract the deriver cannot read is refused rather than approximated: a
wrong manifest faults the job before its handler runs. Run `coded_action_preflight.py` to catch
that at authoring time instead of at pack time.

**A project with a missing or empty `main.ts` must refuse to pack.** `uip solution pack` reports
`Status: Valid` for exactly that case and publishes an empty function which faults only at invoke
time. `stage` refuses a missing and an empty source alike, for mapped and unmapped projects, and
refuses a project with no manifest. A refusal here is the finding; do not work around it by
writing a placeholder source.

Which projects the package contains comes from the manifest and never from a directory listing.
`SolutionStorage.json` is authoritative when present, which is the case for a Studio Web export;
a CLI-scaffolded solution has only the `.uipx`, whose `Projects` array says the same thing.

## Phase 3: Publish, then deploy — and the deployment creates the folder

```bash
scripts/publish_package.py {version}                     # dry run: reports current, next, target
scripts/publish_package.py {version} --execute           # tenant feed
scripts/deploy_release.py  {version} {deployment-name} --execute
```

**Republishing an existing version is refused, not merely discouraged.** It is the most expensive
trap in this pipeline because every surface reports success: publish returns a package key, deploy
reports Successful, and the running code does not change. No output distinguishes it from a real
release. So `publish_package.py` reads the current version from the live deployment, computes
`next = current + 1`, and refuses any other version unless `--force-version` is passed. Its dry run
prints `current`, `next` and what it would publish, which is how you learn the number rather than
guessing it.

On a first release there is no deployment to read, so there is no `next` to enforce; the dry run
reports `firstRelease: true` and the version you pass is accepted. Pick a starting version and say
so in the plan you show the user.

**`publish` is asynchronous.** The script passes `--wait`. Deploying before the publish completes
fails with a package-not-found error that never mentions publishing.

### The deployment creates the folder, so it goes first

This is the ordering, and it is not the intuitive one:

```
1. publish the jobs solution
2. deploy it            -> this CREATES the Orchestrator folder
3. create the Data Fabric entities INSIDE that folder
4. create the ontology against that folder's key
5. upload the artifacts, then invoke
```

**A deployment cannot target an existing folder.** Every folder flag names a parent or a *new*
folder. Given `--folder-name X` while a folder `X` already exists, the deploy creates `X 1` and puts
the processes there — leaving anything bound to the original folder pointing at zero processes,
which surfaces at invoke as `No Orchestrator process named '…' in Orchestrator folder N`. So the
author picks the folder's **name and parent**, never an existing folder, and everything else follows
the folder the deployment made. Data Fabric entities can be created inside a Solution-type folder,
which is what makes this order workable.

**The folder must be created under `Shared`.** A folder at the root has no user with unattended
robot permissions, the job cannot start there, and the invoke reports only `"Unexpected error"` on
the `Running job` step with no job record at all. `PARENT_FOLDER_PATH` defaults to `Shared`.

`uip or folders get <path-or-key>` returns both the `Key` (GUID) and the numeric `Id`
(`OrganizationUnitId`) in one response, so both representations come from one call.

### Re-releasing is an in-place upgrade. Never uninstall

`deploy run` with the **same deployment name** and a new `--package-version` upgrades that
deployment in place: one folder throughout, the same folder key, no duplicate processes. Reusing the
name is the correct path for a re-release, not a hazard.

**`uninstall` deletes the folder and everything provisioned in it** — which now includes the
ontology's Data Fabric entities, because they live in this folder. Uninstalling in order to
re-release destroys the author's data. There is no situation in this pipeline where it is the right
move.

## Phase 4: Await every release

```bash
scripts/await_release.py {ProcessName} {version} --folder-path "{PARENT}/{deployment-name}"
```

`await` polls for up to ten minutes and distinguishes three outcomes.

| Outcome | Meaning | What to do |
|---|---|---|
| `ready` | the release in that folder is on the expected version | proceed |
| `stale` | the release exists on an older version | keep polling; a timeout means the deploy did not take |
| `missing` | no release by that name in the folder | fail at once; the reported `available` list is the diagnosis |

**Nothing may invoke an action until its release reports `ready`.** A stale release is
indistinguishable from a fresh one at the API surface, and invoking against one faults with
`JsCodedFunction.ValidationFailed`: the contract moved, the deployed job did not.

Await every release, not just the one that changed. A publish moves every job in the Solution.

## Phase 5: Hand back to the caller

Return the folder the deployment created and the release inventory. The action TTLs are handed back
unchanged: nothing in them names a folder, so there is nothing to patch.

```text
FOLDER:         name, path, key, numeric id -- the folder the deployment created
RELEASE:        package name, version, deployment name
AWAIT_RESULTS:  process name -> ready | stale | missing, one line per release
```

The caller needs the folder **key** next, because the ontology is created against it and the Data
Fabric entities go inside it. Both representations come from one `uip or folders get`.

**This skill has succeeded when the folder exists and every release reports `ready`.** Anything less
is reported as what it is: a green release in a folder nothing is bound to yet is not a completed
deploy, and neither is a folder whose releases are still stale.

## Scripts

All emit JSON on stdout, put errors on stderr, and exit non-zero on failure. python3, standard
library only, no shell.

One script per action. Each answers `--describe` with its own contract as JSON, so what it takes
and returns comes from the script rather than from this table:

```bash
python3 scripts/<script>.py --describe
```

| Script | Phase | What it does | Mutates |
|---|---|---|---|
| `stage_jobs.py` | 2 | Stage each job as `main.ts`, derive its manifest, set its functions map, strip install inputs | no |
| `publish_package.py` | 3 | Enforce the next version, pack, and upload to the tenant feed | **yes** |
| `deploy_release.py` | 3 | Deploy a version, creating the folder or upgrading the deployment in place | **yes** |
| `await_release.py` | 4 | Poll a release until ready, stale, or missing | no |

Phase 1 has no script; it is two `uip` commands and one small file, documented above. Phase 5 has
none either: it is what you report. There is a script only where a plain command would let a failure
through silently.

Three private modules sit behind them: `_uip.py` (the CLI boundary), `_solution.py` (reading
solution state) and `_staging.py` (the staging tree, the derived manifest, the stripping). They are
not entry points; nothing invokes them directly.

`await_release.py` needs no `SOLUTION_SRC`: it asks the tenant about a release, not the source tree
about a solution.

## When something breaks

Read `references/failure-signatures.md`. Several failures here are actively misleading: a job that
faults with a message naming nothing about dependencies, a release that validates and faults only at
invoke, a publish that succeeds and changes nothing, a guard refusal that reads like a no-op.
Recognising them is faster than re-deriving them.

`references/pipeline.md` has the shape of each value and the reasoning behind the deploy-first
ordering.

## Boundaries

- Never upload an ontology artifact. Hand the paths back and let authoring upload them.
- Never republish an existing version, and never invoke without `await` reporting `ready`.
- **Never uninstall a deployment to re-release it.** That deletes the folder and the ontology's
  entities inside it. Re-release by reusing the deployment name with a new version.
- Never point a deployment at an existing folder. It cannot; it will make a second one beside it.
- Never take an org or a tenant from user-supplied text. `uip login status` is the only source.
- Never write a placeholder job source to get past the stage guard. The refusal is the finding.
- Do not duplicate `uip solution` or `uip functions` syntax here. Reference the sibling skills.
