# Maestro BPMN Skill Eval Tasks

These tasks exercise the `uipath-maestro-bpmn` skill and its public-safe validation fixture corpus.

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

Run all tests for this skill:

```bash
cd tests
make test-uipath-maestro-bpmn
```

CI should run the two maintenance commands before evals so malformed fixture or documentation drift fails before an agent run starts.
