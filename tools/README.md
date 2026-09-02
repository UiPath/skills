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
`input-strictness`, `writes-cover-edits`, `fields-exist-in-schema`, `folder-id-status`,
`job-language`, `typecheck`.
A gate reports `passed`, `failed`, or `skipped` (a skip carries its reason and never counts as a
pass); the exit code is 0 only when nothing failed. `folder-id-status` never fails: it reports
whether `ont:processFolderId` is still the `PENDING_DEPLOY` placeholder, which callers sequence on
via `pairs[].deployable`.

Both job contract idioms are understood: zod (`input: z.object({...}).strict()`, what generation
emits) and `type<T>()` over plain interfaces (Studio-Web-only packing). `input-strictness` requires
the top-level input z.object to carry `.strict()`, the source of `additionalProperties: false` in
the packed schema; a `type<T>()` contract passes it with a note, since the SDK derivation supplies
the flag itself. The typecheck gate compiles the job against a stub of the Coded Functions SDK and
is skipped, with a reason, when no TypeScript compiler is available (set `CODED_ACTION_TSC` to
point it at one) or, for a zod-idiom job, when zod is not resolvable from the workdir upward.

Keep these utilities at the repository level. Do not place them inside a consuming skill; doing so would create an unnecessary structural dependency between the skills.
