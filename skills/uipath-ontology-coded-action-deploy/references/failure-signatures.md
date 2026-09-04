# Failure signatures

Read this when something breaks. Several failures in this system are actively misleading: they
present as a different problem than they are, and the obvious diagnosis is the wrong one. Each
entry gives the symptom, the real cause, and the command that distinguishes it.

## Every job faults with `Serverless.JsFunction.PrepareEnvironmentError`

```
ErrorCode: Serverless.JsFunction.PrepareEnvironmentError
Info:      Failed to prepare environment
```

and the invoke shows only `Orchestrator job for process '...' ended in state Faulted`. Neither
message says anything about dependencies, which is why this costs a cycle.

The serverless runtime runs a prepare step that installs whatever the project's `package.json`
declares. `uip functions new` declares the SDK as a devDependency, the runtime cannot resolve the
`@uipath` scope, and the prepare step fails before the handler is ever reached — so **every** job in
the package faults, not one.

`stage_jobs.py` strips every dependency block, the `.npmrc` and any lockfile from the staged copy,
so a package built through `stage` cannot hit this. Seeing it means something packed a tree that did
not go through `stage`, or a dependency was added back. Nothing is lost by having none: `type<T>()`
is erased at compile time and `defineFunction` comes from the runtime.

## `GET https://registry.npmjs.org/@uipath%2f... - 404` during `uip functions new`

Expected, and harmless. The install runs inside the project directory the command is in the middle
of creating, so no `.npmrc` written beforehand can reach it, and the `@uipath` scope is not on
npmjs. The project directory is still created and nothing downstream needs the SDK installed —
staging removes the dependency anyway. Do not chase it, and do not add
`GH_NPM_REGISTRY_TOKEN` to make it go away: a staged `.npmrc` carrying an unexpanded
`${GH_NPM_REGISTRY_TOKEN}` reaches the runtime as a literal string and is useless there.

## `Project already exists in solution: X/uipath.json`

`uip functions new`, run inside a solution directory, writes the `.uipx` `Projects` entry itself, so
a separate `uip solution projects add` is redundant and fails. Drop the command and verify instead:
every project appears in the `.uipx` `Projects` array.

## `Entity 'X' has no identity property` on `Preparing write statement`

The write is refused **after the job has already run**, and reports `rowsAffected: 0` — which in a
summary is indistinguishable from a legitimate no-op.

The class has no data property annotated `ont:datatype "key"`. Property kind is annotation-only and
is never inferred from the XSD range, so a schema written without that annotation gives every class
a TEXT-only property set and no identity at all. The artifact uploads, validates and deploys
cleanly; this is the first thing that notices.

Fix in the schema, not the job: declare `{Class}.id`, annotate it `"key"`, range `xsd:string`, and
bind it in the mapping to `$(Id)`. `coded_action_preflight.py`'s `entity-identity-declared` gate
catches it offline.

## `Parameter value contains illegal control character at position N`

A `\n`, `\t` or `\r` in a written value fails the whole statement, after the job has run. An
append-style audit trail must join with a visible separator (` | `) rather than a newline.

## `No Orchestrator process named 'X' in Orchestrator folder N`

The ontology is bound to a folder that has no processes. Almost always this is a deployment that
was pointed at a folder name that already existed: `deploy run` cannot target an existing folder,
so it created `<name> 1` and put the processes there, leaving the original folder — the one the
ontology names — empty.

Check which folder actually holds the releases (`uip or processes list --folder-path …`), and
remember that the deployment creates the folder: everything else follows it, rather than the other
way round.

## `error: missing required argument 'fileName'` from `artifact validate`

`validate` takes the artifact-name positional exactly as `upsert` does:

```bash
uip ont artifact validate {name} {fileName} --type … --media-type … --file …
```

Without it the call fails, but the response still parses — so a naive check reads it as a validation
failure and sends the session hunting a phantom artifact bug. Note also that the success field is
`Data.Valid`, capitalised; a lowercase read is always falsy.

## The job faults with `ValidationFailed` and your logs never appear

```
ErrorCode: JsCodedFunction.ValidationFailed
Info:      Input validation failed
           ticket.0.Tags: must have required property 'Tags'
```

The platform validates the job's input against the manifest before the handler runs, so nothing the
job would have logged exists. Read the `Info` field on the Orchestrator job — it names the exact
property — with:

```bash
uip or jobs list --folder-path "<PARENT>/<deployment>" --all-fields --output json
```

Two causes, and the message distinguishes them.

**`must have required property 'X'`** — the row interface declared `X`, and the read did not return
a column by that name. A `SELECT *` read's physical column shape is not knowable at authoring time:
the same entity answered `Tags` through the Data Fabric records API and its schema field name
through the ontology's read. A row interface must therefore declare **no** fields, only
`[column: string]: unknown`, and the handler picks columns defensively. Fix the job, not the entity.

