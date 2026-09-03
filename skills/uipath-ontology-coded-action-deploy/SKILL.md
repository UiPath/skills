---
name: uipath-ontology-coded-action-deploy
description: "Use when an ontology's coded actions have been generated and their Orchestrator leg needs shipping: scaffolding the jobs Solution, staging each job source, publishing and deploying a new release, and patching the resolved folder id into every action TTL. Use when action TTLs still carry ont:processFolderId \"PENDING_DEPLOY\". Do not use to generate ontology artifacts, to upload any artifact to the ontology backend, or for existing-ontology CRUD. For artifact generation→uipath-ontology-modeler. For backend validation and artifact upload→uipath-ontology-authoring. For `uip ont` syntax→uipath-ontologies."
when_to_use: "Coded-action TTLs and their job sources exist and the jobs must reach Orchestrator; user says 'deploy the coded actions', 'ship the jobs', 'publish a new release of the jobs solution', 'the TTLs still say PENDING_DEPLOY', 'the job changed, release it again'."
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
| coded-action pairs | one per action: a TTL carrying `ont:processFolderId "PENDING_DEPLOY"`, and the job source that implements it |

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

`publish_package.py`, `deploy_release.py` and `patch_action_ttl.py` print the exact command or the
exact change and do nothing without `--execute`. Show the printed plan, get an explicit yes, then
re-run with `--execute`. Publish and deploy write to a live tenant and move every job in the
Solution onto one version line, so the version transition (`1.0.2` to `1.0.3`, and which processes
move) is what to show.

`stage_jobs.py`, `resolve_folder_id.py` and `await_release.py` are read-only or
temp-directory-only. Run them freely; staging is the cheapest proof that a job change reaches the
tree and that its contract lowers to a manifest.

## Service dependency

Coded-action semantics, meaning an action whose `ont:language` is the wire literal `"IMPERATIVE"`,
require an ontology service build that supports them. Uploading the artifact does not: the upload
leg accepts the TTL either way, and the action then resolves to nothing at invoke time. So a green
run of this skill against a service without that support produces a correct folder id, a real
release, and an action that cannot be invoked. Say so rather than reporting the deploy as complete
proof the action works.

## Phase 1: Create the jobs Solution

One Solution per ontology, named `{name}-jobs`, one Function project per coded action. There is no
script for this phase: it is four `uip` commands and two small files, and `uip solution` and
`uip functions` already document the commands. What is written here is the order, because the order
is not obvious and two of the steps fail quietly if it is wrong.

Reuse an existing solution directory and existing project directories; create only what is missing.

```bash
cd {workdir}
uip solution init {name}-jobs
cd {name}-jobs

# 1. .npmrc FIRST -- see below. Same content in the solution root and in each project.
cat > .npmrc <<'EOF'
@uipath:registry=https://npm.pkg.github.com/
//npm.pkg.github.com/:_authToken=${GH_NPM_REGISTRY_TOKEN}
EOF

# 2. one project per coded action, PascalCase(actionName) + "Process"
uip functions new {ActionName}Process --language ts --empty

# 3. register it, or the package will not contain it
uip solution projects add ./{ActionName}Process ./{name}-jobs.uipx
```

**`.npmrc` must exist before `uip functions new`.** That command shells out to an installer, and
the `@uipath` scope resolves from GitHub Packages rather than npmjs, so without the file it fails
with `GET https://registry.npmjs.org/@uipath%2fcoded-functions-js-sdk - 404`. The project directory
is still created, which makes the failure easy to miss. Nothing later in the pipeline installs
anything -- the SDK is a devDependency for local typechecking, `type<T>()` is erased at compile
time, and `defineFunction` comes from the runtime -- so a 404 here is the only place the token
matters. The token stays an `${GH_NPM_REGISTRY_TOKEN}` reference; a literal never goes in the file.

**`--empty`, not the hello-world default.** A scaffolded sample job is a second copy of the entry
point, free to drift from the job source phase 2 stages in.

**`projects add` is not optional.** It writes the `.uipx` `Projects` entry and generates the
`resources/solution_folder/**` descriptors that make the release a job rather than an HTTP
endpoint. A project directory that exists but was never added is absent from the package, and the
package still builds. `stage_jobs.py` refuses in that case, naming the project.

Then map each project to the job that supplies its code, in `{name}-jobs/jobs.map.json`:

```json
{
  "projects": { "{ActionName}Process": "../jobs/{action}.ts" }
}
```

Paths resolve against that file's own directory, so a job living beside its action TTL one level up
is `../jobs/{action}.ts`. This is what phase 2 stages from, and the only place the pairing is
recorded.

**Do not hand-edit `uipath.json`.** `uip functions new --empty` leaves `"functions": {}`, and
`uip solution pack` reports `No functions defined in uipath.json` and produces nothing. Phase 2
writes that map into the staging copy, because the map, the staged source and the manifest all have
to name the same file -- setting it here means it can drift from what is actually staged, and
setting it by hand means it can be forgotten.

**Verified end to end offline.** These commands plus phase 2 produce a package whose per-project
nupkg is `{Solution}.Function.{Project}.{version}.nupkg` carrying `content/main.ts` and
`content/entry-points.json`, which is the shape a Studio Web export produces. `uip solution init`
is also where the fresh `SolutionId` comes from.

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

## Phase 3: Version, publish, deploy

