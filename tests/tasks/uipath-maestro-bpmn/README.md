# Maestro BPMN Skill Eval Tasks

These tasks exercise the `uipath-maestro-bpmn` skill — a registry-driven,
authoring-only skill for producing valid, importable Maestro `.bpmn` XML.

- `smoke/` covers the core registry-driven authoring loop.
  `registry_discovery.yaml` checks that the agent discovers extension types via
  `uip maestro bpmn registry pull/list/search/get` (saving raw CLI output as
  evidence) before authoring. `author_validate.yaml` checks that the agent
  authors a structurally sound BPMN (start -> exclusive gateway with two
  conditioned branches -> end, with a full `bpmndi:BPMNDiagram`) and validates
  it with a well-formed-XML parse plus the structural checklist. Both are
  authoring-only — no upload, publish, deploy, debug, run, or pack.
- `author/` covers BPMN skeleton structure, gateways, sequence flows, and
  diagrams.
- `authoring/` covers implementation rows that are not fixture-only: business
  rules, API workflow execution, and the script/Jint lifecycle path.
- `nodes/` covers task-wrapper and script-task authoring behavior, including
  public-safe Maestro BPMN XML contract variants.
- `connector/` covers Integration Service boundary behavior and registry
  discovery for connector wrapper types without cloud-side mutations.
- `hitl/` covers human-in-the-loop (`Actions.HITL` user task) authoring —
  completion wiring, multi-outcome gateway routing, task data-mapping design,
  downstream consumption of the reviewer's decision, boolean-typed decisions,
  and surgical insertion of an approval gate into an existing `.bpmn`. Ported
  from the flow suite's `hitl/` intent.
- `edit/` covers surgical brownfield edits on a pre-built, valid `.bpmn`
  fixture (add / remove / update / reorder a node, add an output mapping,
  extract a group into a subprocess). Each task ships its own fixture and
  grades the requested edit plus preservation of untouched ids, `uipath:*`
  payloads, and `uipath:migrationVersion` via an ElementTree diff against the
  pristine original.
- `e2e/` covers a multi-node authoring scenario end to end.
- `operate-diagnose/` covers diagnostic inspection and operate-action guidance
  using mocked CLI responses, matching the operate and diagnose capabilities the
  skill retains.
- `_shared/` contains small Python helpers for durable XML shape assertions.

These tasks validate with `uip maestro bpmn validate <file>`, which runs the
full PO.Frontend canvas rule set offline (added in UiPath/cli#3135). If the CLI
is unavailable, they fall back to parsing the BPMN for well-formedness and
walking the structural checklist in the skill's `references/structural-bpmn.md`.

## Contributor Commands

Run the Maestro BPMN smoke eval:

```bash
cd tests
make tags TAGS="uipath-maestro-bpmn smoke" EXPERIMENT=experiments/smoke.yaml
```

Run all tests for this skill:

```bash
cd tests
make test-uipath-maestro-bpmn
```