**A renamed or extra top-level input field** — the marker and the job's `Input` have drifted apart.
`coded_action_preflight.py`'s `input-matches-marker` catches this offline; reaching it at runtime
means preflight was skipped.

The third cause is a **stale release**: the deployed job is older than the contract. Check the
version rather than assuming.

```bash
scripts/await_release.py <ProcessName> <expected-version> --folder-path "<PARENT>/<deployment>"
```

## `await` says `missing` when you expected `stale`

They are different failures and the fix differs.

| Outcome | What it means | Fix |
|---|---|---|
| `stale` | the release exists in that folder on an older version | the deploy has not taken yet, or it went to a different folder. Keep polling; on timeout check `deploy list`. |
| `missing` | no release by that name in that folder at all | the folder id is wrong, or the project never made it into the package. The reported `available` list is the diagnosis: if the other releases are there and yours is not, the project is missing from the manifest. |

A `missing` right after a successful deploy usually means the folder path names the previous
deployment. Await against `"Shared/<new-deployment>"`, and re-resolve the id with
`folder-id "Shared/<new-deployment>"`.

## The job deployed fine but the action faults, and the source looks right

Check what actually got packed. `uip solution pack` reports `Status: Valid` for a project whose
job source is **missing or 0 bytes**, and builds a package containing an empty function. Nothing
fails until invoke time. A Studio Web export shipped exactly that: a 0-byte entry point.

`stage_jobs.py` refuses both cases, so prefer it over `uip solution pack` and never
pack the solution directory directly. To confirm after the fact, unzip the package and look inside
the per-project nupkg. The job belongs at `content/main.ts`:

```bash
scripts/stage_jobs.py          # prints its staging path
uip solution pack <staging> /tmp/pk -n <SolutionName> -v <version>
cd /tmp/pk && unzip -q <SolutionName>_<version>.zip
unzip -p files/*/<SolutionName>.Function.<ProjectName>.<version>.nupkg 'content/main.ts' | head
```

## `No functions defined in uipath.json`

The project's `uipath.json` functions map does not name the staged source. It has to read
`{"main": "main.ts:default"}`, matching the `main.ts` that `stage` writes and the
`filePath: content/main.ts` in the derived manifest; those three have to agree. `stage` writes the
source, the manifest and the map together, in the staging copy, so seeing this means
`uip solution pack` was run on a tree that did not go through `stage`.

Note this error belongs to `uip functions pack`, which this pipeline does not run. Reaching it
means something invoked that command directly.

## `entry-points.json not found. Run 'uipath-functions pack' to generate it.`

`uip solution pack` was run without the per-project functions pass. `uip solution pack` never
generates `entry-points.json`, and the error's suggested command names a binary
(`uipath-functions`) that does not exist on PATH. `stage_jobs.py` derives the manifest
for every staged project with `tools/entry_points.py`, so seeing this error means something called
`uip solution pack` on a tree that did not go through `stage`. Go through the script.

## `Manifest extraction failed. A function declares a type<T>() contract ...`

Something ran `uip functions pack`. It cannot lower the `type<T>()` idiom to a JSON Schema on any
tested SDK version (0.4.4, 0.5.0, 0.6.4), and pinning a different version does not help; only
Studio Web's packer carries that derivation walker. This pipeline does not run `uip functions
pack` for exactly this reason. `stage` derives the manifest from the job's interfaces instead, so
the fix is to go through the script rather than to rewrite the contract.

If the deriver itself refuses a contract (`cannot lower type ...`), that is the same wall reached
earlier and on purpose: the type is outside the grammar the contract guide mandates. Narrow the
interface to that grammar rather than hand-writing a manifest, because a manifest that disagrees
with the interfaces faults the job before its handler runs.

## `GET https://registry.npmjs.org/@uipath%2f... - 404` during scaffolding

The `@uipath` npm scope is on GitHub Packages, not npmjs. The project needs an `.npmrc` mapping
the scope to `https://npm.pkg.github.com/` with `${GH_NPM_REGISTRY_TOKEN}` as the token reference,
and the environment needs `GH_NPM_REGISTRY_TOKEN` exported. Phase 1 writes that `.npmrc`
**before** `uip functions new`, because that command installs; a 404 means either the file was
written after the command, or the token is missing from the environment.

This can only happen during scaffolding, when `uip functions new` installs. Stage, pack, publish
and deploy run no installer: the SDK is a devDependency for local typechecking, `type<T>()` is
erased at compile time, and `defineFunction` comes from the runtime. A 404 from those phases means
something is running a command this pipeline does not.

## `stage` refused and the run reports as clean

It did not run. The guard refusals are:

