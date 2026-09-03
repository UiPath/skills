# Shared Ontology Tools

This directory contains repository-level utilities shared by the UiPath ontology skills.

## `ontology_preflight.py`

`ontology_preflight.py` is the neutral, dependency-free validator for ontology artifact workdirs. It is shared by:

- `uipath-ontology-authoring`, which owns deployment orchestration and invokes preflight before backend creation or upload;
- `uipath-ontology-modeler`, which uses it to validate locally generated artifacts before handing them back.

The validator does not log in, call UiPath Cloud, create ontology stubs, upload files, or change user data. It reports JSON gates and an exact artifact inventory.

Run it from the repository root:

```bash
python3 tools/ontology_preflight.py \
  --workdir <ontology-workdir> \
  --ontology-name <ontology-name> \
  --mapping-mode auto
```

## `coded_action_preflight.py`

`coded_action_preflight.py` is the neutral, dependency-free validator for coded-action pairs: a
`{workdir}/{ontology}-{action}.ttl` declaring `ont:language "IMPERATIVE"` plus the job at
`{workdir}/jobs/{action}.ts`. It cross-checks the two files against each other and against the
ontology's `.ofn` schema, which is the offline authority on which entities and fields exist. It
does not log in, call UiPath Cloud, upload anything, or modify the workdir.

```bash
python3 tools/coded_action_preflight.py \
  --workdir <ontology-workdir> \
  --ontology-name <ontology-name> \
  [--action <actionName>]... [--skip-typecheck]
```

Gates: `ttl-parses-and-well-formed`, `signature-resolves`, `input-matches-marker`,
`input-strictness`, `writes-cover-edits`, `fields-exist-in-schema`,
`job-language`, `typecheck`.
A gate reports `passed`, `failed`, or `skipped` (a skip carries its reason and never counts as a
pass); the exit code is 0 only when nothing failed.

Whether an action is ready to deploy is NOT a gate, and deliberately: the `PENDING_DEPLOY`
placeholder is the expected state between generation and deploy, so there is nothing to fail on.
It is reported per pair as `pairs[].deployable`, with the reason in `warnings`. Callers sequence
on that field, not on a gate status.

Contracts are declared with `type<T>()` over plain interfaces. `input-strictness` runs
`entry_points.py` and inspects what it derives, so it checks the property that actually matters --
that the input schema carries `additionalProperties: false` -- rather than assuming the SDK will
supply it. A contract the deriver cannot lower fails here, at authoring time, instead of at pack
time with nothing written.

A Standard-Schema contract (zod, arktype, valibot) fails that gate by design: it carries its own
schema and so cannot be lowered into the manifest the deploy step stages. The diagnostic names the
library and the consequence.

The typecheck gate compiles the job against a stub of the Coded Functions SDK, and is skipped with
a reason when no TypeScript compiler is available (set `CODED_ACTION_TSC` to point it at one). The
job imports nothing but the SDK, and the SDK is stubbed, so no package needs installing.

Implementation lives in `coded_action/` -- turtle lexing, the action model, job-source scanning,
the deriver bridge, pair discovery, typecheck, the verdict shape, and the gates -- with this file's
CLI as the only public surface.

## `entry_points.py`

Lowers a job's TypeScript contract into the Functions `entry-points.json` manifest.

```bash
python3 tools/entry_points.py JOB.ts                      # print the manifest
python3 tools/entry_points.py JOB.ts --out entry-points.json
python3 tools/entry_points.py JOB.ts --check MANIFEST     # compare, exit 1 on drift
```

`type<T>()` is inert at runtime, so the schema the platform validates against has to come from
somewhere. Studio Web's packer derives it from the interfaces; `uip functions pack` cannot and
refuses outright on the idiom. This tool does that derivation, which keeps the interfaces as the
single source of truth and keeps the pipeline on `uip solution pack`, a command that only zips a
directory and reads no TypeScript.

The lowering reproduces byte-for-byte the manifests Studio Web produced for the two verified jobs;
those are committed as goldens under
`tests/tasks/uipath-ontology-modeler/_shared/fixtures/entry-points/` and are the only evidence of
what the platform accepts. The accepted grammar is `string`, `number`, `boolean`, a union of
string literals, `Record<string, unknown>`, an array of any of those, and interfaces declared in
the same file. An interface's `[key: string]: unknown` index signature lowers to a permissive
`additionalProperties`, which is what read rows need because `SELECT *` carries columns the job
never declared; its absence lowers to `additionalProperties: false`, which is what faults a
drifted input before the handler runs. Anything outside the grammar is refused rather than
approximated: a manifest that disagrees with the interfaces faults the job at invoke time.

`--out` preserves an existing entry point's `uniqueId`, which the project's bindings reference.
`--check` re-derives and compares, so a manifest edited by hand or left behind by an interface
change is caught.

Keep these utilities at the repository level. Do not place them inside a consuming skill; doing so would create an unnecessary structural dependency between the skills.
