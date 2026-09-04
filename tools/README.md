# Shared Ontology Tools

This directory contains repository-level utilities shared by the UiPath ontology skills.

Keep them here. CLAUDE.md forbids a skill reading another skill's files, and each of these has
more than one consumer, so moving one inside a skill would create exactly that dependency.
`tools/` is on `package.json`'s `files` list because a shipped script hard-requires it.

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

The same, for coded-action pairs: a `{workdir}/{ontology}-{action}.ttl` declaring
`ont:language "CODED"` beside its job at `{workdir}/jobs/{action}.ts`. It cross-checks the two
against each other and against the ontology's `.ofn`, which is the offline authority on which
entities and fields exist. It calls no service and modifies nothing.

```bash
python3 tools/coded_action_preflight.py \
  --workdir <ontology-workdir> \
  --ontology-name <ontology-name> \
  [--action <actionName>]... [--skip-typecheck]
```

Ten gates, each reporting `passed`, `failed` or `skipped` — a skip carries its reason and never
counts as a pass — with exit 0 only when nothing failed. `--describe`-style detail is not
duplicated here: the gate list is in the payload, and what each one enforces and why is in
`uipath-ontology-modeler`'s `references/coded-action-contract-guide.md`.

No gate reports deployment readiness, because nothing in an action names where its job is
deployed. The artifact is portable; the folder is resolved at invoke time.

Implementation is in `coded_action/` — turtle lexing, the action model, job-source scanning, the
deriver bridge, pair discovery, typecheck, the verdict shape, the gates — with the CLI as the only
public surface.

## `entry_points.py`

Lowers a job's TypeScript contract into the Functions `entry-points.json` manifest.

```bash
python3 tools/entry_points.py JOB.ts                      # print the manifest
python3 tools/entry_points.py JOB.ts --out entry-points.json
python3 tools/entry_points.py JOB.ts --check MANIFEST     # compare, exit 1 on drift
```

`type<T>()` is inert at runtime, so the schema the platform validates against has to come from
somewhere: Studio Web's packer derives it and `uip functions pack` refuses the idiom outright. This
does that derivation, which keeps the interfaces the single source of truth and the pipeline on
`uip solution pack`. The deploy skill's staging step and `coded_action_preflight`'s
`input-strictness` gate are both callers.

Output is byte-identical to Studio Web's for the two verified jobs, committed as goldens under
`tests/tasks/uipath-ontology-modeler/_shared/fixtures/entry-points/` — the only evidence of what
the platform accepts. The lowerable grammar, and why anything outside it is refused rather than
approximated, is in the contract guide.

`--out` preserves an existing entry point's `uniqueId`, which the project's bindings reference.
`--check` re-derives and compares, catching a manifest edited by hand or left behind by an
interface change.