```bash
scripts/publish_package.py {version}                     # dry run: reports current, next, target
scripts/publish_package.py {version} --execute           # tenant feed
scripts/deploy_release.py  {version} {name}-jobs-{version-dashed} --execute
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

A local zip needs no script: `stage_jobs.py` prints its staging path and leaves the tree in place,
so `uip solution pack <staging> /tmp/pk -n {name}-jobs -v {version}` produces one without touching
the tenant.

**`publish` is asynchronous.** The script passes `--wait`. Deploying before the publish completes
fails with a package-not-found error that never mentions publishing.

**A new version means a new deployment, not an upgrade.** `deploy run` creates a deployment plus a
new Orchestrator folder rather than upgrading one in place, so `ont:processFolderId` goes stale on
every release and phase 5 is not optional. Deploying a version that is already live is a no-op that
reports the existing folder rather than creating a second one. The CLI surface lists a
`deploy upgrade` subcommand that no verified run has used; `references/pipeline.md` records it as
the one remaining unverified path, and folder-per-version is what to assume until it is tested.

**The folder must be created under `Shared`.** A folder created at the root has no user with
unattended robot permissions, the job cannot start there, and the invoke reports only
`"Unexpected error"` on the `Running job` step with no job record at all.
`PARENT_FOLDER_PATH` defaults to `Shared` for this reason.

Name the deployment after the version so which folder is which stays obvious. Old deployments are
left running their old version, which is what makes a rollback a one-line TTL edit.

## Phase 4: Resolve the folder and await every release

```bash
scripts/resolve_folder_id.py "Shared/{deployment}"      # -> {folderId, folderKey}
scripts/await_release.py {ProcessName} {next} --folder-path "Shared/{deployment}"
```

`deploy run` reports a folder path and the TTL needs the numeric id, which is why `folder-id`
exists: it lists the folder's processes and reads `OrganizationUnitId` from
`uip or processes get --all-fields`, the one place the numeric id is exposed (`uip or folders get`
takes only a GUID or key, never a path). `deploy --execute` prints it too.

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

## Phase 5: Patch the TTLs

One call per action TTL, with the folder id phase 4 resolved.

```bash
scripts/patch_action_ttl.py {workdir}/{name}-{action}.ttl --folder-id {folderId} --execute
```

`ont:process` is never touched: a release is matched on Name or ProcessKey and never on version, so
the process name survives a new release and only the folder moves.

The script refuses when `ont:processFolderId` is absent, and when it appears more than once. Both
refusals are deliberate and neither is to be worked around: an absent predicate means this is not a
coded-action TTL, and a duplicated one means two definitions of the action merged in RDF and
editing either is guesswork. It is idempotent, so a file already carrying the value is a reported
no-op rather than a rewrite.

Skipping this phase is the quiet failure: the new release exists, the action still names the old
folder, the invoke succeeds, and the old code runs.

## Phase 6: Hand back to the caller

Return the patched TTL paths and the release inventory. Authoring uploads them in its Tier 2; this
skill does not.

```text
PATCHED_TTLS:   absolute path per action
RELEASE:        package name, version, deployment name, folder id, folder key
AWAIT_RESULTS:  process name -> ready | stale | missing, one line per release
```

**This skill has succeeded when every TTL carries a real folder id and every release reports
`ready`.** Anything less is reported as what it is. A patched TTL beside a stale release is not a
completed deploy, and neither is a green release beside a TTL that still says `PENDING_DEPLOY`.

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
| `stage_jobs.py` | 2 | Stage each job as its project's `main.ts`, derive its manifest, set its functions map | no |
| `publish_package.py` | 3 | Enforce the next version, pack, and upload to the tenant feed | **yes** |
| `deploy_release.py` | 3 | Deploy a published version into a new Orchestrator folder | **yes** |
| `resolve_folder_id.py` | 4 | Resolve a folder path to its numeric `OrganizationUnitId` | no |
| `await_release.py` | 4 | Poll a release until ready, stale, or missing | no |
| `patch_action_ttl.py` | 5 | Replace the `PENDING_DEPLOY` placeholder with the resolved folder id | **yes** |

Phase 1 has no script; it is four `uip` commands and two small files, documented above. There is a
script only where a plain command would let a failure through silently.

Three private modules sit behind them: `_uip.py` (the CLI boundary), `_solution.py` (reading
solution state) and `_staging.py` (the staging tree and the derived manifest). They are not entry
points; nothing invokes them directly.

The two phase-4 scripts need no `SOLUTION_SRC`: they ask the tenant about a folder or a release,
not the source tree about a solution.

## When something breaks

Read `references/failure-signatures.md`. Several failures here are actively misleading: a release
that validates and faults only at invoke, a publish that succeeds and changes nothing, a guard
refusal that reads like a no-op. Recognising them is faster than re-deriving them.

`references/pipeline.md` has the shape of each value and the reasoning behind the folder-per-version
model.

## Boundaries

- Never upload an ontology artifact. Patch the file, return the path, let authoring upload it.
- Never republish an existing version, and never invoke without `await` reporting `ready`.
- Never take an org or a tenant from user-supplied text. `uip login status` is the only source.
- Never write a placeholder job source to get past the stage guard. The refusal is the finding.
- Do not duplicate `uip solution` or `uip functions` syntax here. Reference the sibling skills.
- Report a spike-pending path as unverified rather than as working. `uip solution deploy upgrade`
  is the one currently in that state.
