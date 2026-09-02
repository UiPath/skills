# Failure signatures

Read this when something breaks. Several failures in this system are actively misleading: they
present as a different problem than they are, and the obvious diagnosis is the wrong one. Each
entry gives the symptom, the real cause, and the command that distinguishes it.

## The job faults with `ValidationFailed` and your logs never appear

The SDK validates input against the job's `Input` type with `additionalProperties: false`, before
the handler runs. So this is a contract mismatch, not a bug in the handler: a field the marker
declares and the job does not, or the reverse.

The other cause, and the one this skill owns, is a **stale release**: the deployed job is older
than the contract. Check the version rather than assuming.

```bash
scripts/solution_release.py await <ProcessName> <expected-version> --folder-path "Shared/<deployment>"
```

Three consecutive faults of this shape came from invoking before the release had moved. Await is
the guard; a run that skipped it has not ruled this out.

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

`solution_release.py stage` refuses both cases, so prefer it over `uip solution pack` and never
pack the solution directory directly. To confirm after the fact, unzip the package and look inside
the per-project nupkg. The job belongs at `content/main.ts`:

```bash
scripts/solution_release.py pack <version> /tmp/pk
cd /tmp/pk && unzip -q <SolutionName>_<version>.zip
unzip -p files/*/<SolutionName>.Function.<ProjectName>.<version>.nupkg 'content/main.ts' | head
```

## `No functions defined in uipath.json`

The project's `uipath.json` functions map does not name the staged source. It has to read
`{"main": "main.ts:default"}`, matching the `main.ts` that `stage` writes and the
`filePath: content/main.ts` in the derived manifest; those three have to agree. `stage` writes the
source and the manifest, and `solution_scaffold.py` writes the map, so seeing this means the map
was edited or the project came from somewhere other than the scaffold.

Note this error belongs to `uip functions pack`, which this pipeline does not run. Reaching it
means something invoked that command directly.

## `entry-points.json not found. Run 'uipath-functions pack' to generate it.`

`uip solution pack` was run without the per-project functions pass. `uip solution pack` never
generates `entry-points.json`, and the error's suggested command names a binary
(`uipath-functions`) that does not exist on PATH. `solution_release.py stage` derives the manifest
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
and the environment needs `GH_NPM_REGISTRY_TOKEN` exported. `solution_scaffold.py` writes the
`.npmrc`; a 404 after scaffolding means the token is missing from the environment.

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
Re-run `solution_release.py version` and confirm the version is actually present before deploying.

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

Always compute `next = current + 1` from the deployment. `solution_release.py version` does that,
including filtering tombstones.

## The UI still shows the old version after a successful publish

Expected, and not a publish problem. Publishing adds a package version to the feed; a deployment
then has to run on it. `uip solution deploy list` shows `CurrentPackageVersion` (running) beside
`NewPackageVersionAvailable` (published, not taken).

The CLI's `deploy run` creates a new deployment rather than upgrading one, so the pipeline deploys
into a new folder under `Shared` and repoints `ont:processFolderId` at it.

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

`solution_release.py` filters tombstones and picks the highest live version. The tell is a
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
package name, a different namespace. `solution_release.py publish` packs from `SOLUTION_SRC`
instead and needs no cloud project. If you see this error, something is calling `uip` directly.

## `ttl_patch.py` refused

Two refusals, both deliberate.

| Refusal | Cause | Fix |
|---|---|---|
| `ont:processFolderId not found` | not a coded-action TTL, or generation never emitted the `PENDING_DEPLOY` placeholder | check the file is the right one. If it is, the generation step is the bug; that belongs to the modeler. |
| `ont:processFolderId appears N times` | two definitions of one action merged in RDF | the artifact has duplicated subjects. Editing either occurrence is guesswork, and RDF unions the writes of both, so a duplicate silently widens permissions. Deduplicate at the source. |

A no-op report is not a refusal: the file already carried the requested id, and that is a pass.