```
mapped job source missing: ...
mapped job source is empty: ...
<Project>/functions holds no .ts source and the project is not in jobs.map.json; pack would publish an empty function
<Project>/functions/<file>.ts is empty; pack would publish an empty function
```

Every one exits non-zero. Reporting a run as complete when a guard stopped it is the worst possible
outcome, because the failure it prevents is silent: a package that publishes cleanly and faults
only at invoke time. Fix the job source; do not write a placeholder to get past it.

## A guard refusal read as a no-op

`rowsAffected: 0` with no failed step is not an error: the job chose to write nothing. A refusal
also reports zero. Distinguishing them matters and both look the same in a summary.

| What you see | Which it is |
|---|---|
| all steps OK, `rowsAffected: 0` | genuine no-op. The job's target state already held. |
| `Preparing write statement` failed, `SQL_GUARD_REJECTED` | refusal. The job returned an edit outside `ont:writes`, after running, with nothing written. |

The step trace is the whole diagnosis. Report it verbatim rather than summarising it to a row count.

## `deploy run` says the package version does not exist

`publish` must complete first, and it is asynchronous. The error does not mention publishing.
Re-run `publish_package.py <version>` without `--execute`; its dry run reports the current and
next version, and refuses outright if the version is not the next one.

## `HTTP 400: <version> version already exists for this package`

Usually means the publish **succeeded** and something retried. `uip solution publish --wait`
uploads and then polls; a retry after a successful upload reports the conflict, so the failure is
reported for a version that is now live in the feed. Do not bump the version on the strength of
this error. Check what actually landed first:

```bash
uip solution packages list --output json
uip solution packages download <SolutionName> <version> -d /tmp/p.zip
```

`LatestVersion` plus a `PublishDate` matching your attempt is the tell. Downloading and diffing the
nupkg's `content/main.ts` against the job source is the proof.

## A publish and a deploy both reported success and nothing changed

The version number was one that already existed. This is the single most expensive trap in the
pipeline, because every surface reports success: publish returns a package version key, deploy
reports Successful, `deploy list` shows the deployment on that version, and the running code is
whatever it was before.

`publish_package.py` computes `next = current + 1` from the live deployment, filtering
tombstones, and refuses any other version unless `--force-version` is passed. That refusal is the
only thing between this trap and a release that reports success and changes nothing.

## The UI still shows the old version after a successful publish

Expected, and not a publish problem. Publishing adds a package version to the feed; a deployment
then has to run on it. `uip solution deploy list` shows `CurrentPackageVersion` (running) beside
`NewPackageVersionAvailable` (published, not taken).

`deploy run` with the same deployment name and a new version upgrades that deployment in place, so
nothing is repointed: the folder does not move and no artifact names it.

## `Unexpected error` on the `Running job` step, and zero jobs in the folder

The folder has no user with unattended robot permissions, so the job never starts. The invoke
reports a bare `"Unexpected error"`, which says nothing; ask Orchestrator directly and it does:

```
HTTP 409  errorCode 1671
"Couldn't find any user with unattended robot permissions in the current folder."
```

The tell is `rowsAffected: 0` with `Reading context` OK (so the read and the TTL are fine) and no
job record in the folder at all; a job that started and faulted would leave one.

This is what a solution folder created at the ROOT looks like. Deploy under `Shared` instead so the
folder inherits its assignments; `PARENT_FOLDER_PATH` defaults to that. A folder's own record is no
help in diagnosing it: root and Shared-child folders are identical in `FolderType`,
`ProvisionType`, `PermissionModel` and `IsActive`.

## `version` names a deployment that no longer exists

An uninstalled deployment stays in `uip solution deploy list` as a tombstone: `Operation:
Uninstall`, `ActivationStatus: None`, and only a `Delete` action left. It still carries a
`CurrentPackageVersion`, so anything taking the first match reports a plausible version for a dead
record that owns no folder, and `next` is then computed from the wrong release.

`_solution.version_info` filters tombstones and picks the highest live version. The tell is a
`deployment` whose `activation` is `None` and whose `actions` are just `["Delete"]`. Only the UI
can clear the row.

## Publishing bumped a process you did not touch

Expected. Every coded-action job for one ontology lives in one Solution package, so a publish moves
all of them onto the same version line. This is why the publish step is gated and why `await` runs
against every release rather than only the one that changed.

## `HTTP 400: Project with name '<name>' not found` on publish

`projectName` error 2003, `RetryWillNotFix`. Something is calling
`uip solution projects publish --project-name <name>`, which publishes an existing *cloud* solution
project; that flag wants a Studio Web project name, and the name you passed is the deployment and
package name, a different namespace. `publish_package.py` packs from `SOLUTION_SRC`
instead and needs no cloud project. If you see this error, something is calling `uip` directly.
