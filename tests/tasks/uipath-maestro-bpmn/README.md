# Maestro BPMN Skill Eval Tasks

These tasks exercise the `uipath-maestro-bpmn` skill and its public-safe validation fixture corpus.

The layout mirrors the Flow eval suite:

- `smoke/` covers lifecycle and fixture smoke checks. `init_pack_validate.yaml`
  walks the CLI happy path; `validation_fixtures.yaml` validates the corpus;
  `validation_fixtures_pack.yaml` exercises the pack side of the same corpus;
  `imported_xml_inspect.yaml` treats the three complex fixtures as imported
  XML and produces an inspection report without mutating source.
- `author/` covers BPMN skeleton structure, gateways, sequence flows, and
  diagrams. `simple_approval_bpmn.yaml` composes the manual smoke "simple
  approval" matrix (StartAgentJob, gateway, CreateQueueItem, script task,
  variables, migration metadata, BPMN DI) in one task.
- `authoring/` covers implementation-matrix rows that should not be
  fixture-only: business rules, API workflow execution, and the script/Jint
  lifecycle path.
- `nodes/` covers task wrapper and script-task authoring behavior.
- `nodes/contract_variant_wrappers.yaml` covers public-safe Maestro BPMN XML
  contract variants from imported-wrapper parsing, including async call
  activities, message events, case-management shells, preserve-only payloads,
  and numeric migration metadata.
- `skills/uipath-maestro-bpmn/fixtures/validation/registry-coverage-matrix/`
  keeps the static fixture corpus aligned with the current registry wrapper
  surface without claiming cloud execution of resource-backed tasks.
- `connector/` covers Integration Service boundary behavior without
  cloud-side mutations. `registry_discovery.yaml` exercises
  `uip maestro bpmn registry list/search/get` for documented agent, queue,
  and connector wrapper types and falls back to a static-coverage note when
  the CLI subcommand is unavailable.
- `operate-diagnose/` covers public-safe operate and diagnosis paths with
  synthetic runtime responses.
- `_shared/` contains small Python helpers for durable XML shape assertions.

## Contributor Commands

From the repository root:

```bash
bash skills/uipath-maestro-bpmn/.maintenance/check-validation-fixtures.sh
bash skills/uipath-maestro-bpmn/.maintenance/check-all.sh
```

Run the Maestro BPMN smoke eval:

```bash
cd tests
make tags TAGS="uipath-maestro-bpmn smoke" EXPERIMENT=experiments/default.yaml
```

Run the Maestro BPMN e2e eval slice:

```bash
cd tests
make tags TAGS="uipath-maestro-bpmn e2e" EXPERIMENT=experiments/e2e.yaml
```

Run all tests for this skill:

```bash
cd tests
make test-uipath-maestro-bpmn
```

The `operate-diagnose/minimal_fault_triage.yaml` task uses the shared mock
`uip` dispatcher and public-safe synthetic BPMN runtime responses to cover the
Operate -> Diagnose lifecycle without cloud-side mutations.

CI should run the two maintenance commands before evals so malformed fixture or documentation drift fails before an agent run starts.
